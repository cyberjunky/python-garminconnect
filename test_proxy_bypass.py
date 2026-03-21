#!/usr/bin/env python3
# ruff: noqa: T201, S310, S105, S112, S110, TRY002, D103, PTH110, D415, D400, C418, PLW2901
"""Garmin 429 IP Bypass via Free HTTPS Proxy.
Use this script if your home IP is aggressively rate-limited (429) by Garmin.
It securely tunnels the initial authentication handshake through a random HTTPS proxy.
"""

import getpass
import logging
import os
import random
import traceback
import urllib.request

from curl_cffi import requests

from garminconnect.client import CLIENT_ID, SSO_SERVICE_URL, Client, GarthHTTPError

_LOGGER = logging.getLogger(__name__)

# Token storage file
TOKEN_FILE = ".garmin_tokens.json"


def proxy_login(auth_obj: Client, email: str, password: str) -> bool:
    """1. Fetch free anonymous HTTPS proxies"""
    try:
        url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        proxies_list = (
            urllib.request.urlopen(url).read().decode("utf-8").strip().split("\n")
        )
        # Shuffle to pick random proxies instead of hitting the first ones!
        random.shuffle(proxies_list)
    except Exception:
        return False

    # 2. Iterate until we find one that Cloudflare and Garmin likes
    working_proxy = None
    sess = requests.Session(impersonate="chrome131_android", timeout=10)
    sess.headers = dict(
        {
            "User-Agent": "com.garmin.android.apps.connectmobile",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    print(f"Testing {len(proxies_list)} proxies to bypass Garmin's rate limits...")
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
                working_proxy = px
                print(f"Proxy {proxy} is working!")
                break
        except Exception:
            continue

    if not working_proxy:
        print("Failed to find a working proxy.")
        return False

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

    try:
        res = r.json()
    except Exception:
        return False

    resp_type = res.get("responseStatus", {}).get("type")

    if resp_type == "MFA_REQUIRED":
        auth_obj._mfa_method = res.get("customerMfaInfo", {}).get(
            "mfaLastMethodUsed", "email"
        )
        auth_obj._mfa_session = sess
        auth_obj._mfa_proxy = working_proxy  # Save proxy for MFA stage
        raise Exception("mfa_required")

    if "status-code" in res.get("error", {}) and res["error"]["status-code"] == "429":
        print("Proxy failed: 429 Rate Limit from Garmin.")
        return False

    if resp_type == "SUCCESSFUL":
        ticket = res["serviceTicketId"]
        auth_obj._establish_session(ticket)
        return True

    return False


# We monkey-patch the complete_mfa to ALSO use the proxy securely
def proxy_mfa(auth_obj: Client, code: str) -> None:
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
        auth_obj._establish_session(ticket)
        return
    raise GarthHTTPError(Exception(f"MFA Verification failed via proxy: {res}"))


def main():
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email:
        email = input("Garmin Email: ")
    if not password:
        password = getpass.getpass("Garmin Password: ")

    auth = Client()

    # Check if existing session on disk works
    if os.path.exists(TOKEN_FILE):
        try:
            auth.load(TOKEN_FILE)
            if auth.is_authenticated:
                print("Already logged in via existing .garmin_tokens.json file.")
                return
        except Exception:
            pass

    print("Attempting proxy login execution...")
    try:
        if proxy_login(auth, email, password):
            print("Successfully established proxy login bypass!")
        else:
            print("Proxy login failed.")
            return
    except Exception as e:
        if str(e) == "mfa_required":
            code = input("MFA Code (sent to email/SMS): ")
            proxy_mfa(auth, code)
        else:
            traceback.print_exc()
            return

    if auth.is_authenticated:
        auth.dump(TOKEN_FILE)
        print(f"Success! Session safely persisted to {TOKEN_FILE}")
        print("You can now securely use python-garminconnect demo.py normally.")


if __name__ == "__main__":
    main()
