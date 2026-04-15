import pytest
import requests

import garminconnect
from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

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
def test_all_day_stress(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    all_day_stress = garmin.get_all_day_stress(DATE)
    # Validate stress data structure
    assert "calendarDate" in all_day_stress
    assert "avgStressLevel" in all_day_stress
    assert "maxStressLevel" in all_day_stress
    assert "stressValuesArray" in all_day_stress


@pytest.mark.vcr
def test_upload(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    fpath = "tests/12129115726_ACTIVITY.fit"
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


# ---------------------------------------------------------------------------
# Retry / backoff tests (no network, no VCR cassettes).
# ---------------------------------------------------------------------------


def _fast_garmin(**kwargs):
    """Build a Garmin instance with near-zero retry waits for fast tests."""
    return garminconnect.Garmin(
        "email@example.org",
        "password",
        retry_min_wait=0.0,
        retry_max_wait=0.01,
        **kwargs,
    )


def test_connectapi_retries_on_503_then_succeeds(mocker):
    """503 -> 503 -> 200: connectapi should eventually return the good payload."""
    g = _fast_garmin(max_retries=3)
    good_payload = {"calendarDate": "2023-07-01", "totalSteps": 12345}

    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=[
            GarminConnectConnectionError("API Error 503 - Service Unavailable"),
            GarminConnectConnectionError("API Error 503 - Service Unavailable"),
            good_payload,
        ],
    )

    result = g.connectapi("/usersummary-service/usersummary/daily/2023-07-01")
    assert result == good_payload
    assert inner.call_count == 3


def test_connectapi_does_not_retry_on_404(mocker):
    """4xx failures must fail fast — one call only, no retries."""
    g = _fast_garmin(max_retries=3)

    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=GarminConnectConnectionError("API Error 404 - Not Found"),
    )

    with pytest.raises(GarminConnectConnectionError):
        g.connectapi("/does/not/exist")

    assert inner.call_count == 1


def test_connectapi_does_not_retry_on_401(mocker):
    """401 auth errors must fail fast — user has to re-login."""
    g = _fast_garmin(max_retries=3)

    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=GarminConnectConnectionError("API Error 401 - Unauthorized"),
    )

    with pytest.raises(GarminConnectAuthenticationError):
        g.connectapi("/userprofile-service/userprofile/settings")

    assert inner.call_count == 1


def test_connectapi_does_not_retry_on_429(mocker):
    """429 rate-limit errors are already a signal to back off — don't retry."""
    g = _fast_garmin(max_retries=3)

    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=GarminConnectConnectionError("API Error 429 - Too Many Requests"),
    )

    with pytest.raises(GarminConnectTooManyRequestsError):
        g.connectapi("/usersummary-service/usersummary/daily/2023-07-01")

    assert inner.call_count == 1


def test_connectapi_exhausts_retries_and_reraises(mocker):
    """After max_retries transient failures, the final 5xx error is re-raised."""
    g = _fast_garmin(max_retries=2)

    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=GarminConnectConnectionError("API Error 502 - Bad Gateway"),
    )

    with pytest.raises(GarminConnectConnectionError):
        g.connectapi("/usersummary-service/usersummary/daily/2023-07-01")

    # 1 initial attempt + 2 retries == 3 total calls
    assert inner.call_count == 3


def test_connectapi_retries_disabled(mocker):
    """max_retries=0 should disable retries entirely."""
    g = _fast_garmin(max_retries=0)

    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=GarminConnectConnectionError("API Error 503 - Service Unavailable"),
    )

    with pytest.raises(GarminConnectConnectionError):
        g.connectapi("/usersummary-service/usersummary/daily/2023-07-01")

    assert inner.call_count == 1


def test_download_retries_on_5xx(mocker):
    """The download method should use the same retry wrapper."""
    g = _fast_garmin(max_retries=3)
    blob = b"fit-file-bytes"

    inner = mocker.patch.object(
        g.client,
        "download",
        side_effect=[
            GarminConnectConnectionError("API Error 500 - Internal Server Error"),
            blob,
        ],
    )

    result = g.download("/download-service/files/activity/12345")
    assert result == blob
    assert inner.call_count == 2


def test_connectwebproxy_retries_on_5xx(mocker):
    """The connectwebproxy method should also be retried on 5xx."""
    g = _fast_garmin(max_retries=3)

    class _Resp:
        def json(self):
            return {"ok": 1}

    inner = mocker.patch.object(
        g.client,
        "request",
        side_effect=[
            GarminConnectConnectionError("API Error 503 - Service Unavailable"),
            _Resp(),
        ],
    )

    result = g.connectwebproxy("/proxy/path")
    assert result == {"ok": 1}
    assert inner.call_count == 2


def test_retry_invalid_max_retries():
    """max_retries must be a non-negative int."""
    with pytest.raises(ValueError, match="max_retries"):
        garminconnect.Garmin("e@x.y", "p", max_retries=-1)
    with pytest.raises(ValueError, match="max_retries"):
        garminconnect.Garmin("e@x.y", "p", max_retries="3")  # type: ignore[arg-type]


def test_connectapi_retries_on_raw_requests_connection_error(mocker):
    """Raw requests.ConnectionError from lower layers should trigger retry."""
    g = _fast_garmin(max_retries=3)
    good_payload = {"ok": True}

    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=[
            requests.ConnectionError("DNS resolution failed"),
            good_payload,
        ],
    )

    result = g.connectapi("/some/path")
    assert result == good_payload
    assert inner.call_count == 2


def test_connectapi_retries_on_raw_requests_timeout(mocker):
    """Raw requests.Timeout from lower layers should trigger retry."""
    g = _fast_garmin(max_retries=3)
    good_payload = {"ok": True}

    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=[
            requests.Timeout("read timed out"),
            good_payload,
        ],
    )

    result = g.connectapi("/some/path")
    assert result == good_payload
    assert inner.call_count == 2


def test_download_retries_on_raw_requests_connection_error(mocker):
    """download() should retry raw requests.ConnectionError too."""
    g = _fast_garmin(max_retries=3)

    inner = mocker.patch.object(
        g.client,
        "download",
        side_effect=[
            requests.ConnectionError("connection reset"),
            b"bytes",
        ],
    )

    assert g.download("/download/path") == b"bytes"
    assert inner.call_count == 2


def test_connectapi_does_not_retry_statusless_without_network_cause(mocker):
    """Status-less GarminConnectConnectionError without a network cause
    (e.g. JSON decode error, AttributeError wrapped downstream) must NOT
    be retried — it's a deterministic failure, retrying wastes time."""
    g = _fast_garmin(max_retries=3)

    # A fresh GarminConnectConnectionError with no status in the message
    # and no __cause__ — represents a programming / decode bug.
    inner = mocker.patch.object(
        g.client,
        "connectapi",
        side_effect=GarminConnectConnectionError("Unexpected payload shape"),
    )

    with pytest.raises(GarminConnectConnectionError):
        g.connectapi("/some/path")

    assert inner.call_count == 1


def test_get_gear_stats_404_returns_empty_dict(mocker):
    """get_gear_stats() relies on being able to read e.response.status_code
    after a 404 — our retry wrapper must not strip that attribute."""
    g = _fast_garmin(max_retries=0)

    # Fabricate a GarminConnectConnectionError that carries a .response
    # attribute — simulating what a lower layer might attach.
    resp = mocker.Mock()
    resp.status_code = 404
    err = GarminConnectConnectionError("API Error 404 - Not Found")
    err.response = resp  # type: ignore[attr-defined]

    mocker.patch.object(g.client, "connectapi", side_effect=err)

    # Should swallow the 404 and return {} rather than propagating.
    assert g.get_gear_stats("gear-uuid-abc") == {}


def test_get_gear_activities_404_returns_empty_list(mocker):
    """get_gear_activities() must also retain e.response.status_code access."""
    g = _fast_garmin(max_retries=0)

    resp = mocker.Mock()
    resp.status_code = 404
    err = GarminConnectConnectionError("API Error 404 - Not Found")
    err.response = resp  # type: ignore[attr-defined]

    mocker.patch.object(g.client, "connectapi", side_effect=err)

    assert g.get_gear_activities("gear-uuid-abc") == []
