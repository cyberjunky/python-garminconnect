"""Build unified daily coaching payload from Garmin API."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from garmin_coaching.guards import apply_guards
from garmin_coaching.last_activity import fetch_last_activity
from garmin_coaching.macrocycle import active_phase, milestones_as_dict, phase_as_dict
from garmin_coaching.mesocycle import plan_week
from garmin_coaching.messages import format_whatsapp_message
from garmin_coaching.readiness import (
    DEFAULT_THRESHOLDS,
    build_daily_plan,
    classify,
    derive_thresholds_from_history,
)
from garmin_coaching.session_planner import plan_session
from garmin_coaching.weekly_sync import build_weekly_sport_rows


def day_metrics(client: Any, ds: str) -> dict[str, Any]:
    st = client.get_stress_data(ds)
    sl = client.get_sleep_data(ds)
    h = client.get_hrv_data(ds)

    dsd = sl.get("dailySleepDTO") or {}
    sh = dsd.get("sleepTimeSeconds")
    sleep_h = (sh / 3600.0) if isinstance(sh, (int, float)) else None
    sleep_score = ((dsd.get("sleepScores") or {}).get("overall") or {}).get("value")
    hrv = sl.get("avgOvernightHrv")
    stress = st.get("avgStressLevel")
    bb_change = sl.get("bodyBatteryChange")
    hrv_status = ((h or {}).get("hrvSummary") or {}).get("status")

    return {
        "date": ds,
        "sleep_h": sleep_h,
        "sleep_score": sleep_score,
        "hrv": hrv,
        "stress": stress,
        "bb_change": bb_change,
        "hrv_status": hrv_status,
    }


def get_sleep_bb_for_day(client: Any, ds: str) -> dict[str, Any]:
    sl = client.get_sleep_data(ds)
    st = client.get_stress_data(ds)
    bb = client.get_body_battery(ds)

    dsd = sl.get("dailySleepDTO") or {}
    sh = dsd.get("sleepTimeSeconds")
    sleep_h = (sh / 3600.0) if isinstance(sh, (int, float)) else None
    sleep_score = ((dsd.get("sleepScores") or {}).get("overall") or {}).get("value")
    bb_change = sl.get("bodyBatteryChange")

    bb_current = None
    if isinstance(bb, list) and bb:
        vals = bb[0].get("bodyBatteryValuesArray") or []
        if vals and isinstance(vals[-1], (list, tuple)) and len(vals[-1]) >= 3:
            bb_current = vals[-1][2]

    return {
        "date": ds,
        "sleep_hours": round(sleep_h, 2) if sleep_h is not None else None,
        "sleep_score": sleep_score,
        "sleep_stress_avg": dsd.get("avgSleepStress"),
        "body_battery_change": bb_change,
        "body_battery_current": bb_current,
        "stress_day_avg": st.get("avgStressLevel"),
    }


def _first_device_entry(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    latest = data.get("latestTrainingStatusData") or data.get(
        "metricsTrainingLoadBalanceDTOMap"
    )
    if isinstance(latest, dict) and latest:
        return next(iter(latest.values()))
    return None


def fetch_training_load(client: Any, cdate: str | None = None) -> dict[str, Any]:
    ds = cdate or date.today().isoformat()
    out: dict[str, Any] = {}
    try:
        status = client.get_training_status(ds)
        if isinstance(status, dict):
            device = _first_device_entry(status.get("mostRecentTrainingStatus"))
            if device:
                phrase = device.get("trainingStatusFeedbackPhrase") or ""
                out["status_phrase"] = phrase.split("_")[0] if phrase else None
                acute = device.get("acuteTrainingLoadDTO") or {}
                out["acwr"] = acute.get("dailyAcuteChronicWorkloadRatio")
                out["acwr_status"] = acute.get("acwrStatus")
                out["acute_load"] = acute.get("dailyTrainingLoadAcute")
                out["chronic_load"] = acute.get("dailyTrainingLoadChronic")
            vo2_block = status.get("mostRecentVO2Max") or {}
            generic = vo2_block.get("generic") or {}
            cycling = vo2_block.get("cycling") or {}
            out["vo2max"] = generic.get("vo2MaxPreciseValue") or generic.get(
                "vo2MaxValue"
            )
            out["vo2max_cycling"] = cycling.get("vo2MaxPreciseValue") or cycling.get(
                "vo2MaxValue"
            )
            out["load_balance"] = status.get("mostRecentTrainingLoadBalance")
            out["raw"] = status
    except Exception as exc:
        out["status_error"] = str(exc)

    try:
        lthr = client.get_lactate_threshold(latest=True)
        if isinstance(lthr, dict):
            out["lthr"] = lthr
    except Exception as exc:
        out["lthr_error"] = str(exc)

    return out


def collect_recent_metrics(client: Any, days: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i in range(days, 0, -1):
        ds = (date.today() - timedelta(days=i)).isoformat()
        try:
            rows.append(day_metrics(client, ds))
        except Exception:  # noqa: S112 - best effort: a day without Garmin data is skipped
            continue
    return rows


def build_daily_payload(
    client: Any,
    target_day: str | None = None,
    auto_thresholds: bool = True,
    auto_days: int = 60,
) -> dict[str, Any]:
    on_day = date.fromisoformat(target_day) if target_day else date.today()
    ds = on_day.isoformat()

    th = dict(DEFAULT_THRESHOLDS)
    if auto_thresholds:
        metrics = collect_recent_metrics(client, max(7, auto_days))
        th = derive_thresholds_from_history(metrics, th)

    readiness_raw = None
    for candidate in [ds, (on_day - timedelta(days=1)).isoformat()]:
        try:
            m = day_metrics(client, candidate)
            zone, score_ok, rec = classify(m, th)
            m.update({"score_ok": score_ok, "zone": zone, "recommendation": rec})
            readiness_raw = m
            break
        except Exception:  # noqa: S112 - best effort: a day without Garmin data is skipped
            continue

    sleep_bb = None
    for candidate in [ds, (on_day - timedelta(days=1)).isoformat()]:
        try:
            sleep_bb = get_sleep_bb_for_day(client, candidate)
            break
        except Exception:  # noqa: S112 - best effort: a day without Garmin data is skipped
            continue

    phase = active_phase(on_day)
    training_load = fetch_training_load(client, ds)
    session = plan_session(readiness_raw, on_day, phase)
    session = apply_guards(readiness_raw or {}, training_load, session)
    daily_plan = build_daily_plan(readiness_raw)

    mesocycle_week = plan_week(on_day)
    weekly_sport_load = build_weekly_sport_rows(
        client, through=on_day, lookback_days=120
    )
    last_activity = fetch_last_activity(client)

    return {
        "date": ds,
        "mesocycle_week": mesocycle_week,
        "weekly_sport_load": weekly_sport_load,
        "readiness": readiness_raw,
        "sleep_body_battery": sleep_bb,
        "thresholds": th,
        "daily_plan": daily_plan,
        "macrocycle": phase_as_dict(phase),
        "milestones": milestones_as_dict(on_day),
        "training_load": training_load,
        "last_activity": last_activity,
        "session": session,
        "whatsapp_message": format_whatsapp_message(
            {
                "date": ds,
                "readiness": readiness_raw,
                "session": session,
                "macrocycle": phase_as_dict(phase),
                "milestones": milestones_as_dict(on_day),
                "training_load": training_load,
            }
        ),
    }
