"""Regression tests pinning workout constant IDs to Garmin API values.

Prevents silent drift of constant values (see issue #333).
"""

from garminconnect.workout import (
    ConditionType,
    SportType,
    StepType,
    SwimmingWorkout,
    TargetType,
    WorkoutSegment,
    create_warmup_step,
)


def test_target_type_ids() -> None:
    """Pin TargetType IDs to match Garmin API values (issue #333)."""
    assert TargetType.NO_TARGET == 1
    assert TargetType.POWER_ZONE == 2
    assert TargetType.CADENCE == 3
    assert TargetType.HEART_RATE_ZONE == 4
    assert TargetType.SPEED_ZONE == 5
    assert TargetType.PACE_ZONE == 6
    assert TargetType.GRADE == 7
    assert TargetType.HEART_RATE_LAP == 8
    assert TargetType.POWER_LAP == 9
    assert TargetType.RESISTANCE == 15


def test_step_type_ids() -> None:
    """Pin StepType IDs to match Garmin API values."""
    assert StepType.WARMUP == 1
    assert StepType.COOLDOWN == 2
    assert StepType.INTERVAL == 3
    assert StepType.RECOVERY == 4
    assert StepType.REST == 5
    assert StepType.REPEAT == 6
    assert StepType.OTHER == 7
    assert StepType.MAIN == 8


def test_condition_type_ids() -> None:
    """Pin ConditionType IDs to match Garmin API values (fixes issue #370)."""
    assert ConditionType.LAP_BUTTON == 1
    assert ConditionType.TIME == 2
    assert ConditionType.DISTANCE == 3
    assert ConditionType.CALORIES == 4
    assert ConditionType.POWER == 5
    assert ConditionType.HEART_RATE == 6
    assert ConditionType.ITERATIONS == 7
    assert ConditionType.FIXED_REST == 8
    assert ConditionType.FIXED_REPETITION == 9
    assert ConditionType.REPS == 10


def test_sport_type_ids() -> None:
    """Pin SportType IDs to match Garmin API values."""
    assert SportType.RUNNING == 1
    assert SportType.CYCLING == 2
    assert SportType.OTHER == 3
    assert SportType.SWIMMING == 4
    assert SportType.STRENGTH_TRAINING == 5
    assert SportType.CARDIO_TRAINING == 6
    assert SportType.YOGA == 7
    assert SportType.PILATES == 8
    assert SportType.HIIT == 9
    assert SportType.MULTI_SPORT == 10
    assert SportType.MOBILITY == 11


def test_swimming_workout_uses_expected_sport_type_id() -> None:
    """Ensure typed swimming workouts upload as sportTypeKey=swimming."""
    workout = SwimmingWorkout(
        workoutName="Regression Swim",
        estimatedDurationInSecs=300,
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={"sportTypeId": 4, "sportTypeKey": "swimming"},
                workoutSteps=[create_warmup_step(300.0)],
            )
        ],
    )
    payload = workout.to_dict()
    assert payload["sportType"]["sportTypeId"] == 4
    assert payload["sportType"]["sportTypeKey"] == "swimming"
