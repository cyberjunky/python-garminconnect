import json
import re
import requests
from datetime import date


BASE_URL = 'https://connect.garmin.com'
SSO_URL = 'https://sso.garmin.com/sso'
MODERN_URL = 'https://connect.garmin.com/modern'
SIGNIN_URL = 'https://sso.garmin.com/sso/signin'
HR_URL = 'https://connect.garmin.com/modern/proxy/wellness-service/wellness/dailyHeartRate/'

cdate = str(date.today())

class Garmin(object):
    """
    Object using Garmin Connect 's API-method.
    See https://connect.garmin.com/
    """

    url = MODERN_URL + '/proxy/usersummary-service/usersummary/daily/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
        'origin': 'https://sso.garmin.com'
    }

    def __init__(self, username, password):
        """
        Init module
        """
        self.username = username
        self.password = password
        self.req = requests.session()

        self.login(self.username, self.password)

    def login(self, username, password):
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

        response = self.req.get(SIGNIN_URL, headers=self.headers, params=params)
        response.raise_for_status()

        data = {
            'username': username,
            'password': password,
            'embed': 'true',
            'lt': 'e1s1',
            '_eventId': 'submit',
            'displayNameRequired': 'false'
        }

        response = self.req.post(SIGNIN_URL, headers=self.headers, params=params, data=data)
        response.raise_for_status()

        response_url = re.search(r'"(https:[^"]+?ticket=[^"]+)"', response.text)
        if not response_url:
            raise Exception('Could not find response URL')
        response_url = re.sub(r'\\', '', response_url.group(1))
        response = self.req.get(response_url)

        self.user_prefs = self.parse_json(response.text, 'VIEWER_USERPREFERENCES')
        self.display_name = self.user_prefs['displayName']
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
        Fetch all available data
        """
        getURL = self.url + self.display_name + '?' + 'calendarDate=' + cdate
        response = self.req.get(getURL, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def fetch_heart_rates(self, cdate):   #  cDate = 'YYYY-mm-dd'
        """
        Fetch all available data
        """
        getURL = HR_URL + self.display_name + '?date=' + cdate
        response = self.req.get(getURL, headers=self.headers)
        response.raise_for_status()
        return response.json()
