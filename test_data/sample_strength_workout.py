"""Sample strength workout data using typed workout models."""

from garminconnect.workout import (
    StrengthWorkout,
    WorkoutSegment,
    create_strength_set,
    create_warmup_step,
)


def create_sample_strength_workout() -> StrengthWorkout:
    """Create a sample upper-body strength workout.

    Each exercise is a repeat group ("N sets") of rep-based work followed by a
    timed rest.  ``step_order`` increases by 1 across every step, so each
    exercise block (group + work + rest) advances the counter by 3.
    """
    return StrengthWorkout(
        workoutName="Upper Body Strength Session",
        estimatedDurationInSecs=0,
        description="A sample strength workout: bench press, lat pulldown and cable row.",
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 5,
                    "sportTypeKey": "strength_training",
                    "displayOrder": 5,
                },
                workoutSteps=[
                    create_warmup_step(300.0, step_order=1),  # 5 min warmup
                    create_strength_set(
                        "BENCH_PRESS",
                        step_order=2,
                        sets=4,
                        reps=10,
                        rest_seconds=120.0,
                    ),
                    create_strength_set(
                        "PULL_UP",
                        step_order=5,
                        sets=4,
                        reps=12,
                        rest_seconds=90.0,
                        exercise_name="LAT_PULLDOWN",
                    ),
                    create_strength_set(
                        "ROW",
                        step_order=8,
                        sets=4,
                        reps=12,
                        rest_seconds=90.0,
                        exercise_name="SEATED_CABLE_ROW",
                        weight_kg=40,
                    ),
                ],
            )
        ],
    )
