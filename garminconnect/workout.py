"""Typed workout models for Garmin Connect workouts.

This module provides Pydantic models for creating type-safe workout definitions.
Pydantic is an optional dependency - install it with: pip install pydantic
or: pip install garminconnect[workout]
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Protocol, Self

if TYPE_CHECKING:
    from pydantic import BaseModel, ConfigDict, Field, model_validator
else:
    try:
        from pydantic import BaseModel, ConfigDict, Field, model_validator
    except ImportError:
        # Fallback if pydantic is not installed
        BaseModel = object  # type: ignore[assignment,misc]
        ConfigDict = dict  # type: ignore[assignment,misc]

        def model_validator(*_args: Any, **_kwargs: Any) -> Any:
            """No-op decorator for when pydantic is not installed."""

            def decorator(function: Any) -> Any:
                return function

            return decorator

        def Field(*_args: Any, **_kwargs: Any) -> Any:  # type: ignore[misc]
            """Placeholder Field function when pydantic is not installed."""
            return None


# Sport Type IDs — from /workout-service/workout/types
class SportType:
    """Garmin workout sport type IDs."""

    RUNNING = 1
    CYCLING = 2
    OTHER = 3
    SWIMMING = 4
    STRENGTH_TRAINING = 5
    CARDIO_TRAINING = 6
    YOGA = 7
    PILATES = 8
    HIIT = 9
    MULTI_SPORT = 10
    MOBILITY = 11


# Step Type IDs — from /workout-service/workout/types
class StepType:
    """Garmin workout step type IDs."""

    WARMUP = 1
    COOLDOWN = 2
    INTERVAL = 3
    RECOVERY = 4
    REST = 5
    REPEAT = 6
    OTHER = 7
    MAIN = 8


# Condition Type IDs — from /workout-service/workout/types
class ConditionType:
    """Garmin end condition type IDs."""

    LAP_BUTTON = 1
    TIME = 2
    DISTANCE = 3
    CALORIES = 4
    POWER = 5
    HEART_RATE = 6
    ITERATIONS = 7
    FIXED_REST = 8
    FIXED_REPETITION = 9
    REPS = 10


# Target Type IDs — from /workout-service/workout/types
class TargetType:
    """Garmin workout target type IDs."""

    NO_TARGET = 1
    POWER_ZONE = 2
    CADENCE = 3
    HEART_RATE_ZONE = 4
    SPEED_ZONE = 5
    PACE_ZONE = 6
    GRADE = 7
    HEART_RATE_LAP = 8
    POWER_LAP = 9
    RESISTANCE = 15


# Weight unit for strength workout target loads.
# Garmin stores ``weightValue`` in GRAMS tagged with this kilogram unit.
WEIGHT_UNIT_KILOGRAM = {"unitId": 8, "unitKey": "kilogram", "factor": 1000.0}


class SportTypeModel(BaseModel):
    """Sport type model."""

    sportTypeId: int
    sportTypeKey: str
    displayOrder: int = 1


class EndConditionModel(BaseModel):
    """End condition model for workout steps."""

    conditionTypeId: int
    conditionTypeKey: str
    displayOrder: int
    displayable: bool = True


class TargetTypeModel(BaseModel):
    """Target type model for workout steps."""

    workoutTargetTypeId: int
    workoutTargetTypeKey: str
    displayOrder: int


class StrokeTypeModel(BaseModel):
    """Stroke type model (for swimming workouts)."""

    strokeTypeId: int = 0
    displayOrder: int = 0


class EquipmentTypeModel(BaseModel):
    """Equipment type model."""

    equipmentTypeId: int = 0
    displayOrder: int = 0


class ExecutableStep(BaseModel):
    """Executable workout step (warmup, interval, recovery, cooldown, etc.)."""

    type: str = "ExecutableStepDTO"
    stepOrder: int
    stepType: dict[str, Any] | None = None
    endCondition: dict[str, Any] | None = None
    endConditionValue: float | None = None
    targetType: dict[str, Any] | None = None
    targetValueOne: float | None = None
    targetValueTwo: float | None = None
    zoneNumber: int | None = None
    secondaryTargetType: dict[str, Any] | None = None
    secondaryTargetValueOne: float | None = None
    secondaryTargetValueTwo: float | None = None
    secondaryZoneNumber: int | None = None
    strokeType: dict[str, Any] | None = None
    equipmentType: dict[str, Any] | None = None
    childStepId: int | None = None

    model_config = ConfigDict(extra="allow")


class RepeatGroup(BaseModel):
    """Repeat group for repeating workout steps."""

    type: str = "RepeatGroupDTO"
    stepOrder: int
    stepType: dict[str, Any] | None = None
    numberOfIterations: int
    workoutSteps: list[ExecutableStep | RepeatGroup]
    endCondition: dict[str, Any] | None = None
    endConditionValue: float | None = None
    childStepId: int | None = None
    smartRepeat: bool = False

    model_config = ConfigDict(extra="allow")


# Update forward reference (only if pydantic is available)
with suppress(AttributeError, TypeError):
    RepeatGroup.model_rebuild()


class WorkoutSegment(BaseModel):
    """Workout segment containing workout steps."""

    segmentOrder: int
    sportType: dict[str, Any]
    workoutSteps: list[ExecutableStep | RepeatGroup]

    model_config = ConfigDict(extra="allow")


class BaseWorkout(BaseModel):
    """Base workout model."""

    workoutName: str
    sportType: dict[str, Any]
    estimatedDurationInSecs: int
    workoutSegments: list[WorkoutSegment]
    author: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None

    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> dict[str, Any]:
        """Convert workout to dictionary for API upload."""
        return self.model_dump(exclude_none=True, mode="json")


class RunningWorkout(BaseWorkout):
    """Running workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.RUNNING,
            "sportTypeKey": "running",
            "displayOrder": 1,
        }
    )


class CyclingWorkout(BaseWorkout):
    """Cycling workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.CYCLING,
            "sportTypeKey": "cycling",
            "displayOrder": 2,
        }
    )


class SwimmingWorkout(BaseWorkout):
    """Swimming workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.SWIMMING,
            "sportTypeKey": "swimming",
            "displayOrder": 3,
        }
    )


class WalkingWorkout(BaseWorkout):
    """Walking workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": 17,
            "sportTypeKey": "walking",
            "displayOrder": 17,
        }
    )


class MultiSportWorkout(BaseWorkout):
    """Multi-sport workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.MULTI_SPORT,
            "sportTypeKey": "multi_sport",
            "displayOrder": 10,
        }
    )


class FitnessEquipmentWorkout(BaseWorkout):
    """Fitness equipment workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.CARDIO_TRAINING,
            "sportTypeKey": "cardio_training",
            "displayOrder": 6,
        }
    )


class HikingWorkout(BaseWorkout):
    """Hiking workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": 18,
            "sportTypeKey": "hiking",
            "displayOrder": 18,
        }
    )


class StrengthWorkout(BaseWorkout):
    """Strength training workout model.

    Strength workouts are rep-based rather than time/distance-based.  Build the
    steps with :func:`create_strength_exercise_step` /
    :func:`create_strength_rest_step` (or the :func:`create_strength_set`
    convenience), and identify each exercise with a ``category`` /
    ``exerciseName`` pair from :mod:`garminconnect.exercises`.
    """

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.STRENGTH_TRAINING,
            "sportTypeKey": "strength_training",
            "displayOrder": 5,
        }
    )


class IntensityTarget(Protocol):
    """Protocol for power, heart rate, speed and pace targets."""

    target_type: ClassVar[int]
    target_type_key: ClassVar[str]
    zone_number: ClassVar[Literal[None]] = None
    lower_limit: float
    upper_limit: float


class ZonedIntensityTarget(Protocol):
    """Protocol for power zone and heart rate zone targets."""

    target_type: ClassVar[int]
    target_type_key: ClassVar[str]
    upper_limit: ClassVar[Literal[None]] = None
    lower_limit: ClassVar[Literal[None]] = None
    zone_number: int


class _RangeTarget(BaseModel):
    zone_number: ClassVar = None
    lower_limit: float
    upper_limit: float

    @model_validator(mode="after")
    def _check_order(self) -> Self:
        if self.lower_limit > self.upper_limit:
            raise ValueError("lower_limit must be <= upper_limit")
        return self


class CadenceTarget(_RangeTarget):
    """Cadence target.

    upper and lower limits in steps (running) or revolutions (cycling) per minute
    """

    target_type: ClassVar[int] = TargetType.CADENCE
    target_type_key: ClassVar[str] = "cadence"
    zone_number: ClassVar = None
    lower_limit: float
    upper_limit: float


class PowerZoneTarget(BaseModel):
    """Power Zone target."""

    target_type: ClassVar[int] = TargetType.POWER_ZONE
    target_type_key: ClassVar[str] = "power.zone"
    upper_limit: ClassVar = None
    lower_limit: ClassVar = None
    zone_number: int


class CustomPowerTarget(_RangeTarget):
    """Custom Power target.

    upper and lower limits in Watts
    """

    target_type: ClassVar[int] = TargetType.POWER_ZONE
    target_type_key: ClassVar[str] = "power.zone"
    zone_number: ClassVar = None
    lower_limit: float
    upper_limit: float


class HeartRateZoneTarget(BaseModel):
    """Heart Rate Zone target."""

    target_type: ClassVar[int] = TargetType.HEART_RATE_ZONE
    target_type_key: ClassVar[str] = "heart.rate.zone"
    upper_limit: ClassVar = None
    lower_limit: ClassVar = None
    zone_number: int


class CustomHeartRateTarget(_RangeTarget):
    """Custom Heart rate zone target.

    upper and lower limits in beats per minute
    """

    target_type: ClassVar[int] = TargetType.HEART_RATE_ZONE
    target_type_key: ClassVar[str] = "heart.rate.zone"
    zone_number: ClassVar = None
    lower_limit: float
    upper_limit: float


class SpeedTarget(_RangeTarget):
    """Speed target.

    upper and lower limits in m/s
    """

    target_type: ClassVar[int] = TargetType.SPEED_ZONE
    target_type_key: ClassVar[str] = "speed.zone"
    zone_number: ClassVar = None
    lower_limit: float
    upper_limit: float


class PaceTarget(_RangeTarget):
    """Pace target.

    upper and lower limits in m/s
    """

    target_type: ClassVar[int] = TargetType.PACE_ZONE
    target_type_key: ClassVar[str] = "pace.zone"
    zone_number: ClassVar = None
    lower_limit: float
    upper_limit: float


def pace_to_mps(minutes: int, seconds: int, units: Literal["km", "mi"]) -> float:
    """Convert a pace from min:sec/km or min:sec/mi to m/s."""
    to_meters = 1609.344 if units == "mi" else 1000
    return to_meters / (minutes * 60 + seconds)


def speed_to_mps(speed: float, units: Literal["kph", "mph"]) -> float:
    """Convert a speed from kph or mph to m/s."""
    to_meters = 1609.344 if units == "mph" else 1000
    return speed * to_meters / 3600


# Helper functions for creating common workout steps
def create_warmup_step(
    duration_seconds: float,
    step_order: int = 1,
    target_type: dict[str, Any] | None = None,
) -> ExecutableStep:
    """Create a warmup step."""
    return ExecutableStep(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.WARMUP,
            "stepTypeKey": "warmup",
            "displayOrder": 1,
        },
        endCondition={
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        endConditionValue=duration_seconds,
        targetType=target_type
        or {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 1,
        },
    )


def create_interval_step(
    duration_seconds: float,
    step_order: int,
    target_type: dict[str, Any] | None = None,
    target_value_one: float | None = None,
    target_value_two: float | None = None,
    zone_number: int | None = None,
    secondary_target_type: dict[str, Any] | None = None,
    secondary_target_value_one: float | None = None,
    secondary_target_value_two: float | None = None,
    secondary_zone_number: int | None = None,
) -> ExecutableStep:
    """Create an interval step."""
    return ExecutableStep(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.INTERVAL,
            "stepTypeKey": "interval",
            "displayOrder": 1,
        },
        endCondition={
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        endConditionValue=duration_seconds,
        targetType=target_type
        or {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 3,
        },
        targetValueOne=target_value_one,
        targetValueTwo=target_value_two,
        zoneNumber=zone_number,
        secondaryTargetType=secondary_target_type
        or {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 4,
        },
        secondaryTargetValueOne=secondary_target_value_one,
        secondaryTargetValueTwo=secondary_target_value_two,
        secondaryZoneNumber=secondary_zone_number,
    )


def _target_kwargs(
    target: IntensityTarget | ZonedIntensityTarget,
    secondary_target: IntensityTarget | ZonedIntensityTarget | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "target_type": {
            "workoutTargetTypeId": target.target_type,
            "workoutTargetTypeKey": target.target_type_key,
            "displayOrder": 1,
        },
        "target_value_one": target.lower_limit,
        "target_value_two": target.upper_limit,
        "zone_number": target.zone_number,
    }
    if secondary_target is not None:
        kwargs |= {
            "secondary_target_type": {
                "workoutTargetTypeId": secondary_target.target_type,
                "workoutTargetTypeKey": secondary_target.target_type_key,
                "displayOrder": 2,
            },
            "secondary_target_value_one": secondary_target.lower_limit,
            "secondary_target_value_two": secondary_target.upper_limit,
            "secondary_zone_number": secondary_target.zone_number,
        }
    return kwargs


def create_targeted_interval_step(
    duration_seconds: float,
    step_order: int,
    target: IntensityTarget | ZonedIntensityTarget,
    secondary_target: IntensityTarget | ZonedIntensityTarget | None = None,
) -> ExecutableStep:
    """Create a targeted interval step."""
    kwargs = {
        "duration_seconds": duration_seconds,
        "step_order": step_order,
    }
    kwargs |= _target_kwargs(target, secondary_target)

    return create_interval_step(**kwargs)  # type: ignore[arg-type]


def create_distance_interval_step(
    distance_meters: float,
    step_order: int,
    target_type: dict[str, Any] | None = None,
    target_value_one: float | None = None,
    target_value_two: float | None = None,
    zone_number: int | None = None,
    secondary_target_type: dict[str, Any] | None = None,
    secondary_target_value_one: float | None = None,
    secondary_target_value_two: float | None = None,
    secondary_zone_number: int | None = None,
) -> ExecutableStep:
    """Create an interval step that ends after a distance in meters."""
    return ExecutableStep(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.INTERVAL,
            "stepTypeKey": "interval",
            "displayOrder": 1,
        },
        endCondition={
            "conditionTypeId": ConditionType.DISTANCE,
            "conditionTypeKey": "distance",
            "displayOrder": 3,
            "displayable": True,
        },
        endConditionValue=distance_meters,
        targetType=target_type
        or {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 3,
        },
        targetValueOne=target_value_one,
        targetValueTwo=target_value_two,
        zoneNumber=zone_number,
        secondaryTargetType=secondary_target_type
        or {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 4,
        },
        secondaryTargetValueOne=secondary_target_value_one,
        secondaryTargetValueTwo=secondary_target_value_two,
        secondaryZoneNumber=secondary_zone_number,
    )


def create_targeted_distance_interval_step(
    distance_meters: float,
    step_order: int,
    target: IntensityTarget | ZonedIntensityTarget,
    secondary_target: IntensityTarget | ZonedIntensityTarget | None = None,
) -> ExecutableStep:
    """Create a targeted interval step that ends after a distance in meters."""
    kwargs = {
        "distance_meters": distance_meters,
        "step_order": step_order,
    }
    kwargs |= _target_kwargs(target, secondary_target)

    return create_distance_interval_step(**kwargs)  # type: ignore[arg-type]


def create_recovery_step(
    duration_seconds: float,
    step_order: int,
    target_type: dict[str, Any] | None = None,
) -> ExecutableStep:
    """Create a recovery step."""
    return ExecutableStep(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.RECOVERY,
            "stepTypeKey": "recovery",
            "displayOrder": 4,
        },
        endCondition={
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        endConditionValue=duration_seconds,
        targetType=target_type
        or {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 1,
        },
    )


def create_cooldown_step(
    duration_seconds: float,
    step_order: int,
    target_type: dict[str, Any] | None = None,
) -> ExecutableStep:
    """Create a cooldown step."""
    return ExecutableStep(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.COOLDOWN,
            "stepTypeKey": "cooldown",
            "displayOrder": 2,
        },
        endCondition={
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        endConditionValue=duration_seconds,
        targetType=target_type
        or {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 1,
        },
    )


def create_repeat_group(
    iterations: int,
    workout_steps: list[ExecutableStep | RepeatGroup],
    step_order: int,
) -> RepeatGroup:
    """Create a repeat group."""
    return RepeatGroup(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.REPEAT,
            "stepTypeKey": "repeat",
            "displayOrder": 6,
        },
        numberOfIterations=iterations,
        workoutSteps=workout_steps,
        endCondition={
            "conditionTypeId": ConditionType.ITERATIONS,
            "conditionTypeKey": "iterations",
            "displayOrder": 7,
            "displayable": False,
        },
        endConditionValue=float(iterations),
    )


def create_strength_exercise_step(
    category: str,
    step_order: int,
    reps: int,
    exercise_name: str = "",
    weight_kg: float | None = None,
) -> ExecutableStep:
    """Create a rep-based strength exercise step.

    Args:
        category: Garmin exercise category, e.g. ``"BENCH_PRESS"``.  See
            :mod:`garminconnect.exercises` for the full list of valid values.
        step_order: Position of this step within the segment (1-indexed, unique).
        reps: Number of repetitions to perform.
        exercise_name: Specific exercise variant, e.g. ``"LAT_PULLDOWN"``.  An
            empty string shows only the category name.
        weight_kg: Optional target weight in kilograms.

    """
    extra: dict[str, Any] = {"category": category, "exerciseName": exercise_name}
    if weight_kg is not None:
        extra["weightValue"] = float(weight_kg) * 1000.0
        extra["weightUnit"] = dict(WEIGHT_UNIT_KILOGRAM)

    return ExecutableStep(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.INTERVAL,
            "stepTypeKey": "interval",
            "displayOrder": 3,
        },
        endCondition={
            "conditionTypeId": ConditionType.REPS,
            "conditionTypeKey": "reps",
            "displayOrder": 10,
            "displayable": True,
        },
        endConditionValue=float(reps),
        targetType={
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 1,
        },
        **extra,
    )


def create_strength_rest_step(
    duration_seconds: float,
    step_order: int,
) -> ExecutableStep:
    """Create a timed rest step between strength sets."""
    return ExecutableStep(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.REST,
            "stepTypeKey": "rest",
            "displayOrder": 5,
        },
        endCondition={
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        endConditionValue=float(duration_seconds),
        targetType={
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 1,
        },
    )


def create_strength_set(
    category: str,
    step_order: int,
    sets: int,
    reps: int,
    rest_seconds: float,
    exercise_name: str = "",
    weight_kg: float | None = None,
) -> RepeatGroup:
    """Create a full strength exercise block as a repeat group.

    Produces ``sets`` repetitions of ``reps`` reps of the exercise followed by
    a timed rest, i.e. one "N Sets" block in the Garmin workout editor.

    ``step_order`` is the order of the repeat group; the inner exercise and rest
    steps take ``step_order + 1`` and ``step_order + 2``.  Advance the caller's
    running order counter by 3 for each block so every ``stepOrder`` is unique.
    """
    exercise = create_strength_exercise_step(
        category,
        step_order + 1,
        reps,
        exercise_name=exercise_name,
        weight_kg=weight_kg,
    )
    rest = create_strength_rest_step(rest_seconds, step_order + 2)
    return create_repeat_group(sets, [exercise, rest], step_order)
