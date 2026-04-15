"""Mock-based unit tests for Garmin Connect API wrapper.

Unlike ``tests/test_garmin.py`` — which uses ``pytest-vcr`` cassettes recorded
against a real Garmin account — these tests mock ``Garmin.connectapi`` directly.
That lets us verify parameter validation, URL construction, and response
handling on the Python side without any network access, credentials, or
cassette maintenance.

Each test focuses on one of the following:
    * date / numeric parameter validation (``_validate_*`` helpers)
    * URL path or query parameter construction
    * response pass-through / transformation

Run with:

    python -m pytest tests/test_garmin_unit.py -v
"""

from unittest.mock import patch

import pytest

import garminconnect


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def garmin() -> garminconnect.Garmin:
    """Return a Garmin instance with no network access.

    A display name is pre-populated so methods that interpolate it into URLs
    (``get_user_summary``, ``get_personal_record``, ...) can be exercised
    without calling ``login()``.
    """
    g = garminconnect.Garmin("test@example.com", "password")
    g.display_name = "test-display"
    g.full_name = "Test User"
    g.unit_system = "metric"
    return g


# ---------------------------------------------------------------------------
# Date validation tests (rejects bad input on many methods)
# ---------------------------------------------------------------------------


class TestDateValidation:
    """``_validate_date_format`` should reject non-strings and malformed dates."""

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_hrv_data",
            "get_training_readiness",
            "get_morning_training_readiness",
            "get_stress_data",
            "get_max_metrics",
            "get_fitnessage_data",
            "get_training_status",
            "get_respiration_data",
            "get_spo2_data",
            "get_intensity_minutes_data",
            "get_user_summary",
        ],
    )
    def test_rejects_malformed_date_string(
        self, garmin: garminconnect.Garmin, method_name: str
    ) -> None:
        method = getattr(garmin, method_name)
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            method("not-a-date")

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_hrv_data",
            "get_training_readiness",
            "get_stress_data",
            "get_max_metrics",
            "get_fitnessage_data",
            "get_training_status",
        ],
    )
    def test_rejects_non_string_date(
        self, garmin: garminconnect.Garmin, method_name: str
    ) -> None:
        method = getattr(garmin, method_name)
        with pytest.raises(ValueError, match="must be a string"):
            method(20260315)

    def test_rejects_impossible_calendar_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        # Format matches YYYY-MM-DD regex but Feb 30 is not a real date.
        with pytest.raises(ValueError, match="invalid cdate"):
            garmin.get_hrv_data("2026-02-30")


# ---------------------------------------------------------------------------
# URL construction tests
# ---------------------------------------------------------------------------


class TestUrlConstruction:
    """Verify path / query params are threaded through to connectapi correctly."""

    def test_get_hrv_data_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        payload = {"hrvSummary": {"weeklyAvg": 42}}
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_hrv_data("2026-03-15")

        mock.assert_called_once()
        url = mock.call_args[0][0]
        assert url.endswith("/hrv-service/hrv/2026-03-15")
        assert result == payload

    def test_get_training_readiness_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        payload = [{"score": 88, "inputContext": "AFTER_WAKEUP_RESET"}]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_training_readiness("2026-03-15")

        url = mock.call_args[0][0]
        assert "/metrics-service/metrics/trainingreadiness/2026-03-15" in url
        assert result == payload

    def test_get_stress_data_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"avgStress": 25}) as mock:
            garmin.get_stress_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/dailyStress/2026-03-15")

    def test_get_max_metrics_repeats_date_in_path(
        self, garmin: garminconnect.Garmin
    ) -> None:
        # get_max_metrics uses the same date twice: /{cdate}/{cdate}
        with patch.object(garmin, "connectapi", return_value={"vo2Max": 55}) as mock:
            garmin.get_max_metrics("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/metrics-service/metrics/maxmet/daily/2026-03-15/2026-03-15")

    def test_get_fitnessage_data_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"chronologicalAge": 30}) as mock:
            garmin.get_fitnessage_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/fitnessage-service/fitnessage/2026-03-15")

    def test_get_training_status_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"status": "productive"}) as mock:
            garmin.get_training_status("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith(
            "/metrics-service/metrics/trainingstatus/aggregated/2026-03-15"
        )

    def test_get_respiration_data_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"avgSleepRespirationValue": 13.5}) as mock:
            garmin.get_respiration_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/daily/respiration/2026-03-15")

    def test_get_spo2_data_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"averageSpO2": 96}) as mock:
            garmin.get_spo2_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/daily/spo2/2026-03-15")

    def test_get_intensity_minutes_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"weeklyGoal": 150}) as mock:
            garmin.get_intensity_minutes_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/daily/im/2026-03-15")

    def test_get_user_summary_uses_display_name_and_calendar_date(
        self, garmin: garminconnect.Garmin
    ) -> None:
        payload = {"totalKilocalories": 2500, "activeKilocalories": 600}
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_user_summary("2026-03-15")

        url = mock.call_args[0][0]
        params = mock.call_args.kwargs["params"]
        assert url.endswith(f"/usersummary-service/usersummary/daily/{garmin.display_name}")
        assert params == {"calendarDate": "2026-03-15"}
        assert result == payload

    def test_get_personal_record_uses_display_name(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value=[{"id": 1}]) as mock:
            garmin.get_personal_record()

        url = mock.call_args[0][0]
        assert url.endswith(f"/personalrecord-service/personalrecord/prs/{garmin.display_name}")

    def test_get_device_settings_builds_url_with_device_id(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"alarms": []}) as mock:
            garmin.get_device_settings("3271234567")

        url = mock.call_args[0][0]
        assert url.endswith("/device-service/deviceservice/device-info/settings/3271234567")

    def test_get_gear_builds_url_with_profile_number(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value=[{"gearId": 1}]) as mock:
            garmin.get_gear("98765")

        url = mock.call_args[0][0]
        assert "/gear-service/gear/filterGear" in url
        assert "userProfilePk=98765" in url

    def test_get_weigh_ins_builds_url_with_date_range(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"dailyWeightSummaries": []}) as mock:
            garmin.get_weigh_ins("2026-01-01", "2026-01-31")

        url = mock.call_args[0][0]
        assert url.endswith("/weight-service/weight/range/2026-01-01/2026-01-31")
        assert mock.call_args.kwargs["params"] == {"includeAll": True}

    def test_get_weekly_steps_builds_url_with_end_and_weeks(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value=[{"totalSteps": 50000}]) as mock:
            garmin.get_weekly_steps("2026-03-15", weeks=12)

        url = mock.call_args[0][0]
        assert url.endswith("/usersummary-service/stats/steps/weekly/2026-03-15/12")


# ---------------------------------------------------------------------------
# Parameter limit tests
# ---------------------------------------------------------------------------


class TestParameterLimits:
    """Enforce MAX_ACTIVITY_LIMIT, MAX_HYDRATION_ML, and related bounds."""

    def test_get_activities_rejects_limit_above_max(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="limit cannot exceed"):
            garmin.get_activities(start=0, limit=garminconnect.MAX_ACTIVITY_LIMIT + 1)

    def test_get_activities_accepts_limit_at_max(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_activities(start=0, limit=garminconnect.MAX_ACTIVITY_LIMIT)

        # Ensure the API was actually called (no exception before dispatch)
        mock.assert_called_once()
        params = mock.call_args.kwargs["params"]
        assert params["limit"] == str(garminconnect.MAX_ACTIVITY_LIMIT)
        assert params["start"] == "0"

    def test_get_activities_rejects_negative_start(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            garmin.get_activities(start=-1, limit=10)

    def test_get_activities_rejects_zero_limit(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            garmin.get_activities(start=0, limit=0)

    def test_get_activities_passes_activitytype(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_activities(start=0, limit=5, activitytype="running")

        params = mock.call_args.kwargs["params"]
        assert params["activityType"] == "running"

    def test_get_activities_returns_empty_list_when_api_returns_none(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value=None):
            result = garmin.get_activities(start=0, limit=5)

        assert result == []

    def test_add_hydration_data_rejects_excessive_amount(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="unreasonably high"):
            garmin.add_hydration_data(garminconnect.MAX_HYDRATION_ML + 1)

    def test_add_hydration_data_rejects_non_number(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="must be a number"):
            garmin.add_hydration_data("500")  # type: ignore[arg-type]

    def test_add_hydration_data_rejects_excessive_negative_amount(
        self, garmin: garminconnect.Garmin
    ) -> None:
        # Negative amounts (subtractions) are allowed but still bounded by abs().
        with pytest.raises(ValueError, match="unreasonably high"):
            garmin.add_hydration_data(-(garminconnect.MAX_HYDRATION_ML + 1))

    def test_get_adhoc_challenges_rejects_negative_start(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            garmin.get_adhoc_challenges(start=-1, limit=5)

    def test_get_adhoc_challenges_rejects_zero_limit(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            garmin.get_adhoc_challenges(start=0, limit=0)

    def test_get_adhoc_challenges_passes_params_as_strings(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"challenges": []}) as mock:
            garmin.get_adhoc_challenges(start=0, limit=10)

        params = mock.call_args.kwargs["params"]
        assert params == {"start": "0", "limit": "10"}

    def test_get_weekly_steps_rejects_non_positive_weeks(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            garmin.get_weekly_steps("2026-03-15", weeks=0)


# ---------------------------------------------------------------------------
# Response pass-through / transformation tests
# ---------------------------------------------------------------------------


class TestResponseHandling:
    """Verify methods return payloads unchanged or transform them correctly."""

    def test_get_hrv_data_returns_none_on_204(
        self, garmin: garminconnect.Garmin
    ) -> None:
        # Garmin returns 204 No Content when there is no HRV data for a date.
        with patch.object(garmin, "connectapi", return_value=None):
            assert garmin.get_hrv_data("2026-03-15") is None

    def test_get_devices_returns_list_unchanged(
        self, garmin: garminconnect.Garmin
    ) -> None:
        payload = [
            {"deviceId": 1, "displayName": "Fenix"},
            {"deviceId": 2, "displayName": "Edge"},
        ]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_devices()

        mock.assert_called_once_with("/device-service/deviceregistration/devices")
        assert result == payload

    def test_get_earned_badges_passes_through(
        self, garmin: garminconnect.Garmin
    ) -> None:
        payload = [{"badgeId": 100, "badgeName": "5K"}]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_earned_badges()

        mock.assert_called_once_with("/badge-service/badge/earned")
        assert result == payload

    def test_get_available_badges_sets_exclusive_badge_flag(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_available_badges()

        mock.assert_called_once()
        params = mock.call_args.kwargs["params"]
        assert params == {"showExclusiveBadge": "true"}

    def test_get_morning_training_readiness_picks_after_wakeup_entry(
        self, garmin: garminconnect.Garmin
    ) -> None:
        payload = [
            {"inputContext": "MANUAL", "score": 50},
            {"inputContext": "AFTER_WAKEUP_RESET", "score": 85},
            {"inputContext": "MANUAL", "score": 60},
        ]
        with patch.object(garmin, "get_training_readiness", return_value=payload):
            result = garmin.get_morning_training_readiness("2026-03-15")

        assert result == {"inputContext": "AFTER_WAKEUP_RESET", "score": 85}

    def test_get_morning_training_readiness_falls_back_to_first_entry(
        self, garmin: garminconnect.Garmin
    ) -> None:
        payload = [
            {"inputContext": None, "score": 75},
            {"inputContext": None, "score": 70},
        ]
        with patch.object(garmin, "get_training_readiness", return_value=payload):
            result = garmin.get_morning_training_readiness("2026-03-15")

        assert result == {"inputContext": None, "score": 75}

    def test_get_morning_training_readiness_returns_none_for_empty_data(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "get_training_readiness", return_value=None):
            assert garmin.get_morning_training_readiness("2026-03-15") is None

        with patch.object(garmin, "get_training_readiness", return_value=[]):
            assert garmin.get_morning_training_readiness("2026-03-15") is None

    def test_get_morning_training_readiness_passes_through_dict(
        self, garmin: garminconnect.Garmin
    ) -> None:
        payload = {"score": 90, "inputContext": "AFTER_WAKEUP_RESET"}
        with patch.object(garmin, "get_training_readiness", return_value=payload):
            assert garmin.get_morning_training_readiness("2026-03-15") == payload

    def test_get_user_summary_raises_when_response_empty(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value=None):
            with pytest.raises(
                garminconnect.GarminConnectConnectionError,
                match="No data received",
            ):
                garmin.get_user_summary("2026-03-15")

    def test_get_user_summary_raises_on_privacy_protected(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(
            garmin, "connectapi", return_value={"privacyProtected": True}
        ):
            with pytest.raises(
                garminconnect.GarminConnectAuthenticationError,
                match="Authentication error",
            ):
                garmin.get_user_summary("2026-03-15")

    def test_get_body_composition_single_day_uses_start_as_end(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with patch.object(garmin, "connectapi", return_value={"totalAverage": {}}) as mock:
            garmin.get_body_composition("2026-03-15")

        params = mock.call_args.kwargs["params"]
        assert params == {"startDate": "2026-03-15", "endDate": "2026-03-15"}

    def test_get_body_composition_rejects_start_after_end(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="startdate cannot be after enddate"):
            garmin.get_body_composition("2026-03-31", "2026-03-01")

    def test_get_activities_by_date_validates_both_dates(
        self, garmin: garminconnect.Garmin
    ) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            garmin.get_activities_by_date("2026-03-01", "not-a-date")

        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            garmin.get_activities_by_date("bad-start", "2026-03-31")

    def test_get_activities_by_date_paginates_until_empty(
        self, garmin: garminconnect.Garmin
    ) -> None:
        # Simulate two non-empty pages followed by an empty page.
        pages = [
            [{"activityId": i} for i in range(20)],
            [{"activityId": i + 20} for i in range(5)],
            [],
        ]
        with patch.object(garmin, "connectapi", side_effect=pages) as mock:
            result = garmin.get_activities_by_date("2026-03-01", "2026-03-31")

        assert len(result) == 25
        assert mock.call_count == 3
        # Third call should request start=40
        last_params = mock.call_args_list[-1].kwargs["params"]
        assert last_params["start"] == "40"
        assert last_params["startDate"] == "2026-03-01"
        assert last_params["endDate"] == "2026-03-31"
