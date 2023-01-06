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

The code also demonstrates how to implement session saving and re-using of the cookies.  

You can set environment variables with your credentials like so, this is optional:

```bash
export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>
```

Install the pre-requisites for the example program (not all are needed for using the library package):

```bash
pip3 install cloudscraper readchar requests pwinput
```

Or you can just run the program and enter your credentials when asked, it will create and save a session file and use that until it's outdated/invalid.

```
python3 ./example.py
*** Garmin Connect API Demo by cyberjunky ***

Login to Garmin Connect using session loaded from 'session.json'...

1 -- Get full name
2 -- Get unit system
3 -- Get activity data for '2023-01-06'
4 -- Get activity data for '2023-01-06' (compatible with garminconnect-ha)
5 -- Get body composition data for '2023-01-06' (compatible with garminconnect-ha)
6 -- Get body composition data for from '2022-12-30' to '2023-01-06' (to be compatible with garminconnect-ha)
7 -- Get stats and body composition data for '2023-01-06'
8 -- Get steps data for '2023-01-06'
9 -- Get heart rate data for '2023-01-06'
0 -- Get training readiness data for '2023-01-06'
. -- Get training status data for '2023-01-06'
a -- Get resting heart rate data for 2023-01-06'
b -- Get hydration data for '2023-01-06'
c -- Get sleep data for '2023-01-06'
d -- Get stress data for '2023-01-06'
e -- Get respiration data for '2023-01-06'
f -- Get SpO2 data for '2023-01-06'
g -- Get max metric data (like vo2MaxValue and fitnessAge) for '2023-01-06'
h -- Get personal record for user
i -- Get earned badges for user
j -- Get adhoc challenges data from start '0' and limit '100'
k -- Get available badge challenges data from '1' and limit '100'
l -- Get badge challenges data from '1' and limit '100'
m -- Get non completed badge challenges data from '1' and limit '100'
n -- Get activities data from start '0' and limit '100'
o -- Get last activity
p -- Download activities data by date from '2022-12-30' to '2023-01-06'
r -- Get all kinds of activities data from '0'
s -- Upload activity data from file 'MY_ACTIVITY.fit'
t -- Get all kinds of Garmin device info
u -- Get active goals
v -- Get future goals
w -- Get past goals
y -- Get all Garmin device alarms
x -- Get Heart Rate Variability data (HRV) for '2023-01-06'
z -- Get progress summary from '2022-12-30' to '2023-01-06' for all metrics
G -- Get Gear'
Z -- Logout Garmin Connect portal
q -- Exit

Make your selection: 

```

This is some example code, and probably older than the latest code which can be found in 'example.py'.

```python
#!/usr/bin/env python3
"""
pip3 install cloudscraper requests readchar pwinput

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

"""
import datetime
import json
import logging
import os
import sys

import requests
import pwinput
import readchar

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

# Example selections and settings
today = datetime.date.today()
startdate = today - datetime.timedelta(days=7) # Select past week
start = 0
limit = 100
start_badge = 1  # Badge related calls calls start counting at 1
activitytype = ""  # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
activityfile = "MY_ACTIVITY.fit" # Supported file types are: .fit .gpx .tcx

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
    "o": "Get last activity",
    "p": f"Download activities data by date from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "r": f"Get all kinds of activities data from '{start}'",
    "s": f"Upload activity data from file '{activityfile}'",
    "t": "Get all kinds of Garmin device info",
    "Z": "Logout Garmin Connect portal",
    "q": "Exit",
}

def display_json(api_call, output):
    """Format API output for better readability."""
    dashed = "-"*20
    header = f"{dashed} {api_call} {dashed}"
    footer = "-"*len(header)
    print(header)
    print(json.dumps(output, indent=4))
    print(footer)


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
            with open("session.json", "w", encoding="utf-8") as f:
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
                display_json("api.get_full_name()", api.get_full_name())
            elif i == "2":
                # Get unit system from profile
                display_json("api.get_unit_system()", api.get_unit_system())

            # USER STATISTIC SUMMARIES
            elif i == "3":
                # Get activity data for 'YYYY-MM-DD'
                display_json(f"api.get_stats('{today.isoformat()}')", api.get_stats(today.isoformat()))
            elif i == "4":
                # Get activity data (to be compatible with garminconnect-ha)
                display_json(f"api.get_user_summary('{today.isoformat()}')", api.get_user_summary(today.isoformat()))
            elif i == "5":
                # Get body composition data for 'YYYY-MM-DD' (to be compatible with garminconnect-ha)
                display_json(f"api.get_body_composition('{today.isoformat()}')", api.get_body_composition(today.isoformat()))
            elif i == "6":
                # Get body composition data for multiple days 'YYYY-MM-DD' (to be compatible with garminconnect-ha)
                display_json(f"api.get_body_composition('{startdate.isoformat()}', '{today.isoformat()}')",
                    api.get_body_composition(startdate.isoformat(), today.isoformat())
                )
            elif i == "7":
                # Get stats and body composition data for 'YYYY-MM-DD'
                display_json(f"api.get_stats_and_body('{today.isoformat()}')", api.get_stats_and_body(today.isoformat()))

            # USER STATISTICS LOGGED
            elif i == "8":
                # Get steps data for 'YYYY-MM-DD'
                display_json(f"api.get_steps_data('{today.isoformat()}')", api.get_steps_data(today.isoformat()))
            elif i == "9":
                # Get heart rate data for 'YYYY-MM-DD'
                display_json(f"api.get_heart_rates('{today.isoformat()}')", api.get_heart_rates(today.isoformat()))
            elif i == "0":
                # Get training readiness data for 'YYYY-MM-DD'
                display_json(f"api.get_training_readiness('{today.isoformat()}')", api.get_training_readiness(today.isoformat()))
            elif i == ".":
                # Get training status data for 'YYYY-MM-DD'
                display_json(f"api.get_training_status('{today.isoformat()}')", api.get_training_status(today.isoformat()))
            elif i == "a":
                # Get resting heart rate data for 'YYYY-MM-DD'
                display_json(f"api.get_rhr_day('{today.isoformat()}')", api.get_rhr_day(today.isoformat()))
            elif i == "b":
                # Get hydration data 'YYYY-MM-DD'
                display_json(f"api.get_hydration_data('{today.isoformat()}')", api.get_hydration_data(today.isoformat()))
            elif i == "c":
                # Get sleep data for 'YYYY-MM-DD'
                display_json(f"api.get_sleep_data('{today.isoformat()}')", api.get_sleep_data(today.isoformat()))
            elif i == "d":
                # Get stress data for 'YYYY-MM-DD'
                display_json(f"api.get_stress_data('{today.isoformat()}')", api.get_stress_data(today.isoformat()))
            elif i == "e":
                # Get respiration data for 'YYYY-MM-DD'
                display_json(f"api.get_respiration_data('{today.isoformat()}')", api.get_respiration_data(today.isoformat()))
            elif i == "f":
                # Get SpO2 data for 'YYYY-MM-DD'
                display_json(f"api.get_spo2_data('{today.isoformat()}')", api.get_spo2_data(today.isoformat()))
            elif i == "g":
                # Get max metric data (like vo2MaxValue and fitnessAge) for 'YYYY-MM-DD'
                display_json(f"api.get_max_metrics('{today.isoformat()}')", api.get_max_metrics(today.isoformat()))
            elif i == "h":
                # Get personal record for user
                display_json("api.get_personal_record()", api.get_personal_record())
            elif i == "i":
                # Get earned badges for user
                display_json("api.get_earned_badges()", api.get_earned_badges())
            elif i == "j":
                # Get adhoc challenges data from start and limit
                display_json(
                    f"api.get_adhoc_challenges({start},{limit})", api.get_adhoc_challenges(start, limit)
                )  # 1=start, 100=limit
            elif i == "k":
                # Get available badge challenges data from start and limit
                display_json(
                    f"api.get_available_badge_challenges({start_badge}, {limit})", api.get_available_badge_challenges(start_badge, limit)
                )  # 1=start, 100=limit
            elif i == "l":
                # Get badge challenges data from start and limit
                display_json(
                    f"api.get_badge_challenges({start_badge}, {limit})", api.get_badge_challenges(start_badge, limit)
                )  # 1=start, 100=limit
            elif i == "m":
                # Get non completed badge challenges data from start and limit
                display_json(
                    f"api.get_non_completed_badge_challenges({start_badge}, {limit})", api.get_non_completed_badge_challenges(start_badge, limit)
                )  # 1=start, 100=limit

            # ACTIVITIES
            elif i == "n":
                # Get activities data from start and limit
                display_json(f"api.get_activities({start}, {limit})", api.get_activities(start, limit)) # 0=start, 1=limit
            elif i == "o":
                # Get last activity
                display_json("api.get_last_activity()", api.get_last_activity())
            elif i == "p":    
                # Get activities data from startdate 'YYYY-MM-DD' to enddate 'YYYY-MM-DD', with (optional) activitytype
                # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
                activities = api.get_activities_by_date(
                    startdate.isoformat(), today.isoformat(), activitytype
                )

                # Download activities
                for activity in activities:
                    activity_id = activity["activityId"]
                    display_json(f"api.download_activity({activity_id})", api.download_activity(activity_id))

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

            elif i == "r":
                # Get activities data from start and limit
                activities = api.get_activities(start, limit)  # 0=start, 1=limit

                # Get activity splits
                first_activity_id = activities[0].get("activityId")

                display_json(f"api.get_activity_splits({first_activity_id})", api.get_activity_splits(first_activity_id))

                # Get activity split summaries for activity id
                display_json(f"api.get_activity_split_summaries({first_activity_id})", api.get_activity_split_summaries(first_activity_id))

                # Get activity weather data for activity
                display_json(f"api.get_activity_weather({first_activity_id})", api.get_activity_weather(first_activity_id))

                # Get activity hr timezones id
                display_json(f"api.get_activity_hr_in_timezones({first_activity_id})", api.get_activity_hr_in_timezones(first_activity_id))

                # Get activity details for activity id
                display_json(f"api.get_activity_details({first_activity_id})", api.get_activity_details(first_activity_id))

                # Get gear data for activity id
                display_json(f"api.get_activity_gear({first_activity_id})", api.get_activity_gear(first_activity_id))

                # Activity self evaluation data for activity id
                display_json(f"api.get_activity_evaluation({first_activity_id})", api.get_activity_evaluation(first_activity_id))

            elif i == "s":
                # Upload activity from file
                display_json(f"api.upload_activity({activityfile})", api.upload_activity(activityfile))

            # DEVICES
            elif i == "t":
                # Get Garmin devices
                devices = api.get_devices()
                display_json("api.get_devices()", devices)

                # Get device last used
                device_last_used = api.get_device_last_used()
                display_json("api.get_device_last_used()", device_last_used)

                # Get settings per device
                for device in devices:
                    device_id = device["deviceId"]
                    display_json(f"api.get_device_settings({device_id})", api.get_device_settings(device_id))

            elif i == "Z":
                # Logout Garmin Connect portal
                display_json("api.logout()", api.logout())
                api = None

        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error("Error occurred: %s", err)
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
