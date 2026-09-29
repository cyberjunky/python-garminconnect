"""Sample cycling workout data using typed workout models."""

from garminconnect.workout import (
    CadenceTarget,
    CustomPowerTarget,
    CyclingWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_recovery_step,
    create_repeat_group,
    create_targeted_interval_step,
    create_warmup_step,
)


def create_sample_cycling_workout() -> CyclingWorkout:
    """Create a sample interval cycling workout."""
    return CyclingWorkout(
        workoutName="Cycling Power Intervals",
        description="A sample cycling power interval workout with warmup, power intervals with recovery, and cooldown.",
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
                            # 5 min interval at 220-250 W, 85-95 rpm
                            create_targeted_interval_step(
                                300.0,
                                step_order=2,
                                target=CustomPowerTarget(
                                    lower_limit=220, upper_limit=250
                                ),
                                secondary_target=CadenceTarget(
                                    lower_limit=85, upper_limit=95
                                ),
                            ),
                            create_recovery_step(180.0, step_order=3),  # 3 min recovery
                        ],
                        step_order=2,
                    ),
                    create_cooldown_step(300.0, step_order=3),  # 5 min cooldown
                ],
            )
        ],
    )
