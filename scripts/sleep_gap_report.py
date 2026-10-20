#!/usr/bin/env python3
"""Detect days with missing sleep data and export a CSV report."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garmin_auth import login_client

if TYPE_CHECKING:
    from garminconnect import Garmin


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def _is_missing_sleep(payload: dict[str, Any]) -> bool:
    dto = payload.get("dailySleepDTO") or {}
    total = dto.get("sleepTimeSeconds")
    levels = payload.get("sleepLevels") or []
    return total is None and not levels


def _sleep_hours(payload: dict[str, Any]) -> float | None:
    dto = payload.get("dailySleepDTO") or {}
    total = dto.get("sleepTimeSeconds")
    if isinstance(total, (int, float)):
        return round(total / 3600.0, 2)
    return None


def _build_client() -> Garmin:
    return login_client()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export sleep-gap report as CSV")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument(
        "--output",
        default="your_data/sleep_gap_report.csv",
        help="CSV output path",
    )
    args = parser.parse_args()

    start = _parse_date(args.start)
    end = _parse_date(args.end)
    if end < start:
        print("ERROR: --end cannot be before --start")
        return 2

    api = _build_client()

    rows: list[dict[str, Any]] = []
    for day in _daterange(start, end):
        ds = day.isoformat()
        try:
            payload = api.get_sleep_data(ds)
            missing = _is_missing_sleep(payload)
            rows.append(
                {
                    "date": ds,
                    "sleep_hours": _sleep_hours(payload),
                    "missing_sleep": missing,
                    "has_sleep_levels": bool(payload.get("sleepLevels") or []),
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "date": ds,
                    "sleep_hours": None,
                    "missing_sleep": True,
                    "has_sleep_levels": False,
                    "error": str(exc),
                }
            )

    out_path = Path(args.output).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["date", "sleep_hours", "missing_sleep", "has_sleep_levels", "error"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    missing_days = [r["date"] for r in rows if r.get("missing_sleep") is True]
    print("SLEEP_GAP_REPORT_OK")
    print(f"output={out_path}")
    print(f"days_analyzed={len(rows)}")
    print(f"missing_days_count={len(missing_days)}")
    print(f"missing_days={missing_days}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
