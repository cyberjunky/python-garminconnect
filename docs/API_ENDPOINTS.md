# Garmin Connect endpoints used by the web app

In October 2026 the API calls made by the Garmin Connect web app
(`connect.garmin.com`) were compared with what this library implements. This
document lists the result: new methods, extended existing methods, and the
differences that were found and deliberately left alone. For every method the
table gives the HTTP verb, path and query parameters the web app sends.

All paths are relative to `https://connectapi.garmin.com` unless a full URL is
shown. The *Verified* column says whether the call was executed against a real
account while adding it:

- **yes** – returned HTTP 200 with the expected shape;
- **yes (empty)** – returned 200 with an empty list/object because the account
  has no such data, so the field names are not confirmed;
- **no** – a write, or data the test account does not have; the request shape
  matches what the web app sends but was not confirmed with a response.

Dates are `YYYY-MM-DD`. Methods whose date argument is optional default to
*today in the user's Garmin timezone* (`Garmin.today()`), not the machine's
clock.

## Performance metrics (`metrics-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_max_metrics_latest(cdate=None)` | `GET /metrics-service/metrics/maxmet/latest/{date}` | Latest VO2 max: `generic` (running), `cycling`, `heatAltitudeAcclimation`. | yes |
| `get_max_metrics_range(start, end, aggregation="daily", sport=None)` | `GET /metrics-service/metrics/maxmet/{daily\|weekly\|monthly}/{start}/{end}[?sport=]` | Existing method; `aggregation` and `sport` are new and optional. | yes |
| `get_training_readiness_range(start, end)` | `GET /metrics-service/metrics/trainingreadiness/{start}/{end}` | Several entries per day are possible (`inputContext`). | yes |
| `get_weekly_training_status(start, end)` | `GET /metrics-service/metrics/trainingstatus/weekly/{displayName}?fromCalendarDate&toCalendarDate` | Weekly load / status series of the Training Status page. | yes |
| `get_heat_altitude_acclimation(cdate=None)` | `GET /metrics-service/metrics/heataltitudeacclimation/latest/{date}` | | yes |
| `get_heat_altitude_acclimation_range(start, end, aggregation="daily")` | `GET /metrics-service/metrics/heataltitudeacclimation/{daily\|weekly\|monthly}/{start}/{end}` | | yes |
| `get_cycling_ability(cdate=None)` | `GET /metrics-service/metrics/cycling-ability/latest?calendarDate=` | | yes |
| `get_cycling_ability_range(start, end, aggregation="DAILY")` | `GET /metrics-service/metrics/cycling-ability?startDate&endDate&aggregation` | Returns `cyclingAbilitiesMap` keyed by date. | yes |
| `get_running_economy(cdate=None)` | `GET /metrics-service/metrics/runningeconomy/latest/{date}` | Empty without a capable device. | yes (empty) |
| `get_running_economy_range(start, end, aggregation="daily")` | `GET /metrics-service/metrics/runningeconomy/{daily\|weekly}?startDate&endDate` | | yes (empty) |
| `get_stamina_curve(cdate=None, sport_type="running")` | `GET /metrics-service/metrics/stamina-curve/latest?calendarDate&sportType` | | yes (empty) |
| `get_endurance_score(start, end=None, aggregation="weekly")` | `GET /metrics-service/metrics/endurancescore/stats?startDate&endDate&aggregation` | Existing method; `aggregation` (`daily`/`weekly`) is new. | yes |

Not added: `/metrics-service/metrics/eventracetimeprojections/{eventId}/{d1}/{d2}`
(date semantics unclear) and the internal `manualstresslevel` path.

## Biometrics (`biometric-service`, `userprofile-service/biometric`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_heart_rate_zones_v2(generate_defaults=False)` | `GET /biometric-service/heartRateZones/v2?generateDefaults=` | The web app reads zones from v2; `get_heart_rate_zones` keeps v1. | yes |
| `get_biometric_stats(start, end, aggregation="daily", user_first_day="monday")` | `GET /biometric-service/stats?aggregation&userFirstDay&startDate&endDate` | Per-period weight, body fat, LT, FTP statistics. | yes |
| `get_power_to_weight_range(start, end, aggregation="daily", sport=None)` | `GET /biometric-service/stats/powerToWeight/range/{start}/{end}?aggregation[&sport]` | One series per sport. | yes |
| `get_critical_swim_speed(cdate=None)` | `GET /biometric-service/criticalSwimSpeed/latest/{date}` | | yes (empty) |
| `get_critical_swim_speed_range(start, end, aggregation=None)` | `GET /biometric-service/criticalSwimSpeed/range/{start}/{end}[?aggregation]` | | yes (empty) |
| `get_glucose_data(cdate)` | `GET /biometric-service/biometric/glucose/{date}` | `glucoseList`. | yes (empty) |
| `get_glucose_data_range(start, end)` | `GET /biometric-service/biometric/glucose/{start}/{end}` | | yes (empty) |
| `get_current_biometrics()` | `GET /userprofile-service/biometric/current/{displayName}` | Height, weight, VO2 max, LT speed/HR, FTP. | yes |

## Fitness statistics (`fitnessstats-service`, `fitnessage-service`, `personalrecord-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_power_curve(start, end, sport="cycling")` | `GET /fitnessstats-service/powerCurve?startDate&endDate&sport` | | yes (empty) |
| `get_available_metrics(start, end, activity_types=None)` | `GET /fitnessstats-service/activity/availableMetrics?startDate&endDate[&activityType]` | Which metrics `get_progress_summary_between_dates` can return. | yes |
| `get_one_rep_max(cdate=None, exercise_type=None)` | `GET /fitnessstats-service/vbt-stats/one-rep-max[/{exerciseType}]/current/{date}` | | yes (empty) |
| `get_one_rep_max_history(exercise_type, start, end, aggregation="daily")` | `GET /fitnessstats-service/vbt-stats/one-rep-max/{exerciseType}/{daily\|monthly}?startDate&endDate` | 404 when the exercise has no data. | no |
| `get_fitness_age_details(cdate=None)` | `GET /fitnessage-service/fitnessage/v2/{date}` | Components and achievable fitness age. | yes |
| `get_fitness_age_daily(start, end)` | `GET /fitnessage-service/stats/daily/{start}/{end}` | | yes |
| `get_fitness_age_weekly(end=None, weeks=52)` | `GET /fitnessage-service/stats/weekly/{end}/{weeks}` | | yes |
| `get_personal_record(include_history=None, months=None)` | `GET /personalrecord-service/personalrecord/prs/{displayName}[?includeHistory&months]` | Existing method; both parameters are new and only sent when given. | yes |
| `get_personal_record_candidates()` | `GET /personalrecord-service/personalrecordcandidate/{displayName}` | Records awaiting confirmation. | yes |
| `get_personal_record_types()` | `GET /personalrecord-service/personalrecordtype/prtypes/{displayName}` | Type id → key, sport, bounds. | yes |
| `get_personal_records_for_activity(activity_id)` | `GET /personalrecord-service/personalrecord/prByActivityId/{activityId}` | | yes (empty) |
| `get_progress_summary_between_dates(...)` | `GET /fitnessstats-service/activity?...&groupByParentActivityType=true\|false` | Existing method; the boolean is now sent lowercase like the web app. | yes |

## Daily statistics (`usersummary-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_daily_stats(start, end, stats_type="STEPS", current_date=None, aggregated=False)` | `GET /usersummary-service/stats/daily[/aggregated]/{start}/{end}?statsType=STEPS\|PUSHES\|CALORIES&currentDate` | The series the web reports use; `get_daily_steps` keeps the older `stats/steps/daily` path, which still works. | yes |
| `get_daily_heart_rate_stats(start, end)` | `GET /usersummary-service/stats/heartRate/daily/{start}/{end}` | Resting / min / max HR per day. | yes |
| `get_weekly_heart_rate_stats(end=None, weeks=52)` | `GET /usersummary-service/stats/heartRate/weekly/{end}/{weeks}` | | yes |
| `get_daily_stress_stats(start, end)` | `GET /usersummary-service/stats/stress/daily/{start}/{end}` | | yes |
| `get_daily_body_battery_stats(start, end)` | `GET /usersummary-service/stats/bodybattery/daily/{start}/{end}` | Daily low/high. | yes |
| `get_daily_intensity_minutes_stats(start, end)` | `GET /usersummary-service/stats/im/daily/{start}/{end}` | | yes |
| `get_daily_respiration_stats(start, end)` | `GET /usersummary-service/stats/respiration/daily/{start}/{end}` | | yes |
| `get_daily_floors_stats(start, end)` | `GET /usersummary-service/stats/floors/daily/{start}/{end}` | | yes |
| `get_weekly_floors_stats(end=None, weeks=52)` | `GET /usersummary-service/stats/floors/weekly/{end}/{weeks}` | | yes |
| `get_daily_hydration_stats(start, end)` | `GET /usersummary-service/stats/hydration/daily/{start}/{end}` | | yes (empty) |
| `get_weekly_hydration_stats(end=None, weeks=52)` | `GET /usersummary-service/stats/hydration/weekly/{end}/{weeks}` | | yes (empty) |
| `get_weekly_calories_stats(end=None, weeks=52)` | `GET /usersummary-service/stats/calories/weekly/{end}/{weeks}` | | yes |
| `get_monthly_steps(end=None, months=12)` | `GET /usersummary-service/stats/steps/monthly/{end}/{months}` | | yes |
| `get_stats_averages(start, end)` | `GET /usersummary-service/stats/averages/{start}/{end}` | Average steps and resting HR. | yes |
| `get_lifetime_totals()` | `GET /usersummary-service/stats/connectLifetimeTotals/{displayName}` | | yes |
| `get_daily_summaries(start, end)` | `GET /usersummary-service/v2/dailysummaries?startDate&endDate` | One `get_user_summary` record per day in a single call. | yes |
| `get_week_average_resting_hr(cdate=None)` | `GET /usersummary-service/usersummary/weekAverageRestingHR/{displayName}?calendarDate` | | yes |
| `get_hydration_all_data(cdate=None)` | `GET /usersummary-service/usersummary/hydration/allData/{date}` | Intake, goal, sweat loss, containers. | yes |

## Wellness (`wellness-service`, `userstats-service`, `sleep-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_spo2_acclimation_data(cdate=None)` | `GET /wellness-service/wellness/daily/spo2acclimation/{date}` | Superset of `get_spo2_data` (whose `daily/spo2` path still works). | yes |
| `get_daily_movement(cdate=None)` | `GET /wellness-service/wellness/dailyMovement?calendarDate` | | yes |
| `get_steps_goal(cdate=None)` | `GET /wellness-service/wellness/wellness-goals/consolidated/steps/{date}` | Device vs. user step goal. | yes |
| `get_sync_timestamp()` | `GET /wellness-service/wellness/syncTimestamp` | UTC timestamp string. | yes |
| `get_hourly_intensity_minutes(end=None, days=7)` | `GET /wellness-service/stats/hourly/im/{end}/{days}` | Garmin accepts 1–7 days inside the current week. | yes |
| `get_acclimation_stats(start, end)` | `GET /wellness-service/stats/daily/acclimation?fromDate&untilDate` | SpO2 acclimation statistics. | yes |
| `get_weekly_wellness_stats(start, end, metric_ids=None)` | `GET /userstats-service/wellness/weekly/{displayName}?fromWeekStartDate&untilWeekStartDate&metricId&grpParentActType=false` | Default metric 60 = resting HR. | yes |
| `get_monthly_wellness_stats(start, end, metric_ids=None)` | `GET /userstats-service/wellness/monthly/{displayName}?fromMonthStartDate&untilMonthStartDate&metricId&grpParentActType=false` | | yes |
| `get_weekly_activity_stats(start, end, group_by_activity_type=True)` | `GET /userstats-service/activities/weekly/{displayName}?fromWeekStartDate&untilWeekStartDate&grpActType` | | yes |
| `get_user_statistics()` | `GET /userstats-service/statistics/{displayName}` | Totals per activity type. | yes |
| `get_daily_sleep(cdate=None, non_sleep_buffer_minutes=60)` | `GET /sleep-service/sleep/dailySleepData?date[&nonSleepBufferMinutes]` | The Sleep page's current call; `get_sleep_data` keeps the wellness-service variant. | yes |
| `get_naps(cdate=None, include_overlaps=True)` | `GET /sleep-service/sleep/naps/{date}?includeOverlaps` | | yes (empty) |
| `get_sleep_stats_weekly(end=None, weeks=52)` | `GET /sleep-service/stats/sleep/weekly/{end}/{weeks}` | | yes |
| `get_sleep_stats_overall(start, end)` | `GET /sleep-service/stats/sleep/overall/{start}/{end}` | | yes |

## Health Snapshot (`wellnessactivity-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_health_snapshots(cdate=None)` | `GET /wellnessactivity-service/activity/summary/{date}` | | yes (empty) |
| `get_health_snapshots_range(start, end)` | `GET /wellnessactivity-service/activity/summary/range/{start}/{end}` | Entries carry `activityUuid.uuid`. | yes |
| `get_health_snapshot(cdate, snapshot_uuid)` | `GET /wellnessactivity-service/activity/summary/{date}/{uuid}` | | yes |
| `get_health_snapshot_epochs(snapshot_uuid)` | `GET /wellnessactivity-service/activity/epoch/{uuid}` | Per-epoch HR, HRV, SpO2, respiration, stress. | yes |
| `download_health_snapshot_session(cdate, snapshot_uuid)` | `GET /download-service/files/wellness/activity/{date}/{uuid}` | FIT bytes of one session. | yes |

## Nutrition (`nutrition-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_nutrition_status()` | `GET /nutrition-service/user/nutritionCurrentStatus` | | yes |
| `get_calorie_summary(start, end, current_date=None)` | `GET /nutrition-service/calorie/summary/daily?startDate&endDate&currentDate&isDataForReport=true` | Per-meal totals with goals. | yes |
| `get_nutrition_daily_food_log(cdate, include_goals=True, include_nutrition=True, meal_id=None)` | `GET /nutrition-service/food/logs/{date}?includeGoals&includeNutrition[&mealId]` | Existing method; the flags the web app always sends are new. | yes |

## Weight and blood pressure (`weight-service`, `bloodpressure-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_latest_weight(cdate=None)` | `GET /weight-service/weight/latest?date&ignorePriority=true` | | yes |
| `get_first_weight()` | `GET /weight-service/weight/first` | | yes |
| `get_daily_last_weight(start, end)` | `GET /weight-service/weight/daily/last?startDate&endDate` | Last weigh-in per day. | yes |
| `get_weight_snapshot(start, end)` | `GET /weight-service/weight/daterangesnapshot?startDate&endDate` | `dateWeightList`. | yes |
| `get_weekly_weight(end=None)` | `GET /weight-service/weight/weeklyRange/{end-363d}/{end}` | Garmin insists on exactly 52 weeks (364 days inclusive). | yes |
| `get_blood_pressure_day(cdate=None)` | `GET /bloodpressure-service/bloodpressure/dayview/{date}` | | yes (empty) |
| `get_daily_last_blood_pressure(start, end)` | `GET /bloodpressure-service/bloodpressure/daily/last/{start}/{end}` | | yes (empty) |
| `get_weekly_blood_pressure(end=None)` | `GET /bloodpressure-service/bloodpressure/weeklyRange/{end-363d}/{end}` | Same 52-week rule. | yes (empty) |

## ECG (`https://ghs.garmin.com/ghs/ecg/v1`)

The ECG service lives on a sibling host; the client now accepts full URLs on
`*.garmin.com` / `*.garmin.cn` for this purpose. Accounts without the ECG
feature get a 404.

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_ecg_daily(start, end)` | `GET https://ghs.<domain>/ghs/ecg/v1/ecg/daily?firstDay&lastDay` | `content` per day. | yes |
| `get_ecg_list(start="2021-01-01", end=None, page_size=20, page=None)` | `GET https://ghs.<domain>/ghs/ecg/v1/ecg/list?firstDay&lastDay&pageSize[&page]` | `content[].detailId`. | yes |
| `get_ecg(ecg_id)` | `GET https://ghs.<domain>/ghs/ecg/v1/ecg/{ecgId}` | Waveform of one recording. | no |

## Goals, badges and challenges

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_effective_goals(cdate=None)` | `GET /goal-service/goal/user/effective/{date}` | Intensity minutes, floors, hydration goals in effect. | yes |
| `get_user_goals()` | `GET /goal-service/goal/user` | Steps/weight/calorie goals (`userGoalPk`). | yes |
| `get_weight_goal(start, end)` | `GET /goal-service/goal/user/effective/weightgoal/{start}/{end}` | | yes (empty) |
| `get_badge_attributes()` | `GET /badge-service/badge/attributes` | Types, categories, difficulties. | yes |
| `get_badge_detail(badge_id)` | `GET /badge-service/badge/detail/v3/{badgeId}` | | yes |
| `get_latest_earned_badges(limit=5)` | `GET /badge-service/badge/earned/latest/{displayName}?limit` | | yes |
| `get_badges_for_activity(activity_id)` | `GET /badge-service/badge/{displayName}/earned/activity/{activityId}` | | yes (empty) |
| `get_badges_for_day(cdate=None)` | `GET /badge-service/badge/{displayName}/earned/dailysummary/{date}` | | yes (empty) |
| `get_available_virtual_challenges(start=1, limit=100)` | `GET /badgechallenge-service/virtualChallenge/available?start&limit` | Expeditions. | yes |
| `get_completed_virtual_challenges(start=1, limit=100)` | `GET /badgechallenge-service/virtualChallenge/completed?desc=true&start&limit` | | yes (empty) |
| `get_badge_challenge(challenge_uuid)` | `GET /badgechallenge-service/badgeChallenge/{uuid}` | | no |
| `get_active_adhoc_challenges()` | `GET /adhocchallenge-service/adHocChallenge/nonCompleted` | Running friend challenges. | yes (empty) |

## Profile and account

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_user_timezone()` | `GET /userprofile-service/userprofile/personal-information/{displayName}` | IANA timezone of the profile, cached; see `today()`/`now()`. | yes |
| `get_personal_information(include_biometric=True, include_vo2max=True)` | same `?includeBiometric&includeVO2Max` | `userInfo`, `biometricProfile`, VO2 max. | yes |
| `get_user_profile_base()` | `GET /userprofile-service/userprofile/userProfileBase` | | yes |
| `get_privacy_settings()` | `GET /privacysettings-service/privacy-settings` | | yes |
| `get_usage_indicators()` | `GET /web-gateway/snapshot/usageIndicators` | Which features the account's devices support. | yes |
| `get_jetlag_status(cdate=None)` | `GET /jetlag-service/jetlag/status/daily/{date}` | Empty without a trip. | yes (empty) |

## Activities (`activitylist-service`, `activity-service`, `segment-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `search_activities(start=0, limit=20, **filters)` | `GET /activitylist-service/activities/search/activities?start&limit&…` | Full web filter set: `activityType`, `activitySubType`, `startDate`, `endDate`, `search`, `favorite=1`, `sortBy`/`sortOrder`, `minDistance`/`maxDistance`, `minDuration`/`maxDuration`, `minElevation`/`maxElevation`, `eventType`, `excludeChildren`. | yes |
| `get_fastest_splits(start, end, activity_type="running", number_of_bests=10)` | `GET /activitylist-service/activities/fastest-splits?numberOfBests&startDate&endDate&activityType` | | yes |
| `get_favorite_activities(limit=5)` | `GET /activitylist-service/activities/favorite/{displayName}?limit` | | yes (empty) |
| `set_activity_favorite(activity_id, favorite=True)` | `PUT /activity-service/activity/{id}` `{"activityId", "metadataDTO": {"favorite"}}` | Same partial update as `set_activity_name`. Read back via `metadataDTO.favorite` and `get_favorite_activities()`. | yes |
| `get_activity_laps(activity_id)` | `GET /activity-service/activity/{id}/laps` | `lapDTOs`. | yes |
| `get_activity_rounds(activity_id)` | `GET /activity-service/activity/{id}/rounds` | HIIT/boxing rounds with sets. | yes (empty) |
| `get_activity_step_details(activity_id)` | `GET /activity-service/activity/{id}/stepdetails` | Structured-workout steps. | yes (empty) |
| `get_activity_jump_details(activity_id)` | `GET /activity-service/activity/{id}/jumpDetails` | | yes (empty) |
| `get_activity_subsecond_details(activity_id, maxchart=2000)` | `GET /activity-service/activity/{id}/subseconddetails?maxChartSize` | Only when `metadataDTO.hasSubsecondData`. | yes (empty) |
| `get_activity_swim_details(activity_id, maxchart=2000, maxpoly=4000)` | `GET /activity-service/activity/{id}/swimDetails?maxChartSize&maxPolylineSize` | Pool swims use this instead of `/details`. | yes (empty) |
| `get_activity_map_details(activity_id, maxpoly=4000, max_heat_map=4000)` | `GET /activity-service/activity/{id}/mapdetails?maxPolylineSize&maxHeatMapSize` | Polyline + heat map without charts. | yes |
| `get_activity_polyline(activity_id)` | `GET /activity-service/activity/polyline/{id}` | Encoded `gPolyline`. | yes |
| `get_activity_power_curve(activity_id)` | `GET /activity-service/activity/{id}/powerCurve` | | yes (empty) |
| `get_adjacent_activities(activity_id)` | `GET /activity-service/activity/{id}/prev` + `/next` | `{"previous", "next"}` ids. | yes |
| `get_activity_event_types()` | `GET /activity-service/activity/eventTypes` | | yes |
| `get_activity_segments(activity_id)` | `GET /segment-service/segment/list/{activityId}` | | yes (empty) |

## Gear (`gear-service` v2)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_gear_list(start=0, limit=20, gear_statuses=None, gear_type=None, sort_order=None)` | `GET /gear-service/gear/v2/list?start&limit[&gearStatuses&gearType&sortOrder]` | Dashed uuids; `get_gear` returns legacy undashed uuids that v2 does not accept. | yes |
| `get_gear_details(gear_uuid)` | `GET /gear-service/gear/v2/{uuid}` | | yes |
| `set_gear_status(gear_uuid, status)` | `PUT /gear-service/gear/v2/{uuid}/status/{ACTIVE\|RETIRED}` | | no |
| `get_gear_types()` | `GET /gear-service/gear/types` | | yes |
| `get_user_gear_types()` | `GET /gear-service/gear/v2/user-gear-types` | | yes |
| `get_gear_make_models(keywords)` | `GET /gear-service/gear/makemodels?keywords` | Autocomplete for the gear form. | yes |
| `get_activity_gear_v2(activity_id)` | `GET /gear-service/activity/v2/{activityId}` | `get_activity_gear` keeps the legacy `filterGear?activityId` call. | yes (empty) |

## Devices (`device-service`, `devicesettings-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_all_devices()` | `GET /device-service/deviceregistration/devices/all/{displayName}` | Includes inactive devices. | yes |
| `get_historical_devices()` | `GET /device-service/deviceregistration/devices/historical` | | yes |
| `get_active_devices()` | `GET /device-service/deviceservice/device-info/active/{displayName}` | | yes |
| `get_user_device(device_id)` | `GET /device-service/deviceservice/user-device/{deviceId}` | Last upload/download timestamps. | yes |
| `get_device_app_info(device_id)` | `GET /device-service/deviceservice/app-info/device/{deviceId}` | | yes |
| `get_sensors()` | `GET /device-service/sensors` | Paired sensors. | yes (empty) |
| `get_device_messages()` | `GET /device-service/devicemessage/messages` | Pending software updates / pushed items. | yes |
| `get_device_displayed_activities(device_id)` | `GET /devicesettings-service/device/displayed-activities/{deviceId}` | | yes (empty) |
| `update_device_settings(device_id, settings)` | `PUT /device-service/deviceservice/device-info/settings/{deviceId}` | Partial settings object. | no |
| `get_device_solar_gain(device_id, start, end)` | `GET /device-service/devicemonitoring/solargain/{deviceId}/{start}/{end}` | The web app's multi-day solar call; `get_device_solar_data` keeps the web-gateway view. | yes (empty) |

## Workouts and schedule (`workout-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_workouts(start, limit, *, my_workouts_only, shared_workouts_only, include_atp, order_by, order_seq, sport_type_keys)` | `GET /workout-service/workouts?start&limit[&myWorkoutsOnly&sharedWorkoutsOnly&includeAtp&orderBy&orderSeq&sportTypeKey…]` | Existing method; the filters are new, optional keywords. | yes |
| `get_scheduled_workouts_by_period(start, end)` | `GET /workout-service/schedule/workoutScheduleByPeriod?startDate&endDate` | Includes adaptive-plan sessions; the proper source for "next workout". | yes (empty) |
| `get_workout_count(include_atp=False)` | `GET /workout-service/workouts/count?includeAtp` | | yes |
| `get_workout_sport_types()` | `GET /workout-service/workouts/sport-types` | | yes |
| `get_workout_types()` | `GET /workout-service/workout/types` | Source of the ids in `garminconnect.workout`. | yes |
| `get_strength_benchmarks()` | `GET /workout-service/benchmarks` | | yes |
| `copy_workout(workout_id, name)` | `POST /workout-service/workout/copy/{workoutId}` (text/plain name) | Returns the new workout with its `workoutId`. | yes |
| `reschedule_workout(scheduled_workout_id, cdate)` | `PUT /workout-service/schedule/{scheduleId}` | Existing entry + `calendarDate`. | yes |
| `send_scheduled_workouts_to_devices()` | `PUT /workout-service/schedule/sendtodevices` | | no |

## Training plans (`trainingplan-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_training_plans(limit=None, start=None, status=None)` | `GET /trainingplan-service/trainingplan/plans[?limit&start&status]` | Existing method; parameters are new and optional. | yes |
| `get_active_training_plans(cdate=None)` | `GET /trainingplan-service/trainingplan/active-plans?startDate` | | yes (empty) |
| `get_training_plan_tasks(plan_id, locale="en")` | `GET /trainingplan-service/trainingplan/tasks/{planId}?localeKey` | | yes |
| `search_training_plans(start=1, limit=20, locale="en", **filters)` | `POST /trainingplan-service/trainingplan/search?start&limit&locale[&types&subTypes&categories&version]` (empty form body) | Garmin's plan catalogue. | yes |
| `schedule_training_plan(plan_id, start_date)` | `GET /trainingplan-service/trainingplan/schedule/{planId}?startDate` | Side-effecting GET, as the web app does it. | no |
| `delete_training_plan(plan_id)` | `DELETE /trainingplan-service/trainingplan/trainingplan/{planId}` | | no |

## Calendar (`calendar-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_calendar_year(year)` | `GET /calendar-service/year/{year}` | | yes |
| `get_calendar_week(cdate=None, first_day_of_week=1)` | `GET /calendar-service/year/{y}/month/{m-1}/day/{d}/start/{firstDayOfWeek}` | Month is 0-based; 0 = Sunday … 6 = Saturday. | yes |
| `get_calendar_events(start, end)` | `GET /calendar-service/events?startDate&endDate` | Race / goal events. | yes |
| `get_upcoming_events(days_forward=90, limit=10)` | `GET /calendar-service/events/upcoming?numDaysForward&limit` | | yes |
| `get_primary_event()` | `GET /calendar-service/event/primary` | None when there is no primary event. | yes |
| `get_calendar_event(event_id)` | `GET /calendar-service/event/{eventId}` | | yes |
| `create_calendar_event(event)` / `update_calendar_event(event_id, event)` / `delete_calendar_event(event_id)` | `POST /calendar-service/event`, `PUT`/`DELETE /calendar-service/event/{eventId}` | Full event object as returned by `get_calendar_event`. | no |
| `move_calendar_item(item_type, item_id, cdate, item=None)` | `PUT /calendar-service/calendarItem/{itemType}/{id}/date/{date}` | | no |

## Courses (`course-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `get_courses()` | `GET /course-service/course/owner/{displayName}` | | yes (empty) |
| `get_course(course_id)` | `GET /course-service/course/{courseId}` | Geo points included. | no |
| `create_course(course)` / `update_course(course_id, course)` / `delete_course(course_id)` | `POST /course-service/course`, `PUT`/`DELETE /course-service/course/{courseId}` | | no |
| `download_course(course_id, fmt="gpx")` | `GET /course-service/course/gpx/{courseId}` or `/fit/{courseId}/0?elevation=true` | | no |
| `import_course(file_path)` | `POST /course-service/course/import` (multipart `file`) | GPX, TCX or FIT. | no |
| `convert_activity_to_course(activity_id)` | `GET /course-service/course/convert/activity/{activityId}` | Returns an unsaved course object for `create_course`. | yes |
| `get_course_favorites()` / `set_course_favorite(course_id, favorite=True)` | `GET`/`POST /course-service/course/favorites`, `DELETE …/favorites/course/{courseId}` | | yes (empty) / no |
| `get_pace_bands()` | `GET /course-service/pacebands` | PacePro bands. | yes (empty) |

## PDF reports (`reportexport-service`)

| Method | Request | Notes | Verified |
|---|---|---|---|
| `request_report(category, start, end, options=None, locale="en-US")` | `POST /reportexport-service/export/init/{category}/{start}/{end}?locale` | Categories seen: `bloodPressure`, `wellnessactivity`. Returns `reportId`. | no |
| `get_report_status(report_id)` | `GET /reportexport-service/export/reportStatus/{reportId}` | Poll until `progress.status == "READY"`. | no |
| `download_report(report_id)` | `GET /reportexport-service/export/reportContent/{reportId}` | PDF bytes. | no |

## Other changes to existing methods

| Method | Change |
|---|---|
| `get_menstrual_data_for_date(fordate, today_date=None)` | Now sends `todayDate` (defaults to today in the user's timezone) like the web app always does. |
| `request_reload(cdate, device_id=None)` | Optional device id appended to the path. |
| `get_next_scheduled_workout()` | Docstring corrected: adaptive-plan sessions are available via `get_scheduled_workouts_by_period`. |
| `today()`, `now()`, `get_user_timezone()` | New helpers; every default date/timestamp the library fills in now uses the profile timezone. |

## Differences found and deliberately kept

These library calls differ from what the web app sends today, but every one
of them was confirmed to still work against a live account, so they were kept
for backwards compatibility. The web-app variant is available as a new method
where useful.

| Library call | Web app today |
|---|---|
| `get_spo2_data` → `/wellness/daily/spo2/{date}` | `/wellness/daily/spo2acclimation/{date}` (`get_spo2_acclimation_data`) |
| `get_all_day_events` → `/wellness/dailyEvents?calendarDate` | `/wellness/dailyEvents/{displayName}?calendarDate` |
| `get_daily_steps` → `/stats/steps/daily/{s}/{e}` | `/stats/daily/{s}/{e}?statsType=STEPS&currentDate` (`get_daily_stats`) |
| `get_heart_rates`, `get_steps_data` → `…/{displayName}?date` | same path without the display name |
| `get_sleep_data` → `wellness-service/…/dailySleepData/{displayName}` | `sleep-service/sleep/dailySleepData?date` (`get_daily_sleep`) |
| `get_hill_score` → `/metrics/hillscore` | not called by the web app any more (served through GraphQL `hillScoreScalar`), still responds |
| `get_device_solar_data` → `/web-gateway/solar/…?singleDayView` | multi-day ranges use `/devicemonitoring/solargain/…` (`get_device_solar_gain`) |
| `get_gear`, `get_gear_stats`, `get_gear_defaults`, `set_gear_default` → legacy `gear-service/gear/…` | `gear-service/gear/v2/…` (`get_gear_list`, `get_gear_details`, …) |
| `upload_activity` → multipart field `file` | field `userfile`, path `/upload-service/upload/.fit` |
| `push_workout_to_device` → list body to `device-service/devicemessage/messages` | single object to `devicemessage-service/devicemessage/messages` |
| `get_gear_activities` → `start=0` | `start=1`; the server returns the same first page for both |

## Not implemented

Social and account-administration endpoints of the web app are left out on
purpose: comments, likes, image flags, connections and followers, groups,
leaderboards, inbox/newsfeed, ad-hoc challenge invites, profile image upload,
Office 365 calendar sync, Fitbit import, dive/golf/animal (dog) specifics, the
Index scale set-up (`weightscale-service`), nutrition food search/favourites/
recipes/custom foods, dashboard layout (`userfocus-service`) and UI
preferences (`userpreference-service`). Open an issue if you need one of them.

The GraphQL gateway operations the dashboard uses are listed in
[graphql_operations.md](graphql_operations.md).
