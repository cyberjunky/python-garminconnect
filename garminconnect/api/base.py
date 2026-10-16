"""Core of the Garmin Connect API wrapper: construction, login, transport and profile."""

import contextlib
import functools
import os
import time
from collections.abc import Callable
from datetime import UTC, date, datetime, tzinfo
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
from requests import HTTPError

from .. import client
from ..exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from ._common import (
    _coerce_positive_id,
    _handle_api_errors,
    _is_legacy_garth_tokenstore,
    _looks_like_json,
    _validate_date_format,
    logger,
)

if TYPE_CHECKING:
    from ..typed import TypedGarmin
    from . import Garmin


class GarminBase:
    """Shared state and core calls of :class:`garminconnect.Garmin`.

    The domain mixins in this package build on it; ``Garmin`` combines them.
    """

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

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        is_cn: bool = False,
        prompt_mfa: Callable[[], str] | None = None,
        return_on_mfa: bool = False,
        retry_attempts: int = 3,
        retry_min_wait: float = 1.0,
        retry_max_wait: float = 10.0,
        verify_login: bool = True,
    ) -> None:
        """Create a new class instance.

        :param retry_attempts: Retries for transient 5xx / network errors on
            ``connectapi``, ``connectwebproxy`` and ``download``. Defaults to
            ``3``; set to ``0`` to disable. 401, 429 and 4xx always fail fast
            regardless.
        :param retry_min_wait: Initial backoff in seconds; grows exponentially
            with jitter between attempts.
        :param retry_max_wait: Upper bound on the backoff in seconds.
        :param verify_login: When ``True`` (default), each login strategy's
            token is validated against the API tier before the chain accepts
            it, so a token the API rejects (401/403) is discarded and the next
            strategy is tried. Set ``False`` for the legacy "first token wins"
            behavior.
        """
        # Validate input types
        if email is not None and not isinstance(email, str):
            raise ValueError("email must be a string or None")
        if password is not None and not isinstance(password, str):
            raise ValueError("password must be a string or None")
        if not isinstance(is_cn, bool):
            raise ValueError("is_cn must be a boolean")
        if not isinstance(return_on_mfa, bool):
            raise ValueError("return_on_mfa must be a boolean")
        if isinstance(retry_attempts, bool) or not isinstance(retry_attempts, int):
            raise ValueError("retry_attempts must be an int")
        if retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")
        if not isinstance(verify_login, bool):
            raise ValueError("verify_login must be a boolean")

        self.username = email
        self.password = password
        self.is_cn = is_cn
        self.prompt_mfa = prompt_mfa
        self.return_on_mfa = return_on_mfa
        self.retry_attempts = retry_attempts
        self.retry_min_wait = float(retry_min_wait)
        self.retry_max_wait = float(retry_max_wait)
        self.verify_login = verify_login

        self.garmin_connect_user_settings_url = (
            "/userprofile-service/userprofile/user-settings"
        )
        self.garmin_connect_userprofile_settings_url = (
            "/userprofile-service/userprofile/settings"
        )
        self.garmin_connect_personal_information_url = (
            "/userprofile-service/userprofile/personal-information"
        )
        self.garmin_connect_devices_url = "/device-service/deviceregistration/devices"
        self.garmin_connect_device_url = "/device-service/deviceservice"

        self.garmin_connect_devicemessage_url = "/device-service/devicemessage/messages"

        self.garmin_connect_primary_device_url = (
            "/web-gateway/device-info/primary-training-device"
        )

        self.garmin_connect_solar_url = "/web-gateway/solar"
        self.garmin_connect_weight_url = "/weight-service"
        self.garmin_connect_daily_summary_url = "/usersummary-service/usersummary/daily"
        self.garmin_connect_metrics_url = "/metrics-service/metrics/maxmet/daily"
        self.garmin_connect_biometric_url = "/biometric-service/biometric"

        self.garmin_connect_biometric_stats_url = "/biometric-service/stats"
        self.garmin_connect_heart_rate_zones_url = "/biometric-service/heartRateZones"
        self.garmin_connect_power_zones_url = "/biometric-service/powerZones"
        self.garmin_connect_daily_hydration_url = (
            "/usersummary-service/usersummary/hydration/daily"
        )
        self.garmin_connect_set_hydration_url = (
            "/usersummary-service/usersummary/hydration/log"
        )
        self.garmin_connect_daily_stats_steps_url = (
            "/usersummary-service/stats/steps/daily"
        )
        self.garmin_connect_weekly_stats_steps_url = (
            "/usersummary-service/stats/steps/weekly"
        )
        self.garmin_connect_weekly_stats_stress_url = (
            "/usersummary-service/stats/stress/weekly"
        )
        self.garmin_connect_weekly_stats_intensity_minutes_url = (
            "/usersummary-service/stats/im/weekly"
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
        self.garmin_connect_running_tolerance_url = (
            "/metrics-service/metrics/runningtolerance/stats"
        )
        self.garmin_connect_menstrual_calendar_url = (
            "/periodichealth-service/menstrualcycle/calendar"
        )

        self.garmin_connect_menstrual_cycle_url = (
            "/periodichealth-service/menstrualcycle"
        )
        self.garmin_connect_menstrual_dayview_url = (
            "/periodichealth-service/menstrualcycle/dayview"
        )
        self.garmin_connect_menstrual_dailylog_url = (
            "/periodichealth-service/menstrualcycle/dailylog"
        )
        self.garmin_connect_menstrual_calendar_updates_url = (
            "/periodichealth-service/menstrualcycle/calendarupdates"
        )
        self.garmin_connect_menstrual_init_cycle_setup_url = (
            "/periodichealth-service/menstrualcycle/initCycleSetup"
        )
        self.garmin_connect_menstrual_lastconfirmed_url = (
            "/periodichealth-service/menstrualcycle/lastconfirmed"
        )
        self.garmin_connect_menstrual_summary_url = (
            "/periodichealth-service/menstrualcycle/summary"
        )
        self.garmin_connect_menstrual_reports_url = (
            "/periodichealth-service/reports/menstrualcycle"
        )
        self.garmin_connect_pregnancy_snapshot_url = (
            "/periodichealth-service/menstrualcycle/pregnancysnapshot"
        )
        self.garmin_connect_jetlag_trip_url = "/jetlag-service/jetlag/trip"
        self.garmin_connect_goals_url = "/goal-service/goal/goals"

        self.garmin_connect_rhr_url = "/userstats-service/wellness/daily"

        self.garmin_connect_hrv_url = "/hrv-service/hrv"

        self.garmin_connect_training_readiness_url = (
            "/metrics-service/metrics/trainingreadiness"
        )

        self.garmin_connect_training_load_balance_url = (
            "/metrics-service/metrics/trainingloadbalance"
        )
        self.garmin_connect_daily_training_status_url = (
            "/metrics-service/metrics/trainingstatus/daily"
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
        self.garmin_connect_activities_count = "/activitylist-service/activities/count"
        self.garmin_connect_activities_baseurl = "/activitylist-service/activities/"
        self.garmin_connect_activity = "/activity-service/activity"
        self.garmin_connect_activity_types = "/activity-service/activity/activityTypes"
        self.garmin_connect_activity_fordate = "/mobile-gateway/heartRate/forDate"
        self.garmin_connect_fitnessstats = "/fitnessstats-service/activity"
        self.garmin_connect_fitnessage = "/fitnessage-service/fitnessage"

        self.garmin_connect_fit_download = "/download-service/files/activity"
        self.garmin_connect_health_snapshot_download = (
            "/download-service/files/wellness"
        )
        self.garmin_connect_tcx_download = "/download-service/export/tcx/activity"
        self.garmin_connect_gpx_download = "/download-service/export/gpx/activity"
        self.garmin_connect_kml_download = "/download-service/export/kml/activity"
        self.garmin_connect_csv_download = "/download-service/export/csv/activity"

        self.garmin_connect_upload = "/upload-service/upload"

        self.garmin_connect_gear = "/gear-service/gear/filterGear"
        self.garmin_connect_gear_baseurl = "/gear-service/gear"

        self.garmin_request_reload_url = "/wellness-service/wellness/epoch/request"

        self.garmin_workouts = "/workout-service"

        self.garmin_workouts_schedule_url = f"{self.garmin_workouts}/schedule"

        self.garmin_calendar = "/calendar-service"
        self.garmin_scheduled_workouts_url = f"{self.garmin_calendar}"

        self.garmin_nutrition = "/nutrition-service"

        self.garmin_connect_nutrition_daily_food_logs = (
            f"{self.garmin_nutrition}/food/logs"
        )
        self.garmin_connect_nutrition_daily_meals = f"{self.garmin_nutrition}/meals"
        self.garmin_connect_nutrition_daily_settings = (
            f"{self.garmin_nutrition}/settings"
        )

        self.garmin_golf = "/gcs-golfcommunity/api/v2"
        self.garmin_golf_scorecard_summary = f"{self.garmin_golf}/scorecard/summary"
        self.garmin_golf_scorecard_detail = f"{self.garmin_golf}/scorecard/detail"
        self.garmin_golf_shot = f"{self.garmin_golf}/shot/scorecard"
        self.garmin_golf_club_stats = f"{self.garmin_golf}/club/player"
        self.garmin_golf_user_stats = f"{self.garmin_golf}/player/stats"

        self.garmin_connect_delete_activity_url = "/activity-service/activity"

        self.garmin_graphql_endpoint = "graphql-gateway/graphql"

        self.garmin_connect_training_plan_url = "/trainingplan-service/trainingplan"

        self.garmin_connect_daily_lifestyle_logging_url = (
            "/lifestylelogging-service/dailyLog"
        )

        # Service roots for the endpoints mapped from the Garmin Connect web
        # app (see docs/API_ENDPOINTS.md).
        self.garmin_connect_metrics_base_url = "/metrics-service/metrics"
        self.garmin_connect_biometric_service_url = "/biometric-service"
        self.garmin_connect_fitnessstats_service_url = "/fitnessstats-service"
        self.garmin_connect_fitnessage_service_url = "/fitnessage-service"
        self.garmin_connect_personal_record_service_url = "/personalrecord-service"
        self.garmin_connect_usersummary_url = "/usersummary-service/usersummary"
        self.garmin_connect_usersummary_stats_url = "/usersummary-service/stats"
        self.garmin_connect_usersummary_v2_url = "/usersummary-service/v2"
        self.garmin_connect_wellness_url = "/wellness-service/wellness"
        self.garmin_connect_wellness_stats_url = "/wellness-service/stats"
        self.garmin_connect_userstats_url = "/userstats-service"
        self.garmin_connect_sleep_service_url = "/sleep-service"
        self.garmin_connect_health_snapshot_url = "/wellnessactivity-service/activity"
        self.garmin_connect_nutrition_url = "/nutrition-service"
        self.garmin_connect_blood_pressure_url = "/bloodpressure-service/bloodpressure"
        self.garmin_connect_goal_service_url = "/goal-service/goal"
        self.garmin_connect_badge_url = "/badge-service/badge"
        self.garmin_connect_badge_challenge_url = "/badgechallenge-service"
        self.garmin_connect_adhoc_challenge_url = (
            "/adhocchallenge-service/adHocChallenge"
        )
        self.garmin_connect_userprofile_url = "/userprofile-service/userprofile"
        self.garmin_connect_userprofile_service_url = "/userprofile-service"
        self.garmin_connect_privacy_settings_url = (
            "/privacysettings-service/privacy-settings"
        )
        self.garmin_connect_jetlag_url = "/jetlag-service/jetlag"
        self.garmin_connect_ecg_url = (
            f"https://ghs.{'garmin.cn' if is_cn else 'garmin.com'}/ghs/ecg/v1/ecg"
        )
        self.garmin_connect_activitylist_url = "/activitylist-service/activities"
        self.garmin_connect_gear_service_url = "/gear-service"
        self.garmin_connect_device_service_url = "/device-service"
        self.garmin_connect_devicesettings_url = "/devicesettings-service/device"
        self.garmin_connect_web_gateway_url = "/web-gateway"
        self.garmin_connect_workout_service_url = "/workout-service"
        self.garmin_connect_calendar_url = "/calendar-service"
        self.garmin_connect_course_url = "/course-service/course"
        self.garmin_connect_pacebands_url = "/course-service/pacebands"
        self.garmin_connect_segment_url = "/segment-service"
        self.garmin_connect_report_export_url = "/reportexport-service/export"

        self.client = client.Client(
            domain="garmin.cn" if is_cn else "garmin.com",
            pool_connections=20,
            pool_maxsize=20,
            verify_login=verify_login,
        )

        self.display_name: str | None = None
        self.full_name: str | None = None
        self.unit_system: str | None = None
        self.profile_id: int | None = None
        # IANA timezone from the Garmin profile (e.g. "Europe/Paris"). Loaded
        # lazily by get_user_timezone(); None until then or when unavailable.
        self.time_zone: str | None = None
        self._time_zone_loaded = False

    @functools.cached_property
    def typed(self) -> "TypedGarmin":
        """Return a typed namespace that wraps selected endpoints with Pydantic models.

        Example::

            g = Garmin(email, password)
            g.login()
            stats = g.typed.get_stats("2026-04-21")  # DailyStats

        Requires the optional ``typed`` extra::

            pip install 'garminconnect[typed]'

        See :mod:`garminconnect.typed` for the list of wrapped endpoints and
        response models. **Experimental** — shapes may change between minor
        releases.
        """
        # Lazy import so pydantic stays an optional dep. The typed module
        # raises a clear ImportError on its own if pydantic is missing.
        from ..typed import TypedGarmin

        return TypedGarmin(cast("Garmin", self))

    @_handle_api_errors("API call")
    def connectapi(self, path: str, **kwargs: Any) -> Any:
        """Send a GET to a Connect API path and return the decoded JSON."""
        return self.client.connectapi(path, **kwargs)

    @_handle_api_errors("Web proxy call")
    def connectwebproxy(self, path: str, **kwargs: Any) -> Any:
        """Send a GET to a Connect API path (legacy alias of `connectapi`)."""
        return self.client.request("GET", "connect", path, **kwargs).json()

    @_handle_api_errors("Download")
    def download(self, path: str, **kwargs: Any) -> Any:
        """Download raw bytes from a Connect API path."""
        return self.client.download(path, **kwargs)

    def login(self, /, tokenstore: str | None = None) -> tuple[str | None, str | None]:
        """Log in with saved tokens or credentials and load the user profile.

        Returns:
            Tuple[str | None, str | None]: (needs_mfa, None) when MFA is required;
            (None, None) on clean successful login.

        """
        tokenstore = tokenstore or os.getenv("GARMINTOKENS")

        try:
            mfa_status = None
            _legacy_token = None

            # Try to load tokens from tokenstore if provided
            tokens_loaded = False
            tokenstore_path = None
            if tokenstore:
                try:
                    if _looks_like_json(tokenstore):
                        # Token data is provided directly as string
                        self.client.loads(tokenstore)
                    else:
                        # Tokenstore is a path - expand ~ for cross-platform
                        # compatibility. Deliberately NOT .resolve()d: resolve()
                        # follows symlinks, which would let a pre-planted
                        # tokenstore symlink reach client.load()/dump() as an
                        # ordinary path with the symlink already gone, bypassing
                        # token_file_path()'s anti-symlink check entirely.
                        # token_file_path() expands and validates the raw path
                        # itself; logout() already relies on that instead of
                        # resolving here.
                        tokenstore_path = str(Path(tokenstore).expanduser())
                        normalized_path = tokenstore_path
                        logger.debug(
                            f"Loading tokens from normalized path: {normalized_path}"
                        )
                        self.client.load(normalized_path)
                    tokens_loaded = True

                    # Proactively refresh DI token if it's expired or about to expire.
                    # This avoids hitting the SSO login endpoint (which may be
                    # Cloudflare-blocked) when a simple DI refresh would suffice.
                    with self.client._token_lock:
                        if (
                            self.client.di_refresh_token
                            and self.client._token_expires_soon()
                        ):
                            logger.debug("Token expiring soon, refreshing proactively")
                            self.client._refresh_session()

                except Exception as e:
                    # Never log the raw tokenstore value: it may be the inline
                    # token JSON (and thus the refresh token). Log only the
                    # source type, length, and the parse error.
                    source = "inline-json" if _looks_like_json(tokenstore) else "path"
                    logger.debug(
                        "Failed to cleanly load tokens (source=%s, len=%d): %s",
                        source,
                        len(tokenstore),
                        e,
                    )
                    tokens_loaded = False

            # If tokens weren't loaded (or failed to load), use credentials
            if not tokens_loaded:
                # Validate credentials before attempting login
                if not self.username or not self.password:
                    if tokenstore_path is not None and _is_legacy_garth_tokenstore(
                        tokenstore_path
                    ):
                        raise GarminConnectAuthenticationError(
                            "Found old garth-format tokens (oauth1_token.json/"
                            "oauth2_token.json), which are no longer supported. "
                            "Log in once with username and password to create "
                            "new tokens."
                        )
                    raise GarminConnectAuthenticationError(
                        "Username and password are required"
                    )

                if self.return_on_mfa:
                    mfa_status, _legacy_token = self.client.login(
                        self.username,
                        self.password,
                        return_on_mfa=self.return_on_mfa,
                    )
                    # In MFA early-return mode, profile/settings are not loaded yet
                    return mfa_status, _legacy_token
                if tokenstore_path is not None:
                    self.client._tokenstore_path = tokenstore_path
                mfa_status, _legacy_token = self.client.login(
                    self.username,
                    self.password,
                    prompt_mfa=self.prompt_mfa,
                )
                # Persist tokens so next run restores without re-login/MFA
                if tokenstore_path is not None:
                    with contextlib.suppress(Exception):
                        self.client.dump(tokenstore_path)
                # Continue to load profile/settings below

            # Ensure profile is loaded (tokenstore path may not populate it).
            try:
                self._load_profile_and_settings()
            except GarminConnectAuthenticationError:
                # If we resumed from cached tokens and the API rejects them,
                # the cache is stale/poisoned (e.g. a token whose audience the
                # API tier no longer accepts — see #369). Discard it and run a
                # full credential login so the strategy chain can find a token
                # the API accepts. Without this, a poisoned cache silently
                # short-circuits the chain on every run.
                username, password = self.username, self.password
                if not (
                    tokens_loaded and username and password and not self.return_on_mfa
                ):
                    raise
                logger.warning(
                    "Cached tokens were rejected by the API; discarding and "
                    "performing a fresh login."
                )
                self.client._clear_auth_state()
                if tokenstore_path is not None:
                    self.client._tokenstore_path = tokenstore_path
                mfa_status, _legacy_token = self.client.login(
                    username,
                    password,
                    prompt_mfa=self.prompt_mfa,
                )
                if tokenstore_path is not None:
                    with contextlib.suppress(Exception):
                        self.client.dump(tokenstore_path)
                self._load_profile_and_settings()

            # Successful authentication no longer needs the plaintext password.
            # Keeping it would enlarge the credential exposure window (heap dumps,
            # serialization, debug output) for the lifetime of the object.
            self.password = None

            return mfa_status, _legacy_token

        except (
            HTTPError,
            requests.exceptions.HTTPError,
            GarminConnectConnectionError,
        ) as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            error_str = str(e).lower()
            # Re-raised below with a clean message; avoid logging a full
            # traceback for expected failures (rate limits, bot challenges).
            logger.debug("Login failed: %s (status=%s)", e, status)

            if status == 429 or "429" in error_str:
                raise GarminConnectTooManyRequestsError(
                    "Too many login attempts. Please wait a few minutes "
                    "before trying again."
                ) from e

            if status == 401 or "401" in error_str or "unauthorized" in error_str:
                raise GarminConnectAuthenticationError(
                    "Authentication failed (401 Unauthorized). "
                    "Possible causes:\n"
                    "  • Incorrect email or password\n"
                    "  • Account locked — check https://sso.garmin.com\n"
                    "  • Garmin SSO service is temporarily unavailable\n"
                    f"Original error: {e}"
                ) from e

            auth_indicators = ["unauthorized", "authentication failed"]
            if any(indicator in error_str for indicator in auth_indicators):
                raise GarminConnectAuthenticationError(
                    f"Authentication failed: {e}"
                ) from e

            raise GarminConnectConnectionError(f"Login failed: {e}") from e
        except FileNotFoundError:
            raise
        except (GarminConnectTooManyRequestsError, GarminConnectAuthenticationError):
            raise
        except Exception as e:
            error_str = str(e).lower()
            auth_indicators = ["401", "unauthorized", "authentication", "login failed"]
            if any(indicator in error_str for indicator in auth_indicators):
                raise GarminConnectAuthenticationError(
                    f"Authentication failed: {e}"
                ) from e
            logger.debug("Login failed: %s", e)
            raise GarminConnectConnectionError(f"Login failed: {e}") from e

    def _load_social_profile(self) -> None:
        """Fetch the social profile, populating display name and full name.

        A response without a usable ``displayName`` is retried, because the
        display name is needed to build most API URLs. If it is still missing
        after three attempts the profile is accepted as is (new or empty
        Garmin profiles may legitimately lack one) and the username is used
        as fallback. Raises ``GarminConnectAuthenticationError`` if no
        profile could be retrieved at all.
        """
        prof = None
        name = None
        for attempt in range(3):
            try:
                prof = self.client.connectapi("/userprofile-service/socialProfile")
                name = prof.get("displayName") if isinstance(prof, dict) else None
                if isinstance(name, str) and name.strip():
                    break
                name = None
                logger.debug(
                    "Social profile has no usable displayName (attempt %d)", attempt + 1
                )
            except Exception as e:
                if attempt == 2:
                    raise GarminConnectAuthenticationError(
                        "Failed to retrieve social profile"
                    ) from e
                logger.debug("Retrying social profile fetch: %s", e)
            if attempt < 2:
                time.sleep(1)
        if not isinstance(prof, dict):
            raise GarminConnectAuthenticationError("Invalid profile data found")

        self.display_name = name or self.username
        self.full_name = prof.get("fullName", "")
        profile_id = prof.get("profileId")
        self.profile_id = profile_id if isinstance(profile_id, int) else None

    def _load_profile_and_settings(self) -> None:
        """Fetch social profile and user settings, populating display name,
        full name and unit system. Raises ``GarminConnectAuthenticationError``
        if either cannot be retrieved (e.g. the token is rejected).
        """
        self._load_social_profile()

        settings = None
        for attempt in range(3):
            try:
                settings = self.client.connectapi(self.garmin_connect_user_settings_url)
                if settings and isinstance(settings, dict) and "userData" in settings:
                    break
            except Exception as e:
                if attempt == 2:
                    raise GarminConnectAuthenticationError(
                        "Failed to retrieve user settings"
                    ) from e
                logger.debug("Retrying user settings fetch: %s", e)
                time.sleep(1)
        else:
            raise GarminConnectAuthenticationError("Invalid user settings found")

        self.unit_system = settings["userData"].get("measurementSystem")

    def resume_login(
        self, client_state: dict[str, Any], mfa_code: str
    ) -> tuple[Any, Any]:
        """Finish a login that is waiting for an MFA code."""
        mfa_status, _legacy_token = self.client.resume_login(client_state, mfa_code)

        # The client already verifies the token against the API tier; if we reach
        # this point the token is good. Load profile/settings normally and let
        # any failure propagate so callers don't think the login succeeded.
        self._load_profile_and_settings()

        return mfa_status, _legacy_token

    def _require_display_name(self) -> str:
        """Return display_name, URL-encoded, reloading the profile if unset.

        A missing displayName would cause 'None' to be interpolated into
        API URLs and result in 403 Forbidden errors, so one reload is
        attempted before giving up.

        Encoding the value before it enters a URL path prevents a
        compromised or malicious server response from injecting path
        separators or query/fragment characters via displayName.
        """
        if not self.display_name:
            try:
                self._load_social_profile()
            except Exception as e:
                raise GarminConnectConnectionError(
                    "Could not load the Garmin social profile, so the display "
                    "name required for this request is unavailable. "
                    "Please log in again."
                ) from e
        if not self.display_name:
            raise GarminConnectConnectionError(
                "Display name is not set. Your Garmin profile did not include "
                "a display name, so this request cannot be made."
            )
        return quote(self.display_name, safe="")

    def get_full_name(self) -> str | None:
        """Return full name of the authenticated user."""
        return self.full_name

    def get_unit_system(self) -> str | None:
        """Return the user's unit system (e.g. metric)."""
        return self.unit_system

    def get_user_timezone(self) -> str | None:
        """Return the IANA timezone name from the user's Garmin profile.

        Garmin evaluates "today" (``calendarDate``) in this timezone, not in
        the timezone of the machine running this library. The value is read
        once from the personal-information endpoint and cached on
        ``self.time_zone``. Returns None when it cannot be determined (not
        logged in, or the endpoint is unavailable); callers then fall back to
        the machine's local timezone.
        """
        if self.time_zone or self._time_zone_loaded:
            return self.time_zone
        if not self.display_name:
            return None
        self._time_zone_loaded = True
        try:
            info = self.client.connectapi(
                f"{self.garmin_connect_personal_information_url}/"
                f"{self._require_display_name()}"
            )
        except Exception as e:  # best effort, never block callers
            logger.debug("Could not fetch user timezone: %s", e)
            return None
        tz = info.get("timeZone") if isinstance(info, dict) else None
        self.time_zone = tz if isinstance(tz, str) and tz else None
        return self.time_zone

    def _user_tzinfo(self) -> tzinfo:
        """Return tzinfo for the user's Garmin timezone (machine-local fallback)."""
        name = self.get_user_timezone()
        if name:
            try:
                return ZoneInfo(name)
            except Exception:  # unknown zone or missing tzdata
                logger.debug("Unknown timezone %r; using machine local time", name)
        local = datetime.now().astimezone().tzinfo
        return local if local is not None else UTC

    def _localize(self, dt: datetime) -> datetime:
        """Attach the user's timezone to a naive datetime; keep aware ones as-is."""
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=self._user_tzinfo())

    def now(self) -> datetime:
        """Return the current time as an aware datetime in the user's timezone."""
        return datetime.now(self._user_tzinfo())

    def today(self) -> date:
        """Return today's calendar date in the user's Garmin timezone.

        Prefer this over ``date.today()`` when building ``cdate`` arguments:
        on a host running in UTC the machine date lags the user's real day by
        several hours every evening (and leads it in western timezones), so
        "today" requests silently return yesterday's data.
        """
        return self.now().date()

    def get_user_profile(self) -> dict[str, Any]:
        """Return the user settings (user data, units, formats, sleep times)."""
        url = self.garmin_connect_user_settings_url
        logger.debug("Requesting user profile.")

        return self.connectapi(url)

    def get_userprofile_settings(self) -> dict[str, Any]:
        """Return the user profile settings (display name, locale, preferences)."""
        url = self.garmin_connect_userprofile_settings_url
        logger.debug("Getting userprofile settings")

        return self.connectapi(url)

    def update_user_settings(self, settings: dict[str, Any]) -> Any:
        """Write user settings (units, formats, sleep times, training days, ...).

        PUT /userprofile-service/userprofile/user-settings/ with the settings
        object from :meth:`get_user_profile`; ``settings`` is overlaid on the
        current object so only the given keys change. ``userData`` is itself
        a dict and is merged one level deep, e.g.
        ``update_user_settings({"userData": {"measurementSystem": "metric"}})``.
        Verified live with an unchanged object (204).
        """
        if not isinstance(settings, dict) or not settings:
            raise ValueError("settings must be a non-empty dictionary")
        current = self.get_user_profile()
        payload: dict[str, Any] = dict(current) if isinstance(current, dict) else {}
        for key, value in settings.items():
            if isinstance(value, dict) and isinstance(payload.get(key), dict):
                payload[key] = {**payload[key], **value}
            else:
                payload[key] = value
        logger.debug("Updating user settings: %s", sorted(settings))
        return self._json_or_none(
            self.client.put(
                "connectapi", self.garmin_connect_user_settings_url, json=payload
            )
        )

    def set_primary_training_device(self, device_id: int | str) -> Any:
        """Choose which device Garmin treats as the primary training device.

        PUT /userprofile-service/userprofile/user-settings/primary-training-device
        with ``{"deviceId": id}``. Verified live.
        """
        device_id = _coerce_positive_id(device_id, "device_id")
        url = f"{self.garmin_connect_user_settings_url}/primary-training-device"
        logger.debug("Setting primary training device %s", device_id)
        return self._json_or_none(
            self.client.put("connectapi", url, json={"deviceId": device_id})
        )

    def request_reload(
        self, cdate: str, device_id: int | str | None = None
    ) -> dict[str, Any]:
        """Request reload of data for a specific date. This is necessary because
        Garmin offloads older data.

        ``device_id`` optionally limits the reload to one device (the web app
        appends it as an extra path segment).
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_request_reload_url}/{cdate}"
        if device_id is not None:
            url += f"/{_coerce_positive_id(device_id, 'device_id')}"
        logger.debug("Requesting reload of data for %s.", cdate)

        return self.client.post("connectapi", url, api=True)

    def query_garmin_graphql(self, query: dict[str, Any]) -> dict[str, Any]:
        """Run a query against Garmin's GraphQL gateway.

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
        return self.client.post(
            "connectapi", self.garmin_graphql_endpoint, json=query
        ).json()

    def _date_or_today(self, cdate: str | None, name: str = "cdate") -> str:
        """Validate ``cdate`` or default to today in the user's timezone."""
        if cdate is None:
            return self.today().isoformat()
        return _validate_date_format(cdate, name)

    def _json_or_none(self, resp: Any) -> Any:
        """Return the JSON body of a write response, or None for 204/empty."""
        if resp is None or getattr(resp, "status_code", None) == 204:
            return None
        if not getattr(resp, "content", b""):
            return None
        return resp.json()

    def get_personal_information(
        self, include_biometric: bool = True, include_vo2max: bool = True
    ) -> dict[str, Any]:
        """Return personal information: ``userInfo`` (birth date, gender, locale,
        timeZone, country), ``biometricProfile`` and VO2 max.

        GET /userprofile-service/userprofile/personal-information/{displayName}
        ?includeBiometric&includeVO2Max.
        """
        url = f"{self.garmin_connect_personal_information_url}/{self._require_display_name()}"
        params = {
            "includeBiometric": str(bool(include_biometric)).lower(),
            "includeVO2Max": str(bool(include_vo2max)).lower(),
        }
        logger.debug("Requesting personal information")
        return self.connectapi(url, params=params)

    def get_user_profile_base(self) -> dict[str, Any]:
        """Return the base profile record (names, birth date, create date, ...).

        GET /userprofile-service/userprofile/userProfileBase.
        """
        url = f"{self.garmin_connect_userprofile_url}/userProfileBase"
        logger.debug("Requesting user profile base")
        return self.connectapi(url)

    def get_privacy_settings(self) -> dict[str, Any]:
        """Return the account's activity, profile and wellness privacy settings.

        GET /privacysettings-service/privacy-settings.
        """
        logger.debug("Requesting privacy settings")
        return self.connectapi(self.garmin_connect_privacy_settings_url)

    def get_usage_indicators(self) -> dict[str, Any]:
        """Return which features the account's devices and data support.

        GET /web-gateway/snapshot/usageIndicators — handy to decide which
        metrics are worth requesting for this user.
        """
        url = f"{self.garmin_connect_web_gateway_url}/snapshot/usageIndicators"
        logger.debug("Requesting usage indicators")
        return self.connectapi(url)

    def logout(self, tokenstore: str | None = None) -> None:
        """Clear in-memory auth state and any cached tokens on disk.

        Call this after an authentication failure to guarantee the next
        ``login()`` runs the full strategy chain instead of resuming
        stale/poisoned cached tokens. ``login()`` already self-heals from
        rejected cached tokens, so this is only needed for manual control.

        This only clears local authentication state. It does not revoke an
        already-issued token at Garmin. The token-store directory and any
        unrelated files in it are preserved.

        :param tokenstore: Path to the token directory or JSON file whose
            ``garmin_tokens.json`` file should be removed. Falls back to the
            ``GARMINTOKENS`` environment variable. Inline JSON token strings
            are ignored — nothing to delete.
        """
        self.client._clear_auth_state()
        self.username = None
        self.password = None
        self.display_name = None
        self.full_name = None
        self.unit_system = None
        self.profile_id = None
        self.time_zone = None
        self._time_zone_loaded = False

        tokenstore = tokenstore or os.getenv("GARMINTOKENS")
        if not tokenstore or _looks_like_json(tokenstore):
            return
        try:
            path = client.token_file_path(tokenstore)
            path.unlink()
        except FileNotFoundError:
            pass
        except ValueError as e:
            logger.debug("Skipping tokenstore cleanup for unsafe path: %s", e)

    # --- methods provided by the domain mixins (keeps the mixins type-checkable)

    def _activity_subresource(self, *args: Any, **kwargs: Any) -> Any:
        """Implemented by ActivitiesMixin; declared here for the mixins."""
        raise NotImplementedError

    def get_stats(self, *args: Any, **kwargs: Any) -> Any:
        """Implemented by HealthMixin; declared here for the mixins."""
        raise NotImplementedError

    def get_workout_by_id(self, *args: Any, **kwargs: Any) -> Any:
        """Implemented by WorkoutsMixin; declared here for the mixins."""
        raise NotImplementedError

    def get_workouts(self, *args: Any, **kwargs: Any) -> Any:
        """Implemented by WorkoutsMixin; declared here for the mixins."""
        raise NotImplementedError
