"""Sample running workout data using typed workout models."""

from garminconnect.workout import (
    RunningWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_interval_step,
    create_recovery_step,
    create_repeat_group,
    create_warmup_step,
)


def create_sample_running_workout() -> RunningWorkout:
    """Create a sample interval running workout."""
    return RunningWorkout(
        workoutName="Interval Running Session",
        estimatedDurationInSecs=1800,  # 30 minutes
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 1,
                    "sportTypeKey": "running",
                    "displayOrder": 1,
                },
                workoutSteps=[
                    create_warmup_step(300.0, step_order=1),  # 5 min warmup
                    create_repeat_group(
                        iterations=6,
                        workout_steps=[
                            create_interval_step(60.0, step_order=2),  # 1 min interval
                            create_recovery_step(60.0, step_order=3),  # 1 min recovery
                        ],
                        step_order=2,
                    ),
                    create_cooldown_step(120.0, step_order=3),  # 2 min cooldown
                ],
            )
        ],
    )
