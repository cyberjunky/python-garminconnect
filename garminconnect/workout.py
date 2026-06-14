"""Typed workout models for Garmin Connect workouts.

This module provides Pydantic models for creating type-safe workout definitions.
Pydantic is an optional dependency - install it with: pip install pydantic
or: pip install garminconnect[workout]
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel, ConfigDict, Field
else:
    try:
        from pydantic import BaseModel, ConfigDict, Field
    except ImportError:
        # Fallback if pydantic is not installed
        BaseModel = object  # type: ignore[assignment,misc]
        ConfigDict = dict  # type: ignore[assignment,misc]

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
) -> ExecutableStep:
    """Create an interval step."""
    return ExecutableStep(
        stepOrder=step_order,
        stepType={
            "stepTypeId": StepType.INTERVAL,
            "stepTypeKey": "interval",
            "displayOrder": 3,
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
