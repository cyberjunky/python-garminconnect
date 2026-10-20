"""Macrocycle phases and event milestones for mmB 2027 + Reto Letras."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class MacrocyclePhase:
    code: str
    name: str
    start: date
    end: date
    focus: str
    sport: str
    hr_cap: int
    max_duration_min: int


@dataclass(frozen=True)
class EventMilestone:
    code: str
    name: str
    event_date: date


MILESTONES: tuple[EventMilestone, ...] = (
    EventMilestone("bogota_21k_2026", "vChallenges 21K", date(2026, 12, 26)),
    EventMilestone("mmb_2027", "Media Maraton Bogota 2027", date(2027, 7, 25)),
    EventMilestone("reto_letras_2027", "Reto Mariquita Letras 2027", date(2027, 9, 13)),
    EventMilestone(
        "cartagena_703_2027", "Ironman 70.3 Cartagena 2027", date(2027, 11, 29)
    ),
)

PHASES: tuple[MacrocyclePhase, ...] = (
    MacrocyclePhase(
        "R0",
        "Recuperacion",
        date(2026, 9, 20),
        date(2026, 10, 5),
        "ACWR < 1.0",
        "walk/off",
        128,
        45,
    ),
    MacrocyclePhase(
        "R1",
        "Base aerobica",
        date(2026, 10, 6),
        date(2026, 12, 31),
        "80/20 Z1-Z2",
        "run+bike",
        135,
        75,
    ),
    MacrocyclePhase(
        "R2",
        "Construccion",
        date(2027, 1, 1),
        date(2027, 3, 31),
        "Volumen + 1 tempo/sem",
        "run",
        141,
        90,
    ),
    MacrocyclePhase(
        "R3",
        "Especifico 21K",
        date(2027, 4, 1),
        date(2027, 7, 24),
        "Long run + ritmo mmB",
        "run",
        155,
        120,
    ),
    MacrocyclePhase(
        "R4",
        "Carrera mmB",
        date(2027, 7, 25),
        date(2027, 7, 25),
        "Taper + carrera",
        "race",
        182,
        150,
    ),
    MacrocyclePhase(
        "R5",
        "Transicion ciclismo",
        date(2027, 8, 1),
        date(2027, 8, 31),
        "Fuerza + bici subida",
        "bike",
        141,
        120,
    ),
    MacrocyclePhase(
        "R6",
        "Reto Letras",
        date(2027, 9, 1),
        date(2027, 9, 13),
        "Ascenso + taper",
        "bike",
        155,
        180,
    ),
    MacrocyclePhase(
        "R7",
        "Especifico 70.3",
        date(2027, 10, 1),
        date(2027, 11, 28),
        "Brick + volumen tri",
        "tri",
        155,
        180,
    ),
)


def active_phase(on_day: date | None = None) -> MacrocyclePhase:
    today = on_day or date.today()
    for phase in PHASES:
        if phase.start <= today <= phase.end:
            return phase
    if today < PHASES[0].start:
        return PHASES[0]
    return PHASES[-1]


def days_to_milestones(on_day: date | None = None) -> dict[str, int]:
    today = on_day or date.today()
    return {m.code: (m.event_date - today).days for m in MILESTONES}


def phase_as_dict(phase: MacrocyclePhase) -> dict[str, Any]:
    return {
        "code": phase.code,
        "name": phase.name,
        "start": phase.start.isoformat(),
        "end": phase.end.isoformat(),
        "focus": phase.focus,
        "sport": phase.sport,
        "hr_cap": phase.hr_cap,
        "max_duration_min": phase.max_duration_min,
    }


def milestones_as_dict(on_day: date | None = None) -> list[dict[str, Any]]:
    today = on_day or date.today()
    days = days_to_milestones(today)
    return [
        {
            "code": m.code,
            "name": m.name,
            "event_date": m.event_date.isoformat(),
            "days_remaining": days[m.code],
        }
        for m in MILESTONES
    ]
