#!/usr/bin/env python3
"""Collect a daily Garmin snapshot through the local MCP server.

This script calls multiple read-only MCP tools and prints one JSON document
with key wellness and activity indicators for a target date.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _validate_date(value: str) -> str:
    datetime.strptime(value, "%Y-%m-%d")
    return value


def _payload(result: object) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    return {"ok": False, "error": "Missing structuredContent"}


def _extract_metrics(summary: dict[str, Any], heart_rates: dict[str, Any]) -> dict[str, Any]:
    data = summary.get("data") or {}
    hr_data = heart_rates.get("data") or {}
    return {
        "steps": data.get("totalSteps"),
        "distance_m": data.get("totalDistanceMeters"),
        "active_kcal": data.get("activeKilocalories"),
        "resting_hr": data.get("restingHeartRate") or hr_data.get("restingHeartRate"),
        "max_hr": data.get("maxHeartRate") or hr_data.get("maxHeartRate"),
        "min_hr": data.get("minHeartRate") or hr_data.get("minHeartRate"),
        "avg_stress": data.get("averageStressLevel"),
        "body_battery_recent": data.get("bodyBatteryMostRecentValue"),
    }


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _score_resting_hr(resting_hr: float | None) -> float | None:  # noqa: PLR0911 - piecewise score
    if resting_hr is None:
        return None
    if resting_hr < 38:
        return 35.0
    if 38 <= resting_hr <= 50:
        return 80.0 + (resting_hr - 38) * (20.0 / 12.0)
    if 50 < resting_hr <= 60:
        return 100.0 - (resting_hr - 50) * 2.0
    if 60 < resting_hr <= 75:
        return 80.0 - (resting_hr - 60) * (40.0 / 15.0)
    if 75 < resting_hr <= 90:
        return 40.0 - (resting_hr - 75) * (25.0 / 15.0)
    return 15.0


def _score_sleep_hours(hours: float | None) -> float | None:
    if hours is None:
        return None
    if hours <= 4.0:
        return 15.0
    if 4.0 < hours <= 7.0:
        return 15.0 + (hours - 4.0) * (65.0 / 3.0)
    if 7.0 < hours <= 8.5:
        return 80.0 + (hours - 7.0) * (20.0 / 1.5)
    if 8.5 < hours <= 10.0:
        return 100.0 - (hours - 8.5) * (30.0 / 1.5)
    return 55.0


def _score_steps(steps: float | None, goal: float | None) -> float | None:
    if steps is None:
        return None
    target = goal if goal and goal > 0 else 7000.0
    ratio = max(0.0, min(1.2, steps / target))
    return min(100.0, ratio * 100.0)


def _score_stress(avg_stress: float | None) -> float | None:
    if avg_stress is None:
        return None
    if avg_stress <= 15:
        return 95.0
    if 15 < avg_stress <= 30:
        return 95.0 - (avg_stress - 15) * (20.0 / 15.0)
    if 30 < avg_stress <= 50:
        return 75.0 - (avg_stress - 30) * (30.0 / 20.0)
    if 50 < avg_stress <= 70:
        return 45.0 - (avg_stress - 50) * (25.0 / 20.0)
    return 20.0


def _health_score(summary: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    data = summary.get("data") or {}
    resting_hr = _to_float(metrics.get("resting_hr"))
    steps = _to_float(metrics.get("steps"))
    goal = _to_float(data.get("dailyStepGoal"))
    stress = _to_float(metrics.get("avg_stress"))
    sleeping_seconds = _to_float(data.get("sleepingSeconds"))
    sleep_hours = (sleeping_seconds / 3600.0) if sleeping_seconds is not None else None

    scores = {
        "cardio": _score_resting_hr(resting_hr),
        "sleep": _score_sleep_hours(sleep_hours),
        "activity": _score_steps(steps, goal),
        "stress": _score_stress(stress),
    }

    weights = {"cardio": 0.3, "sleep": 0.25, "activity": 0.25, "stress": 0.2}
    weighted = 0.0
    present_weight = 0.0
    for key, value in scores.items():
        if value is not None:
            weighted += value * weights[key]
            present_weight += weights[key]

    total = (weighted / present_weight) if present_weight > 0 else None
    return {
        "score_0_100": _round_or_none(total),
        "components": {k: _round_or_none(v) for k, v in scores.items()},
        "inputs": {
            "resting_hr": resting_hr,
            "sleep_hours": _round_or_none(sleep_hours),
            "steps": steps,
            "steps_goal": goal,
            "avg_stress": stress,
        },
    }


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


async def _load_recent_summaries(
    session: ClientSession, target_day: str, days: int = 7
) -> list[dict[str, Any]]:
    end_day = datetime.strptime(target_day, "%Y-%m-%d").date()
    out: list[dict[str, Any]] = []
    for offset in range(days):
        day = (end_day.fromordinal(end_day.toordinal() - offset)).isoformat()
        payload = _payload(await session.call_tool("get_user_summary", {"date": day}))
        if payload.get("ok") and isinstance(payload.get("data"), dict):
            out.append(payload["data"])
    return out


def _baseline_compare(
    current_summary: dict[str, Any],
    current_metrics: dict[str, Any],
    recent_summaries: list[dict[str, Any]],
    health_score: dict[str, Any],
) -> dict[str, Any]:
    current = current_summary.get("data") or {}

    steps_values = [_to_float(item.get("totalSteps")) for item in recent_summaries]
    steps_values = [v for v in steps_values if v is not None]

    sleep_values = [_to_float(item.get("sleepingSeconds")) for item in recent_summaries]
    sleep_values = [v / 3600.0 for v in sleep_values if v is not None]

    rhr_values = [_to_float(item.get("restingHeartRate")) for item in recent_summaries]
    rhr_values = [v for v in rhr_values if v is not None]

    stress_values = [_to_float(item.get("averageStressLevel")) for item in recent_summaries]
    stress_values = [v for v in stress_values if v is not None]

    baseline = {
        "steps_avg_7d": _round_or_none(_mean(steps_values)),
        "sleep_hours_avg_7d": _round_or_none(_mean(sleep_values)),
        "resting_hr_avg_7d": _round_or_none(_mean(rhr_values)),
        "avg_stress_avg_7d": _round_or_none(_mean(stress_values)),
    }

    current_sleep_hours = _to_float(current.get("sleepingSeconds"))
    if current_sleep_hours is not None:
        current_sleep_hours /= 3600.0

    deltas = {
        "steps_delta": _round_or_none(
            (_to_float(current_metrics.get("steps")) or 0.0)
            - (baseline["steps_avg_7d"] or 0.0)
        )
        if baseline["steps_avg_7d"] is not None and _to_float(current_metrics.get("steps")) is not None
        else None,
        "sleep_hours_delta": _round_or_none(
            (current_sleep_hours or 0.0) - (baseline["sleep_hours_avg_7d"] or 0.0)
        )
        if baseline["sleep_hours_avg_7d"] is not None and current_sleep_hours is not None
        else None,
        "resting_hr_delta": _round_or_none(
            (_to_float(current_metrics.get("resting_hr")) or 0.0)
            - (baseline["resting_hr_avg_7d"] or 0.0)
        )
        if baseline["resting_hr_avg_7d"] is not None and _to_float(current_metrics.get("resting_hr")) is not None
        else None,
        "avg_stress_delta": _round_or_none(
            (_to_float(current_metrics.get("avg_stress")) or 0.0)
            - (baseline["avg_stress_avg_7d"] or 0.0)
        )
        if baseline["avg_stress_avg_7d"] is not None and _to_float(current_metrics.get("avg_stress")) is not None
        else None,
        "health_score": health_score.get("score_0_100"),
    }

    return {
        "baseline": baseline,
        "deltas_vs_7d_avg": deltas,
        "samples_used": len(recent_summaries),
    }


def _benchmark_bogota_male_adult(summary: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    data = summary.get("data") or {}
    resting_hr = _to_float(metrics.get("resting_hr"))
    steps = _to_float(metrics.get("steps"))
    sleep_hours = _to_float(data.get("sleepingSeconds"))
    if sleep_hours is not None:
        sleep_hours /= 3600.0
    spo2 = _to_float(data.get("averageSpo2"))

    def _label(  # noqa: PLR0911 - one return per band
        value: float | None, low: float, high: float, inverse: bool = False
    ) -> str:
        if value is None:
            return "unknown"
        if not inverse:
            if value < low:
                return "below_reference"
            if value > high:
                return "above_reference"
            return "within_reference"
        if value < low:
            return "better_than_reference"
        if value > high:
            return "worse_than_reference"
        return "within_reference"

    return {
        "reference_note": (
            "Approximate non-clinical reference for adult men in high-altitude urban settings "
            "like Bogota; use for orientation only."
        ),
        "resting_hr": {
            "value": resting_hr,
            "reference_bpm": {"typical_low": 55, "typical_high": 75},
            "status": _label(resting_hr, 55, 75, inverse=True),
        },
        "steps": {
            "value": steps,
            "reference_steps": {"typical_daily_min": 7000, "typical_daily_high": 10000},
            "status": _label(steps, 7000, 10000),
        },
        "sleep_hours": {
            "value": _round_or_none(sleep_hours),
            "reference_hours": {"recommended_low": 7, "recommended_high": 9},
            "status": _label(sleep_hours, 7, 9),
        },
        "spo2": {
            "value": spo2,
            "reference_percent_bogota": {"typical_low": 90, "typical_high": 96},
            "status": _label(spo2, 90, 96),
        },
    }


async def _run(
    target_day: str,
    activity_limit: int,
    output: str | None,
    allow_env_credentials: bool,
) -> int:
    params = StdioServerParameters(command="python", args=["-m", "garmin_mcp.server"], cwd=".")

    async with (
        stdio_client(params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        login = _payload(await session.call_tool("login_with_tokens", {}))
        if not login.get("ok") or not login.get("authenticated"):
            if allow_env_credentials:
                email = os.getenv("GARMIN_EMAIL")
                password = os.getenv("GARMIN_PASSWORD")
                if email and password:
                    cred_login = _payload(
                        await session.call_tool(
                            "login_with_credentials",
                            {"email": email, "password": password},
                        )
                    )
                    login = cred_login
                    print("MCP_DAILY_SNAPSHOT_LOGIN_WITH_CREDENTIALS", cred_login)
                else:
                    print(
                        "MCP_DAILY_SNAPSHOT_NO_ENV_CREDS: --allow-env-credentials enabled, "
                        "but GARMIN_EMAIL or GARMIN_PASSWORD is missing."
                    )

            if not login.get("ok") or not login.get("authenticated"):
                print(
                    "MCP_DAILY_SNAPSHOT_NEEDS_TOKENS: token login failed. "
                    "Create tokens first with the e2e script in credential mode."
                )
                return 2

        summary = _payload(await session.call_tool("get_user_summary", {"date": target_day}))
        heart_rates = _payload(await session.call_tool("get_heart_rates", {"date": target_day}))
        sleep = _payload(await session.call_tool("get_sleep_data", {"date": target_day}))
        activities = _payload(
            await session.call_tool("get_activities", {"start": 0, "limit": activity_limit})
        )

        metrics = _extract_metrics(summary, heart_rates)
        health_score = _health_score(summary, metrics)
        recent_summaries = await _load_recent_summaries(session, target_day, days=7)
        baseline = _baseline_compare(summary, metrics, recent_summaries, health_score)
        bogota_benchmark = _benchmark_bogota_male_adult(summary, metrics)

        response = {
            "date": target_day,
            "ok": all(
                call.get("ok")
                for call in (summary, heart_rates, sleep, activities)
            ),
            "metrics": metrics,
            "health_score": health_score,
            "vs_7day_baseline": baseline,
            "vs_bogota_male_adult_reference": bogota_benchmark,
            "sleep": sleep.get("data"),
            "activities_count": len(activities.get("data") or []),
            "activities_sample": (activities.get("data") or [])[:3],
            "errors": {
                "summary": None if summary.get("ok") else summary,
                "heart_rates": None if heart_rates.get("ok") else heart_rates,
                "sleep": None if sleep.get("ok") else sleep,
                "activities": None if activities.get("ok") else activities,
            },
        }

        rendered = json.dumps(response, ensure_ascii=True, indent=2)
        print(rendered)
        if output:
            out_path = Path(output).expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered + "\n", encoding="utf-8")
            print(f"MCP_DAILY_SNAPSHOT_WRITTEN {out_path}")
        return 0 if response["ok"] else 3


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect daily snapshot via MCP")
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Target date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--activity-limit",
        type=int,
        default=20,
        help="How many recent activities to request (default: 20)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path to write the snapshot JSON file.",
    )
    parser.add_argument(
        "--allow-env-credentials",
        action="store_true",
        help=(
            "If token login fails, try login_with_credentials using GARMIN_EMAIL "
            "and GARMIN_PASSWORD from environment variables."
        ),
    )
    args = parser.parse_args()

    if args.activity_limit <= 0:
        print("--activity-limit must be a positive integer")
        return 4

    try:
        target_day = _validate_date(args.date)
    except ValueError:
        print("Invalid --date format. Use YYYY-MM-DD.")
        return 5

    return anyio.run(
        _run,
        target_day,
        args.activity_limit,
        args.output,
        args.allow_env_credentials,
    )


if __name__ == "__main__":
    raise SystemExit(main())
