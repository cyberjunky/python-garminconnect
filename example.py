#!/usr/bin/env python3
"""Simple Garmin Connect API Example.

Demonstrates authentication, token storage, and basic API calls.

For a comprehensive demo of all 127+ API methods, see demo.py

Dependencies:
    pip install garminconnect[example]
    pip install curl_cffi

Environment Variables (optional):
    export EMAIL=<your garmin email address>
    export PASSWORD=<your garmin password>
    export GARMINTOKENS=<path to token storage, default ~/.garminconnect>
"""

import contextlib
import logging
import os
import sys
from datetime import date
from getpass import getpass
from pathlib import Path

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

logging.getLogger("garminconnect").setLevel(logging.CRITICAL)


def safe_api_call(api_method, *args, **kwargs):
    """Call an API method and return (success, result, error_message)."""
    try:
        result = api_method(*args, **kwargs)
        return True, result, None

    except GarminConnectAuthenticationError as e:
        return False, None, f"Authentication error: {e}"
    except GarminConnectTooManyRequestsError as e:
        return False, None, f"Rate limit exceeded: {e}"
    except GarminConnectConnectionError as e:
        error_str = str(e)
        if "400" in error_str:
            return (
                False,
                None,
                "Not available (400) — feature may not be enabled for your account",
            )
        if "401" in error_str:
            return False, None, "Authentication required (401) — please re-authenticate"
        if "403" in error_str:
            return False, None, "Access denied (403) — account may not have permission"
        if "404" in error_str:
            return False, None, "Not found (404) — endpoint may have moved"
        if "429" in error_str:
            return False, None, "Rate limit (429) — please wait before retrying"
        if "500" in error_str:
            return False, None, "Server error (500) — Garmin servers are having issues"
        return False, None, f"Connection error: {e}"
    except Exception as e:
        return False, None, f"Unexpected error: {e}"


def init_api() -> Garmin | None:
    """Initialise Garmin API, restoring saved tokens or logging in fresh.

    Tokens are stored in ``~/.garminconnect/garmin_tokens.json``
    and reused automatically on the next run.  DI OAuth tokens include
    a refresh token so the session auto-renews without user interaction.
    """
    tokenstore = os.getenv("GARMINTOKENS", "~/.garminconnect")
    tokenstore_path = str(Path(tokenstore).expanduser())

    # Try to restore saved tokens
    try:
        garmin = Garmin()
        garmin.login(tokenstore_path)
        print("Logged in using saved tokens.")
        return garmin

    except GarminConnectTooManyRequestsError as err:
        print(f"Rate limit: {err}")
        sys.exit(1)

    except (GarminConnectAuthenticationError, GarminConnectConnectionError):
        print("No valid tokens found — please log in.")

    # Fresh credential login with MFA support
    while True:
        try:
            email = os.getenv("EMAIL") or input("Email: ").strip()
            password = os.getenv("PASSWORD") or getpass("Password: ")

            garmin = Garmin(
                email=email,
                password=password,
                prompt_mfa=lambda: input("MFA code: ").strip(),
            )
            garmin.login(tokenstore_path)
            print(f"Login successful. Tokens saved to: {tokenstore_path}")
            return garmin

        except GarminConnectTooManyRequestsError as err:
            print(f"Rate limit: {err}")
            sys.exit(1)

        except GarminConnectAuthenticationError:
            print("Wrong credentials — please try again.")
            continue

        except GarminConnectConnectionError as err:
            print(f"Connection error: {err}")
            return None

        except KeyboardInterrupt:
            return None


def main():
    """Basic usage example."""
    api = init_api()
    if not api:
        return

    today = date.today().isoformat()

    success, summary, err = safe_api_call(api.get_user_summary, today)
    if success and summary:
        print(f"Steps today : {summary.get('totalSteps', 0)}")
        print(f"Calories    : {summary.get('totalKilocalories', 0):.0f} kcal")
        dist_km = summary.get("totalDistanceMeters", 0) / 1000
        print(f"Distance    : {dist_km:.2f} km")
    elif err:
        print(f"Could not fetch summary: {err}")

    success, hr, err = safe_api_call(api.get_heart_rates, today)
    if success and hr:
        print(f"Resting HR  : {hr.get('restingHeartRate', 'n/a')} bpm")
    elif err:
        print(f"Could not fetch heart rate: {err}")


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        main()
