#!/usr/bin/env python3
"""Collect daily coaching payload: snapshot + readiness + macrocycle + session."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from garmin_auth import login_client

from garmin_coaching.collector import build_daily_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect daily coaching JSON")
    parser.add_argument(
        "--date", default=None, help="Target date YYYY-MM-DD (default: today)"
    )
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--output", default=None, help="Write JSON to file")
    parser.add_argument(
        "--no-auto-thresholds",
        action="store_true",
        help="Use fixed thresholds instead of personal medians",
    )
    parser.add_argument(
        "--auto-days", type=int, default=60, help="Days for auto thresholds"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = login_client()
    payload = build_daily_payload(
        client,
        target_day=args.date,
        auto_thresholds=not args.no_auto_thresholds,
        auto_days=args.auto_days,
    )

    rendered = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered + "\n", encoding="utf-8")
        print(f"COLLECT_DAILY_WRITTEN {out}")

    if args.json or not args.output:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
