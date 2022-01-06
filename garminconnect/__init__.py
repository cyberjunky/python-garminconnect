# -*- coding: utf-8 -*-
"""Python 3 API wrapper for Garmin Connect to get your statistics."""
import json
import logging
import re
from enum import Enum, auto
from typing import Any, Dict

import cloudscraper

logger = logging.getLogger(__file__)


class ApiClient:
    """Class for a single API endpoint."""

    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0"
    }

    def __init__(self, session, baseurl, headers=None, aditional_headers=None):
        """Return a new Client instance."""
        self.session = session
        self.baseurl = baseurl
        if headers:
            self.headers = headers
        else:
            self.headers = self.default_headers.copy()
        self.headers.update(aditional_headers)

    def url(self, addurl=None):
        """Return the url for the API endpoint."""

        path = f"https://{self.baseurl}"
        if addurl is not None:
            path += f"/{addurl}"

        return path

    def get(self, addurl, aditional_headers=None, params=None):
        """Make an API call using the GET method."""
        total_headers = self.headers.copy()
        if aditional_headers:
            total_headers.update(aditional_headers)
        url = self.url(addurl)
        try:
            response = self.session.get(url, headers=total_headers, params=params)
            response.raise_for_status()
            return response
        except Exception as err:
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests") from err
            if response.status_code == 401:
                raise GarminConnectAuthenticationError("Authentication error") from err
            if response.status_code == 403:
                raise GarminConnectConnectionError(f"Forbidden url: %s", url) from err
            if response.status_code == 500:
                raise GarminConnectConnectionError("Server error") from err
            if response.status_code == 404:
                raise GarminConnectConnectionError("Not found") from err
            try:
                resp = response.json()
                error = resp["message"].json()
            except AttributeError:
                error = "Unknown"

            raise GarminConnectConnectionError(
                f"Unknown error {response.status_code} - {error}"
            ) from err

    def post(self, addurl, aditional_headers, params, data):
        """Make an API call using the POST method."""
        total_headers = self.headers.copy()
        if aditional_headers:
            total_headers.update(aditional_headers)
        url = self.url(addurl)
        try:
            response = self.session.post(
                url, headers=total_headers, params=params, data=data
            )
            response.raise_for_status()
            return response
        except Exception as err:
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests") from err
            if response.status_code == 401:
                raise GarminConnectAuthenticationError("Authentication error") from err
            if response.status_code == 403:
                raise GarminConnectConnectionError(f"Forbidden url: %s", url) from err
            if response.status_code == 500:
                raise GarminConnectConnectionError("Server error") from err
            if response.status_code == 404:
                raise GarminConnectConnectionError("Not found") from err
            try:
                resp = response.json()
                error = resp["message"].json()
            except AttributeError:
                error = "Unknown"

            raise GarminConnectConnectionError(
                f"Unknown error {response.status_code} - {error}"
            ) from err


class Garmin:
    """Class for fetching data from Garmin Connect."""

    def __init__(self, email, password, is_cn=False):
        """Create a new class instance."""

        self.username = email
        self.password = password
        self.is_cn = is_cn

        self.garmin_connect_base_url = "https://connect.garmin.com"
        self.garmin_connect_sso_url = "sso.garmin.com/sso"
        self.garmin_connect_modern_url = "connect.garmin.com/modern"
        self.garmin_connect_css_url = "https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css"

        if self.is_cn:
            self.garmin_connect_base_url = "https://connect.garmin.cn"
            self.garmin_connect_sso_url = "sso.garmin.cn/sso"
            self.garmin_connect_modern_url = "connect.garmin.cn/modern"
            self.garmin_connect_css_url = "https://static.garmincdn.cn/cn.garmin.connect/ui/css/gauth-custom-v1.2-min.css"

        self.garmin_connect_login_url = self.garmin_connect_base_url + "/en-US/signin"
        self.garmin_connect_sso_login = "signin"

        self.garmin_connect_devices_url = (
            "proxy/device-service/deviceregistration/devices"
        )
        self.garmin_connect_device_url = "proxy/device-service/deviceservice"
        self.garmin_connect_weight_url = "proxy/weight-service/weight/dateRange"
        self.garmin_connect_daily_summary_url = (
            "proxy/usersummary-service/usersummary/daily"
        )
        self.garmin_connect_metrics_url = "proxy/metrics-service/metrics/maxmet/latest"
        self.garmin_connect_daily_hydration_url = (
            "proxy/usersummary-service/usersummary/hydration/daily"
        )
        self.garmin_connect_personal_record_url = (
            "proxy/personalrecord-service/personalrecord/prs"
        )
        self.garmin_connect_sleep_daily_url = (
            "proxy/wellness-service/wellness/dailySleepData"
        )
        self.garmin_connect_rhr = "proxy/userstats-service/wellness/daily"

        self.garmin_connect_user_summary_chart = (
            "proxy/wellness-service/wellness/dailySummaryChart"
        )
        self.garmin_connect_heartrates_daily_url = (
            "proxy/wellness-service/wellness/dailyHeartRate"
        )
        self.garmin_connect_daily_respiration_url = (
            "proxy/wellness-service/wellness/daily/respiration"
        )
        self.garmin_connect_daily_spo2_url = (
            "proxy/wellness-service/wellness/daily/spo2"
        )
        self.garmin_connect_activities = (
            "proxy/activitylist-service/activities/search/activities"
        )
        self.garmin_connect_activity = "proxy/activity-service/activity"

        self.garmin_connect_fit_download = "proxy/download-service/files/activity"
        self.garmin_connect_tcx_download = "proxy/download-service/export/tcx/activity"
        self.garmin_connect_gpx_download = "proxy/download-service/export/gpx/activity"
        self.garmin_connect_kml_download = "proxy/download-service/export/kml/activity"
        self.garmin_connect_csv_download = "proxy/download-service/export/csv/activity"
        self.garmin_connect_gear = "proxy/gear-service/gear/filterGear"

        self.garmin_connect_logout = "auth/logout/?url="

        self.garmin_headers = {"NK": "NT"}

        self.session = cloudscraper.CloudScraper()
        self.sso_rest_client = ApiClient(
            self.session,
            self.garmin_connect_sso_url,
            aditional_headers=self.garmin_headers,
        )
        self.modern_rest_client = ApiClient(
            self.session,
            self.garmin_connect_modern_url,
            aditional_headers=self.garmin_headers,
        )

        self.display_name = None
        self.full_name = None
        self.unit_system = None

    @staticmethod
    def __get_json(page_html, key):
        """Return json from text."""

        found = re.search(key + r" = (\{.*\});", page_html, re.M)
        if found:
            json_text = found.group(1).replace('\\"', '"')
            return json.loads(json_text)

        return None

    def login(self):
        """Login to Garmin Connect."""

        logger.debug("login: %s %s", self.username, self.password)
        get_headers = {"Referer": self.garmin_connect_login_url}
        params = {
            "service": self.modern_rest_client.url(),
            "webhost": self.garmin_connect_base_url,
            "source": self.garmin_connect_login_url,
            "redirectAfterAccountLoginUrl": self.modern_rest_client.url(),
            "redirectAfterAccountCreationUrl": self.modern_rest_client.url(),
            "gauthHost": self.sso_rest_client.url(),
            "locale": "en_US",
            "id": "gauth-widget",
            "cssUrl": self.garmin_connect_css_url,
            "privacyStatementUrl": "//connect.garmin.com/en-US/privacy/",
            "clientId": "GarminConnect",
            "rememberMeShown": "true",
            "rememberMeChecked": "false",
            "createAccountShown": "true",
            "openCreateAccount": "false",
            "displayNameShown": "false",
            "consumeServiceTicket": "false",
            "initialFocus": "true",
            "embedWidget": "false",
            "generateExtraServiceTicket": "true",
            "generateTwoExtraServiceTickets": "false",
            "generateNoServiceTicket": "false",
            "globalOptInShown": "true",
            "globalOptInChecked": "false",
            "mobile": "false",
            "connectLegalTerms": "true",
            "locationPromptShown": "true",
            "showPassword": "true",
        }

        if self.is_cn:
            params[
                "cssUrl"
            ] = "https://static.garmincdn.cn/cn.garmin.connect/ui/css/gauth-custom-v1.2-min.css"

        response = self.sso_rest_client.get(
            self.garmin_connect_sso_login, get_headers, params
        )

        found = re.search(r"name=\"_csrf\" value=\"(\w*)", response.text, re.M)
        if not found:
            logger.error("_csrf not found: %s", response.status_code)
            return False
        logger.debug("_csrf found (%s).", found.group(1))

        data = {
            "username": self.username,
            "password": self.password,
            "embed": "false",
            "_csrf": found.group(1),
        }
        post_headers = {
            "Referer": response.url,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = self.sso_rest_client.post(
            self.garmin_connect_sso_login, post_headers, params, data
        )

        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        if not found:
            logger.error("Login ticket not found (%d).", response.status_code)
            return False
        params = {"ticket": found.group(1)}

        response = self.modern_rest_client.get("", params=params)

        user_prefs = self.__get_json(response.text, "VIEWER_USERPREFERENCES")
        self.display_name = user_prefs["displayName"]
        logger.debug("Display name is %s", self.display_name)

        self.unit_system = user_prefs["measurementSystem"]
        logger.debug("Unit system is %s", self.unit_system)

        social_profile = self.__get_json(response.text, "VIEWER_SOCIAL_PROFILE")
        self.full_name = social_profile["fullName"]
        logger.debug("Fullname is %s", self.full_name)

        return True

    def get_full_name(self):
        """Return full name."""

        return self.full_name

    def get_unit_system(self):
        """Return unit system."""

        return self.unit_system

    def get_stats(self, cdate: str) -> Dict[str, Any]:
        """Return user activity summary for 'cdate' format 'YYYY-mm-dd' (compat for garminconnect)."""

        return self.get_user_summary(cdate)

    def get_user_summary(self, cdate: str) -> Dict[str, Any]:
        """Return user activity summary for 'cdate' format 'YYYY-mm-dd'."""

        url = f"{self.garmin_connect_daily_summary_url}/{self.display_name}"
        params = {
            "calendarDate": str(cdate),
        }
        logger.debug("Requesting user summary with URL: %s", url)

        response = self.modern_rest_client.get(url, params=params).json()

        if response["privacyProtected"] is True:
            raise GarminConnectAuthenticationError("Authentication error")

        return response

    def get_steps_data(self, cdate):
        """Fetch available steps data 'cDate' format 'YYYY-mm-dd'."""

        url = f"{self.garmin_connect_user_summary_chart}/{self.display_name}"
        params = {
            "date": str(cdate),
        }
        logger.debug("Requesting steps data with url %s", url)

        return self.modern_rest_client.get(url, params=params).json()

    def get_heart_rates(self, cdate):  #
        """Fetch available heart rates data 'cDate' format 'YYYY-mm-dd'."""

        url = f"{self.garmin_connect_heartrates_daily_url}/{self.display_name}"
        params = {
            "date": str(cdate),
        }
        logger.debug("Requesting heart rates with url %s", url)

        return self.modern_rest_client.get(url, params=params).json()

    def get_stats_and_body(self, cdate):
        """Return activity data and body composition (compat for garminconnect)."""

        return {
            **self.get_stats(cdate),
            **self.get_body_composition(cdate)["totalAverage"],
        }

    def get_body_composition(self, startdate: str, enddate=None) -> Dict[str, Any]:
        """Return available body composition data for 'startdate' format 'YYYY-mm-dd' through enddate 'YYYY-mm-dd'."""

        if enddate is None:
            enddate = startdate
        url = self.garmin_connect_weight_url
        params = {"startDate": str(startdate), "endDate": str(enddate)}
        logger.debug("Requesting body composition with URL: %s", url)

        return self.modern_rest_client.get(url, params=params).json()

    def get_max_metrics(self, cdate: str) -> Dict[str, Any]:
        """Return available max metric data for 'cdate' format 'YYYY-mm-dd'."""

        url = f"{self.garmin_connect_metrics_url}/{cdate}"
        logger.debug("Requestng max metrics with URL: %s", url)

        return self.modern_rest_client.get(url).json()

    def get_hydration_data(self, cdate: str) -> Dict[str, Any]:
        """Return available hydration data 'cdate' format 'YYYY-mm-dd'."""

        url = f"{self.garmin_connect_daily_hydration_url}/{cdate}"
        logger.debug("Requesting hydration data with URL: %s", url)

        return self.modern_rest_client.get(url).json()

    def get_respiration_data(self, cdate: str) -> Dict[str, Any]:
        """Return available respiration data 'cdate' format 'YYYY-mm-dd'."""

        url = f"{self.garmin_connect_daily_respiration_url}/{cdate}"
        logger.debug("Requesting respiration data with URL: %s", url)

        return self.modern_rest_client.get(url).json()

    def get_spo2_data(self, cdate: str) -> Dict[str, Any]:
        """Return available SpO2 data 'cdate' format 'YYYY-mm-dd'."""

        url = f"{self.garmin_connect_daily_spo2_url}/{cdate}"
        logger.debug("Requesting SpO2 data with URL: %s", url)

        return self.modern_rest_client.get(url).json()

    def get_personal_record(self) -> Dict[str, Any]:
        """Return personal records for current user."""

        url = f"{self.garmin_connect_personal_record_url}/{self.display_name}"
        logger.debug("Requesting personal records for user with URL: %s", url)

        return self.modern_rest_client.get(url).json()

    def get_sleep_data(self, cdate: str) -> Dict[str, Any]:
        """Return sleep data for current user."""

        url = f"{self.garmin_connect_sleep_daily_url}/{self.display_name}"
        params = {"date": str(cdate), "nonSleepBufferMinutes": 60}

        logger.debug("Requesting sleep data with url %s", url)

        return self.modern_rest_client.get(url, params=params).json()

    def get_rhr_day(self, cdate: str) -> Dict[str, Any]:
        """Return resting heartrate data for current user."""

        params = {"fromDate": str(cdate), "untilDate": str(cdate), "metricId": 60}
        url = f"{self.garmin_connect_rhr}/{self.display_name}"
        logger.debug("Requesting resting heartrate data with url %s", url)

        return self.modern_rest_client.get(url, params=params).json()

    def get_devices(self) -> Dict[str, Any]:
        """Return available devices for the current user account."""

        url = self.garmin_connect_devices_url
        logger.debug("Requesting devices with URL: %s", url)

        return self.modern_rest_client.get(url).json()

    def get_device_settings(self, device_id: str) -> Dict[str, Any]:
        """Return device settings for device with 'device_id'."""

        url = f"{self.garmin_connect_device_url}/device-info/settings/{device_id}"
        logger.debug("Requesting device settings with URL: %s", url)

        return self.modern_rest_client.get(url).json()

    def get_device_alarms(self) -> Dict[str, Any]:
        """Get list of active alarms from all devices."""

        logger.debug("Requesting device alarms")

        alarms = []
        devices = self.get_devices()
        for device in devices:
            device_settings = self.get_device_settings(device["deviceId"])
            alarms += device_settings["alarms"]
        return alarms

    def get_device_last_used(self):
        """Return device last used."""

        url = f"{self.garmin_connect_device_url}/mylastused"
        logger.debug("Requesting device last used with url %s", url)

        return self.modern_rest_client.get(url).json()

    def get_activities(self, start, limit):
        """Return available activities."""

        url = self.garmin_connect_activities
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting activities with url %s", url)

        return self.modern_rest_client.get(url, params=params).json()

    def get_last_activity(self):
        """Return last activity."""

        activities = self.get_activities(0,1)
        if activities:
            return activities[-1]

        return None

    class ActivityDownloadFormat(Enum):
        """Activitie variables."""

        ORIGINAL = auto()
        TCX = auto()
        GPX = auto()
        KML = auto()
        CSV = auto()

    def download_activity(self, activity_id, dl_fmt=ActivityDownloadFormat.TCX):
        """
        Downloads activity in requested format and returns the raw bytes. For
        "Original" will return the zip file content, up to user to extract it.
        "CSV" will return a csv of the splits.
        """
        activity_id = str(activity_id)
        urls = {
            Garmin.ActivityDownloadFormat.ORIGINAL: f"{self.garmin_connect_fit_download}/{activity_id}",
            Garmin.ActivityDownloadFormat.TCX: f"{self.garmin_connect_tcx_download}/{activity_id}",
            Garmin.ActivityDownloadFormat.GPX: f"{self.garmin_connect_gpx_download}/{activity_id}",
            Garmin.ActivityDownloadFormat.KML: f"{self.garmin_connect_kml_download}/{activity_id}",
            Garmin.ActivityDownloadFormat.CSV: f"{self.garmin_connect_csv_download}/{activity_id}",
        }
        if dl_fmt not in urls:
            raise ValueError(f"Unexpected value {dl_fmt} for dl_fmt")
        url = urls[dl_fmt]

        logger.debug("Downloading activities from %s", url)

        return self.modern_rest_client.get(url).content

    def get_activity_splits(self, activity_id):
        """Return activity splits."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/splits"
        logger.debug("Requesting splits for activity id %s", activity_id)

        return self.modern_rest_client.get(url).json()

    def get_activity_split_summaries(self, activity_id):
        """Return activity split summaries."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/split_summaries"
        logger.debug("Requesting split summaries for activity id %s", activity_id)

        return self.modern_rest_client.get(url).json()

    def get_activity_weather(self, activity_id):
        """Return activity weather."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/weather"
        logger.debug("Requesting weather for activity id %s", activity_id)

        return self.modern_rest_client.get(url).json()

    def get_activity_hr_in_timezones(self, activity_id):
        """Return activity heartrate in timezones."""

        activity_id = str(activity_id)
        url = f"{self.garmin_connect_activity}/{activity_id}/hrTimeInZones"
        logger.debug("Requesting split summaries for activity id %s", activity_id)

        return self.modern_rest_client.get(url).json()

    def get_activity_details(self, activity_id, maxchart=2000, maxpoly=4000):
        """Return activity details."""

        activity_id = str(activity_id)
        params = {
            "maxChartSize": str(maxchart),
            "maxPolylineSize": str(maxpoly),
        }
        url = f"{self.garmin_connect_activity}/{activity_id}/details"
        logger.debug("Requesting details for activity id %s", activity_id)

        return self.modern_rest_client.get(url, params=params).json()

    def get_activity_gear(self, activity_id):
        """Return gears used for activity id."""

        activity_id = str(activity_id)
        params = {
            "activityId": str(activity_id),
        }
        url = self.garmin_connect_gear
        logger.debug("Requesting gear for activity_id %s", activity_id)

        return self.modern_rest_client.get(url, params=params).json()

    def logout(self):
        """Log user out of session."""

        self.modern_rest_client.get(self.garmin_connect_logout).json()


class GarminConnectConnectionError(Exception):
    """Raised when communication ended in error."""


class GarminConnectTooManyRequestsError(Exception):
    """Raised when rate limit is exceeded."""


class GarminConnectAuthenticationError(Exception):
    """Raised when authentication is failed."""
