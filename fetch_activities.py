#!/usr/bin/env python3
"""
pip3 install cloudscraper requests

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>
"""
import datetime
import json
import logging
import os

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

def login(email, password):
  try:
      api = Garmin(email, password)
      api.login()
  except (
      GarminConnectConnectionError,
      GarminConnectAuthenticationError,
      GarminConnectTooManyRequestsError,
      requests.exceptions.HTTPError,
  ) as err:
      logger.error("Error occurred during Garmin Connect communication: %s", err)
      return None
  return api

if __name__ == '__main__':
  today = datetime.date.today()
  email = os.getenv("EMAIL")
  password = os.getenv("PASSWORD")
  api = login(email,password)
  activities = api.get_activities_by_date(today.isoformat(), today.isoformat(), "fitness_equipment")

  for a in activities:
    if a["activityType"]["typeKey"] == "strength_training":
      a["exerciseSets"] = api.get_activity_exercise_sets(a["activityId"]).get("exerciseSets",[])

      output_file = f'./{str(a["activityId"])}.json'
      with open(output_file, "w") as fb:
        fb.write(json.dumps(a, indent=2))
