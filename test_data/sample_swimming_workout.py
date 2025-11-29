"""Sample swimming workout data using typed workout models."""

from garminconnect.workout import (
    SwimmingWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_interval_step,
    create_recovery_step,
    create_repeat_group,
    create_warmup_step,
)


def create_sample_swimming_workout() -> SwimmingWorkout:
    """Create a sample swimming workout."""
    return SwimmingWorkout(
        workoutName="Swimming Interval Training",
        estimatedDurationInSecs=2400,  # 40 minutes
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 3,
                    "sportTypeKey": "swimming",
                    "displayOrder": 3,
                },
                workoutSteps=[
                    create_warmup_step(300.0, step_order=1),  # 5 min warmup
                    create_repeat_group(
                        iterations=8,
                        workout_steps=[
                            create_interval_step(
                                90.0, step_order=2
                            ),  # 1.5 min interval
                            create_recovery_step(30.0, step_order=3),  # 30 sec recovery
                        ],
                        step_order=2,
                    ),
                    create_cooldown_step(180.0, step_order=3),  # 3 min cooldown
                ],
            )
        ],
    )
