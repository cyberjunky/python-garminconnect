"""Constants shared by the Garmin Connect client modules.

Everything that identifies this client to Garmin (client IDs, user agents,
service URLs), the anti-WAF timing bounds and the regular expressions used to
parse SSO pages live here so the login, session and transport modules do not
each carry their own copy.
"""

import re

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
# Mobile flow: the pause between loading the sign-in page and submitting it.
MOBILE_DELAY_MIN_S = 2.0
MOBILE_DELAY_MAX_S = 5.0

# -- TLS impersonation profiles --
MOBILE_IMPERSONATIONS: tuple[str, ...] = ("safari_ios", "safari", "chrome120")
PORTAL_IMPERSONATIONS: tuple[str, ...] = (
    "safari",
    "safari_ios",
    "chrome120",
    "edge101",
    "chrome",
)

# -- Native API (connectapi) identity --
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

# A 401 from the API tier means the token itself is refused, but a 403 can
# also mean Garmin is blocking the client or network making the call, in
# which case the token may be fine and the "token rejected" wording misleads.
_API_REJECTION_HINT = (
    "a 403 here can also mean Garmin is blocking this client or network "
    "rather than rejecting the token"
)
# _run_request() errors start with "API Error <status>"; read the status from
# that prefix rather than searching the whole message, whose detail text can
# contain other numbers.
_API_ERROR_STATUS_RE = re.compile(r"^API Error (\d{3})\b")

# Detect ~username expansion that would point into another user's home directory.
_OTHER_USER_HOME_RE = re.compile(r"^~[^/\\]")

# Query values (e.g. ?ticket=ST-...) that must never reach logs or messages.
_QUERY_VALUE_RE = re.compile(r"([?&][\w.-]+=)[^&\s)'\"]+")

# -- Regex helpers for HTML parsing (widget flow) --
_CSRF_RE = re.compile(r'name="_csrf"\s+value="(.+?)"')
_TITLE_RE = re.compile(r"<title>(.+?)</title>")
_TICKET_RE = re.compile(r'\?ticket=(ST-[^"&\s]+)')
# Garmin's widget MFA page exposes these variables in inline <script> tags.
_WIDGET_MFA_VARS_RE = re.compile(
    r'var\s+(customerGuid|mfaMethod|locale|clientId|codeSentTo)\s*=\s*"([^"]*)"\s*;'
)
