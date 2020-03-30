# -*- coding: utf-8 -*-
"""Python 3 API wrapper for Garmin Connect to get your statistics."""
import logging
import json
import re
import requests

from .__version__ import __version__

BASE_URL = 'https://connect.garmin.com'
SSO_URL = 'https://sso.garmin.com/sso'
MODERN_URL = 'https://connect.garmin.com/modern'
SIGNIN_URL = 'https://sso.garmin.com/sso/signin'

class Garmin(object):
    """
    Object using Garmin Connect 's API-method.
    See https://connect.garmin.com/
    """
    url_user_summary = MODERN_URL + '/proxy/usersummary-service/usersummary/daily/'
    url_heartrates = MODERN_URL + '/proxy/wellness-service/wellness/dailyHeartRate/'
    url_body_composition = MODERN_URL + '/proxy/weight-service/weight/daterangesnapshot'
    url_activities = MODERN_URL + '/proxy/activitylist-service/activities/search/activities'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
        'origin': 'https://sso.garmin.com'
    }

    def __init__(self, email, password):
        """
        Init module
        """
        self.email = email
        self.password = password
        self.req = requests.session()
        self.logger = logging.getLogger(__name__)
        self.display_name = ""
        self.full_name = ""
        self.unit_system = ""


    def login(self):
        """
        Login to portal
        """
        params = {
            'webhost': BASE_URL,
            'service': MODERN_URL,
            'source': SIGNIN_URL,
            'redirectAfterAccountLoginUrl': MODERN_URL,
            'redirectAfterAccountCreationUrl': MODERN_URL,
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

        data = {
            'username': self.email,
            'password': self.password,
            'embed': 'true',
            'lt': 'e1s1',
            '_eventId': 'submit',
            'displayNameRequired': 'false'
        }

        self.logger.debug("Login to Garmin Connect using POST url %s", SIGNIN_URL)
        try:
            response = self.req.post(SIGNIN_URL, headers=self.headers, params=params, data=data)
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting")

        if response.status_code == 429:
            raise GarminConnectTooManyRequestsError("Too many requests")

        self.logger.debug("Login response code %s", response.status_code)
        response.raise_for_status()

        response_url = re.search(r'"(https:[^"]+?ticket=[^"]+)"', response.text)
        self.logger.debug("Response is %s", response.text)
        if response.status_code == 429:
            raise GarminConnectTooManyRequestsError("Too many requests")

        if not response_url:
            raise GarminConnectAuthenticationError("Authentication error")

        response_url = re.sub(r'\\', '', response_url.group(1))
        self.logger.debug("Fetching profile info using found response url")
        try:
            response = self.req.get(response_url)
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting")

        self.logger.debug("Profile info is %s", response.text)

        if response.status_code == 429:
            raise GarminConnectTooManyRequestsError("Too many requests")

        self.user_prefs = self.parse_json(response.text, 'VIEWER_USERPREFERENCES')
        self.unit_system = self.user_prefs['measurementSystem']
        self.logger.debug("Unit system is %s", self.unit_system)

        self.social_profile = self.parse_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.display_name = self.social_profile['displayName']
        self.full_name = self.social_profile['fullName']
        self.logger.debug("Display name is %s", self.display_name)
        self.logger.debug("Fullname is %s", self.full_name)
        response.raise_for_status()


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
            self.logger.debug("Fetch response code %s, and json %s", response.status_code, response.json())
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            self.logger.debug("Exception occured during data retrieval - perhaps session expired - trying relogin: %s" % err)
            self.login(self.email, self.password)
            try:
                response = self.req.get(url, headers=self.headers)
                self.logger.debug("Fetch response code %s, and json %s", response.status_code, response.json())
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.logger.debug("Exception occured during data retrieval, relogin without effect: %s" % err)
                raise GarminConnectConnectionError("Error connecting")

        if response.status_code == 429:
            raise GarminConnectTooManyRequestsError("Too many requests")

        return response.json()


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
        return ({**self.get_stats(cdate), **self.get_body_composition(cdate)})


    def get_stats(self, cdate):   # cDate = 'YYY-mm-dd'
        """
        Fetch available activity data
        """
        summaryurl = self.url_user_summary + self.display_name + '?' + 'calendarDate=' + cdate
        self.logger.debug("Fetching statistics %s", summaryurl)
        try:
            response = self.req.get(summaryurl, headers=self.headers)
            self.logger.debug("Statistics response code %s, and json %s", response.status_code, response.json())
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise GarminConnectConnectionError("Error connecting")

        if response.status_code == 429:
            raise GarminConnectTooManyRequestsError("Too many requests")

        if response.json()['privacyProtected'] is True:
            self.logger.debug("Session expired - trying relogin")
            self.login()
            try:
                response = self.req.get(summaryurl, headers=self.headers)
                self.logger.debug("Statistics response code %s, and json %s", response.status_code, response.json())
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.logger.debug("Exception occured during statistics retrieval, relogin without effect: %s" % err)
                raise GarminConnectConnectionError("Error connecting")

        return response.json()


    def get_heart_rates(self, cdate):   # cDate = 'YYYY-mm-dd'
        """
        Fetch available heart rates data
        """
        hearturl = self.url_heartrates + self.display_name + '?date=' + cdate
        self.logger.debug("Fetching heart rates with url %s", hearturl)

        return self.fetch_data(hearturl)


    def get_body_composition(self, cdate):   # cDate = 'YYYY-mm-dd'
        """
        Fetch available body composition data (only for cDate)
        """
        bodycompositionurl = self.url_body_composition + '?startDate=' + cdate + '&endDate=' + cdate
        self.logger.debug("Fetching body composition with url %s", bodycompositionurl)

        return self.fetch_data(bodycompositionurl)


    def get_activities(self, start, limit):
        """
        Fetch available activities
        """
        activitiesurl = self.url_activities + '?start=' + str(start) + '&limit=' + str(limit)
        self.logger.debug("Fetching activities with url %s", activitiesurl)

        return self.fetch_data(activitiesurl)


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

