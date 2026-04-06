"""Garmin Connect authentication test script.

Uses Playwright (headless Chromium) to replicate the exact browser
authentication flow, including Cloudflare JS challenge resolution.

Flow (from HAR capture):
  1. Navigate to SSO sign-in page (CF challenge solved automatically)
  2. POST credentials via fetch() inside the page context
  3. POST MFA code via fetch()
  4. Navigate to ticket URL to establish session (JWT_WEB cookie)
  5. Exchange service ticket for DI Bearer tokens (native API auth)
  6. Verify session with test API calls

Usage:
    python garmin_auth_test.py --email EMAIL --password PASSWORD
    python garmin_auth_test.py  (prompts interactively)

The username and password in this script are placeholders.
Supply your own real credentials at runtime.
"""

import argparse
import base64
import getpass
import json
import logging
import re
import sys
import time
from typing import Any

import requests

try:
    from curl_cffi import requests as cffi_requests

    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

from playwright.sync_api import sync_playwright, Page, BrowserContext

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-25s %(levelname)-7s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("garmin_auth")
# Quiet noisy loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SSO_BASE = "https://sso.garmin.com"
CONNECT_BASE = "https://connect.garmin.com"
CONNECTAPI_BASE = "https://connectapi.garmin.com"

PORTAL_CLIENT_ID = "GarminConnect"
PORTAL_SERVICE_URL = "https://connect.garmin.com/app"

SIGNIN_URL = (
    f"{SSO_BASE}/portal/sso/en-US/sign-in"
    f"?clientId={PORTAL_CLIENT_ID}"
    f"&service={PORTAL_SERVICE_URL}"
)
LOGIN_API = (
    f"{SSO_BASE}/portal/api/login"
    f"?clientId={PORTAL_CLIENT_ID}&locale=en-US"
    f"&service={PORTAL_SERVICE_URL}"
)
MFA_API = (
    f"{SSO_BASE}/portal/api/mfa/verifyCode"
    f"?clientId={PORTAL_CLIENT_ID}&locale=en-US"
    f"&service={PORTAL_SERVICE_URL}"
)

# DI OAuth2 token exchange
DI_TOKEN_URL = "https://diauth.garmin.com/di-oauth2-service/oauth/token"
DI_GRANT_TYPE = (
    "https://connectapi.garmin.com/di-oauth2-service/oauth/grant/service_ticket"
)
DI_CLIENT_IDS = (
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2024Q4",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI",
)

NATIVE_API_USER_AGENT = "GCM-Android-5.23"
NATIVE_X_GARMIN_USER_AGENT = (
    "com.garmin.android.apps.connectmobile/5.23; ; "
    "Google/sdk_gphone64_arm64/google; Android/33; Dalvik/2.1.0"
)


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


def _build_basic_auth(client_id: str) -> str:
    return "Basic " + base64.b64encode(f"{client_id}:".encode()).decode()


# ---------------------------------------------------------------------------
# Playwright-based auth flow
# ---------------------------------------------------------------------------

def _js_fetch_json(page: Page, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Execute a fetch() call inside the browser page context.

    This ensures all Cloudflare cookies (cf_clearance, __cf_bm, etc.)
    are sent automatically, exactly as the real browser would.
    """
    # Serialize payload for injection into JS
    payload_json = json.dumps(payload)
    script = f"""
    async () => {{
        const resp = await fetch("{url}", {{
            method: "POST",
            headers: {{
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
            }},
            body: JSON.stringify({payload_json}),
            credentials: "same-origin",
        }});
        const text = await resp.text();
        return {{ status: resp.status, body: text }};
    }}
    """
    result = page.evaluate(script)
    status = result["status"]
    body_text = result["body"]

    log.info("  fetch() status: %d", status)
    log.debug("  Response body: %s", body_text[:500])

    if status == 429:
        raise RuntimeError(f"429 Rate Limited. Response: {body_text[:300]}")
    if status == 403:
        raise RuntimeError(f"403 Forbidden. Response: {body_text[:300]}")

    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Non-JSON response (HTTP {status}): {body_text[:300]}"
        )


def step1_navigate_signin(page: Page) -> None:
    """Navigate to the SSO sign-in page and wait for Cloudflare challenge."""
    log.info("Step 1: Navigating to SSO sign-in page...")
    page.goto(SIGNIN_URL, wait_until="networkidle", timeout=30000)
    log.info("  Page loaded: %s", page.url[:80])

    # Check for Cloudflare challenge page
    title = page.title()
    if "Just a moment" in title:
        log.info("  Cloudflare challenge detected — waiting for resolution...")
        page.wait_for_function(
            "document.title !== 'Just a moment...'", timeout=15000
        )
        log.info("  Challenge resolved. Title: %s", page.title())

    log.info("  Sign-in page ready")


def step2_post_login(page: Page, email: str, password: str) -> dict[str, Any]:
    """POST credentials via in-page fetch()."""
    log.info("Step 2: Submitting credentials via fetch()...")
    payload = {
        "username": email,
        "password": password,
        "rememberMe": False,
        "captchaToken": "",
    }
    res = _js_fetch_json(page, LOGIN_API, payload)

    resp_type = res.get("responseStatus", {}).get("type")
    log.info("  Response type: %s", resp_type)

    if resp_type == "INVALID_USERNAME_PASSWORD":
        raise RuntimeError("Invalid username or password.")

    if resp_type not in ("MFA_REQUIRED", "SUCCESSFUL"):
        raise RuntimeError(f"Unexpected login response: {json.dumps(res)[:500]}")

    return res


def step3_verify_mfa(
    page: Page, mfa_code: str, mfa_method: str = "email"
) -> dict[str, Any]:
    """POST MFA verification code via in-page fetch()."""
    log.info("Step 3: Submitting MFA code (method=%s)...", mfa_method)
    payload = {
        "mfaMethod": mfa_method,
        "mfaVerificationCode": mfa_code,
        "rememberMyBrowser": True,
        "reconsentList": [],
        "mfaSetup": False,
    }
    res = _js_fetch_json(page, MFA_API, payload)

    resp_type = res.get("responseStatus", {}).get("type")
    log.info("  Response type: %s", resp_type)

    if resp_type != "SUCCESSFUL":
        raise RuntimeError(f"MFA verification failed: {resp_type} — {res}")

    return res


def step4_redeem_ticket(
    page: Page, context: BrowserContext, ticket: str
) -> tuple[str | None, str | None]:
    """Navigate to the ticket URL to establish the web session."""
    log.info("Step 4: Redeeming service ticket: %s...", ticket[:30])
    ticket_url = f"{CONNECT_BASE}/app?ticket={ticket}"
    page.goto(ticket_url, wait_until="networkidle", timeout=30000)
    log.info("  Page loaded: %s", page.url[:80])

    # Extract JWT_WEB from browser cookies
    jwt_web = None
    cookies = context.cookies()
    for c in cookies:
        if c["name"] == "JWT_WEB":
            jwt_web = c["value"]
            log.info("  JWT_WEB cookie obtained (%d chars)", len(jwt_web))
            break

    if not jwt_web:
        log.warning("  JWT_WEB cookie NOT found")
        cookie_names = [c["name"] for c in cookies]
        log.debug("  Available cookies: %s", cookie_names)

    # Extract CSRF token from page HTML
    csrf_token = None
    try:
        csrf_token = page.evaluate(
            '() => document.querySelector(\'meta[name="csrf-token"]\')?.content'
        )
        if csrf_token:
            log.info("  CSRF token: %s", csrf_token)
    except Exception:
        pass

    if not csrf_token:
        log.warning("  CSRF token not found in page")

    return jwt_web, csrf_token


def step5_exchange_di_token(
    ticket: str,
) -> tuple[str | None, str | None, str | None]:
    """Exchange the service ticket for native DI Bearer tokens."""
    log.info("Step 5: Exchanging service ticket for DI Bearer tokens...")

    for client_id in DI_CLIENT_IDS:
        log.debug("  Trying DI client_id: %s", client_id)
        headers = _native_headers(
            {
                "Authorization": _build_basic_auth(client_id),
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cache-Control": "no-cache",
            }
        )
        data = {
            "client_id": client_id,
            "service_ticket": ticket,
            "grant_type": DI_GRANT_TYPE,
            "service_url": PORTAL_SERVICE_URL,
        }

        if HAS_CFFI:
            r = cffi_requests.post(
                DI_TOKEN_URL,
                headers=headers,
                data=data,
                impersonate="chrome",
                timeout=30,
            )
        else:
            r = requests.post(DI_TOKEN_URL, headers=headers, data=data, timeout=30)

        log.debug("  Status: %d", r.status_code)

        if r.status_code == 429:
            log.error("  DI token exchange rate limited!")
            raise RuntimeError("DI token exchange returned 429")

        if not r.ok:
            log.debug("  Failed: %d %s", r.status_code, r.text[:200])
            continue

        try:
            token_data = r.json()
            di_token = token_data["access_token"]
            di_refresh = token_data.get("refresh_token")

            di_client_id = client_id
            try:
                parts = di_token.split(".")
                if len(parts) >= 2:
                    payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
                    payload = json.loads(
                        base64.urlsafe_b64decode(payload_b64).decode()
                    )
                    if payload.get("client_id"):
                        di_client_id = payload["client_id"]
            except Exception:
                pass

            log.info(
                "  DI token obtained (client_id=%s, token=%d chars)",
                di_client_id,
                len(di_token),
            )
            return di_token, di_refresh, di_client_id
        except Exception as e:
            log.debug("  Parse failed: %s", e)
            continue

    log.warning("  DI token exchange failed for all client IDs")
    return None, None, None


def step6_test_api(
    jwt_web: str | None,
    csrf_token: str | None,
    di_token: str | None,
) -> None:
    """Verify authentication by making test API calls."""
    log.info("Step 6: Testing authenticated API access...")

    if jwt_web:
        log.info("  Testing JWT_WEB cookie auth...")
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "NK": "NT",
            "X-Requested-With": "XMLHttpRequest",
            "X-App-Ver": "5.23.0.33",
            "X-Lang": "en-US",
            "Cookie": f"JWT_WEB={jwt_web}",
        }
        if csrf_token:
            headers["connect-csrf-token"] = csrf_token

        url = f"{CONNECT_BASE}/gc-api/userprofile-service/userprofile/user-settings/"
        r = requests.get(url, headers=headers, timeout=15)
        log.info("    user-settings: %d", r.status_code)
        if r.ok:
            data = r.json()
            log.info("    Display name: %s", data.get("displayName", "N/A"))
            log.info("    JWT_WEB AUTH: SUCCESS")
        else:
            log.warning("    JWT_WEB AUTH: FAILED (%d)", r.status_code)

    if di_token:
        log.info("  Testing DI Bearer token auth...")
        headers = _native_headers(
            {
                "Authorization": f"Bearer {di_token}",
                "Accept": "application/json",
            }
        )
        url = f"{CONNECTAPI_BASE}/userprofile-service/userprofile/user-settings/"
        r = requests.get(url, headers=headers, timeout=15)
        log.info("    user-settings: %d", r.status_code)
        if r.ok:
            data = r.json()
            log.info("    Display name: %s", data.get("displayName", "N/A"))
            log.info("    DI BEARER AUTH: SUCCESS")
        else:
            log.warning("    DI BEARER AUTH: FAILED (%d)", r.status_code)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test Garmin Connect authentication flow"
    )
    parser.add_argument("--email", help="Garmin account email")
    parser.add_argument("--password", help="Garmin account password")
    parser.add_argument(
        "--dump-tokens",
        metavar="PATH",
        help="Write DI tokens to JSON file (loadable by garminconnect library)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (visible window) for debugging",
    )
    args = parser.parse_args()

    email = args.email or input("Email: ")
    password = args.password or getpass.getpass("Password: ")

    log.info("=" * 60)
    log.info("Garmin Connect Authentication Test (Playwright)")
    log.info("=" * 60)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        page = context.new_page()

        # Step 1: Navigate to sign-in page (solves CF challenge)
        step1_navigate_signin(page)
        time.sleep(1)

        # Step 2: Submit credentials
        login_result = step2_post_login(page, email, password)
        resp_type = login_result.get("responseStatus", {}).get("type")

        ticket = None
        if resp_type == "MFA_REQUIRED":
            mfa_info = login_result.get("customerMfaInfo", {})
            mfa_method = mfa_info.get("mfaLastMethodUsed", "email")
            log.info(
                "MFA required (method: %s). Check your email for the code.",
                mfa_method,
            )
            time.sleep(1)

            mfa_code = input("Enter MFA code: ").strip()
            mfa_result = step3_verify_mfa(page, mfa_code, mfa_method)
            ticket = mfa_result.get("serviceTicketId")
        elif resp_type == "SUCCESSFUL":
            ticket = login_result.get("serviceTicketId")

        if not ticket:
            raise RuntimeError("No service ticket received!")
        log.info("Service ticket: %s", ticket)
        time.sleep(1)

        # Step 4: Redeem ticket for JWT_WEB
        jwt_web, csrf_token = step4_redeem_ticket(page, context, ticket)

        # Step 5: Exchange ticket for DI Bearer tokens
        di_token, di_refresh, di_client_id = step5_exchange_di_token(ticket)

        # Close browser — no longer needed
        browser.close()

    # Step 6: Test API access
    log.info("")
    step6_test_api(jwt_web, csrf_token, di_token)

    # Summary
    log.info("")
    log.info("=" * 60)
    log.info("AUTHENTICATION SUMMARY")
    log.info("=" * 60)
    log.info("  JWT_WEB:       %s", "OK" if jwt_web else "MISSING")
    log.info("  CSRF Token:    %s", "OK" if csrf_token else "MISSING")
    log.info("  DI Token:      %s", "OK" if di_token else "MISSING")
    log.info("  DI Refresh:    %s", "OK" if di_refresh else "MISSING")
    log.info("  DI Client ID:  %s", di_client_id or "N/A")

    if args.dump_tokens and di_token:
        token_data = {
            "di_token": di_token,
            "di_refresh_token": di_refresh,
            "di_client_id": di_client_id,
        }
        with open(args.dump_tokens, "w") as f:
            json.dump(token_data, f, indent=2)
        log.info("Tokens written to %s", args.dump_tokens)
        log.info(
            "Load in garminconnect: api.client.loads(open('%s').read())",
            args.dump_tokens,
        )


if __name__ == "__main__":
    main()
