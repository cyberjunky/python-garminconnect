# Python: Garmin Connect

![image](https://github.com/cyberjunky/python-garminconnect/assets/5447161/c7ed7155-0f8c-4fdc-8369-1281759dc5c9)

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
