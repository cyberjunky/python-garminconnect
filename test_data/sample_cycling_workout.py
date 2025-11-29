"""Sample cycling workout data using typed workout models."""

from garminconnect.workout import (
    CyclingWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_interval_step,
    create_recovery_step,
    create_repeat_group,
    create_warmup_step,
)


def create_sample_cycling_workout() -> CyclingWorkout:
    """Create a sample interval cycling workout."""
    return CyclingWorkout(
        workoutName="Cycling Power Intervals",
        estimatedDurationInSecs=3600,  # 60 minutes
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 2,
                    "sportTypeKey": "cycling",
                    "displayOrder": 2,
                },
                workoutSteps=[
                    create_warmup_step(600.0, step_order=1),  # 10 min warmup
                    create_repeat_group(
                        iterations=5,
                        workout_steps=[
                            create_interval_step(300.0, step_order=2),  # 5 min interval
                            create_recovery_step(180.0, step_order=3),  # 3 min recovery
                        ],
                        step_order=2,
                    ),
                    create_cooldown_step(300.0, step_order=3),  # 5 min cooldown
                ],
            )
        ],
    )
