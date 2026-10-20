"""Readiness classification and daily plan helpers."""

from __future__ import annotations

from typing import Any

DEFAULT_THRESHOLDS: dict[str, float] = {
    "sleep_h": 7.5,
    "sleep_score": 84.0,
    "hrv": 45.0,
    "stress_max": 27.0,
    "bb_change": 61.0,
}


def classify(m: dict[str, Any], th: dict[str, float]) -> tuple[str, int, str]:
    checks = [
        m.get("sleep_h") is not None and m["sleep_h"] >= th["sleep_h"],
        m.get("sleep_score") is not None and m["sleep_score"] >= th["sleep_score"],
        m.get("hrv") is not None and m["hrv"] >= th["hrv"],
        m.get("stress") is not None and m["stress"] <= th["stress_max"],
        m.get("bb_change") is not None and m["bb_change"] >= th["bb_change"],
    ]
    score_ok = sum(checks)

    red_flag = (
        m.get("hrv_status") == "UNBALANCED" and (m.get("sleep_h") or 0) < th["sleep_h"]
    )

    if red_flag or score_ok <= 2:
        return "ROJO", score_ok, "Solo recuperacion/Z1-Z2 30-60 min o descanso."
    if score_ok == 3:
        return (
            "AMARILLO",
            score_ok,
            "Mantener entrenamiento pero recortar 15-25% o bajar intensidad.",
        )
    return "VERDE", score_ok, "Apto para calidad (tempo/VO2) o fondo >2h segun agenda."


def _median_numeric(values: list[Any]) -> float | None:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    nums_sorted = sorted(nums)
    mid = len(nums_sorted) // 2
    if len(nums_sorted) % 2:
        return nums_sorted[mid]
    return (nums_sorted[mid - 1] + nums_sorted[mid]) / 2.0


def derive_thresholds_from_history(
    metrics: list[dict[str, Any]], base: dict[str, float] | None = None
) -> dict[str, float]:
    base = dict(base or DEFAULT_THRESHOLDS)
    if not metrics:
        return base

    sleep_h = _median_numeric([m.get("sleep_h") for m in metrics])
    sleep_score = _median_numeric([m.get("sleep_score") for m in metrics])
    hrv = _median_numeric([m.get("hrv") for m in metrics])
    stress = _median_numeric([m.get("stress") for m in metrics])
    bb_change = _median_numeric([m.get("bb_change") for m in metrics])

    auto = dict(base)
    if sleep_h is not None:
        auto["sleep_h"] = round(sleep_h, 2)
    if sleep_score is not None:
        auto["sleep_score"] = round(sleep_score, 1)
    if hrv is not None:
        auto["hrv"] = round(hrv, 1)
    if stress is not None:
        auto["stress_max"] = round(stress, 1)
    if bb_change is not None:
        auto["bb_change"] = round(bb_change, 1)
    return auto


def build_daily_plan(today_readiness: dict[str, Any] | None) -> dict[str, Any]:
    if not today_readiness:
        return {
            "zone": None,
            "session": "No data",
            "details": ["No readiness data available for today."],
        }

    zone = today_readiness.get("zone")
    if zone == "VERDE":
        return {
            "zone": zone,
            "session": "Calidad",
            "details": [
                "Option A Tempo: 3x10 min @ tempo, 3 min recoveries.",
                "Option B VO2: 5x3 min hard, 3 min recoveries.",
                "If schedule allows: long ride >2h in Z2.",
            ],
        }
    if zone == "AMARILLO":
        return {
            "zone": zone,
            "session": "Carga ajustada",
            "details": [
                "Keep planned session but cut volume 15-25%.",
                "Prefer tempo over VO2.",
                "Cap total duration at 60-90 min.",
            ],
        }
    return {
        "zone": zone,
        "session": "Recuperacion",
        "details": [
            "Z1-Z2 30-60 min easy or full rest.",
            "Prioritize sleep and hydration.",
            "Re-evaluate tomorrow before quality work.",
        ],
    }
