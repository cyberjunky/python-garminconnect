"""Sample running workout data using typed workout models."""

from garminconnect.workout import (
    PaceTarget,
    RunningWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_recovery_step,
    create_repeat_group,
    create_targeted_interval_step,
    create_warmup_step,
    pace_to_mps,
)


def create_sample_running_workout() -> RunningWorkout:
    """Create a sample interval running workout."""
    return RunningWorkout(
        workoutName="Interval Running Session",
        estimatedDurationInSecs=1800,  # 30 minutes
        description="A sample interval running workout with warmup, intervals, recovery, and cooldown.",
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
                            # 1 min interval at 4:30-4:50 min/km (limits in m/s,
                            # so the slower pace is the lower limit)
                            create_targeted_interval_step(
                                60.0,
                                step_order=2,
                                target=PaceTarget(
                                    lower_limit=pace_to_mps(4, 50, "km"),
                                    upper_limit=pace_to_mps(4, 30, "km"),
                                ),
                            ),
                            create_recovery_step(60.0, step_order=3),  # 1 min recovery
                        ],
                        step_order=2,
                    ),
                    create_cooldown_step(120.0, step_order=3),  # 2 min cooldown
                ],
            )
        ],
    )
