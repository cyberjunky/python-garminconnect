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
tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
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
gearUUID = "MY_GEAR_UUID"

def display_json(api_call, output):
	"""Format API output for better readability."""

	dashed = "-" * 20
	header = f"{dashed} {api_call} {dashed}"
	footer = "-" * len(header)

	print(header)

	if isinstance(output, (int, str, dict, list)):
		print(json.dumps(output, indent=4))
	else:
		print(output)

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

			garmin = Garmin(email=email, password=password, is_cn=False, prompt_mfa=get_mfa)
			garmin.login()
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
		except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
			logger.error(err)
			return None

	return garmin


def get_mfa():
	"""Get MFA."""

	return input("MFA one-time code: ")


def format_timedelta(td):
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)


def gear(api):
	"""Calculate total time of use of a piece of gear by going through all activities where said gear has been used."""

	# Skip requests if login failed
	if api:
		try:
			display_json(
				f"api.get_gear_stats({gearUUID})",
				api.get_gear_stats(gearUUID),
			)
			activityList = api.get_gear_ativities(gearUUID)
			if len(activityList) == 0:
				print("No activities found for the given gear uuid.")
			else:
				print("Found " + str(len(activityList)) + " activities.")

			D=0
			for a in activityList:
				print('Activity: ' + a['startTimeLocal'] + (' | ' + a['activityName'] if a['activityName'] else ''))
				print('  Duration: ' + format_timedelta(datetime.timedelta(seconds=a['duration'])))
				D += a['duration']    
			print('')
			print('Total Duration: ' + format_timedelta(datetime.timedelta(seconds=D)))
			print('')
			print('Done!')
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

# Display header and login
print("\n*** Garmin Connect API Demo by cyberjunky ***\n")

# Init API
if not api:
	api = init_api(email, password)

if api:
	gear(api)
else:
	api = init_api(email, password)
