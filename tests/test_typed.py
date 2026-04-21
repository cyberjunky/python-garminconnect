"""Unit tests for the optional typed namespace wrapper.

These tests cover the ``g.typed`` accessor introduced in the ``[typed]``
extra: every wrapper method delegates to the underlying raw ``Garmin`` method
and validates the response with a Pydantic model.

The tests mock each raw method with canned payloads pulled from real Garmin
responses (fields renamed / truncated so we don't commit a full user record)
and assert:

    * happy-path: the returned model exposes the expected attributes
    * ``extra='allow'``: unknown fields round-trip into ``model_extra``
      instead of failing validation
    * missing fields: all modelled fields tolerate absence (default ``None``)
    * validation errors: structural failures raise
      ``GarminConnectResponseValidationError`` with ``.raw`` preserved
    * list endpoints: empty / non-list responses return ``[]``
    * ``get_hrv_data``: a ``None`` response passes through unchanged

Run with::

    python -m pytest tests/test_typed.py -v
"""

from unittest.mock import MagicMock

import pytest

import garminconnect
from garminconnect.typed import (
    Activity,
    BodyBatteryEntry,
    DailyStats,
    GarminConnectResponseValidationError,
    HrvData,
    SleepData,
    TrainingReadiness,
    TypedGarmin,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def garmin() -> garminconnect.Garmin:
    """Return a Garmin instance with no network dependency."""
    g = garminconnect.Garmin("test@example.com", "password")
    g.display_name = "test-display"
    g.full_name = "Test User"
    return g


# Sample payloads are deliberately small — just enough to exercise validation
# and happy-path access. Real Garmin responses are much larger; the models are
# permissive (``extra='allow'``) so extra fields are accepted silently.


SAMPLE_DAILY_STATS: dict = {
    "userProfileId": 12345,
    "calendarDate": "2026-04-21",
    "totalSteps": 8500,
    "totalDistanceMeters": 6200.5,
    "totalKilocalories": 2450.0,
    "activeKilocalories": 700.0,
    "restingHeartRate": 54,
    "minHeartRate": 48,
    "maxHeartRate": 142,
    "highlyActiveSeconds": 1200,
    "moderateIntensityMinutes": 22,
    "vigorousIntensityMinutes": 4,
    "bodyBatteryHighestValue": 92,
    "bodyBatteryLowestValue": 38,
    "averageStressLevel": 29,
    "privacyProtected": False,
}


SAMPLE_SLEEP_DATA: dict = {
    "dailySleepDTO": {
        "userProfilePK": 12345,
        "calendarDate": "2026-04-21",
        "sleepTimeSeconds": 25200,
        "napTimeSeconds": 0,
        "deepSleepSeconds": 5400,
        "lightSleepSeconds": 14400,
        "remSleepSeconds": 4800,
        "awakeSleepSeconds": 600,
        "sleepStartTimestampGMT": 1761100200000,
        "sleepEndTimestampGMT": 1761125400000,
        "avgSleepHRV": 52.3,
        "avgSpO2": 96.0,
        "avgRespirationValue": 14.2,
        "sleepScores": {
            "overall": {"value": 84, "qualifierKey": "GOOD"},
            "totalDuration": {"value": 90, "qualifierKey": "EXCELLENT"},
        },
    }
}


SAMPLE_HRV_DATA: dict = {
    "userProfilePK": 12345,
    "hrvSummary": {
        "calendarDate": "2026-04-21",
        "weeklyAvg": 48.5,
        "lastNightAvg": 52.0,
        "lastNight5MinHigh": 71.0,
        "status": "BALANCED",
        "feedbackPhrase": "BALANCED_1",
        "baseline": {
            "lowUpper": 42.0,
            "balancedLow": 43.0,
            "balancedUpper": 58.0,
            "markerValue": 0.5,
        },
    },
    "hrvReadings": [],
    "startTimestampGMT": "2026-04-20T22:00:00.0",
    "endTimestampGMT": "2026-04-21T06:00:00.0",
}


SAMPLE_BODY_BATTERY: list = [
    {
        "date": "2026-04-21",
        "charged": 58,
        "drained": 32,
        "startTimestampGMT": "2026-04-21T00:00:00.0",
        "endTimestampGMT": "2026-04-21T23:59:59.0",
        "bodyBatteryValuesArray": [
            [1761100200000, 65],
            [1761100500000, 66],
        ],
    }
]


SAMPLE_TRAINING_READINESS: list = [
    {
        "userProfilePK": 12345,
        "calendarDate": "2026-04-21",
        "timestamp": "2026-04-21T06:12:00.0",
        "timestampLocal": "2026-04-21T10:12:00.0",
        "deviceId": 3412882339,
        "score": 72,
        "level": "HIGH",
        "feedbackLong": "You are well recovered.",
        "feedbackShort": "READY",
        "sleepScore": 84,
        "sleepScoreFactorPercent": 85,
        "recoveryTime": 0,
        "recoveryTimeChangePhrase": "REACHED_ZERO",
        "acwrFactorPercent": 90,
        "hrvFactorPercent": 80,
        "inputContext": "AFTER_WAKEUP_RESET",
    }
]


SAMPLE_ACTIVITY: list = [
    {
        "activityId": 19876543210,
        "activityName": "Morning Run",
        "startTimeLocal": "2026-04-21 06:30:00",
        "startTimeGMT": "2026-04-21 02:30:00",
        "activityType": {
            "typeId": 1,
            "typeKey": "running",
            "parentTypeId": 17,
            "isHidden": False,
        },
        "duration": 2400.0,
        "movingDuration": 2380.0,
        "distance": 6200.0,
        "elevationGain": 45.0,
        "elevationLoss": 42.0,
        "averageHR": 148.0,
        "maxHR": 172.0,
        "calories": 512.0,
        "aerobicTrainingEffect": 3.2,
        "anaerobicTrainingEffect": 0.8,
        "activityTrainingLoad": 98.5,
        "averageRunningCadenceInStepsPerMinute": 178.0,
    }
]


# ---------------------------------------------------------------------------
# Accessor plumbing
# ---------------------------------------------------------------------------


def test_typed_returns_typed_garmin(garmin: garminconnect.Garmin) -> None:
    """``g.typed`` returns a ``TypedGarmin`` wrapping the same instance."""
    assert isinstance(garmin.typed, TypedGarmin)
    assert garmin.typed._garmin is garmin


def test_typed_is_cached(garmin: garminconnect.Garmin) -> None:
    """``g.typed`` returns the same wrapper across calls (cached_property)."""
    assert garmin.typed is garmin.typed


# ---------------------------------------------------------------------------
# Happy path — each wrapper returns the expected model with key fields set
# ---------------------------------------------------------------------------


def test_get_stats_returns_daily_stats(garmin: garminconnect.Garmin) -> None:
    garmin.get_stats = MagicMock(return_value=SAMPLE_DAILY_STATS)

    stats = garmin.typed.get_stats("2026-04-21")

    assert isinstance(stats, DailyStats)
    assert stats.total_steps == 8500
    assert stats.resting_heart_rate == 54
    assert stats.moderate_intensity_minutes == 22
    assert stats.body_battery_highest_value == 92
    garmin.get_stats.assert_called_once_with("2026-04-21")


def test_get_user_summary_returns_daily_stats(garmin: garminconnect.Garmin) -> None:
    """``get_user_summary`` uses the same ``DailyStats`` model."""
    garmin.get_user_summary = MagicMock(return_value=SAMPLE_DAILY_STATS)

    stats = garmin.typed.get_user_summary("2026-04-21")

    assert isinstance(stats, DailyStats)
    assert stats.total_steps == 8500
    garmin.get_user_summary.assert_called_once_with("2026-04-21")


def test_get_sleep_data_returns_nested_dto(garmin: garminconnect.Garmin) -> None:
    garmin.get_sleep_data = MagicMock(return_value=SAMPLE_SLEEP_DATA)

    sleep = garmin.typed.get_sleep_data("2026-04-21")

    assert isinstance(sleep, SleepData)
    assert sleep.daily_sleep_dto is not None
    assert sleep.daily_sleep_dto.sleep_time_seconds == 25200
    assert sleep.daily_sleep_dto.deep_sleep_seconds == 5400
    assert sleep.daily_sleep_dto.avg_sleep_hrv == 52.3
    # Nested scores are also typed
    assert sleep.daily_sleep_dto.sleep_scores is not None
    assert sleep.daily_sleep_dto.sleep_scores.overall is not None
    assert sleep.daily_sleep_dto.sleep_scores.overall.value == 84


def test_get_hrv_data_returns_hrv_model(garmin: garminconnect.Garmin) -> None:
    garmin.get_hrv_data = MagicMock(return_value=SAMPLE_HRV_DATA)

    hrv = garmin.typed.get_hrv_data("2026-04-21")

    assert isinstance(hrv, HrvData)
    assert hrv.hrv_summary is not None
    assert hrv.hrv_summary.weekly_avg == 48.5
    assert hrv.hrv_summary.status == "BALANCED"
    assert hrv.hrv_summary.baseline is not None
    assert hrv.hrv_summary.baseline.balanced_upper == 58.0


def test_get_hrv_data_passes_through_none(garmin: garminconnect.Garmin) -> None:
    """``get_hrv_data`` may legitimately return ``None`` — the wrapper keeps that."""
    garmin.get_hrv_data = MagicMock(return_value=None)

    assert garmin.typed.get_hrv_data("2026-04-21") is None


def test_get_body_battery_returns_list(garmin: garminconnect.Garmin) -> None:
    garmin.get_body_battery = MagicMock(return_value=SAMPLE_BODY_BATTERY)

    entries = garmin.typed.get_body_battery("2026-04-21", "2026-04-21")

    assert len(entries) == 1
    entry = entries[0]
    assert isinstance(entry, BodyBatteryEntry)
    assert entry.date == "2026-04-21"
    assert entry.charged == 58
    assert entry.drained == 32
    assert entry.body_battery_values_array == [[1761100200000, 65], [1761100500000, 66]]


def test_get_body_battery_non_list_returns_empty(garmin: garminconnect.Garmin) -> None:
    """Defensive: if Garmin returns something unexpected, return ``[]``."""
    garmin.get_body_battery = MagicMock(return_value=None)

    assert garmin.typed.get_body_battery("2026-04-21") == []


def test_get_training_readiness_returns_list(garmin: garminconnect.Garmin) -> None:
    """Garmin returns a list of snapshots even though the raw method is typed as dict."""
    garmin.get_training_readiness = MagicMock(return_value=SAMPLE_TRAINING_READINESS)

    readings = garmin.typed.get_training_readiness("2026-04-21")

    assert len(readings) == 1
    r = readings[0]
    assert isinstance(r, TrainingReadiness)
    assert r.score == 72
    assert r.level == "HIGH"
    assert r.recovery_time == 0
    assert r.recovery_time_change_phrase == "REACHED_ZERO"
    assert r.input_context == "AFTER_WAKEUP_RESET"


def test_get_training_readiness_non_list_returns_empty(
    garmin: garminconnect.Garmin,
) -> None:
    garmin.get_training_readiness = MagicMock(return_value={})

    assert garmin.typed.get_training_readiness("2026-04-21") == []


def test_get_activities_by_date_returns_list(garmin: garminconnect.Garmin) -> None:
    garmin.get_activities_by_date = MagicMock(return_value=SAMPLE_ACTIVITY)

    activities = garmin.typed.get_activities_by_date("2026-04-21", "2026-04-21")

    assert len(activities) == 1
    a = activities[0]
    assert isinstance(a, Activity)
    assert a.activity_id == 19876543210
    assert a.activity_name == "Morning Run"
    assert a.distance == 6200.0
    assert a.activity_type is not None
    assert a.activity_type.type_key == "running"


def test_get_activities_by_date_forwards_optional_args(
    garmin: garminconnect.Garmin,
) -> None:
    """Activity filters pass through to the underlying method unchanged."""
    garmin.get_activities_by_date = MagicMock(return_value=[])

    garmin.typed.get_activities_by_date(
        "2026-01-01", "2026-04-21", activitytype="running", sortorder="asc"
    )

    garmin.get_activities_by_date.assert_called_once_with(
        "2026-01-01", "2026-04-21", "running", "asc"
    )


# ---------------------------------------------------------------------------
# Schema tolerance — extra fields, missing fields
# ---------------------------------------------------------------------------


def test_extra_fields_are_tolerated(garmin: garminconnect.Garmin) -> None:
    """Garmin can (and does) add fields; they must not break validation."""
    payload = {**SAMPLE_DAILY_STATS, "brandNewFieldFromGarmin2030": "hello"}
    garmin.get_stats = MagicMock(return_value=payload)

    stats = garmin.typed.get_stats("2026-04-21")

    # Unknown field is preserved in model_extra for callers that want it
    assert stats.model_extra is not None
    assert stats.model_extra.get("brandNewFieldFromGarmin2030") == "hello"


def test_missing_fields_default_to_none(garmin: garminconnect.Garmin) -> None:
    """An almost-empty response must still validate."""
    garmin.get_stats = MagicMock(return_value={"userProfileId": 1})

    stats = garmin.typed.get_stats("2026-04-21")

    assert stats.user_profile_id == 1
    assert stats.total_steps is None
    assert stats.resting_heart_rate is None


# ---------------------------------------------------------------------------
# Validation error carries the raw payload
# ---------------------------------------------------------------------------


def test_validation_error_preserves_raw(garmin: garminconnect.Garmin) -> None:
    """Structural failures raise a typed error with ``.raw`` set."""
    # A list where a dict is expected — structural mismatch
    bad_payload = ["not", "a", "dict"]
    garmin.get_stats = MagicMock(return_value=bad_payload)

    with pytest.raises(GarminConnectResponseValidationError) as excinfo:
        garmin.typed.get_stats("2026-04-21")

    assert excinfo.value.raw is bad_payload
    assert excinfo.value.pydantic_error is not None
    assert "get_stats" in str(excinfo.value)
