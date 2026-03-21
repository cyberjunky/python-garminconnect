#!/usr/bin/env python3
"""Garmin 429 IP Bypass via Free HTTPS Proxy.
Use this script if your home IP is aggressively rate-limited (429) by Garmin.
It securely tunnels the initial authentication handshake through a random HTTPS proxy.
"""

import asyncio
import getpass
import logging
import os
import random
import urllib.request

from curl_cffi import requests

from aiogarmin.auth import CLIENT_ID, SSO_SERVICE_URL, GarminAuth
from aiogarmin.exceptions import GarminAuthError, GarminMFARequired

_LOGGER = logging.getLogger(__name__)

# Token storage file
TOKEN_FILE = ".garmin_tokens.json"


async def proxy_login(auth_obj, email, password):
    # 1. Fetch free anonymous HTTPS proxies
    print("Fetching free anonymous proxy list to bypass Garmin's IP ban...")
    try:
        url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        proxies_list = (
            urllib.request.urlopen(url).read().decode("utf-8").strip().split("\n")
        )
        # Shuffle to pick random proxies instead of hitting the first ones!
        random.shuffle(proxies_list)
    except Exception as e:
        print(f"Failed to fetch proxy list: {e}")
        return False

    print(f"Found {len(proxies_list)} proxies. Finding a working one...")

    # 2. Iterate until we find one that Cloudflare and Garmin likes
    working_proxy = None
    sess = requests.Session(impersonate="chrome131_android", timeout=10)
    sess.headers = {
        "User-Agent": "com.garmin.android.apps.connectmobile",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for proxy in proxies_list[:50]:
        proxy = proxy.strip()
        px = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            # We are sending HTTPS traffic through the proxy, so it's perfectly end-to-end encrypted.
            # The proxy provider physically cannot read your password.
            r = sess.get(
                "https://sso.garmin.com/mobile/sso/en/sign-in",
                params={"clientId": CLIENT_ID},
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                },
                proxies=px,
            )
            if r.status_code == 200:
                print(f"   -> Proxy {proxy} is alive and bypassed WAF!")
                working_proxy = px
                break
        except Exception:
            continue

    if not working_proxy:
        print("Could not find a fast proxy. Try again later.")
        return False

    print("3. Executing Mobile JSON Login via Proxy...")
    r = sess.post(
        "https://sso.garmin.com/mobile/api/login",
        params={"clientId": CLIENT_ID, "locale": "en-US", "service": SSO_SERVICE_URL},
        json={
            "username": email,
            "password": password,
            "rememberMe": False,
            "captchaToken": "",
        },
        proxies=working_proxy,
    )

    res = r.json()
    resp_type = res.get("responseStatus", {}).get("type")

    if resp_type == "MFA_REQUIRED":
        print("\n[!] MFA Required! Check your phone/email.")
        auth_obj._mfa_method = res.get("customerMfaInfo", {}).get(
            "mfaLastMethodUsed", "email"
        )
        auth_obj._mfa_session = sess
        auth_obj._mfa_proxy = working_proxy  # Save proxy for MFA stage
        raise GarminMFARequired("mfa_required")

    if "status-code" in res.get("error", {}) and res["error"]["status-code"] == "429":
        print(
            f"Proxy was ALSO rate limited by Garmin. This means Garmin blocked entire subnets globally. {res}"
        )
        return False

    if resp_type == "SUCCESSFUL":
        ticket = res["serviceTicketId"]
        return await auth_obj._establish_session(ticket)

    print(f"Login failed: {res}")
    return False


# We monkey-patch the complete_mfa to ALSO use the proxy securely
async def proxy_mfa(auth_obj, code):
    r = auth_obj._mfa_session.post(
        "https://sso.garmin.com/mobile/api/mfa/verifyCode",
        params={"clientId": CLIENT_ID, "locale": "en-US", "service": SSO_SERVICE_URL},
        json={
            "mfaMethod": auth_obj._mfa_method,
            "mfaVerificationCode": code,
            "rememberMyBrowser": False,
            "reconsentList": [],
            "mfaSetup": False,
        },
        proxies=getattr(auth_obj, "_mfa_proxy", None),
    )
    res = r.json()
    if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
        ticket = res["serviceTicketId"]
        # Establish session completely bypasses Proxy and returns to your main clean IP
        return await auth_obj._establish_session(ticket)
    raise GarminAuthError(f"MFA Verification failed via proxy: {res}")


async def main():
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email:
        email = input("Garmin Email: ")
    if not password:
        password = getpass.getpass("Garmin Password: ")

    auth = GarminAuth()

    # Check if existing session on disk works
    if auth.load_session(TOKEN_FILE):
        print("Session securely loaded from disk! No login needed.")
        return

    try:
        await proxy_login(auth, email, password)
    except GarminMFARequired:
        code = input("MFA Code: ")
        await proxy_mfa(auth, code)
    except Exception as e:
        print(f"Login interrupted: {e}")
        return

    if auth.is_authenticated:
        print("\nSUCCESS! Successfully injected JWT_WEB and CSRF via proxy evasion!")
        auth.save_session(TOKEN_FILE)
        print(f"Tokens saved permanently to {TOKEN_FILE}.")
        print("\nTesting natively on your local IP against GC-API...")
        try:
            r_devs = await asyncio.to_thread(
                auth.api_request, "GET", "device-service/deviceregistration/devices"
            )
            print(f"Devices found securely via local IP: {len(r_devs)}")
        except Exception as e:
            print(f"Post-auth validation failed. {e}")


if __name__ == "__main__":
    asyncio.run(main())
