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
    create_strength_timed_set,
    create_strength_timed_step,
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


def test_timed_step_ends_on_time_and_carries_enums():
    """A timed exercise step ends on time but is otherwise an exercise step."""
    step = create_strength_timed_step(
        "PLANK", step_order=3, duration_seconds=45, exercise_name="PLANK"
    )
    data = step.model_dump(exclude_none=True, mode="json")
    assert data["stepType"]["stepTypeId"] == StepType.INTERVAL
    assert data["endCondition"]["conditionTypeId"] == ConditionType.TIME
    assert data["endCondition"]["conditionTypeKey"] == "time"
    assert data["endConditionValue"] == 45.0
    assert data["category"] == "PLANK"
    assert data["exerciseName"] == "PLANK"


def test_timed_step_weight_matches_rep_step():
    """weight_kg is encoded the same way for timed and rep-based steps."""
    timed = create_strength_timed_step(
        "CARRY", step_order=3, duration_seconds=30, weight_kg=20
    ).model_dump(exclude_none=True, mode="json")
    reps = create_strength_exercise_step(
        "CARRY", step_order=3, reps=10, weight_kg=20
    ).model_dump(exclude_none=True, mode="json")
    assert timed["weightValue"] == reps["weightValue"] == 20000.0
    assert timed["weightUnit"] == reps["weightUnit"]


def test_description_is_set_when_given_and_absent_otherwise():
    """description is sent only when provided, so existing payloads are unchanged."""
    with_desc = create_strength_exercise_step(
        "SQUAT", step_order=1, reps=8, description="Knees out"
    ).model_dump(exclude_none=True, mode="json")
    without = create_strength_exercise_step(
        "SQUAT", step_order=1, reps=8
    ).model_dump(exclude_none=True, mode="json")
    assert with_desc["description"] == "Knees out"
    assert "description" not in without


def test_sets_put_description_on_the_exercise_step_only():
    """Set helpers apply description to the exercise step, not the rest step."""
    for group in (
        create_strength_set(
            "SQUAT", step_order=1, sets=3, reps=8, rest_seconds=60, description="cue"
        ),
        create_strength_timed_set(
            "PLANK",
            step_order=1,
            sets=3,
            duration_seconds=45,
            rest_seconds=30,
            description="cue",
        ),
    ):
        exercise, rest = group.model_dump(exclude_none=True, mode="json")[
            "workoutSteps"
        ]
        assert exercise["description"] == "cue"
        assert "description" not in rest


def test_timed_set_builds_repeat_group():
    """A timed set is a repeat group of a timed exercise step and a rest step."""
    group = create_strength_timed_set(
        "PLANK", step_order=1, sets=3, duration_seconds=45, rest_seconds=30
    )
    data = group.model_dump(exclude_none=True, mode="json")
    assert data["numberOfIterations"] == 3
    exercise, rest = data["workoutSteps"]
    assert (exercise["stepOrder"], rest["stepOrder"]) == (2, 3)
    assert exercise["endCondition"]["conditionTypeId"] == ConditionType.TIME
    assert exercise["endConditionValue"] == 45.0
    assert rest["stepType"]["stepTypeId"] == StepType.REST
    assert rest["endConditionValue"] == 30.0


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


def test_sample_timed_strength_workout_round_trips(monkeypatch):
    """The timed demo sample mixes time- and rep-based sets, all with notes."""
    from pathlib import Path

    test_data = Path(__file__).parent.parent / "test_data"
    monkeypatch.syspath_prepend(str(test_data))
    from sample_strength_workout import create_sample_timed_strength_workout

    payload = create_sample_timed_strength_workout().to_dict()
    groups = [
        s
        for s in payload["workoutSegments"][0]["workoutSteps"]
        if s["type"] == "RepeatGroupDTO"
    ]
    exercises_ = [g["workoutSteps"][0] for g in groups]
    assert [e["endCondition"]["conditionTypeKey"] for e in exercises_] == [
        "time",
        "time",
        "reps",
    ]
    assert all(e["description"] for e in exercises_)
    # Every exercise the sample uploads must be a real catalog entry.
    catalog = {(x["category"], x["exercise"]) for x in exercises.EXERCISES}
    for e in exercises_:
        if e["exerciseName"]:
            assert (e["category"], e["exerciseName"]) in catalog
        else:
            assert e["category"] in exercises.CATEGORIES


def test_exercise_catalog_lookup():
    """The catalog resolves known machine exercises to their enums."""
    assert exercises.CATEGORIES  # non-empty
    lat = exercises.resolve("Lat Pull-down")
    assert lat is not None
    assert lat["category"] == "PULL_UP"
    assert lat["exercise"] == "LAT_PULLDOWN"
    assert exercises.resolve("Definitely Not An Exercise") is None
    assert any(e["exercise"] == "LEG_PRESS" for e in exercises.find("Leg Press"))
