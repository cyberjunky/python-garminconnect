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
import http.cookiejar
import json
import logging
import math
import os
import random
import re
import secrets
import threading
import time
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote

import requests
from requests.adapters import HTTPAdapter

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
    GarminConnectNotFoundError,
    GarminConnectTooManyRequestsError,
)

_LOGGER = logging.getLogger(__name__)


# Detect ~username expansion that would point into another user's home directory.
_OTHER_USER_HOME_RE = re.compile(r"^~[^/\\]")


def token_file_path(path: str) -> Path:
    """Return the token file represented by a directory or JSON path.

    Rejects paths that expand into another user's home directory via
    ``~username`` syntax. Bare ``~`` and ``~/...`` are allowed because they
    resolve to the current user's home.

    Also rejects symlinked tokenstore paths so a pre-planted symlink cannot
    redirect load/dump/logout to an attacker-controlled location.
    """
    if _OTHER_USER_HOME_RE.match(path):
        raise ValueError(
            f"Token path must not reference another user's home directory: {path!r}"
        )
    token_path = Path(path).expanduser()
    # Reject symlinks anywhere in the tokenstore ancestry (e.g.
    # ~/.garminconnect -> /attacker/dir). O_NOFOLLOW on the final open()
    # only covers the last component; an intermediate symlinked directory
    # would still redirect load/dump/logout into an attacker-controlled tree.
    for check_path in (token_path, *token_path.parents):
        try:
            if check_path.is_symlink():
                raise ValueError(f"Token path must not be a symlink: {path!r}")
        except OSError as e:
            raise ValueError(
                f"Token path cannot be checked for symlinks: {path!r}"
            ) from e
    if token_path.is_dir() or token_path.suffix.casefold() != ".json":
        return token_path / "garmin_tokens.json"
    return token_path


# -- Domain allowlist --
# Only official Garmin domains are valid for authentication and API traffic.
# Arbitrary values would let a malicious caller redirect credentials elsewhere.
ALLOWED_DOMAINS = {"garmin.com", "garmin.cn"}

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
# Garmin's widget MFA page exposes these variables in inline <script> tags.
_WIDGET_MFA_VARS_RE = re.compile(
    r'var\s+(customerGuid|mfaMethod|locale|clientId|codeSentTo)\s*=\s*"([^"]*)"\s*;'
)


def _parse_widget_mfa_vars(html: str) -> dict[str, str]:
    """Extract the inline JS variables Garmin uses for widget MFA."""
    return {m.group(1): m.group(2) for m in _WIDGET_MFA_VARS_RE.finditer(html)}


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

    Stops the strategy chain immediately. The caller (login()) handles it via
    prompt_mfa / return_on_mfa.
    """


def _build_basic_auth(client_id: str) -> str:
    return "Basic " + base64.b64encode(f"{client_id}:".encode()).decode()


_QUERY_VALUE_RE = re.compile(r"([?&][\w.-]+=)[^&\s)'\"]+")


def _sanitize_exception_text(err: Exception) -> str:
    """Render an exception for logs/messages with URL query values redacted.

    ``requests`` embeds the full request URL — query string included — in its
    exception text. On the login fallback path that URL carries the CAS
    service ticket (``?ticket=ST-...``), so logging or re-raising the raw
    exception would leak a credential into application logs and bug reports.
    """
    return _QUERY_VALUE_RE.sub(r"\1<redacted>", f"{type(err).__name__}: {err}")


def _iter_file_objects(kwargs: dict[str, Any]) -> Iterator[Any]:
    """Yield file-like objects referenced by request kwargs (files/data)."""
    files = kwargs.get("files")
    if isinstance(files, Mapping):
        values = list(files.values())
    elif isinstance(files, list | tuple):
        values = [v for _, v in files]
    else:
        values = []
    for value in values:
        # requests accepts fileobj or (name, fileobj[, content_type[, headers]])
        fileobj = (
            value[1] if isinstance(value, tuple | list) and len(value) >= 2 else value
        )
        if hasattr(fileobj, "read"):
            yield fileobj
    data = kwargs.get("data")
    if hasattr(data, "read"):
        yield data


def _capture_file_positions(
    kwargs: dict[str, Any],
) -> list[tuple[Any, int]] | None:
    """Record the stream position of each file-like body before a request.

    Returns None when any body cannot be repositioned, meaning a retry
    would re-read from EOF and silently send empty/truncated content.
    """
    positions: list[tuple[Any, int]] = []
    for fileobj in _iter_file_objects(kwargs):
        try:
            if not fileobj.seekable():
                return None
            positions.append((fileobj, fileobj.tell()))
        except (OSError, ValueError, AttributeError):
            return None
    data = kwargs.get("data")
    if data is not None and not hasattr(data, "read") and isinstance(data, Iterator):
        # Streamed iterable body (e.g. a generator): attempt #1 consumes it
        # and it cannot be rewound, so a retry must not be attempted.
        return None
    return positions


def _restore_file_positions(positions: list[tuple[Any, int]]) -> bool:
    """Rewind file-like bodies to their pre-request positions. False on failure."""
    try:
        for fileobj, pos in positions:
            fileobj.seek(pos)
    except (OSError, ValueError, AttributeError):
        return False
    return True


def _decode_jwt_payload(token: str) -> dict[str, Any] | None:
    """Decode a JWT payload without verifying the signature.

    Garmin signs tokens on the server side; the client does not have the
    signing key, so full signature verification is not possible here. We do
    reject tokens that claim ``alg: none`` or otherwise look structurally
    invalid, preventing the most trivial client-side spoofing of unsigned
    payloads.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        header_b64 = parts[0] + "=" * (-len(parts[0]) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_b64).decode())
        if header.get("alg") == "none":
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    except Exception:
        return None


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
        if domain not in ALLOWED_DOMAINS:
            raise ValueError(
                f"Invalid domain {domain!r}; must be one of {sorted(ALLOWED_DOMAINS)}"
            )
        self.domain = domain
        self._sso = f"https://sso.{domain}"
        self._connect = f"https://connect.{domain}"
        self._connectapi = f"https://connectapi.{domain}"
        # Portal service URL is domain-aware for CN support
        # Mobile service URLs are domain-aware for CN support
        self._ios_service_url = f"https://mobile.integration.{domain}/gcm/ios"
        self._mobile_sso_service_url = (
            f"https://mobile.integration.{domain}/gcm/android"
        )
        self._portal_service_url = f"https://connect.{domain}/app"
        # DI auth host is domain-aware too — CN users live on diauth.garmin.cn
        # and don't exist in the .com user database. Without this, token refresh
        # for CN accounts fails with 400 invalid_grant.
        self._di_token_url = f"https://diauth.{domain}/di-oauth2-service/oauth/token"

        # Native Bearer tokens (primary auth)
        self.di_token: str | None = None
        self.di_refresh_token: str | None = None
        self.di_client_id: str | None = None

        # JWT_WEB cookie auth (fallback when DI token exchange fails)
        self.jwt_web: str | None = None
        self.csrf_token: str | None = None

        # Plain session for JWT_WEB fallback and session refresh
        self.cs: Any = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=kwargs.get("pool_connections", 20),
            pool_maxsize=kwargs.get("pool_maxsize", 20),
        )
        self.cs.mount("https://", adapter)

        # Dedicated keep-alive session for API calls. Kept separate from
        # self.cs so auth cookies (JWT_WEB jar, CAS TGT) don't leak into API
        # requests — API auth travels in headers per-call via get_api_headers.
        # Reusing one session lets urllib3 pool TCP/TLS across calls instead
        # of doing a fresh handshake every request (~1 s saved per call).
        self._api_session: requests.Session = requests.Session()
        # Reject all cookies so server-set cookies can't accumulate in the jar
        # and collide with the explicit Cookie header used on the JWT_WEB path.
        # Matches the old fresh-session-per-call guarantee: empty cookie state.
        self._api_session.cookies.set_policy(
            http.cookiejar.DefaultCookiePolicy(allowed_domains=[])
        )
        api_adapter = HTTPAdapter(
            pool_connections=kwargs.get("pool_connections", 20),
            pool_maxsize=kwargs.get("pool_maxsize", 20),
        )
        self._api_session.mount("https://", api_adapter)

        self._tokenstore_path: str | None = None
        # Serialize token refresh and state mutation so concurrent API calls can't
        # race on the same refresh token or observe half-updated state.
        self._token_lock: threading.RLock = threading.RLock()
        # True after login(return_on_mfa=True) returns "needs_mfa" until
        # resume_login() finishes. Prevents interleaving another login on the
        # same instance while MFA state is held on self.
        self._mfa_pending: bool = False
        # Set of strategy names to skip during login, e.g. {"mobile+cffi"}.
        # Valid names: mobile+cffi, mobile+requests, widget+cffi,
        #              portal+cffi, portal+requests
        self.skip_strategies: set[str] = set()
        # When True (default), each login strategy's token is validated against
        # the API tier before the chain accepts it; a token the API rejects
        # (401/403) is discarded and the next strategy is tried. Set False to
        # restore the legacy "first token wins" behavior.
        self.verify_login: bool = kwargs.get("verify_login", True)

    @property
    def is_authenticated(self) -> bool:
        return bool(self.di_token or self.jwt_web)

    def _clear_auth_state(self, *, keep_tokenstore_path: bool = False) -> None:
        """Wipe all in-memory auth tokens and session state so the next login starts clean.

        ``keep_tokenstore_path`` preserves the persistence target: login() sets
        it via the Garmin wrapper *before* the credential flow runs, and a
        fresh login should keep persisting to the same store.
        """
        self.di_token = None
        self.di_refresh_token = None
        self.di_client_id = None
        self.jwt_web = None
        self.csrf_token = None
        if not keep_tokenstore_path:
            self._tokenstore_path = None
        self._mfa_pending = False
        for attr in (
            "_mfa_session",
            "_mfa_login_params",
            "_mfa_post_headers",
            "_mfa_service_url",
            "_mfa_flow",
            "_mfa_method",
            "_widget_last_resp",
        ):
            setattr(self, attr, None)
        # Drop any SSO / CAS / JWT_WEB cookies so a stale session cannot be
        # silently refreshed after logout.
        self.cs.cookies.clear()

    def _verify_token(self) -> bool:
        """Check that the current token is actually accepted by the API tier.

        A strategy can obtain a DI token from the auth host (HTTP 200) that the
        API tier (connectapi) then rejects with 401 "Token is not active" —
        this is account/region dependent (see issue #369). We confirm the token
        works with one lightweight authenticated call.

        Returns True if accepted, or if the check is inconclusive. Only a
        definitive auth rejection (401/403) returns False, so a transient
        network error or 5xx never blocks an otherwise-working login.
        """
        try:
            self.connectapi("/userprofile-service/socialProfile")
            return True
        except GarminConnectConnectionError as e:
            msg = str(e)
            if "401" in msg or "403" in msg:
                _LOGGER.warning("Token rejected by API tier: %s", msg)
                return False
            _LOGGER.debug("Token validation inconclusive (kept): %s", msg)
            return True
        except Exception as e:
            _LOGGER.debug(
                "Token validation inconclusive (kept): %s",
                _sanitize_exception_text(e),
            )
            return True

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
        the next strategy. MFA requirements are resolved immediately via
        prompt_mfa / return_on_mfa.

        Args:
            email: Garmin account email.
            password: Garmin account password.
            prompt_mfa: Callable that returns an MFA code string when invoked.
            return_on_mfa: When True, return ("needs_mfa", None) instead of
                           calling prompt_mfa; caller must call resume_login().

        Returns:
            (None, None) on success; ("needs_mfa", None) when return_on_mfa=True.

        """
        if self._mfa_pending:
            raise GarminConnectAuthenticationError(
                "MFA login already in progress; complete it with resume_login() "
                "or call logout() first"
            )

        # Start every credential login from a clean slate. A stale di_token
        # from a previous login/token-load must not survive this call: it
        # would keep is_authenticated True after all strategies fail, and
        # get_api_headers() prefers di_token, so it would silently shadow a
        # fresh jwt_web obtained by a web strategy (and _verify_token would
        # then "verify" the old identity instead of the new login).
        self._clear_auth_state(keep_tokenstore_path=True)

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
        if self.skip_strategies:
            strategies = [
                (n, fn) for n, fn in strategies if n not in self.skip_strategies
            ]
            _LOGGER.debug("Skipping login strategies: %s", self.skip_strategies)

        last_err: Exception | None = None
        rate_limited_count = 0

        def resolve_mfa(name: str) -> tuple[str | None, Any]:
            if return_on_mfa:
                self._mfa_pending = True
                return "needs_mfa", None
            if prompt_mfa:
                mfa_code = prompt_mfa()
                self._complete_mfa(mfa_code)
                if self.verify_login and not self._verify_token():
                    self._clear_auth_state(keep_tokenstore_path=True)
                    raise GarminConnectConnectionError(
                        f"{name}: token rejected by API tier after MFA"
                    )
                self._mfa_pending = False
                return None, None
            raise GarminConnectAuthenticationError(
                "MFA Required but no prompt_mfa mechanism supplied"
            )

        for name, run in strategies:
            try:
                _LOGGER.debug("Trying login strategy: %s", name)
                run()
                # Strategy got a token — make sure the API tier accepts it
                # before declaring success (else fall through to the next).
                if self.verify_login and not self._verify_token():
                    _LOGGER.warning(
                        "%s obtained a token the API rejected; trying next strategy",
                        name,
                    )
                    self._clear_auth_state(keep_tokenstore_path=True)
                    last_err = GarminConnectConnectionError(
                        f"{name}: token rejected by API tier"
                    )
                    continue
                return None, None
            except GarminConnectAuthenticationError:
                # Wrong credentials — stop immediately, no point trying further
                raise
            except _MFARequired:
                # Resolve MFA immediately; the strategy is responsible for
                # triggering code delivery (widget flow does so explicitly).
                try:
                    return resolve_mfa(name)
                except GarminConnectConnectionError as e:
                    last_err = e
                    continue
            except GarminConnectTooManyRequestsError as e:
                _LOGGER.warning(
                    "%s returned 429: %s", name, _sanitize_exception_text(e)
                )
                rate_limited_count += 1
                last_err = e
                continue
            except Exception as e:
                _LOGGER.warning("%s failed: %s", name, _sanitize_exception_text(e))
                last_err = e
                continue

        if rate_limited_count == len(strategies):
            raise GarminConnectTooManyRequestsError(
                "All login strategies rate limited (429). "
                "Try again later or check your IP/network."
            )
        raise GarminConnectConnectionError(
            "All login strategies exhausted: "
            + (_sanitize_exception_text(last_err) if last_err else "no strategies ran")
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
                sess: Any = cffi_requests.Session(impersonate=cast("Any", imp))
                self._do_mobile_login(sess, email, password)
                return
            except (GarminConnectAuthenticationError, _MFARequired):
                raise
            except GarminConnectTooManyRequestsError as e:
                _LOGGER.debug(
                    "mobile+cffi(%s) 429: %s", imp, _sanitize_exception_text(e)
                )
                last_err = e
                continue
            except Exception as e:
                _LOGGER.debug(
                    "mobile+cffi(%s) failed: %s", imp, _sanitize_exception_text(e)
                )
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
            "service": self._ios_service_url,
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

        if r.status_code == 403:
            raise GarminConnectConnectionError(
                "Mobile login: HTTP 403 (Cloudflare bot challenge) — "
                "falling through to next strategy"
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
            self._mfa_service_url = self._ios_service_url
            self._mfa_flow = "ios"
            raise _MFARequired()

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(
                ticket, sess=sess, service_url=self._ios_service_url
            )
            return

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        # Check for 429 buried inside JSON error body
        if res.get("error", {}).get("status-code") == "429":
            raise GarminConnectTooManyRequestsError("Mobile login: 429 in JSON body")

        if resp_type == "CAPTCHA_REQUIRED":
            raise GarminConnectConnectionError(
                "Mobile login: CAPTCHA required (bot challenge) — "
                "falling through to next strategy"
            )

        _LOGGER.debug("Mobile login unexpected response: %s", res)
        raise GarminConnectConnectionError(
            f"Mobile login failed: HTTP {r.status_code}, "
            f"responseStatus={resp_type or 'unknown'}"
        )

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

        # Child/family accounts are restricted from web SSO — log clearly and
        # fall through so the remaining strategies still get a chance.
        if "unable to sign in" in title_lower or "unable to login" in title_lower:
            _LOGGER.warning(
                "Widget login: '%s' — account may be a Garmin child/family account "
                "restricted from web SSO; child accounts are not supported.",
                title,
            )
            raise GarminConnectConnectionError(
                f"Widget login: account restricted '{title}'"
            )

        # MFA challenge. The signin page itself is also titled "GARMIN
        # Authentication Application", so rely on the inline JS variables
        # Garmin emits for the MFA page (mfaMethod, customerGuid, etc.) rather
        # than the title alone. Email/SMS MFA pages may not actually send the
        # code during the credential POST, so we explicitly request delivery via
        # the same endpoint the browser's "Request a new code" link uses.
        mfa_vars = _parse_widget_mfa_vars(r.text)
        mfa_method = mfa_vars.get("mfaMethod", "").lower()
        looks_like_mfa = "mfa" in title_lower or (
            "authentication application" in title_lower and mfa_method
        )
        if looks_like_mfa:
            self._widget_request_mfa_code(sess, r.text, r.url)
            self._mfa_session = sess
            self._mfa_login_params = signin_params
            self._mfa_post_headers = {"Referer": r.url}
            self._mfa_flow = "widget"
            self._mfa_method = mfa_vars.get("mfaMethod", "")
            self._widget_last_resp = r
            raise _MFARequired()

        if title != "Success":
            raise GarminConnectConnectionError(
                f"Widget login: unexpected title '{title}'"
            )

        # Step 4: Extract service ticket — ticket may appear under any service URL
        ticket_match = re.search(r'\?ticket=(ST-[^"&\s]+)', r.text)
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

        ticket_match = re.search(r'\?ticket=(ST-[^"&\s]+)', r.text)
        if not ticket_match:
            raise GarminConnectAuthenticationError("Widget MFA: missing service ticket")

        self._establish_session(
            ticket_match.group(1),
            sess=sess,
            service_url=f"{self._sso}/sso/embed",
        )

    def _widget_request_mfa_code(self, sess: Any, page_html: str, referer: str) -> None:
        """Request Garmin to send an email/SMS MFA code for this widget session.

        The widget's own JavaScript calls ``/sso/verifyMFA/mfaCode`` when the
        user clicks "Request a new code". We use the same endpoint to ensure
        the code is actually delivered before prompting the user.
        """
        mfa_vars = _parse_widget_mfa_vars(page_html)
        mfa_method = mfa_vars.get("mfaMethod", "").lower()
        if mfa_method not in ("email", "sms"):
            # Nothing to trigger for TOTP/authenticator apps.
            return

        if mfa_vars.get("codeSentTo"):
            # Garmin already sent a code during the signin POST.
            return

        client_id = mfa_vars.get("clientId", "")
        payload = {
            "customerGuid": mfa_vars.get("customerGuid", ""),
            "mfaMethod": mfa_vars.get("mfaMethod", ""),
            "locale": mfa_vars.get("locale", ""),
        }

        _LOGGER.debug(
            "Widget MFA: explicitly requesting %s code from Garmin", mfa_method
        )
        r = sess.post(
            f"{self._sso}/sso/verifyMFA/mfaCode",
            params={"clientId": client_id},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Referer": referer,
            },
            json=payload,
            timeout=30,
        )

        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError(
                "Widget MFA code request returned 429"
            )
        if not r.ok:
            raise GarminConnectConnectionError(
                f"Widget MFA code request returned {r.status_code}"
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
                sess: Any = cffi_requests.Session(impersonate=cast("Any", imp))
                self._do_portal_web_login(sess, email, password)
                return
            except (GarminConnectAuthenticationError, _MFARequired):
                raise
            except GarminConnectTooManyRequestsError as e:
                _LOGGER.debug(
                    "portal+cffi(%s) 429: %s", imp, _sanitize_exception_text(e)
                )
                last_err = e
                continue
            except Exception as e:
                _LOGGER.debug(
                    "portal+cffi(%s) failed: %s", imp, _sanitize_exception_text(e)
                )
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

        if r.status_code == 403:
            raise GarminConnectConnectionError(
                "Portal login: HTTP 403 (Cloudflare bot challenge) — "
                "falling through to next strategy"
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

        if resp_type == "CAPTCHA_REQUIRED":
            raise GarminConnectConnectionError(
                "Portal login: CAPTCHA required (bot challenge) — "
                "falling through to next strategy"
            )

        _LOGGER.debug("Portal web login unexpected response: %s", res)
        raise GarminConnectConnectionError(
            f"Portal web login failed: HTTP {r.status_code}, "
            f"responseStatus={resp_type or 'unknown'}"
        )

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
                "service": self._ios_service_url,
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
                    self._ios_service_url
                    if flow == "ios"
                    else getattr(self, "_mfa_service_url", self._portal_service_url)
                )
                self._establish_session(ticket, sess=sess, service_url=svc_url)
                return

            # Non-success JSON response — could be auth failure. Log the full
            # response at DEBUG but keep exception messages free of sensitive
            # SSO metadata such as serviceTicketId, customerGuid, or URLs.
            _LOGGER.debug("MFA verify non-success response from %s: %s", mfa_url, res)
            status = res.get("responseStatus", {}).get("type") or res.get(
                "error", {}
            ).get("status-code", "unknown")
            failures.append(f"{mfa_url}: {status}")

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
            _LOGGER.warning(
                "DI token exchange failed (%s), falling back to JWT_WEB",
                _sanitize_exception_text(e),
            )

        # Fallback: consume ticket via connect.garmin.com for JWT_WEB cookie
        if sess is not None:
            self.cs = sess

        svc = service_url or self._ios_service_url
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
        timeout = kwargs.pop("timeout", 30)
        if HAS_CFFI:
            return cffi_requests.post(
                url, impersonate="chrome", timeout=timeout, **kwargs
            )
        return requests.post(url, timeout=timeout, **kwargs)

    def _exchange_service_ticket(
        self, ticket: str, service_url: str | None = None
    ) -> None:
        """Exchange a CAS service ticket for native DI + IT Bearer tokens.

        POST to diauth.garmin.com to get a DI OAuth2 token, then exchange
        for an IT token via services.garmin.com.
        """
        # service_url must match the one used during SSO login
        svc_url = service_url or self._mobile_sso_service_url

        di_token = None
        di_refresh = None
        di_client_id = None

        for client_id in DI_CLIENT_IDS:
            r = self._http_post(
                self._di_token_url,
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
        with self._token_lock:
            # Re-check under the lock in case another thread already refreshed
            # while we were waiting.
            if not self.di_refresh_token or not self.di_client_id:
                raise GarminConnectAuthenticationError("No DI refresh token available")
            r = self._http_post(
                self._di_token_url,
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
                _LOGGER.debug(
                    "DI token refresh failed: status=%s body=%r",
                    r.status_code,
                    r.text[:200],
                )
                raise GarminConnectAuthenticationError(
                    f"DI token refresh failed: {r.status_code}"
                )
            data = r.json()
            access_token = data["access_token"]
            self.di_token = access_token
            self.di_refresh_token = data.get("refresh_token", self.di_refresh_token)
            self.di_client_id = (
                self._extract_client_id_from_jwt(access_token) or self.di_client_id
            )

    def _extract_client_id_from_jwt(self, token: str) -> str | None:
        payload = _decode_jwt_payload(token)
        if not payload:
            return None
        value = payload.get("client_id")
        return str(value) if value else None

    def _token_expires_soon(self) -> bool:
        token = self.di_token or self.jwt_web
        if not token:
            return False
        payload = _decode_jwt_payload(str(token))
        if not payload:
            return False
        # 'exp' is a server-controlled claim from an unverified JWT payload, so
        # coerce it defensively: a non-numeric string, container, boolean,
        # non-finite or overflowing value must not raise (TypeError/ValueError/
        # OverflowError) and take down every request.
        raw_exp = payload.get("exp")
        if isinstance(raw_exp, bool):
            return False
        try:
            exp = float(raw_exp)  # type: ignore[arg-type]
        except (TypeError, ValueError, OverflowError):
            return False
        if not math.isfinite(exp):
            return False
        return time.time() > exp - 900

    def _refresh_session(self) -> None:
        """Refresh auth — DI token refresh or legacy JWT_WEB CAS refresh."""
        with self._token_lock:
            if self.di_token:
                try:
                    self._refresh_di_token()
                    if self._tokenstore_path:
                        with contextlib.suppress(Exception):
                            self.dump(self._tokenstore_path)
                except Exception as err:
                    _LOGGER.debug(
                        "DI token refresh failed: %s", _sanitize_exception_text(err)
                    )
                return

            # JWT_WEB refresh via CAS TGT
            if not self.is_authenticated:
                return
            try:
                self.cs.get(
                    f"{self._sso}/mobile/sso/en_US/sign-in",
                    params={
                        "clientId": MOBILE_SSO_CLIENT_ID,
                        "service": self._mobile_sso_service_url,
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
                _LOGGER.debug("Refresh failed: %s", _sanitize_exception_text(err))

    def dumps(self) -> str:
        """Serialize session state to JSON string."""
        data: dict[str, Any] = {
            "di_token": self.di_token,
            "di_refresh_token": self.di_refresh_token,
            "di_client_id": self.di_client_id,
        }
        return json.dumps(data)

    def dump(self, path: str) -> None:
        """Write tokens safely to disk with owner-only permissions.

        The token file contains the DI refresh token, which grants persistent
        account access. It is written as 0o600 inside a 0o700 directory so a
        permissive process umask can't leave it world-readable on a shared host
        (GHSA-wjhr-76vg-2hvc).

        Writes to a sibling temporary file and atomically replaces the target so
        a concurrent reader never sees a truncated or partial token file.
        """
        p = token_file_path(path)
        # Serialize with token mutation so the serialized snapshot is consistent
        # (e.g. not torn across a concurrent refresh).
        with self._token_lock:
            payload = self.dumps()
        p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        # mkdir's mode is subject to umask and a no-op if the dir already
        # exists; chmod enforces 0o700 unconditionally.
        with contextlib.suppress(OSError):
            p.parent.chmod(0o700)
        # Open with O_CREAT|O_EXCL mode 0o600 (and O_NOFOLLOW where available)
        # instead of write_text, which would create the file under the umask
        # first. The temp name is unpredictable and O_EXCL is required (not
        # just O_TRUNC): a fixed sibling name is guessable, and without
        # O_EXCL a pre-planted file's inode would be reused for the write
        # instead of a fresh one being created, letting whoever holds a
        # descriptor on that pre-planted inode observe the token payload.
        tmp = p.with_name(f".{p.name}.{secrets.token_hex(8)}.tmp")
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(tmp, flags, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as token_file:
                token_file.write(payload)
            # Enforce 0o600 even if the file pre-existed with looser permissions.
            with contextlib.suppress(OSError):
                tmp.chmod(0o600)
            tmp.replace(p)
        except Exception:
            with contextlib.suppress(OSError):
                tmp.unlink()
            raise

    def load(self, path: str) -> None:
        """Read tokens from disk, refusing to follow symlinks.

        A pre-planted symlink must not redirect the read to an attacker-controlled
        file, so this mirrors the write-side hardening in ``dump()``.
        """
        try:
            self._tokenstore_path = path
            p = token_file_path(path)
            flags = os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(p, flags)
            with os.fdopen(fd, encoding="utf-8") as token_file:
                self.loads(token_file.read())
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
            _LOGGER.debug("Token extraction loads() structurally failed: %s", e)
            raise GarminConnectConnectionError(
                "Token extraction loads() structurally failed"
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
        try:
            self._complete_mfa(mfa_code)
            if self.verify_login and not self._verify_token():
                self._clear_auth_state()
                raise GarminConnectConnectionError(
                    "token rejected by API tier after MFA"
                )
            return None, None
        finally:
            # Always clear the pending MFA flag and per-attempt state so a new
            # login can start after resume_login() finishes (success or failure).
            self._mfa_pending = False
            for attr in (
                "_mfa_session",
                "_mfa_login_params",
                "_mfa_post_headers",
                "_mfa_service_url",
                "_mfa_flow",
                "_mfa_method",
                "_widget_last_resp",
            ):
                setattr(self, attr, None)

    def download(self, path: str, **kwargs: Any) -> bytes:
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update({"Accept": "*/*"})
        return self._run_request("GET", path, **kwargs).content

    def _run_request(self, method: str, path: str, **kwargs: Any) -> Any:
        with self._token_lock:
            if self.is_authenticated and self._token_expires_soon():
                self._refresh_session()

        # Defense-in-depth: callers must pass clean path components; query strings
        # belong in the `params` kwarg, not embedded in the path. Validate the
        # percent-decoded form: requests' requote_uri() decodes unreserved
        # characters (e.g. %2e -> .) after this check, so a literal-only match
        # would let a %2e%2e traversal slip through.
        decoded_path = unquote(path)
        # A quoted display name may legitimately contain a run of dots (e.g.
        # "first..last"); only a path *segment* that is exactly ".." (or
        # "..;<matrix-params>", a known filter-bypass trick) is traversal.
        has_traversal_segment = any(
            segment.split(";", 1)[0] == ".." for segment in decoded_path.split("/")
        )
        if (
            has_traversal_segment
            or "?" in decoded_path
            or "#" in decoded_path
            or "\\" in decoded_path
        ):
            raise ValueError(f"Invalid API path: {path!r}")

        url = f"{self._connectapi}/{path.lstrip('/')}"

        if "timeout" not in kwargs:
            kwargs["timeout"] = 15

        headers = self.get_api_headers()
        custom_headers = kwargs.pop("headers", {})
        headers.update(custom_headers)

        sess = self._api_session
        # Snapshot stream positions of any file bodies so a 401 retry can
        # rewind them; attempt #1 reads file handles to EOF, and re-sending
        # the same kwargs would otherwise upload an empty/truncated body.
        file_positions = _capture_file_positions(kwargs)
        resp = sess.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            with self._token_lock:
                self._refresh_session()
            if file_positions is not None and _restore_file_positions(file_positions):
                headers = self.get_api_headers()
                headers.update(custom_headers)
                resp = sess.request(method, url, headers=headers, **kwargs)
            else:
                # Unseekable/unrewindable file body: retrying would silently
                # send an empty part. Fall through so the 401 raises below.
                _LOGGER.debug("Skipping 401 retry: request body is not rewindable")

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
            safe_detail = ""
            try:
                error_data = resp.json()
                if isinstance(error_data, dict):
                    safe_detail = (
                        error_data.get("message")
                        or error_data.get("content")
                        or error_data.get("detailedImportResult", {})
                        .get("failures", [{}])[0]
                        .get("messages", [""])[0]
                    ) or ""
            except Exception as e:
                _LOGGER.debug("Could not extract safe error detail: %s", e)
            if safe_detail:
                error_msg += f" - {safe_detail}"
            _LOGGER.debug(
                "API error response: status=%s body=%r", resp.status_code, resp.text
            )
            # A 404 is a missing resource, not a connectivity failure.
            if resp.status_code == 404:
                raise GarminConnectNotFoundError(error_msg)
            raise GarminConnectConnectionError(error_msg)

        return resp
