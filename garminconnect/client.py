"""Authentication engine for Garmin Connect."""
import random
from time import sleep

import base64
import contextlib
import json
import logging
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

# Auth constants (matching Android GCM app)
MOBILE_SSO_CLIENT_ID = "GCM_ANDROID_DARK"
MOBILE_SSO_SERVICE_URL = "https://mobile.integration.garmin.com/gcm/android"
MOBILE_SSO_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; sdk_gphone64_arm64 Build/TE1A.220922.025; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.0.0 Mobile Safari/537.36"
)

# Web portal constants (desktop browser flow — less likely to be Cloudflare-blocked)
PORTAL_SSO_CLIENT_ID = "GarminConnect"
PORTAL_SSO_SERVICE_URL = "https://connect.garmin.com/app"
DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


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
)


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

        # Native Bearer tokens (primary auth)
        self.di_token: str | None = None
        self.di_refresh_token: str | None = None
        self.di_client_id: str | None = None

        # JWT_WEB cookie auth (fallback when DI token is unavailable)
        self.jwt_web: str | None = None
        self.csrf_token: str | None = None

        # curl_cffi session for login flows
        self.cs: Any = None
        if HAS_CFFI:
            self.cs = cffi_requests.Session(impersonate="chrome")
        else:
            self.cs = requests.Session()
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
        """Log in to Garmin Connect.

        Tries multiple login strategies in order:
        1. Portal web flow with curl_cffi (desktop browser TLS + UA)
        2. Portal web flow with plain requests (desktop browser UA)
        3. Mobile SSO with curl_cffi (Android WebView TLS)
        4. Mobile SSO with plain requests (last resort)
        """
        strategies: list[tuple[str, Any]] = []

        # Portal web login — uses /portal/api/login with desktop Chrome UA.
        # This is the endpoint connect.garmin.com itself uses, so Cloudflare
        # cannot block it without breaking their own website.
        if HAS_CFFI:
            strategies.append(("portal+cffi", self._portal_web_login_cffi))
        strategies.append(("portal+requests", self._portal_web_login_requests))

        # Mobile SSO — uses /mobile/api/login with Android WebView UA.
        if HAS_CFFI:
            strategies.append(("mobile+cffi", self._portal_login))
        strategies.append(("mobile+requests", self._mobile_login))

        last_err: Exception | None = None
        for name, method in strategies:
            try:
                _LOGGER.debug("Trying login strategy: %s", name)
                return method(
                    email,
                    password,
                    prompt_mfa=prompt_mfa,
                    return_on_mfa=return_on_mfa,
                )
            except GarminConnectAuthenticationError:  # noqa: PERF203
                # Wrong credentials / invalid MFA — no point trying other strategies
                raise
            except (
                GarminConnectTooManyRequestsError,
                GarminConnectConnectionError,
            ) as e:
                # 429 or connection error on this endpoint — try the next one
                _LOGGER.warning("Login strategy %s failed: %s", name, e)
                last_err = e
                continue
            except Exception as e:
                _LOGGER.warning("Login strategy %s failed: %s", name, e)
                last_err = e
                continue

        # All strategies exhausted
        if isinstance(last_err, GarminConnectTooManyRequestsError):
            raise last_err
        raise GarminConnectConnectionError(
            f"All login strategies failed. Last error: {last_err}"
        )

    # ------------------------------------------------------------------
    # Portal web login (desktop browser flow)
    # ------------------------------------------------------------------

    def _portal_web_login_cffi(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Login via the web portal endpoint using curl_cffi TLS impersonation.

        Tries multiple browser impersonations — Safari's TLS fingerprint
        is less likely to be blocked by Cloudflare than Chrome's.
        """
        impersonations = ["safari", "safari_ios", "chrome120", "edge101", "chrome"]
        last_err: Exception | None = None
        for imp in impersonations:
            try:
                _LOGGER.debug("Trying portal+cffi with impersonation=%s", imp)
                sess: Any = cffi_requests.Session(impersonate=imp)  # type: ignore[arg-type]
                return self._portal_web_login(
                    sess,
                    email,
                    password,
                    prompt_mfa=prompt_mfa,
                    return_on_mfa=return_on_mfa,
                )
            except GarminConnectAuthenticationError:  # noqa: PERF203
                raise
            except Exception as e:
                _LOGGER.debug("portal+cffi(%s) failed: %s", imp, e)
                last_err = e
                continue
        raise last_err or GarminConnectConnectionError("All cffi impersonations failed")

    def _portal_web_login_requests(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Login via the web portal endpoint using plain requests + random browser UA."""
        sess = requests.Session()
        sess.headers.update(_random_browser_headers())
        return self._portal_web_login(
            sess, email, password, prompt_mfa=prompt_mfa, return_on_mfa=return_on_mfa
        )

    def _portal_web_login(
        self,
        sess: Any,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Login via /portal/api/login — the web Connect flow.

        This is the same endpoint the Garmin Connect React app uses.
        Cloudflare cannot block it without breaking the website itself.
        """
        signin_url = f"{self._sso}/portal/sso/en-US/sign-in"

        # Generate a consistent random browser identity for this login attempt
        browser_hdrs = _random_browser_headers()

        # Step 1: GET the sign-in page to establish session cookies
        get_headers = {
            **browser_hdrs,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        sess.get(
            signin_url,
            params={
                "clientId": PORTAL_SSO_CLIENT_ID,
                "service": PORTAL_SSO_SERVICE_URL,
            },
            headers=get_headers,
            timeout=30,
        )
        sleep(random.uniform(30, 45))

        # Step 2: POST credentials to the portal login API
        login_url = f"{self._sso}/portal/api/login"
        login_params = {
            "clientId": PORTAL_SSO_CLIENT_ID,
            "locale": "en-US",
            "service": PORTAL_SSO_SERVICE_URL,
        }
        post_headers = {
            **browser_hdrs,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": self._sso,
            "Referer": f"{signin_url}?clientId={PORTAL_SSO_CLIENT_ID}"
            f"&service={PORTAL_SSO_SERVICE_URL}",
        }

        r = sess.post(
            login_url,
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
                "Portal login returned 429. Cloudflare is blocking this request."
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
            # Store session + context for MFA completion
            self._mfa_portal_web_session = sess
            self._mfa_portal_web_params = login_params
            self._mfa_portal_web_headers = post_headers

            if return_on_mfa:
                return "needs_mfa", sess

            if prompt_mfa:
                mfa_code = prompt_mfa()
                self._complete_mfa_portal_web(mfa_code)
                return None, None
            raise GarminConnectAuthenticationError(
                "MFA Required but no prompt_mfa mechanism supplied"
            )

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(
                ticket, sess=sess, service_url=PORTAL_SSO_SERVICE_URL
            )
            return None, None

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        raise GarminConnectConnectionError(f"Portal web login failed: {res}")

    def _complete_mfa_portal_web(self, mfa_code: str) -> None:
        """Complete MFA via the portal web flow.

        Tries /portal/api/mfa/verifyCode first, then /mobile/api/mfa/verifyCode
        as fallback (same SSO session cookies work for both).
        """
        sess = self._mfa_portal_web_session
        mfa_json: dict[str, Any] = {
            "mfaMethod": getattr(self, "_mfa_method", "email"),
            "mfaVerificationCode": mfa_code,
            "rememberMyBrowser": True,
            "reconsentList": [],
            "mfaSetup": False,
        }

        # Try both portal and mobile MFA endpoints
        mfa_endpoints = [
            (
                f"{self._sso}/portal/api/mfa/verifyCode",
                self._mfa_portal_web_params,
                self._mfa_portal_web_headers,
            ),
            (
                f"{self._sso}/mobile/api/mfa/verifyCode",
                {
                    "clientId": MOBILE_SSO_CLIENT_ID,
                    "locale": "en-US",
                    "service": MOBILE_SSO_SERVICE_URL,
                },
                self._mfa_portal_web_headers,
            ),
        ]

        failures: list[str] = []
        for mfa_url, params, headers in mfa_endpoints:
            _LOGGER.debug("Trying MFA endpoint: %s", mfa_url)
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

            # Check for 429 at HTTP level
            if r.status_code == 429:
                failures.append(f"{mfa_url}: HTTP 429")
                continue

            try:
                res = r.json()
            except Exception:
                body_preview = r.text[:200] if r.text else "(empty)"
                failures.append(
                    f"{mfa_url}: HTTP {r.status_code} non-JSON: {body_preview}"
                )
                continue

            # Check for 429 inside JSON error body
            if res.get("error", {}).get("status-code") == "429":
                failures.append(f"{mfa_url}: 429 in JSON body")
                continue

            if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
                ticket = res["serviceTicketId"]
                # Use the service_url matching whichever endpoint succeeded
                svc_url = (
                    PORTAL_SSO_SERVICE_URL
                    if "/portal/" in mfa_url
                    else MOBILE_SSO_SERVICE_URL
                )
                self._establish_session(ticket, sess=sess, service_url=svc_url)
                return

            failures.append(f"{mfa_url}: HTTP {r.status_code} => {res}")

        raise GarminConnectAuthenticationError(
            f"MFA Verification failed on all endpoints: {'; '.join(failures)}"
        )

    # ------------------------------------------------------------------
    # Mobile SSO login (Android app flow)
    # ------------------------------------------------------------------

    def _portal_login(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Login via mobile SSO API using curl_cffi for TLS impersonation."""
        sess: Any = cffi_requests.Session(impersonate="safari")

        # Step 1: GET mobile sign-in page (sets SESSION cookies)
        signin_url = f"{self._sso}/mobile/sso/en_US/sign-in"
        sess.get(
            signin_url,
            params={
                "clientId": MOBILE_SSO_CLIENT_ID,
                "service": MOBILE_SSO_SERVICE_URL,
            },
            headers={
                "User-Agent": MOBILE_SSO_USER_AGENT,
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.9",
            },
            timeout=30,
        )

        # Step 2: POST credentials
        login_params = {
            "clientId": MOBILE_SSO_CLIENT_ID,
            "locale": "en-US",
            "service": MOBILE_SSO_SERVICE_URL,
        }
        post_headers = {
            "User-Agent": MOBILE_SSO_USER_AGENT,
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": self._sso,
            "referer": f"{signin_url}?clientId={MOBILE_SSO_CLIENT_ID}&service={MOBILE_SSO_SERVICE_URL}",
        }
        r = sess.post(
            f"{self._sso}/mobile/api/login",
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
        r.raise_for_status()
        res = r.json()
        resp_type = res.get("responseStatus", {}).get("type")

        if resp_type == "MFA_REQUIRED":
            self._mfa_method = res.get("customerMfaInfo", {}).get(
                "mfaLastMethodUsed", "email"
            )
            self._mfa_cffi_session = sess
            self._mfa_cffi_params = login_params
            self._mfa_cffi_headers = post_headers

            if return_on_mfa:
                return "needs_mfa", sess

            if prompt_mfa:
                mfa_code = prompt_mfa()
                self._complete_mfa_portal(mfa_code)
                return None, None
            raise GarminConnectAuthenticationError(
                "MFA Required but no prompt_mfa mechanism supplied"
            )

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket, sess=sess)
            return None, None

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        raise GarminConnectAuthenticationError(f"Portal login failed: {res}")

    def _complete_mfa_portal(self, mfa_code: str) -> None:
        """Complete MFA verification via mobile API with curl_cffi."""
        sess = self._mfa_cffi_session
        r = sess.post(
            f"{self._sso}/mobile/api/mfa/verifyCode",
            params=self._mfa_cffi_params,
            headers=self._mfa_cffi_headers,
            json={
                "mfaMethod": getattr(self, "_mfa_method", "email"),
                "mfaVerificationCode": mfa_code,
                "rememberMyBrowser": True,
                "reconsentList": [],
                "mfaSetup": False,
            },
            timeout=30,
        )
        res = r.json()
        if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket, sess=sess)
            return
        raise GarminConnectAuthenticationError(f"MFA Verification failed: {res}")

    def _mobile_login(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Login via mobile SSO API using plain requests (fallback)."""
        sess = requests.Session()
        sess.headers.update(
            {
                "User-Agent": MOBILE_SSO_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

        sess.get(
            f"{self._sso}/mobile/sso/en_US/sign-in",
            params={
                "clientId": MOBILE_SSO_CLIENT_ID,
                "service": MOBILE_SSO_SERVICE_URL,
            },
        )

        r = sess.post(
            f"{self._sso}/mobile/api/login",
            params={
                "clientId": MOBILE_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": MOBILE_SSO_SERVICE_URL,
            },
            json={
                "username": email,
                "password": password,
                "rememberMe": True,
                "captchaToken": "",
            },
        )

        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError(
                "Login failed (429 Rate Limit). Try again later."
            )

        try:
            res = r.json()
        except Exception as err:
            raise GarminConnectConnectionError(
                f"Login failed (Not JSON): HTTP {r.status_code}"
            ) from err

        resp_type = res.get("responseStatus", {}).get("type")

        if resp_type == "MFA_REQUIRED":
            self._mfa_method = res.get("customerMfaInfo", {}).get(
                "mfaLastMethodUsed", "email"
            )
            self._mfa_session = sess

            if return_on_mfa:
                return "needs_mfa", self._mfa_session

            if prompt_mfa:
                mfa_code = prompt_mfa()
                self._complete_mfa(mfa_code)
                return None, None
            raise GarminConnectAuthenticationError(
                "MFA Required but no prompt_mfa mechanism supplied"
            )

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket)
            return None, None

        if (
            "status-code" in res.get("error", {})
            and res["error"]["status-code"] == "429"
        ):
            raise GarminConnectTooManyRequestsError("429 Rate Limit")

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        raise GarminConnectAuthenticationError(
            f"Unhandled Garmin Login JSON, Login failed: {res}"
        )

    def _complete_mfa(self, mfa_code: str) -> None:
        r = self._mfa_session.post(
            f"{self._sso}/mobile/api/mfa/verifyCode",
            params={
                "clientId": MOBILE_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": MOBILE_SSO_SERVICE_URL,
            },
            json={
                "mfaMethod": getattr(self, "_mfa_method", "email"),
                "mfaVerificationCode": mfa_code,
                "rememberMyBrowser": True,
                "reconsentList": [],
                "mfaSetup": False,
            },
        )
        res = r.json()
        if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket)
            return
        raise GarminConnectAuthenticationError(f"MFA Verification failed: {res}")

    def _establish_session(
        self, ticket: str, sess: Any = None, service_url: str | None = None
    ) -> None:
        """Consume a CAS service ticket — try native DI token exchange first,
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

        self.cs.get(
            MOBILE_SSO_SERVICE_URL,
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
        if hasattr(self, "_mfa_portal_web_session"):
            self._complete_mfa_portal_web(mfa_code)
        elif hasattr(self, "_mfa_cffi_session"):
            self._complete_mfa_portal(mfa_code)
        else:
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
