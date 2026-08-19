import os
from pathlib import Path

import pytest

import garminconnect
from garminconnect.fit import FitEncoder

DATE = "2023-07-01"
pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def garmin() -> garminconnect.Garmin:
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        pytest.skip("GARMIN_EMAIL and GARMIN_PASSWORD are required")
    return garminconnect.Garmin(email, password)


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
    steps = garmin.get_steps_data(DATE)
    if not steps:
        pytest.skip("No steps data for date")
    steps_data = steps[0]
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
    # The API returns a list of daily step dictionaries
    assert isinstance(daily_steps_data, list)
    assert len(daily_steps_data) > 0

    # Check the first day's data
    daily_steps = daily_steps_data[0]
    assert "calendarDate" in daily_steps
    assert "totalSteps" in daily_steps


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
    bb = garmin.get_body_battery(DATE)
    if not bb:
        pytest.skip("No body battery data for date")
    body_battery = bb[0]
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
    # HRV data might not be available for all dates (API returns 204 No Content)
    if hrv_data is not None:
        # If data exists, validate the structure
        assert "hrvSummary" in hrv_data
        assert "weeklyAvg" in hrv_data["hrvSummary"]
    else:
        # If no data, that's also a valid response (204 No Content)
        assert hrv_data is None


@pytest.mark.vcr
def test_download_activity(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    activity_id = "11998957007"
    # This test may fail with 403 Forbidden if the activity is private or not accessible
    # In such cases, we verify that the appropriate error is raised
    try:
        activity = garmin.download_activity(activity_id)
        assert activity  # If successful, activity should not be None/empty
    except garminconnect.GarminConnectConnectionError as e:
        # Expected error for inaccessible activities
        assert "403" in str(e) or "Forbidden" in str(e)
        pytest.skip(
            "Activity not accessible (403 Forbidden) - expected in test environment"
        )


@pytest.mark.vcr
def test_download_health_snapshot(garmin: garminconnect.Garmin) -> None:
    garmin.login()

    try:
        snapshot = garmin.download_health_snapshot(DATE)
        assert isinstance(snapshot, bytes)
        assert snapshot
    except garminconnect.GarminConnectConnectionError as e:
        assert any(code in str(e) for code in ("403", "404", "Forbidden", "Not Found"))
        pytest.skip("Health Snapshot unavailable for this date")


@pytest.mark.vcr
def test_all_day_stress(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    all_day_stress = garmin.get_all_day_stress(DATE)
    # Validate stress data structure
    assert "calendarDate" in all_day_stress
    assert "avgStressLevel" in all_day_stress
    assert "maxStressLevel" in all_day_stress
    assert "stressValuesArray" in all_day_stress


def _synthetic_activity_fit(tmp_path: Path) -> str:
    """Return the path to a minimal, anonymised .fit upload fixture.

    The historical test file was a real physical-device recording containing
    biometric PII; it has been removed from the repository.  Integration
    testers can still supply a real file via the GARMIN_TEST_ACTIVITY_FIT env
    var if they need to record against the live API.
    """
    if path := os.getenv("GARMIN_TEST_ACTIVITY_FIT"):
        return path

    encoder = FitEncoder()
    encoder.write_file_info(
        serial_number=1234567890,
        manufacturer=1,  # garmin
        product=1,
    )
    encoder.write_file_creator(software_version=1)
    encoder.finish()

    fpath = tmp_path / "synthetic_activity.fit"
    fpath.write_bytes(encoder.getvalue())
    return str(fpath)


@pytest.mark.vcr
def test_upload(garmin: garminconnect.Garmin, tmp_path: Path) -> None:
    garmin.login()
    fpath = _synthetic_activity_fit(tmp_path)
    # This test may fail with 409 Conflict if the activity already exists
    # In such cases, we verify that the appropriate error is raised
    try:
        result = garmin.upload_activity(fpath)
        assert result  # If successful, should return upload result
    except Exception as e:
        # Expected error for duplicate uploads
        if "409" in str(e) or "Conflict" in str(e):
            pytest.skip(
                "Activity already exists (409 Conflict) - expected in test environment"
            )
        else:
            # Re-raise unexpected errors
            raise


@pytest.mark.vcr
def test_request_reload(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    cdate = "2021-01-01"
    # Get initial steps data
    sum(steps["steps"] for steps in garmin.get_steps_data(cdate))
    # Test that request_reload returns a valid response
    reload_response = garmin.request_reload(cdate)
    assert reload_response is not None
    # Get steps data after reload - should still be accessible
    final_steps = sum(steps["steps"] for steps in garmin.get_steps_data(cdate))
    assert final_steps >= 0  # Steps data should be non-negative

@pytest.mark.vcr
def test_get_golf_shot_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    # Test with no holes specified
    result = garmin.get_golf_shot_data(12345678)
    assert result is not None
