"""Sample hiking workout data using typed workout models."""

from garminconnect.workout import (
    HikingWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_warmup_step,
)


def create_sample_hiking_workout() -> HikingWorkout:
    """Create a sample hiking workout."""
    return HikingWorkout(
        workoutName="Mountain Hiking Trail",
        estimatedDurationInSecs=7200,  # 2 hours
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 7,
                    "sportTypeKey": "hiking",
                    "displayOrder": 7,
                },
                workoutSteps=[
                    create_warmup_step(600.0, step_order=1),  # 10 min warmup
                    # Main hiking segment (continuous)
                    create_cooldown_step(600.0, step_order=2),  # 10 min cooldown
                ],
            )
        ],
    )
