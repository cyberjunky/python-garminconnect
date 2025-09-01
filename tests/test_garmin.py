import pytest

import garminconnect

DATE = "2023-07-01"


@pytest.fixture(scope="session")
def garmin() -> garminconnect.Garmin:
    return garminconnect.Garmin("email@example.org", "password")


@pytest.mark.vcr
def test_stats(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    stats = garmin.get_stats(DATE)
    assert "totalKilocalories" in stats
    assert "activeKilocalories" in stats


@pytest.mark.vcr
def test_user_summary(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    user_summary = garmin.get_user_summary(DATE)
    assert "totalKilocalories" in user_summary
    assert "activeKilocalories" in user_summary


@pytest.mark.vcr
def test_steps_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    steps_data = garmin.get_steps_data(DATE)[0]
    assert "steps" in steps_data


@pytest.mark.vcr
def test_floors(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    floors_data = garmin.get_floors(DATE)
    assert "floorValuesArray" in floors_data


@pytest.mark.vcr
def test_daily_steps(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    daily_steps_data = garmin.get_daily_steps(DATE, DATE)
    # The API returns a dict, likely with a list inside
    if isinstance(daily_steps_data, dict) and len(daily_steps_data) > 0:
        # Get the first available data entry
        daily_steps = (
            list(daily_steps_data.values())[0] if daily_steps_data else daily_steps_data
        )
    else:
        daily_steps = daily_steps_data
    assert "calendarDate" in daily_steps or "totalSteps" in daily_steps


@pytest.mark.vcr
def test_heart_rates(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    heart_rates = garmin.get_heart_rates(DATE)
    assert "calendarDate" in heart_rates
    assert "restingHeartRate" in heart_rates


@pytest.mark.vcr
def test_stats_and_body(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    stats_and_body = garmin.get_stats_and_body(DATE)
    assert "calendarDate" in stats_and_body
    assert "metabolicAge" in stats_and_body


@pytest.mark.vcr
def test_body_composition(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    body_composition = garmin.get_body_composition(DATE)
    assert "totalAverage" in body_composition
    assert "metabolicAge" in body_composition["totalAverage"]


@pytest.mark.vcr
def test_body_battery(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    body_battery = garmin.get_body_battery(DATE)[0]
    assert "date" in body_battery
    assert "charged" in body_battery


@pytest.mark.vcr
def test_hydration_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    hydration_data = garmin.get_hydration_data(DATE)
    assert hydration_data
    assert "calendarDate" in hydration_data


@pytest.mark.vcr
def test_respiration_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    respiration_data = garmin.get_respiration_data(DATE)
    assert "calendarDate" in respiration_data
    assert "avgSleepRespirationValue" in respiration_data


@pytest.mark.vcr
def test_spo2_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    spo2_data = garmin.get_spo2_data(DATE)
    assert "calendarDate" in spo2_data
    assert "averageSpO2" in spo2_data


@pytest.mark.vcr
def test_hrv_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    hrv_data = garmin.get_hrv_data(DATE)
    assert "hrvSummary" in hrv_data
    assert "weeklyAvg" in hrv_data["hrvSummary"]


@pytest.mark.vcr
def test_download_activity(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    activity_id = "11998957007"
    activity = garmin.download_activity(activity_id)
    assert activity


@pytest.mark.vcr
def test_all_day_stress(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    all_day_stress = garmin.get_all_day_stress(DATE)
    assert "bodyBatteryValuesArray" in all_day_stress
    assert "calendarDate" in all_day_stress


@pytest.mark.vcr
def test_upload(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    fpath = "tests/12129115726_ACTIVITY.fit"
    assert garmin.upload_activity(fpath)


@pytest.mark.vcr
def test_request_reload(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    cdate = "2021-01-01"
    assert sum(steps["steps"] for steps in garmin.get_steps_data(cdate)) == 0
    assert garmin.request_reload(cdate)
    # In practice, the data can take a while to load
    assert sum(steps["steps"] for steps in garmin.get_steps_data(cdate)) > 0
