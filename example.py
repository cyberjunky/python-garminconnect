#!/usr/bin/env python3
"""
pip3 install garth requests readchar

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

"""
import datetime
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
api = None

# Example selections and settings
today = datetime.date.today()
startdate = today - datetime.timedelta(days=7)  # Select past week
start = 0
limit = 100
start_badge = 1  # Badge related calls calls start counting at 1
activitytype = ""  # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
activityfile = "MY_ACTIVITY.fit"  # Supported file types are: .fit .gpx .tcx
weight = 89.6
weightunit = 'kg'

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
    "E": f"Add a weigh-in of {weight}{weightunit} on '{today.isoformat()}')",
    "F": f"Get virual challenges/expeditions from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "G": f"Get hill score data from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "H": f"Get endurance score data from '{startdate.isoformat()}' to '{today.isoformat()}'",
    "Z": "Remove stored login tokens (to reauth)",
    "q": "Exit",
}


def display_json(api_call, output):
    """Format API output for better readability."""

    dashed = "-" * 20
    header = f"{dashed} {api_call} {dashed}"
    footer = "-" * len(header)

    print(header)
    print(json.dumps(output, indent=4))
    print(footer)


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
        print(
            f"Trying to login to Garmin Connect using token data from '{tokenstore}'...\n"
        )
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

            garmin = Garmin(email, password)
            garmin.login()
            # Save tokens for next login
            garmin.garth.dump(tokenstore)

        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
            logger.error(err)
            return None

    return garmin


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
                    activity_id = activity["activityId"]
                    activity_name = activity["activityName"]
                    display_text(activity)

                    print(
                        f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.GPX)"
                    )
                    gpx_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.GPX
                    )
                    output_file = f"./{str(activity_name)}.gpx"
                    with open(output_file, "wb") as fb:
                        fb.write(gpx_data)
                    print(f"Activity data downloaded to file {output_file}")

                    print(
                        f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.TCX)"
                    )
                    tcx_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.TCX
                    )
                    output_file = f"./{str(activity_name)}.tcx"
                    with open(output_file, "wb") as fb:
                        fb.write(tcx_data)
                    print(f"Activity data downloaded to file {output_file}")

                    print(
                        f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.ORIGINAL)"
                    )
                    zip_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.ORIGINAL
                    )
                    output_file = f"./{str(activity_name)}.zip"
                    with open(output_file, "wb") as fb:
                        fb.write(zip_data)
                    print(f"Activity data downloaded to file {output_file}")

                    print(
                        f"api.download_activity({activity_id}, dl_fmt=api.ActivityDownloadFormat.CSV)"
                    )
                    csv_data = api.download_activity(
                        activity_id, dl_fmt=api.ActivityDownloadFormat.CSV
                    )
                    output_file = f"./{str(activity_name)}.csv"
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

                # Activity self evaluation data for activity id
                display_json(
                    f"api.get_activity_evaluation({first_activity_id})",
                    api.get_activity_evaluation(first_activity_id),
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

            # Gear
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
                    api.get_weigh_ins(startdate.isoformat(), today.isoformat())
                )
            elif i == "C":
                # Get daily weigh-ins data
                display_json(
                    f"api.get_daily_weigh_ins({today.isoformat()})",
                    api.get_daily_weigh_ins(today.isoformat())
                )
            elif i == "D":
                # Delete weigh-ins data for today
                display_json(
                    f"api.delete_weigh_ins({today.isoformat()}, delete_all=True)",
                    api.delete_weigh_ins(today.isoformat(), delete_all=True)
                )
            elif i == "E":
                # Add a weigh-in
                weight = 89.6
                unit = 'kg'
                display_json(
                    f"api.add_weigh_in(weight={weight}, unitKey={unit})",
                    api.add_weigh_in(weight=weight, unitKey=unit)
                )
            # Challenges/expeditions
            elif i == "F":
                # Get virtual challenges/expeditions
                display_json(
                    f"api.get_inprogress_virtual_challenges({startdate.isoformat()}, {today.isoformat()})",
                    api.get_inprogress_virtual_challenges(startdate.isoformat(), today.isoformat())
                )
            elif i == "G":
                # Get hill score data
                display_json(
                    f"api.get_hill_score({startdate.isoformat()}, {today.isoformat()})",
                    api.get_hill_score(startdate.isoformat(), today.isoformat())
                )
            elif i == "H":
                # Get endurance score data
                display_json(
                    f"api.get_endurance_score({startdate.isoformat()}, {today.isoformat()})",
                    api.get_endurance_score(startdate.isoformat(), today.isoformat())
                )
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
            GarthHTTPError
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