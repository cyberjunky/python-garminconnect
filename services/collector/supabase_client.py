"""Supabase upsert helpers for daily coaching data."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def get_supabase():
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
    return create_client(url, key)


def upsert_daily_payload(payload: dict[str, Any], user_id: str = DEFAULT_USER_ID) -> dict[str, str]:
    client = get_supabase()
    ds = payload["date"]
    readiness = payload.get("readiness") or {}
    training = payload.get("training_load") or {}
    session = payload.get("session") or {}

    client.table("readiness_daily").upsert(
        {
            "user_id": user_id,
            "readiness_date": ds,
            "zone": readiness.get("zone"),
            "score_ok": readiness.get("score_ok"),
            "sleep_h": readiness.get("sleep_h"),
            "sleep_score": readiness.get("sleep_score"),
            "hrv": readiness.get("hrv"),
            "stress": readiness.get("stress"),
            "bb_change": readiness.get("bb_change"),
            "hrv_status": readiness.get("hrv_status"),
            "thresholds": payload.get("thresholds"),
            "recommendation": readiness.get("recommendation"),
            "payload": readiness,
        },
        on_conflict="user_id,readiness_date",
    ).execute()

    client.table("training_load").upsert(
        {
            "user_id": user_id,
            "load_date": ds,
            "status_phrase": training.get("status_phrase"),
            "acwr": training.get("acwr"),
            "vo2max": training.get("vo2max"),
            "lthr": training.get("lthr"),
            "payload": training,
        },
        on_conflict="user_id,load_date",
    ).execute()

    client.table("daily_snapshots").upsert(
        {
            "user_id": user_id,
            "snapshot_date": ds,
            "payload": payload,
            "health_score": None,
        },
        on_conflict="user_id,snapshot_date",
    ).execute()

    client.table("session_log").upsert(
        {
            "user_id": user_id,
            "session_date": ds,
            "planned": session,
            "executed": None,
            "confirmed": False,
        },
        on_conflict="user_id,session_date",
    ).execute()

    for row in payload.get("weekly_sport_load") or []:
        client.table("weekly_sport_load").upsert(
            {
                "user_id": user_id,
                "week_start": row["week_start"],
                "block_index": row.get("block_index"),
                "week_in_block": row.get("week_in_block"),
                "kind": row.get("kind"),
                "phase_code": row.get("phase_code"),
                "planned_run_min": row.get("planned_run_min"),
                "planned_bike_min": row.get("planned_bike_min"),
                "planned_swim_min": row.get("planned_swim_min"),
                "planned_walk_min": row.get("planned_walk_min"),
                "planned_total_min": row.get("planned_total_min"),
                "executed_run_min": row.get("executed_run_min"),
                "executed_bike_min": row.get("executed_bike_min"),
                "executed_swim_min": row.get("executed_swim_min"),
                "executed_walk_min": row.get("executed_walk_min"),
                "executed_other_min": row.get("executed_other_min"),
                "executed_total_min": row.get("executed_total_min"),
                "payload": row.get("payload"),
            },
            on_conflict="user_id,week_start",
        ).execute()

    return {"status": "ok", "date": ds}


def get_garmin_tokens_from_supabase(
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any] | None:
    """Retrieve Garmin token data for a user from Supabase garmin_tokens table."""
    client = get_supabase()
    res = (
        client.table("garmin_tokens")
        .select("token_data")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not res or not hasattr(res, "data") or not res.data:
        return None
    data = res.data
    if isinstance(data, list) and len(data) > 0:
        row = data[0]
    elif isinstance(data, dict):
        row = data
    else:
        return None
    token_data = row.get("token_data")
    if isinstance(token_data, dict):
        return token_data
    return None


def upsert_garmin_tokens_to_supabase(
    token_data: dict[str, Any],
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any] | None:
    """Upsert Garmin token data for a user to Supabase if valid (REQ-005)."""
    if not isinstance(token_data, dict) or not token_data:
        return None

    di_token = token_data.get("di_token")
    di_refresh = token_data.get("di_refresh_token")
    has_token = bool(di_token and (not isinstance(di_token, str) or di_token.strip()))
    has_refresh = bool(di_refresh and (not isinstance(di_refresh, str) or di_refresh.strip()))
    if not (has_token or has_refresh):
        return None

    client = get_supabase()
    now_iso = datetime.now(timezone.utc).isoformat()
    res = (
        client.table("garmin_tokens")
        .upsert(
            {
                "user_id": user_id,
                "token_data": token_data,
                "updated_at": now_iso,
            },
            on_conflict="user_id",
        )
        .execute()
    )

    if res and hasattr(res, "data") and res.data:
        return res.data[0] if isinstance(res.data, list) else res.data
    return {"status": "ok", "user_id": user_id, "token_data": token_data}

