import pytest

import garminconnect


DATE = "2023-07-01"


@pytest.fixture(scope="session")
def garmin():
    return garminconnect.Garmin("email", "password")


@pytest.mark.vcr
def test_stats(garmin):
    garmin.login()
    stats = garmin.get_stats(DATE)
    assert "totalKilocalories" in stats
    assert "activeKilocalories" in stats


@pytest.mark.vcr
def test_user_summary(garmin):
    garmin.login()
    user_summary = garmin.get_user_summary(DATE)
    assert "totalKilocalories" in user_summary
    assert "activeKilocalories" in user_summary


@pytest.mark.vcr
def test_steps_data(garmin):
    garmin.login()
    steps_data = garmin.get_steps_data(DATE)[0]
    assert "steps" in steps_data


@pytest.mark.vcr
def test_floors(garmin):
    garmin.login()
    floors_data = garmin.get_floors(DATE)
    assert "floorValuesArray" in floors_data


@pytest.mark.vcr
def test_daily_steps(garmin):
    garmin.login()
    daily_steps = garmin.get_daily_steps(DATE, DATE)[0]
    assert "calendarDate" in daily_steps
    assert "totalSteps" in daily_steps
    assert "stepGoal" in daily_steps
