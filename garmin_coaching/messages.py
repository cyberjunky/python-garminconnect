"""WhatsApp message formatting for daily coaching."""

from __future__ import annotations

from datetime import date
from typing import Any

RULE_ROTATION = [
    "Regla: max 2 tazas cafe antes de las 11:00.",
    "Regla: sueno >= 7.5 h esta noche.",
    "Regla: 0 alcohol post-carga.",
    "Regla: ACWR objetivo < 1.3.",
    "Regla: 80% del tiempo en Z1-Z2.",
    "Regla: hidratacion 2.5-3 L/dia.",
    "Regla: proteina >= 110 g/dia.",
]


def format_whatsapp_message(
    payload: dict[str, Any], athlete_name: str = "Diego"
) -> str:
    today = payload.get("date") or date.today().isoformat()
    readiness = payload.get("readiness") or {}
    session = payload.get("session") or {}
    phase = payload.get("macrocycle") or {}
    milestones = payload.get("milestones") or []
    training = payload.get("training_load") or {}

    zone = readiness.get("zone", "?")
    score = readiness.get("score_ok", "?")
    hrv = readiness.get("hrv")
    bb = readiness.get("bb_change")
    status = training.get("status_phrase") or ""
    acwr = training.get("acwr")

    mmb = next((m for m in milestones if m.get("code") == "mmb_2027"), {})
    letras = next((m for m in milestones if m.get("code") == "reto_letras_2027"), {})

    hrv_s = f"{hrv:.0f}" if isinstance(hrv, (int, float)) else "?"
    bb_s = f"+{bb:.0f}" if isinstance(bb, (int, float)) else "?"

    session_line = _session_line(session)
    rule = RULE_ROTATION[date.fromisoformat(today).toordinal() % len(RULE_ROTATION)]

    lines = [
        f"Buenos dias {athlete_name} — {today}",
        f"Readiness: {zone} ({score}/5) | HRV {hrv_s} | BB {bb_s}",
        f"Macrociclo: {phase.get('code')} {phase.get('name')} | mmB: {mmb.get('days_remaining', '?')}d | Letras: {letras.get('days_remaining', '?')}d",
        "",
        f"HOY: {session_line}",
    ]

    if status:
        acwr_s = f"{acwr:.1f}" if isinstance(acwr, (int, float)) else "?"
        lines.append(f"Carga: {status} | ACWR {acwr_s}")

    if session.get("guard_flags"):
        lines.append(f"Guards: {', '.join(session['guard_flags'])}")

    lines.extend(["", rule, "Responde: OK | Descanso | Recortar | ?dudas"])
    return "\n".join(lines)


def _session_line(session: dict[str, Any]) -> str:
    if session.get("action") in ("rest", "race"):
        return session.get("title") or "Descanso"
    sport = session.get("sport", "")
    dur = session.get("duration_min", 0)
    cap = session.get("hr_cap", "")
    title = session.get("title") or sport
    return f"{title} — {dur} min, FC techo {cap} bpm"
