from garminconnect.workout import TargetType, StepType, ConditionType, SportType

def test_target_type_ids() -> None:
    """Pin TargetType IDs to match Garmin API values (issue #333)."""
    assert TargetType.NO_TARGET == 1
    assert TargetType.POWER == 2
    assert TargetType.CADENCE == 3
    assert TargetType.HEART_RATE == 4
    assert TargetType.SPEED == 5
    assert TargetType.OPEN == 6

def test_step_type_ids() -> None:
    assert StepType.WARMUP == 1
    assert StepType.COOLDOWN == 2
    assert StepType.INTERVAL == 3
    assert StepType.RECOVERY == 4
    assert StepType.REST == 5
    assert StepType.REPEAT == 6

def test_condition_type_ids() -> None:
    assert ConditionType.DISTANCE == 1
    assert ConditionType.TIME == 2
    assert ConditionType.HEART_RATE == 3
    assert ConditionType.CALORIES == 4
    assert ConditionType.CADENCE == 5
    assert ConditionType.POWER == 6
    assert ConditionType.ITERATIONS == 7

def test_sport_type_ids() -> None:
    assert SportType.RUNNING == 1
    assert SportType.CYCLING == 2
    assert SportType.SWIMMING == 3
    assert SportType.WALKING == 4
    assert SportType.MULTI_SPORT == 5
    assert SportType.FITNESS_EQUIPMENT == 6
    assert SportType.HIKING == 7
    assert SportType.OTHER == 8
