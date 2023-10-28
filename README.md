# Python: Garmin Connect

```
$ ./example.py 

*** Garmin Connect API Demo by cyberjunky ***

Trying to login to Garmin Connect using token data from '~/.garminconnect'...

1 -- Get full name
2 -- Get unit system
3 -- Get activity data for '2023-10-28'
4 -- Get activity data for '2023-10-28' (compatible with garminconnect-ha)
5 -- Get body composition data for '2023-10-28' (compatible with garminconnect-ha)
6 -- Get body composition data for from '2023-10-21' to '2023-10-28' (to be compatible with garminconnect-ha)
7 -- Get stats and body composition data for '2023-10-28'
8 -- Get steps data for '2023-10-28'
9 -- Get heart rate data for '2023-10-28'
0 -- Get training readiness data for '2023-10-28'
- -- Get daily step data for '2023-10-21' to '2023-10-28'
/ -- Get body battery data for '2023-10-21' to '2023-10-28'
! -- Get floors data for '2023-10-21'
? -- Get blood pressure data for '2023-10-21' to '2023-10-28'
. -- Get training status data for '2023-10-28'
a -- Get resting heart rate data for 2023-10-28'
b -- Get hydration data for '2023-10-28'
c -- Get sleep data for '2023-10-28'
d -- Get stress data for '2023-10-28'
e -- Get respiration data for '2023-10-28'
f -- Get SpO2 data for '2023-10-28'
g -- Get max metric data (like vo2MaxValue and fitnessAge) for '2023-10-28'
h -- Get personal record for user
i -- Get earned badges for user
j -- Get adhoc challenges data from start '0' and limit '100'
k -- Get available badge challenges data from '1' and limit '100'
l -- Get badge challenges data from '1' and limit '100'
m -- Get non completed badge challenges data from '1' and limit '100'
n -- Get activities data from start '0' and limit '100'
o -- Get last activity
p -- Download activities data by date from '2023-10-21' to '2023-10-28'
r -- Get all kinds of activities data from '0'
s -- Upload activity data from file 'MY_ACTIVITY.fit'
t -- Get all kinds of Garmin device info
u -- Get active goals
v -- Get future goals
w -- Get past goals
y -- Get all Garmin device alarms
x -- Get Heart Rate Variability data (HRV) for '2023-10-28'
z -- Get progress summary from '2023-10-21' to '2023-10-28' for all metrics
A -- Get gear, the defaults, activity types and statistics
B -- Get weight-ins from '2023-10-21' to '2023-10-28'
C -- Get daily weigh-ins for '2023-10-28'
D -- Delete all weigh-ins for '2023-10-28'
E -- Add a weigh-in of 89.6kg on '2023-10-28'
F -- Get virtual challenges/expeditions from '2023-10-21' to '2023-10-28'
G -- Get hill score data from '2023-10-21' to '2023-10-28'
H -- Get endurance score data from '2023-10-21' to '2023-10-28'
I -- Get activities for date '2023-10-28'
J -- Get race predictions
K -- Get all day stress data for '2023-10-28'
L -- Add body composition for '2023-10-28'
M -- Set blood pressure '120,80,80,notes='Testing with example.py'
N -- Get user profile/settings
Z -- Remove stored login tokens (logout)
q -- Exit
```

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)

Python 3 API wrapper for Garmin Connect to get your statistics.

## NOTE: For developers using this package
From `version 0.2.1 onwards`, this package uses `garth` to authenticate and perform API calls.  
This requires minor changes to your login code, look at the code in `example.py` or the `reference.ipynb` file how to do that.  
It fixes a lot of stability issues, so it's well worth the effort!  

## About

This package allows you to request garmin device, activity and health data from your Garmin Connect account.
See <https://connect.garmin.com/>

## Installation

```bash
pip3 install garminconnect
```

## Authentication

The library uses the same authentication method as the app using [Garth](https://github.com/matin/garth).
The login credentials generated with Garth are valid for a year to avoid needing to login each time.  
NOTE: We obtain the OAuth tokens using the consumer key and secret as the Connect app does.
`garth.sso.OAUTH_CONSUMER` can be set manually prior to calling api.login() if someone wants to use a custom consumer key and secret.

## Testing

The test files use the credential tokens created by `example.py` script, so use that first.

```bash
export GARMINTOKENS=~/.garminconnect
sudo apt install python3-pytest (needed some distros)

make install-test
make test
```

## Development

To create a development enviroment to commit code.

```
pip3 install pdm
pip3 install ruff
pdm init

sudo apt install pre-commit
pip3 install pre-commit
```
Run checks before PR/Commit:
```
make format
make lint
make codespell
```

## Example
The tests provide examples of how to use the library.  
There is a Jupyter notebook called `reference.ipynb` provided [here](https://github.com/cyberjunky/python-garminconnect/blob/master/reference.ipynb).  
And you can check out the `example.py` code you can find [here](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/example.py), you can run it like so:  
```
pip3 install -r requirements-dev.txt
./example.py
```

## Credits

:heart: Special thanks to all people contributed, either by asking questions, reporting bugs, coming up with great ideas, or even by creating whole Pull Requests to add new features!
This project deserves more attention, but I'm struggling to free up time sometimes, so thank you for your patience too!

## Donations

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)
