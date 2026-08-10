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

import base64
import io
import json
import logging
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

import garminconnect
from garminconnect import client as client_mod

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
# Client construction / domain validation
# ---------------------------------------------------------------------------


class TestClientConstruction:
    """Constructor should reject unsafe configuration values."""

    def test_rejects_arbitrary_domain(self):
        """Arbitrary domains would redirect credentials to attacker-controlled hosts."""
        with pytest.raises(ValueError, match="Invalid domain"):
            client_mod.Client(domain="evil.com")

    @pytest.mark.parametrize("domain", ["garmin.com", "garmin.cn"])
    def test_accepts_official_domains(self, domain: str):
        c = client_mod.Client(domain=domain, verify_login=False)
        assert c.domain == domain
        assert c._sso == f"https://sso.{domain}"


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

    def test_get_functional_threshold_power_range_builds_url_with_weekly_aggregation(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(garmin, "connectapi", return_value=[]) as mock:
            garmin.get_functional_threshold_power_range(
                "2025-06-01",
                "2025-06-30",
                sport="RUNNING",
                aggregation="weekly",
            )

        assert "sport=RUNNING&aggregation=weekly" in mock.call_args[0][0]

    @pytest.mark.parametrize(
        ("start", "end", "sport", "aggregation", "message"),
        [
            ("2025-06-30", "2025-06-01", "CYCLING", "daily", "start date cannot be after end date"),
            ("2025-06-01", "2025-06-30", "cycling/running", "daily", "sport must"),
            ("2025-06-01", "2025-06-30", "CYCLING", "hourly", "aggregation"),
        ],
    )
    def test_get_functional_threshold_power_range_validates_parameters(
        self,
        garmin: garminconnect.Garmin,
        start: str,
        end: str,
        sport: str,
        aggregation: str,
        message: str,
    ):
        with pytest.raises(ValueError, match=message):
            garmin.get_functional_threshold_power_range(
                start, end, sport=sport, aggregation=aggregation
            )

    def test_get_lactate_threshold_rejects_inverted_range(
        self, garmin: garminconnect.Garmin
    ):
        with (
            patch.object(garmin, "connectapi") as mock_connectapi,
            patch.object(
                garmin,
                "get_functional_threshold_power_range",
                side_effect=ValueError("start date cannot be after end date"),
            ) as mock_ftp,
            pytest.raises(ValueError, match="start date cannot be after end date"),
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

    def test_get_spo2_data_normalizes_last_seven_days_avg(
        self, garmin: garminconnect.Garmin
    ):
        payload = {"lastSevenDaysAvgSpO2": "94.42857142857143"}
        with patch.object(garmin, "connectapi", return_value=payload):
            result = garmin.get_spo2_data("2026-03-15")

        assert result["lastSevenDaysAvgSpO2"] == 94.42857142857143
        assert isinstance(result["lastSevenDaysAvgSpO2"], float)

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
        assert url.endswith("/gear-service/gear/filterGear")
        assert mock.call_args.kwargs["params"] == {"userProfilePk": "98765"}

    def test_get_lactate_threshold_latest_passes_power_sport_in_params(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin,
            "connectapi",
            side_effect=[
                [{"value": 250}],
                [
                    {
                        "speed": 12,
                        "heartRate": 160,
                        "userProfilePK": 12345,
                        "version": 1,
                        "calendarDate": "2026-03-15",
                        "sequence": 1,
                    }
                ],
            ],
        ) as mock:
            garmin.get_lactate_threshold(latest=True)

        assert mock.call_count == 2
        power_call = mock.call_args_list[0]
        assert "/powerToWeight/latest/" in power_call[0][0]
        assert "?sport" not in power_call[0][0]
        assert power_call.kwargs["params"] == {"sport": "Running"}

    def test_get_all_day_events_builds_url_with_params(
        self, garmin: garminconnect.Garmin
    ):
        with patch.object(
            garmin, "connectapi", return_value={"calendarEvents": []}
        ) as mock:
            garmin.get_all_day_events("2026-03-15")

        url = mock.call_args[0][0]
        assert url.endswith("/wellness-service/wellness/dailyEvents")
        assert mock.call_args.kwargs["params"] == {"calendarDate": "2026-03-15"}

    def test_require_display_name_url_encodes_special_chars(
        self, garmin: garminconnect.Garmin
    ):
        garmin.display_name = "../admin?user#x"
        encoded = garmin._require_display_name()
        assert "../" not in encoded
        assert "%2F" in encoded
        assert "%3F" in encoded
        assert "%23" in encoded

    def test_require_display_name_raises_when_not_set(
        self, garmin: garminconnect.Garmin
    ):
        garmin.display_name = None
        with pytest.raises(
            garminconnect.GarminConnectConnectionError, match="Display name is not set"
        ):
            garmin._require_display_name()

    @pytest.mark.parametrize(
        "method_name,args,expected_suffix",
        [
            ("get_heart_rates", ("2026-03-15",), "/wellness-service/wellness/dailyHeartRate"),
            ("get_sleep_data", ("2026-03-15",), "/wellness-service/wellness/dailySleepData"),
        ],
    )
    def test_display_name_is_url_encoded_in_path(
        self,
        garmin: garminconnect.Garmin,
        method_name: str,
        args: tuple[Any, ...],
        expected_suffix: str,
    ):
        garmin.display_name = "name with space"
        with patch.object(garmin, "connectapi", return_value={}) as mock:
            getattr(garmin, method_name)(*args)

        url = mock.call_args[0][0]
        assert url.endswith(f"{expected_suffix}/name%20with%20space")

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
            garmin.get_golf_shot_data(12345, hole_numbers="1-9")

        assert mock.call_args.kwargs["params"] == "hole-numbers=1-9"

    def test_get_golf_shot_data_falls_back_to_all_holes_for_double_digits(
        self, garmin: garminconnect.Garmin
    ):
        """Garmin's endpoint drops double-digit holes from hole-numbers queries.

        The only reliable way to retrieve holes 10-18 is to omit the parameter
        and receive every hole.
        """
        with patch.object(garmin, "connectapi", return_value={"holes": []}) as mock:
            garmin.get_golf_shot_data(12345, hole_numbers="4-10-11-13")

        assert mock.call_args.kwargs["params"] is None

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
# Credential lifecycle
# ---------------------------------------------------------------------------


class TestCredentialLifecycle:
    """Plaintext credentials should not outlive successful authentication."""

    def test_password_cleared_after_successful_credential_login(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        with (
            patch.object(g.client, "login", return_value=(None, None)),
            patch.object(g, "_load_profile_and_settings"),
        ):
            g.login()

        assert g.password is None
        assert g.username == "user@example.com"

    def test_password_cleared_after_successful_tokenstore_login(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        g.client.di_refresh_token = "refresh"
        with (
            patch.object(g.client, "load") as mock_load,
            patch.object(g.client, "_token_expires_soon", return_value=False),
            patch.object(g, "_load_profile_and_settings"),
        ):
            g.login("/tmp/tokens")

        mock_load.assert_called_once()
        assert g.password is None

    def test_password_retained_when_login_returns_for_mfa(self):
        g = garminconnect.Garmin(
            "user@example.com", "secret", return_on_mfa=True
        )
        with patch.object(
            g.client, "login", return_value=("mfa_status", "legacy_token")
        ):
            status, token = g.login()

        assert status == "mfa_status"
        assert g.password == "secret"


# ---------------------------------------------------------------------------
# MFA resume_login
# ---------------------------------------------------------------------------


class TestResumeLogin:
    """Two-step MFA resume_login must verify the token and propagate failures."""

    def test_client_resume_login_verifies_token_when_verify_login_enabled(self):
        c = client_mod.Client(verify_login=True)
        with (
            patch.object(c, "_complete_mfa") as mock_complete,
            patch.object(c, "_verify_token", return_value=True) as mock_verify,
            patch.object(c, "_clear_auth_state") as mock_clear,
        ):
            assert c.resume_login({}, "123456") == (None, None)

        mock_complete.assert_called_once_with("123456")
        mock_verify.assert_called_once()
        mock_clear.assert_not_called()

    def test_client_resume_login_clears_auth_when_token_rejected(self):
        c = client_mod.Client(verify_login=True)
        with (
            patch.object(c, "_complete_mfa"),
            patch.object(c, "_verify_token", return_value=False),
            patch.object(c, "_clear_auth_state") as mock_clear,
            pytest.raises(garminconnect.GarminConnectConnectionError, match="token rejected by API tier after MFA"),
        ):
            c.resume_login({}, "123456")

        mock_clear.assert_called_once()

    def test_client_resume_login_skips_verify_when_verify_login_disabled(self):
        c = client_mod.Client(verify_login=False)
        with (
            patch.object(c, "_complete_mfa") as mock_complete,
            patch.object(c, "_verify_token") as mock_verify,
        ):
            assert c.resume_login({}, "123456") == (None, None)

        mock_complete.assert_called_once_with("123456")
        mock_verify.assert_not_called()

    def test_garmin_resume_login_propagates_profile_load_failure(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        with (
            patch.object(g.client, "resume_login", return_value=(None, None)),
            patch.object(
                g,
                "_load_profile_and_settings",
                side_effect=garminconnect.GarminConnectAuthenticationError(
                    "bad token"
                ),
            ) as mock_load,
            pytest.raises(
                garminconnect.GarminConnectAuthenticationError, match="bad token"
            ),
        ):
            g.resume_login({}, "123456")

        mock_load.assert_called_once()


# ---------------------------------------------------------------------------
# MFA resolution in login()
# ---------------------------------------------------------------------------


class TestLoginMFA:
    """A strategy that raises _MFARequired must be resolved immediately.

    The historical "shelving" fallback for uncertain widget-MFA delivery was
    dead code (the trigger flag was never set in production); these tests cover
    the actual current behavior.
    """

    def test_mfa_resolved_immediately_with_prompt_mfa(self):
        c = client_mod.Client(verify_login=False)

        def mfa_strategy(_email, _password):
            c._mfa_flow = "widget"
            raise client_mod._MFARequired()

        def fake_complete(code):
            c.di_token = f"{c._mfa_flow}-{code}"

        with (
            patch.object(c, "_widget_web_login", side_effect=mfa_strategy),
            patch.object(c, "_complete_mfa", side_effect=fake_complete),
        ):
            c.login("e@x.com", "pw", prompt_mfa=lambda: "654321")

        assert c.di_token == "widget-654321"  # noqa: S105

    def test_mfa_returns_immediately_with_return_on_mfa(self):
        c = client_mod.Client(verify_login=False)

        def mfa_strategy(_email, _password):
            raise client_mod._MFARequired()

        with patch.object(c, "_widget_web_login", side_effect=mfa_strategy):
            status, _ = c.login("e@x.com", "pw", return_on_mfa=True)

        assert status == "needs_mfa"

    def test_mfa_without_prompt_raises(self):
        c = client_mod.Client(verify_login=False)

        def mfa_strategy(_email, _password):
            raise client_mod._MFARequired()

        with (
            patch.object(c, "_widget_web_login", side_effect=mfa_strategy),
            pytest.raises(
                garminconnect.GarminConnectAuthenticationError,
                match="MFA Required but no prompt_mfa mechanism supplied",
            ),
        ):
            c.login("e@x.com", "pw")

    def test_mfa_token_rejection_falls_through_to_next_strategy(self):
        c = client_mod.Client(verify_login=True)

        def mfa_strategy(_email, _password):
            c._mfa_flow = "widget"
            raise client_mod._MFARequired()

        def portal_strategy(_email, _password):
            c.di_token = "portal-token"  # noqa: S105

        with (
            patch.object(c, "_widget_web_login", side_effect=mfa_strategy),
            patch.object(c, "_portal_web_login_cffi", side_effect=portal_strategy),
            patch.object(c, "_complete_mfa"),
            patch.object(c, "_verify_token", side_effect=[False, True]),
            patch.object(c, "_clear_auth_state") as mock_clear,
        ):
            c.login("e@x.com", "pw", prompt_mfa=lambda: "000000")

        assert c.di_token == "portal-token"  # noqa: S105
        mock_clear.assert_called_once()

    def test_return_on_mfa_sets_pending_flag(self):
        c = client_mod.Client(verify_login=False)

        def mfa_strategy(_email, _password):
            c._mfa_flow = "widget"
            raise client_mod._MFARequired()

        with patch.object(c, "_widget_web_login", side_effect=mfa_strategy):
            status, _ = c.login("e@x.com", "pw", return_on_mfa=True)

        assert status == "needs_mfa"
        assert c._mfa_pending is True

    def test_login_rejects_interleaved_mfa_attempt(self):
        """A second login while MFA is pending must be rejected to avoid
        overwriting the first attempt's MFA state.
        """
        c = client_mod.Client(verify_login=False)

        def mfa_strategy(_email, _password):
            c._mfa_flow = "widget"
            raise client_mod._MFARequired()

        with patch.object(c, "_widget_web_login", side_effect=mfa_strategy):
            c.login("a@x.com", "pw", return_on_mfa=True)

        with (
            patch.object(c, "_widget_web_login", side_effect=mfa_strategy),
            pytest.raises(
                garminconnect.GarminConnectAuthenticationError,
                match="MFA login already in progress",
            ),
        ):
            c.login("b@x.com", "pw", return_on_mfa=True)

    def test_resume_login_clears_pending_flag(self):
        c = client_mod.Client(verify_login=False)

        def mfa_strategy(_email, _password):
            c._mfa_flow = "widget"
            raise client_mod._MFARequired()

        def fake_complete(code):
            c.di_token = f"widget-{code}"  # noqa: S105

        with patch.object(c, "_widget_web_login", side_effect=mfa_strategy):
            c.login("e@x.com", "pw", return_on_mfa=True)

        assert c._mfa_pending is True

        with patch.object(c, "_complete_mfa", side_effect=fake_complete):
            c.resume_login({}, "654321")

        assert c._mfa_pending is False
        assert c._mfa_flow is None


# ---------------------------------------------------------------------------
# Token refresh concurrency
# ---------------------------------------------------------------------------


class TestTokenRefreshConcurrency:
    """Token refresh and state mutation must be serialized across threads."""

    def test_refresh_session_blocks_on_token_lock(self):
        """`_refresh_session()` must acquire the instance token lock; a second
        thread should block while the lock is held elsewhere."""
        c = client_mod.Client(verify_login=False)
        c.di_token = "token"
        c.di_refresh_token = "refresh"
        c.di_client_id = "client"

        hold_lock = threading.Event()
        release_lock = threading.Event()

        def lock_holder():
            with c._token_lock:
                hold_lock.set()
                release_lock.wait(timeout=5)

        t1 = threading.Thread(target=lock_holder)
        t1.start()
        hold_lock.wait(timeout=1)

        t2 = threading.Thread(target=c._refresh_session)
        t2.start()
        t2.join(timeout=0.3)
        assert t2.is_alive(), "_refresh_session did not block on token lock"

        release_lock.set()
        t1.join(timeout=5)
        t2.join(timeout=5)


# ---------------------------------------------------------------------------
# Sanitized login error messages
# ---------------------------------------------------------------------------


class TestSanitizedLoginErrors:
    """Authentication error messages must not embed full server responses
    containing session metadata such as serviceTicketId, customerGuid, or
    internal endpoint URLs.
    """

    @staticmethod
    def _json_response(status_code, json_data):
        resp = type(
            "Resp",
            (),
            {
                "status_code": status_code,
                "ok": 200 <= status_code < 400,
                "text": str(json_data),
                "json": lambda self: json_data,
            },
        )()
        return resp

    def test_mobile_login_error_does_not_embed_full_response(self):
        sensitive = {
            "responseStatus": {"type": "LOCKED"},
            "serviceTicketId": "ST-LEAK-123",
            "customerGuid": "guid-123",
            "serviceUrl": "https://internal-sso.garmin.com/secret",
        }
        sess = type("Sess", (), {"post": lambda *a, **k: self._json_response(200, sensitive)})()
        c = client_mod.Client(verify_login=False)
        with pytest.raises(
            garminconnect.GarminConnectConnectionError, match="responseStatus=LOCKED"
        ) as exc:
            c._do_mobile_login(sess, "e@x.com", "pw")

        msg = str(exc.value)
        assert "ST-LEAK-123" not in msg
        assert "guid-123" not in msg
        assert "internal-sso" not in msg

    def test_portal_login_error_does_not_embed_full_response(self):
        sensitive = {
            "responseStatus": {"type": "MAINTENANCE"},
            "serviceTicketId": "ST-LEAK-456",
            "customerGuid": "guid-456",
            "serviceUrl": "https://internal-sso.garmin.com/secret",
        }
        sess = type(
            "Sess",
            (),
            {
                "get": lambda *a, **k: self._json_response(200, {}),
                "post": lambda *a, **k: self._json_response(200, sensitive),
            },
        )()
        c = client_mod.Client(verify_login=False)
        with (
            patch.object(client_mod.time, "sleep"),
            pytest.raises(
                garminconnect.GarminConnectConnectionError,
                match="responseStatus=MAINTENANCE",
            ) as exc,
        ):
            c._do_portal_web_login(sess, "e@x.com", "pw")

        msg = str(exc.value)
        assert "ST-LEAK-456" not in msg
        assert "guid-456" not in msg
        assert "internal-sso" not in msg

    def test_mfa_failure_does_not_embed_full_response(self):
        sensitive = {
            "responseStatus": {"type": "INVALID_OTP"},
            "serviceTicketId": "ST-MFA-LEAK",
            "customerGuid": "mfa-guid",
        }
        sess = type(
            "Sess",
            (),
            {
                "post": lambda *a, **k: self._json_response(200, sensitive),
                "cookies": type("Jar", (), {"jar": []})(),
            },
        )()
        c = client_mod.Client(verify_login=False)
        c._mfa_flow = "portal"
        c._mfa_session = sess
        c._mfa_login_params = {}
        c._mfa_post_headers = {}
        c._mfa_service_url = c._portal_service_url
        with pytest.raises(
            garminconnect.GarminConnectAuthenticationError, match="INVALID_OTP"
        ) as exc:
            c._complete_mfa("000000")

        msg = str(exc.value)
        assert "ST-MFA-LEAK" not in msg
        assert "mfa-guid" not in msg


# ---------------------------------------------------------------------------
# Logout cleanup
# ---------------------------------------------------------------------------


class TestLogout:
    """logout() must clear session cookies and user-facing state."""

    def test_logout_clears_client_auth_tokens_and_cookies(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        g.client.di_token = "token"
        g.client.cs.cookies.set("CASTGT", "ticket", domain="garmin.com")

        g.logout()

        assert g.client.di_token is None
        assert len(g.client.cs.cookies) == 0

    def test_logout_clears_mfa_state(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        g.client._mfa_session = object()
        g.client._mfa_login_params = {"x": 1}
        g.client._widget_last_resp = object()

        g.logout()

        assert g.client._mfa_session is None
        assert g.client._mfa_login_params is None
        assert g.client._widget_last_resp is None

    def test_logout_clears_garmin_wrapper_state(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        g.display_name = "test-user"
        g.full_name = "Test User"
        g.unit_system = "metric"

        g.logout()

        assert g.username is None
        assert g.password is None
        assert g.display_name is None
        assert g.full_name is None
        assert g.unit_system is None

    def test_logout_skips_unlinking_inline_token_json(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        token_json = '{"di_token": "x"}'
        with patch.object(Path, "unlink") as mock_unlink:
            g.logout(token_json)
        mock_unlink.assert_not_called()

    def test_logout_does_not_delete_through_symlinked_directory(
        self, tmp_path, make_symlink
    ):
        """A symlinked tokenstore directory must not let logout() delete a file
        outside the intended location.
        """
        target_dir = tmp_path / "attacker_dir"
        target_dir.mkdir()
        victim_file = target_dir / "garmin_tokens.json"
        victim_file.write_text('{"di_token": "x"}')
        link_dir = tmp_path / "garminconnect"
        make_symlink(target_dir, link_dir)

        g = garminconnect.Garmin("user@example.com", "secret")
        g.logout(str(link_dir))

        assert victim_file.exists()


# ---------------------------------------------------------------------------
# Token file path
# ---------------------------------------------------------------------------


class TestTokenFilePath:
    """token_file_path must stay within the current user's scope."""

    def test_bare_tilde_expands_to_current_user(self):
        path = client_mod.token_file_path("~/.garminconnect")
        assert path.name == "garmin_tokens.json"

    def test_rejects_other_user_home_expansion(self):
        with pytest.raises(ValueError, match="another user's home"):
            client_mod.token_file_path("~otheruser/.garminconnect")

    def test_rejects_other_user_home_at_root(self):
        with pytest.raises(ValueError, match="another user's home"):
            client_mod.token_file_path("~root")

    def test_absolute_path_outside_home_still_allowed(self):
        # Absolute paths are explicit configuration, not a cross-user trick.
        path = client_mod.token_file_path("/var/lib/garmin/tokens.json")
        assert path == Path("/var/lib/garmin/tokens.json")

    def test_rejects_symlinked_directory_tokenstore(self, tmp_path, make_symlink):
        target_dir = tmp_path / "attacker_dir"
        target_dir.mkdir()
        link_dir = tmp_path / "garminconnect"
        make_symlink(target_dir, link_dir)

        with pytest.raises(ValueError, match="must not be a symlink"):
            client_mod.token_file_path(str(link_dir))

    def test_rejects_symlinked_parent_of_json_tokenstore(self, tmp_path, make_symlink):
        target_dir = tmp_path / "attacker_dir"
        target_dir.mkdir()
        link_dir = tmp_path / "garminconnect"
        make_symlink(target_dir, link_dir)

        with pytest.raises(ValueError, match="must not be a symlink"):
            client_mod.token_file_path(str(link_dir / "garmin_tokens.json"))


# ---------------------------------------------------------------------------
# Tokenstore path-vs-data detection
# ---------------------------------------------------------------------------


class TestTokenstoreDetection:
    """tokenstore may be a path or inline JSON; detection must not rely on length."""

    @contextmanager
    def _tokenstore_mocks(self, g: garminconnect.Garmin):
        with (
            patch.object(g.client, "load") as mock_load,
            patch.object(g.client, "loads") as mock_loads,
            patch.object(g.client, "_token_expires_soon", return_value=False),
            patch.object(g, "_load_profile_and_settings"),
        ):
            yield mock_load, mock_loads

    def test_long_path_uses_file_load_not_json_loads(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        long_path = "/home/" + "a" * 600 + "/tokens"
        with self._tokenstore_mocks(g) as (mock_load, mock_loads):
            g.login(tokenstore=long_path)

        mock_load.assert_called_once()
        mock_loads.assert_not_called()

    def test_short_json_uses_inline_loads(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        token_json = '{"di_token": "x"}'
        with self._tokenstore_mocks(g) as (mock_load, mock_loads):
            g.login(tokenstore=token_json)

        mock_loads.assert_called_once()
        mock_load.assert_not_called()

    def test_long_json_uses_inline_loads(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        token_json = '{"di_token": "' + "A" * 600 + '"}'
        with self._tokenstore_mocks(g) as (mock_load, mock_loads):
            g.login(tokenstore=token_json)

        mock_loads.assert_called_once()
        mock_load.assert_not_called()

    def test_json_array_uses_inline_loads(self):
        g = garminconnect.Garmin("user@example.com", "secret")
        token_json = '[{"di_token": "x"}]'
        with self._tokenstore_mocks(g) as (mock_load, mock_loads):
            g.login(tokenstore=token_json)

        mock_loads.assert_called_once()
        mock_load.assert_not_called()

    def test_failed_inline_token_load_does_not_log_refresh_token(self):
        """A malformed inline token blob must not be written to the debug log."""
        g = garminconnect.Garmin("user@example.com", "secret")
        canary = "REFRESH-TOKEN-CANARY-9d1f7c2a"
        blob = '{"padding": "' + "P" * 559 + '", "refresh_token": "' + canary + '"}'

        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("garminconnect")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        try:
            with self._tokenstore_mocks(g) as (mock_load, mock_loads):
                mock_loads.side_effect = Exception("parse error")
                with patch.object(
                    g.client, "login", side_effect=Exception("skip login")
                ):
                    with pytest.raises(Exception, match="skip login"):
                        g.login(tokenstore=blob)
        finally:
            logger.removeHandler(handler)

        logged = log_stream.getvalue()
        assert "Failed to cleanly load tokens" in logged
        assert canary not in logged
        assert blob not in logged


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

    def test_get_activities_by_date_pagination_is_capped(
        self, garmin: garminconnect.Garmin
    ):
        # A hostile server that never returns an empty page must not be able
        # to loop the client forever.
        with (
            patch.object(garmin, "connectapi", return_value=[{}]) as mock,
            pytest.raises(
                garminconnect.GarminConnectConnectionError,
                match="Pagination exceeded",
            ),
        ):
            garmin.get_activities_by_date("2026-03-01", "2026-03-31")

        assert mock.call_count == garminconnect.MAX_PAGINATED_REQUESTS

    def test_get_goals_pagination_is_capped(self, garmin: garminconnect.Garmin):
        with (
            patch.object(garmin, "connectapi", return_value=[{}]) as mock,
            pytest.raises(
                garminconnect.GarminConnectConnectionError,
                match="Pagination exceeded",
            ),
        ):
            garmin.get_goals()

        assert mock.call_count == garminconnect.MAX_PAGINATED_REQUESTS

    def test_get_goals_paginates_until_empty(self, garmin: garminconnect.Garmin):
        # Normal termination: two non-empty pages followed by an empty page
        # must complete successfully and advance start by limit each page.
        # (params is mutated between calls, so snapshot start at call time.)
        starts: list[str] = []
        pages = [
            [{"goalId": i} for i in range(30)],
            [{"goalId": i + 30} for i in range(10)],
            [],
        ]

        def fake_connectapi(url, params=None):
            starts.append(params["start"])
            return pages.pop(0)

        with patch.object(garmin, "connectapi", side_effect=fake_connectapi) as mock:
            result = garmin.get_goals()

        assert len(result) == 40
        assert mock.call_count == 3
        assert starts == ["0", "30", "60"]


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

    def test_error_message_includes_safe_message_field(self, monkeypatch):
        c = self._client(monkeypatch, _FakeResp(500, {"message": "server error"}))
        with pytest.raises(garminconnect.GarminConnectConnectionError) as exc_info:
            c._run_request("GET", "x")
        assert "server error" in str(exc_info.value)

    def test_error_message_omits_raw_response_body(self, monkeypatch):
        body = "<html><body>internal hostname: db01.garmin.internal</body></html>"
        c = self._client(monkeypatch, _FakeResp(500, body))
        with pytest.raises(garminconnect.GarminConnectConnectionError) as exc_info:
            c._run_request("GET", "x")
        assert "db01.garmin.internal" not in str(exc_info.value)
        assert "API Error 500" in str(exc_info.value)

    @pytest.mark.parametrize(
        "bad_path",
        [
            "foo/../bar",
            "foo?bar=1",
            "foo#fragment",
        ],
    )
    def test_rejects_path_with_traversal_or_query(
        self, monkeypatch, bad_path: str
    ):
        c = self._client(monkeypatch, _FakeResp(200, {}))
        with pytest.raises(ValueError, match="Invalid API path"):
            c._run_request("GET", bad_path)


# ---------------------------------------------------------------------------
# Error-message sanitization
# ---------------------------------------------------------------------------


class TestErrorMessageSanitization:
    """Exception messages must not embed raw server responses or token content."""

    def test_di_refresh_error_omits_response_body(self):
        c = client_mod.Client(verify_login=False)
        c.di_refresh_token = "refresh"
        c.di_client_id = "client"

        class FakeResp:
            ok = False
            status_code = 500
            text = "internal stack trace: db01.garmin.internal"

        with patch.object(c, "_http_post", return_value=FakeResp()):
            with pytest.raises(
                garminconnect.GarminConnectAuthenticationError
            ) as exc_info:
                c._refresh_di_token()

        assert "db01.garmin.internal" not in str(exc_info.value)
        assert "500" in str(exc_info.value)

    def test_loads_error_omits_token_content(self):
        c = client_mod.Client(verify_login=False)
        with pytest.raises(garminconnect.GarminConnectConnectionError) as exc_info:
            c.loads('{"di_token": "SECRET_TOKEN_VALUE"')
        assert "SECRET_TOKEN_VALUE" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# JWT handling
# ---------------------------------------------------------------------------


def _b64url(data: dict[str, Any]) -> str:
    return (
        base64.urlsafe_b64encode(json.dumps(data).encode())
        .decode()
        .rstrip("=")
    )


def _make_jwt(header: dict[str, Any], payload: dict[str, Any]) -> str:
    return f"{_b64url(header)}.{_b64url(payload)}.signature"


class TestJwtHandling:
    """JWT payload decoding should reject unsigned tokens and parse known claims."""

    def test_extract_client_id_rejects_alg_none(self):
        c = client_mod.Client(verify_login=False)
        token = _make_jwt({"alg": "none"}, {"client_id": "12345"})
        assert c._extract_client_id_from_jwt(token) is None

    def test_extract_client_id_parses_valid_claim(self):
        c = client_mod.Client(verify_login=False)
        token = _make_jwt({"alg": "RS256"}, {"client_id": 12345})
        assert c._extract_client_id_from_jwt(token) == "12345"

    def test_extract_client_id_returns_none_when_claim_missing(self):
        c = client_mod.Client(verify_login=False)
        token = _make_jwt({"alg": "RS256"}, {"sub": "user"})
        assert c._extract_client_id_from_jwt(token) is None

    def test_token_expires_soon_rejects_alg_none(self):
        c = client_mod.Client(verify_login=False)
        token = _make_jwt(
            {"alg": "none"}, {"exp": int(time.time()) + 60}
        )
        c.di_token = token
        assert c._token_expires_soon() is False

    def test_token_expires_soon_true_when_close_to_expiry(self):
        c = client_mod.Client(verify_login=False)
        token = _make_jwt(
            {"alg": "RS256"}, {"exp": int(time.time()) + 60}
        )
        c.di_token = token
        assert c._token_expires_soon() is True

    def test_token_expires_soon_false_when_far_from_expiry(self):
        c = client_mod.Client(verify_login=False)
        token = _make_jwt(
            {"alg": "RS256"}, {"exp": int(time.time()) + 3600}
        )
        c.di_token = token
        assert c._token_expires_soon() is False

    def test_token_expires_soon_falls_back_to_jwt_web(self):
        c = client_mod.Client(verify_login=False)
        token = _make_jwt(
            {"alg": "RS256"}, {"exp": int(time.time()) + 60}
        )
        c.jwt_web = token
        assert c._token_expires_soon() is True


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
                garmin.update_workout(123, [1, 2, 3])  # type: ignore[arg-type]
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


# ---------------------------------------------------------------------------
# Identifier validation on mutating/download/gear endpoints
# ---------------------------------------------------------------------------


class TestIdentifierValidation:
    """Methods that interpolate identifiers into URLs must validate them."""

    MALICIOUS = "123/../../userprofile-service/socialProfile"
    UUID = "3c814e7a-0db1-41a4-bdb8-4944db6fb8b3"

    @pytest.mark.parametrize(
        "method_name,args",
        [
            ("set_activity_name", (MALICIOUS, "title")),
            ("set_activity_type", (MALICIOUS, 2, "RUNNING", 1)),
            ("set_activity_description", (MALICIOUS, "desc")),
            ("download_activity", (MALICIOUS,)),
            ("get_gear_defaults", (MALICIOUS,)),
            ("delete_weigh_in", (MALICIOUS, "2026-01-01")),
            ("delete_blood_pressure", (MALICIOUS, "2026-01-01")),
        ],
    )
    def test_rejects_path_traversal_in_numeric_id(
        self, garmin: garminconnect.Garmin, method_name: str, args: tuple[Any, ...]
    ):
        method = getattr(garmin, method_name)
        with pytest.raises(ValueError):
            method(*args)

    def test_rejects_path_traversal_in_gear_uuid(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError):
            garmin.get_gear_stats(self.MALICIOUS)

    def test_rejects_path_traversal_in_add_gear(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError):
            garmin.add_gear_to_activity(self.MALICIOUS, 1)

    def test_rejects_invalid_activity_type(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError):
            garmin.set_gear_default("invalid!", self.UUID)

    def test_accepts_valid_gear_uuid(self, garmin: garminconnect.Garmin):
        with patch.object(garmin, "connectapi", return_value={}) as api:
            garmin.get_gear_stats(self.UUID)
        assert self.UUID in api.call_args[0][0]

    def test_delete_blood_pressure_validates_date(self, garmin: garminconnect.Garmin):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            garmin.delete_blood_pressure("1", "not-a-date")


# ---------------------------------------------------------------------------
# Activity upload filename handling
# ---------------------------------------------------------------------------


class TestActivityUpload:
    """import_activity() must pass filenames to requests without extra quoting."""

    def test_import_activity_passes_filename_without_extra_quotes(self, tmp_path):
        fit_file = tmp_path / "activity.fit"
        fit_file.write_bytes(b"fake-fit-data")
        g = garminconnect.Garmin("user@example.com", "secret")

        with patch.object(g.client, "post", return_value={}) as mock_post:
            g.import_activity(str(fit_file))

        files = mock_post.call_args.kwargs["files"]
        filename = files["file"][0]
        assert filename == "activity.fit"
        assert not filename.startswith('"')
        assert not filename.endswith('"')
