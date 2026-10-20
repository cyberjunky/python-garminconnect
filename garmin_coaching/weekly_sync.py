"""Sync planned + Garmin-executed weekly sport load for dashboard mesocycles."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from garmin_coaching.activity_load import (
    aggregate_activities_by_week,
    executed_week_payload,
    fetch_activities_in_range,
)
from garmin_coaching.mesocycle import MESOCYCLE_ANCHOR, iter_weeks, plan_week


def build_weekly_sport_rows(
    client: Any,
    *,
    through: date | None = None,
    lookback_days: int = 120,
) -> list[dict[str, Any]]:
    end = through or date.today()
    activity_start = max(MESOCYCLE_ANCHOR, end - timedelta(days=lookback_days))
    activities = fetch_activities_in_range(client, activity_start, end)
    start = MESOCYCLE_ANCHOR
    executed_by_week = aggregate_activities_by_week(activities)

    rows: list[dict[str, Any]] = []
    for ws in iter_weeks(start, end):
        plan = plan_week(ws)
        exec_sports = executed_by_week.get(ws, {})
        exec_payload = executed_week_payload(ws, exec_sports)
        rows.append(
            {
                "week_start": ws.isoformat(),
                "block_index": plan["block_index"],
                "week_in_block": plan["week_in_block"],
                "kind": plan["kind"],
                "phase_code": plan["phase_code"],
                "planned_run_min": plan["planned_run_min"],
                "planned_bike_min": plan["planned_bike_min"],
                "planned_swim_min": plan["planned_swim_min"],
                "planned_walk_min": plan["planned_walk_min"],
                "planned_total_min": plan["planned_total_min"],
                "executed_run_min": exec_payload["run_min"],
                "executed_bike_min": exec_payload["bike_min"],
                "executed_swim_min": exec_payload["swim_min"],
                "executed_walk_min": exec_payload["walk_min"],
                "executed_other_min": exec_payload["other_min"],
                "executed_total_min": exec_payload["total_min"],
                "payload": {"plan": plan, "executed": exec_payload},
            }
        )
    return rows


def sync_weekly_sport_load(
    client: Any, through: date | None = None
) -> list[dict[str, Any]]:
    return build_weekly_sport_rows(client, through=through)
