"""Typed workout models for Garmin Connect workouts.

This module provides Pydantic models for creating type-safe workout definitions.
Pydantic is an optional dependency - install it with: pip install pydantic
or: pip install garminconnect[workout]
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel, Field
else:
    try:
        from pydantic import BaseModel, Field
    except ImportError:
        # Fallback if pydantic is not installed
        BaseModel = object  # type: ignore[assignment,misc]

        def Field(*_args: Any, **_kwargs: Any) -> Any:  # type: ignore[misc]
            """Placeholder Field function when pydantic is not installed."""
            return None


# Sport Type IDs (common values)
class SportType:
    """Common Garmin sport type IDs."""

    RUNNING = 1
    CYCLING = 2
    SWIMMING = 3
    WALKING = 4
    MULTI_SPORT = 5
    FITNESS_EQUIPMENT = 6
    HIKING = 7
    OTHER = 8


# Step Type IDs
class StepType:
    """Common Garmin workout step type IDs."""

    WARMUP = 1
    COOLDOWN = 2
    INTERVAL = 3
    RECOVERY = 4
    REST = 5
    REPEAT = 6


# Condition Type IDs
class ConditionType:
    """Common Garmin end condition type IDs."""

    DISTANCE = 1
    TIME = 2
    HEART_RATE = 3
    CALORIES = 4
    CADENCE = 5
    POWER = 6
    ITERATIONS = 7


# Target Type IDs
class TargetType:
    """Common Garmin workout target type IDs."""

    NO_TARGET = 1
    HEART_RATE = 2
    CADENCE = 3
    SPEED = 4
    POWER = 5
    OPEN = 6


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

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow extra fields for flexibility


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

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow extra fields for flexibility


# Update forward reference (only if pydantic is available)
with suppress(AttributeError, TypeError):
    RepeatGroup.model_rebuild()


class WorkoutSegment(BaseModel):
    """Workout segment containing workout steps."""

    segmentOrder: int
    sportType: dict[str, Any]
    workoutSteps: list[ExecutableStep | RepeatGroup]

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow extra fields for flexibility


class BaseWorkout(BaseModel):
    """Base workout model."""

    workoutName: str
    sportType: dict[str, Any]
    estimatedDurationInSecs: int
    workoutSegments: list[WorkoutSegment]
    author: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow extra fields for flexibility

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
            "sportTypeId": SportType.WALKING,
            "sportTypeKey": "walking",
            "displayOrder": 4,
        }
    )


class MultiSportWorkout(BaseWorkout):
    """Multi-sport workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.MULTI_SPORT,
            "sportTypeKey": "multi_sport",
            "displayOrder": 5,
        }
    )


class FitnessEquipmentWorkout(BaseWorkout):
    """Fitness equipment workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.FITNESS_EQUIPMENT,
            "sportTypeKey": "fitness_equipment",
            "displayOrder": 6,
        }
    )


class HikingWorkout(BaseWorkout):
    """Hiking workout model."""

    sportType: dict[str, Any] = Field(
        default_factory=lambda: {
            "sportTypeId": SportType.HIKING,
            "sportTypeKey": "hiking",
            "displayOrder": 7,
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
