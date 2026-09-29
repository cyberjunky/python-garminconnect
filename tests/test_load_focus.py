"""Offline regression tests for the load-focus API methods."""

from unittest.mock import Mock

import pytest

from garminconnect import Garmin


@pytest.fixture
def garmin():
    """Return a Garmin client with connectapi mocked."""
    client = Garmin()
    client.connectapi = Mock()
    return client


@pytest.mark.parametrize(
    "method,path",
    [
        ("get_training_four_week_load_balance", "trainingloadbalance/latest"),
        ("get_daily_training_status", "trainingstatus/daily"),
    ],
)
def test_load_summary(garmin, method, path):
    """Verify training-load summary endpoint construction."""
    response = {"load": 123}
    garmin.connectapi.return_value = response
    assert getattr(garmin, method)("2026-09-20") is response
    garmin.connectapi.assert_called_once_with(
        f"/metrics-service/metrics/{path}/2026-09-20"
    )


@pytest.mark.parametrize(
    "method,args",
    [
        ("get_training_four_week_load_balance", ("bad-date",)),
        ("get_daily_training_status", ("2026-02-30",)),
        ("get_training_load_activities", ("bad-date", "2026-09-20")),
        ("get_training_load_activities", ("2026-09-01", "bad-date")),
        ("get_training_load_activities", ("2026-09-20", "2026-09-01")),
    ],
)
def test_invalid_dates_do_not_send_requests(garmin, method, args):
    """Reject invalid date inputs before making requests."""
    with pytest.raises(ValueError):
        getattr(garmin, method)(*args)
    garmin.connectapi.assert_not_called()


@pytest.mark.parametrize(
    "metrics,expected_metrics",
    [
        (
            None,
            [
                "activityTrainingLoad",
                "trainingEffectLabel",
                "trainingEffectLabelSrvrCalc",
            ],
        ),
        ([], []),
        (["activityTrainingLoad"], ["activityTrainingLoad"]),
    ],
)
@pytest.mark.parametrize("activitytype", [None, "running"])
def test_activity_load_metrics_and_filter(
    garmin, metrics, expected_metrics, activitytype
):
    """Verify activity load metric and activity-type query parameters."""
    response = [{"activityTrainingLoad": 123}]
    garmin.connectapi.return_value = response
    assert (
        garmin.get_training_load_activities(
            "2026-09-01", "2026-09-20", metrics=metrics, activitytype=activitytype
        )
        is response
    )
    params = {
        "startDate": "2026-09-01",
        "endDate": "2026-09-20",
        "metric": expected_metrics,
    }
    if activitytype:
        params["activityType"] = activitytype
    garmin.connectapi.assert_called_once_with(
        "/fitnessstats-service/activity/all", params=params
    )
