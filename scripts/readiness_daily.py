#!/usr/bin/env python3
"""Daily readiness report based on Garmin sleep, stress, HRV and Body Battery.

Usage:
  ./.venv/bin/python scripts/readiness_daily.py
  ./.venv/bin/python scripts/readiness_daily.py --days 14 --json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from garmin_auth import login_client

from garmin_coaching.collector import (
    collect_recent_metrics,
    day_metrics,
    get_sleep_bb_for_day,
)
from garmin_coaching.readiness import (
    build_daily_plan,
    classify,
    derive_thresholds_from_history,
)

if TYPE_CHECKING:
    from garminconnect import Garmin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Garmin daily readiness report")
    parser.add_argument(
        "--days", type=int, default=14, help="Days to include in history"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON output instead of human summary",
    )
    parser.add_argument(
        "--sleep-hours", type=float, default=7.5, help="Sleep hours threshold"
    )
    parser.add_argument(
        "--sleep-score", type=float, default=84, help="Sleep score threshold"
    )
    parser.add_argument("--hrv", type=float, default=45, help="Overnight HRV threshold")
    parser.add_argument(
        "--stress-max", type=float, default=27, help="Max average stress threshold"
    )
    parser.add_argument(
        "--bb-change",
        type=float,
        default=61,
        help="Body Battery overnight change threshold",
    )
    parser.add_argument(
        "--short",
        action="store_true",
        help="Print one-line semaphore summary",
    )
    parser.add_argument(
        "--save-history",
        action="store_true",
        help="Append today's readiness snapshot to CSV and JSONL history files",
    )
    parser.add_argument(
        "--history-dir",
        default=".readiness_history",
        help="Directory used for history files",
    )
    parser.add_argument(
        "--auto-thresholds",
        action="store_true",
        help="Compute thresholds from recent personal medians",
    )
    parser.add_argument(
        "--auto-days",
        type=int,
        default=60,
        help="Days used to compute automatic thresholds",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Print daily training plan based on current readiness zone",
    )
    return parser.parse_args()


def get_client() -> Garmin:
    return login_client()


def build_summary(client: Garmin, days: int, th: dict[str, float]) -> dict[str, Any]:
    sleep_bb_today = None
    for ds in [
        date.today().isoformat(),
        (date.today() - timedelta(days=1)).isoformat(),
    ]:
        try:
            sleep_bb_today = get_sleep_bb_for_day(client, ds)
            break
        except Exception:  # noqa: S112 - best effort: a day without Garmin data is skipped
            continue

    rows: list[dict[str, Any]] = []
    for i in range(days, 0, -1):
        ds = (date.today() - timedelta(days=i)).isoformat()
        try:
            m = day_metrics(client, ds)
            zone, n, rec = classify(m, th)
            m.update({"score_ok": n, "zone": zone, "recommendation": rec})
            rows.append(m)
        except Exception:  # noqa: S112 - best effort: a day without Garmin data is skipped
            continue

    today_readiness = None
    for ds in [
        date.today().isoformat(),
        (date.today() - timedelta(days=1)).isoformat(),
    ]:
        try:
            m = day_metrics(client, ds)
            zone, n, rec = classify(m, th)
            m.update({"score_ok": n, "zone": zone, "recommendation": rec})
            today_readiness = m
            break
        except Exception:  # noqa: S112 - best effort: a day without Garmin data is skipped
            continue

    return {
        "counts": {
            "VERDE": sum(1 for r in rows if r["zone"] == "VERDE"),
            "AMARILLO": sum(1 for r in rows if r["zone"] == "AMARILLO"),
            "ROJO": sum(1 for r in rows if r["zone"] == "ROJO"),
        },
        "today_sleep_body_battery": sleep_bb_today,
        "today_readiness": today_readiness,
        "rows_last_nd": rows,
        "thresholds": th,
    }


def save_history(summary: dict[str, Any], history_dir: str) -> tuple[str, str]:
    root = Path(history_dir)
    root.mkdir(parents=True, exist_ok=True)
    jsonl_path = root / "readiness_history.jsonl"
    csv_path = root / "readiness_history.csv"

    tsb = summary.get("today_sleep_body_battery") or {}
    tr = summary.get("today_readiness") or {}
    counts = summary.get("counts") or {}
    th = summary.get("thresholds") or {}

    row = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "date": tr.get("date") or tsb.get("date"),
        "zone": tr.get("zone"),
        "score_ok": tr.get("score_ok"),
        "sleep_h": tr.get("sleep_h"),
        "sleep_score": tr.get("sleep_score"),
        "hrv": tr.get("hrv"),
        "stress": tr.get("stress"),
        "bb_change": tr.get("bb_change"),
        "hrv_status": tr.get("hrv_status"),
        "bb_current": tsb.get("body_battery_current"),
        "count_verde": counts.get("VERDE", 0),
        "count_amarillo": counts.get("AMARILLO", 0),
        "count_rojo": counts.get("ROJO", 0),
        "th_sleep_h": th.get("sleep_h"),
        "th_sleep_score": th.get("sleep_score"),
        "th_hrv": th.get("hrv"),
        "th_stress_max": th.get("stress_max"),
        "th_bb_change": th.get("bb_change"),
    }

    with jsonl_path.open("a", encoding="utf-8") as jf:
        jf.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_header = not csv_path.exists()
    with csv_path.open("a", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    return str(jsonl_path), str(csv_path)


def print_human(summary: dict[str, Any]) -> None:
    tsb = summary.get("today_sleep_body_battery") or {}
    tr = summary.get("today_readiness") or {}
    c = summary.get("counts") or {}

    print("Resultado de sueno + Body Battery (hoy)")
    print(f"- Fecha: {tsb.get('date')}")
    print(f"- Sueno (h): {tsb.get('sleep_hours')}")
    print(f"- Sleep score: {tsb.get('sleep_score')}")
    print(f"- Sleep stress avg: {tsb.get('sleep_stress_avg')}")
    print(f"- Body Battery change: {tsb.get('body_battery_change')}")
    print(f"- Body Battery actual: {tsb.get('body_battery_current')}")
    print(f"- Stress dia avg: {tsb.get('stress_day_avg')}")

    print("\nReadiness de hoy")
    print(f"- Zona: {tr.get('zone')} ({tr.get('score_ok')}/5)")
    print(f"- Recomendacion: {tr.get('recommendation')}")

    print("\nConteo periodo")
    print(f"- VERDE: {c.get('VERDE', 0)}")
    print(f"- AMARILLO: {c.get('AMARILLO', 0)}")
    print(f"- ROJO: {c.get('ROJO', 0)}")


def print_short(summary: dict[str, Any]) -> None:
    tsb = summary.get("today_sleep_body_battery") or {}
    tr = summary.get("today_readiness") or {}
    print(
        f"{tr.get('date')} | {tr.get('zone')} ({tr.get('score_ok')}/5)"
        f" | sleep={tsb.get('sleep_hours')}h score={tsb.get('sleep_score')}"
        f" | bb+={tsb.get('body_battery_change')}"
        f" | {tr.get('recommendation')}"
    )


def print_plan(summary: dict[str, Any]) -> None:
    plan = summary.get("daily_plan") or {}
    print("\nPlan diario")
    print(f"- Zona: {plan.get('zone')}")
    print(f"- Tipo: {plan.get('session')}")
    for step in plan.get("details") or []:
        print(f"- {step}")


def main() -> None:
    args = parse_args()
    base_th = {
        "sleep_h": float(args.sleep_hours),
        "sleep_score": float(args.sleep_score),
        "hrv": float(args.hrv),
        "stress_max": float(args.stress_max),
        "bb_change": float(args.bb_change),
    }

    client = get_client()
    th = dict(base_th)
    if args.auto_thresholds:
        metrics = collect_recent_metrics(client, max(7, int(args.auto_days)))
        th = derive_thresholds_from_history(metrics, base_th)

    summary = build_summary(client, args.days, th)
    summary["daily_plan"] = build_daily_plan(summary.get("today_readiness"))

    if args.save_history:
        jsonl_path, csv_path = save_history(summary, args.history_dir)
        summary["history_files"] = {"jsonl": jsonl_path, "csv": csv_path}

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.short:
        print_short(summary)
    else:
        print_human(summary)
        if args.plan:
            print_plan(summary)

    if args.save_history and not args.json:
        files = summary.get("history_files") or {}
        print("\nHistorial guardado")
        print(f"- JSONL: {files.get('jsonl')}")
        print(f"- CSV: {files.get('csv')}")


if __name__ == "__main__":
    main()
