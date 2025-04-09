"""Python 3 API wrapper for Garmin Connect."""

import logging
import os
from datetime import date, datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional

import garth
from withings_sync import fit

logger = logging.getLogger(__name__)

# Temp fix for API change!
garth.http.USER_AGENT = {"User-Agent": "GCM-iOS-5.7.2.1"}


class Garmin:
    """Class for fetching data from Garmin Connect."""

    def __init__(
        self, email=None, password=None, is_cn=False, prompt_mfa=None
    ):
        """Create a new class instance."""
        self.username = email
        self.password = password
        self.is_cn = is_cn
        self.prompt_mfa = prompt_mfa

        self.garmin_connect_user_settings_url = (
            "/userprofile-service/userprofile/user-settings"
        )
        self.garmin_connect_userprofile_settings_url = (
            "/userprofile-service/userprofile/settings"
        )
        self.garmin_connect_devices_url = (
            "/device-service/deviceregistration/devices"
        )
        self.garmin_connect_device_url = "/device-service/deviceservice"

        self.garmin_connect_primary_device_url = (
            "/web-gateway/device-info/primary-training-device"
        )

        self.garmin_connect_solar_url = "/web-gateway/solar"
        self.garmin_connect_weight_url = "/weight-service"
        self.garmin_connect_daily_summary_url = (
            "/usersummary-service/usersummary/daily"
        )
        self.garmin_connect_metrics_url = (
            "/metrics-service/metrics/maxmet/daily"
        )
        self.garmin_connect_daily_hydration_url = (
            "/usersummary-service/usersummary/hydration/daily"
        )
        self.garmin_connect_set_hydration_url = (
            "usersummary-service/usersummary/hydration/log"
        )
        self.garmin_connect_daily_stats_steps_url = (
            "/usersummary-service/stats/steps/daily"
        )
        self.garmin_connect_personal_record_url = (
            "/personalrecord-service/personalrecord/prs"
        )
        self.garmin_connect_earned_badges_url = "/badge-service/badge/earned"
        self.garmin_connect_adhoc_challenges_url = (
            "/adhocchallenge-service/adHocChallenge/historical"
        )
        self.garmin_connect_adhoc_challenges_url = (
            "/adhocchallenge-service/adHocChallenge/historical"
        )
        self.garmin_connect_adhoc_challenge_url = (
            "/adhocchallenge-service/adHocChallenge/"
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
        self.garmin_connect_daily_stress_url = (
            "/wellness-service/wellness/dailyStress"
        )
        self.garmin_connect_hill_score_url = (
            "/metrics-service/metrics/hillscore"
        )

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
            "periodichealth-service/menstrualcycle/pregnancysnapshot"
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
        self.garmin_connect_daily_spo2_url = (
            "/wellness-service/wellness/daily/spo2"
        )
        self.garmin_connect_daily_intensity_minutes = (
            "/wellness-service/wellness/daily/im"
        )
        self.garmin_all_day_stress_url = (
            "/wellness-service/wellness/dailyStress"
        )
        self.garmin_daily_events_url = "/wellness-service/wellness/dailyEvents"
        self.garmin_connect_activities = (
            "/activitylist-service/activities/search/activities"
        )
        self.garmin_connect_activities_baseurl = (
            "/activitylist-service/activities/"
        )
        self.garmin_connect_activity = "/activity-service/activity"
        self.garmin_connect_activity_types = (
            "/activity-service/activity/activityTypes"
        )
        self.garmin_connect_activity_fordate = (
            "/mobile-gateway/heartRate/forDate"
        )
        self.garmin_connect_fitnessstats = "/fitnessstats-service/activity"
        self.garmin_connect_fitnessage = "/fitnessage-service/fitnessage"

        self.garmin_connect_fit_download = "/download-service/files/activity"
        self.garmin_connect_tcx_download = (
            "/download-service/export/tcx/activity"
        )
        self.garmin_connect_gpx_download = (
            "/download-service/export/gpx/activity"
        )
        self.garmin_connect_kml_download = (
            "/download-service/export/kml/activity"
        )
        self.garmin_connect_csv_download = (
            "/download-service/export/csv/activity"
        )

        self.garmin_connect_upload = "/upload-service/upload"

        self.garmin_connect_gear = "/gear-service/gear/filterGear"
        self.garmin_connect_gear_baseurl = "/gear-service/gear/"

        self.garmin_request_reload_url = (
            "/wellness-service/wellness/epoch/request"
        )

        self.garmin_workouts = "/workout-service"

        self.garmin_connect_delete_activity_url = "/activity-service/activity"

        self.garmin_graphql_endpoint = "graphql-gateway/graphql"

        self.garth = garth.Client(
            domain="garmin.cn" if is_cn else "garmin.com",
            pool_connections=20,
            pool_maxsize=20,
        )

        self.display_name = None
        self.full_name = None
        self.unit_system = None

    def connectapi(self, path, **kwargs):
        return self.garth.connectapi(path, **kwargs)

    def download(self, path, **kwargs):
        return self.garth.download(path, **kwargs)

    def login(self, /, tokenstore: Optional[str] = None):
        """Log in using Garth."""
        tokenstore = tokenstore or os.getenv("GARMINTOKENS")

        if tokenstore:
            if len(tokenstore) > 512:
                self.garth.loads(tokenstore)
            else:
                self.garth.load(tokenstore)
        else:
            self.garth.login(
                self.username, self.password, prompt_mfa=self.prompt_mfa
            )

        self.display_name = self.garth.profile["displayName"]
        self.full_name = self.garth.profile["fullName"]

        settings = self.garth.connectapi(self.garmin_connect_user_settings_url)
        self.unit_system = settings["userData"]["measurementSystem"]

        return True

    def get_full_name(self):
        """Return full name."""

        return self.full_name

    def get_unit_system(self):
        """Return unit system."""

        return self.unit_system

    def get_stats(self, cdate: str) -> Dict[str, Any]:
        """
        Return user activity summary for 'cdate' format 'YYYY-MM-DD'
        (compat for garminconnect).
        """

        return self.get_user_summary(cdate)

    def get_user_summary(self, cdate: str) -> Dict[str, Any]:
        """Return user activity summary for 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_daily_summary_url}/{self.display_name}"
        params = {"calendarDate": str(cdate)}
        logger.debug("Requesting user summary")

        response = self.connectapi(url, params=params)

        if response["privacyProtected"] is True:
            raise GarminConnectAuthenticationError("Authentication error")

        return response

    def get_steps_data(self, cdate):
        """Fetch available steps data 'cDate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_user_summary_chart}/{self.display_name}"
        params = {"date": str(cdate)}
        logger.debug("Requesting steps data")

        return self.connectapi(url, params=params)

    def get_floors(self, cdate):
        """Fetch available floors data 'cDate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_floors_chart_daily_url}/{cdate}"
        logger.debug("Requesting floors data")

        return self.connectapi(url)

    def get_daily_steps(self, start, end):
        """Fetch available steps data 'start' and 'end' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_daily_stats_steps_url}/{start}/{end}"
        logger.debug("Requesting daily steps data")

        return self.connectapi(url)

    def get_heart_rates(self, cdate):
        """Fetch available heart rates data 'cDate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_heartrates_daily_url}/{self.display_name}"
        params = {"date": str(cdate)}
        logger.debug("Requesting heart rates")

        return self.connectapi(url, params=params)

    def get_stats_and_body(self, cdate):
        """Return activity data and body composition (compat for garminconnect)."""

        return {
            **self.get_stats(cdate),
            **self.get_body_composition(cdate)["totalAverage"],
        }

    def get_body_composition(
        self, startdate: str, enddate=None
    ) -> Dict[str, Any]:
        """
        Return available body composition data for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'.
        """

        if enddate is None:
            enddate = startdate
        url = f"{self.garmin_connect_weight_url}/weight/dateRange"
        params = {"startDate": str(startdate), "endDate": str(enddate)}
        logger.debug("Requesting body composition")

        return self.connectapi(url, params=params)

    def add_body_composition(
        self,
        timestamp: Optional[str],
        weight: float,
        percent_fat: Optional[float] = None,
        percent_hydration: Optional[float] = None,
        visceral_fat_mass: Optional[float] = None,
        bone_mass: Optional[float] = None,
        muscle_mass: Optional[float] = None,
        basal_met: Optional[float] = None,
        active_met: Optional[float] = None,
        physique_rating: Optional[float] = None,
        metabolic_age: Optional[float] = None,
        visceral_fat_rating: Optional[float] = None,
        bmi: Optional[float] = None,
    ):
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        fitEncoder = fit.FitEncoderWeight()
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
        return self.garth.post("connectapi", url, files=files, api=True)

    def add_weigh_in(
        self, weight: int, unitKey: str = "kg", timestamp: str = ""
    ):
        """Add a weigh-in (default to kg)"""

        url = f"{self.garmin_connect_weight_url}/user-weight"
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        # Apply timezone offset to get UTC/GMT time
        dtGMT = dt.astimezone(timezone.utc)
        payload = {
            "dateTimestamp": dt.isoformat()[:19] + ".00",
            "gmtTimestamp": dtGMT.isoformat()[:19] + ".00",
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }
        logger.debug("Adding weigh-in")

        return self.garth.post("connectapi", url, json=payload)

    def add_weigh_in_with_timestamps(
        self,
        weight: int,
        unitKey: str = "kg",
        dateTimestamp: str = "",
        gmtTimestamp: str = "",
    ):
        """Add a weigh-in with explicit timestamps (default to kg)"""

        url = f"{self.garmin_connect_weight_url}/user-weight"

        # Validate and format the timestamps
        dt = (
            datetime.fromisoformat(dateTimestamp)
            if dateTimestamp
            else datetime.now()
        )
        dtGMT = (
            datetime.fromisoformat(gmtTimestamp)
            if gmtTimestamp
            else dt.astimezone(timezone.utc)
        )

        # Build the payload
        payload = {
            "dateTimestamp": dt.isoformat()[:19] + ".00",  # Local time
            "gmtTimestamp": dtGMT.isoformat()[:19] + ".00",  # GMT/UTC time
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }

        # Debug log for payload
        logger.debug(f"Adding weigh-in with explicit timestamps: {payload}")

        # Make the POST request
        return self.garth.post("connectapi", url, json=payload)

    def get_weigh_ins(self, startdate: str, enddate: str):
        """Get weigh-ins between startdate and enddate using format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_weight_url}/weight/range/{startdate}/{enddate}"
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def get_daily_weigh_ins(self, cdate: str):
        """Get weigh-ins for 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_weight_url}/weight/dayview/{cdate}"
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def delete_weigh_in(self, weight_pk: str, cdate: str):
        """Delete specific weigh-in."""
        url = f"{self.garmin_connect_weight_url}/weight/{cdate}/byversion/{weight_pk}"
        logger.debug("Deleting weigh-in")

        return self.garth.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def delete_weigh_ins(self, cdate: str, delete_all: bool = False):
        """
        Delete weigh-in for 'cdate' format 'YYYY-MM-DD'.
        Includes option to delete all weigh-ins for that date.
        """

        daily_weigh_ins = self.get_daily_weigh_ins(cdate)
        weigh_ins = daily_weigh_ins.get("dateWeightList", [])
        if not weigh_ins or len(weigh_ins) == 0:
            logger.warning(f"No weigh-ins found on {cdate}")
            return
        elif len(weigh_ins) > 1:
            logger.warning(f"Multiple weigh-ins found for {cdate}")
            if not delete_all:
                logger.warning(
                    f"Set delete_all to True to delete all {len(weigh_ins)} weigh-ins"
                )
                return

        for w in weigh_ins:
            self.delete_weigh_in(w["samplePk"], cdate)

        return len(weigh_ins)

    def get_body_battery(
        self, startdate: str, enddate=None
    ) -> List[Dict[str, Any]]:
        """
        Return body battery values by day for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'
        """

        if enddate is None:
            enddate = startdate
        url = self.garmin_connect_daily_body_battery_url
        params = {"startDate": str(startdate), "endDate": str(enddate)}
        logger.debug("Requesting body battery data")

        return self.connectapi(url, params=params)

    def get_body_battery_events(self, cdate: str) -> List[Dict[str, Any]]:
        """
        Return body battery events for date 'cdate' format 'YYYY-MM-DD'.
        The return value is a list of dictionaries, where each dictionary contains event data for a specific event.
        Events can include sleep, recorded activities, auto-detected activities, and naps
        """

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
    ):
        """
        Add blood pressure measurement
        """

        url = f"{self.garmin_connect_set_blood_pressure_endpoint}"
        dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        # Apply timezone offset to get UTC/GMT time
        dtGMT = dt.astimezone(timezone.utc)
        payload = {
            "measurementTimestampLocal": dt.isoformat()[:19] + ".00",
            "measurementTimestampGMT": dtGMT.isoformat()[:19] + ".00",
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse,
            "sourceType": "MANUAL",
            "notes": notes,
        }

        logger.debug("Adding blood pressure")

        return self.garth.post("connectapi", url, json=payload)

    def get_blood_pressure(
        self, startdate: str, enddate=None
    ) -> Dict[str, Any]:
        """
        Returns blood pressure by day for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'
        """

        if enddate is None:
            enddate = startdate
        url = f"{self.garmin_connect_blood_pressure_endpoint}/{startdate}/{enddate}"
        params = {"includeAll": True}
        logger.debug("Requesting blood pressure data")

        return self.connectapi(url, params=params)

    def delete_blood_pressure(self, version: str, cdate: str):
        """Delete specific blood pressure measurement."""
        url = f"{self.garmin_connect_set_blood_pressure_endpoint}/{cdate}/{version}"
        logger.debug("Deleting blood pressure measurement")

        return self.garth.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def get_max_metrics(self, cdate: str) -> Dict[str, Any]:
        """Return available max metric data for 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_metrics_url}/{cdate}/{cdate}"
        logger.debug("Requesting max metrics")

        return self.connectapi(url)

    def add_hydration_data(
        self, value_in_ml: float, timestamp=None, cdate: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add hydration data in ml.  Defaults to current date and current timestamp if left empty
        :param float required - value_in_ml: The number of ml of water you wish to add (positive) or subtract (negative)
        :param timestamp optional - timestamp: The timestamp of the hydration update, format 'YYYY-MM-DDThh:mm:ss.ms' Defaults to current timestamp
        :param date optional - cdate: The date of the weigh in, format 'YYYY-MM-DD'. Defaults to current date
        """

        url = self.garmin_connect_set_hydration_url

        if timestamp is None and cdate is None:
            # If both are null, use today and now
            raw_date = date.today()
            cdate = str(raw_date)

            raw_ts = datetime.now()
            timestamp = datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

        elif cdate is not None and timestamp is None:
            # If cdate is not null, use timestamp associated with midnight
            raw_ts = datetime.strptime(cdate, "%Y-%m-%d")
            timestamp = datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

        elif cdate is None and timestamp is not None:
            # If timestamp is not null, set cdate equal to date part of timestamp
            raw_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
            cdate = str(raw_ts.date())

        payload = {
            "calendarDate": cdate,
            "timestampLocal": timestamp,
            "valueInML": value_in_ml,
        }

        logger.debug("Adding hydration data")

        return self.garth.put("connectapi", url, json=payload)

    def get_hydration_data(self, cdate: str) -> Dict[str, Any]:
        """Return available hydration data 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_daily_hydration_url}/{cdate}"
        logger.debug("Requesting hydration data")

        return self.connectapi(url)

    def get_respiration_data(self, cdate: str) -> Dict[str, Any]:
        """Return available respiration data 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_daily_respiration_url}/{cdate}"
        logger.debug("Requesting respiration data")

        return self.connectapi(url)

    def get_spo2_data(self, cdate: str) -> Dict[str, Any]:
        """Return available SpO2 data 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_daily_spo2_url}/{cdate}"
        logger.debug("Requesting SpO2 data")

        return self.connectapi(url)

    def get_intensity_minutes_data(self, cdate: str) -> Dict[str, Any]:
        """Return available Intensity Minutes data 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_connect_daily_intensity_minutes}/{cdate}"
        logger.debug("Requesting Intensity Minutes data")

        return self.connectapi(url)

    def get_all_day_stress(self, cdate: str) -> Dict[str, Any]:
        """Return available all day stress data 'cdate' format 'YYYY-MM-DD'."""

        url = f"{self.garmin_all_day_stress_url}/{cdate}"
        logger.debug("Requesting all day stress data")

        return self.connectapi(url)

    def get_all_day_events(self, cdate: str) -> Dict[str, Any]:
        """
        Return available daily events data 'cdate' format 'YYYY-MM-DD'.
        Includes autodetected activities, even if not recorded on the watch
        """

        url = f"{self.garmin_daily_events_url}?calendarDate={cdate}"
        logger.debug("Requesting all day stress data")

        return self.connectapi(url)

    def get_personal_record(self) -> Dict[str, Any]:
        """Return personal records for current user."""

        url = f"{self.garmin_connect_personal_record_url}/{self.display_name}"
        logger.debug("Requesting personal records for user")

        return self.connectapi(url)

    def get_earned_badges(self) -> Dict[str, Any]:
        """Return earned badges for current user."""

        url = self.garmin_connect_earned_badges_url
        logger.debug("Requesting earned badges for user")

        return self.connectapi(url)

    def get_adhoc_challenges(self, start, limit) -> Dict[str, Any]:
        """Return adhoc challenges for current user."""

        url = self.garmin_connect_adhoc_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting adhoc challenges for user")

        return self.connectapi(url, params=params)

    def get_badge_challenges(self, start, limit) -> Dict[str, Any]:
        """Return badge challenges for current user."""

        url = self.garmin_connect_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_available_badge_challenges(self, start, limit) -> Dict[str, Any]:
        """Return available badge challenges."""

        url = self.garmin_connect_available_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting available badge challenges")

        return self.connectapi(url, params=params)

    def get_non_completed_badge_challenges(
        self, start, limit
    ) -> Dict[str, Any]:
        """Return badge non-completed challenges for current user."""

        url = self.garmin_connect_non_completed_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_inprogress_virtual_challenges(
        self, start, limit
    ) -> Dict[str, Any]:
        """Return in-progress virtual challenges for current user."""

        url = self.garmin_connect_inprogress_virtual_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting in-progress virtual challenges for user")

        return self.connectapi(url, params=params)

    def get_sleep_data(self, cdate: str) -> Dict[str, Any]:
        """Return sleep data for current user."""

        url = f"{self.garmin_connect_daily_sleep_url}/{self.display_name}"
        params = {"date": str(cdate), "nonSleepBufferMinutes": 60}
        logger.debug("Requesting sleep data")

        return self.connectapi(url, params=params)

    def get_stress_data(self, cdate: str) -> Dict[str, Any]:
        """Return stress data for current user."""

        url = f"{self.garmin_connect_daily_stress_url}/{cdate}"
        logger.debug("Requesting stress data")

        return self.connectapi(url)

    def get_rhr_day(self, cdate: str) -> Dict[str, Any]:
        """Return resting heartrate data for current user."""

        url = f"{self.garmin_connect_rhr_url}/{self.display_name}"
        params = {
            "fromDate": str(cdate),
            "untilDate": str(cdate),
            "metricId": 60,
        }
        logger.debug("Requesting resting heartrate data")

        return self.connectapi(url, params=params)

    def get_hrv_data(self, cdate: str) -> Dict[str, Any]:
        """Return Heart Rate Variability (hrv) data for current user."""

        url = f"{self.garmin_connect_hrv_url}/{cdate}"
        logger.debug("Requesting Heart Rate Variability (hrv) data")

        return self.connectapi(url)

    def get_training_readiness(self, cdate: str) -> Dict[str, Any]:
        """Return training readiness data for current user."""

        url = f"{self.garmin_connect_training_readiness_url}/{cdate}"
        logger.debug("Requesting training readiness data")

        return self.connectapi(url)

    def get_endurance_score(self, startdate: str, enddate=None):
        """
        Return endurance score by day for 'startdate' format 'YYYY-MM-DD'
        through enddate 'YYYY-MM-DD'.
        Using a single day returns the precise values for that day.
        Using a range returns the aggregated weekly values for that week.
        """

        if enddate is None:
            url = self.garmin_connect_endurance_score_url
            params = {"calendarDate": str(startdate)}
            logger.debug("Requesting endurance score data for a single day")

            return self.connectapi(url, params=params)
        else:
            url = f"{self.garmin_connect_endurance_score_url}/stats"
            params = {
                "startDate": str(startdate),
                "endDate": str(enddate),
                "aggregation": "weekly",
            }
            logger.debug("Requesting endurance score data for a range of days")

            return self.connectapi(url, params=params)

    def get_race_predictions(self, startdate=None, enddate=None, _type=None):
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
            raise ValueError("results: _type must be one of %r." % valid)

        if _type is None and startdate is None and enddate is None:
            url = (
                self.garmin_connect_race_predictor_url
                + f"/latest/{self.display_name}"
            )
            return self.connectapi(url)

        elif (
            _type is not None and startdate is not None and enddate is not None
        ):
            url = (
                self.garmin_connect_race_predictor_url
                + f"/{_type}/{self.display_name}"
            )
            params = {
                "fromCalendarDate": str(startdate),
                "toCalendarDate": str(enddate),
            }
            return self.connectapi(url, params=params)

        else:
            raise ValueError(
                "You must either provide all parameters or no parameters"
            )

    def get_training_status(self, cdate: str) -> Dict[str, Any]:
        """Return training status data for current user."""

        url = f"{self.garmin_connect_training_status_url}/{cdate}"
        logger.debug("Requesting training status data")

        return self.connectapi(url)

    def get_fitnessage_data(self, cdate: str) -> Dict[str, Any]:
        """Return Fitness Age data for current user."""

        url = f"{self.garmin_connect_fitnessage}/{cdate}"
        logger.debug("Requesting Fitness Age data")

        return self.connectapi(url)

    def get_hill_score(self, startdate: str, enddate=None):
        """
        Return hill score by day from 'startdate' format 'YYYY-MM-DD'
        to enddate 'YYYY-MM-DD'
        """

        if enddate is None:
            url = self.garmin_connect_hill_score_url
            params = {"calendarDate": str(startdate)}
            logger.debug("Requesting hill score data for a single day")

            return self.connectapi(url, params=params)

        else:
            url = f"{self.garmin_connect_hill_score_url}/stats"
            params = {
                "startDate": str(startdate),
                "endDate": str(enddate),
                "aggregation": "daily",
            }
            logger.debug("Requesting hill score data for a range of days")

            return self.connectapi(url, params=params)

    def get_devices(self) -> List[Dict[str, Any]]:
        """Return available devices for the current user account."""

        url = self.garmin_connect_devices_url
        logger.debug("Requesting devices")

        return self.connectapi(url)

    def get_device_settings(self, device_id: str) -> Dict[str, Any]:
        """Return device settings for device with 'device_id'."""

        url = f"{self.garmin_connect_device_url}/device-info/settings/{device_id}"
        logger.debug("Requesting device settings")

        return self.connectapi(url)

    def get_primary_training_device(self) -> Dict[str, Any]:
        """Return detailed information around primary training devices, included the specified device and the
        priority of all devices.
        """

        url = self.garmin_connect_primary_device_url
        logger.debug("Requesting primary training device information")

        return self.connectapi(url)

    def get_device_solar_data(
        self, device_id: str, startdate: str, enddate=None
    ) -> Dict[str, Any]:
        """Return solar data for compatible device with 'device_id'"""
        if enddate is None:
            enddate = startdate
            single_day = True
        else:
            single_day = False

        params = {"singleDayView": single_day}

        url = f"{self.garmin_connect_solar_url}/{device_id}/{startdate}/{enddate}"

        return self.connectapi(url, params=params)["deviceSolarInput"]

    def get_device_alarms(self) -> List[Any]:
        """Get list of active alarms from all devices."""

        logger.debug("Requesting device alarms")

        alarms = []
        devices = self.get_devices()
        for device in devices:
            device_settings = self.get_device_settings(device["deviceId"])
            device_alarms = device_settings["alarms"]
            if device_alarms is not None:
                alarms += device_alarms
        return alarms

    def get_device_last_used(self):
        """Return device last used."""

        url = f"{self.garmin_connect_device_url}/mylastused"
        logger.debug("Requesting device last used")

        return self.connectapi(url)

    def get_activities(self, start: int = 0, limit: int = 20, activitytype = None):
        """
        Return available activities.
        :param start: Starting activity offset, where 0 means the most recent activity
        :param limit: Number of activities to return
        :return: List of activities from Garmin
        """

        url = self.garmin_connect_activities
        params = {"start": str(start), "limit": str(limit)}
        if activitytype:
            params["activityType"] = str(activitytype)

        logger.debug("Requesting activities")

        return self.connectapi(url, params=params)

    def get_activities_fordate(self, fordate: str):
        """Return available activities for date."""

        url = f"{self.garmin_connect_activity_fordate}/{fordate}"
        logger.debug(f"Requesting activities for date {fordate}")

        return self.connectapi(url)

    def set_activity_name(self, activity_id, title):
        """Set name for activity with id."""

        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {"activityId": activity_id, "activityName": title}

        return self.garth.put("connectapi", url, json=payload, api=True)

    def set_activity_type(
        self, activity_id, type_id, type_key, parent_type_id
    ):
        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {
            "activityId": activity_id,
            "activityTypeDTO": {
                "typeId": type_id,
                "typeKey": type_key,
                "parentTypeId": parent_type_id,
            },
        }
        logger.debug(f"Changing activity type: {str(payload)}")
        return self.garth.put("connectapi", url, json=payload, api=True)

    def create_manual_activity_from_json(self, payload):
        url = f"{self.garmin_connect_activity}"
        logger.debug(f"Uploading manual activity: {str(payload)}")
        return self.garth.post("connectapi", url, json=payload, api=True)

    def create_manual_activity(
        self,
        start_datetime,
        timezone,
        type_key,
        distance_km,
        duration_min,
        activity_name,
    ):
        """
        Create a private activity manually with a few basic parameters.
        type_key - Garmin field representing type of activity. See https://connect.garmin.com/modern/main/js/properties/activity_types/activity_types.properties
                    Value to use is the key without 'activity_type_' prefix, e.g. 'resort_skiing'
        start_datetime - timestamp in this pattern "2023-12-02T10:00:00.00"
        timezone - local timezone of the activity, e.g. 'Europe/Paris'
        distance_km - distance of the activity in kilometers
        duration_min - duration of the activity in minutes
        activity_name - the title
        """
        payload = {
            "activityTypeDTO": {"typeKey": type_key},
            "accessControlRuleDTO": {"typeId": 2, "typeKey": "private"},
            "timeZoneUnitDTO": {"unitKey": timezone},
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

    def get_last_activity(self):
        """Return last activity."""

        activities = self.get_activities(0, 1)
        if activities:
            return activities[-1]

        return None

    def upload_activity(self, activity_path: str):
        """Upload activity in fit format from file."""
        # This code is borrowed from python-garminconnect-enhanced ;-)

        file_base_name = os.path.basename(activity_path)
        file_extension = file_base_name.split(".")[-1]
        allowed_file_extension = (
            file_extension.upper() in Garmin.ActivityUploadFormat.__members__
        )

        if allowed_file_extension:
            files = {
                "file": (file_base_name, open(activity_path, "rb" or "r")),
            }
            url = self.garmin_connect_upload
            return self.garth.post("connectapi", url, files=files, api=True)
        else:
            raise GarminConnectInvalidFileFormatError(
                f"Could not upload {activity_path}"
            )

    def delete_activity(self, activity_id):
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
        self, startdate, enddate=None, activitytype=None, sortorder=None
    ):
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
        params = {
            "startDate": str(startdate),
            "start": str(start),
            "limit": str(limit),
        }
        if enddate:
            params["endDate"] = str(enddate)
        if activitytype:
            params["activityType"] = str(activitytype)
        if sortorder:
            params["sortOrder"] = str(sortorder)

        logger.debug(
            f"Requesting activities by date from {startdate} to {enddate}"
        )
        while True:
            params["start"] = str(start)
            logger.debug(f"Requesting activities {start} to {start+limit}")
            act = self.connectapi(url, params=params)
            if act:
                activities.extend(act)
                start = start + limit
            else:
                break

        return activities

    def get_progress_summary_between_dates(
        self, startdate, enddate, metric="distance", groupbyactivities=True
    ):
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
        params = {
            "startDate": str(startdate),
            "endDate": str(enddate),
            "aggregation": "lifetime",
            "groupByParentActivityType": str(groupbyactivities),
            "metric": str(metric),
        }

        logger.debug(
            f"Requesting fitnessstats by date from {startdate} to {enddate}"
        )
        return self.connectapi(url, params=params)

    def get_activity_types(self):
        url = self.garmin_connect_activity_types
        logger.debug("Requesting activity types")
        return self.connectapi(url)

    def get_goals(self, status="active", start=1, limit=30):
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
        params = {
            "status": status,
            "start": str(start),
            "limit": str(limit),
            "sortOrder": "asc",
        }

        logger.debug(f"Requesting {status} goals")
        while True:
            params["start"] = str(start)
            logger.debug(
                f"Requesting {status} goals {start} to {start + limit - 1}"
            )
            goals_json = self.connectapi(url, params=params)
            if goals_json:
                goals.extend(goals_json)
                start = start + limit
            else:
                break

        return goals

    def get_gear(self, userProfileNumber):
        """Return all user gear."""
        url = f"{self.garmin_connect_gear}?userProfilePk={userProfileNumber}"
        logger.debug("Requesting gear for user %s", userProfileNumber)

        return self.connectapi(url)

    def get_gear_stats(self, gearUUID):
        url = f"{self.garmin_connect_gear_baseurl}stats/{gearUUID}"
        logger.debug("Requesting gear stats for gearUUID %s", gearUUID)
        return self.connectapi(url)

    def get_gear_defaults(self, userProfileNumber):
        url = (
            f"{self.garmin_connect_gear_baseurl}user/"
            f"{userProfileNumber}/activityTypes"
        )
        logger.debug("Requesting gear for user %s", userProfileNumber)
        return self.connectapi(url)

    def set_gear_default(self, activityType, gearUUID, defaultGear=True):
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
        self, activity_id, dl_fmt=ActivityDownloadFormat.TCX
    ):
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
            raise ValueError(f"Unexpected value {dl_fmt} for dl_fmt")
        url = urls[dl_fmt]

        logger.debug("Downloading activities from %s", url)

        return self.download(url)

    def get_activity_splits(self, activity_id):
        """Return activity splits."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/splits"
        logger.debug("Requesting splits for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_typed_splits(self, activity_id):
        """Return typed activity splits. Contains similar info to `get_activity_splits`, but for certain activity types
        (e.g., Bouldering), this contains more detail."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/typedsplits"
        logger.debug("Requesting typed splits for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_split_summaries(self, activity_id):
        """Return activity split summaries."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/split_summaries"
        logger.debug(
            "Requesting split summaries for activity id %s", activity_id
        )

        return self.connectapi(url)

    def get_activity_weather(self, activity_id):
        """Return activity weather."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/weather"
        logger.debug("Requesting weather for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_hr_in_timezones(self, activity_id):
        """Return activity heartrate in timezones."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/hrTimeInZones"
        logger.debug(
            "Requesting split summaries for activity id %s", activity_id
        )

        return self.connectapi(url)

    def get_activity(self, activity_id):
        """Return activity summary, including basic splits."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}"
        logger.debug(
            "Requesting activity summary data for activity id %s", activity_id
        )

        return self.connectapi(url)

    def get_activity_details(self, activity_id, maxchart=2000, maxpoly=4000):
        """Return activity details."""

        activity_id = str(activity_id)
        params = {
            "maxChartSize": str(maxchart),
            "maxPolylineSize": str(maxpoly),
        }
        url = f"{self.garmin_connect_activity}/{activity_id}/details"
        logger.debug("Requesting details for activity id %s", activity_id)

        return self.connectapi(url, params=params)

    def get_activity_exercise_sets(self, activity_id):
        """Return activity exercise sets."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/exerciseSets"
        logger.debug(
            "Requesting exercise sets for activity id %s", activity_id
        )

        return self.connectapi(url)

    def get_activity_gear(self, activity_id):
        """Return gears used for activity id."""

        activity_id = str(activity_id)
        params = {
            "activityId": str(activity_id),
        }
        url = self.garmin_connect_gear
        logger.debug("Requesting gear for activity_id %s", activity_id)

        return self.connectapi(url, params=params)

    def get_gear_ativities(self, gearUUID, limit = 9999):
        """Return activities where gear uuid was used."""

        gearUUID = str(gearUUID)

        url = f"{self.garmin_connect_activities_baseurl}{gearUUID}/gear?start=0&limit={limit}"
        logger.debug("Requesting activities for gearUUID %s", gearUUID)

        return self.connectapi(url)

    def get_user_profile(self):
        """Get all users settings."""

        url = self.garmin_connect_user_settings_url
        logger.debug("Requesting user profile.")

        return self.connectapi(url)

    def get_userprofile_settings(self):
        """Get user settings."""

        url = self.garmin_connect_userprofile_settings_url
        logger.debug("Getting userprofile settings")

        return self.connectapi(url)

    def request_reload(self, cdate: str):
        """
        Request reload of data for a specific date. This is necessary because
        Garmin offloads older data.
        """

        url = f"{self.garmin_request_reload_url}/{cdate}"
        logger.debug(f"Requesting reload of data for {cdate}.")

        return self.garth.post("connectapi", url, api=True)

    def get_workouts(self, start=0, end=100):
        """Return workouts from start till end."""

        url = f"{self.garmin_workouts}/workouts"
        logger.debug(f"Requesting workouts from {start}-{end}")
        params = {"start": start, "limit": end}
        return self.connectapi(url, params=params)

    def get_workout_by_id(self, workout_id):
        """Return workout by id."""

        url = f"{self.garmin_workouts}/workout/{workout_id}"
        return self.connectapi(url)

    def download_workout(self, workout_id):
        """Download workout by id."""

        url = f"{self.garmin_workouts}/workout/FIT/{workout_id}"
        logger.debug("Downloading workout from %s", url)

        return self.download(url)

    # def upload_workout(self, workout_json: str):
    #     """Upload workout using json data."""

    #     url = f"{self.garmin_workouts}/workout"
    #     logger.debug("Uploading workout using %s", url)

    #     return self.garth.post("connectapi", url, json=workout_json, api=True)
    def get_menstrual_data_for_date(self, fordate: str):
        """Return menstrual data for date."""

        url = f"{self.garmin_connect_menstrual_dayview_url}/{fordate}"
        logger.debug(f"Requesting menstrual data for date {fordate}")

        return self.connectapi(url)

    def get_menstrual_calendar_data(self, startdate: str, enddate: str):
        """Return summaries of cycles that have days between startdate and enddate."""

        url = f"{self.garmin_connect_menstrual_calendar_url}/{startdate}/{enddate}"
        logger.debug(
            f"Requesting menstrual data for dates {startdate} through {enddate}"
        )

        return self.connectapi(url)

    def get_pregnancy_summary(self):
        """Return snapshot of pregnancy data"""

        url = f"{self.garmin_connect_pregnancy_snapshot_url}"
        logger.debug("Requesting pregnancy snapshot data")

        return self.connectapi(url)

    def query_garmin_graphql(self, query: dict):
        """Returns the results of a POST request to the Garmin GraphQL Endpoints.
        Requires a GraphQL structured query.  See {TBD} for examples.
        """

        logger.debug(f"Querying Garmin GraphQL Endpoint with query: {query}")

        return self.garth.post(
            "connectapi", self.garmin_graphql_endpoint, json=query
        ).json()

    def logout(self):
        """Log user out of session."""

        logger.error(
            "Deprecated: Alternative is to delete login tokens to logout."
        )


class GarminConnectConnectionError(Exception):
    """Raised when communication ended in error."""


class GarminConnectTooManyRequestsError(Exception):
    """Raised when rate limit is exceeded."""


class GarminConnectAuthenticationError(Exception):
    """Raised when authentication is failed."""


class GarminConnectInvalidFileFormatError(Exception):
    """Raised when an invalid file format is passed to upload."""
