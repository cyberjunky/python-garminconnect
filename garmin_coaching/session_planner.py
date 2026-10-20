"""Daily session planner merging macrocycle phase + readiness zone."""

from __future__ import annotations

from datetime import date
from typing import Any

from garmin_coaching.macrocycle import MacrocyclePhase, active_phase

_WEEKDAY_SESSION: dict[int, dict[str, Any]] = {
    0: {"action": "rest", "sport": "rest", "duration_min": 0, "title": "Descanso"},
    1: {"action": "train", "sport": "run", "duration_min": 55, "title": "Run Z2"},
    2: {
        "action": "train",
        "sport": "walk",
        "duration_min": 35,
        "title": "Caminata Z1-Z2",
    },
    3: {"action": "train", "sport": "run", "duration_min": 60, "title": "Run Z2"},
    4: {
        "action": "rest",
        "sport": "walk",
        "duration_min": 0,
        "title": "Descanso o caminata opcional",
    },
    5: {
        "action": "train",
        "sport": "long",
        "duration_min": 80,
        "title": "Sesion larga Z2",
    },
    6: {
        "action": "train",
        "sport": "recovery",
        "duration_min": 35,
        "title": "Recuperacion activa",
    },
}


def plan_session(
    readiness: dict[str, Any] | None,
    on_day: date | None = None,
    phase: MacrocyclePhase | None = None,
) -> dict[str, Any]:
    today = on_day or date.today()
    phase = phase or active_phase(today)
    zone = (readiness or {}).get("zone")

    base = dict(_WEEKDAY_SESSION.get(today.weekday(), _WEEKDAY_SESSION[0]))
    base["hr_cap"] = phase.hr_cap
    base["phase_code"] = phase.code
    base["phase_name"] = phase.name
    base["date"] = today.isoformat()

    if phase.code == "R0" and base["action"] == "train":
        base = {
            **base,
            "sport": "walk",
            "duration_min": min(base["duration_min"], phase.max_duration_min, 45),
            "title": "Caminata Z1-Z2",
            "details": ["Fase recuperacion: solo Z1-Z2, sin intensidad."],
        }
    elif phase.code in ("R1", "R5") and base.get("sport") == "long":
        base["sport"] = (
            "bike"
            if phase.sport.startswith("bike") or "bike" in phase.sport
            else base["sport"]
        )
        base["duration_min"] = min(base["duration_min"], phase.max_duration_min)
    elif phase.code == "R3" and base.get("sport") == "long":
        base["sport"] = "run"
        base["duration_min"] = min(90, phase.max_duration_min)
        base["title"] = "Long run Z2"
    elif phase.code == "R4":
        base = {
            "action": "race",
            "sport": "run",
            "duration_min": 150,
            "hr_cap": 182,
            "title": "Media Maraton Bogota",
        }

    base["duration_min"] = min(base.get("duration_min") or 0, phase.max_duration_min)

    if zone == "ROJO":
        base["details"] = ["Readiness ROJO: priorizar descanso."]
    elif zone == "AMARILLO":
        base["duration_min"] = max(20, int((base.get("duration_min") or 30) * 0.8))
        base["details"] = ["Readiness AMARILLO: sesion recortada."]

    if not base.get("details"):
        base["details"] = [
            f"FC techo {base.get('hr_cap')} bpm.",
            f"Duracion max {base.get('duration_min')} min.",
        ]

    return base
