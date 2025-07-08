#!/usr/bin/env python3
"""
pip3 install garth requests readchar

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

"""
import datetime
from datetime import timezone
import json
import logging
import os
import sys
from getpass import getpass

import readchar
import requests
from garth.exc import GarthHTTPError

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
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
api = None

# Example selections and settings

# Let's say we want to scrape all activities using switch menu_option "p". We change the values of the below variables, IE startdate days, limit,...
today = datetime.date.today()
startdate = today - datetime.timedelta(days=7)  # Select past week
startdate_four_weeks = today - datetime.timedelta(days=28)
start = 0
limit = 100
start_badge = 1  # Badge related calls calls start counting at 1
activitytype = ""  # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
activityfile = "MY_ACTIVITY.fit"  # Supported file types are: .fit .gpx .tcx
weight = 89.6
weightunit = "kg"
# workout_example = """
# {
#     'workoutId': "random_id",
#     'ownerId': "random",
#     'workoutName': 'Any workout name',
#     'description': 'FTP 200, TSS 1, NP 114, IF 0.57',
#     'sportType': {'sportTypeId': 2, 'sportTypeKey': 'cycling'},
#     'workoutSegments': [
#         {
#             'segmentOrder': 1,
#             'sportType': {'sportTypeId': 2, 'sportTypeKey': 'cycling'},
#             'workoutSteps': [
#                 {'type': 'ExecutableStepDTO', 'stepOrder': 1,
#                     'stepType': {'stepTypeId': 3, 'stepTypeKey': 'interval'}, 'childStepId': None,
#                     'endCondition': {'conditionTypeId': 2, 'conditionTypeKey': 'time'}, 'endConditionValue': 60,
#                     'targetType': {'workoutTargetTypeId': 2, 'workoutTargetTypeKey': 'power.zone'},
#                     'targetValueOne': 95, 'targetValueTwo': 105},
#                 {'type': 'ExecutableStepDTO', 'stepOrder': 2,
#                     'stepType': {'stepTypeId': 3, 'stepTypeKey': 'interval'}, 'childStepId': None,
#                     'endCondition': {'conditionTypeId': 2, 'conditionTypeKey': 'time'}, 'endConditionValue': 120,
#                     'targetType': {'workoutTargetTypeId': 2, 'workoutTargetTypeKey': 'power.zone'},
#                     'targetValueOne': 114, 'targetValueTwo': 126}
#             ]
#         }
#     ]
# }
# """

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
    "-": f"Get daily step data for '{startdate.isoformat()}' to '{today.isoformat()}'",
    "/": f"Get body battery data for '{startdate.isoformat()}' to '{today.isoformat()}'",
    "!": f"Get floors data for '{startdate.isoformat()}'",
    "?": f"Get blood pressure data for '{startdate.isoformat()}' to '{today.isoformat()}'",
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
    "u": "Get active goals",
    "v": "Get future goals",
    "w": "Get past goals",
    "y": "Get all Garmin device alarms",
    "x": f"Get Heart Rate Variability data (HRV) for '{today.isoformat()}'",
    "z": f"Get progress summary from '{startdate.isoformat()}' to '{today.isoformat()}' for all metrics",
    "A": "Get gear, the defaults, activity types and statistics",
    "B": f"Get weight-ins from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "C": f"Get daily weigh-ins for '{today.isoformat()}'",
    "D": f"Delete all weigh-ins for '{today.isoformat()}'",
    "E": f"Add a weigh-in of {weight}{weightunit} on '{today.isoformat()}'",
    "F": f"Get virtual challenges/expeditions from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "G": f"Get hill score data from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "H": f"Get endurance score data from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "I": f"Get activities for date '{today.isoformat()}'",
    "J": "Get race predictions",
    "K": f"Get all day stress data for '{today.isoformat()}'",
    "L": f"Add body composition for '{today.isoformat()}'",
    "M": "Set blood pressure '120,80,80,notes='Testing with example.py'",
    "N": "Get user profile/settings",
    "O": f"Reload epoch data for {today.isoformat()}",
    "P": "Get workouts 0-100, get and download last one to .FIT file",
    # "Q": "Upload workout from json data",
    "R": "Get solar data from your devices",
    "S": "Get pregnancy summary data",
    "T": "Add hydration data",
    "U": f"Get Fitness Age data for {today.isoformat()}",
    "V": f"Get daily wellness events data for {startdate.isoformat()}",
    "W": "Get userprofile settings",
    "X": "Get lactate threshold data, both Latest and for the past four weeks",
    "Z": "Remove stored login tokens (logout)",
    "q": "Exit",
}


def display_json(api_call, output):
    """Format API output for better readability."""

    dashed = "-" * 20
    header = f"{dashed} {api_call} {dashed}"
    footer = "-" * len(header)

    # print(header)

    # if isinstance(output, (int, str, dict, list)):
    #     print(json.dumps(output, indent=4))
    # else:
    #     print(output)

    # print(footer)
    # Format the output
    if isinstance(output, (int, str, dict, list)):
        formatted_output = json.dumps(output, indent=4)
    else:
        formatted_output = str(output)

    # Combine the header, output, and footer
    full_output = f"{header}\n{formatted_output}\n{footer}"

    # Print to console
    print(full_output)

    # Save to a file
    output_filename = "response.json"
    with open(output_filename, "w") as file:
        file.write(full_output)

    print(f"Output saved to {output_filename}")

def display_text(output):
    """Format API output for better readability."""

    dashed = "-" * 60
    header = f"{dashed}"
    footer = "-" * len(header)

    print(header)
    print(json.dumps(output, indent=4))
    print(footer)


def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        # Using Oauth1 and OAuth2 token files from directory
        print(
            f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...\n"
        )

        # Using Oauth1 and Oauth2 tokens from base64 encoded string
        # print(
        #     f"Trying to login to Garmin Connect using token data from file '{tokenstore_base64}'...\n"
        # )
        # dir_path = os.path.expanduser(tokenstore_base64)
        # with open(dir_path, "r") as token_file:
        #     tokenstore = token_file.read()

        garmin = Garmin()
        garmin.login(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()
            if result1 == "needs_mfa":  # MFA is required
                mfa_code = get_mfa()
                garmin.resume_login(result2, mfa_code)

            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )

            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login (alternative way)
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            )

            # Re-login Garmin API with tokens
            garmin.login(tokenstore)
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error(err)
            return None

    return garmin


def get_mfa():
    """Get MFA."""

    return input("MFA one-time code: ")


def print_menu():
    """Print examples menu."""
    for key in menu_options.keys():
        print(f"{key} -- {menu_options[key]}")
    print("Make your selection: ", end="", flush=True)


def switch(api, i):
    """Run selected API call."""

    # Exit example program
    if i == "q":
        print("Be active, generate some data to fetch next time ;-) Bye!")
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
                display_json(
                    f"api.get_stats('{today.isoformat()}')",
                    api.get_stats(today.isoformat()),
                )
            elif i == "4":
                # Get activity data (to be compatible with garminconnect-ha)
                display_json(
                    f"api.get_user_summary('{today.isoformat()}')",
                    api.get_user_summary(today.isoformat()),
                )
            elif i == "5":
                # Get body composition data for 'YYYY-MM-DD' (to be compatible with garminconnect-ha)
                display_json(
                    f"api.get_body_composition('{today.isoformat()}')",
                    api.get_body_composition(today.isoformat()),
                )
            elif i == "6":
                # Get body composition data for multiple days 'YYYY-MM-DD' (to be compatible with garminconnect-ha)
                display_json(
                    f"api.get_body_composition('{startdate.isoformat()}', '{today.isoformat()}')",
                    api.get_body_composition(startdate.isoformat(), today.isoformat()),
                )
            elif i == "7":
                # Get stats and body composition data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_stats_and_body('{today.isoformat()}')",
                    api.get_stats_and_body(today.isoformat()),
                )

            # USER STATISTICS LOGGED
            elif i == "8":
                # Get steps data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_steps_data('{today.isoformat()}')",
                    api.get_steps_data(today.isoformat()),
                )
            elif i == "9":
                # Get heart rate data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_heart_rates('{today.isoformat()}')",
                    api.get_heart_rates(today.isoformat()),
                )
            elif i == "0":
                # Get training readiness data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_training_readiness('{today.isoformat()}')",
                    api.get_training_readiness(today.isoformat()),
                )
            elif i == "/":
                # Get daily body battery data for 'YYYY-MM-DD' to 'YYYY-MM-DD'
                display_json(
                    f"api.get_body_battery('{startdate.isoformat()}, {today.isoformat()}')",
                    api.get_body_battery(startdate.isoformat(), today.isoformat()),
                )
                # Get daily body battery event data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_body_battery_events('{startdate.isoformat()}, {today.isoformat()}')",
                    api.get_body_battery_events(startdate.isoformat()),
                )
            elif i == "?":
                # Get daily blood pressure data for 'YYYY-MM-DD' to 'YYYY-MM-DD'
                display_json(
                    f"api.get_blood_pressure('{startdate.isoformat()}, {today.isoformat()}')",
                    api.get_blood_pressure(startdate.isoformat(), today.isoformat()),
                )
            elif i == "-":
                # Get daily step data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_daily_steps('{startdate.isoformat()}, {today.isoformat()}')",
                    api.get_daily_steps(startdate.isoformat(), today.isoformat()),
                )
            elif i == "!":
                # Get daily floors data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_floors('{today.isoformat()}')",
                    api.get_floors(today.isoformat()),
                )
            elif i == ".":
                # Get training status data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_training_status('{today.isoformat()}')",
                    api.get_training_status(today.isoformat()),
                )
            elif i == "a":
                # Get resting heart rate data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_rhr_day('{today.isoformat()}')",
                    api.get_rhr_day(today.isoformat()),
                )
            elif i == "b":
                # Get hydration data 'YYYY-MM-DD'
                display_json(
                    f"api.get_hydration_data('{today.isoformat()}')",
                    api.get_hydration_data(today.isoformat()),
                )
            elif i == "c":
                # Get sleep data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_sleep_data('{today.isoformat()}')",
                    api.get_sleep_data(today.isoformat()),
                )
            elif i == "d":
                # Get stress data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_stress_data('{today.isoformat()}')",
                    api.get_stress_data(today.isoformat()),
                )
            elif i == "e":
                # Get respiration data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_respiration_data('{today.isoformat()}')",
                    api.get_respiration_data(today.isoformat()),
                )
            elif i == "f":
                # Get SpO2 data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_spo2_data('{today.isoformat()}')",
                    api.get_spo2_data(today.isoformat()),
                )
            elif i == "g":
                # Get max metric data (like vo2MaxValue and fitnessAge) for 'YYYY-MM-DD'
                display_json(
                    f"api.get_max_metrics('{today.isoformat()}')",
                    api.get_max_metrics(today.isoformat()),
                )
            elif i == "h":
                # Get personal record for user
                display_json("api.get_personal_record()", api.get_personal_record())
            elif i == "i":
                # Get earned badges for user
                display_json("api.get_earned_badges()", api.get_earned_badges())
            elif i == "j":
                # Get adhoc challenges data from start and limit
                display_json(
                    f"api.get_adhoc_challenges({start},{limit})",
                    api.get_adhoc_challenges(start, limit),
                )  # 1=start, 100=limit
            elif i == "k":
                # Get available badge challenges data from start and limit
                display_json(
                    f"api.get_available_badge_challenges({start_badge}, {limit})",
                    api.get_available_badge_challenges(start_badge, limit),
                )  # 1=start, 100=limit
            elif i == "l":
                # Get badge challenges data from start and limit
                display_json(
                    f"api.get_badge_challenges({start_badge}, {limit})",
                    api.get_badge_challenges(start_badge, limit),
                )  # 1=start, 100=limit
            elif i == "m":
                # Get non completed badge challenges data from start and limit
                display_json(
                    f"api.get_non_completed_badge_challenges({start_badge}, {limit})",
                    api.get_non_completed_badge_challenges(start_badge, limit),
                )  # 1=start, 100=limit

            # ACTIVITIES
            elif i == "n":
                # Get activities data from start and limit
                display_json(
                    f"api.get_activities({start}, {limit})",
                    api.get_activities(start, limit),
                )  # 0=start, 1=limit
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
                    activity_start_time = datetime.datetime.strptime(
                        activity["startTimeLocal"], "%Y-%m-%d %H:%M:%S"
                    ).strftime(
                        "%d-%m-%Y"
                    )  # Format as DD-MM-YYYY, for creating unique activity names for scraping
                    activity_id = activity["activityId"]
                    activity_name = activity["activityName"]
                    display_text(activity)

                    print(
                        f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.GPX)"
                    )
                    gpx_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.GPX
                    )
                    output_file = f"./{str(activity_name)}_{str(activity_start_time)}_{str(activity_id)}.gpx"
                    with open(output_file, "wb") as fb:
                        fb.write(gpx_data)
                    print(f"Activity data downloaded to file {output_file}")

                    print(
                        f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.TCX)"
                    )
                    tcx_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.TCX
                    )
                    output_file = f"./{str(activity_name)}_{str(activity_start_time)}_{str(activity_id)}.tcx"
                    with open(output_file, "wb") as fb:
                        fb.write(tcx_data)
                    print(f"Activity data downloaded to file {output_file}")

                    print(
                        f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.ORIGINAL)"
                    )
                    zip_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.ORIGINAL
                    )
                    output_file = f"./{str(activity_name)}_{str(activity_start_time)}_{str(activity_id)}.zip"
                    with open(output_file, "wb") as fb:
                        fb.write(zip_data)
                    print(f"Activity data downloaded to file {output_file}")

                    print(
                        f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.CSV)"
                    )
                    csv_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.CSV
                    )
                    output_file = f"./{str(activity_name)}_{str(activity_start_time)}_{str(activity_id)}.csv"
                    with open(output_file, "wb") as fb:
                        fb.write(csv_data)
                    print(f"Activity data downloaded to file {output_file}")

            elif i == "r":
                # Get activities data from start and limit
                activities = api.get_activities(start, limit)  # 0=start, 1=limit

                # Get activity splits
                first_activity_id = activities[0].get("activityId")

                display_json(
                    f"api.get_activity_splits({first_activity_id})",
                    api.get_activity_splits(first_activity_id),
                )

                # Get activity typed splits

                display_json(
                    f"api.get_activity_typed_splits({first_activity_id})",
                    api.get_activity_typed_splits(first_activity_id),
                )
                # Get activity split summaries for activity id
                display_json(
                    f"api.get_activity_split_summaries({first_activity_id})",
                    api.get_activity_split_summaries(first_activity_id),
                )

                # Get activity weather data for activity
                display_json(
                    f"api.get_activity_weather({first_activity_id})",
                    api.get_activity_weather(first_activity_id),
                )

                # Get activity hr timezones id
                display_json(
                    f"api.get_activity_hr_in_timezones({first_activity_id})",
                    api.get_activity_hr_in_timezones(first_activity_id),
                )

                # Get activity details for activity id
                display_json(
                    f"api.get_activity_details({first_activity_id})",
                    api.get_activity_details(first_activity_id),
                )

                # Get gear data for activity id
                display_json(
                    f"api.get_activity_gear({first_activity_id})",
                    api.get_activity_gear(first_activity_id),
                )

                # Activity data for activity id
                display_json(
                    f"api.get_activity({first_activity_id})",
                    api.get_activity(first_activity_id),
                )

                # Get exercise sets in case the activity is a strength_training
                if activities[0]["activityType"]["typeKey"] == "strength_training":
                    display_json(
                        f"api.get_activity_exercise_sets({first_activity_id})",
                        api.get_activity_exercise_sets(first_activity_id),
                    )

            elif i == "s":
                try:
                    # Upload activity from file
                    display_json(
                        f"api.upload_activity({activityfile})",
                        api.upload_activity(activityfile),
                    )
                except FileNotFoundError:
                    print(f"File to upload not found: {activityfile}")

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
                    display_json(
                        f"api.get_device_settings({device_id})",
                        api.get_device_settings(device_id),
                    )

                # Get primary training device information
                primary_training_device = api.get_primary_training_device()
                display_json(
                    "api.get_primary_training_device()", primary_training_device
                )

            elif i == "R":
                # Get solar data from Garmin devices
                devices = api.get_devices()
                display_json("api.get_devices()", devices)

                # Get device last used
                device_last_used = api.get_device_last_used()
                display_json("api.get_device_last_used()", device_last_used)

                # Get settings per device
                for device in devices:
                    device_id = device["deviceId"]
                    display_json(
                        f"api.get_device_solar_data({device_id}, {today.isoformat()})",
                        api.get_device_solar_data(device_id, today.isoformat()),
                    )
            # GOALS
            elif i == "u":
                # Get active goals
                goals = api.get_goals("active")
                display_json('api.get_goals("active")', goals)

            elif i == "v":
                # Get future goals
                goals = api.get_goals("future")
                display_json('api.get_goals("future")', goals)

            elif i == "w":
                # Get past goals
                goals = api.get_goals("past")
                display_json('api.get_goals("past")', goals)

            # ALARMS
            elif i == "y":
                # Get Garmin device alarms
                alarms = api.get_device_alarms()
                for alarm in alarms:
                    alarm_id = alarm["alarmId"]
                    display_json(f"api.get_device_alarms({alarm_id})", alarm)

            elif i == "x":
                # Get Heart Rate Variability (hrv) data
                display_json(
                    f"api.get_hrv_data({today.isoformat()})",
                    api.get_hrv_data(today.isoformat()),
                )

            elif i == "z":
                # Get progress summary
                for metric in [
                    "elevationGain",
                    "duration",
                    "distance",
                    "movingDuration",
                ]:
                    display_json(
                        f"api.get_progress_summary_between_dates({today.isoformat()})",
                        api.get_progress_summary_between_dates(
                            startdate.isoformat(), today.isoformat(), metric
                        ),
                    )
            # GEAR
            elif i == "A":
                last_used_device = api.get_device_last_used()
                display_json("api.get_device_last_used()", last_used_device)
                userProfileNumber = last_used_device["userProfileNumber"]
                gear = api.get_gear(userProfileNumber)
                display_json("api.get_gear()", gear)
                display_json(
                    "api.get_gear_defaults()", api.get_gear_defaults(userProfileNumber)
                )
                display_json("api.get()", api.get_activity_types())
                for gear in gear:
                    uuid = gear["uuid"]
                    name = gear["displayName"]
                    display_json(
                        f"api.get_gear_stats({uuid}) / {name}", api.get_gear_stats(uuid)
                    )

            # WEIGHT-INS
            elif i == "B":
                # Get weigh-ins data
                display_json(
                    f"api.get_weigh_ins({startdate.isoformat()}, {today.isoformat()})",
                    api.get_weigh_ins(startdate.isoformat(), today.isoformat()),
                )
            elif i == "C":
                # Get daily weigh-ins data
                display_json(
                    f"api.get_daily_weigh_ins({today.isoformat()})",
                    api.get_daily_weigh_ins(today.isoformat()),
                )
            elif i == "D":
                # Delete weigh-ins data for today
                display_json(
                    f"api.delete_weigh_ins({today.isoformat()}, delete_all=True)",
                    api.delete_weigh_ins(today.isoformat(), delete_all=True),
                )
            elif i == "E":
                # Add a weigh-in
                display_json(
                    f"api.add_weigh_in(weight={weight}, unitKey={weightunit})",
                    api.add_weigh_in(weight=weight, unitKey=weightunit),
                )

                # Add a weigh-in with timestamps
                yesterday = today - datetime.timedelta(days=1) # Get yesterday's date
                weigh_in_date = datetime.datetime.strptime(yesterday.isoformat(), "%Y-%m-%d")
                local_timestamp = weigh_in_date.strftime('%Y-%m-%dT%H:%M:%S')
                gmt_timestamp = weigh_in_date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

                display_json(
                    f"api.add_weigh_in_with_timestamps(weight={weight}, unitKey={weightunit}, dateTimestamp={local_timestamp}, gmtTimestamp={gmt_timestamp})",
                    api.add_weigh_in_with_timestamps(
                        weight=weight,
                        unitKey=weightunit,
                        dateTimestamp=local_timestamp,
                        gmtTimestamp=gmt_timestamp
                    )
                )

            # CHALLENGES/EXPEDITIONS
            elif i == "F":
                # Get virtual challenges/expeditions
                display_json(
                    f"api.get_inprogress_virtual_challenges({startdate.isoformat()}, {today.isoformat()})",
                    api.get_inprogress_virtual_challenges(
                        startdate.isoformat(), today.isoformat()
                    ),
                )
            elif i == "G":
                # Get hill score data
                display_json(
                    f"api.get_hill_score({startdate.isoformat()}, {today.isoformat()})",
                    api.get_hill_score(startdate.isoformat(), today.isoformat()),
                )
            elif i == "H":
                # Get endurance score data
                display_json(
                    f"api.get_endurance_score({startdate.isoformat()}, {today.isoformat()})",
                    api.get_endurance_score(startdate.isoformat(), today.isoformat()),
                )
            elif i == "I":
                # Get activities for date
                display_json(
                    f"api.get_activities_fordate({today.isoformat()})",
                    api.get_activities_fordate(today.isoformat()),
                )
            elif i == "J":
                # Get race predictions
                display_json("api.get_race_predictions()", api.get_race_predictions())
            elif i == "K":
                # Get all day stress data for date
                display_json(
                    f"api.get_all_day_stress({today.isoformat()})",
                    api.get_all_day_stress(today.isoformat()),
                )
            elif i == "L":
                # Add body composition
                weight = 70.0
                percent_fat = 15.4
                percent_hydration = 54.8
                visceral_fat_mass = 10.8
                bone_mass = 2.9
                muscle_mass = 55.2
                basal_met = 1454.1
                active_met = None
                physique_rating = None
                metabolic_age = 33.0
                visceral_fat_rating = None
                bmi = 22.2
                display_json(
                    f"api.add_body_composition({today.isoformat()}, {weight}, {percent_fat}, {percent_hydration}, {visceral_fat_mass}, {bone_mass}, {muscle_mass}, {basal_met}, {active_met}, {physique_rating}, {metabolic_age}, {visceral_fat_rating}, {bmi})",
                    api.add_body_composition(
                        today.isoformat(),
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
                    ),
                )
            elif i == "M":
                # Set blood pressure values
                display_json(
                    "api.set_blood_pressure(120, 80, 80, notes=`Testing with example.py`)",
                    api.set_blood_pressure(
                        120, 80, 80, notes="Testing with example.py"
                    ),
                )
            elif i == "N":
                # Get user profile
                display_json("api.get_user_profile()", api.get_user_profile())
            elif i == "O":
                # Reload epoch data for date
                display_json(
                    f"api.request_reload({today.isoformat()})",
                    api.request_reload(today.isoformat()),
                )

            # WORKOUTS
            elif i == "P":
                workouts = api.get_workouts()
                # Get workout 0-100
                display_json("api.get_workouts()", api.get_workouts())

                # Get last fetched workout
                workout_id = workouts[-1]["workoutId"]
                workout_name = workouts[-1]["workoutName"]
                display_json(
                    f"api.get_workout_by_id({workout_id})",
                    api.get_workout_by_id(workout_id),
                )

                # Download last fetched workout
                print(f"api.download_workout({workout_id})")
                workout_data = api.download_workout(workout_id)

                output_file = f"./{str(workout_name)}.fit"
                with open(output_file, "wb") as fb:
                    fb.write(workout_data)
                print(f"Workout data downloaded to file {output_file}")

            # elif i == "Q":
            #     display_json(
            #         f"api.upload_workout({workout_example})",
            #         api.upload_workout(workout_example))

            # DAILY EVENTS
            elif i == "V":
                # Get all day wellness events for 7 days ago
                display_json(
                    f"api.get_all_day_events({today.isoformat()})",
                    api.get_all_day_events(startdate.isoformat()),
                )
            # WOMEN'S HEALTH
            elif i == "S":
                # Get pregnancy summary data
                display_json("api.get_pregnancy_summary()", api.get_pregnancy_summary())

            # Additional related calls:
            # get_menstrual_data_for_date(self, fordate: str): takes a single date and returns the Garmin Menstrual Summary data for that date
            # get_menstrual_calendar_data(self, startdate: str, enddate: str) takes two dates and returns summaries of cycles that have days between the two days

            elif i == "T":
                # Add hydration data for today
                value_in_ml = 240
                raw_date = datetime.date.today()
                cdate = str(raw_date)
                raw_ts = datetime.datetime.now()
                timestamp = datetime.datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

                display_json(
                    f"api.add_hydration_data(value_in_ml={value_in_ml},cdate='{cdate}',timestamp='{timestamp}')",
                    api.add_hydration_data(
                        value_in_ml=value_in_ml, cdate=cdate, timestamp=timestamp
                    ),
                )

            elif i == "U":
                # Get fitness age data
                display_json(
                    f"api.get_fitnessage_data({today.isoformat()})",
                    api.get_fitnessage_data(today.isoformat()),
                )

            elif i == "W":
                # Get userprofile settings
                display_json(
                    "api.get_userprofile_settings()", api.get_userprofile_settings()
                )

            elif i == "X":
                # Get latest lactate threshold
                display_json(
                    "api.get_lactate_threshold(latest=True)", api.get_lactate_threshold(latest=True)
                )
                # Get latest lactate threshold
                display_json(f"api.get_lactate_threshold(latest=False, start_date='{startdate_four_weeks.isoformat()}', end_date='{today.isoformat()}', aggregation='daily')", api.get_lactate_threshold(latest=False, start_date=startdate_four_weeks.isoformat(),
                                              end_date=today.isoformat(), aggregation="daily"),                )
            elif i == "Z":
                # Remove stored login tokens for Garmin Connect portal
                tokendir = os.path.expanduser(tokenstore)
                print(f"Removing stored login tokens from: {tokendir}")
                try:
                    for root, dirs, files in os.walk(tokendir, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    print(f"Directory {tokendir} removed")
                except FileNotFoundError:
                    print(f"Directory not found: {tokendir}")
                api = None

        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
            requests.exceptions.HTTPError,
            GarthHTTPError,
        ) as err:
            logger.error(err)
        except KeyError:
            # Invalid menu option chosen
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

    if api:
        # Display menu
        print_menu()
        option = readchar.readkey()
        switch(api, option)
    else:
        api = init_api(email, password)
