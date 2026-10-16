"""Authentication and transport client for Garmin Connect.

The client is split by concern:

- :mod:`.constants` — client identities, URLs, timing bounds, regexes
- :mod:`.sso` — the five login strategies and MFA completion
- :mod:`.session` — CAS ticket → DI token (or JWT_WEB) exchange and refresh
- :mod:`.tokens` — token persistence and JWT inspection
- :mod:`.transport` — authenticated requests to the API tier

``Client`` assembles those mixins; everything that used to live in the single
``garminconnect.client`` module is still importable from here.
"""

import http.cookiejar
import logging
import os  # noqa: F401  (re-exported: callers patch garminconnect.client.os)
import threading
import time  # noqa: F401  (re-exported: callers patch garminconnect.client.time)
from typing import Any

import requests
from requests.adapters import HTTPAdapter

# Optional dependencies are imported exactly once, here, and read through the
# package by the submodules so a single assignment (or test patch) controls
# them everywhere.
try:
    from curl_cffi import requests as cffi_requests  # noqa: F401  (used via package)

    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

try:
    from ua_generator import generate as _generate_ua  # noqa: F401  (used via package)

    HAS_UA_GEN = True
except ImportError:
    HAS_UA_GEN = False

# The single-module client imported these, so callers could import them from
# garminconnect.client; they stay importable from here.
from ..exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectNotFoundError,
    GarminConnectTooManyRequestsError,
)
from .constants import (
    _API_ERROR_STATUS_RE,
    _API_REJECTION_HINT,
    _CSRF_RE,
    _OTHER_USER_HOME_RE,
    _QUERY_VALUE_RE,
    _TITLE_RE,
    _WIDGET_MFA_VARS_RE,
    ALLOWED_DOMAINS,
    DESKTOP_USER_AGENT,
    DI_CLIENT_IDS,
    DI_GRANT_TYPE,
    DI_TOKEN_URL,
    IOS_LOGIN_UA,
    IOS_SERVICE_URL,
    IOS_SSO_CLIENT_ID,
    LOGIN_DELAY_MAX_S,
    LOGIN_DELAY_MIN_S,
    MOBILE_IMPERSONATIONS,
    MOBILE_SSO_CLIENT_ID,
    MOBILE_SSO_SERVICE_URL,
    MOBILE_SSO_USER_AGENT,
    NATIVE_API_USER_AGENT,
    NATIVE_X_GARMIN_USER_AGENT,
    PORTAL_IMPERSONATIONS,
    PORTAL_SSO_CLIENT_ID,
    PORTAL_SSO_SERVICE_URL,
    WIDGET_DELAY_MAX_S,
    WIDGET_DELAY_MIN_S,
)
from .session import SessionMixin
from .sso import (
    LoginMixin,
    _MFARequired,
    _parse_widget_mfa_vars,
    _random_browser_headers,
)
from .tokens import (
    TokenStoreMixin,
    _build_basic_auth,
    _decode_jwt_payload,
    token_file_path,
)
from .transport import (
    ApiTransportMixin,
    _capture_file_positions,
    _iter_file_objects,
    _native_headers,
    _restore_file_positions,
    _sanitize_exception_text,
)

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "ALLOWED_DOMAINS",
    "DESKTOP_USER_AGENT",
    "DI_CLIENT_IDS",
    "DI_GRANT_TYPE",
    "DI_TOKEN_URL",
    "HAS_CFFI",
    "HAS_UA_GEN",
    "IOS_LOGIN_UA",
    "IOS_SERVICE_URL",
    "IOS_SSO_CLIENT_ID",
    "LOGIN_DELAY_MAX_S",
    "LOGIN_DELAY_MIN_S",
    "MOBILE_IMPERSONATIONS",
    "MOBILE_SSO_CLIENT_ID",
    "MOBILE_SSO_SERVICE_URL",
    "MOBILE_SSO_USER_AGENT",
    "NATIVE_API_USER_AGENT",
    "NATIVE_X_GARMIN_USER_AGENT",
    "PORTAL_IMPERSONATIONS",
    "PORTAL_SSO_CLIENT_ID",
    "PORTAL_SSO_SERVICE_URL",
    "WIDGET_DELAY_MAX_S",
    "WIDGET_DELAY_MIN_S",
    "_API_ERROR_STATUS_RE",
    "_API_REJECTION_HINT",
    "_CSRF_RE",
    "_OTHER_USER_HOME_RE",
    "_QUERY_VALUE_RE",
    "_TITLE_RE",
    "_WIDGET_MFA_VARS_RE",
    "Client",
    "GarminConnectAuthenticationError",
    "GarminConnectConnectionError",
    "GarminConnectNotFoundError",
    "GarminConnectTooManyRequestsError",
    # Private helpers kept importable for existing callers and tests.
    "_MFARequired",
    "_build_basic_auth",
    "_capture_file_positions",
    "_decode_jwt_payload",
    "_iter_file_objects",
    "_native_headers",
    "_parse_widget_mfa_vars",
    "_random_browser_headers",
    "_restore_file_positions",
    "_sanitize_exception_text",
    "token_file_path",
]


class Client(LoginMixin, SessionMixin, TokenStoreMixin, ApiTransportMixin):
    """A client to communicate with Garmin Connect."""

    def __init__(self, domain: str = "garmin.com", **kwargs: Any) -> None:
        if domain not in ALLOWED_DOMAINS:
            raise ValueError(
                f"Invalid domain {domain!r}; must be one of {sorted(ALLOWED_DOMAINS)}"
            )
        self.domain = domain
        self._domain = domain
        self._sso = f"https://sso.{domain}"
        self._connect = f"https://connect.{domain}"
        self._connectapi = f"https://connectapi.{domain}"
        # Service URLs are domain-aware for CN support
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
        self.di_token = None
        self.di_refresh_token = None
        self.di_client_id = None

        # JWT_WEB cookie auth (fallback when DI token exchange fails)
        self.jwt_web = None
        self.csrf_token = None

        pool_kwargs = {
            "pool_connections": kwargs.get("pool_connections", 20),
            "pool_maxsize": kwargs.get("pool_maxsize", 20),
        }
        # Plain session for JWT_WEB fallback and session refresh
        self.cs = requests.Session()
        self.cs.mount("https://", HTTPAdapter(**pool_kwargs))

        # Dedicated keep-alive session for API calls. Kept separate from
        # self.cs so auth cookies (JWT_WEB jar, CAS TGT) don't leak into API
        # requests — API auth travels in headers per-call via get_api_headers.
        # Reusing one session lets urllib3 pool TCP/TLS across calls instead
        # of doing a fresh handshake every request (~1 s saved per call).
        self._api_session = requests.Session()
        # Reject all cookies so server-set cookies can't accumulate in the jar
        # and collide with the explicit Cookie header used on the JWT_WEB path.
        # Matches the old fresh-session-per-call guarantee: empty cookie state.
        self._api_session.cookies.set_policy(
            http.cookiejar.DefaultCookiePolicy(allowed_domains=[])
        )
        self._api_session.mount("https://", HTTPAdapter(**pool_kwargs))

        self._tokenstore_path = None
        # Serialize token refresh and state mutation so concurrent API calls can't
        # race on the same refresh token or observe half-updated state.
        self._token_lock = threading.RLock()
        # True after login(return_on_mfa=True) returns "needs_mfa" until
        # resume_login() finishes. Prevents interleaving another login on the
        # same instance while MFA state is held on self.
        self._mfa_pending = False
        self._clear_mfa_pending_state()
        # Set of strategy names to skip during login, e.g. {"mobile+cffi"}.
        # Valid names: mobile+cffi, mobile+requests, widget+cffi,
        #              portal+cffi, portal+requests
        self.skip_strategies = set()
        # When True (default), each login strategy's token is validated against
        # the API tier before the chain accepts it; a token the API rejects
        # (401/403) is discarded and the next strategy is tried. Set False to
        # restore the legacy "first token wins" behavior.
        self.verify_login = kwargs.get("verify_login", True)
        # HTTP status (401/403) of the last _verify_token() rejection, so the
        # resulting error can tell a refused token from a blocked client.
        self._last_rejection_status = None
