#!/usr/bin/env python3
"""Refresh Garmin Connect session tokens.

Tries cached tokens first. If they are expired or invalid, falls back to
stored credentials (Keychain / .env.local / env vars) and saves new tokens.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from garmin_auth import login_client, persist_tokens_to_supabase

from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


def main() -> int:
    today = date.today().isoformat()
    try:
        api = login_client()
        summary = api.get_user_summary(today)
    except GarminConnectAuthenticationError as exc:
        print(f"AUTH_ERROR: {exc}")
        return 3
    except GarminConnectTooManyRequestsError as exc:
        print(f"RATE_LIMIT: {exc}")
        return 4
    except GarminConnectConnectionError as exc:
        print(f"CONNECTION_ERROR: {exc}")
        return 5

    print("SESSION_OK")
    persisted = persist_tokens_to_supabase()
    if persisted:
        print("SUPABASE_TOKENS_OK")
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
