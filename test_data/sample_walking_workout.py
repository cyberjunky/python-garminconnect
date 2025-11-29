"""Sample walking workout data using typed workout models."""

from garminconnect.workout import (
    WalkingWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_warmup_step,
)


def create_sample_walking_workout() -> WalkingWorkout:
    """Create a sample walking workout."""
    return WalkingWorkout(
        workoutName="Brisk Walking Session",
        estimatedDurationInSecs=2700,  # 45 minutes
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 4,
                    "sportTypeKey": "walking",
                    "displayOrder": 4,
                },
                workoutSteps=[
                    create_warmup_step(300.0, step_order=1),  # 5 min warmup
                    # Main walking segment (no specific steps, just continuous)
                    create_cooldown_step(300.0, step_order=2),  # 5 min cooldown
                ],
            )
        ],
    )
