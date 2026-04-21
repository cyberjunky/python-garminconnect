"""Authentication engine for Garmin Connect.

Strategy chain (each strategy is tried in order; only auth errors stop the chain):
1. Mobile iOS + curl_cffi  (TLS fingerprint rotation, no delay needed)
2. Mobile iOS + requests   (plain HTTP fallback)
3. SSO embed widget + cffi (HTML form flow, bypasses clientId rate limits)
4. Portal web + curl_cffi  (TLS fingerprint rotation, 10-20s anti-WAF delay)
5. Portal web + requests   (plain HTTP last resort)
"""

import base64
import contextlib
import json
import logging
import random
import re
import time
from pathlib import Path
from typing import Any

import requests

try:
    from curl_cffi import requests as cffi_requests

    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

try:
    from ua_generator import generate as _generate_ua

    HAS_UA_GEN = True
except ImportError:
    HAS_UA_GEN = False

from .exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

_LOGGER = logging.getLogger(__name__)

# -- iOS mobile app constants (Strategy 1 & 2) --
IOS_SSO_CLIENT_ID = "GCM_IOS_DARK"
IOS_SERVICE_URL = "https://mobile.integration.garmin.com/gcm/ios"
IOS_LOGIN_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
)

# -- Android mobile app constants (legacy alias, kept for backward compat) --
MOBILE_SSO_CLIENT_ID = "GCM_ANDROID_DARK"
MOBILE_SSO_SERVICE_URL = "https://mobile.integration.garmin.com/gcm/android"
MOBILE_SSO_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Mobile Safari/537.36"
)

# -- Portal (fallback) constants --
PORTAL_SSO_CLIENT_ID = "GarminConnect"
PORTAL_SSO_SERVICE_URL = "https://connect.garmin.com/app"
DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# -- Anti-WAF delay bounds (seconds) --
# Cloudflare flags rapid GET→POST sequences as bot-like.
LOGIN_DELAY_MIN_S = 10.0
LOGIN_DELAY_MAX_S = 20.0
# Widget flow uses a shorter delay (different rate-limit bucket).
WIDGET_DELAY_MIN_S = 3.0
WIDGET_DELAY_MAX_S = 8.0

# -- TLS impersonation profiles --
MOBILE_IMPERSONATIONS: tuple[str, ...] = ("safari_ios", "safari", "chrome120")
PORTAL_IMPERSONATIONS: tuple[str, ...] = (
    "safari",
    "safari_ios",
    "chrome120",
    "edge101",
    "chrome",
)

# -- Regex helpers for HTML parsing (widget flow) --
_CSRF_RE = re.compile(r'name="_csrf"\s+value="(.+?)"')
_TITLE_RE = re.compile(r"<title>(.+?)</title>")


def _random_browser_headers() -> dict[str, str]:
    """Generate a random browser User-Agent + sec-ch-ua headers.

    Falls back to a static desktop Chrome UA if ua_generator is not installed.
    """
    if HAS_UA_GEN:
        ua = _generate_ua()
        return dict(ua.headers.get())
    return {"User-Agent": DESKTOP_USER_AGENT}


NATIVE_API_USER_AGENT = "GCM-Android-5.23"
NATIVE_X_GARMIN_USER_AGENT = (
    "com.garmin.android.apps.connectmobile/5.23; ; Google/sdk_gphone64_arm64/google; "
    "Android/33; Dalvik/2.1.0"
)
DI_TOKEN_URL = "https://diauth.garmin.com/di-oauth2-service/oauth/token"  # noqa: S105
DI_GRANT_TYPE = (
    "https://connectapi.garmin.com/di-oauth2-service/oauth/grant/service_ticket"
)
DI_CLIENT_IDS = (
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2024Q4",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI",
    "GARMIN_CONNECT_MOBILE_IOS_DI",
)


class _MFARequired(Exception):
    """Internal sentinel — raised by login strategies when MFA is needed.

    Stops the strategy chain immediately (like a credential error).
    The caller (login()) handles it via prompt_mfa / return_on_mfa.
    """


def _build_basic_auth(client_id: str) -> str:
    return "Basic " + base64.b64encode(f"{client_id}:".encode()).decode()


def _native_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers: dict[str, str] = {
        "User-Agent": NATIVE_API_USER_AGENT,
        "X-Garmin-User-Agent": NATIVE_X_GARMIN_USER_AGENT,
        "X-Garmin-Paired-App-Version": "10861",
        "X-Garmin-Client-Platform": "Android",
        "X-App-Ver": "10861",
        "X-Lang": "en",
        "X-GCExperience": "GC5",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra:
        headers.update(extra)
    return headers


class Client:
    """A client to communicate with Garmin Connect."""

    def __init__(self, domain: str = "garmin.com", **kwargs: Any) -> None:
        self.domain = domain
        self._sso = f"https://sso.{domain}"
        self._connect = f"https://connect.{domain}"
        self._connectapi = f"https://connectapi.{domain}"
        # Portal service URL is domain-aware for CN support
        self._portal_service_url = f"https://connect.{domain}/app"

        # Native Bearer tokens (primary auth)
        self.di_token: str | None = None
        self.di_refresh_token: str | None = None
        self.di_client_id: str | None = None

        # JWT_WEB cookie auth (fallback when DI token exchange fails)
        self.jwt_web: str | None = None
        self.csrf_token: str | None = None

        # Plain session for JWT_WEB fallback and session refresh
        self.cs: Any = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=kwargs.get("pool_connections", 20),
            pool_maxsize=kwargs.get("pool_maxsize", 20),
        )
        self.cs.mount("https://", adapter)

        self._tokenstore_path: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.di_token or self.jwt_web)

    def get_api_headers(self) -> dict[str, str]:
        if not self.is_authenticated:
            raise GarminConnectAuthenticationError("Not authenticated")
        if self.di_token:
            return _native_headers(
                {
                    "Authorization": f"Bearer {self.di_token}",
                    "Accept": "application/json",
                }
            )
        # JWT_WEB fallback
        headers: dict[str, str] = {
            "Accept": "application/json",
            "NK": "NT",
            "Origin": self._connect,
            "Referer": f"{self._connect}/modern/",
            "DI-Backend": f"connectapi.{self.domain}",
            "Cookie": f"JWT_WEB={self.jwt_web}",
        }
        if self.csrf_token:
            headers["connect-csrf-token"] = str(self.csrf_token)
        return headers

    def login(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Log in using a cascading 5-strategy chain (ha-garmin order).

        Tries each strategy in order.  Only credential errors (GarminConnectAuthenticationError)
        and MFA requirements stop the chain immediately — all other failures
        (429 rate limits, transport errors, HTML challenges) fall through to
        the next strategy.

        Args:
            email: Garmin account email.
            password: Garmin account password.
            prompt_mfa: Callable that returns an MFA code string when invoked.
            return_on_mfa: When True, return ("needs_mfa", None) instead of
                           calling prompt_mfa; caller must call resume_login().

        Returns:
            (None, None) on success; ("needs_mfa", None) when return_on_mfa=True.

        """
        strategies: list[tuple[str, Any]] = [
            ("mobile+cffi", lambda: self._mobile_login_cffi(email, password)),
            ("mobile+requests", lambda: self._mobile_login_requests(email, password)),
            ("widget+cffi", lambda: self._widget_web_login(email, password)),
            ("portal+cffi", lambda: self._portal_web_login_cffi(email, password)),
            (
                "portal+requests",
                lambda: self._portal_web_login_requests(email, password),
            ),
        ]

        last_err: Exception | None = None
        rate_limited_count = 0

        for name, run in strategies:
            try:
                _LOGGER.debug("Trying login strategy: %s", name)
                run()
                # Strategy succeeded — login complete
                return None, None
            except GarminConnectAuthenticationError:
                # Wrong credentials — stop immediately, no point trying further
                raise
            except _MFARequired:
                # MFA state is stored on self — handle and stop chain
                if return_on_mfa:
                    return "needs_mfa", None
                if prompt_mfa:
                    mfa_code = prompt_mfa()
                    self._complete_mfa(mfa_code)
                    return None, None
                raise GarminConnectAuthenticationError(  # noqa: B904
                    "MFA Required but no prompt_mfa mechanism supplied"
                )
            except GarminConnectTooManyRequestsError as e:
                _LOGGER.warning("%s returned 429: %s", name, e)
                rate_limited_count += 1
                last_err = e
                continue
            except Exception as e:
                _LOGGER.warning("%s failed: %s", name, e)
                last_err = e
                continue

        if rate_limited_count == len(strategies):
            raise GarminConnectTooManyRequestsError(
                "All login strategies rate limited (429). "
                "Try again later or check your IP/network."
            )
        raise GarminConnectConnectionError(
            f"All login strategies exhausted: {last_err}"
        )

    # ------------------------------------------------------------------ #
    #  STRATEGY 1 — Mobile iOS + curl_cffi (TLS fingerprint rotation)    #
    # ------------------------------------------------------------------ #

    def _mobile_login_cffi(self, email: str, password: str) -> None:
        """Mobile login with curl_cffi TLS fingerprint rotation.

        Different TLS fingerprints land in different Cloudflare rate-limit
        buckets, so rotating through them gives multiple shots.
        """
        if not HAS_CFFI:
            raise GarminConnectConnectionError("curl_cffi not available")
        last_err: Exception | None = None
        for imp in MOBILE_IMPERSONATIONS:
            try:
                _LOGGER.debug("mobile+cffi trying impersonation=%s", imp)
                sess: Any = cffi_requests.Session(impersonate=imp)  # type: ignore[arg-type]
                self._do_mobile_login(sess, email, password)
                return
            except (GarminConnectAuthenticationError, _MFARequired):
                raise
            except GarminConnectTooManyRequestsError as e:
                _LOGGER.debug("mobile+cffi(%s) 429: %s", imp, e)
                last_err = e
                continue
            except Exception as e:
                _LOGGER.debug("mobile+cffi(%s) failed: %s", imp, e)
                last_err = e
                continue
        if last_err:
            raise last_err
        raise GarminConnectConnectionError("mobile+cffi: no impersonations available")

    # ------------------------------------------------------------------ #
    #  STRATEGY 2 — Mobile iOS + plain requests                           #
    # ------------------------------------------------------------------ #

    def _mobile_login_requests(self, email: str, password: str) -> None:
        """Mobile login with plain requests (no TLS fingerprinting)."""
        sess = requests.Session()
        self._do_mobile_login(sess, email, password)

    # ------------------------------------------------------------------ #
    #  Shared mobile login logic                                          #
    # ------------------------------------------------------------------ #

    def _do_mobile_login(self, sess: Any, email: str, password: str) -> None:
        """Login via sso.garmin.com/mobile/api/login (iOS app flow)."""
        login_url = f"{self._sso}/mobile/api/login"
        login_params = {
            "clientId": IOS_SSO_CLIENT_ID,
            "locale": "en-US",
            "service": IOS_SERVICE_URL,
        }
        login_headers = {
            "User-Agent": IOS_LOGIN_UA,
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": self._sso,
        }

        r = sess.post(
            login_url,
            params=login_params,
            headers=login_headers,
            json={
                "username": email,
                "password": password,
                "rememberMe": True,
                "captchaToken": "",
            },
            timeout=30,
        )

        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError(
                "Mobile login returned 429 — IP rate limited by Garmin"
            )

        try:
            res = r.json()
        except Exception as err:
            raise GarminConnectConnectionError(
                f"Mobile login failed (non-JSON): HTTP {r.status_code}"
            ) from err

        resp_type = res.get("responseStatus", {}).get("type")

        if resp_type == "MFA_REQUIRED":
            self._mfa_method = res.get("customerMfaInfo", {}).get(
                "mfaLastMethodUsed", "email"
            )
            self._mfa_session = sess
            self._mfa_login_params = login_params
            self._mfa_post_headers = login_headers
            self._mfa_service_url = IOS_SERVICE_URL
            self._mfa_flow = "ios"
            raise _MFARequired()

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket, sess=sess, service_url=IOS_SERVICE_URL)
            return

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        # Check for 429 buried inside JSON error body
        if res.get("error", {}).get("status-code") == "429":
            raise GarminConnectTooManyRequestsError("Mobile login: 429 in JSON body")

        raise GarminConnectConnectionError(f"Mobile login failed: {res}")

    # ------------------------------------------------------------------ #
    #  STRATEGY 3 — SSO Embed Widget + curl_cffi                         #
    # ------------------------------------------------------------------ #

    def _widget_web_login(self, email: str, password: str) -> None:
        """Login via the SSO embed HTML widget.

        Uses HTML form flow which bypasses clientId-based rate limits.
        Uses curl_cffi for TLS fingerprinting.
        """
        if not HAS_CFFI:
            raise GarminConnectConnectionError("curl_cffi not available")
        sess: Any = cffi_requests.Session(impersonate="chrome", timeout=30)
        sso_base = f"{self._sso}/sso"
        sso_embed = f"{sso_base}/embed"
        embed_params = {
            "id": "gauth-widget",
            "embedWidget": "true",
            "gauthHost": sso_base,
        }
        signin_params = {
            **embed_params,
            "gauthHost": sso_embed,
            "service": sso_embed,
            "source": sso_embed,
            "redirectAfterAccountLoginUrl": sso_embed,
            "redirectAfterAccountCreationUrl": sso_embed,
        }

        # Step 1: GET embed page to establish session cookies
        r = sess.get(sso_embed, params=embed_params)
        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError("Widget embed GET returned 429")
        if not r.ok:
            raise GarminConnectConnectionError(f"Widget embed returned {r.status_code}")

        # Step 2: GET signin page for CSRF token
        r = sess.get(
            f"{sso_base}/signin",
            params=signin_params,
            headers={"Referer": sso_embed},
        )
        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError("Widget signin GET returned 429")

        csrf_match = _CSRF_RE.search(r.text)
        if not csrf_match:
            raise GarminConnectConnectionError("Widget login: missing CSRF token")

        # Anti-WAF delay between GET and POST
        delay_s = random.uniform(WIDGET_DELAY_MIN_S, WIDGET_DELAY_MAX_S)  # noqa: S311
        _LOGGER.debug("Widget login: waiting %.0fs anti-WAF delay...", delay_s)
        time.sleep(delay_s)

        # Step 3: POST credentials
        r = sess.post(
            f"{sso_base}/signin",
            params=signin_params,
            headers={"Referer": r.url},
            data={
                "username": email,
                "password": password,
                "embed": "true",
                "_csrf": csrf_match.group(1),
            },
            timeout=30,
        )

        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError("Widget signin POST returned 429")

        title_match = _TITLE_RE.search(r.text)
        title = title_match.group(1) if title_match else ""

        # Detect server/infrastructure errors — fall through to next strategy
        title_lower = title.lower()
        if any(
            hint in title_lower
            for hint in (
                "bad gateway",
                "service unavailable",
                "cloudflare",
                "502",
                "503",
            )
        ):
            raise GarminConnectConnectionError(f"Widget login: server error '{title}'")

        # Early credential detection — don't waste remaining strategies
        if any(
            hint in title_lower
            for hint in ("locked", "invalid", "incorrect", "account error")
        ):
            raise GarminConnectAuthenticationError(
                f"Widget authentication failed: '{title}'"
            )

        if "MFA" in title:
            self._mfa_session = sess
            self._mfa_login_params = signin_params
            self._mfa_post_headers = {"Referer": r.url}
            self._mfa_flow = "widget"
            self._widget_last_resp = r
            raise _MFARequired()

        if title != "Success":
            raise GarminConnectConnectionError(
                f"Widget login: unexpected title '{title}'"
            )

        # Step 4: Extract service ticket
        ticket_match = re.search(r'embed\?ticket=([^"]+)"', r.text)
        if not ticket_match:
            raise GarminConnectConnectionError("Widget login: missing service ticket")

        self._establish_session(ticket_match.group(1), sess=sess, service_url=sso_embed)

    def _complete_mfa_widget(self, mfa_code: str) -> None:
        """Complete MFA for widget flow."""
        sess = getattr(self, "_mfa_session", None)
        r = getattr(self, "_widget_last_resp", None)
        if not sess or not r:
            raise GarminConnectAuthenticationError("Missing widget MFA context")

        csrf_match = _CSRF_RE.search(r.text)
        if not csrf_match:
            raise GarminConnectAuthenticationError("Widget MFA: missing CSRF token")

        r = sess.post(
            f"{self._sso}/sso/verifyMFA/loginEnterMfaCode",
            params=getattr(self, "_mfa_login_params", {}),
            headers=getattr(self, "_mfa_post_headers", {}),
            data={
                "mfa-code": mfa_code,
                "embed": "true",
                "_csrf": csrf_match.group(1),
                "fromPage": "setupEnterMfaCode",
            },
            timeout=30,
        )

        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError("Widget MFA verify returned 429")

        title_match = _TITLE_RE.search(r.text)
        title = title_match.group(1) if title_match else ""

        if title != "Success":
            raise GarminConnectAuthenticationError(f"Widget MFA failed: {title}")

        ticket_match = re.search(r'embed\?ticket=([^"]+)"', r.text)
        if not ticket_match:
            raise GarminConnectAuthenticationError("Widget MFA: missing service ticket")

        self._establish_session(
            ticket_match.group(1),
            sess=sess,
            service_url=f"{self._sso}/sso/embed",
        )

    # ------------------------------------------------------------------ #
    #  STRATEGY 4 — Portal web + curl_cffi (TLS fingerprint rotation)    #
    # ------------------------------------------------------------------ #

    def _portal_web_login_cffi(self, email: str, password: str) -> None:
        """Portal login with curl_cffi TLS fingerprint rotation.

        Different TLS fingerprints land in different Cloudflare rate-limit
        buckets, so rotating through them gives multiple shots.
        """
        if not HAS_CFFI:
            raise GarminConnectConnectionError("curl_cffi not available")
        last_err: Exception | None = None
        for imp in PORTAL_IMPERSONATIONS:
            try:
                _LOGGER.debug("portal+cffi trying impersonation=%s", imp)
                sess: Any = cffi_requests.Session(impersonate=imp)  # type: ignore[arg-type]
                self._do_portal_web_login(sess, email, password)
                return
            except (GarminConnectAuthenticationError, _MFARequired):
                raise
            except GarminConnectTooManyRequestsError as e:
                _LOGGER.debug("portal+cffi(%s) 429: %s", imp, e)
                last_err = e
                continue
            except Exception as e:
                _LOGGER.debug("portal+cffi(%s) failed: %s", imp, e)
                last_err = e
                continue
        if last_err:
            raise last_err
        raise GarminConnectConnectionError("portal+cffi: no impersonations available")

    # ------------------------------------------------------------------ #
    #  STRATEGY 5 — Portal web + plain requests                          #
    # ------------------------------------------------------------------ #

    def _portal_web_login_requests(self, email: str, password: str) -> None:
        """Portal login with plain requests (no TLS fingerprinting)."""
        sess = requests.Session()
        self._do_portal_web_login(sess, email, password)

    # ------------------------------------------------------------------ #
    #  Shared portal login logic                                          #
    # ------------------------------------------------------------------ #

    def _do_portal_web_login(self, sess: Any, email: str, password: str) -> None:
        """Login via /portal/api/login — desktop browser flow."""
        signin_url = f"{self._sso}/portal/sso/en-US/sign-in"
        browser_hdrs = _random_browser_headers()

        # Step 1: GET the signin page to grab initial cookies
        get_resp = sess.get(
            signin_url,
            params={
                "clientId": PORTAL_SSO_CLIENT_ID,
                "service": self._portal_service_url,
            },
            headers={
                **browser_hdrs,
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30,
        )

        if get_resp.status_code == 429:
            raise GarminConnectTooManyRequestsError(
                "Portal login GET returned 429 — Cloudflare blocking this request."
            )

        # Anti-WAF delay: 10-20s mimics real browser "read then type" behaviour.
        delay_s = random.uniform(LOGIN_DELAY_MIN_S, LOGIN_DELAY_MAX_S)  # noqa: S311
        _LOGGER.info(
            "Portal login: waiting %.0fs to avoid Cloudflare rate limiting...",
            delay_s,
        )
        time.sleep(delay_s)

        # Step 2: POST credentials
        login_params = {
            "clientId": PORTAL_SSO_CLIENT_ID,
            "locale": "en-US",
            "service": self._portal_service_url,
        }
        post_headers = {
            **browser_hdrs,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": self._sso,
            "Referer": (
                f"{signin_url}?clientId={PORTAL_SSO_CLIENT_ID}"
                f"&service={self._portal_service_url}"
            ),
        }

        r = sess.post(
            f"{self._sso}/portal/api/login",
            params=login_params,
            headers=post_headers,
            json={
                "username": email,
                "password": password,
                "rememberMe": True,
                "captchaToken": "",
            },
            timeout=30,
        )

        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError(
                "Portal login POST returned 429 — Cloudflare blocking this request."
            )

        try:
            res = r.json()
        except Exception as err:
            raise GarminConnectConnectionError(
                f"Portal login failed (non-JSON): HTTP {r.status_code}"
            ) from err

        resp_type = res.get("responseStatus", {}).get("type")

        if resp_type == "MFA_REQUIRED":
            self._mfa_method = res.get("customerMfaInfo", {}).get(
                "mfaLastMethodUsed", "email"
            )
            self._mfa_session = sess
            self._mfa_login_params = login_params
            self._mfa_post_headers = post_headers
            self._mfa_service_url = self._portal_service_url
            self._mfa_flow = "portal"
            raise _MFARequired()

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(
                ticket, sess=sess, service_url=self._portal_service_url
            )
            return

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        # Check for 429 buried inside JSON error body
        if res.get("error", {}).get("status-code") == "429":
            raise GarminConnectTooManyRequestsError("Portal login: 429 in JSON body")

        raise GarminConnectConnectionError(f"Portal web login failed: {res}")

    # ------------------------------------------------------------------ #
    #  MFA COMPLETION — dual-endpoint fallback                           #
    # ------------------------------------------------------------------ #

    def _complete_mfa(self, mfa_code: str) -> None:
        """Complete MFA — routes to the handler matching the login flow.

        For portal/ios flows, tries both /portal and /mobile MFA verify
        endpoints as they may be on different rate-limit buckets.
        """
        flow = getattr(self, "_mfa_flow", "portal")
        if flow == "widget":
            self._complete_mfa_widget(mfa_code)
            return

        sess = self._mfa_session

        mfa_json: dict[str, Any] = {
            "mfaMethod": getattr(self, "_mfa_method", "email"),
            "mfaVerificationCode": mfa_code,
            "rememberMyBrowser": True,
            "reconsentList": [],
            "mfaSetup": False,
        }

        # Map flow name to SSO path segment ("ios" flow uses /mobile/ endpoint)
        flow_path = "mobile" if flow == "ios" else flow

        # Try both MFA endpoints — they share SSO session cookies but may be
        # on different rate-limit buckets.
        mfa_endpoints: list[tuple[str, dict[str, str], dict[str, str]]] = [
            (
                f"{self._sso}/{flow_path}/api/mfa/verifyCode",
                self._mfa_login_params,
                self._mfa_post_headers,
            ),
        ]
        # Add the other path as fallback
        if flow_path == "mobile":
            alt_endpoint = f"{self._sso}/portal/api/mfa/verifyCode"
            alt_params: dict[str, str] = {
                "clientId": PORTAL_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": self._portal_service_url,
            }
        else:
            alt_endpoint = f"{self._sso}/mobile/api/mfa/verifyCode"
            alt_params = {
                "clientId": IOS_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": IOS_SERVICE_URL,
            }
        mfa_endpoints.append((alt_endpoint, alt_params, self._mfa_post_headers))

        failures: list[str] = []
        rate_limited_count = 0

        for mfa_url, params, headers in mfa_endpoints:
            try:
                r = sess.post(
                    mfa_url,
                    params=params,
                    headers=headers,
                    json=mfa_json,
                    timeout=30,
                )
            except Exception as e:
                failures.append(f"{mfa_url}: connection error {e}")
                continue

            if r.status_code == 429:
                failures.append(f"{mfa_url}: HTTP 429")
                rate_limited_count += 1
                continue

            try:
                res = r.json()
            except Exception:
                # Non-JSON response is almost always a Cloudflare HTML challenge
                failures.append(f"{mfa_url}: HTTP {r.status_code} non-JSON")
                continue

            if res.get("error", {}).get("status-code") == "429":
                failures.append(f"{mfa_url}: 429 in JSON body")
                rate_limited_count += 1
                continue

            if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
                ticket = res["serviceTicketId"]
                svc_url = (
                    IOS_SERVICE_URL
                    if flow == "ios"
                    else getattr(self, "_mfa_service_url", self._portal_service_url)
                )
                self._establish_session(ticket, sess=sess, service_url=svc_url)
                return

            # Non-success JSON response — could be auth failure
            failures.append(f"{mfa_url}: {res}")

        # All endpoints failed
        if rate_limited_count == len(mfa_endpoints):
            raise GarminConnectTooManyRequestsError(
                f"MFA verification rate limited on all endpoints: {failures}"
            )
        raise GarminConnectAuthenticationError(f"MFA verification failed: {failures}")

    # ------------------------------------------------------------------ #
    #  SESSION ESTABLISHMENT — DI token first, JWT_WEB fallback          #
    # ------------------------------------------------------------------ #

    def _establish_session(
        self, ticket: str, sess: Any = None, service_url: str | None = None
    ) -> None:
        """Consume a CAS service ticket — DI token exchange first,
        fall back to JWT_WEB cookie auth.
        """
        try:
            self._exchange_service_ticket(ticket, service_url=service_url)
            return
        except Exception as e:
            _LOGGER.warning("DI token exchange failed (%s), falling back to JWT_WEB", e)

        # Fallback: consume ticket via connect.garmin.com for JWT_WEB cookie
        if sess is not None:
            self.cs = sess

        svc = service_url or IOS_SERVICE_URL
        self.cs.get(
            svc,
            params={"ticket": ticket},
            allow_redirects=True,
            timeout=30,
        )

        jwt_web = None
        for c in self.cs.cookies.jar:
            if c.name == "JWT_WEB":
                jwt_web = c.value
                break

        if not jwt_web:
            raise GarminConnectAuthenticationError(
                "JWT_WEB cookie not set after ticket consumption"
            )
        self.jwt_web = jwt_web

    def _http_post(self, url: str, **kwargs: Any) -> Any:
        """POST using curl_cffi if available, else plain requests."""
        if HAS_CFFI:
            return cffi_requests.post(url, impersonate="chrome", **kwargs)
        return requests.post(url, **kwargs)  # noqa: S113

    def _exchange_service_ticket(
        self, ticket: str, service_url: str | None = None
    ) -> None:
        """Exchange a CAS service ticket for native DI + IT Bearer tokens.

        POST to diauth.garmin.com to get a DI OAuth2 token, then exchange
        for an IT token via services.garmin.com.
        """
        # service_url must match the one used during SSO login
        svc_url = service_url or MOBILE_SSO_SERVICE_URL

        di_token = None
        di_refresh = None
        di_client_id = None

        for client_id in DI_CLIENT_IDS:
            r = self._http_post(
                DI_TOKEN_URL,
                headers=_native_headers(
                    {
                        "Authorization": _build_basic_auth(client_id),
                        "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Cache-Control": "no-cache",
                    }
                ),
                data={
                    "client_id": client_id,
                    "service_ticket": ticket,
                    "grant_type": DI_GRANT_TYPE,
                    "service_url": svc_url,
                },
                timeout=30,
            )
            if r.status_code == 429:
                raise GarminConnectTooManyRequestsError(
                    "DI token exchange rate limited"
                )
            if not r.ok:
                _LOGGER.debug(
                    "DI exchange failed for %s: %s %s",
                    client_id,
                    r.status_code,
                    r.text[:200],
                )
                continue
            try:
                data = r.json()
                di_token = data["access_token"]
                di_refresh = data.get("refresh_token")
                di_client_id = self._extract_client_id_from_jwt(di_token) or client_id
                break
            except Exception as e:
                _LOGGER.debug("DI token parse failed for %s: %s", client_id, e)
                continue

        if not di_token:
            raise GarminConnectAuthenticationError(
                "DI token exchange failed for all client IDs"
            )

        self.di_token = di_token
        self.di_refresh_token = di_refresh
        self.di_client_id = di_client_id

    def _refresh_di_token(self) -> None:
        """Refresh the DI Bearer token using the stored refresh token."""
        if not self.di_refresh_token or not self.di_client_id:
            raise GarminConnectAuthenticationError("No DI refresh token available")
        r = self._http_post(
            DI_TOKEN_URL,
            headers=_native_headers(
                {
                    "Authorization": _build_basic_auth(self.di_client_id),
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cache-Control": "no-cache",
                }
            ),
            data={
                "grant_type": "refresh_token",
                "client_id": self.di_client_id,
                "refresh_token": self.di_refresh_token,
            },
            timeout=30,
        )
        if not r.ok:
            raise GarminConnectAuthenticationError(
                f"DI token refresh failed: {r.status_code} {r.text[:200]}"
            )
        data = r.json()
        self.di_token = data["access_token"]
        self.di_refresh_token = data.get("refresh_token", self.di_refresh_token)
        self.di_client_id = (
            self._extract_client_id_from_jwt(self.di_token) or self.di_client_id
        )

    def _extract_client_id_from_jwt(self, token: str) -> str | None:
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return None
            payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
            value = payload.get("client_id")
            return str(value) if value else None
        except Exception:
            return None

    def _token_expires_soon(self) -> bool:
        token = self.di_token or self.jwt_web
        if not token:
            return False
        try:
            import time as _time

            parts = str(token).split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
                payload = json.loads(
                    base64.urlsafe_b64decode(payload_b64.encode()).decode()
                )
                exp = payload.get("exp")
                if exp and _time.time() > (int(exp) - 900):
                    return True
        except Exception:
            _LOGGER.debug("Failed to check token expiry")
        return False

    def _refresh_session(self) -> None:
        """Refresh auth — DI token refresh or legacy JWT_WEB CAS refresh."""
        if self.di_token:
            try:
                self._refresh_di_token()
                if self._tokenstore_path:
                    with contextlib.suppress(Exception):
                        self.dump(self._tokenstore_path)
            except Exception as err:
                _LOGGER.debug("DI token refresh failed: %s", err)
            return

        # JWT_WEB refresh via CAS TGT
        if not self.is_authenticated:
            return
        try:
            self.cs.get(
                f"{self._sso}/mobile/sso/en_US/sign-in",
                params={
                    "clientId": MOBILE_SSO_CLIENT_ID,
                    "service": MOBILE_SSO_SERVICE_URL,
                },
                allow_redirects=True,
                timeout=15,
            )
            for c in self.cs.cookies.jar:
                if c.name == "JWT_WEB":
                    self.jwt_web = c.value
                    _LOGGER.debug("Session refreshed via CAS TGT")
                    if self._tokenstore_path:
                        with contextlib.suppress(Exception):
                            self.dump(self._tokenstore_path)
                    return

            with contextlib.suppress(Exception):
                self.cs.post(
                    f"{self._connect}/services/auth/token/di-oauth/refresh",
                    headers={
                        "Accept": "application/json",
                        "NK": "NT",
                        "Referer": f"{self._connect}/modern/",
                    },
                    timeout=10,
                )
            for c in self.cs.cookies.jar:
                if c.name == "JWT_WEB":
                    self.jwt_web = c.value
                    break
        except Exception as err:
            _LOGGER.debug("Refresh failed: %s", err)

    def dumps(self) -> str:
        """Serialize session state to JSON string."""
        data: dict[str, Any] = {
            "di_token": self.di_token,
            "di_refresh_token": self.di_refresh_token,
            "di_client_id": self.di_client_id,
        }
        return json.dumps(data)

    def dump(self, path: str) -> None:
        """Write tokens safely to disk."""
        p = Path(path).expanduser()
        if p.is_dir() or not p.name.endswith(".json"):
            p = p / "garmin_tokens.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.dumps())

    def load(self, path: str) -> None:
        try:
            self._tokenstore_path = path
            p = Path(path).expanduser()
            if p.is_dir() or not p.name.endswith(".json"):
                p = p / "garmin_tokens.json"
            self.loads(p.read_text())
        except Exception as e:
            raise GarminConnectConnectionError(
                f"Token path not loading cleanly: {e}"
            ) from e

    def loads(self, tokenstore: str) -> None:
        try:
            data = json.loads(tokenstore)
            self.di_token = data.get("di_token")
            self.di_refresh_token = data.get("di_refresh_token")
            self.di_client_id = data.get("di_client_id")
            if not self.is_authenticated:
                raise GarminConnectAuthenticationError("Missing tokens from dict load")
        except Exception as e:
            raise GarminConnectConnectionError(
                f"Token extraction loads() structurally failed: {e}"
            ) from e

    def connectapi(self, path: str, **kwargs: Any) -> Any:
        return self._run_request("GET", path, **kwargs).json()

    def request(self, method: str, _domain: str, path: str, **kwargs: Any) -> Any:
        kwargs.pop("api", None)
        return self._run_request(method, path, **kwargs)

    def post(self, _domain: str, path: str, **kwargs: Any) -> Any:
        api = kwargs.pop("api", False)
        resp = self._run_request("POST", path, **kwargs)
        if api:
            return resp.json() if hasattr(resp, "json") else None
        return resp

    def put(self, _domain: str, path: str, **kwargs: Any) -> Any:
        api = kwargs.pop("api", False)
        resp = self._run_request("PUT", path, **kwargs)
        if api:
            return resp.json() if hasattr(resp, "json") else None
        return resp

    def delete(self, _domain: str, path: str, **kwargs: Any) -> Any:
        api = kwargs.pop("api", False)
        resp = self._run_request("DELETE", path, **kwargs)
        if api:
            return resp.json() if hasattr(resp, "json") else None
        return resp

    def resume_login(self, _client_state: Any, mfa_code: str) -> tuple[str | None, Any]:
        """Complete a previously initiated MFA login."""
        self._complete_mfa(mfa_code)
        return None, None

    def download(self, path: str, **kwargs: Any) -> bytes:
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update({"Accept": "*/*"})
        return self._run_request("GET", path, **kwargs).content

    def _fresh_api_session(self) -> requests.Session:
        """Create a fresh plain requests.Session for each API call."""
        sess = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
        sess.mount("https://", adapter)
        return sess

    def _run_request(self, method: str, path: str, **kwargs: Any) -> Any:
        if self.is_authenticated and self._token_expires_soon():
            self._refresh_session()

        url = f"{self._connectapi}/{path.lstrip('/')}"

        if "timeout" not in kwargs:
            kwargs["timeout"] = 15

        headers = self.get_api_headers()
        custom_headers = kwargs.pop("headers", {})
        headers.update(custom_headers)

        sess = self._fresh_api_session()
        resp = sess.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            self._refresh_session()
            resp = sess.request(method, url, headers=self.get_api_headers(), **kwargs)

        if resp.status_code == 204:

            class EmptyJSONResp:
                status_code = 204
                content = b""

                def json(self) -> Any:
                    return {}

                def __repr__(self) -> str:
                    return "{}"

                def __str__(self) -> str:
                    return "{}"

            return EmptyJSONResp()

        if resp.status_code >= 400:
            error_msg = f"API Error {resp.status_code}"
            try:
                error_data = resp.json()
                if isinstance(error_data, dict):
                    msg = (
                        error_data.get("message")
                        or error_data.get("content")
                        or error_data.get("detailedImportResult", {})
                        .get("failures", [{}])[0]
                        .get("messages", [""])[0]
                    )
                    if msg:
                        error_msg += f" - {msg}"
                    else:
                        error_msg += f" - {error_data}"
            except Exception:
                if len(resp.text) < 500:
                    error_msg += f" - {resp.text}"
            raise GarminConnectConnectionError(error_msg)

        return resp
