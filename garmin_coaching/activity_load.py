"""Aggregate Garmin activities into weekly sport duration (run / bike / swim)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _type_key(activity: dict[str, Any]) -> str:
    at = activity.get("activityType")
    if isinstance(at, dict):
        key = at.get("typeKey") or at.get("typeName") or ""
        if key:
            return str(key).lower()
    raw = activity.get("activityTypeKey") or activity.get("activityType")
    if isinstance(raw, str):
        return raw.lower()
    return ""


def classify_sport(activity: dict[str, Any]) -> str:
    key = _type_key(activity)
    if key in (
        "running",
        "trail_running",
        "treadmill_running",
        "track_running",
        "virtual_run",
    ):
        return "run"
    if key in (
        "cycling",
        "road_biking",
        "mountain_biking",
        "indoor_cycling",
        "gravel_cycling",
        "e_biking",
        "virtual_ride",
    ):
        return "bike"
    if key in ("swimming", "lap_swimming", "open_water_swimming"):
        return "swim"
    if key in ("walking", "hiking", "mountaineering"):
        return "walk"
    if key == "multi_sport":
        return "multisport"
    return "other"


def activity_duration_min(activity: dict[str, Any]) -> float:
    for field in ("movingDuration", "duration", "elapsedDuration"):
        val = activity.get(field)
        if isinstance(val, (int, float)) and val > 0:
            return float(val) / 60.0
    return 0.0


def activity_local_date(activity: dict[str, Any]) -> date | None:
    raw = activity.get("startTimeLocal") or activity.get("startTimeGMT")
    if not raw or not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def aggregate_activities_by_week(
    activities: list[dict[str, Any]],
) -> dict[date, dict[str, float]]:
    """Map week_start (Monday) -> sport -> minutes."""
    buckets: dict[date, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for act in activities:
        d = activity_local_date(act)
        if d is None:
            continue
        sport = classify_sport(act)
        mins = activity_duration_min(act)
        if mins <= 0:
            continue
        ws = monday_of(d)
        buckets[ws][sport] += mins
        buckets[ws]["total"] += mins
    return {k: dict(v) for k, v in buckets.items()}


def fetch_activities_in_range(
    client: Any, start: date, end: date
) -> list[dict[str, Any]]:
    try:
        rows = client.get_activities_by_date(start.isoformat(), end.isoformat())
    except Exception:
        return []
    return rows if isinstance(rows, list) else []


def executed_week_payload(week_start: date, sports: dict[str, float]) -> dict[str, Any]:
    return {
        "week_start": week_start.isoformat(),
        "run_min": round(sports.get("run", 0), 1),
        "bike_min": round(sports.get("bike", 0), 1),
        "swim_min": round(sports.get("swim", 0), 1),
        "walk_min": round(sports.get("walk", 0), 1),
        "other_min": round(sports.get("other", 0) + sports.get("multisport", 0), 1),
        "total_min": round(sports.get("total", 0), 1),
    }
