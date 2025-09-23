"""Python 3 API wrapper for Garmin Connect."""

import logging
import numbers
import os
import re
from collections.abc import Callable
from datetime import date, datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any

import garth
import requests
from garth.exc import GarthException, GarthHTTPError
from requests import HTTPError

from .fit import FitEncoderWeight  # type: ignore

logger = logging.getLogger(__name__)

# Constants for validation
MAX_ACTIVITY_LIMIT = 1000
MAX_HYDRATION_ML = 10000  # 10 liters
DATE_FORMAT_REGEX = r"^\d{4}-\d{2}-\d{2}$"
DATE_FORMAT_STR = "%Y-%m-%d"
VALID_WEIGHT_UNITS = {"kg", "lbs"}


# Add validation utilities
def _validate_date_format(date_str: str, param_name: str = "date") -> str:
    """Validate date string format YYYY-MM-DD."""
    if not isinstance(date_str, str):
        raise ValueError(f"{param_name} must be a string")

    # Remove any extra whitespace
    date_str = date_str.strip()

    if not re.fullmatch(DATE_FORMAT_REGEX, date_str):
        raise ValueError(
            f"{param_name} must be in format 'YYYY-MM-DD', got: {date_str}"
        )

    try:
        # Validate that it's a real date
        datetime.strptime(date_str, DATE_FORMAT_STR)
    except ValueError as e:
        raise ValueError(f"invalid {param_name}: {e}") from e

    return date_str


def _validate_positive_number(
    value: int | float, param_name: str = "value"
) -> int | float:
    """Validate that a number is positive."""
    if not isinstance(value, numbers.Real):
        raise ValueError(f"{param_name} must be a number")

    if isinstance(value, bool):
        raise ValueError(f"{param_name} must be a number, not bool")

    if value <= 0:
        raise ValueError(f"{param_name} must be positive, got: {value}")

    return value


def _validate_non_negative_integer(value: int, param_name: str = "value") -> int:
    """Validate that a value is a non-negative integer."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{param_name} must be an integer")

    if value < 0:
        raise ValueError(f"{param_name} must be non-negative, got: {value}")

    return value


def _validate_positive_integer(value: int, param_name: str = "value") -> int:
    """Validate that a value is a positive integer."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{param_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{param_name} must be a positive integer, got: {value}")
    return value


def _fmt_ts(dt: datetime) -> str:
    # Use ms precision to match server expectations
    return dt.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


class Garmin:
    """Class for fetching data from Garmin Connect."""

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        is_cn: bool = False,
        prompt_mfa: Callable[[], str] | None = None,
        return_on_mfa: bool = False,
    ) -> None:
        """Create a new class instance."""

        # Validate input types
        if email is not None and not isinstance(email, str):
            raise ValueError("email must be a string or None")
        if password is not None and not isinstance(password, str):
            raise ValueError("password must be a string or None")
        if not isinstance(is_cn, bool):
            raise ValueError("is_cn must be a boolean")
        if not isinstance(return_on_mfa, bool):
            raise ValueError("return_on_mfa must be a boolean")

        self.username = email
        self.password = password
        self.is_cn = is_cn
        self.prompt_mfa = prompt_mfa
        self.return_on_mfa = return_on_mfa

        self.garmin_connect_user_settings_url = (
            "/userprofile-service/userprofile/user-settings"
        )
        self.garmin_connect_userprofile_settings_url = (
            "/userprofile-service/userprofile/settings"
        )
        self.garmin_connect_devices_url = "/device-service/deviceregistration/devices"
        self.garmin_connect_device_url = "/device-service/deviceservice"

        self.garmin_connect_primary_device_url = (
            "/web-gateway/device-info/primary-training-device"
        )

        self.garmin_connect_solar_url = "/web-gateway/solar"
        self.garmin_connect_weight_url = "/weight-service"
        self.garmin_connect_daily_summary_url = "/usersummary-service/usersummary/daily"
        self.garmin_connect_metrics_url = "/metrics-service/metrics/maxmet/daily"
        self.garmin_connect_biometric_url = "/biometric-service/biometric"

        self.garmin_connect_biometric_stats_url = "/biometric-service/stats"
        self.garmin_connect_daily_hydration_url = (
            "/usersummary-service/usersummary/hydration/daily"
        )
        self.garmin_connect_set_hydration_url = (
            "/usersummary-service/usersummary/hydration/log"
        )
        self.garmin_connect_daily_stats_steps_url = (
            "/usersummary-service/stats/steps/daily"
        )
        self.garmin_connect_personal_record_url = (
            "/personalrecord-service/personalrecord/prs"
        )
        self.garmin_connect_earned_badges_url = "/badge-service/badge/earned"
        self.garmin_connect_available_badges_url = "/badge-service/badge/available"
        self.garmin_connect_adhoc_challenges_url = (
            "/adhocchallenge-service/adHocChallenge/historical"
        )
        self.garmin_connect_badge_challenges_url = (
            "/badgechallenge-service/badgeChallenge/completed"
        )
        self.garmin_connect_available_badge_challenges_url = (
            "/badgechallenge-service/badgeChallenge/available"
        )
        self.garmin_connect_non_completed_badge_challenges_url = (
            "/badgechallenge-service/badgeChallenge/non-completed"
        )
        self.garmin_connect_inprogress_virtual_challenges_url = (
            "/badgechallenge-service/virtualChallenge/inProgress"
        )
        self.garmin_connect_daily_sleep_url = (
            "/wellness-service/wellness/dailySleepData"
        )
        self.garmin_connect_daily_stress_url = "/wellness-service/wellness/dailyStress"
        self.garmin_connect_hill_score_url = "/metrics-service/metrics/hillscore"

        self.garmin_connect_daily_body_battery_url = (
            "/wellness-service/wellness/bodyBattery/reports/daily"
        )

        self.garmin_connect_body_battery_events_url = (
            "/wellness-service/wellness/bodyBattery/events"
        )

        self.garmin_connect_blood_pressure_endpoint = (
            "/bloodpressure-service/bloodpressure/range"
        )

        self.garmin_connect_set_blood_pressure_endpoint = (
            "/bloodpressure-service/bloodpressure"
        )

        self.garmin_connect_endurance_score_url = (
            "/metrics-service/metrics/endurancescore"
        )
        self.garmin_connect_menstrual_calendar_url = (
            "/periodichealth-service/menstrualcycle/calendar"
        )

        self.garmin_connect_menstrual_dayview_url = (
            "/periodichealth-service/menstrualcycle/dayview"
        )
        self.garmin_connect_pregnancy_snapshot_url = (
            "/periodichealth-service/menstrualcycle/pregnancysnapshot"
        )
        self.garmin_connect_goals_url = "/goal-service/goal/goals"

        self.garmin_connect_rhr_url = "/userstats-service/wellness/daily"

        self.garmin_connect_hrv_url = "/hrv-service/hrv"

        self.garmin_connect_training_readiness_url = (
            "/metrics-service/metrics/trainingreadiness"
        )

        self.garmin_connect_race_predictor_url = (
            "/metrics-service/metrics/racepredictions"
        )
        self.garmin_connect_training_status_url = (
            "/metrics-service/metrics/trainingstatus/aggregated"
        )
        self.garmin_connect_user_summary_chart = (
            "/wellness-service/wellness/dailySummaryChart"
        )
        self.garmin_connect_floors_chart_daily_url = (
            "/wellness-service/wellness/floorsChartData/daily"
        )
        self.garmin_connect_heartrates_daily_url = (
            "/wellness-service/wellness/dailyHeartRate"
        )
        self.garmin_connect_daily_respiration_url = (
            "/wellness-service/wellness/daily/respiration"
        )
        self.garmin_connect_daily_spo2_url = "/wellness-service/wellness/daily/spo2"
        self.garmin_connect_daily_intensity_minutes = (
            "/wellness-service/wellness/daily/im"
        )
        self.garmin_daily_events_url = "/wellness-service/wellness/dailyEvents"
        self.garmin_connect_activities = (
            "/activitylist-service/activities/search/activities"
        )
        self.garmin_connect_activities_baseurl = "/activitylist-service/activities/"
        self.garmin_connect_activity = "/activity-service/activity"
        self.garmin_connect_activity_types = "/activity-service/activity/activityTypes"
        self.garmin_connect_activity_fordate = "/mobile-gateway/heartRate/forDate"
        self.garmin_connect_fitnessstats = "/fitnessstats-service/activity"
        self.garmin_connect_fitnessage = "/fitnessage-service/fitnessage"

        self.garmin_connect_fit_download = "/download-service/files/activity"
        self.garmin_connect_tcx_download = "/download-service/export/tcx/activity"
        self.garmin_connect_gpx_download = "/download-service/export/gpx/activity"
        self.garmin_connect_kml_download = "/download-service/export/kml/activity"
        self.garmin_connect_csv_download = "/download-service/export/csv/activity"

        self.garmin_connect_upload = "/upload-service/upload"

        self.garmin_connect_gear = "/gear-service/gear/filterGear"
        self.garmin_connect_gear_baseurl = "/gear-service/gear/"

        self.garmin_request_reload_url = "/wellness-service/wellness/epoch/request"

        self.garmin_workouts = "/workout-service"

        self.garmin_connect_delete_activity_url = "/activity-service/activity"

        self.garmin_graphql_endpoint = "graphql-gateway/graphql"

        self.garmin_training_plan_url = "/trainingplan-service/trainingplan"

        self.garth = garth.Client(
            domain="garmin.cn" if is_cn else "garmin.com",
            pool_connections=20,
            pool_maxsize=20,
        )

        self.display_name = None
        self.full_name = None
        self.unit_system = None

    def connectapi(self, path: str, **kwargs: Any) -> Any:
        """Wrapper for garth connectapi with error handling."""
        try:
            return self.garth.connectapi(path, **kwargs)
        except (HTTPError, GarthHTTPError) as e:
            # For GarthHTTPError, extract status from the wrapped HTTPError
            if isinstance(e, GarthHTTPError):
                status = getattr(
                    getattr(e.error, "response", None), "status_code", None
                )
            else:
                status = getattr(getattr(e, "response", None), "status_code", None)

            logger.error(
                "API call failed for path '%s': %s (status=%s)", path, e, status
            )
            if status == 401:
                raise GarminConnectAuthenticationError(
                    f"Authentication failed: {e}"
                ) from e
            elif status == 429:
                raise GarminConnectTooManyRequestsError(
                    f"Rate limit exceeded: {e}"
                ) from e
            elif status and 400 <= status < 500:
                # Client errors (400-499) - API endpoint issues, bad parameters, etc.
                raise GarminConnectConnectionError(
                    f"API client error ({status}): {e}"
                ) from e
            else:
                raise GarminConnectConnectionError(f"HTTP error: {e}") from e
        except Exception as e:
            logger.exception("Connection error during connectapi path=%s", path)
            raise GarminConnectConnectionError(f"Connection error: {e}") from e

    def download(self, path: str, **kwargs: Any) -> Any:
        """Wrapper for garth download with error handling."""
        try:
            return self.garth.download(path, **kwargs)
        except (HTTPError, GarthHTTPError) as e:
            # For GarthHTTPError, extract status from the wrapped HTTPError
            if isinstance(e, GarthHTTPError):
                status = getattr(
                    getattr(e.error, "response", None), "status_code", None
                )
            else:
                status = getattr(getattr(e, "response", None), "status_code", None)

            logger.exception("Download failed for path '%s' (status=%s)", path, status)
            if status == 401:
                raise GarminConnectAuthenticationError(f"Download error: {e}") from e
            elif status == 429:
                raise GarminConnectTooManyRequestsError(f"Download error: {e}") from e
            elif status and 400 <= status < 500:
                # Client errors (400-499) - API endpoint issues, bad parameters, etc.
                raise GarminConnectConnectionError(
                    f"Download client error ({status}): {e}"
                ) from e
            else:
                raise GarminConnectConnectionError(f"Download error: {e}") from e
        except Exception as e:
            logger.exception("Download failed for path '%s'", path)
            raise GarminConnectConnectionError(f"Download error: {e}") from e

    def login(self, /, tokenstore: str | None = None) -> tuple[str | None, str | None]:
        """
        Log in using Garth.

        Returns:
            Tuple[str | None, str | None]: (access_token, refresh_token) when using credential flow;
            (None, None) when loading from tokenstore.
        """
        tokenstore = tokenstore or os.getenv("GARMINTOKENS")

        try:
            token1 = None
            token2 = None

            if tokenstore:
                if len(tokenstore) > 512:
                    self.garth.loads(tokenstore)
                else:
                    self.garth.load(tokenstore)
            else:
                # Validate credentials before attempting login
                if not self.username or not self.password:
                    raise GarminConnectAuthenticationError(
                        "Username and password are required"
                    )

                # Validate email format when actually used for login
                if not self.is_cn and self.username and "@" not in self.username:
                    raise GarminConnectAuthenticationError(
                        "Email must contain '@' symbol"
                    )

                if self.return_on_mfa:
                    token1, token2 = self.garth.login(
                        self.username,
                        self.password,
                        return_on_mfa=self.return_on_mfa,
                    )
                    # In MFA early-return mode, profile/settings are not loaded yet
                    return token1, token2
                else:
                    token1, token2 = self.garth.login(
                        self.username,
                        self.password,
                        prompt_mfa=self.prompt_mfa,
                    )
                    # Continue to load profile/settings below

            # Ensure profile is loaded (tokenstore path may not populate it)
            if not getattr(self.garth, "profile", None):
                try:
                    prof = self.garth.connectapi(
                        "/userprofile-service/userprofile/profile"
                    )
                except Exception as e:
                    raise GarminConnectAuthenticationError(
                        "Failed to retrieve profile"
                    ) from e
                if not prof or "displayName" not in prof:
                    raise GarminConnectAuthenticationError("Invalid profile data found")
                # Use profile data directly since garth.profile is read-only
                self.display_name = prof.get("displayName")
                self.full_name = prof.get("fullName")
            else:
                self.display_name = self.garth.profile.get("displayName")
                self.full_name = self.garth.profile.get("fullName")

            settings = self.garth.connectapi(self.garmin_connect_user_settings_url)

            if not settings:
                raise GarminConnectAuthenticationError(
                    "Failed to retrieve user settings"
                )

            if "userData" not in settings:
                raise GarminConnectAuthenticationError("Invalid user settings found")

            self.unit_system = settings["userData"].get("measurementSystem")

            return token1, token2

        except (HTTPError, requests.exceptions.HTTPError, GarthException) as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            logger.error("Login failed: %s (status=%s)", e, status)

            # Check status code first
            if status == 401:
                raise GarminConnectAuthenticationError(
                    f"Authentication failed: {e}"
                ) from e
            elif status == 429:
                raise GarminConnectTooManyRequestsError(
                    f"Rate limit exceeded: {e}"
                ) from e

            # If no status code, check error message for authentication indicators
            error_str = str(e).lower()
            auth_indicators = ["401", "unauthorized", "authentication failed"]
            if any(indicator in error_str for indicator in auth_indicators):
                raise GarminConnectAuthenticationError(
                    f"Authentication failed: {e}"
                ) from e

            # Default to connection error
            raise GarminConnectConnectionError(f"Login failed: {e}") from e
        except FileNotFoundError:
            # Let FileNotFoundError pass through - this is expected when no tokens exist
            raise
        except Exception as e:
            if isinstance(e, GarminConnectAuthenticationError):
                raise
            # Check if this is an authentication error based on the error message
            error_str = str(
                e
            ).lower()  # Convert to lowercase for case-insensitive matching
            auth_indicators = ["401", "unauthorized", "authentication", "login failed"]
            is_auth_error = any(indicator in error_str for indicator in auth_indicators)

            if is_auth_error:
                raise GarminConnectAuthenticationError(
                    f"Authentication failed: {e}"
                ) from e
            logger.exception("Login failed")
            raise GarminConnectConnectionError(f"Login failed: {e}") from e

    def resume_login(
        self, client_state: dict[str, Any], mfa_code: str
    ) -> tuple[Any, Any]:
        """Resume login using Garth."""
        result1, result2 = self.garth.resume_login(client_state, mfa_code)

        if self.garth.profile:
            self.display_name = self.garth.profile["displayName"]
            self.full_name = self.garth.profile["fullName"]

        settings = self.garth.connectapi(self.garmin_connect_user_settings_url)
        if settings and "userData" in settings:
            self.unit_system = settings["userData"]["measurementSystem"]

        return result1, result2

    def get_full_name(self) -> str | None:
        """Return full name."""

        return self.full_name

    def get_unit_system(self) -> str | None:
        """Return unit system."""

        return self.unit_system

    def get_stats(self, cdate: str) -> dict[str, Any]:
        """
        Return user activity summary for 'cdate' format 'YYYY-MM-DD'
        (compat for garminconnect).
        """

        return self.get_user_summary(cdate)

    def get_user_summary(self, cdate: str) -> dict[str, Any]:
        """Return user activity summary for 'cdate' format 'YYYY-MM-DD'."""

        # Validate input
        cdate = _validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_daily_summary_url}/{self.display_name}"
        params = {"calendarDate": cdate}
        logger.debug("Requesting user summary")

        response = self.connectapi(url, params=params)

        if not response:
            raise GarminConnectConnectionError("No data received from server")

        if response.get("privacyProtected") is True:
            raise GarminConnectAuthenticationError("Authentication error")

        return response

    def get_steps_data(self, cdate: str) -> list[dict[str, Any]]:
        """Fetch available steps data 'cDate' format 'YYYY-MM-DD'."""

        # Validate input
        cdate = _validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_user_summary_chart}/{self.display_name}"
        params = {"date": cdate}
        logger.debug("Requesting steps data")

        response = self.connectapi(url, params=params)

        if response is None:
            logger.warning("No steps data received")
            return []

        return response

    def get_floors(self, cdate: str) -> dict[str, Any]:
        """Fetch available floors data 'cDate' format 'YYYY-MM-DD'."""

        # Validate input
        cdate = _validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_floors_chart_daily_url}/{cdate}"
        logger.debug("Requesting floors data")

        response = self.connectapi(url)

        if response is None:
            raise GarminConnectConnectionError("No floors data received")

        return response

    def get_daily_steps(self, start: str, end: str) -> list[dict[str, Any]]:
        """Fetch available steps data 'start' and 'end' format 'YYYY-MM-DD'."""

        # Validate inputs
        start = _validate_date_format(start, "start")
        end = _validate_date_format(end, "end")

        # Validate date range
        start_date = datetime.strptime(start, DATE_FORMAT_STR).date()
        end_date = datetime.strptime(end, DATE_FORMAT_STR).date()

        if start_date > end_date:
            raise ValueError("start date cannot be after end date")

        url = f"{self.garmin_connect_daily_stats_steps_url}/{start}/{end}"
        logger.debug("Requesting daily steps data")

        return self.connectapi(url)

    def get_heart_rates(self, cdate: str) -> dict[str, Any]:
        """Fetch available heart rates data 'cDate' format 'YYYY-MM-DD'.

        Args:
            cdate: Date string in format 'YYYY-MM-DD'

        Returns:
            Dictionary containing heart rate data for the specified date

        Raises:
            ValueError: If cdate format is invalid
            GarminConnectConnectionError: If no data received
            GarminConnectAuthenticationError: If authentication fails
        """

        # Validate input
        cdate = _validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_heartrates_daily_url}/{self.display_name}"
        params = {"date": cdate}
        logger.debug("Requesting heart rates")

        response = self.connectapi(url, params=params)

        if response is None:
            raise GarminConnectConnectionError("No heart rate data received")

        return response

    def get_stats_and_body(self, cdate: str) -> dict[str, Any]:
        """Return activity data and body composition (compat for garminconnect)."""

        stats = self.get_stats(cdate)
        body = self.get_body_composition(cdate)
        body_avg = body.get("totalAverage") or {}
        if not isinstance(body_avg, dict):
            body_avg = {}
        return {**stats, **body_avg}

    def get_body_composition(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """
        Return available body composition data for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'.
        """

        startdate = _validate_date_format(startdate, "startdate")
        enddate = (
            startdate if enddate is None else _validate_date_format(enddate, "enddate")
        )
        if (
            datetime.strptime(startdate, DATE_FORMAT_STR).date()
            > datetime.strptime(enddate, DATE_FORMAT_STR).date()
        ):
            raise ValueError("startdate cannot be after enddate")
        url = f"{self.garmin_connect_weight_url}/weight/dateRange"
        params = {"startDate": str(startdate), "endDate": str(enddate)}
        logger.debug("Requesting body composition")

        return self.connectapi(url, params=params)

    def add_body_composition(
        self,
        timestamp: str | None,
        weight: float,
        percent_fat: float | None = None,
        percent_hydration: float | None = None,
        visceral_fat_mass: float | None = None,
        bone_mass: float | None = None,
        muscle_mass: float | None = None,
        basal_met: float | None = None,
        active_met: float | None = None,
        physique_rating: float | None = None,
        metabolic_age: float | None = None,
        visceral_fat_rating: float | None = None,
        bmi: float | None = None,
    ) -> dict[str, Any]:
        weight = _validate_positive_number(weight, "weight")
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        fitEncoder = FitEncoderWeight()
        fitEncoder.write_file_info()
        fitEncoder.write_file_creator()
        fitEncoder.write_device_info(dt)
        fitEncoder.write_weight_scale(
            dt,
            weight=weight,
            percent_fat=percent_fat,
            percent_hydration=percent_hydration,
            visceral_fat_mass=visceral_fat_mass,
            bone_mass=bone_mass,
            muscle_mass=muscle_mass,
            basal_met=basal_met,
            active_met=active_met,
            physique_rating=physique_rating,
            metabolic_age=metabolic_age,
            visceral_fat_rating=visceral_fat_rating,
            bmi=bmi,
        )
        fitEncoder.finish()

        url = self.garmin_connect_upload
        files = {
            "file": ("body_composition.fit", fitEncoder.getvalue()),
        }
        return self.garth.post("connectapi", url, files=files, api=True).json()

    def add_weigh_in(
        self, weight: int | float, unitKey: str = "kg", timestamp: str = ""
    ) -> dict[str, Any]:
        """Add a weigh-in (default to kg)"""

        # Validate inputs
        weight = _validate_positive_number(weight, "weight")

        if unitKey not in VALID_WEIGHT_UNITS:
            raise ValueError(f"unitKey must be one of {VALID_WEIGHT_UNITS}")

        url = f"{self.garmin_connect_weight_url}/user-weight"

        try:
            dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        except ValueError as e:
            raise ValueError(f"invalid timestamp format: {e}") from e

        # Apply timezone offset to get UTC/GMT time
        dtGMT = dt.astimezone(timezone.utc)
        payload = {
            "dateTimestamp": _fmt_ts(dt),
            "gmtTimestamp": _fmt_ts(dtGMT),
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }
        logger.debug("Adding weigh-in")

        return self.garth.post("connectapi", url, json=payload).json()

    def add_weigh_in_with_timestamps(
        self,
        weight: int | float,
        unitKey: str = "kg",
        dateTimestamp: str = "",
        gmtTimestamp: str = "",
    ) -> dict[str, Any]:
        """Add a weigh-in with explicit timestamps (default to kg)"""

        url = f"{self.garmin_connect_weight_url}/user-weight"

        if unitKey not in VALID_WEIGHT_UNITS:
            raise ValueError(f"unitKey must be one of {VALID_WEIGHT_UNITS}")
        # Make local timestamp timezone-aware
        dt = (
            datetime.fromisoformat(dateTimestamp).astimezone()
            if dateTimestamp
            else datetime.now().astimezone()
        )
        if gmtTimestamp:
            g = datetime.fromisoformat(gmtTimestamp)
            # Assume provided GMT is UTC if naive; otherwise convert to UTC
            if g.tzinfo is None:
                g = g.replace(tzinfo=timezone.utc)
            dtGMT = g.astimezone(timezone.utc)
        else:
            dtGMT = dt.astimezone(timezone.utc)

        # Validate weight for consistency with add_weigh_in
        weight = _validate_positive_number(weight, "weight")
        # Build the payload
        payload = {
            "dateTimestamp": _fmt_ts(dt),  # Local time (ms)
            "gmtTimestamp": _fmt_ts(dtGMT),  # GMT/UTC time (ms)
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }

        # Debug log for payload
        logger.debug("Adding weigh-in with explicit timestamps: %s", payload)

        # Make the POST request
        return self.garth.post("connectapi", url, json=payload).json()

    def get_weigh_ins(self, startdate: str, enddate: str) -> dict[str, Any]:
        """Get weigh-ins between startdate and enddate using format 'YYYY-MM-DD'."""

        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_weight_url}/weight/range/{startdate}/{enddate}"
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def get_daily_weigh_ins(self, cdate: str) -> dict[str, Any]:
        """Get weigh-ins for 'cdate' format 'YYYY-MM-DD'."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_weight_url}/weight/dayview/{cdate}"
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def delete_weigh_in(self, weight_pk: str, cdate: str) -> Any:
        """Delete specific weigh-in."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_weight_url}/weight/{cdate}/byversion/{weight_pk}"
        logger.debug("Deleting weigh-in")

        return self.garth.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def delete_weigh_ins(self, cdate: str, delete_all: bool = False) -> int | None:
        """
        Delete weigh-in for 'cdate' format 'YYYY-MM-DD'.
        Includes option to delete all weigh-ins for that date.
        """

        daily_weigh_ins = self.get_daily_weigh_ins(cdate)
        weigh_ins = daily_weigh_ins.get("dateWeightList", [])
        if not weigh_ins or len(weigh_ins) == 0:
            logger.warning(f"No weigh-ins found on {cdate}")
            return None
        elif len(weigh_ins) > 1:
            logger.warning(f"Multiple weigh-ins found for {cdate}")
            if not delete_all:
                logger.warning(
                    f"Set delete_all to True to delete all {len(weigh_ins)} weigh-ins"
                )
                return None

        for w in weigh_ins:
            self.delete_weigh_in(w["samplePk"], cdate)

        return len(weigh_ins)

    def get_body_battery(
        self, startdate: str, enddate: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Return body battery values by day for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'
        """

        startdate = _validate_date_format(startdate, "startdate")
        if enddate is None:
            enddate = startdate
        else:
            enddate = _validate_date_format(enddate, "enddate")
        url = self.garmin_connect_daily_body_battery_url
        params = {"startDate": str(startdate), "endDate": str(enddate)}
        logger.debug("Requesting body battery data")

        return self.connectapi(url, params=params)

    def get_body_battery_events(self, cdate: str) -> list[dict[str, Any]]:
        """
        Return body battery events for date 'cdate' format 'YYYY-MM-DD'.
        The return value is a list of dictionaries, where each dictionary contains event data for a specific event.
        Events can include sleep, recorded activities, auto-detected activities, and naps
        """

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_body_battery_events_url}/{cdate}"
        logger.debug("Requesting body battery event data")

        return self.connectapi(url)

    def set_blood_pressure(
        self,
        systolic: int,
        diastolic: int,
        pulse: int,
        timestamp: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        """
        Add blood pressure measurement
        """

        url = f"{self.garmin_connect_set_blood_pressure_endpoint}"
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        # Apply timezone offset to get UTC/GMT time
        dtGMT = dt.astimezone(timezone.utc)
        payload = {
            "measurementTimestampLocal": _fmt_ts(dt),
            "measurementTimestampGMT": _fmt_ts(dtGMT),
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse,
            "sourceType": "MANUAL",
            "notes": notes,
        }
        for name, val, lo, hi in (
            ("systolic", systolic, 70, 260),
            ("diastolic", diastolic, 40, 150),
            ("pulse", pulse, 20, 250),
        ):
            if not isinstance(val, int) or not (lo <= val <= hi):
                raise ValueError(f"{name} must be an int in [{lo}, {hi}]")
        logger.debug("Adding blood pressure")

        return self.garth.post("connectapi", url, json=payload).json()

    def get_blood_pressure(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """
        Returns blood pressure by day for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'
        """

        startdate = _validate_date_format(startdate, "startdate")
        if enddate is None:
            enddate = startdate
        else:
            enddate = _validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_blood_pressure_endpoint}/{startdate}/{enddate}"
        params = {"includeAll": True}
        logger.debug("Requesting blood pressure data")

        return self.connectapi(url, params=params)

    def delete_blood_pressure(self, version: str, cdate: str) -> dict[str, Any]:
        """Delete specific blood pressure measurement."""
        url = f"{self.garmin_connect_set_blood_pressure_endpoint}/{cdate}/{version}"
        logger.debug("Deleting blood pressure measurement")

        return self.garth.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        ).json()

    def get_max_metrics(self, cdate: str) -> dict[str, Any]:
        """Return available max metric data for 'cdate' format 'YYYY-MM-DD'."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_metrics_url}/{cdate}/{cdate}"
        logger.debug("Requesting max metrics")

        return self.connectapi(url)

    def get_lactate_threshold(
        self,
        *,
        latest: bool = True,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        aggregation: str = "daily",
    ) -> dict[str, Any]:
        """
        Returns Running Lactate Threshold information, including heart rate, power, and speed

        :param bool (Required) - latest: Whether to query for the latest Lactate Threshold info or a range.  False if querying a range
        :param date (Optional) - start_date: The first date in the range to query, format 'YYYY-MM-DD'.  Required if `latest` is False.  Ignored if `latest` is True
        :param date (Optional) - end_date: The last date in the range to query, format 'YYYY-MM-DD'. Defaults to current data. Ignored if `latest` is True
        :param str (Optional) - aggregation: How to aggregate the data. Must be one of `daily`, `weekly`, `monthly`, `yearly`.
        """

        if latest:
            speed_and_heart_rate_url = (
                f"{self.garmin_connect_biometric_url}/latestLactateThreshold"
            )
            power_url = f"{self.garmin_connect_biometric_url}/powerToWeight/latest/{date.today()}?sport=Running"

            power = self.connectapi(power_url)
            if isinstance(power, list) and power:
                power_dict = power[0]
            elif isinstance(power, dict):
                power_dict = power
            else:
                power_dict = {}

            speed_and_heart_rate = self.connectapi(speed_and_heart_rate_url)

            speed_and_heart_rate_dict = {
                "userProfilePK": None,
                "version": None,
                "calendarDate": None,
                "sequence": None,
                "speed": None,
                "heartRate": None,
                "heartRateCycling": None,
            }

            # Garmin /latestLactateThreshold endpoint returns a list of two
            # (or more, if cyclingHeartRate ever gets values) nearly identical dicts.
            # We're combining them here
            for entry in speed_and_heart_rate:
                speed = entry.get("speed")
                if speed is not None:
                    speed_and_heart_rate_dict["userProfilePK"] = entry["userProfilePK"]
                    speed_and_heart_rate_dict["version"] = entry["version"]
                    speed_and_heart_rate_dict["calendarDate"] = entry["calendarDate"]
                    speed_and_heart_rate_dict["sequence"] = entry["sequence"]
                    speed_and_heart_rate_dict["speed"] = speed

                # Prefer correct key; fall back to Garmin's historical typo ("hearRate")
                hr = entry.get("heartRate") or entry.get("hearRate")
                if hr is not None:
                    speed_and_heart_rate_dict["heartRate"] = hr

                # Doesn't exist for me but adding it just in case.  We'll check for each entry
                hrc = entry.get("heartRateCycling")
                if hrc is not None:
                    speed_and_heart_rate_dict["heartRateCycling"] = hrc
            return {
                "speed_and_heart_rate": speed_and_heart_rate_dict,
                "power": power_dict,
            }

        if start_date is None:
            raise ValueError("you must either specify 'latest=True' or a start_date")

        if end_date is None:
            end_date = date.today().isoformat()

        # Normalize and validate
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        else:
            start_date = _validate_date_format(start_date, "start_date")
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        else:
            end_date = _validate_date_format(end_date, "end_date")

        _valid_aggregations = {"daily", "weekly", "monthly", "yearly"}
        if aggregation not in _valid_aggregations:
            raise ValueError(f"aggregation must be one of {_valid_aggregations}")

        speed_url = f"{self.garmin_connect_biometric_stats_url}/lactateThresholdSpeed/range/{start_date}/{end_date}?sport=RUNNING&aggregation={aggregation}&aggregationStrategy=LATEST"

        heart_rate_url = f"{self.garmin_connect_biometric_stats_url}/lactateThresholdHeartRate/range/{start_date}/{end_date}?sport=RUNNING&aggregation={aggregation}&aggregationStrategy=LATEST"

        power_url = f"{self.garmin_connect_biometric_stats_url}/functionalThresholdPower/range/{start_date}/{end_date}?sport=RUNNING&aggregation={aggregation}&aggregationStrategy=LATEST"

        speed = self.connectapi(speed_url)
        heart_rate = self.connectapi(heart_rate_url)
        power = self.connectapi(power_url)

        return {"speed": speed, "heart_rate": heart_rate, "power": power}

    def add_hydration_data(
        self,
        value_in_ml: float,
        timestamp: str | None = None,
        cdate: str | None = None,
    ) -> dict[str, Any]:
        """Add hydration data in ml.  Defaults to current date and current timestamp if left empty
        :param float required - value_in_ml: The number of ml of water you wish to add (positive) or subtract (negative)
        :param timestamp optional - timestamp: The timestamp of the hydration update, format 'YYYY-MM-DDThh:mm:ss.ms' Defaults to current timestamp
        :param date optional - cdate: The date of the weigh in, format 'YYYY-MM-DD'. Defaults to current date
        """

        # Validate inputs
        if not isinstance(value_in_ml, numbers.Real):
            raise ValueError("value_in_ml must be a number")

        # Allow negative values for subtraction but validate reasonable range
        if abs(value_in_ml) > MAX_HYDRATION_ML:
            raise ValueError(
                f"value_in_ml seems unreasonably high (>{MAX_HYDRATION_ML}ml)"
            )

        url = self.garmin_connect_set_hydration_url

        if timestamp is None and cdate is None:
            # If both are null, use today and now
            raw_date = date.today()
            cdate = str(raw_date)

            raw_ts = datetime.now()
            timestamp = _fmt_ts(raw_ts)

        elif cdate is not None and timestamp is None:
            # If cdate is provided, validate and use midnight local time
            cdate = _validate_date_format(cdate, "cdate")
            raw_ts = datetime.strptime(cdate, DATE_FORMAT_STR)  # midnight local
            timestamp = _fmt_ts(raw_ts)

        elif cdate is None and timestamp is not None:
            # If timestamp is provided, normalize and set cdate to its date part
            if not isinstance(timestamp, str):
                raise ValueError("timestamp must be a string")
            try:
                try:
                    raw_ts = datetime.fromisoformat(timestamp)
                except ValueError:
                    raw_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                cdate = raw_ts.date().isoformat()
                timestamp = _fmt_ts(raw_ts)
            except ValueError as e:
                raise ValueError("Invalid timestamp format (expected ISO 8601)") from e
        else:
            # Both provided - validate consistency and normalize
            cdate = _validate_date_format(cdate, "cdate")
            if not isinstance(timestamp, str):
                raise ValueError("timestamp must be a string")
            try:
                try:
                    raw_ts = datetime.fromisoformat(timestamp)
                except ValueError:
                    raw_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                ts_date = raw_ts.date().isoformat()
                if ts_date != cdate:
                    raise ValueError(
                        f"timestamp date ({ts_date}) doesn't match cdate ({cdate})"
                    )
                timestamp = _fmt_ts(raw_ts)
            except ValueError:
                raise

        payload = {
            "calendarDate": cdate,
            "timestampLocal": timestamp,
            "valueInML": value_in_ml,
        }

        logger.debug("Adding hydration data")
        return self.garth.put("connectapi", url, json=payload).json()

    def get_hydration_data(self, cdate: str) -> dict[str, Any]:
        """Return available hydration data 'cdate' format 'YYYY-MM-DD'."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_hydration_url}/{cdate}"
        logger.debug("Requesting hydration data")

        return self.connectapi(url)

    def get_respiration_data(self, cdate: str) -> dict[str, Any]:
        """Return available respiration data 'cdate' format 'YYYY-MM-DD'."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_respiration_url}/{cdate}"
        logger.debug("Requesting respiration data")

        return self.connectapi(url)

    def get_spo2_data(self, cdate: str) -> dict[str, Any]:
        """Return available SpO2 data 'cdate' format 'YYYY-MM-DD'."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_spo2_url}/{cdate}"
        logger.debug("Requesting SpO2 data")

        return self.connectapi(url)

    def get_intensity_minutes_data(self, cdate: str) -> dict[str, Any]:
        """Return available Intensity Minutes data 'cdate' format 'YYYY-MM-DD'."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_intensity_minutes}/{cdate}"
        logger.debug("Requesting Intensity Minutes data")

        return self.connectapi(url)

    def get_all_day_stress(self, cdate: str) -> dict[str, Any]:
        """Return available all day stress data 'cdate' format 'YYYY-MM-DD'."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_stress_url}/{cdate}"
        logger.debug("Requesting all day stress data")

        return self.connectapi(url)

    def get_all_day_events(self, cdate: str) -> dict[str, Any]:
        """
        Return available daily events data 'cdate' format 'YYYY-MM-DD'.
        Includes autodetected activities, even if not recorded on the watch
        """

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_daily_events_url}?calendarDate={cdate}"
        logger.debug("Requesting all day events data")

        return self.connectapi(url)

    def get_personal_record(self) -> dict[str, Any]:
        """Return personal records for current user."""

        url = f"{self.garmin_connect_personal_record_url}/{self.display_name}"
        logger.debug("Requesting personal records for user")

        return self.connectapi(url)

    def get_earned_badges(self) -> list[dict[str, Any]]:
        """Return earned badges for current user."""

        url = self.garmin_connect_earned_badges_url
        logger.debug("Requesting earned badges for user")

        return self.connectapi(url)

    def get_available_badges(self) -> list[dict[str, Any]]:
        """Return available badges for current user."""

        url = self.garmin_connect_available_badges_url
        logger.debug("Requesting available badges for user")

        return self.connectapi(url, params={"showExclusiveBadge": "true"})

    def get_in_progress_badges(self) -> list[dict[str, Any]]:
        """Return in progress badges for current user."""

        logger.debug("Requesting in progress badges for user")

        earned_badges = self.get_earned_badges()
        available_badges = self.get_available_badges()

        # Filter out badges that are not in progress
        def is_badge_in_progress(badge: dict) -> bool:
            """Return True if the badge is in progress."""
            progress = badge.get("badgeProgressValue")
            if not progress:
                return False
            if progress == 0:
                return False
            target = badge.get("badgeTargetValue")
            if progress == target:
                if badge.get("badgeLimitCount") is None:
                    return False
                return badge.get("badgeEarnedNumber", 0) < badge["badgeLimitCount"]
            return True

        earned_in_progress_badges = list(filter(is_badge_in_progress, earned_badges))
        available_in_progress_badges = list(
            filter(is_badge_in_progress, available_badges)
        )

        combined = {b["badgeId"]: b for b in earned_in_progress_badges}
        combined.update({b["badgeId"]: b for b in available_in_progress_badges})
        return list(combined.values())

    def get_adhoc_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return adhoc challenges for current user."""

        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_adhoc_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting adhoc challenges for user")

        return self.connectapi(url, params=params)

    def get_badge_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return badge challenges for current user."""

        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_available_badge_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return available badge challenges."""

        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_available_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting available badge challenges")

        return self.connectapi(url, params=params)

    def get_non_completed_badge_challenges(
        self, start: int, limit: int
    ) -> dict[str, Any]:
        """Return badge non-completed challenges for current user."""

        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_non_completed_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_inprogress_virtual_challenges(
        self, start: int, limit: int
    ) -> dict[str, Any]:
        """Return in-progress virtual challenges for current user."""

        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_inprogress_virtual_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting in-progress virtual challenges for user")

        return self.connectapi(url, params=params)

    def get_sleep_data(self, cdate: str) -> dict[str, Any]:
        """Return sleep data for current user."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_sleep_url}/{self.display_name}"
        params = {"date": cdate, "nonSleepBufferMinutes": 60}
        logger.debug("Requesting sleep data")

        return self.connectapi(url, params=params)

    def get_stress_data(self, cdate: str) -> dict[str, Any]:
        """Return stress data for current user."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_stress_url}/{cdate}"
        logger.debug("Requesting stress data")

        return self.connectapi(url)

    def get_rhr_day(self, cdate: str) -> dict[str, Any]:
        """Return resting heartrate data for current user."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_rhr_url}/{self.display_name}"
        params = {
            "fromDate": cdate,
            "untilDate": cdate,
            "metricId": 60,
        }
        logger.debug("Requesting resting heartrate data")

        return self.connectapi(url, params=params)

    def get_hrv_data(self, cdate: str) -> dict[str, Any] | None:
        """Return Heart Rate Variability (hrv) data for current user."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_hrv_url}/{cdate}"
        logger.debug("Requesting Heart Rate Variability (hrv) data")

        return self.connectapi(url)

    def get_training_readiness(self, cdate: str) -> dict[str, Any]:
        """Return training readiness data for current user."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_training_readiness_url}/{cdate}"
        logger.debug("Requesting training readiness data")

        return self.connectapi(url)

    def get_endurance_score(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """
        Return endurance score by day for 'startdate' format 'YYYY-MM-DD'
        through enddate 'YYYY-MM-DD'.
        Using a single day returns the precise values for that day.
        Using a range returns the aggregated weekly values for that week.
        """

        startdate = _validate_date_format(startdate, "startdate")
        if enddate is None:
            url = self.garmin_connect_endurance_score_url
            params = {"calendarDate": str(startdate)}
            logger.debug("Requesting endurance score data for a single day")

            return self.connectapi(url, params=params)
        else:
            url = f"{self.garmin_connect_endurance_score_url}/stats"
            enddate = _validate_date_format(enddate, "enddate")
            params = {
                "startDate": str(startdate),
                "endDate": str(enddate),
                "aggregation": "weekly",
            }
            logger.debug("Requesting endurance score data for a range of days")

            return self.connectapi(url, params=params)

    def get_race_predictions(
        self,
        startdate: str | None = None,
        enddate: str | None = None,
        _type: str | None = None,
    ) -> dict[str, Any]:
        """
        Return race predictions for the 5k, 10k, half marathon and marathon.
        Accepts either 0 parameters or all three:
        If all parameters are empty, returns the race predictions for the current date
        Or returns the race predictions for each day or month in the range provided

        Keyword Arguments:
        'startdate' the date of the earliest race predictions
        Cannot be more than one year before 'enddate'
        'enddate' the date of the last race predictions
        '_type' either 'daily' (the predictions for each day in the range) or
        'monthly' (the aggregated monthly prediction for each month in the range)
        """

        valid = {"daily", "monthly", None}
        if _type not in valid:
            raise ValueError(f"results: _type must be one of {valid!r}.")

        if _type is None and startdate is None and enddate is None:
            url = (
                self.garmin_connect_race_predictor_url + f"/latest/{self.display_name}"
            )
            return self.connectapi(url)

        elif _type is not None and startdate is not None and enddate is not None:
            startdate = _validate_date_format(startdate, "startdate")
            enddate = _validate_date_format(enddate, "enddate")
            if (
                datetime.strptime(enddate, DATE_FORMAT_STR).date()
                - datetime.strptime(startdate, DATE_FORMAT_STR).date()
            ).days > 366:
                raise ValueError(
                    "Startdate cannot be more than one year before enddate"
                )
            url = (
                self.garmin_connect_race_predictor_url + f"/{_type}/{self.display_name}"
            )
            params = {"fromCalendarDate": startdate, "toCalendarDate": enddate}
            return self.connectapi(url, params=params)

        else:
            raise ValueError("you must either provide all parameters or no parameters")

    def get_training_status(self, cdate: str) -> dict[str, Any]:
        """Return training status data for current user."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_training_status_url}/{cdate}"
        logger.debug("Requesting training status data")

        return self.connectapi(url)

    def get_fitnessage_data(self, cdate: str) -> dict[str, Any]:
        """Return Fitness Age data for current user."""

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_fitnessage}/{cdate}"
        logger.debug("Requesting Fitness Age data")

        return self.connectapi(url)

    def get_hill_score(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """
        Return hill score by day from 'startdate' format 'YYYY-MM-DD'
        to enddate 'YYYY-MM-DD'
        """

        if enddate is None:
            url = self.garmin_connect_hill_score_url
            startdate = _validate_date_format(startdate, "startdate")
            params = {"calendarDate": str(startdate)}
            logger.debug("Requesting hill score data for a single day")

            return self.connectapi(url, params=params)

        else:
            url = f"{self.garmin_connect_hill_score_url}/stats"
            startdate = _validate_date_format(startdate, "startdate")
            enddate = _validate_date_format(enddate, "enddate")
            params = {
                "startDate": str(startdate),
                "endDate": str(enddate),
                "aggregation": "daily",
            }
            logger.debug("Requesting hill score data for a range of days")

            return self.connectapi(url, params=params)

    def get_devices(self) -> list[dict[str, Any]]:
        """Return available devices for the current user account."""

        url = self.garmin_connect_devices_url
        logger.debug("Requesting devices")

        return self.connectapi(url)

    def get_device_settings(self, device_id: str) -> dict[str, Any]:
        """Return device settings for device with 'device_id'."""

        url = f"{self.garmin_connect_device_url}/device-info/settings/{device_id}"
        logger.debug("Requesting device settings")

        return self.connectapi(url)

    def get_primary_training_device(self) -> dict[str, Any]:
        """Return detailed information around primary training devices, included the specified device and the
        priority of all devices.
        """

        url = self.garmin_connect_primary_device_url
        logger.debug("Requesting primary training device information")

        return self.connectapi(url)

    def get_device_solar_data(
        self, device_id: str, startdate: str, enddate: str | None = None
    ) -> list[dict[str, Any]]:
        """Return solar data for compatible device with 'device_id'"""
        if enddate is None:
            enddate = startdate
            single_day = True
        else:
            single_day = False

        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        params = {"singleDayView": single_day}

        url = f"{self.garmin_connect_solar_url}/{device_id}/{startdate}/{enddate}"

        resp = self.connectapi(url, params=params)
        if not resp or "deviceSolarInput" not in resp:
            raise GarminConnectConnectionError("No device solar input data received")
        return resp["deviceSolarInput"]

    def get_device_alarms(self) -> list[Any]:
        """Get list of active alarms from all devices."""

        logger.debug("Requesting device alarms")

        alarms = []
        devices = self.get_devices()
        for device in devices:
            device_settings = self.get_device_settings(device["deviceId"])
            device_alarms = device_settings.get("alarms")
            if device_alarms is not None:
                alarms += device_alarms
        return alarms

    def get_device_last_used(self) -> dict[str, Any]:
        """Return device last used."""

        url = f"{self.garmin_connect_device_url}/mylastused"
        logger.debug("Requesting device last used")

        return self.connectapi(url)

    def get_activities(
        self,
        start: int = 0,
        limit: int = 20,
        activitytype: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Return available activities.
        :param start: Starting activity offset, where 0 means the most recent activity
        :param limit: Number of activities to return
        :param activitytype: (Optional) Filter activities by type
        :return: List of activities from Garmin
        """

        # Validate inputs
        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")

        if limit > MAX_ACTIVITY_LIMIT:
            raise ValueError(f"limit cannot exceed {MAX_ACTIVITY_LIMIT}")

        url = self.garmin_connect_activities
        params = {"start": str(start), "limit": str(limit)}
        if activitytype:
            params["activityType"] = str(activitytype)

        logger.debug("Requesting activities from %d with limit %d", start, limit)

        activities = self.connectapi(url, params=params)

        if activities is None:
            logger.warning("No activities data received")
            return []

        return activities

    def get_activities_fordate(self, fordate: str) -> dict[str, Any]:
        """Return available activities for date."""

        fordate = _validate_date_format(fordate, "fordate")
        url = f"{self.garmin_connect_activity_fordate}/{fordate}"
        logger.debug("Requesting activities for date %s", fordate)

        return self.connectapi(url)

    def set_activity_name(self, activity_id: str, title: str) -> Any:
        """Set name for activity with id."""

        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {"activityId": activity_id, "activityName": title}

        return self.garth.put("connectapi", url, json=payload, api=True)

    def set_activity_type(
        self,
        activity_id: str,
        type_id: int,
        type_key: str,
        parent_type_id: int,
    ) -> Any:
        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {
            "activityId": activity_id,
            "activityTypeDTO": {
                "typeId": type_id,
                "typeKey": type_key,
                "parentTypeId": parent_type_id,
            },
        }
        logger.debug("Changing activity type: %s", payload)
        return self.garth.put("connectapi", url, json=payload, api=True)

    def create_manual_activity_from_json(self, payload: dict[str, Any]) -> Any:
        url = f"{self.garmin_connect_activity}"
        logger.debug("Uploading manual activity: %s", str(payload))
        return self.garth.post("connectapi", url, json=payload, api=True)

    def create_manual_activity(
        self,
        start_datetime: str,
        time_zone: str,
        type_key: str,
        distance_km: float,
        duration_min: int,
        activity_name: str,
    ) -> Any:
        """
        Create a private activity manually with a few basic parameters.
        type_key - Garmin field representing type of activity. See https://connect.garmin.com/modern/main/js/properties/activity_types/activity_types.properties
                    Value to use is the key without 'activity_type_' prefix, e.g. 'resort_skiing'
        start_datetime - timestamp in this pattern "2023-12-02T10:00:00.000"
        time_zone - local timezone of the activity, e.g. 'Europe/Paris'
        distance_km - distance of the activity in kilometers
        duration_min - duration of the activity in minutes
        activity_name - the title
        """
        payload = {
            "activityTypeDTO": {"typeKey": type_key},
            "accessControlRuleDTO": {"typeId": 2, "typeKey": "private"},
            "timeZoneUnitDTO": {"unitKey": time_zone},
            "activityName": activity_name,
            "metadataDTO": {
                "autoCalcCalories": True,
            },
            "summaryDTO": {
                "startTimeLocal": start_datetime,
                "distance": distance_km * 1000,
                "duration": duration_min * 60,
            },
        }
        return self.create_manual_activity_from_json(payload)

    def get_last_activity(self) -> dict[str, Any] | None:
        """Return last activity."""

        activities = self.get_activities(0, 1)
        if activities and isinstance(activities, list) and len(activities) > 0:
            return activities[-1]
        elif (
            activities and isinstance(activities, dict) and "activityList" in activities
        ):
            activity_list = activities["activityList"]
            if activity_list and len(activity_list) > 0:
                return activity_list[-1]

        return None

    def upload_activity(self, activity_path: str) -> Any:
        """Upload activity in fit format from file."""
        # This code is borrowed from python-garminconnect-enhanced ;-)

        # Validate input
        if not activity_path:
            raise ValueError("activity_path cannot be empty")

        if not isinstance(activity_path, str):
            raise ValueError("activity_path must be a string")

        # Check if file exists
        p = Path(activity_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {activity_path}")

        # Check if it's actually a file
        if not p.is_file():
            raise ValueError(f"path is not a file: {activity_path}")

        file_base_name = p.name

        if not file_base_name:
            raise ValueError("invalid file path - no filename found")

        # More robust extension checking
        file_parts = file_base_name.split(".")
        if len(file_parts) < 2:
            raise GarminConnectInvalidFileFormatError(
                f"File has no extension: {activity_path}"
            )

        file_extension = file_parts[-1]
        allowed_file_extension = (
            file_extension.upper() in Garmin.ActivityUploadFormat.__members__
        )

        if allowed_file_extension:
            try:
                # Use context manager for file handling
                with p.open("rb") as file_handle:
                    files = {"file": (file_base_name, file_handle)}
                    url = self.garmin_connect_upload
                    return self.garth.post("connectapi", url, files=files, api=True)
            except OSError as e:
                raise GarminConnectConnectionError(
                    f"Failed to read file {activity_path}: {e}"
                ) from e
        else:
            allowed_formats = ", ".join(Garmin.ActivityUploadFormat.__members__.keys())
            raise GarminConnectInvalidFileFormatError(
                f"Invalid file format '{file_extension}'. Allowed formats: {allowed_formats}"
            )

    def delete_activity(self, activity_id: str) -> Any:
        """Delete activity with specified id"""

        url = f"{self.garmin_connect_delete_activity_url}/{activity_id}"
        logger.debug("Deleting activity with id %s", activity_id)

        return self.garth.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def get_activities_by_date(
        self,
        startdate: str,
        enddate: str | None = None,
        activitytype: str | None = None,
        sortorder: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch available activities between specific dates
        :param startdate: String in the format YYYY-MM-DD
        :param enddate: (Optional) String in the format YYYY-MM-DD
        :param activitytype: (Optional) Type of activity you are searching
                             Possible values are [cycling, running, swimming,
                             multi_sport, fitness_equipment, hiking, walking, other]
        :param sortorder: (Optional) sorting direction. By default, Garmin uses descending order by startLocal field.
                          Use "asc" to get activities from oldest to newest.
        :return: list of JSON activities
        """

        activities = []
        start = 0
        limit = 20
        # mimicking the behavior of the web interface that fetches
        # 20 activities at a time
        # and automatically loads more on scroll
        url = self.garmin_connect_activities
        startdate = _validate_date_format(startdate, "startdate")
        if enddate is not None:
            enddate = _validate_date_format(enddate, "enddate")
        params = {
            "startDate": startdate,
            "start": str(start),
            "limit": str(limit),
        }
        if enddate:
            params["endDate"] = enddate
        if activitytype:
            params["activityType"] = str(activitytype)
        if sortorder:
            params["sortOrder"] = str(sortorder)

        logger.debug("Requesting activities by date from %s to %s", startdate, enddate)
        while True:
            params["start"] = str(start)
            logger.debug("Requesting activities %d to %d", start, start + limit)
            act = self.connectapi(url, params=params)
            if act:
                activities.extend(act)
                start = start + limit
            else:
                break

        return activities

    def get_progress_summary_between_dates(
        self,
        startdate: str,
        enddate: str,
        metric: str = "distance",
        groupbyactivities: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch progress summary data between specific dates
        :param startdate: String in the format YYYY-MM-DD
        :param enddate: String in the format YYYY-MM-DD
        :param metric: metric to be calculated in the summary:
            "elevationGain", "duration", "distance", "movingDuration"
        :param groupbyactivities: group the summary by activity type
        :return: list of JSON activities with their aggregated progress summary
        """

        url = self.garmin_connect_fitnessstats
        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        params = {
            "startDate": str(startdate),
            "endDate": str(enddate),
            "aggregation": "lifetime",
            "groupByParentActivityType": str(groupbyactivities),
            "metric": str(metric),
        }

        logger.debug(
            "Requesting fitnessstats by date from %s to %s", startdate, enddate
        )
        return self.connectapi(url, params=params)

    def get_activity_types(self) -> dict[str, Any]:
        url = self.garmin_connect_activity_types
        logger.debug("Requesting activity types")
        return self.connectapi(url)

    def get_goals(
        self, status: str = "active", start: int = 1, limit: int = 30
    ) -> list[dict[str, Any]]:
        """
        Fetch all goals based on status
        :param status: Status of goals (valid options are "active", "future", or "past")
        :type status: str
        :param start: Initial goal index
        :type start: int
        :param limit: Pagination limit when retrieving goals
        :type limit: int
        :return: list of goals in JSON format
        """

        goals = []
        url = self.garmin_connect_goals_url
        valid_statuses = {"active", "future", "past"}
        if status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        params = {
            "status": status,
            "start": str(start),
            "limit": str(limit),
            "sortOrder": "asc",
        }

        logger.debug("Requesting %s goals", status)
        while True:
            params["start"] = str(start)
            logger.debug(
                "Requesting %s goals %d to %d", status, start, start + limit - 1
            )
            goals_json = self.connectapi(url, params=params)
            if goals_json:
                goals.extend(goals_json)
                start = start + limit
            else:
                break

        return goals

    def get_gear(self, userProfileNumber: str) -> dict[str, Any]:
        """Return all user gear."""
        url = f"{self.garmin_connect_gear}?userProfilePk={userProfileNumber}"
        logger.debug("Requesting gear for user %s", userProfileNumber)

        return self.connectapi(url)

    def get_gear_stats(self, gearUUID: str) -> dict[str, Any]:
        url = f"{self.garmin_connect_gear_baseurl}stats/{gearUUID}"
        logger.debug("Requesting gear stats for gearUUID %s", gearUUID)
        return self.connectapi(url)

    def get_gear_defaults(self, userProfileNumber: str) -> dict[str, Any]:
        url = (
            f"{self.garmin_connect_gear_baseurl}user/"
            f"{userProfileNumber}/activityTypes"
        )
        logger.debug("Requesting gear defaults for user %s", userProfileNumber)
        return self.connectapi(url)

    def set_gear_default(
        self, activityType: str, gearUUID: str, defaultGear: bool = True
    ) -> Any:
        defaultGearString = "/default/true" if defaultGear else ""
        method_override = "PUT" if defaultGear else "DELETE"
        url = (
            f"{self.garmin_connect_gear_baseurl}{gearUUID}/"
            f"activityType/{activityType}{defaultGearString}"
        )
        return self.garth.request(method_override, "connectapi", url, api=True)

    class ActivityDownloadFormat(Enum):
        """Activity variables."""

        ORIGINAL = auto()
        TCX = auto()
        GPX = auto()
        KML = auto()
        CSV = auto()

    class ActivityUploadFormat(Enum):
        FIT = auto()
        GPX = auto()
        TCX = auto()

    def download_activity(
        self,
        activity_id: str,
        dl_fmt: ActivityDownloadFormat = ActivityDownloadFormat.TCX,
    ) -> bytes:
        """
        Downloads activity in requested format and returns the raw bytes. For
        "Original" will return the zip file content, up to user to extract it.
        "CSV" will return a csv of the splits.
        """
        activity_id = str(activity_id)
        urls = {
            Garmin.ActivityDownloadFormat.ORIGINAL: f"{self.garmin_connect_fit_download}/{activity_id}",  # noqa
            Garmin.ActivityDownloadFormat.TCX: f"{self.garmin_connect_tcx_download}/{activity_id}",  # noqa
            Garmin.ActivityDownloadFormat.GPX: f"{self.garmin_connect_gpx_download}/{activity_id}",  # noqa
            Garmin.ActivityDownloadFormat.KML: f"{self.garmin_connect_kml_download}/{activity_id}",  # noqa
            Garmin.ActivityDownloadFormat.CSV: f"{self.garmin_connect_csv_download}/{activity_id}",  # noqa
        }
        if dl_fmt not in urls:
            raise ValueError(f"unexpected value {dl_fmt} for dl_fmt")
        url = urls[dl_fmt]

        logger.debug("Downloading activity from %s", url)

        return self.download(url)

    def get_activity_splits(self, activity_id: str) -> dict[str, Any]:
        """Return activity splits."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/splits"
        logger.debug("Requesting splits for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_typed_splits(self, activity_id: str) -> dict[str, Any]:
        """Return typed activity splits. Contains similar info to `get_activity_splits`, but for certain activity types
        (e.g., Bouldering), this contains more detail."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/typedsplits"
        logger.debug("Requesting typed splits for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_split_summaries(self, activity_id: str) -> dict[str, Any]:
        """Return activity split summaries."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/split_summaries"
        logger.debug("Requesting split summaries for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_weather(self, activity_id: str) -> dict[str, Any]:
        """Return activity weather."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/weather"
        logger.debug("Requesting weather for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_hr_in_timezones(self, activity_id: str) -> dict[str, Any]:
        """Return activity heartrate in timezones."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/hrTimeInZones"
        logger.debug("Requesting HR time-in-zones for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity(self, activity_id: str) -> dict[str, Any]:
        """Return activity summary, including basic splits."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}"
        logger.debug("Requesting activity summary data for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_details(
        self, activity_id: str, maxchart: int = 2000, maxpoly: int = 4000
    ) -> dict[str, Any]:
        """Return activity details."""

        activity_id = str(activity_id)
        maxchart = _validate_positive_integer(maxchart, "maxchart")
        maxpoly = _validate_positive_integer(maxpoly, "maxpoly")
        params = {"maxChartSize": str(maxchart), "maxPolylineSize": str(maxpoly)}
        url = f"{self.garmin_connect_activity}/{activity_id}/details"
        logger.debug("Requesting details for activity id %s", activity_id)

        return self.connectapi(url, params=params)

    def get_activity_exercise_sets(self, activity_id: int | str) -> dict[str, Any]:
        """Return activity exercise sets."""

        activity_id = _validate_positive_integer(int(activity_id), "activity_id")
        url = f"{self.garmin_connect_activity}/{activity_id}/exerciseSets"
        logger.debug("Requesting exercise sets for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_gear(self, activity_id: int | str) -> dict[str, Any]:
        """Return gears used for activity id."""

        activity_id = _validate_positive_integer(int(activity_id), "activity_id")
        params = {
            "activityId": str(activity_id),
        }
        url = self.garmin_connect_gear
        logger.debug("Requesting gear for activity_id %s", activity_id)

        return self.connectapi(url, params=params)

    def get_gear_activities(
        self, gearUUID: str, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Return activities where gear uuid was used.
        :param gearUUID: UUID of the gear to get activities for
        :param limit: Maximum number of activities to return (default: 1000)
        :return: List of activities where the specified gear was used
        """
        gearUUID = str(gearUUID)
        limit = _validate_positive_integer(limit, "limit")
        # Optional: enforce a reasonable ceiling to avoid heavy responses
        limit = min(limit, MAX_ACTIVITY_LIMIT)
        url = f"{self.garmin_connect_activities_baseurl}{gearUUID}/gear?start=0&limit={limit}"
        logger.debug("Requesting activities for gearUUID %s", gearUUID)

        return self.connectapi(url)

    def get_user_profile(self) -> dict[str, Any]:
        """Get all users settings."""

        url = self.garmin_connect_user_settings_url
        logger.debug("Requesting user profile.")

        return self.connectapi(url)

    def get_userprofile_settings(self) -> dict[str, Any]:
        """Get user settings."""

        url = self.garmin_connect_userprofile_settings_url
        logger.debug("Getting userprofile settings")

        return self.connectapi(url)

    def request_reload(self, cdate: str) -> dict[str, Any]:
        """
        Request reload of data for a specific date. This is necessary because
        Garmin offloads older data.
        """

        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_request_reload_url}/{cdate}"
        logger.debug("Requesting reload of data for %s.", cdate)

        return self.garth.post("connectapi", url, api=True).json()

    def get_workouts(self, start: int = 0, limit: int = 100) -> dict[str, Any]:
        """Return workouts starting at offset `start` with at most `limit` results."""

        url = f"{self.garmin_workouts}/workouts"
        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        logger.debug("Requesting workouts from %d with limit %d", start, limit)
        params = {"start": start, "limit": limit}
        return self.connectapi(url, params=params)

    def get_workout_by_id(self, workout_id: int | str) -> dict[str, Any]:
        """Return workout by id."""

        workout_id = _validate_positive_integer(int(workout_id), "workout_id")
        url = f"{self.garmin_workouts}/workout/{workout_id}"
        return self.connectapi(url)

    def download_workout(self, workout_id: int | str) -> bytes:
        """Download workout by id."""

        workout_id = _validate_positive_integer(int(workout_id), "workout_id")
        url = f"{self.garmin_workouts}/workout/FIT/{workout_id}"
        logger.debug("Downloading workout from %s", url)

        return self.download(url)

    def upload_workout(
        self, workout_json: dict[str, Any] | list[Any] | str
    ) -> dict[str, Any]:
        """Upload workout using json data."""

        url = f"{self.garmin_workouts}/workout"
        logger.debug("Uploading workout using %s", url)

        if isinstance(workout_json, str):
            import json as _json

            try:
                payload = _json.loads(workout_json)
            except Exception as e:
                raise ValueError(f"invalid workout_json string: {e}") from e
        else:
            payload = workout_json
        if not isinstance(payload, dict | list):
            raise ValueError("workout_json must be a JSON object or array")
        return self.garth.post("connectapi", url, json=payload, api=True).json()

    def get_menstrual_data_for_date(self, fordate: str) -> dict[str, Any]:
        """Return menstrual data for date."""

        fordate = _validate_date_format(fordate, "fordate")
        url = f"{self.garmin_connect_menstrual_dayview_url}/{fordate}"
        logger.debug("Requesting menstrual data for date %s", fordate)

        return self.connectapi(url)

    def get_menstrual_calendar_data(
        self, startdate: str, enddate: str
    ) -> dict[str, Any]:
        """Return summaries of cycles that have days between startdate and enddate."""

        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_menstrual_calendar_url}/{startdate}/{enddate}"
        logger.debug(
            "Requesting menstrual data for dates %s through %s", startdate, enddate
        )

        return self.connectapi(url)

    def get_pregnancy_summary(self) -> dict[str, Any]:
        """Return snapshot of pregnancy data"""

        url = f"{self.garmin_connect_pregnancy_snapshot_url}"
        logger.debug("Requesting pregnancy snapshot data")

        return self.connectapi(url)

    def query_garmin_graphql(self, query: dict[str, Any]) -> dict[str, Any]:
        """Execute a POST to Garmin's GraphQL endpoint.

        Args:
            query: A GraphQL request body, e.g. {"query": "...", "variables": {...}}
            See example.py for example queries.
        Returns:
            Parsed JSON response as a dict.
        """

        op = (
            (query.get("operationName") or "unnamed")
            if isinstance(query, dict)
            else "unnamed"
        )
        vars_keys = (
            sorted((query.get("variables") or {}).keys())
            if isinstance(query, dict)
            else []
        )
        logger.debug("Querying Garmin GraphQL op=%s vars=%s", op, vars_keys)
        return self.garth.post(
            "connectapi", self.garmin_graphql_endpoint, json=query
        ).json()

    def logout(self) -> None:
        """Log user out of session."""

        logger.warning(
            "Deprecated: Alternative is to delete the login tokens to logout."
        )

    def get_training_plans(self) -> dict[str, Any]:
        """Return all available training plans."""

        url = f"{self.garmin_training_plan_url}/plans"
        logger.debug("Requesting training plans.")
        return self.connectapi(url)

    def get_training_plan_by_id(self, plan_id: int | str) -> dict[str, Any]:
        """Return details for a specific training plan."""

        plan_id = _validate_positive_integer(int(plan_id), "plan_id")

        url = f"{self.garmin_training_plan_url}/plans/{plan_id}"
        logger.debug("Requesting training plan details for %s", plan_id)
        return self.connectapi(url)

    def get_adaptive_training_plan_by_id(self, plan_id: int | str) -> dict[str, Any]:
        """Return details for a specific adaptive training plan."""

        plan_id = _validate_positive_integer(int(plan_id), "plan_id")
        url = f"{self.garmin_training_plan_url}/fbt-adaptive/{plan_id}"

        logger.debug("Requesting adaptive training plan details for %s", plan_id)
        return self.connectapi(url)


class GarminConnectConnectionError(Exception):
    """Raised when communication ended in error."""


class GarminConnectTooManyRequestsError(Exception):
    """Raised when rate limit is exceeded."""


class GarminConnectAuthenticationError(Exception):
    """Raised when authentication is failed."""


class GarminConnectInvalidFileFormatError(Exception):
    """Raised when an invalid file format is passed to upload."""
