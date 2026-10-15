"""Sample swimming workout data using typed workout models."""

from garminconnect.workout import (
    SwimCssOffsetTarget,
    SwimmingWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_interval_step,
    create_recovery_step,
    create_repeat_group,
    create_targeted_interval_step,
    create_warmup_step,
)


def create_sample_swimming_workout() -> SwimmingWorkout:
    """Create a sample swimming workout."""
    return SwimmingWorkout(
        workoutName="Swimming Interval Training",
        description="A sample swimming interval workout with warmup, multiple intervals with recovery, and cooldown.",
        estimatedDurationInSecs=1440,  # 24 minutes: 300 + 8 x (90 + 30) + 180
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


def create_sample_swimming_css_workout() -> SwimmingWorkout:
    """Create a sample swimming workout with CSS-offset interval targets.

    Same structure as ``create_sample_swimming_workout`` (time-based steps),
    except each interval carries a secondary ``SwimCssOffsetTarget`` of
    +5 seconds, so the CSS target is the only difference between the two.
    """
    return SwimmingWorkout(
        workoutName="Swimming CSS Intervals",
        description="A sample swimming workout with intervals at CSS +5 seconds.",
        estimatedDurationInSecs=1440,  # 24 minutes: 300 + 8 x (90 + 30) + 180
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
                            create_targeted_interval_step(
                                90.0,
                                step_order=2,
                                secondary_target=SwimCssOffsetTarget(
                                    offset_seconds=5.0
                                ),
                            ),  # 1.5 min interval at CSS +5s
                            create_recovery_step(30.0, step_order=3),  # 30 sec recovery
                        ],
                        step_order=2,
                    ),
                    create_cooldown_step(180.0, step_order=3),  # 3 min cooldown
                ],
            )
        ],
    )
