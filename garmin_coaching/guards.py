"""Hard training guards — rules that override session plans."""

from __future__ import annotations

from typing import Any


def apply_guards(
    readiness: dict[str, Any],
    training_load: dict[str, Any] | None,
    session: dict[str, Any],
) -> dict[str, Any]:
    """Apply guard rules; returns adjusted session + guard flags."""
    zone = readiness.get("zone")
    acwr = _float_or_none((training_load or {}).get("acwr"))
    status = (training_load or {}).get("status_phrase") or ""
    flags: list[str] = []
    adjusted = dict(session)

    if zone == "ROJO":
        flags.append("readiness_rojo")
        adjusted = _force_rest(
            session, "Readiness ROJO — descanso total o caminata <=30 min FC<110"
        )

    if acwr is not None and acwr > 1.5:
        flags.append("acwr_very_high")
        adjusted = _force_rest(session, f"ACWR {acwr:.1f} VERY HIGH — descanso 48h")
    elif acwr is not None and acwr > 1.3:
        flags.append("acwr_high")
        adjusted = _cut_volume(session, 0.25, f"ACWR {acwr:.1f} — recortar 25% volumen")

    if "OVERREACHING" in status.upper():
        flags.append("overreaching")
        if zone != "ROJO":
            adjusted = _force_rest(
                session, f"Training status {status} — solo recuperacion"
            )

    if zone == "AMARILLO" and adjusted.get("action") != "rest":
        flags.append("readiness_amarillo")
        adjusted = _cut_volume(adjusted, 0.20, "Readiness AMARILLO — recortar 20%")

    adjusted["guard_flags"] = flags
    adjusted["guards_applied"] = len(flags) > 0
    return adjusted


def _float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _force_rest(session: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        **session,
        "action": "rest",
        "sport": "rest",
        "duration_min": 0,
        "hr_cap": 110,
        "title": "Descanso",
        "details": [reason, "Re-evaluar manana antes de entrenar."],
        "forced": True,
    }


def _cut_volume(
    session: dict[str, Any], fraction: float, reason: str
) -> dict[str, Any]:
    if session.get("action") == "rest":
        return session
    duration = session.get("duration_min") or 0
    new_duration = max(20, int(duration * (1.0 - fraction))) if duration else 30
    details = list(session.get("details") or [])
    details.insert(0, reason)
    return {**session, "duration_min": new_duration, "details": details, "forced": True}
