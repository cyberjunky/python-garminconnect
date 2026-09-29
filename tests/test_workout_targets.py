"""Tests for workout intensity targets and targeted interval steps."""

import pytest
from pydantic import ValidationError

from garminconnect.workout import (
    CadenceTarget,
    ConditionType,
    CustomHeartRateTarget,
    CustomPowerTarget,
    CyclingWorkout,
    HeartRateZoneTarget,
    PaceTarget,
    PowerZoneTarget,
    SpeedTarget,
    StepType,
    TargetType,
    WorkoutSegment,
    create_distance_interval_step,
    create_interval_step,
    create_targeted_distance_interval_step,
    create_targeted_interval_step,
    pace_to_mps,
    speed_to_mps,
)


def _dump(step):
    return step.model_dump(exclude_none=True, mode="json")


def test_untargeted_interval_step_payload_unchanged():
    """Interval steps without targets upload exactly as before targets existed."""
    assert _dump(create_interval_step(300.0, step_order=2)) == {
        "type": "ExecutableStepDTO",
        "stepOrder": 2,
        "stepType": {
            "stepTypeId": StepType.INTERVAL,
            "stepTypeKey": "interval",
            "displayOrder": 3,
        },
        "endCondition": {
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        "endConditionValue": 300.0,
        "targetType": {
            "workoutTargetTypeId": TargetType.NO_TARGET,
            "workoutTargetTypeKey": "no.target",
            "displayOrder": 1,
        },
    }


def test_untargeted_distance_interval_step_payload_unchanged():
    """Distance interval steps without targets upload exactly as before."""
    data = _dump(create_distance_interval_step(600.0, step_order=1))
    assert data["stepType"]["displayOrder"] == 3
    assert data["targetType"] == {
        "workoutTargetTypeId": TargetType.NO_TARGET,
        "workoutTargetTypeKey": "no.target",
        "displayOrder": 1,
    }
    for key in (
        "targetValueOne",
        "targetValueTwo",
        "zoneNumber",
        "secondaryTargetType",
        "secondaryTargetValueOne",
        "secondaryTargetValueTwo",
        "secondaryZoneNumber",
    ):
        assert key not in data


@pytest.mark.parametrize(
    ("target", "type_id", "type_key"),
    [
        (CadenceTarget(lower_limit=170, upper_limit=180), 3, "cadence"),
        (CustomPowerTarget(lower_limit=200, upper_limit=250), 2, "power.zone"),
        (
            CustomHeartRateTarget(lower_limit=140, upper_limit=155),
            4,
            "heart.rate.zone",
        ),
        (SpeedTarget(lower_limit=8.0, upper_limit=9.0), 5, "speed.zone"),
        (PaceTarget(lower_limit=2.7, upper_limit=2.8), 6, "pace.zone"),
    ],
)
def test_range_target_sets_type_and_limits(target, type_id, type_key):
    """Range targets send their type plus lower/upper limits, no zone number."""
    data = _dump(create_targeted_interval_step(120.0, step_order=1, target=target))
    assert data["targetType"] == {
        "workoutTargetTypeId": type_id,
        "workoutTargetTypeKey": type_key,
        "displayOrder": 1,
    }
    assert data["targetValueOne"] == target.lower_limit
    assert data["targetValueTwo"] == target.upper_limit
    assert "zoneNumber" not in data
    assert "secondaryTargetType" not in data


@pytest.mark.parametrize(
    ("target", "type_id", "type_key"),
    [
        (PowerZoneTarget(zone_number=3), 2, "power.zone"),
        (HeartRateZoneTarget(zone_number=2), 4, "heart.rate.zone"),
    ],
)
def test_zone_target_sets_zone_number_only(target, type_id, type_key):
    """Zone targets send the zone number and no limits."""
    data = _dump(create_targeted_interval_step(120.0, step_order=1, target=target))
    assert data["targetType"]["workoutTargetTypeId"] == type_id
    assert data["targetType"]["workoutTargetTypeKey"] == type_key
    assert data["zoneNumber"] == target.zone_number
    assert "targetValueOne" not in data
    assert "targetValueTwo" not in data


def test_secondary_target():
    """A secondary target is sent in the secondary* fields."""
    step = create_targeted_interval_step(
        120.0,
        step_order=1,
        target=CustomPowerTarget(lower_limit=200, upper_limit=250),
        secondary_target=HeartRateZoneTarget(zone_number=2),
    )
    data = _dump(step)
    assert data["secondaryTargetType"] == {
        "workoutTargetTypeId": TargetType.HEART_RATE_ZONE,
        "workoutTargetTypeKey": "heart.rate.zone",
        "displayOrder": 2,
    }
    assert data["secondaryZoneNumber"] == 2
    assert "secondaryTargetValueOne" not in data


def test_targeted_distance_interval_step():
    """Targeted distance steps keep the distance end condition."""
    step = create_targeted_distance_interval_step(
        1000.0, step_order=4, target=CadenceTarget(lower_limit=85, upper_limit=95)
    )
    data = _dump(step)
    assert data["stepOrder"] == 4
    assert data["endCondition"]["conditionTypeId"] == ConditionType.DISTANCE
    assert data["endConditionValue"] == 1000.0
    assert data["targetType"]["workoutTargetTypeId"] == TargetType.CADENCE
    assert (data["targetValueOne"], data["targetValueTwo"]) == (85, 95)


def test_range_target_rejects_reversed_limits():
    with pytest.raises(ValidationError, match="lower_limit must be <= upper_limit"):
        SpeedTarget(lower_limit=9.0, upper_limit=8.0)


def test_range_target_accepts_equal_limits():
    target = CadenceTarget(lower_limit=180, upper_limit=180)
    assert target.lower_limit == target.upper_limit


def test_pace_to_mps():
    assert pace_to_mps(5, 0, "km") == pytest.approx(1000 / 300)
    assert pace_to_mps(8, 0, "mi") == pytest.approx(1609.344 / 480)
    # A slower pace is a lower speed, so it is the lower limit.
    assert pace_to_mps(6, 11, "km") < pace_to_mps(6, 0, "km")


def test_speed_to_mps():
    assert speed_to_mps(36.0, "kph") == pytest.approx(10.0)
    assert speed_to_mps(10.0, "mph") == pytest.approx(4.4704)


def test_targets_survive_workout_serialization():
    """Targets end up in the upload payload of a full workout."""
    workout = CyclingWorkout(
        workoutName="Sweet spot",
        estimatedDurationInSecs=600,
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={"sportTypeId": 2, "sportTypeKey": "cycling"},
                workoutSteps=[
                    create_targeted_interval_step(
                        600.0,
                        step_order=1,
                        target=PowerZoneTarget(zone_number=4),
                        secondary_target=CadenceTarget(lower_limit=85, upper_limit=95),
                    )
                ],
            )
        ],
    )
    step = workout.to_dict()["workoutSegments"][0]["workoutSteps"][0]
    assert step["zoneNumber"] == 4
    assert step["secondaryTargetType"]["workoutTargetTypeId"] == TargetType.CADENCE
    assert (step["secondaryTargetValueOne"], step["secondaryTargetValueTwo"]) == (
        85,
        95,
    )
