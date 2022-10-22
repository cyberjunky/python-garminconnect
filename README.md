[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)

# Python: Garmin Connect

Python 3 API wrapper for Garmin Connect to get your statistics.

## About

This package allows you to request garmin device, activity and health data from your Garmin Connect account.
See <https://connect.garmin.com/>

## Installation

```bash
pip3 install garminconnect
```

## API Demo Program 

I wrote this for testing and playing with all available/known API calls.  
If you run it from the python-garmin connect directory it will use the library code beneath it, so you can develop without reinstalling the package.  

The code also demostrate how to implement session saving and re-using of the cookies.  

You can set enviroment variables with your credentials like so, this is optional:
```
export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>
```

Install the pre-requisites for the example program. (not all are needed for using the library package)  

```bash
pip3 install cloudscaper readchar requests json pwinput

```

Or you can just run the program and enter your credentials when asked, it will create and save a session file and use that until it's outdated/invalid.

```
python3 ./example.py

*** Garmin Connect API Demo by cyberjunky ***

1 -- Get full name
2 -- Get unit system
3 -- Get activity data for '2022-10-21'
4 -- Get activity data for '2022-10-21' (compatible with garminconnect-ha)
5 -- Get body composition data for '2022-10-21' (compatible with garminconnect-ha)
6 -- Get body composition data for from '2022-10-14' to '2022-10-21' (to be compatible with garminconnect-ha)
7 -- Get stats and body composition data for '2022-10-21'
8 -- Get steps data for '2022-10-21'
9 -- Get heart rate data for '2022-10-21'
0 -- Get training readiness data for '2022-10-21'
. -- Get training status data for '2022-10-21'
a -- Get resting heart rate data for 2022-10-21'
b -- Get hydration data for '2022-10-21'
c -- Get sleep data for '2022-10-21'
d -- Get stress data for '2022-10-21'
e -- Get respiration data for '2022-10-21'
f -- Get SpO2 data for '2022-10-21'
g -- Get max metric data (like vo2MaxValue and fitnessAge) for '2022-10-21'
h -- Get personal record for user
i -- Get earned badges for user
j -- Get adhoc challenges data from start '0' and limit '100'
k -- Get available badge challenges data from '1' and limit '100'
l -- Get badge challenges data from '1' and limit '100'
m -- Get non completed badge challenges data from '1' and limit '100'
n -- Get activities data from start '0' and limit '100'
o -- Download activities data by date from '2022-10-14' to '2022-10-21'
p -- Get all kinds of activities data from '0'
r -- Upload activity data from file 'MY_ACTIVITY.fit'
s -- Get all kinds of Garmin device info
Z -- Logout Garmin Connect portal
q -- Exit

Make your selection: 

```

This is the example code, also available in example.py.

```python
#!/usr/bin/env python3
"""
pip3 install cloudscaper readchar requests json pwinput

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

"""
import datetime
import json
import logging
import os
import sys

import pwinput
import readchar
import requests

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Configure debug logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
api = None

# Example ranges
today = datetime.date.today()
startdate = today - datetime.timedelta(days=7)
start = 0
limit = 100
start_badge = 1  # badges calls start counting at 1
activitytype = ""  # Possible values are [cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other]
activityfile = "MY_ACTIVITY.fit"

menu_options = {
    "1": "Get full name",
    "2": "Get unit system",
    "3": f"Get activity data for '{today.isoformat()}'",
    "4": f"Get activity data for '{today.isoformat()}' (compatible with garminconnect-ha)",
    "5": f"Get body composition data for '{today.isoformat()}' (compatible with garminconnect-ha)",
    "6": f"Get body composition data for from '{startdate.isoformat()}' to '{today.isoformat()}' (to be compatible with garminconnect-ha)",
    "7": f"Get stats and body composition data for '{today.isoformat()}'",
    "8": f"Get steps data for '{today.isoformat()}'",
    "9": f"Get heart rate data for '{today.isoformat()}'",
    "0": f"Get training readiness data for '{today.isoformat()}'",
    ".": f"Get training status data for '{today.isoformat()}'",
    "a": f"Get resting heart rate data for {today.isoformat()}'",
    "b": f"Get hydration data for '{today.isoformat()}'",
    "c": f"Get sleep data for '{today.isoformat()}'",
    "d": f"Get stress data for '{today.isoformat()}'",
    "e": f"Get respiration data for '{today.isoformat()}'",
    "f": f"Get SpO2 data for '{today.isoformat()}'",
    "g": f"Get max metric data (like vo2MaxValue and fitnessAge) for '{today.isoformat()}'",
    "h": "Get personal record for user",
    "i": "Get earned badges for user",
    "j": f"Get adhoc challenges data from start '{start}' and limit '{limit}'",
    "k": f"Get available badge challenges data from '{start_badge}' and limit '{limit}'",
    "l": f"Get badge challenges data from '{start_badge}' and limit '{limit}'",
    "m": f"Get non completed badge challenges data from '{start_badge}' and limit '{limit}'",
    "n": f"Get activities data from start '{start}' and limit '{limit}'",
    "o": f"Download activities data by date from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "p": f"Get all kinds of activities data from '{start}'",
    "r": f"Upload activity data from file '{activityfile}'",
    "s": "Get all kinds of Garmin device info",
    "Z": "Logout Garmin Connect portal",
    "q": "Exit",
}


def get_credentials():
    """Get user credentials."""
    email = input("Login e-mail: ")
    password = pwinput.pwinput(prompt='Password: ')

    return email, password


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        ## Try to load the previous session
        with open("session.json") as f:
            saved_session = json.load(f)

            print(
                "Login to Garmin Connect using session loaded from 'session.json'...\n"
            )

            # Use the loaded session for initializing the API (without need for credentials)
            api = Garmin(session_data=saved_session)

            # Login using the
            api.login()

    except (FileNotFoundError, GarminConnectAuthenticationError):
        # Login to Garmin Connect portal with credentials since session is invalid or not presentlastweek.
        print(
            "Session file not present or invalid, login with your credentials, please wait...\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            api = Garmin(email, password)
            api.login()

            # Save session dictionary to json file for future use
            with open("session.json", "w", encofromding="utf-8") as f:
                json.dump(api.session_data, f, ensure_ascii=False, indent=4)
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error("Error occurred during Garmin Connect communication: %s", err)
            return None

    return api


def print_menu():
    """Print examples menu."""
    for key in menu_options.keys():
        print(f"{key} -- {menu_options[key]}")
    print("Make your selection: ", end="", flush=True)


def switch(api, i):
    """Run selected API call."""

    # Exit example program
    if i == "q":
        print("Bye!")
        sys.exit()

    # Skip requests if login failed
    if api:
        try:
            print(f"\n\nExecuting: {menu_options[i]}\n")

            # USER BASICS
            if i == "1":
                # Get full name from profile
                logger.info(api.get_full_name())
            elif i == "2":
                # Get unit system from profile
                logger.info(api.get_unit_system())

            # USER STATISTIC SUMMARIES
            elif i == "3":
                # Get activity data for 'YYYY-MM-DD'
                logger.info(api.get_stats(today.isoformat()))
            elif i == "4":
                # Get activity data (to be compatible with garminconnect-ha)
                logger.info(api.get_user_summary(today.isoformat()))
            elif i == "5":
                # Get body composition data for 'YYYY-MM-DD' (to be compatible with garminconnect-ha)
                logger.info(api.get_body_composition(today.isoformat()))
            elif i == "6":
                # Get body composition data for multiple days 'YYYY-MM-DD' (to be compatible with garminconnect-ha)
                logger.info(
                    api.get_body_composition(startdate.isoformat(), today.isoformat())
                )
            elif i == "7":
                # Get stats and body composition data for 'YYYY-MM-DD'
                logger.info(api.get_stats_and_body(today.isoformat()))

            # USER STATISTICS LOGGED
            elif i == "8":
                # Get steps data for 'YYYY-MM-DD'
                logger.info(api.get_steps_data(today.isoformat()))
            elif i == "9":
                # Get heart rate data for 'YYYY-MM-DD'
                logger.info(api.get_heart_rates(today.isoformat()))
            elif i == "0":
                # Get training readiness data for 'YYYY-MM-DD'
                logger.info(api.get_training_readiness(today.isoformat()))
            elif i == ".":
                # Get training status data for 'YYYY-MM-DD'
                logger.info(api.get_training_status(today.isoformat()))
            elif i == "a":
                # Get resting heart rate data for 'YYYY-MM-DD'
                logger.info(api.get_rhr_day(today.isoformat()))
            elif i == "b":
                # Get hydration data 'YYYY-MM-DD'
                logger.info(api.get_hydration_data(today.isoformat()))
            elif i == "c":
                # Get sleep data for 'YYYY-MM-DD'
                logger.info(api.get_sleep_data(today.isoformat()))
            elif i == "d":
                # Get stress data for 'YYYY-MM-DD'
                logger.info(api.get_stress_data(today.isoformat()))
            elif i == "e":
                # Get respiration data for 'YYYY-MM-DD'
                logger.info(api.get_respiration_data(today.isoformat()))
            elif i == "f":
                # Get SpO2 data for 'YYYY-MM-DD'
                logger.info(api.get_spo2_data(today.isoformat()))
            elif i == "g":
                # Get max metric data (like vo2MaxValue and fitnessAge) for 'YYYY-MM-DD'
                logger.info(api.get_max_metrics(today.isoformat()))
            elif i == "h":
                # Get personal record for user
                logger.info(api.get_personal_record())
            elif i == "i":
                # Get earned badges for user
                logger.info(api.get_earned_badges())
            elif i == "j":
                # Get adhoc challenges data from start and limit
                logger.info(
                    api.get_adhoc_challenges(start, limit)
                )  # 1=start, 100=limit
            elif i == "k":
                # Get available badge challenges data from start and limit
                logger.info(
                    api.get_available_badge_challenges(start_badge, limit)
                )  # 1=start, 100=limit
            elif i == "l":
                # Get badge challenges data from start and limit
                logger.info(
                    api.get_badge_challenges(start_badge, limit)
                )  # 1=start, 100=limit
            elif i == "m":
                # Get non completed badge challenges data from start and limit
                logger.info(
                    api.get_non_completed_badge_challenges(start_badge, limit)
                )  # 1=start, 100=limit

            # ACTIVITIES
            elif i == "n":
                # Get activities data from start and limit
                activities = api.get_activities(start, limit)  # 0=start, 1=limit
                logger.info(activities)
            elif i == "o":
                # Get activities data from startdate 'YYYY-MM-DD' to enddate 'YYYY-MM-DD', with (optional) activitytype
                # Possible values are [cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other]
                activities = api.get_activities_by_date(
                    startdate.isoformat(), today.isoformat(), activitytype
                )

                # Get last activity
                logger.info(api.get_last_activity())

                # Download an Activity
                for activity in activities:
                    activity_id = activity["activityId"]
                    logger.info("api.download_activities(%s)", activity_id)

                    gpx_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.GPX
                    )
                    output_file = f"./{str(activity_id)}.gpx"
                    with open(output_file, "wb") as fb:
                        fb.write(gpx_data)

                    tcx_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.TCX
                    )
                    output_file = f"./{str(activity_id)}.tcx"
                    with open(output_file, "wb") as fb:
                        fb.write(tcx_data)

                    zip_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.ORIGINAL
                    )
                    output_file = f"./{str(activity_id)}.zip"
                    with open(output_file, "wb") as fb:
                        fb.write(zip_data)

                    csv_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.CSV
                    )
                    output_file = f"./{str(activity_id)}.csv"
                    with open(output_file, "wb") as fb:
                        fb.write(csv_data)

            elif i == "p":
                # Get activities data from start and limit
                activities = api.get_activities(start, limit)  # 0=start, 1=limit

                # Get activity splits
                first_activity_id = activities[0].get("activityId")

                logger.info(api.get_activity_splits(first_activity_id))

                # Get activity split summaries for activity id
                logger.info(api.get_activity_split_summaries(first_activity_id))

                # Get activity weather data for activity
                logger.info(api.get_activity_weather(first_activity_id))

                # Get activity hr timezones id
                logger.info(api.get_activity_hr_in_timezones(first_activity_id))

                # Get activity details for activity id
                logger.info(api.get_activity_details(first_activity_id))

                # Get gear data for activity id
                logger.info(api.get_activity_gear(first_activity_id))

                # Activity self evaluation data for activity id
                logger.info(api.get_activity_evaluation(first_activity_id))

            elif i == "r":
                # Upload activity from file
                logger.info(api.upload_activity(activityfile))

            # DEVICES
            elif i == "s":
                # Get Garmin devices
                devices = api.get_devices()
                logger.info(devices)

                # Get device last used
                device_last_used = api.get_device_last_used()
                logger.info(device_last_used)

                for device in devices:
                    device_id = device["deviceId"]
                    logger.info(api.get_device_settings(device_id))

                # Get device settings
                for device in devices:
                    device_id = device["deviceId"]
                    logger.info(api.get_device_settings(device_id))

            elif i == "Z":
                # Logout Garmin Connect portal
                api.logout()
                api = None

        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error("Error occurred during Garmin Connect communication: %s", err)
        except KeyError:
            # Invalid menu option choosen
            pass
    else:
        print("Could not login to Garmin Connect, try again later.")

# Main program loop
while True:
    # Display header and login
    print("\n*** Garmin Connect API Demo by cyberjunky ***\n")

    # Init API
    if not api:
        api = init_api(email, password)

    # Display menu
    print_menu()
    option = readchar.readkey()
    switch(api, option)
```

## Donations
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)
