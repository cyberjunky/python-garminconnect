[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

# Python: Garmin Connect

The Garmin Connect API library comes with two examples:

- **`example.py`** - Simple getting-started example showing authentication, token storage, and basic API calls
- **`demo.py`** - Comprehensive demo providing access to **270 API methods** organized into **15 categories** for easy navigation

```bash
$ ./demo.py
📁 Exported data will be saved to the directory: 'your_data'
📄 All API responses are written to: 'response.json'
Attempting to login using stored tokens from: ~/.garminconnect
Successfully logged in using stored tokens!

📊 Your Stats Today: 4,045 steps | 1445.0 kcal
🐌 Time to get those legs moving!

==================================================
🚴 Full-blown Garmin Connect API Demo - Main Menu
==================================================
Select a category:

  [1] 👤 User & Profile
  [2] 📊 Daily Health & Activity
  [3] 🔬 Advanced Health Metrics
  [4] 📈 Historical Data & Trends
  [5] 🏃 Activities & Workouts
  [6] ⚖️ Body Composition & Weight
  [7] 🏆 Goals & Achievements
  [8] ⌚ Device & Technical
  [9] 🎽 Gear & Equipment
  [0] 💧 Hydration & Wellness
  [a] 🔧 System & Export
  [b] 📅 Training Plans & Calendar
  [c] ⛳ Golf
  [d] ✏️ Activity Editing
  [e] 🏃 Activity Details & Courses

  [q] Exit program

Make your selection:
```

## API Coverage Statistics

- **Total API Methods**: 348 methods; every method with a one-line description is listed in the [Method Reference](#-method-reference)
- **Categories**: 15 organized sections
- **Web-app endpoint map**: the endpoints the Garmin Connect web app uses documented with the exact request it sends and whether it was verified live, in [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md); the dashboard's GraphQL operations are in [docs/graphql_operations.md](docs/graphql_operations.md)
- **User & Profile**: 8 methods (basic user info, settings)
- **Daily Health & Activity**: 21 methods (today's health data plus daily calories, resting HR and sleep ranges)
- **Advanced Health Metrics**: 35 methods (fitness metrics, HRV, VO2, FTP range, training readiness, training zones, running tolerance, training load balance, daily training status, activity training load)
- **Historical Data & Trends**: 29 methods (date range queries, weekly aggregates)
- **Activities & Workouts**: 37 methods (comprehensive activity, workout management, typed workout uploads including strength and swim CSS targets, in-place edit, scheduling, push to device, import, activity type/subtype filtering, earliest-upcoming-workout lookup, activity photos)
- **Body Composition & Weight**: 11 methods (weight tracking, body composition)
- **Goals & Achievements**: 24 methods (challenges, badges, goals)
- **Device & Technical**: 13 methods (device info, settings)
- **Gear & Equipment**: 13 methods (gear management, tracking, creation)
- **Hydration & Wellness**: 30 methods (hydration, nutrition, blood pressure, menstrual reads and writes, Jet Lag Adviser trips)
- **System & Export**: 5 methods (reporting, logout, GraphQL, health snapshot download)
- **Training Plans & Calendar**: 23 methods (calendar weeks/years/events, upcoming and primary race events, active plans and plan tasks, plans, plan by ID, typed strength workout uploads including timed sets, exercise catalog search, in-place workout editing, push to device, workout scheduling management)
- **Golf**: 5 methods (scorecard summary, scorecard detail, shot data, club stats, user stats)
- **Activity Editing**: 3 methods (set activity description, set strength-activity exercise sets)
- **Activity Details & Courses**: 13 methods (laps, rounds, step/jump/swim details, map and polyline, activity search, courses)

### Interactive Features

- **Enhanced User Experience**: Categorized navigation with emoji indicators
- **Smart Data Management**: Interactive weigh-in deletion with search capabilities
- **Comprehensive Coverage**: All major Garmin Connect features are accessible
- **Error Handling**: Robust error handling with user-friendly prompts
- **Data Export**: JSON export functionality for all data types

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

A comprehensive Python3 API wrapper for Garmin Connect, providing access to health, fitness, and device data.

## 📖 About

This library enables developers to programmatically access Garmin Connect data including:

- **Health Metrics**: Heart rate, sleep, stress, body composition, SpO2, HRV
- **Activity Data**: Workouts, typed workout uploads (running, cycling, swimming, strength), workout scheduling, exercises, training status, performance metrics, import-style uploads (no Strava re-export)
- **Nutrition**: Daily food logs, meals, and nutrition settings
- **Golf**: Scorecard summaries, scorecard details, shot-by-shot data
- **Device Information**: Connected devices, settings, alarms, solar data
- **Goals & Achievements**: Personal records, badges, challenges, race predictions
- **Historical Data**: Trends, progress tracking, date range queries

Compatible with all Garmin Connect accounts. See <https://connect.garmin.com/>

## 📦 Installation

Requires Python 3.12 or later.

Install from PyPI:

```bash
pip install --upgrade garminconnect curl_cffi
```

### Upgrading from 0.2.x (garth)

Since 0.3.0 this library no longer uses `garth`, which is deprecated.
Sessions saved by older versions (`oauth1_token.json`/`oauth2_token.json`,
created with `garth.save()`) cannot be converted, and assigning a resumed
client to `Garmin().garth` no longer does anything. Log in once with your
username and password; new tokens are saved to `garmin_tokens.json` in your
tokenstore and are used for later logins:

```python
garmin = Garmin(email, password)
garmin.login("~/.garminconnect")  # later runs: Garmin().login("~/.garminconnect")
```

## Run demo software (recommended)

Clone the repo, then:

```bash
python3 -m venv .venv --copies
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[example]"

python3 ./example.py   # simple getting-started example
python3 ./demo.py      # comprehensive demo (270 API methods)
```

## 📚 Method Reference

<!-- METHODS:START -->
348 public methods on `Garmin`, generated from the code by `scripts/gen_method_reference.py`. Click a section to expand it.

<details><summary><b>Login, profile & account</b> (21)</summary>

| Method | Description |
| --- | --- |
| `connectapi(path, **kwargs)` | Send a GET to a Connect API path and return the decoded JSON. |
| `connectwebproxy(path, **kwargs)` | Send a GET to a Connect API path (legacy alias of `connectapi`). |
| `download(path, **kwargs)` | Download raw bytes from a Connect API path. |
| `get_full_name()` | Return full name of the authenticated user. |
| `get_personal_information(include_biometric=True, include_vo2max=True)` | Return personal information: `userInfo` (birth date, gender, locale, timeZone, country), `biometricProfile` and VO2 max. |
| `get_privacy_settings()` | Return the account's activity, profile and wellness privacy settings. |
| `get_unit_system()` | Return the user's unit system (e.g. metric). |
| `get_usage_indicators()` | Return which features the account's devices and data support. |
| `get_user_profile()` | Return the user settings (user data, units, formats, sleep times). |
| `get_user_profile_base()` | Return the base profile record (names, birth date, create date, ...). |
| `get_user_timezone()` | Return the IANA timezone name from the user's Garmin profile. |
| `get_userprofile_settings()` | Return the user profile settings (display name, locale, preferences). |
| `login(tokenstore=None)` | Log in with saved tokens or credentials and load the user profile. |
| `logout(tokenstore=None)` | Clear in-memory auth state and any cached tokens on disk. |
| `now()` | Return the current time as an aware datetime in the user's timezone. |
| `query_garmin_graphql(query)` | Run a query against Garmin's GraphQL gateway. |
| `request_reload(cdate, device_id=None)` | Request reload of data for a specific date. |
| `resume_login(client_state, mfa_code)` | Finish a login that is waiting for an MFA code. |
| `set_primary_training_device(device_id)` | Choose which device Garmin treats as the primary training device. |
| `today()` | Return today's calendar date in the user's Garmin timezone. |
| `update_user_settings(settings)` | Write user settings (units, formats, sleep times, training days, ...). |

</details>

<details><summary><b>Daily health & wellness</b> (75)</summary>

| Method | Description |
| --- | --- |
| `add_hydration_data(value_in_ml, timestamp=None, cdate=None)` | Log a hydration intake in ml (negative values subtract). |
| `add_jetlag_trip(start_date, end_date, flights)` | Create a Jet Lag Adviser trip. |
| `delete_jetlag_trip(trip_id)` | Delete a Jet Lag Adviser trip. |
| `download_health_snapshot(requested_date)` | Download the Health Snapshot ZIP file for a calendar date. |
| `download_health_snapshot_session(cdate, snapshot_uuid)` | Download one Health Snapshot session as a FIT file. |
| `get_all_day_events(cdate)` | Return available daily events data 'cdate' format 'YYYY-MM-DD'. |
| `get_all_day_stress(cdate)` | Return available all day stress data 'cdate' format 'YYYY-MM-DD'. |
| `get_body_battery(startdate, enddate=None)` | Return body battery values by day for 'startdate' format 'YYYY-MM-DD' through enddate 'YYYY-MM-DD'. |
| `get_body_battery_events(cdate)` | Return body battery events for date 'cdate' format 'YYYY-MM-DD'. |
| `get_calorie_summary(start, end, current_date=None)` | Return daily nutrition totals per meal with goals for a date range. |
| `get_calories_daily(start, end)` | Return daily active + resting (BMR) calories for a date range. |
| `get_daily_body_battery_stats(start, end)` | Return the daily Body Battery low/high values. |
| `get_daily_floors_stats(start, end)` | Return floors ascended/descended and the floors goal per day. |
| `get_daily_heart_rate_stats(start, end)` | Return resting / min / max heart rate per day. |
| `get_daily_hydration_stats(start, end)` | Return hydration intake per day. |
| `get_daily_intensity_minutes_stats(start, end)` | Return moderate/vigorous intensity minutes per day with the weekly goal. |
| `get_daily_movement(cdate=None)` | Return the daily movement chart (movement per 15-minute block). |
| `get_daily_respiration_stats(start, end)` | Return average waking and sleeping respiration per day. |
| `get_daily_sleep(cdate=None, non_sleep_buffer_minutes=60)` | Return sleep data for a day from the newer sleep-service endpoint. |
| `get_daily_stats(start, end, stats_type='STEPS', current_date=None, aggregated=False)` | Return a daily series of steps, pushes or calories with aggregations. |
| `get_daily_steps(start, end)` | Fetch available steps data 'start' and 'end' format 'YYYY-MM-DD'. |
| `get_daily_stress_stats(start, end)` | Return overall stress level and stress durations per day. |
| `get_daily_summaries(start, end)` | Return full daily summaries for a date range in one call. |
| `get_ecg(ecg_id)` | Return one ECG recording with its waveform. |
| `get_ecg_daily(start, end)` | Return ECG recordings per day for a date range. |
| `get_ecg_list(start='2021-01-01', end=None, page_size=20, …)` | Return a page of ECG recordings. |
| `get_floors(cdate)` | Fetch available floors data 'cDate' format 'YYYY-MM-DD'. |
| `get_health_snapshot(cdate, snapshot_uuid)` | Return one Health Snapshot session summary. |
| `get_health_snapshot_epochs(snapshot_uuid)` | Return the per-epoch samples (HR, HRV, SpO2, ...) of a Health Snapshot. |
| `get_health_snapshots(cdate=None)` | Return Health Snapshot sessions recorded on a day. |
| `get_health_snapshots_range(start, end)` | Return Health Snapshot sessions recorded in a date range. |
| `get_heart_rates(cdate)` | Fetch available heart rates data 'cDate' format 'YYYY-MM-DD'. |
| `get_hourly_intensity_minutes(end=None, days=7)` | Return intensity minutes per hour for up to 7 days ending at `end`. |
| `get_hrv_data(cdate)` | Return HRV (Heart Rate Variability) data for 'cdate' format 'YYYY-MM-DD'. |
| `get_hrv_data_range(start, end)` | Return HRV (Heart Rate Variability) data for a date range. |
| `get_hydration_all_data(cdate=None)` | Return hydration intake, goal, sweat loss and container settings for a day. |
| `get_hydration_data(cdate)` | Return available hydration data 'cdate' format 'YYYY-MM-DD'. |
| `get_intensity_minutes_data(cdate)` | Return available Intensity Minutes data 'cdate' format 'YYYY-MM-DD'. |
| `get_jetlag_status(cdate=None)` | Return the Jet Lag Adviser guidance for a day (empty dict without a trip). |
| `get_jetlag_trips()` | Return all Jet Lag Adviser trips, each with its flights. |
| `get_lifestyle_logging_data(cdate)` | Return lifestyle logging data for 'cdate' format 'YYYY-MM-DD'. |
| `get_lifetime_totals()` | Return lifetime totals (distance, steps, calories, active days, ...). |
| `get_monthly_steps(end=None, months=12)` | Return monthly step totals for `months` months ending at `end`. |
| `get_monthly_wellness_stats(start, end, metric_ids=None)` | Return monthly wellness metrics (default: resting heart rate, id 60). |
| `get_naps(cdate=None, include_overlaps=True)` | Return naps recorded on a day. |
| `get_nutrition_daily_food_log(cdate, include_goals=True, include_nutrition=True, meal_id=None)` | Return food log summary for 'cdate' format 'YYYY-MM-DD'. |
| `get_nutrition_daily_meals(cdate)` | Return meals summary for 'cdate' format 'YYYY-MM-DD'. |
| `get_nutrition_daily_settings(cdate)` | Return nutrition settings for 'cdate' format 'YYYY-MM-DD'. |
| `get_nutrition_status()` | Return whether nutrition tracking (or MyFitnessPal) is in use. |
| `get_respiration_data(cdate)` | Return available respiration data 'cdate' format 'YYYY-MM-DD'. |
| `get_rhr_daily(start, end)` | Return daily resting heart rate for a date range ('start'/'end' format 'YYYY-MM-DD'). |
| `get_rhr_day(cdate)` | Return resting heart rate data for 'cdate' format 'YYYY-MM-DD'. |
| `get_sleep_daily(start, end)` | Fetch daily sleep summaries for 'start' and 'end' format 'YYYY-MM-DD'. |
| `get_sleep_data(cdate)` | Return sleep data for 'cdate' format 'YYYY-MM-DD'. |
| `get_sleep_stats_overall(start, end)` | Return overall sleep statistics (averages) for a date range. |
| `get_sleep_stats_weekly(end=None, weeks=52)` | Return weekly sleep statistics (`overallStats` + per-week values). |
| `get_spo2_data(cdate)` | Return available SpO2 data 'cdate' format 'YYYY-MM-DD'. |
| `get_stats(cdate)` | Return the daily summary for 'cdate' format 'YYYY-MM-DD' (same as `get_user_summary`). |
| `get_stats_averages(start, end)` | Return average steps and resting heart rate over a date range. |
| `get_steps_data(cdate)` | Fetch available steps data 'cDate' format 'YYYY-MM-DD'. |
| `get_stress_data(cdate)` | Return stress data for 'cdate' format 'YYYY-MM-DD'. |
| `get_sync_timestamp()` | Return the timestamp (UTC, no offset) of the last device sync. |
| `get_user_statistics()` | Return the profile statistics block (totals per activity type). |
| `get_user_summary(cdate)` | Return user activity summary for 'cdate' format 'YYYY-MM-DD'. |
| `get_week_average_resting_hr(cdate=None)` | Return the 7-day average resting heart rate as of `cdate`. |
| `get_weekly_calories_stats(end=None, weeks=52)` | Return weekly resting/active/total calories. |
| `get_weekly_floors_stats(end=None, weeks=52)` | Return weekly floors totals. |
| `get_weekly_heart_rate_stats(end=None, weeks=52)` | Return weekly heart rate averages (incl. abnormal HR alert counts). |
| `get_weekly_hydration_stats(end=None, weeks=52)` | Return weekly hydration totals. |
| `get_weekly_intensity_minutes(start, end)` | Fetch weekly intensity minutes aggregates. |
| `get_weekly_steps(end, weeks=52)` | Fetch weekly steps aggregates. |
| `get_weekly_stress(end, weeks=52)` | Fetch weekly stress aggregates. |
| `get_weekly_wellness_stats(start, end, metric_ids=None)` | Return weekly wellness metrics (default: resting heart rate, id 60). |
| `set_steps_goal(steps, cdate=None)` | Set a manual daily step goal, or return to the device's automatic goal. |
| `update_jetlag_trip(trip_id, start_date, end_date, flights)` | Replace a Jet Lag Adviser trip. |

</details>

<details><summary><b>Performance metrics</b> (46)</summary>

| Method | Description |
| --- | --- |
| `get_acclimation_stats(start, end)` | Return SpO2 acclimation statistics over a date range. |
| `get_activity_power_curve(activity_id)` | Return the power curve of one activity (empty without power data). |
| `get_biometric_stats(start, end, aggregation='daily', user_first_day='monday')` | Return aggregated biometric statistics (weight, body fat, LT, ...) per period. |
| `get_critical_swim_speed(cdate=None)` | Return the latest Critical Swim Speed as of `cdate` (default today). |
| `get_critical_swim_speed_range(start, end, aggregation=None)` | Return Critical Swim Speed history for a date range. |
| `get_current_biometrics()` | Return the current biometric profile (height, weight, VO2 max, LT, FTP). |
| `get_cycling_ability(cdate=None)` | Return the latest Cycling Ability profile as of `cdate` (default today). |
| `get_cycling_ability_range(start, end, aggregation='DAILY')` | Return Cycling Ability history (`cyclingAbilitiesMap` keyed by date). |
| `get_cycling_ftp()` | Return cycling Functional Threshold Power (FTP) information. |
| `get_daily_training_status(cdate)` | Return the training status for a single day for the current user. |
| `get_endurance_score(startdate, enddate=None, aggregation='weekly')` | Return endurance score by day for 'startdate' format 'YYYY-MM-DD' through enddate 'YYYY-MM-DD'. |
| `get_fitness_age_daily(start, end)` | Return daily Fitness Age history (fitness age, RHR, body fat, ...). |
| `get_fitness_age_details(cdate=None)` | Return Fitness Age with its components and achievable targets. |
| `get_fitness_age_weekly(end=None, weeks=52)` | Return weekly Fitness Age history for `weeks` weeks ending at `end`. |
| `get_fitnessage_data(cdate)` | Return Fitness Age data for current user. |
| `get_functional_threshold_power_range(start, end, *, sport='RUNNING', aggregation='daily')` | Return historic functional threshold power for a Garmin sport. |
| `get_glucose_data(cdate)` | Return logged glucose readings for a day (`glucoseList`). |
| `get_glucose_data_range(start, end)` | Return logged glucose readings for a date range. |
| `get_heart_rate_zones()` | Return configured heart rate zones for all sport profiles. |
| `get_heart_rate_zones_v2(generate_defaults=False)` | Return heart rate zones per sport from the v2 endpoint the web app uses. |
| `get_heat_altitude_acclimation(cdate=None)` | Return heat and altitude acclimation as of `cdate` (default today). |
| `get_heat_altitude_acclimation_range(start, end, aggregation='daily')` | Return heat and altitude acclimation history for a date range. |
| `get_hill_score(startdate, enddate=None)` | Return hill score by day from 'startdate' format 'YYYY-MM-DD' to enddate 'YYYY-MM-DD'. |
| `get_lactate_threshold(*, latest=True, start_date=None, end_date=None, …)` | Return running lactate threshold information, including heart rate, power, and speed. |
| `get_max_metrics(cdate)` | Return available max metric data for 'cdate' format 'YYYY-MM-DD'. |
| `get_max_metrics_latest(cdate=None)` | Return the latest VO2 max record as of `cdate` (default today). |
| `get_max_metrics_range(start, end, aggregation='daily', sport=None)` | Return max metric data for a date range ('start'/'end' format 'YYYY-MM-DD'). |
| `get_morning_training_readiness(cdate)` | Return morning training readiness data for current user. |
| `get_one_rep_max(cdate=None, exercise_type=None)` | Return current estimated one-rep-max values (strength training). |
| `get_one_rep_max_history(exercise_type, start, end, aggregation='daily')` | Return one-rep-max history for an exercise (`daily` or `monthly`). |
| `get_power_curve(start, end, sport='cycling')` | Return the power curve (best power per duration) for a date range. |
| `get_power_zones()` | Return configured power zones for all supported sports. |
| `get_power_zones_for_sport(sport)` | Return configured power zones for a Garmin sport key. |
| `get_race_predictions(startdate=None, enddate=None, _type=None)` | Return race predictions for the 5k, 10k, half marathon and marathon. |
| `get_running_economy(cdate=None)` | Return the latest Running Economy score as of `cdate` (default today). |
| `get_running_economy_range(start, end, aggregation='daily')` | Return Running Economy history for a date range. |
| `get_running_tolerance(startdate, enddate, aggregation='weekly')` | Return running tolerance data for date range. |
| `get_spo2_acclimation_data(cdate=None)` | Return daily pulse ox readings together with acclimation values. |
| `get_stamina_curve(cdate=None, sport_type='running')` | Return the latest stamina curve for `sport_type` (`running`/`cycling`). |
| `get_training_four_week_load_balance(cdate)` | Return training load balance (load focus) data for the current user. |
| `get_training_readiness(cdate)` | Return training readiness data for 'cdate' format 'YYYY-MM-DD'. |
| `get_training_readiness_range(start, end)` | Return training readiness entries for a date range. |
| `get_training_status(cdate)` | Return training status data for current user. |
| `get_weekly_training_status(start, end)` | Return the weekly training status / load history for a date range. |
| `update_heart_rate_zones(zones)` | Write heart rate zones for one or more sports. |
| `update_power_zones(zones)` | Write power zones for one or more sports. |

</details>

<details><summary><b>Weight, body composition & blood pressure</b> (22)</summary>

| Method | Description |
| --- | --- |
| `add_body_composition(timestamp, weight, percent_fat=None, percent_hydration=None, visceral_fat_mass=None, …)` | Add a weigh-in with body composition values, uploaded as a FIT file. |
| `add_weigh_in(weight, unitKey='kg', timestamp='')` | Add a weigh-in (kg by default). |
| `add_weigh_in_with_timestamps(weight, unitKey='kg', dateTimestamp='', gmtTimestamp='')` | Add a weigh-in with explicit local and GMT timestamps (kg by default). |
| `delete_blood_pressure(version, cdate)` | Delete one blood pressure reading. |
| `delete_weigh_in(weight_pk, cdate)` | Delete one weigh-in. |
| `delete_weigh_ins(cdate, delete_all=False)` | Delete the weigh-ins on 'cdate' (all of them only with `delete_all=True`). |
| `get_blood_pressure(startdate, enddate=None)` | Return blood pressure by day for 'startdate' format 'YYYY-MM-DD' through enddate 'YYYY-MM-DD'. |
| `get_blood_pressure_day(cdate=None)` | Return blood pressure readings for one day. |
| `get_body_composition(startdate, enddate=None)` | Return available body composition data for 'startdate' format 'YYYY-MM-DD' through enddate 'YYYY-MM-DD'. |
| `get_daily_last_blood_pressure(start, end)` | Return the last blood pressure reading of each day in a range. |
| `get_daily_last_weight(start, end)` | Return the last weigh-in of each day in a date range (chart series). |
| `get_daily_weigh_ins(cdate)` | Get weigh-ins for 'cdate' format 'YYYY-MM-DD'. |
| `get_first_weight()` | Return the first weigh-in ever recorded on the account. |
| `get_latest_weight(cdate=None)` | Return the most recent weigh-in as of `cdate` (default today). |
| `get_power_to_weight_range(start, end, aggregation='daily', sport=None)` | Return power-to-weight history, one series per sport. |
| `get_stats_and_body(cdate)` | Return the daily summary and body composition for a date. |
| `get_weekly_blood_pressure(end=None)` | Return weekly blood pressure aggregates for the 52 weeks ending at `end`. |
| `get_weekly_weight(end=None)` | Return weekly weight aggregates for the 52 weeks ending at `end`. |
| `get_weigh_ins(startdate, enddate)` | Get weigh-ins between startdate and enddate using format 'YYYY-MM-DD'. |
| `get_weight_snapshot(start, end)` | Return all weigh-ins in a range as `dateWeightList` entries. |
| `set_blood_pressure(systolic, diastolic, pulse=None, timestamp='', notes='')` | Add a blood pressure reading. |
| `update_blood_pressure(measurement, *, notes)` | Change the note of an existing blood pressure reading. |

</details>

<details><summary><b>Activities</b> (46)</summary>

| Method | Description |
| --- | --- |
| `count_activities()` | Return total number of activities for the current user account. |
| `create_manual_activity(start_datetime, time_zone, type_key, distance_km, duration_min, activity_name)` | Create a private activity manually with a few basic parameters. |
| `create_manual_activity_from_json(payload)` | Create a manual activity from a complete activity payload. |
| `delete_activity(activity_id)` | Delete activity with specified id. |
| `download_activity(activity_id, dl_fmt=<ActivityDownloadFormat.TCX: 2>)` | Download an activity as the original file (zip), TCX, GPX, KML or CSV. |
| `get_activities(start=0, limit=20, activitytype=None, …)` | Return a page of activities, newest first, optionally filtered by type. |
| `get_activities_by_date(startdate, enddate=None, activitytype=None, sortorder=None)` | Return activities between two dates, optionally filtered by type. |
| `get_activities_fordate(fordate)` | Return available activities for date. |
| `get_activity(activity_id)` | Return activity summary, including basic splits. |
| `get_activity_details(activity_id, maxchart=2000, maxpoly=4000)` | Return activity details. |
| `get_activity_event_types()` | Return the activity event types (race, training, recreation, ...). |
| `get_activity_exercise_sets(activity_id)` | Return activity exercise sets. |
| `get_activity_hr_in_timezones(activity_id)` | Return the time spent in each heart rate zone during an activity. |
| `get_activity_images(activity_id)` | Return the photos attached to an activity. |
| `get_activity_jump_details(activity_id)` | Return jump data (jump rope and similar; empty when `jumpCount` is 0). |
| `get_activity_laps(activity_id)` | Return the laps of an activity (`lapDTOs`). |
| `get_activity_map_details(activity_id, maxpoly=4000, max_heat_map=4000)` | Return the polyline and heat map of an activity without the charts. |
| `get_activity_polyline(activity_id)` | Return the encoded track polyline of an activity (`gPolyline`). |
| `get_activity_power_in_timezones(activity_id)` | Return the time spent in each power zone during an activity. |
| `get_activity_rounds(activity_id)` | Return rounds with their exercise sets (HIIT, boxing, ...). |
| `get_activity_segments(activity_id)` | Return the segments matched in an activity. |
| `get_activity_split_summaries(activity_id)` | Return activity split summaries. |
| `get_activity_splits(activity_id)` | Return activity splits. |
| `get_activity_step_details(activity_id)` | Return the per-workout-step details of a structured workout activity. |
| `get_activity_subsecond_details(activity_id, maxchart=2000)` | Return sub-second samples (only when `metadataDTO.hasSubsecondData`). |
| `get_activity_swim_details(activity_id, maxchart=2000, maxpoly=4000)` | Return details for a lap-swimming activity. |
| `get_activity_typed_splits(activity_id)` | Return typed activity splits. |
| `get_activity_types()` | Return all activity types and their parent types. |
| `get_activity_weather(activity_id)` | Return activity weather. |
| `get_adjacent_activities(activity_id)` | Return the ids of the previous and next activity (`None` when absent). |
| `get_available_metrics(start, end, activity_types=None)` | Return which progress-summary metrics have data per activity type. |
| `get_fastest_splits(start, end, activity_type='running', number_of_bests=10)` | Return the fastest splits (best times per distance) in a date range. |
| `get_favorite_activities(limit=5)` | Return activities marked as favorite (`activityList`). |
| `get_last_activity()` | Return the most recent activity. |
| `get_progress_summary_between_dates(startdate, enddate, metric='distance', groupbyactivities=True)` | Return progress totals (distance, duration, ...) between two dates. |
| `get_training_load_activities(startdate, enddate, *, metrics=None, activitytype=None)` | Fetch individual activities and their training load metrics for a date range. |
| `get_weekly_activity_stats(start, end, group_by_activity_type=True)` | Return weekly activity aggregates (VO2 max, distance, duration, ...). |
| `import_activity(activity_path)` | Upload activity as an import (not re-exported to third parties like Strava). |
| `search_activities(start=0, limit=20, **filters)` | Search activities with the full filter set of the web app's activity list. |
| `set_activity_description(activity_id, description)` | Set the description of an activity. |
| `set_activity_exercise_sets(activity_id, payload)` | Replace the exercise sets of a strength activity. |
| `set_activity_favorite(activity_id, favorite=True)` | Mark or unmark an activity as favorite. |
| `set_activity_name(activity_id, title)` | Set the name of an activity. |
| `set_activity_type(activity_id, type_id, type_key, parent_type_id)` | Change the activity type of an activity. |
| `update_activity(activity_id, fields)` | Change one or more fields of an activity in a single call. |
| `upload_activity(activity_path)` | Upload an activity file (FIT, GPX or TCX). |

</details>

<details><summary><b>Workouts</b> (24)</summary>

| Method | Description |
| --- | --- |
| `copy_workout(workout_id, name)` | Duplicate a workout under a new name and return the copy. |
| `delete_workout(workout_id)` | Delete a workout template from the workout library. |
| `download_workout(workout_id)` | Download a workout as a FIT file. |
| `get_next_scheduled_workout()` | Return the earliest upcoming scheduled workout (today or later). |
| `get_scheduled_workout_by_id(scheduled_workout_id)` | Return one scheduled workout. |
| `get_scheduled_workouts(year, month)` | Return the scheduled workouts of a calendar month. |
| `get_scheduled_workouts_by_period(start, end)` | Return all scheduled workouts between two dates, including adaptive plans. |
| `get_strength_benchmarks()` | Return the strength benchmark exercises (used for 1RM based targets). |
| `get_workout_by_id(workout_id)` | Return one workout from the library. |
| `get_workout_count(include_atp=False)` | Return workout counts per sport (`totalCount`, `runningCount`, ...). |
| `get_workout_sport_types()` | Return the sport types that have workouts in the library. |
| `get_workout_types()` | Return the workout dictionaries (step, condition, target, sport, equipment types). |
| `get_workouts(start=0, limit=100, *, my_workouts_only=None, …)` | Return workouts starting at offset `start` with at most `limit` results. |
| `reschedule_workout(scheduled_workout_id, cdate)` | Move a scheduled workout to another date. |
| `schedule_workout(workout_id, date_str)` | Schedule a workout on a specific date in the Garmin calendar. |
| `unschedule_workout(scheduled_workout_id)` | Remove a scheduled workout from the calendar without deleting the template. |
| `update_workout(workout_id, workout_json)` | Replace an existing workout in place, keeping its id. |
| `upload_cycling_workout(workout)` | Upload a typed cycling workout. |
| `upload_hiking_workout(workout)` | Not supported: Garmin has no hiking workout sport type; always raises. |
| `upload_running_workout(workout)` | Upload a typed running workout. |
| `upload_strength_workout(workout)` | Upload a typed strength training workout. |
| `upload_swimming_workout(workout)` | Upload a typed swimming workout. |
| `upload_walking_workout(workout)` | Not supported: Garmin has no walking workout sport type; always raises. |
| `upload_workout(workout_json)` | Upload a workout from a JSON dict or string. |

</details>

<details><summary><b>Training plans, calendar, courses & reports</b> (35)</summary>

| Method | Description |
| --- | --- |
| `convert_activity_to_course(activity_id)` | Return a course object built from an activity's track (not yet saved). |
| `create_calendar_event(event)` | Create a race / goal event from a full event object (see `get_calendar_event`). |
| `create_calendar_note(cdate, name, content='')` | Add a note to a calendar day. |
| `create_course(course)` | Create a course from a full course object (see `get_course`). |
| `delete_calendar_event(event_id)` | Delete a calendar event. |
| `delete_calendar_note(note_id)` | Delete a calendar note. |
| `delete_course(course_id)` | Delete a course. |
| `delete_training_plan(plan_id)` | Remove a scheduled training plan from the calendar. |
| `download_course(course_id, fmt='gpx')` | Download a course as GPX or FIT. |
| `download_report(report_id)` | Download a finished report as PDF bytes. |
| `get_active_training_plans(cdate=None)` | Return the training plans active on a date (`trainingPlanList`). |
| `get_adaptive_training_plan_by_id(plan_id)` | Return details for a specific adaptive training plan. |
| `get_calendar_event(event_id)` | Return one calendar event. |
| `get_calendar_events(start, end)` | Return race / goal events between two dates. |
| `get_calendar_week(cdate=None, first_day_of_week=1)` | Return the calendar items of the week containing `cdate`. |
| `get_calendar_year(year)` | Return the year overview (which days have items). |
| `get_course(course_id)` | Return a course with its geo points. |
| `get_course_favorites()` | Return courses marked as favorite. |
| `get_courses()` | Return the user's courses. |
| `get_pace_bands()` | Return the user's PacePro pace bands. |
| `get_primary_event()` | Return the primary (focus) race event, or None when there is none. |
| `get_report_status(report_id)` | Return the progress of a report export (`progress.status`). |
| `get_training_plan_by_id(plan_id)` | Return details for a specific training plan. |
| `get_training_plan_tasks(plan_id, locale='en')` | Return the workout tasks of a training plan. |
| `get_training_plans(limit=None, start=None, status=None)` | Return the user's training plans (`{"trainingPlanList": [...]}`). |
| `get_upcoming_events(days_forward=90, limit=10)` | Return upcoming race / goal events. |
| `import_course(file_path)` | Import a course from a GPX, TCX or FIT file. |
| `move_calendar_item(item_type, item_id, cdate, item=None)` | Move a calendar item (workout, note, ...) to another date. |
| `request_report(category, start, end, options=None, locale='en-US')` | Start a PDF report export and return `{"reportId", "estimatedTimeForStatusCheck"}`. |
| `schedule_training_plan(plan_id, start_date)` | Schedule a training plan from the catalogue starting on `start_date`. |
| `search_training_plans(start=1, limit=20, locale='en', **filters)` | Browse the Garmin training plan catalogue (`trainingPlanList`). |
| `set_course_favorite(course_id, favorite=True)` | Mark or unmark a course as favorite. |
| `update_calendar_event(event_id, event)` | Update a calendar event with a full event object. |
| `update_calendar_note(note_id, cdate, name, content='')` | Change a calendar note's date, name or content. |
| `update_course(course_id, course)` | Update a course with a full course object. |

</details>

<details><summary><b>Goals, badges & challenges</b> (27)</summary>

| Method | Description |
| --- | --- |
| `get_active_adhoc_challenges()` | Return ad-hoc (friend) challenges that are still running. |
| `get_adhoc_challenges(start, limit)` | Return adhoc challenges for the current user. |
| `get_available_badge_challenges(start, limit)` | Return available badge challenges. |
| `get_available_badges()` | Return available (not yet earned) badges for the current user. |
| `get_available_virtual_challenges(start=1, limit=100)` | Return virtual (expedition) challenges that can be joined. |
| `get_badge_attributes()` | Return badge metadata: types, categories, difficulties. |
| `get_badge_challenge(challenge_uuid)` | Return one badge challenge. |
| `get_badge_challenges(start, limit)` | Return badge challenges for the current user. |
| `get_badge_detail(badge_id)` | Return the details of one badge. |
| `get_badges_for_activity(activity_id)` | Return badges earned by one activity. |
| `get_badges_for_day(cdate=None)` | Return badges earned on a day. |
| `get_completed_virtual_challenges(start=1, limit=100)` | Return completed virtual (expedition) challenges. |
| `get_earned_badges()` | Return all earned badges for the current user. |
| `get_effective_goals(cdate=None)` | Return the daily goals in effect on a day (intensity minutes, floors, hydration, ...). |
| `get_goals(status='active', start=1, limit=30)` | Return goals by status (active, future or past). |
| `get_in_progress_badges()` | Return all badges currently in progress for the current user. |
| `get_inprogress_virtual_challenges(start, limit)` | Return in-progress virtual challenges for current user. |
| `get_latest_earned_badges(limit=5)` | Return the most recently earned badges. |
| `get_non_completed_badge_challenges(start, limit)` | Return badge challenges that are not completed yet. |
| `get_personal_record(include_history=None, months=None)` | Return personal records for current user. |
| `get_personal_record_candidates()` | Return personal-record candidates awaiting confirmation. |
| `get_personal_record_types()` | Return the personal-record type definitions (id, key, sport, bounds). |
| `get_personal_records_for_activity(activity_id)` | Return personal records set by one activity. |
| `get_steps_goal(cdate=None)` | Return the effective step goal for a day (device vs. user goal). |
| `get_user_goals()` | Return the user's wellness goals (steps, weight, calories, ...). |
| `get_weight_goal(start, end)` | Return the weight goal(s) in effect over a date range. |
| `set_daily_goal(goal_type, value, cdate=None)` | Set a daily wellness goal such as intensity minutes, floors or hydration. |

</details>

<details><summary><b>Devices</b> (18)</summary>

| Method | Description |
| --- | --- |
| `get_active_devices()` | Return device info for the currently active devices. |
| `get_all_devices()` | Return all registered devices including inactive ones. |
| `get_device_alarms()` | Return the active alarms of all devices. |
| `get_device_app_info(device_id)` | Return device type and software information. |
| `get_device_displayed_activities(device_id)` | Return which activity profiles are shown on a device. |
| `get_device_last_used()` | Return the device that synced last. |
| `get_device_messages()` | Return the queue of pending device messages (software updates, pushed workouts, ...). |
| `get_device_settings(device_id)` | Return device settings for device with 'device_id'. |
| `get_device_solar_data(device_id, startdate, enddate=None)` | Return solar data for compatible device with 'device_id'. |
| `get_device_solar_gain(device_id, start, end)` | Return daily solar gain for a device over a date range. |
| `get_devices()` | Return available devices for the current user account. |
| `get_historical_devices()` | Return devices that were registered in the past. |
| `get_primary_training_device()` | Return the primary training device and the priority order of all devices. |
| `get_sensors()` | Return paired external sensors (HRM, power meters, ...). |
| `get_user_device(device_id)` | Return the device's registration record (last upload/download times). |
| `push_workout_to_device(workout_id=None, device_id=None)` | Push a workout to a device. |
| `send_scheduled_workouts_to_devices()` | Push all scheduled workouts to the user's devices. |
| `update_device_settings(device_id, settings)` | Write (partial) device settings, e.g. alarms or activity tracking options. |

</details>

<details><summary><b>Gear</b> (18)</summary>

| Method | Description |
| --- | --- |
| `add_gear_to_activity(gearUUID, activity_id)` | Link gear to an activity. |
| `create_gear(gear_type, brand, model, name, first_use_date, usage_type='DISTANCE', max_usage_distance_km=None, max_usage_duration_min=None, …)` | Create a new piece of gear (e.g. a pair of shoes) and return it. |
| `delete_gear(gear_uuid)` | Delete a piece of gear. |
| `get_activity_gear(activity_id)` | Return the gear linked to an activity. |
| `get_activity_gear_v2(activity_id)` | Return the gear linked to an activity (v2 endpoint). |
| `get_gear(userProfileNumber)` | Return the gear of a user profile number (legacy `filterGear` endpoint). |
| `get_gear_activities(gearUUID, limit=1000)` | Return the activities a piece of gear was used in. |
| `get_gear_defaults(userProfileNumber)` | Return the default gear per activity type. |
| `get_gear_details(gear_uuid)` | Return one piece of gear (v2, dashed uuid). |
| `get_gear_list(start=0, limit=20, gear_statuses=None, …)` | Return the user's gear from the v2 endpoint the web app uses. |
| `get_gear_make_models(keywords)` | Search Garmin's make/model catalogue for the gear form's autocomplete. |
| `get_gear_stats(gearUUID)` | Return statistics (e.g. distance) for specific gear UUID. |
| `get_gear_types()` | Return the gear types Garmin knows (shoes, bike, ...). |
| `get_user_gear_types()` | Return the gear types the user actually has (`activeGearTypes`). |
| `remove_gear_from_activity(gearUUID, activity_id)` | Unlink gear from an activity. |
| `set_gear_default(activityType, gearUUID, defaultGear=True)` | Make gear the default for an activity type, or remove it as the default. |
| `set_gear_status(gear_uuid, status)` | Retire or re-activate gear. |
| `update_gear(gear_uuid, *, name=None, brand=None, model=None, …)` | Edit a piece of gear and return the updated gear object. |

</details>

<details><summary><b>Women's health</b> (11)</summary>

| Method | Description |
| --- | --- |
| `confirm_menstrual_period_start(period_start_date, period_length, cycle_length, *, predicted_cycle=False)` | Confirm a menstrual period start date, including a prediction. |
| `get_menstrual_calendar_data(startdate, enddate)` | Return summaries of cycles that have days between startdate and enddate. |
| `get_menstrual_cycle_summary(fordate)` | Return the menstrual cycle summary for `fordate`. |
| `get_menstrual_data_for_date(fordate, today_date=None)` | Return the menstrual day view for a date. |
| `get_menstrual_last_confirmed(fordate)` | Return the last confirmed menstrual cycle as of `fordate`. |
| `get_menstrual_reports(fordate, number_of_cycles=6, *, next_report=False, report_type='CYCLE', …)` | Return menstrual cycle reports for 1, 6, or 12 cycles ending at date. |
| `get_pregnancy_summary()` | Return pregnancy summary for the current user. |
| `init_menstrual_cycle_setup(period_start_date, period_length, cycle_length)` | Initialize menstrual cycle tracking with the first confirmed period. |
| `update_menstrual_calendar(startdate, enddate, cycle_dates_lists, *, today_calendar_date=None)` | Replace menstrual period dates in `startdate`..`enddate`. |
| `update_menstrual_daily_log(calendar_date, *, symptoms=None, moods=None, flow=None, …)` | Replace the menstrual daily log for `calendar_date`. |
| `update_menstrual_settings(settings, *, user_settings_id=None)` | Update `userMenstrualCycleSettings` on the user profile. |

</details>

<details><summary><b>Golf</b> (5)</summary>

| Method | Description |
| --- | --- |
| `get_golf_club_stats(limit=1000)` | Return golf club names and statistics. |
| `get_golf_scorecard(scorecard_id)` | Return golf scorecard detail by scorecard ID. |
| `get_golf_shot_data(scorecard_id, hole_numbers=None)` | Return golf shot data for a scorecard and specific holes. |
| `get_golf_summary(start=0, limit=100)` | Return golf scorecard summary. |
| `get_golf_user_stats()` | Return an overview of the user's golf statistics. |

</details>
<!-- METHODS:END -->

## 🛠️ Development

This project uses [PDM](https://pdm.fming.dev/) for dependency management and task automation.

> **⚠️ Important**: Create a virtual environment first on externally-managed Python installs (Debian/Ubuntu) to avoid system package conflicts.

```bash
python3 -m venv .venv --copies
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install pdm
python3 -m pdm install --group :all
pre-commit install --install-hooks  # optional but recommended
```

> **Note**: Using `python -m pdm` instead of `pdm` avoids PATH issues on some
> Windows setups where `pip install pdm` places the `pdm` executable outside
> the directories on `PATH`. Once `pdm install` has run, subsequent `pdm run ...`
> commands work normally because the venv's `Scripts/` directory is on `PATH`
> while the venv is active.

**Development commands:**

```bash
pdm run format      # Auto-format code (isort, black, ruff --fix)
pdm run lint        # Check code quality (isort, ruff, black, mypy)
pdm run codespell   # Check spelling
pdm run test        # Run test suite
pdm run testcov     # Run tests with coverage report
pdm run all         # Run all checks (lint + codespell + pre-commit + test)
pdm run clean       # Clean build artifacts and cache files
pdm run build       # Build package for distribution
pdm run publish     # Build and publish to PyPI
pdm run --list      # Show all available commands
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the checks CI runs and what a pull request needs.

## 🔐 Authentication

Authentication uses the same mobile SSO flow as the official Garmin Connect mobile apps.
No browser is needed.

**How it works:**

1. **First login**: Authenticates via `sso.garmin.com/mobile/api/login` using the iOS
   app's client ID (`GCM_IOS_DARK`). If MFA is required, a callback (`prompt_mfa`) prompts for the one-time code.
2. **Token exchange**: The service ticket is exchanged for DI OAuth Bearer tokens
   (`access_token` + `refresh_token`) via `diauth.garmin.com`. Tokens are stored at
   `~/.garminconnect/garmin_tokens.json`.
3. **Auto-refresh**: Before each API request the library checks whether the DI token is about
   to expire and refreshes it automatically — no user interaction required.

**Session lifetime:**
- DI tokens auto-refresh indefinitely as long as the refresh token remains valid.
- A full re-login with credentials (and possibly MFA) is only needed if the refresh token
  itself expires or is revoked.

**Token storage:**
```bash
~/.garminconnect/garmin_tokens.json   # saved automatically, mode 0600
```

The containing directory is restricted to mode `0700`. Treat the token file
like a password: the refresh token can provide persistent account access. Avoid
putting a Garmin password in shell history or a long-lived environment variable;
prefer `getpass()` or another interactive secret prompt.

**Resilient login (multi-strategy + token validation):**

`login()` tries several authentication strategies in order (mobile, SSO widget,
web portal — each with and without TLS impersonation) and only declares success
when the resulting token is actually accepted by the API. If a strategy obtains
a token the API later rejects (a region/account-specific condition — see
[#369](https://github.com/cyberjunky/python-garminconnect/issues/369)), the
library transparently falls through to the next strategy. Set
`Garmin(..., verify_login=False)` to restore the legacy "first token wins"
behavior.

**Cached-token gotcha & self-healing:** when a `tokenstore` is supplied,
`login()` loads those tokens *before* the strategy chain and short-circuits if
they load — so stale/poisoned cached tokens used to fail every run. The library
now detects this: if cached tokens are rejected by the API, it discards them and
performs a fresh credential login automatically. To force a clean slate yourself
(e.g. between a failed resume and a retry), call:

```python
g.logout()  # clears in-memory auth + cached tokens (uses GARMINTOKENS)
g.logout(tokenstore)  # or pass an explicit path
```

`logout()` removes only the local `garmin_tokens.json` file and preserves its
directory and unrelated files. It does **not** revoke a token that has already
been issued by Garmin. Revoke account access from Garmin's account/security
settings if a token may have been copied or exposed.

### What running it locally does

This is an unofficial client for Garmin's web services; it does not pair with
the Garmin Connect phone app or connect directly to a watch. When you call
`login()`, your credentials and MFA code are sent over HTTPS to Garmin's login
service. The library receives an access/refresh token pair and, when a token
store is supplied, caches it locally for later sessions. Subsequent API methods
send that token to Garmin and can read or change the same account data that the
selected method targets.

The library does not automatically download an entire account. The demo writes
responses, activity downloads, and health reports only when you select those
actions. Demo exports are stored under `your_data/` with owner-only directory
and file permissions. Run the project in a dedicated virtual environment, read
the method you plan to call, and start with read-only methods. Upload, edit,
delete, schedule, hydration, weigh-in, menstrual, and jet lag trip write methods can change Garmin account data.

## 🧪 Testing

The default suite is credential-free and excludes live-account integration tests:

```bash
pdm run test        # Run all tests
pdm run testcov     # Run tests with coverage report
```

To explicitly run live integration tests, use a test account if possible. This
can create local VCR recordings and includes methods that may mutate the account:

```bash
export GARMIN_EMAIL="you@example.com"
read -s GARMIN_PASSWORD && export GARMIN_PASSWORD
pdm run pytest -m integration --vcr-record=once
unset GARMIN_PASSWORD
```

VCR recordings are ignored by Git because Garmin responses contain sensitive
health, activity, location, and account data. Do not commit them.

## 📦 Publishing

For package maintainers:

**Setup PyPI credentials:**

```bash
pip install twine
# Edit with your preferred editor, or create via here-doc:
# cat > ~/.pypirc <<'EOF'
# [pypi]
# username = __token__
# password = <PyPI_API_TOKEN>
# EOF
```

```ini
[pypi]
username = __token__
password = <PyPI_API_TOKEN>
```

Recommended: use environment variables and restrict file perms

```bash
chmod 600 ~/.pypirc
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="<PyPI_API_TOKEN>"
```

**Publish new version:**

```bash
pdm run publish    # Build and publish to PyPI
```

**Alternative publishing steps:**

```bash
pdm run build      # Build package only
pdm publish        # Publish pre-built package
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- **Report Issues**: Bug reports and feature requests via GitHub issues
- **Submit PRs**: Code improvements, new features, documentation updates
- **Testing**: Help test new features and report compatibility issues
- **Documentation**: Improve examples, add use cases, fix typos

**Before contributing**, read [CONTRIBUTING.md](CONTRIBUTING.md). It covers the dev setup, the checks CI runs, and how to add an API method. Release notes are in [CHANGELOG.md](CHANGELOG.md).

### Jupyter Notebook

Explore the API interactively with our [reference notebook](https://github.com/cyberjunky/python-garminconnect/blob/master/docs/reference.ipynb).

### Python Code Examples

```python
import os
from getpass import getpass
from datetime import date
from garminconnect import Garmin

# First run: logs in and saves tokens to ~/.garminconnect
# Subsequent runs: loads saved tokens and auto-refreshes
client = Garmin(
    os.getenv("GARMIN_EMAIL"),
    getpass("Garmin password: "),
    prompt_mfa=lambda: input("MFA code: "),
)
client.login("~/.garminconnect")

# Get today's stats
today = date.today().isoformat()
stats = client.get_stats(today)

# Get heart rate data
hr_data = client.get_heart_rates(today)
print(f"Resting HR: {hr_data.get('restingHeartRate', 'n/a')}")
```

### Typed Workouts (Pydantic Models)

The library includes optional typed workout models for creating type-safe workout definitions:

```bash
pip install garminconnect[workout]
```

```python
from garminconnect.workout import (
    RunningWorkout,
    WorkoutSegment,
    PaceTarget,
    create_warmup_step,
    create_interval_step,
    create_targeted_interval_step,
    create_distance_interval_step,
    create_cooldown_step,
    create_repeat_group,
    pace_to_mps,
)

easy_pace = PaceTarget(
    lower_limit=pace_to_mps(6, 11, "km"), upper_limit=pace_to_mps(6, 0, "km")
)

# Create a structured running workout
workout = RunningWorkout(
    workoutName="Easy Run",
    estimatedDurationInSecs=900,
    workoutSegments=[
        WorkoutSegment(
            segmentOrder=1,
            sportType={"sportTypeId": 1, "sportTypeKey": "running"},
            workoutSteps=[
                create_warmup_step(300.0),
                create_interval_step(  # No intensity target
                    duration_seconds=400.0,
                    step_order=2,
                ),
                create_targeted_interval_step(  # With target pace
                    duration_seconds=200.0,
                    step_order=3,
                    target=easy_pace,
                ),
            ],
        )
    ],
)

# Upload and optionally schedule it
result = client.upload_running_workout(workout)
client.schedule_workout(result["workoutId"], "2026-03-20")

# Edit it in place - keeps its id, so any schedules pointing at it stay valid
workout_data = client.get_workout_by_id(result["workoutId"])
workout_data["workoutName"] = "Easy Run (revised)"
client.update_workout(result["workoutId"], workout_data)

# Delete a workout or remove it from the calendar
client.delete_workout(workout_id)
client.unschedule_workout(scheduled_workout_id)

# Push a workout to a device - defaults to the last workout / last used device
client.push_workout_to_device(result["workoutId"], device_id)
```

**Swimming CSS targets:** `SwimCssOffsetTarget` represents a signed offset from
Critical Swim Speed, rather than an absolute pace range. Supply it as the
secondary target; the primary target can be omitted (Garmin `no.target`):

```python
from garminconnect.workout import (
    SwimCssOffsetTarget,
    create_targeted_distance_interval_step,
)

step = create_targeted_distance_interval_step(
    100.0,
    step_order=1,
    secondary_target=SwimCssOffsetTarget(offset_seconds=5.0),
)
```

Positive offsets are slower than CSS; negative offsets are faster. The offset
is serialized as `secondaryTargetValueOne`, with `secondaryTargetValueTwo=0`.
The time-based targeted helper also accepts secondary-only targets. These
helpers retain their existing interval step/end-condition behavior; swimming
stroke, rest, and pool settings are configured separately.

**Available workout classes:** `RunningWorkout`, `CyclingWorkout`, `SwimmingWorkout`, `StrengthWorkout`, `MultiSportWorkout`, `FitnessEquipmentWorkout`. Garmin has no walking or hiking workout sport type, so `upload_walking_workout()` and `upload_hiking_workout()` raise `ValueError`; the sport types Garmin accepts are listed by `get_workout_types()["workoutSportTypes"]`.

**Strength workouts** are usually rep-based. Build each exercise with `create_strength_set(category, step_order, sets, reps, rest_seconds, exercise_name="", weight_kg=None, description=None)` and identify exercises with a `category` / `exercise` pair from the bundled catalog in `garminconnect.exercises` (1,527 exercises across 47 categories, with `resolve(name)` and `find(term)` helpers):

```python
from garminconnect import exercises
from garminconnect.workout import StrengthWorkout, WorkoutSegment, create_strength_set

lat = exercises.resolve(
    "Lat Pull-down"
)  # {'category': 'PULL_UP', 'exercise': 'LAT_PULLDOWN'}

workout = StrengthWorkout(
    workoutName="Upper Body",
    estimatedDurationInSecs=0,
    workoutSegments=[
        WorkoutSegment(
            segmentOrder=1,
            sportType={"sportTypeId": 5, "sportTypeKey": "strength_training"},
            workoutSteps=[
                create_strength_set(
                    "BENCH_PRESS", step_order=1, sets=4, reps=10, rest_seconds=120
                ),
                create_strength_set(
                    lat["category"],
                    step_order=4,
                    sets=3,
                    reps=12,
                    rest_seconds=90,
                    exercise_name=lat["exercise"],
                ),
            ],
        )
    ],
)
client.upload_strength_workout(workout)
```

For exercises done for time, such as planks or carries, use `create_strength_timed_set` (or `create_strength_timed_step` for a single step); it takes `duration_seconds` instead of `reps`. Every strength helper also accepts an optional `description`, a per-step note such as a form cue:

```python
from garminconnect.workout import create_strength_timed_set

plank = create_strength_timed_set(
    "PLANK",
    step_order=1,
    sets=3,
    duration_seconds=45,
    rest_seconds=30,
    exercise_name="PLANK",
    description="Squeeze glutes, keep a neutral spine",
)
```

**Helper functions:** `create_warmup_step`, `create_interval_step`,
`create_targeted_interval_step`, `create_distance_interval_step`,
`create_targeted_distance_interval_step`, `create_recovery_step`,
`create_cooldown_step`, `create_repeat_group`, `create_strength_exercise_step`,
`create_strength_timed_step`, `create_strength_rest_step`, `create_strength_set`,
`create_strength_timed_set`

**Intensity Targets**: `CadenceTarget`, `PowerZoneTarget`, `CustomPowerTarget`,
`HeartRateZoneTarget`, `CustomHeartRateTarget`, `SpeedTarget`, `PaceTarget`

Use `create_distance_interval_step(600.0, step_order=1)` for interval steps that should end after a distance in meters instead of after a duration.

### Golf

The library supports reading Garmin Golf scorecards, shot-level data, club statistics, and golf user statistics.

```python
# List recent golf scorecards
summary = client.get_golf_summary(limit=10)
scorecard_id = summary["scorecardSummaries"][0]["id"]

# Get the full scorecard details
scorecard = client.get_golf_scorecard(scorecard_id)

# Get shot-by-shot data
# - Omit hole_numbers to receive every hole (recommended for holes 10-18).
# - Single-digit holes work as a comma- or dash-separated list, e.g. "1,2,3".
#   Commas are normalized to dashes because Garmin only accepts '-' as the
#   separator.
# - Double-digit holes (10-18) cannot be fetched with a filter at all; the
#   API either drops them or returns an empty response. If you request holes
#   10-18, the library falls back to returning all 18 holes.
shots = client.get_golf_shot_data(scorecard_id)
shots = client.get_golf_shot_data(scorecard_id, hole_numbers="1,2,3")

# Club and player statistics
club_stats = client.get_golf_club_stats()
user_stats = client.get_golf_user_stats()
```

### Jet Lag Adviser

The library can list, create, replace, and delete Jet Lag Adviser trips. Garmin does not geocode a location: give each place its UTC offset on that date, and give each time as the local time at that place, without an offset.

Each flight is one origin and destination, so you can include legs as part of a trip or not. Garmin accepts any legs, including a leg that changes no timezone and a trip in the past, which the web page does not allow. Garmin says it deletes a trip by itself after the trip ends.

```python
flights = [
    {
        "originLocation": "Portland, OR, United States",
        "originTimezone": "-07:00",
        "originTimestamp": "2027-10-04T15:20:00.00",
        "destinationLocation": "Melbourne, VIC, Australia",
        "destinationTimezone": "+11:00",
        "destinationTimestamp": "2027-10-06T06:45:00.00",
    },
]
start_date = "2027-10-04"
trip = client.add_jetlag_trip(start_date, "2027-10-09", flights)

# A PUT replaces the whole trip: send every flight, and keep each flightId
client.update_jetlag_trip(trip["tripId"], start_date, "2027-10-12", trip["flights"])

client.delete_jetlag_trip(trip["tripId"])
```

### Activity Photos

Photos attached to an activity are available inside the `get_activity()`
response at `metadataDTO.activityImages`; the `get_activity_images()`
helper returns that list directly:

```python
# [{imageId, url, photoDate}, ...] or [] when the activity has no photos
images = client.get_activity_images(activity_id)
```

The `url` values are presigned S3 links that expire after 24 hours, so
download the images promptly instead of storing the URLs. The `hasImages`
flag in `get_activities()` results is not a reliable indicator that an
activity has photos attached.

### Additional Resources
- **Simple Example**: [example.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/example.py) - Getting started guide
- **Comprehensive Demo**: [demo.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/demo.py) - All 270 API methods
- **API Documentation**: Comprehensive method documentation in source code
- **Test Cases**: Real-world usage examples in `tests/` directory

## 🙏 Acknowledgments

Special thanks to all contributors who have helped improve this project:

- **Community Contributors**: Bug reports, feature requests, and code improvements
- **Issue Reporters**: Helping identify and resolve compatibility issues
- **Feature Developers**: Adding new API endpoints and functionality
- **Documentation Authors**: Improving examples and user guides

This project thrives thanks to community involvement and feedback.

## 💖 Support This Project

If you find this library useful for your projects, please consider supporting its continued development and maintenance:

### 🌟 Ways to Support

- **⭐ Star this repository** - Help others discover the project
- **💰 Financial Support** - Contribute to development and hosting costs
- **🐛 Report Issues** - Help improve stability and compatibility
- **📖 Spread the Word** - Share with other developers

### 💳 Financial Support Options

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

**Why Support?**
- Keeps the project actively maintained
- Enables faster bug fixes and new features
- Supports infrastructure costs (testing, AI, CI/CD)
- Shows appreciation for hundreds of hours of development

Every contribution, no matter the size, makes a difference and is greatly appreciated! 🙏

[releases-shield]: https://img.shields.io/github/release/cyberjunky/python-garminconnect.svg?style=for-the-badge
[releases]: https://github.com/cyberjunky/python-garminconnect/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/cyberjunky/python-garminconnect.svg?style=for-the-badge
[commits]: https://github.com/cyberjunky/python-garminconnect/commits/master
[license-shield]: https://img.shields.io/github/license/cyberjunky/python-garminconnect.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-cyberjunky-blue.svg?style=for-the-badge
