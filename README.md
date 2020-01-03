# Garmin Connect
Python API wrapper for Garmin Connect

See https://connect.garmin.com/

## Usage
Create a new connection by supplying your user credentials
```
import garmin-connect

data = garmin-connect.Garmin(YOUR_EMAIL, YOUR_PASSWORD)
```

Fetch your Garmin Connect activities data
```
print(data.fetch_stats())
```
