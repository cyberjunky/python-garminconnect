"""Optional Pydantic response models for typed Garmin Connect API access.

Experimental — model shapes and the ``g.typed`` surface may change between
minor releases until the pattern stabilises. Pin a specific version if you
depend on typed response shapes.

The typed namespace wraps a small, curated set of high-value endpoints. All
other endpoints remain available via the standard ``g.get_*()`` methods with
``dict[str, Any]`` responses — this layer is purely additive.

Usage:
    from garminconnect import Garmin

    g = Garmin(email, password)
    g.login()

    raw = g.get_stats("2026-04-21")           # dict[str, Any] — unchanged
    stats = g.typed.get_stats("2026-04-21")   # DailyStats (Pydantic)
    print(stats.total_steps, stats.resting_heart_rate)

Install the optional dependency first::

    pip install 'garminconnect[typed]'

On validation failure, raises :class:`GarminConnectResponseValidationError`
with the unvalidated response preserved as ``.raw`` so callers can still
access the data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

try:
    from pydantic import BaseModel, ConfigDict, Field
    from pydantic import ValidationError as _PydanticValidationError
except ImportError as _exc:  # pragma: no cover - exercised via integration
    raise ImportError(
        "The `typed` namespace requires pydantic. Install it with:\n"
        "    pip install 'garminconnect[typed]'"
    ) from _exc

_M = TypeVar("_M", bound=BaseModel)

if TYPE_CHECKING:
    from . import Garmin


class GarminConnectResponseValidationError(Exception):
    """Raised when a Garmin response fails Pydantic validation.

    The unvalidated response is available as ``raw`` so callers can still
    inspect the data. The underlying :class:`pydantic.ValidationError` is
    available as ``pydantic_error``.
    """

    def __init__(
        self,
        message: str,
        raw: Any,
        pydantic_error: _PydanticValidationError,
    ) -> None:
        super().__init__(message)
        self.raw = raw
        self.pydantic_error = pydantic_error


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

# ``extra='allow'`` is deliberate: Garmin occasionally adds fields with new
# firmware / subscription tiers, and we don't want validation failures for
# benign additions. ``populate_by_name=True`` lets callers construct models
# using either the Python attribute name or the JSON alias, which is useful
# for tests.
_COMMON_CONFIG = ConfigDict(
    extra="allow",
    populate_by_name=True,
)


class _BaseResponse(BaseModel):
    model_config = _COMMON_CONFIG


# ---------------------------------------------------------------------------
# Daily Stats (get_stats / get_user_summary)
# ---------------------------------------------------------------------------


class DailyStats(_BaseResponse):
    """Daily summary returned by ``get_stats`` and ``get_user_summary``.

    Only the most commonly consumed fields are modelled explicitly; additional
    fields are accessible through ``model_extra`` or by dumping the model.
    """

    user_profile_id: int | None = Field(default=None, alias="userProfileId")
    calendar_date: str | None = Field(default=None, alias="calendarDate")

    total_steps: int | None = Field(default=None, alias="totalSteps")
    daily_step_goal: int | None = Field(default=None, alias="dailyStepGoal")
    total_distance_meters: float | None = Field(
        default=None, alias="totalDistanceMeters"
    )

    total_kilocalories: float | None = Field(default=None, alias="totalKilocalories")
    active_kilocalories: float | None = Field(default=None, alias="activeKilocalories")
    bmr_kilocalories: float | None = Field(default=None, alias="bmrKilocalories")
    wellness_kilocalories: float | None = Field(
        default=None, alias="wellnessKilocalories"
    )

    min_heart_rate: int | None = Field(default=None, alias="minHeartRate")
    max_heart_rate: int | None = Field(default=None, alias="maxHeartRate")
    resting_heart_rate: int | None = Field(default=None, alias="restingHeartRate")

    sleeping_seconds: int | None = Field(default=None, alias="sleepingSeconds")
    sedentary_seconds: int | None = Field(default=None, alias="sedentarySeconds")
    active_seconds: int | None = Field(default=None, alias="activeSeconds")
    highly_active_seconds: int | None = Field(default=None, alias="highlyActiveSeconds")

    moderate_intensity_minutes: int | None = Field(
        default=None, alias="moderateIntensityMinutes"
    )
    vigorous_intensity_minutes: int | None = Field(
        default=None, alias="vigorousIntensityMinutes"
    )

    floors_ascended: float | None = Field(default=None, alias="floorsAscended")
    floors_descended: float | None = Field(default=None, alias="floorsDescended")

    average_stress_level: int | None = Field(default=None, alias="averageStressLevel")
    max_stress_level: int | None = Field(default=None, alias="maxStressLevel")
    stress_duration: int | None = Field(default=None, alias="stressDuration")
    rest_stress_duration: int | None = Field(default=None, alias="restStressDuration")

    body_battery_charged_value: int | None = Field(
        default=None, alias="bodyBatteryChargedValue"
    )
    body_battery_drained_value: int | None = Field(
        default=None, alias="bodyBatteryDrainedValue"
    )
    body_battery_highest_value: int | None = Field(
        default=None, alias="bodyBatteryHighestValue"
    )
    body_battery_lowest_value: int | None = Field(
        default=None, alias="bodyBatteryLowestValue"
    )

    privacy_protected: bool | None = Field(default=None, alias="privacyProtected")


# ---------------------------------------------------------------------------
# Sleep (get_sleep_data)
# ---------------------------------------------------------------------------


class SleepScoreValue(_BaseResponse):
    """One component of the Garmin sleep score breakdown (value + qualifier)."""

    value: int | None = None
    qualifier_key: str | None = Field(default=None, alias="qualifierKey")


class SleepScores(_BaseResponse):
    """Sub-scores that make up the overall nightly sleep score."""

    overall: SleepScoreValue | None = None
    total_duration: SleepScoreValue | None = Field(default=None, alias="totalDuration")
    stress: SleepScoreValue | None = None
    awake_count: SleepScoreValue | None = Field(default=None, alias="awakeCount")
    rem_percentage: SleepScoreValue | None = Field(default=None, alias="remPercentage")
    restlessness: SleepScoreValue | None = None
    light_percentage: SleepScoreValue | None = Field(
        default=None, alias="lightPercentage"
    )
    deep_percentage: SleepScoreValue | None = Field(
        default=None, alias="deepPercentage"
    )


class DailySleepDTO(_BaseResponse):
    """Nested sleep summary inside a :class:`SleepData` response."""

    user_profile_pk: int | None = Field(default=None, alias="userProfilePK")
    calendar_date: str | None = Field(default=None, alias="calendarDate")

    sleep_time_seconds: int | None = Field(default=None, alias="sleepTimeSeconds")
    nap_time_seconds: int | None = Field(default=None, alias="napTimeSeconds")
    sleep_window_confirmed: bool | None = Field(
        default=None, alias="sleepWindowConfirmed"
    )

    deep_sleep_seconds: int | None = Field(default=None, alias="deepSleepSeconds")
    light_sleep_seconds: int | None = Field(default=None, alias="lightSleepSeconds")
    rem_sleep_seconds: int | None = Field(default=None, alias="remSleepSeconds")
    awake_sleep_seconds: int | None = Field(default=None, alias="awakeSleepSeconds")

    sleep_start_timestamp_gmt: int | None = Field(
        default=None, alias="sleepStartTimestampGMT"
    )
    sleep_end_timestamp_gmt: int | None = Field(
        default=None, alias="sleepEndTimestampGMT"
    )
    sleep_start_timestamp_local: int | None = Field(
        default=None, alias="sleepStartTimestampLocal"
    )
    sleep_end_timestamp_local: int | None = Field(
        default=None, alias="sleepEndTimestampLocal"
    )

    avg_sleep_hrv: float | None = Field(default=None, alias="avgSleepHRV")
    avg_spo2: float | None = Field(default=None, alias="avgSpO2")
    avg_respiration_value: float | None = Field(
        default=None, alias="avgRespirationValue"
    )
    lowest_respiration_value: float | None = Field(
        default=None, alias="lowestRespirationValue"
    )
    highest_respiration_value: float | None = Field(
        default=None, alias="highestRespirationValue"
    )

    sleep_scores: SleepScores | None = Field(default=None, alias="sleepScores")


class SleepData(_BaseResponse):
    """Response for ``get_sleep_data``.

    The most useful summary lives under ``daily_sleep_dto``; callers that want
    per-minute heart rate / movement / SpO2 arrays should use the raw dict via
    ``g.get_sleep_data`` since those arrays are large and rarely needed in
    typed form.
    """

    daily_sleep_dto: DailySleepDTO | None = Field(default=None, alias="dailySleepDTO")


# ---------------------------------------------------------------------------
# HRV (get_hrv_data)
# ---------------------------------------------------------------------------


class HrvBaseline(_BaseResponse):
    """Personal HRV baseline ranges derived from the user's history."""

    low_upper: float | None = Field(default=None, alias="lowUpper")
    balanced_low: float | None = Field(default=None, alias="balancedLow")
    balanced_upper: float | None = Field(default=None, alias="balancedUpper")
    marker_value: float | None = Field(default=None, alias="markerValue")


class HrvSummary(_BaseResponse):
    """Summary of HRV stats (weekly / last-night averages, status, feedback)."""

    calendar_date: str | None = Field(default=None, alias="calendarDate")
    weekly_avg: float | None = Field(default=None, alias="weeklyAvg")
    last_night_avg: float | None = Field(default=None, alias="lastNightAvg")
    last_night_5_min_high: float | None = Field(default=None, alias="lastNight5MinHigh")
    status: str | None = None
    feedback_phrase: str | None = Field(default=None, alias="feedbackPhrase")
    baseline: HrvBaseline | None = None


class HrvData(_BaseResponse):
    """Response for ``get_hrv_data``.

    Note: ``get_hrv_data`` may return ``None`` if HRV data is not available for
    the requested date. The typed wrapper preserves this — ``g.typed.get_hrv_data``
    returns ``HrvData | None``.
    """

    user_profile_pk: int | None = Field(default=None, alias="userProfilePK")
    hrv_summary: HrvSummary | None = Field(default=None, alias="hrvSummary")
    hrv_readings: list[dict[str, Any]] | None = Field(default=None, alias="hrvReadings")
    start_timestamp_gmt: str | None = Field(default=None, alias="startTimestampGMT")
    end_timestamp_gmt: str | None = Field(default=None, alias="endTimestampGMT")
    start_timestamp_local: str | None = Field(default=None, alias="startTimestampLocal")
    end_timestamp_local: str | None = Field(default=None, alias="endTimestampLocal")
    sleep_start_timestamp_gmt: str | None = Field(
        default=None, alias="sleepStartTimestampGMT"
    )
    sleep_end_timestamp_gmt: str | None = Field(
        default=None, alias="sleepEndTimestampGMT"
    )


# ---------------------------------------------------------------------------
# Body Battery (get_body_battery)
# ---------------------------------------------------------------------------


class BodyBatteryEntry(_BaseResponse):
    """One entry from ``get_body_battery``.

    ``get_body_battery`` always returns a list; for a single date the list has
    one entry. ``body_battery_values_array`` is a list of ``[timestamp, level]``
    pairs sampled throughout the day.
    """

    date: str | None = None
    charged: int | None = None
    drained: int | None = None
    start_timestamp_gmt: str | None = Field(default=None, alias="startTimestampGMT")
    end_timestamp_gmt: str | None = Field(default=None, alias="endTimestampGMT")
    start_timestamp_local: str | None = Field(default=None, alias="startTimestampLocal")
    end_timestamp_local: str | None = Field(default=None, alias="endTimestampLocal")
    body_battery_values_array: list[list[Any]] | None = Field(
        default=None, alias="bodyBatteryValuesArray"
    )
    body_battery_value_descriptors_dto_list: list[dict[str, Any]] | None = Field(
        default=None, alias="bodyBatteryValueDescriptorDTOList"
    )


# ---------------------------------------------------------------------------
# Training Readiness (get_training_readiness)
# ---------------------------------------------------------------------------


class TrainingReadiness(_BaseResponse):
    """One snapshot from ``get_training_readiness``.

    The endpoint returns a list of snapshots — typically one per wake-up event
    or scheduled update. Use the snapshot with the most recent ``timestamp``
    for the current reading.

    ``recovery_time`` is reported in **minutes**. When
    ``recovery_time_change_phrase == 'REACHED_ZERO'`` the user is fully
    recovered regardless of the numeric value (Garmin keeps the last assigned
    value after the clock drains).
    """

    user_profile_pk: int | None = Field(default=None, alias="userProfilePK")
    calendar_date: str | None = Field(default=None, alias="calendarDate")
    timestamp: str | None = None
    timestamp_local: str | None = Field(default=None, alias="timestampLocal")
    device_id: int | None = Field(default=None, alias="deviceId")

    score: int | None = None
    level: str | None = None
    feedback_long: str | None = Field(default=None, alias="feedbackLong")
    feedback_short: str | None = Field(default=None, alias="feedbackShort")

    sleep_score: int | None = Field(default=None, alias="sleepScore")
    sleep_score_factor_percent: int | None = Field(
        default=None, alias="sleepScoreFactorPercent"
    )
    sleep_score_factor_feedback: str | None = Field(
        default=None, alias="sleepScoreFactorFeedback"
    )

    recovery_time: int | None = Field(default=None, alias="recoveryTime")
    recovery_time_factor_percent: int | None = Field(
        default=None, alias="recoveryTimeFactorPercent"
    )
    recovery_time_factor_feedback: str | None = Field(
        default=None, alias="recoveryTimeFactorFeedback"
    )
    recovery_time_change_phrase: str | None = Field(
        default=None, alias="recoveryTimeChangePhrase"
    )

    acwr_factor_percent: int | None = Field(default=None, alias="acwrFactorPercent")
    acwr_factor_feedback: str | None = Field(default=None, alias="acwrFactorFeedback")

    hrv_factor_percent: int | None = Field(default=None, alias="hrvFactorPercent")
    hrv_factor_feedback: str | None = Field(default=None, alias="hrvFactorFeedback")

    stress_history_factor_percent: int | None = Field(
        default=None, alias="stressHistoryFactorPercent"
    )
    stress_history_factor_feedback: str | None = Field(
        default=None, alias="stressHistoryFactorFeedback"
    )

    input_context: str | None = Field(default=None, alias="inputContext")


# ---------------------------------------------------------------------------
# Activity (get_activities_by_date)
# ---------------------------------------------------------------------------


class ActivityType(_BaseResponse):
    """Garmin activity type classification (``typeKey`` is the main lookup)."""

    type_id: int | None = Field(default=None, alias="typeId")
    type_key: str | None = Field(default=None, alias="typeKey")
    parent_type_id: int | None = Field(default=None, alias="parentTypeId")
    is_hidden: bool | None = Field(default=None, alias="isHidden")


class Activity(_BaseResponse):
    """One activity from ``get_activities_by_date``.

    Strength-training activities populate ``total_sets``, ``total_reps`` and
    ``total_volume``; other activity types leave those fields as ``None``.
    """

    activity_id: int | None = Field(default=None, alias="activityId")
    activity_name: str | None = Field(default=None, alias="activityName")

    start_time_local: str | None = Field(default=None, alias="startTimeLocal")
    start_time_gmt: str | None = Field(default=None, alias="startTimeGMT")

    activity_type: ActivityType | None = Field(default=None, alias="activityType")

    duration: float | None = None
    moving_duration: float | None = Field(default=None, alias="movingDuration")
    elapsed_duration: float | None = Field(default=None, alias="elapsedDuration")

    distance: float | None = None
    elevation_gain: float | None = Field(default=None, alias="elevationGain")
    elevation_loss: float | None = Field(default=None, alias="elevationLoss")

    average_speed: float | None = Field(default=None, alias="averageSpeed")
    max_speed: float | None = Field(default=None, alias="maxSpeed")

    average_hr: float | None = Field(default=None, alias="averageHR")
    max_hr: float | None = Field(default=None, alias="maxHR")

    calories: float | None = None
    bmr_calories: float | None = Field(default=None, alias="bmrCalories")

    avg_power: float | None = Field(default=None, alias="avgPower")
    max_power: float | None = Field(default=None, alias="maxPower")
    normalized_power: float | None = Field(default=None, alias="normPower")

    aerobic_training_effect: float | None = Field(
        default=None, alias="aerobicTrainingEffect"
    )
    anaerobic_training_effect: float | None = Field(
        default=None, alias="anaerobicTrainingEffect"
    )
    activity_training_load: float | None = Field(
        default=None, alias="activityTrainingLoad"
    )
    training_effect_label: str | None = Field(default=None, alias="trainingEffectLabel")

    average_running_cadence: float | None = Field(
        default=None, alias="averageRunningCadenceInStepsPerMinute"
    )
    max_running_cadence: float | None = Field(
        default=None, alias="maxRunningCadenceInStepsPerMinute"
    )

    total_sets: int | None = Field(default=None, alias="totalSets")
    active_sets: int | None = Field(default=None, alias="activeSets")
    total_reps: int | None = Field(default=None, alias="totalReps")
    total_volume: float | None = Field(default=None, alias="totalVolume")


# ---------------------------------------------------------------------------
# Wrapper
# ---------------------------------------------------------------------------


class TypedGarmin:
    """Typed namespace accessor for a curated set of Garmin Connect endpoints.

    Access via the :attr:`Garmin.typed` cached property, never instantiate
    directly::

        g = Garmin(email, password)
        g.login()
        stats = g.typed.get_stats("2026-04-21")

    Each method is a thin wrapper around the corresponding ``Garmin`` method
    that validates the response with a Pydantic model. On validation failure,
    raises :class:`GarminConnectResponseValidationError` with the unvalidated
    response available as ``.raw``.

    **Experimental.** Model shapes and method signatures may change in future
    releases; pin a specific version if you depend on them.
    """

    def __init__(self, garmin: Garmin) -> None:
        self._garmin = garmin

    @staticmethod
    def _validate(model_cls: type[_M], raw: Any, method_name: str) -> _M:
        try:
            return model_cls.model_validate(raw)
        except _PydanticValidationError as exc:
            raise GarminConnectResponseValidationError(
                f"Response from {method_name}() failed {model_cls.__name__} "
                f"validation: {exc}",
                raw=raw,
                pydantic_error=exc,
            ) from exc

    # -- Daily stats ---------------------------------------------------------

    def get_stats(self, cdate: str) -> DailyStats:
        """Return daily stats for ``cdate`` as a :class:`DailyStats` model."""
        raw = self._garmin.get_stats(cdate)
        return self._validate(DailyStats, raw, "get_stats")

    def get_user_summary(self, cdate: str) -> DailyStats:
        """Return the user summary for ``cdate`` as a :class:`DailyStats` model."""
        raw = self._garmin.get_user_summary(cdate)
        return self._validate(DailyStats, raw, "get_user_summary")

    # -- Sleep ---------------------------------------------------------------

    def get_sleep_data(self, cdate: str) -> SleepData:
        """Return sleep data for ``cdate`` as a :class:`SleepData` model."""
        raw = self._garmin.get_sleep_data(cdate)
        return self._validate(SleepData, raw, "get_sleep_data")

    # -- HRV -----------------------------------------------------------------

    def get_hrv_data(self, cdate: str) -> HrvData | None:
        """Return HRV data for ``cdate`` as :class:`HrvData`, or ``None`` if absent."""
        raw = self._garmin.get_hrv_data(cdate)
        if raw is None:
            return None
        return self._validate(HrvData, raw, "get_hrv_data")

    # -- Body battery --------------------------------------------------------

    def get_body_battery(
        self, startdate: str, enddate: str | None = None
    ) -> list[BodyBatteryEntry]:
        """Return body battery entries between ``startdate`` and ``enddate``."""
        raw = self._garmin.get_body_battery(startdate, enddate)
        if not isinstance(raw, list):
            return []
        return [
            self._validate(BodyBatteryEntry, item, "get_body_battery") for item in raw
        ]

    # -- Training readiness --------------------------------------------------

    def get_training_readiness(self, cdate: str) -> list[TrainingReadiness]:
        """Return training readiness snapshots for ``cdate``.

        Despite the underlying ``Garmin.get_training_readiness`` returning
        ``dict[str, Any]`` in its type annotation, the live endpoint returns a
        list of snapshots; this wrapper reflects the real shape.
        """
        raw = self._garmin.get_training_readiness(cdate)
        if not isinstance(raw, list):
            return []
        return [
            self._validate(TrainingReadiness, item, "get_training_readiness")
            for item in raw
        ]

    # -- Activities ----------------------------------------------------------

    def get_activities_by_date(
        self,
        startdate: str,
        enddate: str | None = None,
        activitytype: str | None = None,
        sortorder: str | None = None,
    ) -> list[Activity]:
        """Return activities between two dates as a list of :class:`Activity`."""
        raw = self._garmin.get_activities_by_date(
            startdate, enddate, activitytype, sortorder
        )
        if not isinstance(raw, list):
            return []
        return [
            self._validate(Activity, item, "get_activities_by_date") for item in raw
        ]


__all__ = [
    "Activity",
    "ActivityType",
    "BodyBatteryEntry",
    "DailySleepDTO",
    "DailyStats",
    "GarminConnectResponseValidationError",
    "HrvBaseline",
    "HrvData",
    "HrvSummary",
    "SleepData",
    "SleepScoreValue",
    "SleepScores",
    "TrainingReadiness",
    "TypedGarmin",
]
