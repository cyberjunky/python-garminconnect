# Python: Garmin Connect

Python 3 API wrapper for Garmin Connect to get your statistics.

## About

This package allows you to request your device, activity and health data from your Garmin Connect account.
See https://connect.garmin.com/

## Installation

```bash
pip3 install garminconnect
```

## Usage

```python
#!/usr/bin/env python3
import logging
import datetime

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

# Configure debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Example dates
today = datetime.date.today()
lastweek = today - datetime.timedelta(days=7)

try:
    # API

    ## Initialize Garmin api with your credentials
    api = Garmin("YOUR EMAIL", "YOUR PASSWORD")

    ## Login to Garmin Connect portal
    api.login()

    # USER INFO

    # Get full name from profile
    logger.info(api.get_full_name())

    ## Get unit system from profile
    logger.info(api.get_unit_system())


    # USER STATISTIC SUMMARIES

    ## Get activity data for today 'YYYY-MM-DD'
    logger.info(api.get_stats(today.isoformat()))

    ## Get activity data (to be compatible with garminconnect-ha)
    logger.info(api.get_user_summary(today.isoformat()))

    ## Get body composition data for today 'YYYY-MM-DD' (to be compatible with garminconnect-ha)
    logger.info(api.get_body_composition(today.isoformat()))

    ## Get body composition data for multiple days 'YYYY-MM-DD' (to be compatible with garminconnect-ha)
    logger.info(api.get_body_composition(lastweek.isoformat(), today.isoformat()))


    ## Get stats and body composition data for today 'YYYY-MM-DD'
    logger.info(api.get_stats_and_body(today.isoformat()))


    # USER STATISTICS LOGGED

    ## Get steps data for today 'YYYY-MM-DD'
    logger.info(api.get_steps_data(today.isoformat()))
    
    ## Get heart rate data for today 'YYYY-MM-DD'
    logger.info(api.get_heart_rates(today.isoformat()))

    ## Get resting heart rate data for today 'YYYY-MM-DD'
    logger.info(api.get_rhr_day(today.isoformat()))

    ## Get hydration data 'YYYY-MM-DD'
    logger.info(api.get_hydration_data(today.isoformat()))

    ## Get sleep data for today 'YYYY-MM-DD'
    logger.info(api.get_sleep_data(today.isoformat()))
    
    ## Get respiration data for today 'YYYY-MM-DD'
    logger.info(api.get_respiration_data(today.isoformat()))

    ## Get SpO2 data for today 'YYYY-MM-DD'
    logger.info(api.get_spo2_data(today.isoformat()))

    ## Get max metric data (like vo2MaxValue and fitnessAge) for today 'YYYY-MM-DD'
    logger.info(api.get_max_metrics(today.isoformat()))

    ## Get personal record
    logger.info(api.get_personal_record())


    # ACTIVITIES

    # Get activities data from start and limit
    activities = api.get_activities(0,1) # 0=start, 1=limit
    logger.info(activities)

    ## Download an Activity
    for activity in activities:
        activity_id = activity["activityId"]
        logger.info("api.download_activities(%s)", activity_id)

        gpx_data = api.download_activity(activity_id, dl_fmt=api.ActivityDownloadFormat.GPX)
        output_file = f"./{str(activity_id)}.gpx"
        with open(output_file, "wb") as fb:
            fb.write(gpx_data)

        tcx_data = api.download_activity(activity_id, dl_fmt=api.ActivityDownloadFormat.TCX)
        output_file = f"./{str(activity_id)}.tcx"
        with open(output_file, "wb") as fb:
            fb.write(tcx_data)

        zip_data = api.download_activity(activity_id, dl_fmt=api.ActivityDownloadFormat.ORIGINAL)
        output_file = f"./{str(activity_id)}.zip"
        with open(output_file, "wb") as fb:
            fb.write(zip_data)

        csv_data = api.download_activity(activity_id, dl_fmt=api.ActivityDownloadFormat.CSV)
        output_file = f"./{str(activity_id)}.csv"
        with open(output_file, "wb") as fb:
            fb.write(csv_data)

    ## Get activity splits
    first_activity_id = activities[0].get("activityId")
    owner_display_name =  activities[0].get("ownerDisplayName")

    logger.info(api.get_activity_splits(first_activity_id))

    ## Get activity split summaries
    logger.info(api.get_activity_split_summaries(first_activity_id))

    ## Get activity weather data for activity
    logger.info(api.get_activity_weather(first_activity_id))

    ## Get activity hr timezones
    logger.info(api.get_activity_hr_in_timezones(first_activity_id))

    ## Get activity details for activity
    logger.info(api.get_activity_details(first_activity_id))

    # ## Get gear data for activity
    logger.info(api.get_activity_gear(first_activity_id))


    # DEVICES

    ## Get Garmin devices
    devices = api.get_devices()
    logger.info(devices)

    ## Get device last used
    device_last_used = api.get_device_last_used()
    logger.info(device_last_used)

    for device in devices:
        device_id = device["deviceId"]
        logger.info(api.get_device_settings(device_id))

    ## Get device settings
    for device in devices:
        device_id = device["deviceId"]
        logger.info(api.get_device_settings(device_id))


    ## Logout of Garmin Connect portal
    # api.logout()

except (
        GarminConnectConnectionError,
        GarminConnectAuthenticationError,
        GarminConnectTooManyRequestsError,
    ) as err:
    logger.error("Error occurred during Garmin Connect communication: %s", err)
```
