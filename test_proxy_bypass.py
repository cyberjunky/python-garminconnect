#!/usr/bin/env python3
"""Garmin 429 IP Bypass via Free HTTPS Proxy.
Use this script if your home IP is aggressively rate-limited (429) by Garmin.
It securely tunnels the initial authentication handshake through a random HTTPS proxy.
"""
# ruff: noqa: T201, S310, S105, S112, S110, TRY002, D103, PTH110, D415, D400

import contextlib
import getpass
import logging
import os
import random
import traceback
import urllib.request
from typing import Optional

import requests

from garminconnect.client import CLIENT_ID, SSO_SERVICE_URL, Client, GarthHTTPError

_LOGGER = logging.getLogger(__name__)

# Token storage file
TOKEN_FILE = "~/.garminconnect/.garmin_tokens.json"

SESSION_UA = "GCM-iOS-5.22.1.4"
SSO_PAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Site": "none",
}

def proxy_login(auth_obj: Client, email: str, password: str) -> bool:
    try:
        url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        proxies_list = (
            urllib.request.urlopen(url).read().decode("utf-8").strip().split("\n")
        )
        random.shuffle(proxies_list)
    except Exception:
        return False

    sess = requests.Session()
    print(f"Testing {len(proxies_list)} proxies to bypass Garmin's rate limits...")
    
    for proxy in proxies_list[:50]:
        proxy = proxy.strip()
        px = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            r_get = sess.get(
                "https://sso.garmin.com/mobile/sso/en/sign-in",
                params={"clientId": CLIENT_ID},
                headers=SSO_PAGE_HEADERS,
                proxies=px,
                timeout=10
            )
            if r_get.status_code != 200:
                continue

            r = sess.post(
                "https://sso.garmin.com/mobile/api/login",
                params={"clientId": CLIENT_ID, "locale": "en-US", "service": SSO_SERVICE_URL},
                json={
                    "username": email,
                    "password": password,
                    "rememberMe": False,
                    "captchaToken": "",
                },
                headers=SSO_PAGE_HEADERS,
                proxies=px,
                timeout=10
            )

            try:
                res = r.json()
            except Exception:
                continue

            resp_type = res.get("responseStatus", {}).get("type")

            if resp_type == "MFA_REQUIRED":
                print(f"Proxy {proxy} works and requires MFA!")
                auth_obj._mfa_method = res.get("customerMfaInfo", {}).get(
                    "mfaLastMethodUsed", "email"
                )
                auth_obj._mfa_session = sess
                auth_obj._mfa_proxy = px  # Save proxy for MFA stage
                raise Exception("mfa_required")

            if "status-code" in res.get("error", {}) and res["error"]["status-code"] == "429":
                print(f"Proxy {proxy} blocked by Garmin (429 Rate Limit). Trying next...")
                continue

            if resp_type == "SUCCESSFUL":
                print(f"Proxy {proxy} successfully logged in!")
                ticket = res["serviceTicketId"]
                auth_obj._establish_session(ticket) # Doesn't use proxy for API tokens natively!
                return True

        except Exception as e:
            if str(e) == "mfa_required":
                raise
            continue

    print("Failed to find any working proxy that allows Garmin logins.")
    return False

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
        headers=SSO_PAGE_HEADERS,
        timeout=10
    )
    res = r.json()
    if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
        ticket = res["serviceTicketId"]
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
    try:
        auth.load("~/.garminconnect")
        if auth.is_authenticated:
            print("Already logged in via existing ~/.garminconnect file.")
            return
    except Exception:
        pass

    print("Attempting proxy login execution to fetch fresh session cookies...")
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
        auth.dump("~/.garminconnect")
        print(f"Success! Session safely persisted to ~/.garminconnect")
        print("You can now securely run ./demo.py using identically native requests!")


if __name__ == "__main__":
    main()
