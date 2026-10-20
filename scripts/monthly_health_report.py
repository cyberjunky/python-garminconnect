#!/usr/bin/env python3
"""Monthly health indicators report with summary table.

Usage:
  ./.venv/bin/python scripts/monthly_health_report.py
  ./.venv/bin/python scripts/monthly_health_report.py --month 2026-08
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Disable system/IDE-injected proxies so requests reach Garmin directly.
for _v in (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
    "FTP_PROXY",
    "ftp_proxy",
):
    os.environ.pop(_v, None)
os.environ["no_proxy"] = "*"
os.environ["NO_PROXY"] = "*"

import requests as _requests  # noqa: E402 - after proxy/sys.path setup

_orig_session_init = _requests.Session.__init__


def _no_proxy_session_init(self, *a, **kw):
    _orig_session_init(self, *a, **kw)
    self.trust_env = False


_requests.Session.__init__ = _no_proxy_session_init

from garmin_auth import login_client  # noqa: E402 - after proxy/sys.path setup

if TYPE_CHECKING:
    from garminconnect import Garmin


def parse_args() -> argparse.Namespace:
    today = date.today()
    default_month = f"{today.year}-{today.month:02d}"
    parser = argparse.ArgumentParser(description="Monthly Garmin health indicators")
    parser.add_argument(
        "--month", default=default_month, help="Month YYYY-MM (default: current)"
    )
    return parser.parse_args()


def get_client() -> Garmin:
    return login_client()


def _safe(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception:
        return None


def _sleep_fields(payload: dict | None) -> dict[str, Any]:
    if not payload:
        return {}
    dsd = payload.get("dailySleepDTO") or {}
    total_s = dsd.get("sleepTimeSeconds")
    sleep_h = round(total_s / 3600, 2) if isinstance(total_s, (int, float)) else None
    scores = dsd.get("sleepScores") or {}
    sleep_score = (scores.get("overall") or {}).get("value")
    deep_s = dsd.get("deepSleepSeconds")
    rem_s = dsd.get("remSleepSeconds")
    deep_pct = round(deep_s / total_s * 100) if total_s and deep_s else None
    rem_pct = round(rem_s / total_s * 100) if total_s and rem_s else None
    spo2 = dsd.get("averageSpO2Value")
    return {
        "sleep_h": sleep_h,
        "sleep_score": sleep_score,
        "deep_pct": deep_pct,
        "rem_pct": rem_pct,
        "spo2": spo2,
    }


def _stats_fields(payload: dict | None) -> dict[str, Any]:
    if not payload:
        return {}
    return {
        "steps": payload.get("totalSteps"),
        "active_kcal": payload.get("activeKilocalories"),
        "resting_hr": payload.get("restingHeartRate"),
        "avg_stress": payload.get("averageStressLevel"),
        "body_battery": payload.get("bodyBatteryMostRecentValue"),
    }


def _hrv_fields(payload: dict | None) -> dict[str, Any]:
    if not payload:
        return {}
    summary = payload.get("hrvSummary") or {}
    return {"hrv": summary.get("lastNight")}


def fetch_day(client: Garmin, ds: str) -> dict[str, Any]:
    stats = _safe(client.get_stats, ds) or {}
    sleep_raw = _safe(client.get_sleep_data, ds)
    hrv_raw = _safe(client.get_hrv_data, ds)

    row: dict[str, Any] = {"date": ds}
    row.update(_stats_fields(stats))
    row.update(_sleep_fields(sleep_raw))
    row.update(_hrv_fields(hrv_raw))
    return row


def _fmt(val, fmt=".0f", missing="—"):
    if val is None:
        return missing
    try:
        return format(val, fmt)
    except (TypeError, ValueError):
        return missing


def _trend(values: list[float | None]) -> str:
    clean = [v for v in values if v is not None]
    if len(clean) < 3:
        return ""
    avg_first = sum(clean[: len(clean) // 2]) / (len(clean) // 2)
    avg_last = sum(clean[len(clean) // 2 :]) / (len(clean) - len(clean) // 2)
    diff = avg_last - avg_first
    if abs(diff) < 0.03 * avg_first:
        return "→"
    return "↑" if diff > 0 else "↓"


def _avg(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 1) if clean else None


def print_table(rows: list[dict[str, Any]], month_label: str) -> None:
    cols = [
        ("Fecha", "date", "10s", None),
        ("Pasos", "steps", "6.0f", None),
        ("kCal", "active_kcal", "5.0f", None),
        ("FC Rep", "resting_hr", "6.0f", "bpm"),
        ("Estrés", "avg_stress", "6.0f", None),
        ("BB", "body_battery", "4.0f", None),
        ("Sueño h", "sleep_h", "7.2f", "h"),
        ("S.Score", "sleep_score", "7.0f", None),
        ("REM%", "rem_pct", "5.0f", "%"),
        ("Prof%", "deep_pct", "5.0f", "%"),
        ("SpO2", "spo2", "5.1f", "%"),
        ("HRV", "hrv", "4.0f", "ms"),
    ]

    header = "  ".join(f"{label:<{len(label)}}" for label, *_ in cols)
    sep = "  ".join("-" * max(len(label), 6) for label, *_ in cols)

    print(f"\n{'=' * len(sep)}")
    print(f"  INDICADORES DE SALUD — {month_label}")
    print(f"{'=' * len(sep)}")
    print(header)
    print(sep)

    for row in rows:
        parts = []
        for label, key, fmt, _unit in cols:
            val = row.get(key)
            if key == "date":
                parts.append(f"{val:<10}")
            else:
                parts.append(f"{_fmt(val, fmt):<{max(len(label), 6)}}")
        print("  ".join(parts))

    # --- Summary ---
    print(sep)
    print("PROMEDIO", end="  ")
    parts = []
    all_vals: dict[str, list] = {key: [r.get(key) for r in rows] for _, key, *_ in cols}
    for label, key, fmt, _unit in cols:
        if key == "date":
            parts.append(f"{'Promedio':<10}")
        else:
            avg = _avg(all_vals[key])
            parts.append(f"{_fmt(avg, fmt):<{max(len(label), 6)}}")
    # Replace the hand-written "PROMEDIO" prefix with the first column slot
    line_parts = ["  ".join(parts)]
    print(line_parts[0])

    print(f"\n{'=' * len(sep)}")
    print("TENDENCIAS DEL MES")
    print(f"{'=' * len(sep)}")

    trend_keys = [
        ("Pasos", "steps"),
        ("FC Reposo", "resting_hr"),
        ("Estrés", "avg_stress"),
        ("Sueño (h)", "sleep_h"),
        ("Score Sueño", "sleep_score"),
        ("HRV", "hrv"),
        ("SpO2", "spo2"),
    ]
    for label, key in trend_keys:
        vals = [r.get(key) for r in rows]
        avg = _avg(vals)
        t = _trend(vals)
        clean = [v for v in vals if v is not None]
        mn = min(clean) if clean else None
        mx = max(clean) if clean else None
        print(
            f"  {label:<14}  avg={_fmt(avg):>7}  min={_fmt(mn):>7}  max={_fmt(mx):>7}  {t}"
        )

    print(f"\n{'=' * len(sep)}")
    days_with_data = sum(1 for r in rows if r.get("steps") is not None)
    print(f"  Días con datos: {days_with_data}/{len(rows)}")
    print(f"{'=' * len(sep)}\n")


def main() -> int:
    args = parse_args()
    try:
        year, month = map(int, args.month.split("-"))
    except ValueError:
        print("ERROR: --month debe tener formato YYYY-MM")
        return 2

    month_label = f"{year}-{month:02d}"

    # Build date range: first of month up to today (or last day of month)
    start = date(year, month, 1)
    if month == 12:
        end_of_month = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = date(year, month + 1, 1) - timedelta(days=1)
    end = min(end_of_month, date.today())

    print("Conectando a Garmin Connect…")
    try:
        client = get_client()
    except Exception as e:
        print(f"ERROR de autenticación: {e}")
        return 1

    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)

    rows: list[dict[str, Any]] = []
    total = len(days)
    for i, day in enumerate(days, 1):
        ds = day.isoformat()
        print(f"\r  Obteniendo {ds} ({i}/{total})…", end="", flush=True)
        rows.append(fetch_day(client, ds))

    print("\r" + " " * 50 + "\r", end="")

    print_table(rows, month_label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
