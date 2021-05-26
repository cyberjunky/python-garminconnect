# -*- coding: utf-8 -*-
"""Python 3 API wrapper for Garmin Connect to get your statistics."""
import logging
import json
import re
import requests
import cloudscraper
from enum import Enum, auto

from .__version__ import __version__

BASE_URL = 'https://connect.garmin.com'
SSO_URL = 'https://sso.garmin.com/sso'
SIGNIN_URL = 'https://sso.garmin.com/sso/signin'

class Garmin(object):
    """
    Object using Garmin Connect 's API-method.
    See https://connect.garmin.com/
    or you are in mainland China
    See https://connect.garmin.cn/
    """

    def __init__(self, email, password, is_cn=False):
        """
        Init module
        """
        global BASE_URL
        global SSO_URL
        global SIGNIN_URL
        self.email = email
        self.password = password
        self.cf_req = cloudscraper.CloudScraper()
        self.req = requests.session()
        self.logger = logging.getLogger(__name__)
        self.display_name = ""
        self.full_name = ""
        self.unit_system = ""
        self.is_cn = is_cn
        if is_cn:
            BASE_URL = BASE_URL.replace(".com", ".cn")
            SSO_URL = SSO_URL.replace(".com", ".cn")
            SIGNIN_URL = SIGNIN_URL.replace(".com", ".cn")

        self.url_user_summary = BASE_URL + '/proxy/usersummary-service/usersummary/daily/'
        self.url_user_summary_chart = BASE_URL + \
            '/proxy/wellness-service/wellness/dailySummaryChart/'
        self.url_heartrates = BASE_URL + '/proxy/wellness-service/wellness/dailyHeartRate/'
        self.url_sleepdata = BASE_URL + '/proxy/wellness-service/wellness/dailySleepData/'
        self.url_body_composition = BASE_URL + \
            '/proxy/weight-service/weight/daterangesnapshot'
        self.url_activities = BASE_URL + \
            '/proxy/activitylist-service/activities/search/activities'
        self.url_hydrationdata = BASE_URL + '/proxy/usersummary-service/usersummary/hydration/daily/'
        self.url_activity = BASE_URL + '/proxy/activity-service/activity/'
        self.url_personal_record = BASE_URL + '/proxy/personalrecord-service/personalrecord/'
        self.url_tcx_download = BASE_URL + "/proxy/download-service/export/tcx/activity/"
        self.url_gpx_download = BASE_URL + "/proxy/download-service/export/gpx/activity/"
        self.url_kml_download = BASE_URL + "/proxy/download-service/export/kml/activity/"
        self.url_fit_download = BASE_URL + "/proxy/download-service/files/activity/"
        self.url_csv_download = BASE_URL + "/proxy/download-service/export/csv/activity/"
        self.url_device_list = BASE_URL + '/proxy/device-service/deviceregistration/devices'
        self.url_device_service = BASE_URL + \
            '/proxy/device-service/deviceservice/'

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
            'origin': 'https://sso.garmin.com' if not self.is_cn else "https://sso.garmin.cn"
        }

    def login(self):
        """
        Login to portal
        """
        params = {
            'webhost': BASE_URL,
            'service': BASE_URL,
            'source': SIGNIN_URL,
            'redirectAfterAccountLoginUrl': BASE_URL,
            'redirectAfterAccountCreationUrl': BASE_URL,
            'gauthHost': SSO_URL,
            'locale': 'en_US',
            'id': 'gauth-widget',
            'cssUrl': 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css',
            'clientId': 'GarminConnect',
            'rememberMeShown': 'true',
            'rememberMeChecked': 'false',
            'createAccountShown': 'true',
            'openCreateAccount': 'false',
            'usernameShown': 'false',
            'displayNameShown': 'false',
            'consumeServiceTicket': 'false',
            'initialFocus': 'true',
            'embedWidget': 'false',
            'generateExtraServiceTicket': 'false'
        }
        if self.is_cn:
            params['cssUrl'] = 'https://static.garmincdn.cn/cn.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

        data = {
            'username': self.email,
            'password': self.password,
            'embed': 'true',
            'lt': 'e1s1',
            '_eventId': 'submit',
            'displayNameRequired': 'false'
        }

        self.logger.debug(
            "Login to Garmin Connect using POST url %s", SIGNIN_URL)
        try:
            response = self.cf_req.get(
                SIGNIN_URL, headers=self.headers, params=params)

            response = self.cf_req.post(
                SIGNIN_URL, headers=self.headers, params=params, data=data)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")
            response.raise_for_status()
            self.req.cookies = self.cf_req.cookies
            self.logger.debug("Login response code %s", response.status_code)
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting") from err

        self.logger.debug("Response is %s", response.text)
        response_url = re.search(
            r'"(https:[^"]+?ticket=[^"]+)"', response.text)

        if not response_url:
            raise GarminConnectAuthenticationError("Authentication error")

        response_url = re.sub(r'\\', '', response_url.group(1))
        self.logger.debug("Fetching profile info using found response url")
        try:
            response = self.req.get(response_url)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")

            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting") from err

        self.logger.debug("Profile info is %s", response.text)

        self.user_prefs = self.parse_json(
            response.text, 'VIEWER_USERPREFERENCES')
        self.unit_system = self.user_prefs['measurementSystem']
        self.logger.debug("Unit system is %s", self.unit_system)

        self.social_profile = self.parse_json(
            response.text, 'VIEWER_SOCIAL_PROFILE')
        self.display_name = self.social_profile['displayName']
        self.full_name = self.social_profile['fullName']
        self.logger.debug("Display name is %s", self.display_name)
        self.logger.debug("Fullname is %s", self.full_name)

    def parse_json(self, html, key):
        """
        Find and return json data
        """
        found = re.search(key + r" = JSON.parse\(\"(.*)\"\);", html, re.M)
        if found:
            text = found.group(1).replace('\\"', '"')
            return json.loads(text)

    def fetch_data(self, url):
        """
        Fetch and return data
        """
        try:
            response = self.req.get(url, headers=self.headers)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")

            self.logger.debug("Fetch response code %s", response.status_code)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            self.logger.debug(
                "Exception occurred during data retrieval - perhaps session expired - trying relogin: %s" % err)
            self.login()
            try:
                response = self.req.get(url, headers=self.headers)
                if response.status_code == 429:
                    raise GarminConnectTooManyRequestsError(
                        "Too many requests")

                self.logger.debug("Fetch response code %s",
                                  response.status_code)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.logger.debug(
                    "Exception occurred during data retrieval, relogin without effect: %s" % err)
                raise GarminConnectConnectionError("Error connecting") from err

        resp_json = response.json()
        self.logger.debug("Fetch response json %s", resp_json)
        return resp_json

    def get_full_name(self):
        """
        Return full name
        """
        return self.full_name

    def get_unit_system(self):
        """
        Return unit system
        """
        return self.unit_system

    def get_stats_and_body(self, cdate):
        """
        Return activity data and body composition
        """
        return ({**self.get_stats(cdate), **self.get_body_composition(cdate)['totalAverage']})

    def get_stats(self, cdate):   # cDate = 'YYY-mm-dd'
        """
        Fetch available activity data
        """
        summaryurl = self.url_user_summary + \
            self.display_name + '?' + 'calendarDate=' + cdate
        self.logger.debug("Fetching statistics %s", summaryurl)
        try:
            response = self.req.get(summaryurl, headers=self.headers)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")

            self.logger.debug("Statistics response code %s",
                              response.status_code)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting") from err

        resp_json = response.json()
        if resp_json['privacyProtected'] is True:
            self.logger.debug("Session expired - trying relogin")
            self.login()
            try:
                response = self.req.get(summaryurl, headers=self.headers)
                if response.status_code == 429:
                    raise GarminConnectTooManyRequestsError(
                        "Too many requests")

                self.logger.debug(
                    "Statistics response code %s", response.status_code)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.logger.debug(
                    "Exception occurred during statistics retrieval, relogin without effect: %s" % err)
                raise GarminConnectConnectionError("Error connecting") from err
            else:
                resp_json = response.json()

        self.logger.debug("Statistics response json %s", resp_json)
        return resp_json

    def get_heart_rates(self, cdate):   # cDate = 'YYYY-mm-dd'
        """
        Fetch available heart rates data
        """
        hearturl = self.url_heartrates + self.display_name + '?date=' + cdate
        self.logger.debug("Fetching heart rates with url %s", hearturl)

        return self.fetch_data(hearturl)

    def get_sleep_data(self, cdate):   # cDate = 'YYYY-mm-dd'
        """
        Fetch available sleep data
        """
        sleepurl = self.url_sleepdata + self.display_name + '?date=' + cdate
        self.logger.debug("Fetching sleep data with url %s", sleepurl)

        return self.fetch_data(sleepurl)

    def get_steps_data(self, cdate):   # cDate = 'YYYY-mm-dd'
        """
        Fetch available steps data
        """
        steps_url = self.url_user_summary_chart + self.display_name + '?date=' + cdate
        self.logger.debug("Fetching steps data with url %s", steps_url)

        return self.fetch_data(steps_url)

    def get_body_composition(self, cdate):   # cDate = 'YYYY-mm-dd'
        """
        Fetch available body composition data (only for cDate)
        """
        bodycompositionurl = self.url_body_composition + \
            '?startDate=' + cdate + '&endDate=' + cdate
        self.logger.debug(
            "Fetching body composition with url %s", bodycompositionurl)

        return self.fetch_data(bodycompositionurl)

    def get_activities(self, start, limit):
        """
        Fetch available activities
        """
        activitiesurl = self.url_activities + '?start=' + \
            str(start) + '&limit=' + str(limit)
        self.logger.debug("Fetching activities with url %s", activitiesurl)

        return self.fetch_data(activitiesurl)

    def get_activities_by_date(self, startdate, enddate, activitytype):
        """
        Fetch available activities between specific dates

        :param startdate: String in the format YYYY-MM-DD
        :param enddate: String in the format YYYY-MM-DD
        :param activitytype: (Optional) Type of activity you are searching
                             Possible values are [cycling, running, swimming,
                             multi_sport, fitness_equipment, hiking, walking, other]
        :return: list of JSON activities
        """

        activities = []
        start = 0
        limit = 20
        returndata = True
        # mimicking the behavior of the web interface that fetches 20 activities at a time
        # and automatically loads more on scroll
        if activitytype:
            activityslug = "&activityType=" + str(activitytype)
        else:
            activityslug = ""
        while returndata:
            activitiesurl = self.url_activities + '?startDate=' + str(startdate) + '&endDate=' + str(
                enddate) + '&start=' + str(start) + '&limit=' + str(limit) + activityslug
            self.logger.debug("Fetching activities with url %s", activitiesurl)
            act = self.fetch_data(activitiesurl)
            if act:
                activities.extend(act)
                start = start + limit
            else:
                returndata = False

        return activities

    def get_excercise_sets(self, activity_id):
        activity_id = str(activity_id)
        exercisesetsurl = f"{self.url_activity}{activity_id}"
        self.logger.debug(
            f"Fetching excercise sets for activity_id {activity_id}")

        return self.fetch_data(exercisesetsurl)

    def get_activity_splits(self, activity_id):
        activity_id = str(activity_id)
        splits_url = f"{self.url_activity}{activity_id}/splits"
        self.logger.debug(
            f"Fetching splits for activity_id {activity_id}")

        return self.fetch_data(splits_url)

    def get_activity_split_summaries(self, activity_id):
        activity_id = str(activity_id)
        split_summaries_url = f"{self.url_activity}{activity_id}/split_summaries"
        self.logger.debug(
            f"Fetching split summaries for activity_id {activity_id}")

        return self.fetch_data(split_summaries_url)

    def get_activity_weather(self, activity_id):
        activity_id = str(activity_id)
        activity_weather_url = f"{self.url_activity}{activity_id}/weather"
        self.logger.debug(
            f"Fetching weather for activity_id {activity_id}")

        return self.fetch_data(activity_weather_url)

    def get_activity_hr_in_timezones(self, activity_id):
        activity_id = str(activity_id)
        activity_hr_timezone_url = f"{self.url_activity}{activity_id}/hrTimeInZones"
        self.logger.debug(
            f"Fetching split summaries for activity_id {activity_id}")

        return self.fetch_data(activity_hr_timezone_url)

    def get_activity_details(self, activity_id, maxChartSize=2000, maxPolylineSize=4000):
        activity_id = str(activity_id)
        params = f"maxChartSize={maxChartSize}&maxPolylineSize={maxPolylineSize}"
        details_url = f"{self.url_activity}{activity_id}/details?{params}"
        self.logger.debug(
            f"Fetching details for activity_id {activity_id}")

        return self.fetch_data(details_url)

    def get_personal_record(self, owner_display_name):
        personal_records_url = f"{self.url_personal_record}prs/{owner_display_name}"
        self.logger.debug(
            f"Fetching prs for owner {owner_display_name}")

        return self.fetch_data(personal_records_url)

    def get_devices(self):
        """
        Fetch available devices for the current account
        """
        devicesurl = self.url_device_list
        self.logger.debug(
            "Fetching available devices for the current account with url %s", devicesurl)

        return self.fetch_data(devicesurl)

    def get_device_settings(self, device_id):
        """
        Fetch device settings for current device
        """
        devicesurl = f"{self.url_device_service}device-info/settings/{device_id}"
        self.logger.debug("Fetching device settings with url %s", devicesurl)
        return self.fetch_data(devicesurl)

    def get_device_last_used(self):
        """
        Fetch device last used
        """
        device_last_used_url = f"{self.url_device_service}mylastused"
        self.logger.debug(
            "Fetching device last used with url %s", device_last_used_url)
        return self.fetch_data(device_last_used_url)

    def get_hydration_data(self, cdate):   # cDate = 'YYYY-mm-dd'
        """
        Fetch available hydration data
        """
        hydration_url = self.url_hydrationdata + cdate
        self.logger.debug("Fetching hydration data with url %s", hydration_url)

        return self.fetch_data(hydration_url)

    class ActivityDownloadFormat(Enum):
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
            Garmin.ActivityDownloadFormat.ORIGINAL: f"{self.url_fit_download}{activity_id}",
            Garmin.ActivityDownloadFormat.TCX: f"{self.url_tcx_download}{activity_id}",
            Garmin.ActivityDownloadFormat.GPX: f"{self.url_gpx_download}{activity_id}",
            Garmin.ActivityDownloadFormat.KML: f"{self.url_kml_download}{activity_id}",
            Garmin.ActivityDownloadFormat.CSV: f"{self.url_csv_download}{activity_id}",
        }
        if dl_fmt not in urls:
            raise ValueError(f"Unexpected value {dl_fmt} for dl_fmt")
        url = urls[dl_fmt]

        self.logger.debug(f"Downloading from {url}")
        try:
            response = self.req.get(url, headers=self.headers)
            if response.status_code == 429:
                raise GarminConnectTooManyRequestsError("Too many requests")
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting")
        return response.content


class GarminConnectConnectionError(Exception):
    """Raised when communication ended in error."""

    def __init__(self, status):
        """Initialize."""
        super(GarminConnectConnectionError, self).__init__(status)
        self.status = status


class GarminConnectTooManyRequestsError(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, status):
        """Initialize."""
        super(GarminConnectTooManyRequestsError, self).__init__(status)
        self.status = status


class GarminConnectAuthenticationError(Exception):
    """Raised when login returns wrong result."""

    def __init__(self, status):
        """Initialize."""
        super(GarminConnectAuthenticationError, self).__init__(status)
        self.status = status
