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

from datetime import date, datetime
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
    ):
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
    ):
        method = getattr(garmin, method_name)
        with pytest.raises(ValueError, match="must be a string"):
            method(20260315)

    def test_rejects_impossible_calendar_date(self, garmin: garminconnect.Garmin):
        # Format matches YYYY-MM-DD regex but Feb 30 is not a real date.
        with pytest.raises(ValueError, match="invalid cdate"):
            garmin.get_hrv_data("2026-02-30")


# ---------------------------------------------------------------------------
# URL construction tests
# ---------------------------------------------------------------------------


class TestUrlConstruction:
    """Verify path / query params are threaded through to connectapi correctly."""

    def test_get_hrv_data_builds_url_with_date(self, garmin: garminconnect.Garmin):
        payload = {"hrvSummary": {"weeklyAvg": 42}}
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_hrv_data("2026-03-15")

        mock.assert_called_once()
        url = mock.call_args[0][0]
        assert url.endswith("/hrv-service/hrv/2026-03-15")
        assert result == payload

    def test_get_training_readiness_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ):
        payload = [{"score": 88, "inputContext": "AFTER_WAKEUP_RESET"}]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_training_readiness("2026-03-15")

        url = mock.call_args[0][0]
        assert "/metrics-service/metrics/trainingreadiness/2026-03-15" in url
        assert result == payload

    def test_get_heart_rate_zones_builds_url(self, garmin: garminconnect.Garmin):
        payload = [{"sport": "RUNNING", "zone1Floor": 120}]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_heart_rate_zones()

        mock.assert_called_once_with("/biometric-service/heartRateZones")
        assert result == payload

    def test_get_power_zones_builds_all_sports_url(self, garmin: garminconnect.Garmin):
        payload = [{"sport": "CYCLING", "zone1Floor": 100}]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_power_zones()

        mock.assert_called_once_with("/biometric-service/powerZones/sports/all")
        assert result == payload

    def test_get_power_zones_for_sport_normalizes_sport_key(
        self, garmin: garminconnect.Garmin
    ):
        payload = {"sport": "CROSS_COUNTRY_SKIING", "zone1Floor": 100}
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_power_zones_for_sport(" cross_country_skiing ")

        mock.assert_called_once_with(
            "/biometric-service/powerZones/sport/CROSS_COUNTRY_SKIING"
        )
        assert result == payload

    @pytest.mark.parametrize("sport", ["", "   ", "cycling/running", 123, None])
    def test_get_power_zones_for_sport_rejects_invalid_keys(
        self, garmin: garminconnect.Garmin, sport: object
    ):
        with pytest.raises(ValueError, match="sport must"):
            garmin.get_power_zones_for_sport(sport)  # type: ignore[arg-type]

    def test_get_stress_data_builds_url_with_date(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "connectapi", return_value={"avgStress": 25}) as mock:
            garmin.get_stress_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/dailyStress/2026-03-15")

    def test_get_max_metrics_repeats_date_in_path(self, garmin: garminconnect.Garmin):
        # get_max_metrics uses the same date twice: /{cdate}/{cdate}
        with patch.object(garmin, "connectapi", return_value={"vo2Max": 55}) as mock:
            garmin.get_max_metrics("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith(
            "/metrics-service/metrics/maxmet/daily/2026-03-15/2026-03-15"
        )

    def test_get_functional_threshold_power_range_builds_cycling_url(
        self, garmin: garminconnect.Garmin
    ):
        payload = [{"series": "cycling", "value": 255}]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_functional_threshold_power_range(
                "2025-06-01", "2025-06-30", sport=" cycling "
            )

        mock.assert_called_once_with(
            "/biometric-service/stats/functionalThresholdPower/range/2025-06-01/2025-06-30"
            "?sport=CYCLING&aggregation=daily&aggregationStrategy=LATEST"
        )
        assert result == payload

    def test_get_max_metrics_range_builds_distinct_date_url(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_max_metrics_range("2026-03-01", "2026-03-15")
        assert mock.call_args[0][0].endswith(
            "/metrics-service/metrics/maxmet/daily/2026-03-01/2026-03-15"
        )

    def test_get_hrv_data_range_builds_distinct_date_url(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value={}) as mock:
            garmin.get_hrv_data_range("2026-03-01", "2026-03-15")
        assert mock.call_args[0][0].endswith(
            "/hrv-service/hrv/daily/2026-03-01/2026-03-15"
        )

    @pytest.mark.parametrize(
        "method_name", ["get_max_metrics_range", "get_hrv_data_range"]
    )
    def test_new_range_methods_reject_inverted_dates(
        self, garmin: garminconnect.Garmin, method_name: str
    ):
        with pytest.raises(ValueError, match="start date cannot be after end date"):
            getattr(garmin, method_name)("2026-03-15", "2026-03-01")

    def test_get_functional_threshold_power_range_accepts_dates(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_functional_threshold_power_range(
                date(2025, 6, 1),
                date(2025, 6, 30),
                sport="RUNNING",
                aggregation="weekly",
            )

        assert "sport=RUNNING&aggregation=weekly" in mock.call_args[0][0]

    @pytest.mark.parametrize(
        ("start_date", "end_date", "sport", "aggregation", "message"),
        [
            ("2025-06-30", "2025-06-01", "CYCLING", "daily", "start_date"),
            ("2025-06-01", "2025-06-30", "cycling/running", "daily", "sport must"),
            ("2025-06-01", "2025-06-30", "CYCLING", "hourly", "aggregation"),
        ],
    )
    def test_get_functional_threshold_power_range_validates_parameters(
        self,
        garmin: garminconnect.Garmin,
        start_date: str,
        end_date: str,
        sport: str,
        aggregation: str,
        message: str,
    ):
        with pytest.raises(ValueError, match=message):
            garmin.get_functional_threshold_power_range(
                start_date, end_date, sport=sport, aggregation=aggregation
            )

    def test_get_lactate_threshold_rejects_inverted_range(
        self, garmin: garminconnect.Garmin
    ):
        with (
            patch.object(garmin, "connectapi") as mock_connectapi,
            patch.object(
                garmin,
                "get_functional_threshold_power_range",
                side_effect=ValueError("start_date must be on or before end_date"),
            ) as mock_ftp,
        ):
            with pytest.raises(
                ValueError, match="start_date must be on or before end_date"
            ):
                garmin.get_lactate_threshold(
                    latest=False,
                    start_date="2025-06-30",
                    end_date="2025-06-01",
                )

        mock_ftp.assert_called_once_with(
            "2025-06-30",
            "2025-06-01",
            sport="RUNNING",
            aggregation="daily",
        )
        mock_connectapi.assert_not_called()

    def test_get_fitnessage_data_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value={"chronologicalAge": 30}
        ) as mock:
            garmin.get_fitnessage_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/fitnessage-service/fitnessage/2026-03-15")

    def test_get_training_status_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value={"status": "productive"}
        ) as mock:
            garmin.get_training_status("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith(
            "/metrics-service/metrics/trainingstatus/aggregated/2026-03-15"
        )

    def test_get_respiration_data_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value={"avgSleepRespirationValue": 13.5}
        ) as mock:
            garmin.get_respiration_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/daily/respiration/2026-03-15")

    def test_get_spo2_data_builds_url_with_date(self, garmin: garminconnect.Garmin):
        with patch.object(
            garmin, "connectapi", return_value={"averageSpO2": 96}
        ) as mock:
            garmin.get_spo2_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/daily/spo2/2026-03-15")

    def test_get_intensity_minutes_builds_url_with_date(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value={"weeklyGoal": 150}
        ) as mock:
            garmin.get_intensity_minutes_data("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/daily/im/2026-03-15")

    def test_get_user_summary_uses_display_name_and_calendar_date(
        self, garmin: garminconnect.Garmin
    ):
        payload = {"totalKilocalories": 2500, "activeKilocalories": 600}
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_user_summary("2026-03-15")

        url = mock.call_args[0][0]
        params = mock.call_args.kwargs["params"]
        assert url.endswith(
            f"/usersummary-service/usersummary/daily/{garmin.display_name}"
        )
        assert params == {"calendarDate": "2026-03-15"}
        assert result == payload

    def test_get_personal_record_uses_display_name(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "connectapi", return_value=[{"id": 1}]) as mock:
            garmin.get_personal_record()

        url = mock.call_args[0][0]
        assert url.endswith(
            f"/personalrecord-service/personalrecord/prs/{garmin.display_name}"
        )

    def test_get_device_settings_builds_url_with_device_id(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value={"alarms": []}) as mock:
            garmin.get_device_settings("3271234567")

        url = mock.call_args[0][0]
        assert url.endswith(
            "/device-service/deviceservice/device-info/settings/3271234567"
        )

    def test_get_gear_builds_url_with_profile_number(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value=[{"gearId": 1}]) as mock:
            garmin.get_gear("98765")

        url = mock.call_args[0][0]
        assert "/gear-service/gear/filterGear" in url
        assert "userProfilePk=98765" in url

    def test_get_weigh_ins_builds_url_with_date_range(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value={"dailyWeightSummaries": []}
        ) as mock:
            garmin.get_weigh_ins("2026-01-01", "2026-01-31")

        url = mock.call_args[0][0]
        assert url.endswith("/weight-service/weight/range/2026-01-01/2026-01-31")
        assert mock.call_args.kwargs["params"] == {"includeAll": True}

    def test_get_weekly_steps_builds_url_with_end_and_weeks(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value=[{"totalSteps": 50000}]
        ) as mock:
            garmin.get_weekly_steps("2026-03-15", weeks=12)

        url = mock.call_args[0][0]
        assert url.endswith("/usersummary-service/stats/steps/weekly/2026-03-15/12")

    def test_get_golf_shot_data_omits_hole_numbers_by_default(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value={"holes": []}) as mock:
            garmin.get_golf_shot_data(12345)

        url = mock.call_args[0][0]
        assert url.endswith("/hole")
        assert mock.call_args.kwargs["params"] is None

    def test_get_golf_shot_data_normalizes_commas_to_dashes(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value={"holes": []}) as mock:
            garmin.get_golf_shot_data(12345, hole_numbers="1,2,3")

        assert mock.call_args.kwargs["params"] == "hole-numbers=1-2-3"

    def test_get_golf_shot_data_accepts_dash_separated_holes(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value={"holes": []}) as mock:
            garmin.get_golf_shot_data(12345, hole_numbers="1-18")

        assert mock.call_args.kwargs["params"] == "hole-numbers=1-18"

    def test_get_golf_shot_data_rejects_out_of_range_hole(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="hole_numbers"):
            garmin.get_golf_shot_data(12345, hole_numbers="19")

    def test_get_golf_shot_data_rejects_injected_query_syntax(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="hole_numbers"):
            garmin.get_golf_shot_data(12345, hole_numbers="1,2&foo=bar")


# ---------------------------------------------------------------------------
# Date-range wellness method tests (max metrics, RHR, calories, sleep, HRV)
# ---------------------------------------------------------------------------


class TestWellnessDailyRangeMethods:
    """URL/param construction and chunking for the *_daily / *_range wellness methods."""

    def test_get_max_metrics_range_builds_url_with_distinct_dates(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value={"vo2Max": 55}) as mock:
            result = garmin.get_max_metrics_range("2026-03-01", "2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith(
            "/metrics-service/metrics/maxmet/daily/2026-03-01/2026-03-15"
        )
        assert result == {"vo2Max": 55}

    def test_get_max_metrics_range_rejects_malformed_date(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            garmin.get_max_metrics_range("not-a-date", "2026-03-15")

    def test_get_hrv_data_range_builds_url_with_distinct_dates(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value={"hrvSummaries": []}
        ) as mock:
            result = garmin.get_hrv_data_range("2026-03-01", "2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/hrv-service/hrv/daily/2026-03-01/2026-03-15")
        assert result == {"hrvSummaries": []}

    def test_get_rhr_daily_builds_url_and_filters_metric_map(
        self, garmin: garminconnect.Garmin
    ):
        payload = {
            "allMetrics": {
                "metricsMap": {
                    "WELLNESS_RESTING_HEART_RATE": [
                        {"calendarDate": "2026-03-01", "value": 52},
                        {"calendarDate": "2026-03-02", "value": None},
                    ]
                }
            }
        }
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_rhr_daily("2026-03-01", "2026-03-02")

        url, kwargs = mock.call_args[0][0], mock.call_args[1]
        assert url.endswith("/userstats-service/wellness/daily/test-display")
        assert kwargs["params"] == {
            "fromDate": "2026-03-01",
            "untilDate": "2026-03-02",
            "metricId": 60,
        }
        # Rows with a null value are dropped.
        assert result == [{"calendarDate": "2026-03-01", "value": 52}]

    def test_get_rhr_daily_rejects_malformed_date(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            garmin.get_rhr_daily("not-a-date", "2026-03-02")

    def test_get_calories_daily_merges_active_and_resting(
        self, garmin: garminconnect.Garmin
    ):
        payload = {
            "allMetrics": {
                "metricsMap": {
                    "WELLNESS_ACTIVE_CALORIES": [
                        {"calendarDate": "2026-03-01", "value": 400},
                    ],
                    "WELLNESS_BMR_CALORIES": [
                        {"calendarDate": "2026-03-01", "value": 1600},
                        {"calendarDate": "2026-03-02", "value": 1500},
                    ],
                }
            }
        }
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_calories_daily("2026-03-01", "2026-03-02")

        kwargs = mock.call_args[1]
        assert kwargs["params"]["metricId"] == [22, 23]
        assert result == [
            {
                "calendarDate": "2026-03-01",
                "active": 400,
                "resting": 1600,
                "total": 2000,
            },
            {
                "calendarDate": "2026-03-02",
                "active": None,
                "resting": 1500,
                "total": 1500,
            },
        ]

    def test_get_sleep_daily_single_chunk_dedupes_and_sorts(
        self, garmin: garminconnect.Garmin
    ):
        payload = {
            "individualStats": [
                {"calendarDate": "2026-03-02", "overallSleepScore": 80},
                {"calendarDate": "2026-03-01", "overallSleepScore": 75},
                {"calendarDate": "2026-03-01", "overallSleepScore": 75},
            ]
        }
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_sleep_daily("2026-03-01", "2026-03-02")

        mock.assert_called_once()
        url = mock.call_args[0][0]
        assert url.endswith("/sleep-service/stats/sleep/daily/2026-03-01/2026-03-02")
        assert [row["calendarDate"] for row in result] == ["2026-03-01", "2026-03-02"]

    def test_get_sleep_daily_chunks_ranges_over_28_days(
        self, garmin: garminconnect.Garmin
    ):
        # 30-day range should be split into two requests (28 days + 2 days).
        with patch.object(
            garmin, "connectapi", return_value={"individualStats": []}
        ) as mock:
            garmin.get_sleep_daily("2026-01-01", "2026-01-30")

        assert mock.call_count == 2
        first_url = mock.call_args_list[0][0][0]
        second_url = mock.call_args_list[1][0][0]
        assert first_url.endswith(
            "/sleep-service/stats/sleep/daily/2026-01-01/2026-01-28"
        )
        assert second_url.endswith(
            "/sleep-service/stats/sleep/daily/2026-01-29/2026-01-30"
        )

    def test_get_sleep_daily_rejects_start_after_end(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="start date cannot be after end date"):
            garmin.get_sleep_daily("2026-03-15", "2026-03-01")

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_max_metrics_range",
            "get_hrv_data_range",
            "get_rhr_daily",
            "get_calories_daily",
            "get_sleep_daily",
        ],
    )
    def test_range_methods_reject_inverted_range_without_api_call(
        self, garmin: garminconnect.Garmin, method_name: str
    ):
        """All *_range/*_daily methods must reject start > end before calling the API."""
        method = getattr(garmin, method_name)
        with (
            patch.object(garmin, "connectapi") as mock,
            pytest.raises(ValueError, match="start date cannot be after end date"),
        ):
            method("2026-03-15", "2026-03-01")
        mock.assert_not_called()


# ---------------------------------------------------------------------------
# Parameter limit tests
# ---------------------------------------------------------------------------


class TestParameterLimits:
    """Enforce MAX_ACTIVITY_LIMIT, MAX_HYDRATION_ML, and related bounds."""

    def test_get_activities_rejects_limit_above_max(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError, match="limit cannot exceed"):
            garmin.get_activities(start=0, limit=garminconnect.MAX_ACTIVITY_LIMIT + 1)

    def test_get_activities_accepts_limit_at_max(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_activities(start=0, limit=garminconnect.MAX_ACTIVITY_LIMIT)

        # Ensure the API was actually called (no exception before dispatch)
        mock.assert_called_once()
        params = mock.call_args.kwargs["params"]
        assert params["limit"] == str(garminconnect.MAX_ACTIVITY_LIMIT)
        assert params["start"] == "0"

    def test_get_activities_rejects_negative_start(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError, match="non-negative"):
            garmin.get_activities(start=-1, limit=10)

    def test_get_activities_rejects_zero_limit(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError, match="positive integer"):
            garmin.get_activities(start=0, limit=0)

    def test_get_activities_passes_activitytype(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_activities(start=0, limit=5, activitytype="running")

        params = mock.call_args.kwargs["params"]
        assert params["activityType"] == "running"

    def test_get_activities_returns_empty_list_when_api_returns_none(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value=None):
            result = garmin.get_activities(start=0, limit=5)

        assert result == []

    def test_add_hydration_data_rejects_excessive_amount(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="unreasonably high"):
            garmin.add_hydration_data(garminconnect.MAX_HYDRATION_ML + 1)

    def test_add_hydration_data_rejects_non_number(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError, match="must be a number"):
            garmin.add_hydration_data("500")  # type: ignore[arg-type]

    def test_add_hydration_data_rejects_excessive_negative_amount(
        self, garmin: garminconnect.Garmin
    ):
        # Negative amounts (subtractions) are allowed but still bounded by abs().
        with pytest.raises(ValueError, match="unreasonably high"):
            garmin.add_hydration_data(-(garminconnect.MAX_HYDRATION_ML + 1))

    def test_get_adhoc_challenges_rejects_negative_start(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="non-negative"):
            garmin.get_adhoc_challenges(start=-1, limit=5)

    def test_get_adhoc_challenges_rejects_zero_limit(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="positive integer"):
            garmin.get_adhoc_challenges(start=0, limit=0)

    def test_get_adhoc_challenges_passes_params_as_strings(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value={"challenges": []}
        ) as mock:
            garmin.get_adhoc_challenges(start=0, limit=10)

        params = mock.call_args.kwargs["params"]
        assert params == {"start": "0", "limit": "10"}

    def test_get_weekly_steps_rejects_non_positive_weeks(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="positive integer"):
            garmin.get_weekly_steps("2026-03-15", weeks=0)


# ---------------------------------------------------------------------------
# Response pass-through / transformation tests
# ---------------------------------------------------------------------------


class TestResponseHandling:
    """Verify methods return payloads unchanged or transform them correctly."""

    def test_get_hrv_data_returns_none_on_204(self, garmin: garminconnect.Garmin):
        # Garmin returns 204 No Content when there is no HRV data for a date.
        with patch.object(garmin, "connectapi", return_value=None):
            assert garmin.get_hrv_data("2026-03-15") is None

    def test_get_devices_returns_list_unchanged(self, garmin: garminconnect.Garmin):
        payload = [
            {"deviceId": 1, "displayName": "Fenix"},
            {"deviceId": 2, "displayName": "Edge"},
        ]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_devices()

        mock.assert_called_once_with("/device-service/deviceregistration/devices")
        assert result == payload

    def test_get_earned_badges_passes_through(self, garmin: garminconnect.Garmin):
        payload = [{"badgeId": 100, "badgeName": "5K"}]
        with patch.object(garmin, "connectapi", return_value=payload) as mock:
            result = garmin.get_earned_badges()

        mock.assert_called_once_with("/badge-service/badge/earned")
        assert result == payload

    def test_get_available_badges_sets_exclusive_badge_flag(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_available_badges()

        mock.assert_called_once()
        params = mock.call_args.kwargs["params"]
        assert params == {"showExclusiveBadge": "true"}

    def test_get_morning_training_readiness_picks_after_wakeup_entry(
        self, garmin: garminconnect.Garmin
    ):
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
    ):
        payload = [
            {"inputContext": None, "score": 75},
            {"inputContext": None, "score": 70},
        ]
        with patch.object(garmin, "get_training_readiness", return_value=payload):
            result = garmin.get_morning_training_readiness("2026-03-15")

        assert result == {"inputContext": None, "score": 75}

    def test_get_morning_training_readiness_returns_none_for_empty_data(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "get_training_readiness", return_value=None):
            assert garmin.get_morning_training_readiness("2026-03-15") is None

        with patch.object(garmin, "get_training_readiness", return_value=[]):
            assert garmin.get_morning_training_readiness("2026-03-15") is None

    def test_get_morning_training_readiness_passes_through_dict(
        self, garmin: garminconnect.Garmin
    ):
        payload = {"score": 90, "inputContext": "AFTER_WAKEUP_RESET"}
        with patch.object(garmin, "get_training_readiness", return_value=payload):
            assert garmin.get_morning_training_readiness("2026-03-15") == payload

    def test_get_user_summary_raises_when_response_empty(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value=None):
            with pytest.raises(
                garminconnect.GarminConnectConnectionError,
                match="No data received",
            ):
                garmin.get_user_summary("2026-03-15")

    def test_get_user_summary_raises_on_privacy_protected(
        self, garmin: garminconnect.Garmin
    ):
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
    ):
        with patch.object(
            garmin, "connectapi", return_value={"totalAverage": {}}
        ) as mock:
            garmin.get_body_composition("2026-03-15")

        params = mock.call_args.kwargs["params"]
        assert params == {"startDate": "2026-03-15", "endDate": "2026-03-15"}

    def test_get_body_composition_rejects_start_after_end(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="startdate cannot be after enddate"):
            garmin.get_body_composition("2026-03-31", "2026-03-01")

    def test_get_activities_by_date_validates_both_dates(
        self, garmin: garminconnect.Garmin
    ):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            garmin.get_activities_by_date("2026-03-01", "not-a-date")

        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            garmin.get_activities_by_date("bad-start", "2026-03-31")

    def test_get_activities_by_date_paginates_until_empty(
        self, garmin: garminconnect.Garmin
    ):
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


# ---------------------------------------------------------------------------
# _run_request: HTTP status -> exception mapping
# ---------------------------------------------------------------------------


class _FakeResp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class TestHttpErrorMapping:
    """A 404 raises GarminConnectNotFoundError; other >=400 stay ConnectionError."""

    def _client(self, monkeypatch, resp):
        g = garminconnect.Garmin()
        c = g.client
        monkeypatch.setattr(c, "get_api_headers", dict)
        monkeypatch.setattr(c._api_session, "request", lambda *a, **k: resp)
        return c

    def test_404_raises_not_found(self, monkeypatch):
        c = self._client(monkeypatch, _FakeResp(404, {"error": "NotFoundException"}))
        with pytest.raises(garminconnect.GarminConnectNotFoundError):
            c._run_request("DELETE", "workout-service/workout/1")

    def test_not_found_is_backwards_compatible(self, monkeypatch):
        # Existing handlers catching GarminConnectConnectionError must still work.
        c = self._client(monkeypatch, _FakeResp(404, {"error": "NotFoundException"}))
        with pytest.raises(garminconnect.GarminConnectConnectionError):
            c._run_request("GET", "workout-service/workout/1")

    def test_500_stays_connection_error_not_not_found(self, monkeypatch):
        c = self._client(monkeypatch, _FakeResp(500, {"message": "boom"}))
        with pytest.raises(garminconnect.GarminConnectConnectionError) as exc_info:
            c._run_request("GET", "x")
        assert not isinstance(exc_info.value, garminconnect.GarminConnectNotFoundError)

    def _garmin(self, monkeypatch, resp):
        g = garminconnect.Garmin()
        monkeypatch.setattr(g.client, "get_api_headers", dict)
        monkeypatch.setattr(g.client._api_session, "request", lambda *a, **k: resp)
        monkeypatch.setattr(type(g.client), "is_authenticated", False)
        return g

    def test_connectapi_404_raises_not_found(self, monkeypatch):
        # Garmin.connectapi is wrapped by _handle_api_errors, which must not
        # downgrade GarminConnectNotFoundError back to a plain
        # GarminConnectConnectionError the way it does for other 4xx codes.
        g = self._garmin(monkeypatch, _FakeResp(404, {"error": "NotFoundException"}))
        with pytest.raises(garminconnect.GarminConnectNotFoundError):
            g.connectapi("some/path")

    def test_connectapi_400_stays_connection_error_not_not_found(self, monkeypatch):
        g = self._garmin(monkeypatch, _FakeResp(400, {"message": "bad request"}))
        with pytest.raises(garminconnect.GarminConnectConnectionError) as exc_info:
            g.connectapi("some/path")
        assert not isinstance(exc_info.value, garminconnect.GarminConnectNotFoundError)


# ---------------------------------------------------------------------------
# update_workout (in-place PUT)
# ---------------------------------------------------------------------------


class TestUpdateWorkout:
    """``update_workout`` PUTs the full workout to /workout-service/workout/<id>."""

    def test_puts_to_workout_url_with_injected_id(self, garmin: garminconnect.Garmin):
        workout = {"workoutName": "Edited", "sportType": {"sportTypeId": 1}}
        with patch.object(garmin, "client") as client:
            client.put.return_value = {"workoutId": 123, "workoutName": "Edited"}
            result = garmin.update_workout(123, workout)

        args, kwargs = client.put.call_args
        assert args[0] == "connectapi"
        assert args[1] == "/workout-service/workout/123"
        assert kwargs["api"] is True
        assert kwargs["json"]["workoutId"] == 123
        assert kwargs["json"]["workoutName"] == "Edited"
        assert result == {"workoutId": 123, "workoutName": "Edited"}

    def test_injected_id_overrides_stray_workout_id(self, garmin: garminconnect.Garmin):
        workout = {"workoutId": 999, "workoutName": "Edited"}
        with patch.object(garmin, "client") as client:
            garmin.update_workout(123, workout)

        assert client.put.call_args.kwargs["json"]["workoutId"] == 123
        # caller dict is not mutated
        assert workout["workoutId"] == 999

    def test_accepts_json_string(self, garmin: garminconnect.Garmin):
        import json as _json

        with patch.object(garmin, "client") as client:
            garmin.update_workout(123, _json.dumps({"workoutName": "Edited"}))

        assert client.put.call_args.kwargs["json"]["workoutId"] == 123

    def test_rejects_non_positive_id(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "client") as client:
            with pytest.raises(ValueError, match="positive integer"):
                garmin.update_workout(0, {"workoutName": "Edited"})
        client.put.assert_not_called()

    def test_rejects_non_dict_payload(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "client") as client:
            with pytest.raises(ValueError, match="must be a JSON object"):
                garmin.update_workout(123, [1, 2, 3])
        client.put.assert_not_called()

    def test_rejects_invalid_json_string(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "client") as client:
            with pytest.raises(ValueError, match="invalid workout_json string"):
                garmin.update_workout(123, "{not json")
        client.put.assert_not_called()


# ---------------------------------------------------------------------------
# push_workout_to_device
# ---------------------------------------------------------------------------


class TestPushWorkoutToDevice:
    """``push_workout_to_device`` POSTs a device message for a workout."""

    def test_pushes_with_explicit_ids(self, garmin: garminconnect.Garmin):
        with (
            patch.object(garmin, "get_workout_by_id") as get_workout_by_id,
            patch.object(garmin, "client") as client,
        ):
            get_workout_by_id.return_value = {"workoutName": "Easy Run"}
            client.post.return_value = {"result": "ok"}

            result = garmin.push_workout_to_device(123, 456)

        get_workout_by_id.assert_called_once_with(123)
        args, kwargs = client.post.call_args
        assert args[0] == "connectapi"
        assert args[1] == "/device-service/devicemessage/messages"
        assert kwargs["api"] is True
        payload = kwargs["json"][0]
        assert payload["deviceId"] == 456
        assert payload["metaDataId"] == 123
        assert payload["messageUrl"] == "workout-service/workout/FIT/123"
        assert payload["messageName"] == "Easy Run"
        assert result == {"result": "ok"}

    def test_defaults_to_last_used_device(self, garmin: garminconnect.Garmin):
        with (
            patch.object(garmin, "get_device_last_used") as get_device_last_used,
            patch.object(garmin, "get_workout_by_id") as get_workout_by_id,
            patch.object(garmin, "client") as client,
        ):
            get_device_last_used.return_value = {"userDeviceId": 789}
            get_workout_by_id.return_value = {"workoutName": "Easy Run"}

            garmin.push_workout_to_device(workout_id=123)

        get_device_last_used.assert_called_once()
        assert client.post.call_args.kwargs["json"][0]["deviceId"] == 789

    def test_defaults_to_last_workout(self, garmin: garminconnect.Garmin):
        with (
            patch.object(garmin, "get_workouts") as get_workouts,
            patch.object(garmin, "get_workout_by_id") as get_workout_by_id,
            patch.object(garmin, "client") as client,
        ):
            get_workouts.return_value = [{"workoutId": 555, "workoutName": "Last"}]
            get_workout_by_id.return_value = {"workoutName": "Last"}

            garmin.push_workout_to_device(device_id=456)

        get_workouts.assert_called_once_with(start=0, limit=1)
        get_workout_by_id.assert_called_once_with(555)
        assert client.post.call_args.kwargs["json"][0]["metaDataId"] == 555

    def test_raises_when_no_workouts_found(self, garmin: garminconnect.Garmin):
        with (
            patch.object(garmin, "get_workouts") as get_workouts,
            patch.object(garmin, "client") as client,
        ):
            get_workouts.return_value = []
            with pytest.raises(ValueError, match="No workouts found"):
                garmin.push_workout_to_device(device_id=456)
        client.post.assert_not_called()

    def test_rejects_non_positive_workout_id(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "client") as client:
            with pytest.raises(ValueError, match="positive integer"):
                garmin.push_workout_to_device(workout_id=0, device_id=456)
        client.post.assert_not_called()

    def test_rejects_non_positive_device_id(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "client") as client:
            with pytest.raises(ValueError, match="positive integer"):
                garmin.push_workout_to_device(workout_id=123, device_id=0)
        client.post.assert_not_called()
