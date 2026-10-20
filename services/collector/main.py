"""FastAPI collector worker — POST /collect with Garmin auth + Supabase upsert."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from garmin_auth import login_client  # noqa: E402 - after sys.path setup

from garmin_coaching.collector import build_daily_payload  # noqa: E402 - after sys.path setup
from garmin_coaching.messages import format_whatsapp_message  # noqa: E402 - after sys.path setup
from services.collector.supabase_client import upsert_daily_payload  # noqa: E402 - after sys.path setup

app = FastAPI(title="Garmin Coaching Collector", version="0.1.0")


class CollectResponse(BaseModel):
    ok: bool
    date: str
    zone: str | None
    session_action: str | None
    guard_flags: list[str]
    whatsapp_preview: str
    supabase: dict[str, str] | None = None


class HealthResponse(BaseModel):
    status: str
    supabase_configured: bool


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        supabase_configured=bool(
            os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        ),
    )


@app.post("/collect", response_model=CollectResponse)
def collect(
    target_date: str | None = Query(None, alias="date"),
    write_supabase: bool = Query(True),
    auto_thresholds: bool = Query(True),
) -> CollectResponse:
    if target_date:
        try:
            date.fromisoformat(target_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid date format YYYY-MM-DD") from exc

    try:
        client = login_client(prompt=False)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Garmin auth failed: {exc}") from exc

    try:
        payload = build_daily_payload(
            client,
            target_day=target_date,
            auto_thresholds=auto_thresholds,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Garmin collect failed: {exc}") from exc

    supabase_result = None
    if write_supabase:
        try:
            supabase_result = upsert_daily_payload(payload)
        except RuntimeError:
            supabase_result = {"status": "skipped", "reason": "supabase not configured"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Supabase upsert failed: {exc}") from exc

    session = payload.get("session") or {}
    readiness = payload.get("readiness") or {}
    return CollectResponse(
        ok=True,
        date=payload["date"],
        zone=readiness.get("zone"),
        session_action=session.get("action"),
        guard_flags=session.get("guard_flags") or [],
        whatsapp_preview=payload.get("whatsapp_message") or format_whatsapp_message(payload),
        supabase=supabase_result,
    )


@app.post("/publish-session")
def publish_session(body: dict[str, Any]) -> dict[str, Any]:
    """Optional: publish confirmed session to Garmin (phase 2 hook)."""
    zone = body.get("zone")
    if zone != "VERDE":
        raise HTTPException(status_code=400, detail="Only VERDE sessions can be auto-published")
    return {"status": "not_implemented", "message": "Use publish_weekend_readiness_plan.py manually for now"}


def run() -> None:
    import uvicorn

    port = int(os.environ.get("COLLECTOR_PORT", "8080"))
    uvicorn.run("services.collector.main:app", host="0.0.0.0", port=port, reload=False)  # noqa: S104 - container worker listens on all interfaces


if __name__ == "__main__":
    run()
