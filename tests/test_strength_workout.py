"""Tests for typed strength workouts and the exercise catalog."""

from garminconnect import exercises
from garminconnect.workout import (
    ConditionType,
    SportType,
    StepType,
    StrengthWorkout,
    create_strength_exercise_step,
    create_strength_rest_step,
    create_strength_set,
)


def test_exercise_step_reps_and_enums():
    """A strength exercise step is rep-based and carries category/exerciseName."""
    step = create_strength_exercise_step(
        "PULL_UP", step_order=3, reps=12, exercise_name="LAT_PULLDOWN"
    )
    data = step.model_dump(exclude_none=True, mode="json")
    assert data["stepType"]["stepTypeId"] == StepType.INTERVAL
    assert data["endCondition"]["conditionTypeId"] == ConditionType.REPS
    assert data["endConditionValue"] == 12.0
    assert data["category"] == "PULL_UP"
    assert data["exerciseName"] == "LAT_PULLDOWN"


def test_exercise_step_weight_is_grams_kilogram_unit():
    """weight_kg is stored in grams with a kilogram unit."""
    step = create_strength_exercise_step(
        "BENCH_PRESS", step_order=3, reps=10, weight_kg=40
    )
    data = step.model_dump(exclude_none=True, mode="json")
    assert data["weightValue"] == 40000.0
    assert data["weightUnit"]["unitKey"] == "kilogram"


def test_rest_step_is_timed():
    """A strength rest step ends on time."""
    step = create_strength_rest_step(120.0, step_order=4)
    data = step.model_dump(exclude_none=True, mode="json")
    assert data["stepType"]["stepTypeId"] == StepType.REST
    assert data["endCondition"]["conditionTypeId"] == ConditionType.TIME
    assert data["endConditionValue"] == 120.0


def test_strength_set_builds_repeat_group():
    """create_strength_set wraps an exercise + rest in a repeat group."""
    group = create_strength_set(
        "BENCH_PRESS", step_order=2, sets=4, reps=10, rest_seconds=90.0
    )
    data = group.model_dump(exclude_none=True, mode="json")
    assert data["numberOfIterations"] == 4
    assert data["stepOrder"] == 2
    assert [s["stepOrder"] for s in data["workoutSteps"]] == [3, 4]
    assert data["workoutSteps"][0]["category"] == "BENCH_PRESS"


def test_strength_workout_sport_type():
    """StrengthWorkout defaults to the strength_training sport type."""
    workout = StrengthWorkout(
        workoutName="Test",
        estimatedDurationInSecs=0,
        workoutSegments=[],
    )
    assert workout.sportType["sportTypeId"] == SportType.STRENGTH_TRAINING
    assert workout.sportType["sportTypeKey"] == "strength_training"


def test_sample_strength_workout_round_trips(monkeypatch):
    """The demo sample builds a valid strength workout dict."""
    from pathlib import Path

    test_data = Path(__file__).parent.parent / "test_data"
    monkeypatch.syspath_prepend(str(test_data))
    from sample_strength_workout import create_sample_strength_workout

    payload = create_sample_strength_workout().to_dict()
    assert payload["sportType"]["sportTypeKey"] == "strength_training"
    steps = payload["workoutSegments"][0]["workoutSteps"]
    # 1 warmup + 3 exercise repeat groups
    assert sum(s["type"] == "RepeatGroupDTO" for s in steps) == 3


def test_exercise_catalog_lookup():
    """The catalog resolves known machine exercises to their enums."""
    assert exercises.CATEGORIES  # non-empty
    lat = exercises.resolve("Lat Pull-down")
    assert lat is not None
    assert lat["category"] == "PULL_UP"
    assert lat["exercise"] == "LAT_PULLDOWN"
    assert exercises.resolve("Definitely Not An Exercise") is None
    assert any(e["exercise"] == "LEG_PRESS" for e in exercises.find("Leg Press"))
