# Python: Garmin Connect

Python 3 API wrapper for Garmin Connect to get your statistics.

## About

This package allows you to request your activity and health data you gather on Garmin Connect.
See https://connect.garmin.com/


## Installation

```bash
pip install garminconnect
```

## Usage

```python
from datetime import date

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

today = date.today()


client = Garmin(YOUR_EMAIL, YOUR_PASSWORD)

"""Login to portal using specified credentials"""
    try:
        client.login()
    except (
        GarminConnectConnectionError,
        GarminConnectAuthenticationError,
        GarminConnectTooManyRequestsError,
    ) as err:
        print("Error occured during Garmin Connect Client setup: %s", err)
        return
    except Exception:  # pylint: disable=broad-except
        print("Unknown error occured during Garmin Connect Client setup")
        return

"""Get Full name"""
print(client.get_full_name()

"""Get Unit system"""
print(client.get_unit_system()

"""Fetch your activities data"""
print(client.get_stats(today.isoformat())

"""Fetch your logged heart rates"""
print(client.get_heart_rates(today.isoformat())
```
