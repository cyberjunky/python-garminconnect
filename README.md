# Python: Garmin Connect

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE.md)

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
import garminconnect

"""Login to portal using specified credentials"""
client = garminconnect.Garmin(YOUR_EMAIL, YOUR_PASSWORD)

"""Fetch your activities data"""
print(client.fetch_stats('2020-01-04'))

"""Fetch your logged heart rates"""
print(client.fetch_heart_rates('2020-01-04'))
```
