#!/usr/bin/env python3
"""Apply weekly_sport_load migration via Supabase service role (idempotent)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260922_weekly_sport_load.sql"


def main() -> int:
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Missing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY", file=sys.stderr)
        return 1

    from supabase import create_client

    client = create_client(url, key)
    try:
        client.table("weekly_sport_load").select("week_start").limit(1).execute()
        print("weekly_sport_load: already exists")
        return 0
    except Exception as exc:
        msg = str(exc).lower()
        if (
            "weekly_sport_load" not in msg
            and "relation" not in msg
            and "schema cache" not in msg
        ):
            print(f"check failed: {exc}", file=sys.stderr)
            return 1

    print(
        "Table weekly_sport_load missing. Run supabase/migrations/20260922_weekly_sport_load.sql "
        "in Supabase SQL Editor (Dashboard → SQL).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
