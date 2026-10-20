#!/usr/bin/env python3
"""Live Garmin account smoke test using stored credentials or tokens."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from garmin_auth import login_client

from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


def main() -> int:
    today = date.today().isoformat()
    try:
        api = login_client(prompt=False)
        summary = api.get_user_summary(today)
    except GarminConnectAuthenticationError as exc:
        print(f"LIVE_TEST_AUTH_ERROR: {exc}")
        return 3
    except GarminConnectTooManyRequestsError as exc:
        print(f"LIVE_TEST_RATE_LIMIT: {exc}")
        return 4
    except GarminConnectConnectionError as exc:
        print(f"LIVE_TEST_CONNECTION_ERROR: {exc}")
        return 5

    print("LIVE_TEST_OK")
    print(
        {
            "date": today,
            "steps": summary.get("totalSteps"),
            "calories": summary.get("totalKilocalories"),
            "distance_m": summary.get("totalDistanceMeters"),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
