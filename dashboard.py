#!/usr/bin/env python3
"""Personal Garmin Connect dashboard.

A small local web app showing today's health summary, recent daily
metrics, and recent activities, using the garminconnect library.

Dependencies:
    pip install garminconnect curl_cffi flask

Environment Variables (optional):
    export EMAIL=<your garmin email address>
    export PASSWORD=<your garmin password>
    export GARMINTOKENS=<path to token storage, default ~/.garminconnect>

Run:
    python3 dashboard.py
    # then open http://127.0.0.1:5000
"""

import logging
import os
import sys
from datetime import date, timedelta
from getpass import getpass
from pathlib import Path

from flask import Flask, render_template

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

logging.getLogger("garminconnect").setLevel(logging.CRITICAL)

app = Flask(__name__)
DAYS_HISTORY = 7


def init_api() -> Garmin | None:
    """Authenticate with Garmin Connect, reusing saved tokens if available."""
    tokenstore = os.getenv("GARMINTOKENS", "~/.garminconnect")
    tokenstore_path = str(Path(tokenstore).expanduser())

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


def safe_call(fn, *args, default=None):
    try:
        return fn(*args)
    except Exception as e:
        print(f"Warning: {fn.__name__} failed: {e}")
        return default


def build_daily_history(api: Garmin, days: int) -> list[dict]:
    history = []
    for i in range(days - 1, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        summary = safe_call(api.get_user_summary, d, default={}) or {}
        sleep = safe_call(api.get_sleep_data, d, default={}) or {}
        sleep_seconds = (
            sleep.get("dailySleepDTO", {}).get("sleepTimeSeconds", 0) or 0
        )
        history.append(
            {
                "date": d,
                "steps": summary.get("totalSteps", 0) or 0,
                "resting_hr": summary.get("restingHeartRate"),
                "stress": summary.get("averageStressLevel"),
                "sleep_hours": round(sleep_seconds / 3600, 1),
                "calories": summary.get("totalKilocalories", 0) or 0,
            }
        )
    return history


def build_recent_activities(api: Garmin, limit: int = 10) -> list[dict]:
    activities = safe_call(api.get_activities, 0, limit, default=[]) or []
    result = []
    for a in activities:
        result.append(
            {
                "name": a.get("activityName", "Activity"),
                "type": (a.get("activityType") or {}).get("typeKey", "n/a"),
                "date": (a.get("startTimeLocal") or "")[:16],
                "distance_km": round((a.get("distance") or 0) / 1000, 2),
                "duration_min": round((a.get("duration") or 0) / 60, 1),
                "avg_hr": a.get("averageHR"),
                "calories": a.get("calories"),
            }
        )
    return result


@app.route("/")
def index():
    today = date.today().isoformat()
    summary = safe_call(api.get_user_summary, today, default={}) or {}
    history = build_daily_history(api, DAYS_HISTORY)
    activities = build_recent_activities(api)

    return render_template(
        "dashboard.html",
        today=today,
        summary=summary,
        history=history,
        activities=activities,
    )


api: Garmin | None = None


def main():
    global api
    api = init_api()
    if not api:
        print("Could not authenticate. Exiting.")
        sys.exit(1)
    app.run(debug=False, port=5000)


if __name__ == "__main__":
    main()
