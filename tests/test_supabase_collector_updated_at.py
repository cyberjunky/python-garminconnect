"""Unit tests for updated_at tracking in services.collector.supabase_client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from datetime import datetime

from services.collector.supabase_client import DEFAULT_USER_ID, upsert_daily_payload


def test_upsert_daily_payload_includes_updated_at_in_all_upserts():
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = MagicMock(data=[])

    sample_payload = {
        "date": "2026-10-13",
        "readiness": {
            "zone": "VERDE",
            "score_ok": 85,
            "sleep_h": 7.5,
            "sleep_score": 88,
            "hrv": 45,
            "stress": 22,
            "bb_change": 14,
            "hrv_status": "BALANCED",
            "recommendation": "Entrenamiento normal",
        },
        "training_load": {
            "status_phrase": "Productive",
            "acwr": 1.05,
            "vo2max": 49.0,
            "lthr": {"hr": 165},
        },
        "session": {
            "title": "Z2 Run",
            "sport": "running",
            "duration_min": 50,
        },
        "weekly_sport_load": [
            {
                "week_start": "2026-10-12",
                "planned_run_min": 180,
                "executed_run_min": 50,
            }
        ],
    }

    with patch("services.collector.supabase_client.get_supabase", return_value=mock_client):
        res = upsert_daily_payload(sample_payload, DEFAULT_USER_ID)

    assert res["status"] == "ok"
    assert res["date"] == "2026-10-13"

    # Verify that each table called upsert with updated_at in the payload dict
    table_calls = [call.args[0] for call in mock_client.table.call_args_list]
    assert "readiness_daily" in table_calls
    assert "training_load" in table_calls
    assert "daily_snapshots" in table_calls
    assert "session_log" in table_calls
    assert "weekly_sport_load" in table_calls

    upsert_calls = mock_table.upsert.call_args_list
    assert len(upsert_calls) == 5

    for call in upsert_calls:
        row_data = call.args[0]
        assert "updated_at" in row_data, f"Missing updated_at in row: {row_data}"
        # verify it's a valid ISO timestamp
        dt = datetime.fromisoformat(row_data["updated_at"].replace("Z", "+00:00"))
        assert dt is not None
