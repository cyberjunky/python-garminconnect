"""3+1 mesocycles: planned weekly volume by sport (Monday always recovery)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from garmin_coaching.activity_load import monday_of
from garmin_coaching.macrocycle import MacrocyclePhase, active_phase

# First Monday on or after macrocycle R0 start (2026-09-21).
MESOCYCLE_ANCHOR = date(2026, 9, 21)

# Base weekly minutes at load week 2 (sport totals; Monday recovery baked into daily split).
_PHASE_WEEKLY_BASE: dict[str, dict[str, int]] = {
    "R0": {"run": 60, "bike": 30, "swim": 0, "walk": 120},
    "R1": {"run": 200, "bike": 150, "swim": 0, "walk": 45},
    "R2": {"run": 280, "bike": 60, "swim": 0, "walk": 30},
    "R3": {"run": 320, "bike": 40, "swim": 0, "walk": 30},
    "R4": {"run": 180, "bike": 0, "swim": 0, "walk": 60},
    "R5": {"run": 90, "bike": 280, "swim": 0, "walk": 30},
    "R6": {"run": 60, "bike": 320, "swim": 0, "walk": 30},
    "R7": {"run": 150, "bike": 200, "swim": 120, "walk": 30},
}

_LOAD_WEEK_SCALE = (0.85, 1.0, 1.1)
_RECOVERY_WEEK_SCALE = 0.65
_MONDAY_WALK_MIN = 30


@dataclass(frozen=True)
class MesocycleWeek:
    week_start: date
    block_index: int
    week_in_block: int
    kind: str
    phase_code: str


def week_meta(week_start: date) -> MesocycleWeek:
    ws = monday_of(week_start)
    days = (ws - MESOCYCLE_ANCHOR).days
    if days < 0:
        block_index, week_in_block = 0, 0
    else:
        week_index = days // 7
        block_index = week_index // 4
        week_in_block = week_index % 4
    kind = "recovery" if week_in_block == 3 else "load"
    phase = active_phase(ws)
    return MesocycleWeek(
        week_start=ws,
        block_index=block_index,
        week_in_block=week_in_block,
        kind=kind,
        phase_code=phase.code,
    )


def _scale_for_week(week_in_block: int) -> float:
    if week_in_block == 3:
        return _RECOVERY_WEEK_SCALE
    return _LOAD_WEEK_SCALE[week_in_block]


def planned_weekly_sports(week_start: date) -> dict[str, float]:
    meta = week_meta(week_start)
    base = dict(_PHASE_WEEKLY_BASE.get(meta.phase_code, _PHASE_WEEKLY_BASE["R0"]))
    scale = _scale_for_week(meta.week_in_block)
    return {sport: round(mins * scale, 1) for sport, mins in base.items()}


def _daily_non_monday_budget(weekly: dict[str, float]) -> dict[str, float]:
    """Reserve Monday walk; spread remaining planned minutes Tue-Sun."""
    out = dict(weekly)
    walk = out.get("walk", 0)
    out["walk"] = max(0.0, walk - _MONDAY_WALK_MIN)
    days = 6
    return {
        k: (v / days if k != "swim" else v / max(3, days // 2)) for k, v in out.items()
    }


def planned_daily_sports(on_day: date) -> dict[str, float]:
    ws = monday_of(on_day)
    weekly = planned_weekly_sports(ws)
    if on_day.weekday() == 0:
        return {"run": 0.0, "bike": 0.0, "swim": 0.0, "walk": float(_MONDAY_WALK_MIN)}
    per_day = _daily_non_monday_budget(weekly)
    return {k: round(v, 1) for k, v in per_day.items()}


def plan_week(week_start: date) -> dict[str, Any]:
    ws = monday_of(week_start)
    meta = week_meta(ws)
    phase = active_phase(ws)
    planned = planned_weekly_sports(ws)
    daily: list[dict[str, Any]] = []
    for i in range(7):
        d = ws + timedelta(days=i)
        daily.append({"date": d.isoformat(), "sports": planned_daily_sports(d)})

    return {
        "week_start": ws.isoformat(),
        "block_index": meta.block_index,
        "week_in_block": meta.week_in_block,
        "week_label": f"Bloque {meta.block_index + 1} · Semana {meta.week_in_block + 1}/4",
        "kind": meta.kind,
        "phase_code": meta.phase_code,
        "phase_name": phase.name,
        "planned_run_min": planned.get("run", 0),
        "planned_bike_min": planned.get("bike", 0),
        "planned_swim_min": planned.get("swim", 0),
        "planned_walk_min": planned.get("walk", 0),
        "planned_total_min": round(sum(planned.values()), 1),
        "daily": daily,
    }


def iter_weeks(from_date: date, to_date: date) -> list[date]:
    start = monday_of(from_date)
    end = monday_of(to_date)
    out: list[date] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=7)
    return out


def phase_for_week(week_start: date) -> MacrocyclePhase:
    return active_phase(monday_of(week_start))


def mesocycle_summary_until(end: date) -> list[dict[str, Any]]:
    start = MESOCYCLE_ANCHOR
    return [plan_week(ws) for ws in iter_weeks(start, end)]
