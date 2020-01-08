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
    url_activities = MODERN_URL + '/proxy/usersummary-service/usersummary/daily/'
    url_heartrates = MODERN_URL + '/proxy/wellness-service/wellness/dailyHeartRate/'
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

        self.login(self.email, self.password)

    def login(self, email, password):
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

#        self.logger.debug("Login to Garmin Connect using GET url %s", SIGNIN_URL)
#        response = self.req.get(SIGNIN_URL, headers=self.headers, params=params)
#        response.raise_for_status()

        data = {
            'username': email,
            'password': password,
            'embed': 'true',
            'lt': 'e1s1',
            '_eventId': 'submit',
            'displayNameRequired': 'false'
        }

        self.logger.debug("Login to Garmin Connect using POST url %s", SIGNIN_URL)
        response = self.req.post(SIGNIN_URL, headers=self.headers, params=params, data=data)
        response.raise_for_status()

        response_url = re.search(r'"(https:[^"]+?ticket=[^"]+)"', response.text)
        self.logger.debug("Response is %s", response.text)
        if not response_url:
            raise Exception('Could not find response url')
        response_url = re.sub(r'\\', '', response_url.group(1))
        self.logger.debug("Fetching displayname using found response url")
        response = self.req.get(response_url)

        self.user_prefs = self.parse_json(response.text, 'VIEWER_USERPREFERENCES')
        self.display_name = self.user_prefs['displayName']
        self.logger.debug("Display name is %s", self.display_name)
        response.raise_for_status()

    def parse_json(self, html, key):
        """
        Find and return json data
        """
        found = re.search(key + r" = JSON.parse\(\"(.*)\"\);", html, re.M)
        if found:
            text = found.group(1).replace('\\"', '"')
            return json.loads(text)

    def fetch_stats(self, cdate):   # cDate = 'YYY-mm-dd'
        """
        Fetch available activity data
        """
        acturl = self.url_activities + self.display_name + '?' + 'calendarDate=' + cdate
        self.logger.debug("Fetching activities %s", acturl)
        try:
            response = self.req.get(acturl, headers=self.headers)
            self.logger.debug("Activities response code %s, and json %s", response.status_code, response.json())
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            self.logger.error("Exception occured during activities retrieval: %s" % err)
            return

        if response.json()['privacyProtected'] is True:
            self.logger.debug("Session expired - trying relogin")
            self.login(self.email, self.password)
            try:
                response = self.req.get(acturl, headers=self.headers)
                self.logger.debug("Activities response code %s, and json %s", response.status_code, response.json())
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.logger.error("Exception occured during activities retrieval: %s" % err)
                return
        return response.json()

    def fetch_heart_rates(self, cdate):   # cDate = 'YYYY-mm-dd'
        """
        Fetch available heart rates data
        """
        hearturl = self.url_heartrates + self.display_name + '?date=' + cdate
        self.logger.debug("Fetching heart rates with url %s", hearturl)
        try:
            response = self.req.get(hearturl, headers=self.headers)
            self.logger.debug("Heart Rates response code %s, and json %s", response.status_code, response.json())
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            self.logger.debug("Exception occured during heart rate retrieval - perhaps session expired - trying relogin: %s" % err)
            self.login(self.email, self.password)
            try:
                response = self.req.get(hearturl, headers=self.headers)
                self.logger.debug("Heart Rates response code %s, and json %s", response.status_code, response.json())
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.logger.debug("Exception occured during stats retrieval, relogin without effect: %s" % err)
                return
        return response.json()
