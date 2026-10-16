# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Numbers in parentheses refer to GitHub issues and pull requests. Releases before
0.3.10 are described on the [GitHub Releases](https://github.com/cyberjunky/python-garminconnect/releases)
page.

## [0.3.19] - 2026-10-16

### Added

- **Gear notes can be read and edited**: new `update_gear(gear_uuid, notes=..., name=..., max_usage_distance_km=..., ...)` edits a piece of gear the way the Garmin Connect web app does (a `PUT` of the complete gear object to `gear-service/gear/v2/{uuid}`; Garmin rejects partial bodies), and `delete_gear(gear_uuid)` removes one. Notes were never part of the legacy `get_gear()` record; `get_gear_list()` and `get_gear_details()` return them. Tested live: an edited note persists and is shown in Garmin Connect. (issue 420)
- **More edit calls, each checked live against Garmin**: `update_activity()` (generic partial update of an activity), `update_blood_pressure()` (note of an existing reading — Garmin only stores the note on this call; values need delete + re-add), `set_steps_goal()` (manual step goal or back to automatic), `set_daily_goal()` (intensity minutes, floors, hydration, weight goal), `update_heart_rate_zones()` / `update_power_zones()`, `update_user_settings()`, `set_primary_training_device()`, and calendar notes (`create_calendar_note()`, `update_calendar_note()`, `delete_calendar_note()`). `add_weigh_in()` now also sends the local `date` and `add_hydration_data()` the `userProfileId`, as the web app does. The legacy `set_gear_default()` endpoint returns 404 for gear created through the v2 API; `update_gear(activity_type_keys=...)` is the working alternative and its docstring says so.
- **165 new methods covering the endpoints the Garmin Connect web app uses**: every API call the web app makes was compared with the library and the missing ones were added. The new methods are documented, with the exact request each one sends and whether it was verified against a live account, in [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md). Highlights:
  - *Performance*: `get_max_metrics_latest()`, `get_training_readiness_range()`, `get_weekly_training_status()`, heat/altitude acclimation, cycling ability, running economy, stamina curve, power curve, critical swim speed, glucose, heart rate zones v2, biometric statistics, power-to-weight history, fitness age v2 with daily/weekly history, personal-record candidates/types/per-activity.
  - *Daily statistics*: `get_daily_stats()` (steps/pushes/calories with aggregations), daily and weekly series for heart rate, stress, Body Battery, intensity minutes, respiration, floors, hydration and calories, monthly steps, averages, lifetime totals, `get_daily_summaries()` for a date range, week-average resting HR, full hydration data.
  - *Wellness*: SpO2 with acclimation, daily movement, step goal, sync timestamp, hourly intensity minutes, weekly/monthly wellness and activity statistics, `get_daily_sleep()` (sleep-service), naps, weekly/overall sleep statistics, Health Snapshot sessions (list, detail, epochs, FIT download), nutrition status and calorie summary.
  - *Weight & blood pressure*: latest/first weight, last weight per day, weight snapshot, weekly weight; blood pressure day view, last reading per day, weekly aggregates.
  - *ECG*: `get_ecg_daily()`, `get_ecg_list()` and `get_ecg()` from the `ghs.connect.garmin.com` service.
  - *Goals, badges, challenges, profile*: effective daily goals, user goals, weight goal, badge attributes/detail/latest/per-activity/per-day, virtual (expedition) challenges, active ad-hoc challenges, `get_personal_information()`, user profile base, privacy settings, usage indicators, jet lag status.
  - *Activities*: `search_activities()` with the web app's full filter set, fastest splits, favorites, laps, rounds, step/jump/sub-second/swim details, map details, polyline, power curve, previous/next activity, event types, matched segments, `set_activity_favorite()`.
  - *Gear & devices*: gear v2 list/detail/status/types/make-models, gear on an activity (v2); all/historical/active devices, device record, app info, sensors, device message queue, displayed activities, `update_device_settings()`, multi-day solar gain.
  - *Workouts, plans, calendar, courses*: scheduled workouts by period (includes adaptive plans), workout counts/sport types/type dictionaries, strength benchmarks, copy/reschedule/send-to-devices; active plans, plan tasks, plan catalogue search, schedule/delete plan; calendar year/week/events/upcoming/primary event and event CRUD, move calendar item; courses list/detail/CRUD/download/import/convert/favorites, PacePro bands; PDF report export flow.
- **Extended existing methods (all optional, backwards compatible)**: `get_workouts()` gains the library page's filters and sorting; `get_training_plans()` gains `limit`/`start`/`status`; `get_personal_record()` gains `include_history`/`months`; `get_endurance_score()` and `get_max_metrics_range()` gain `aggregation` (and `sport`); `get_nutrition_daily_food_log()` sends `includeGoals`/`includeNutrition` like the web app; `request_reload()` accepts a device id; `get_menstrual_data_for_date()` sends `todayDate` as the web app does.
- **GraphQL**: all 53 operations the web dashboard sends to the GraphQL gateway are documented in [docs/graphql_operations.md](docs/graphql_operations.md) for use with `query_garmin_graphql()`.
- **User timezone helpers**: new `get_user_timezone()` returns the IANA timezone from your Garmin profile (for example `Europe/Paris`), and `today()` / `now()` give the current date and time in that timezone. Garmin evaluates "today" in the profile timezone, so use `api.today()` rather than `date.today()` when asking for today's data.
- **Method reference in the README**: every public method, grouped by domain, with its parameters and a one-line description. `scripts/gen_method_reference.py` generates it from the docstrings and a test fails when it is out of date. Unclear or missing docstrings were rewritten for it.
- **Demo**: the 100 new read methods are available from the existing menu categories (Training Plans is now "Training Plans & Calendar"), plus a new "Activity Details & Courses" category for per-activity details, activity search and courses.

### Changed

- **The `Garmin` class is now assembled from one module per data domain** in the new `garminconnect.api` package: `base` (construction, login, transport, profile), `activities`, `health`, `metrics`, `body`, `achievements`, `gear`, `devices`, `workouts`, `training` (plans, calendar, courses, reports), `womens_health` and `golf`, with the shared constants and validation helpers in `api/_common.py`. `from garminconnect import Garmin` and every constant and helper previously importable from the package still work; `Garmin.ActivityDownloadFormat` and `Garmin.ActivityUploadFormat` are unchanged. The only internal move that affects test code is that `_fmt_ts_utc` is now patched at `garminconnect.api.womens_health._fmt_ts_utc`.
- **`garminconnect.client` is now a package** split by concern: `constants`, `sso` (login strategies and MFA), `session` (ticket exchange and token refresh), `tokens` (token store and JWT helpers) and `transport` (authenticated requests). Every name that was importable from `garminconnect.client` still is, including the optional-dependency flags `HAS_CFFI`/`HAS_UA_GEN`, so existing imports and test patches keep working. Duplicated code was folded into shared helpers: one TLS-fingerprint rotation loop and one credential-response handler serve both the mobile and portal flows, the `post`/`put`/`delete` wrappers share one implementation, the two DI token requests share one, and JWT_WEB cookie extraction and SSO page parsing each live in one place.

### Fixed

- **"Today" no longer follows the machine clock**: every default date and timestamp the library fills in itself (the lactate-threshold and power-to-weight lookups, the next scheduled workout, menstrual reports and calendar updates, and the local timestamps of new weigh-ins, body-composition entries, blood-pressure readings and hydration logs) is now computed in your Garmin profile timezone. On a host running in UTC these used to lag behind your real day every evening, so "today" silently returned or wrote yesterday's data. Timestamps you pass in without an offset are now also read as your profile's local time rather than the host's. Nothing changes when the host and your profile share a timezone.
- **README**: the demo method and category counts match the demo again (262 methods in 15 categories).
- **Demo**: dates are evaluated when a menu option runs, not once at startup, so a session left open overnight no longer keeps using yesterday; once logged in they follow your profile timezone.
- **`get_progress_summary_between_dates()` sends `groupByParentActivityType` as `true`/`false`**, the form the web app uses, instead of Python's `True`/`False`.
- **Walking and hiking workouts raise a clear error instead of uploading without a sport type**: Garmin has no walking or hiking workout sport type (see `get_workout_types()["workoutSportTypes"]`), so `upload_walking_workout()` and `upload_hiking_workout()` sent IDs Garmin discarded and the workout was stored with no sport type. Both now raise `ValueError`; `WalkingWorkout` and `HikingWorkout` stay importable. The demo's walking and hiking sample uploads are removed.
- **Upload errors show Garmin's message text**: a rejected upload such as a duplicate now raises `API Error 409 - Duplicate Activity.` instead of including the raw `{'code': 202, 'content': ...}` structure, and error details that are not text are left out.
- **HTTP errors keep their response**, so `get_gear_activities()` and `get_gear_stats()` return their empty result on a 404 instead of raising, and `import_activity()` reports a duplicate upload (409) as such. Thanks [@mifuha](https://github.com/mifuha)! (#470)
- **Clearer error when `curl_cffi` is missing**: login warns up front that the browser-impersonating strategies are unavailable, and the final "all login strategies exhausted" error names the missing package as the likely cause, instead of only reporting a Cloudflare 403.

## [0.3.18] - 2026-10-15

### Added

- **Jet Lag Adviser trips**: new `get_jetlag_trips()`, `add_jetlag_trip()`, `update_jetlag_trip()` and `delete_jetlag_trip()`. Tested live on a real account, including multi-leg trips in both directions, trips in the past, and a start date before the first flight. Garmin doesn't look up locations, so each place needs its UTC offset on that date (between `-12:00` and `+14:00`), and each time is the local time at that place, without an offset. (#457)
- **Activity photos**: new `get_activity_images(activity_id)` returns the photos attached to an activity as a list of `{imageId, url, photoDate}`, or `[]` when there are none. The URLs expire after 24 hours, and the `hasImages` flag in `get_activities()` results isn't a reliable sign that an activity has photos. (#454, #455)
- **Timed strength exercises and per-step notes**: new `create_strength_timed_step()` and `create_strength_timed_set()` for exercises done for time (planks, carries). Every strength helper also accepts an optional `description`, a per-step note such as a form cue. Tested live: Garmin stores the time-based steps and the descriptions as sent. (#458, #466)
- **Swim CSS offset targets**: new `SwimCssOffsetTarget(offset_seconds=...)` sets a pace target relative to your Critical Swim Speed, as the secondary target. The targeted step helpers now also accept a secondary target without a primary one. Tested live: Garmin Connect shows the step as CSS +5s. (#456)
- **Skip the last rest in a repeat**: `create_repeat_group()` takes an optional `skip_last_rest_step`, which leaves out the final rest of a repeat group. Works fully on newer watches (roughly FR955 and later). (#452)
- **Type information**: the package now ships a `py.typed` marker, so mypy and other type checkers use its annotations.
- **Python 3.14** is now tested in CI.
- **Demo**: new menu entries for jet lag trips (Hydration & Wellness), activity photos (Activities & Workouts), and sample uploads for swim CSS targets and timed strength sets. The two sample uploads read the workout back to show what Garmin stored.

### Fixed

- **IDs are no longer silently rounded down**: every method that takes an ID (activities, workouts, devices, weigh-ins, trips, training plans, golf scorecards) used to cut off anything after the decimal point, so `delete_activity(1.9)` would have deleted activity 1. Values like `1.9` and `"1.9"` are now rejected before any request is sent. Integers, `"123"` and `123.0` still work. (#465)
- **Clearer error when the API refuses a call after login**: when the test call made after login gets a 403, the "token rejected by API tier" error now notes that a 403 can mean Garmin is blocking your client or network, not rejecting your token. A 401 (an actually refused token) is unchanged. The status is also read more reliably from the error, so a server error whose text happens to mention "403" no longer counts as a rejected token. (#444, #467)
- **API error responses are no longer logged**: when an API call fails, the debug log now records only the status code, not the full response body, which could contain account or session details. (#464)
- **Token exchange errors are no longer logged**: when the login token exchange fails, the debug log records only the status code, not Garmin's error response. (#468)
- **Demo**: the HTML health report's Step Goal card now actually shows, filled from the daily summary. (#462)

### Docs

- The Authentication section now says that login uses the iOS app's client ID (`GCM_IOS_DARK`), not the Android one, and the token exchange is described as it actually happens. (#461)
- README method counts updated to 164+ across 14 categories.
- Fixed formatting in a README code example that newer ruff versions flagged, which had been failing CI. (#463)
- New `CONTRIBUTING.md` and this changelog. The login-strategy diagnostic script moved to `scripts/test_strategy.py`.

### Thanks

- [@aaronspruit](https://github.com/aaronspruit) for the Jet Lag Adviser methods (#457), tested live across every edge case Garmin accepts.
- [@cpruijsen](https://github.com/cpruijsen) for `get_activity_images()` (#455).
- [@fasoxy-it](https://github.com/fasoxy-it) for the swim CSS offset target (#456).
- [@MartinDejmal](https://github.com/MartinDejmal) for `skip_last_rest_step` (#452).
- [@danihrndzld](https://github.com/danihrndzld) for the authentication docs fix (#461) and the demo Step Goal card fix (#462).
- [@mukhtadir-syed](https://github.com/mukhtadir-syed) for the detailed, live-tested report behind the timed strength steps and per-step notes (#458).

## [0.3.17] - 2026-09-29

### ⚠️ Breaking

- `get_goals()` now counts from 1 (new default `start=1`; `start=0` returned no goals), and `start=0` raises `ValueError` there and in the badge challenge methods, where Garmin already rejected it. If you pass `start=0` to these methods, use `start=1`. (#441, #445)

### Added

- **Workout intensity targets:** interval steps can now have a pace, speed, cadence, power or heart-rate target, either as a custom range or as one of your configured zones, with an optional secondary target (e.g. power + cadence for cycling). Use `create_targeted_interval_step` / `create_targeted_distance_interval_step` with `PaceTarget`, `SpeedTarget`, `CadenceTarget`, `CustomPowerTarget`, `PowerZoneTarget`, `CustomHeartRateTarget` or `HeartRateZoneTarget`. `pace_to_mps` and `speed_to_mps` convert min/km, min/mi, km/h and mph to the m/s Garmin expects. Thanks @Silver-Saucepan! (#440, #446)
- **Training load:** `get_training_four_week_load_balance(cdate)`, `get_daily_training_status(cdate)` and `get_training_load_activities(startdate, enddate, metrics=None, activitytype=None)` for training load balance, daily training status (acute/chronic load) and per-activity training load. Thanks @brycehenson! (#437, #447)

### Fixed

- Timestamps with a timezone offset (e.g. `"2026-07-01T08:45:00+05:45"`) passed to `add_body_composition` and the other FIT-based uploads are now stored at the correct time; previously the offset was ignored and the time was treated as local time on the machine. Timestamps without an offset behave as before. Thanks @bensynapse! (#438)
- Clearer errors when upgrading from garth-based versions: `login()` now says so when it finds old garth tokens, and API calls without `login()` say to call it first. (#448)
- Login 429 errors no longer claim the IP is rate limited; Garmin can also block based on the client fingerprint. (#449)

### Demo & docs

- The running and cycling upload examples now use intensity targets: the running workout has a 4:30–4:50 min/km pace target on its intervals, and the cycling workout 220–250 W power with an 85–95 rpm cadence secondary target.
- The new training load methods are available under Advanced Health Metrics (options g, h, i).
- The README has a new "Upgrading from 0.2.x (garth)" section.

## [0.3.16] - 2026-09-18

### Added

- New menstrual-cycle write methods: `update_menstrual_daily_log()`, `update_menstrual_calendar()`, `init_menstrual_cycle_setup()`, `confirm_menstrual_period_start()`, and `update_menstrual_settings()` — previously only reads (dayview/calendar/pregnancy snapshots) were supported; recording a daily log, editing period dates, running first-time cycle setup, or changing tracking settings required going through Garmin Connect's own UI. Payload shapes were checked against live requests where practical; `init_menstrual_cycle_setup()`/`confirm_menstrual_period_start()` request shapes come from the frontend and haven't been exercised live on an already-configured account, so treat those two with extra care. Writes are full snapshots, not field-level merges — see each method's docstring for exactly what gets cleared vs. preserved when a field is omitted.
- New read methods alongside the writes: `get_menstrual_last_confirmed()`, `get_menstrual_cycle_summary()`, `get_menstrual_reports()`.
- `demo.py`: interactive menu entries for all of the above (Hydration & Wellness category), consistent with every other write in the demo — no extra confirmation step beyond the normal input prompts.

### Fixed

- `get_goals()` silently returned `[]` (HTTP 200, no error) for newer goal types — custom accumulation goals with a date range, created via the current Garmin Connect UI. Root cause: `goal-service/goal/goals` requires a `Sec-Fetch-Site: same-origin` header for these goal types; browsers always send it on a same-origin request, but this client didn't send any `Sec-Fetch-*` headers before. (#431, #434)
- `update_menstrual_settings()` could clobber fields the caller didn't pass — it now GETs the current profile and merges the caller's keys onto the existing `userMenstrualCycleSettings` before the PUT, so omitted tracking flags are preserved.
- Two formatting-only nits from the menstrual-writes change (an unnecessary line wrap in a demo error message and in `get_menstrual_reports()`'s URL construction).

### Docs

- README method/category counts updated to 154+ across 14 categories (Hydration & Wellness now 20 methods, up from 12).

### Thanks

- [@TSHOGX](https://github.com/TSHOGX) for the menstrual-cycle write methods (#432) — payload shapes checked against live requests, not guessed.
- [@skweeker](https://github.com/skweeker) for reporting the `get_goals()` regression (#431) and isolating the root cause via curl — narrowing it down to one missing header made the fix straightforward.

## [0.3.15] - 2026-09-12

### Fixed

- Bumped version number in `pyproject.toml` file

## [0.3.14] - 2026-09-12

### Fixed

- `daily_sleep.avg_respiration_value` was aliased to the wrong API field (`avgRespirationValue`, which never matches a real response) — corrected to `averageRespirationValue`, so this field now actually populates instead of always being `None`. `lowestRespirationValue`/`highestRespirationValue` were already correct. (#427)
- `set_blood_pressure()`'s `pulse` parameter is now optional (`int | None = None`) — Garmin Connect's own UI allows saving a blood-pressure entry without a heart-rate value, but the library required one. When omitted, `pulse` is left out of the outgoing payload entirely rather than sent as a placeholder. (#426, #428)
- `demo.py`'s local blood-pressure range checks (systolic/diastolic/pulse) didn't match `set_blood_pressure()`'s own validation ranges, so a value the demo accepted could still be rejected by the API, and vice versa. All three ranges now match the library exactly (systolic 70-260, diastolic 40-150, pulse 20-250).
- `demo.py`'s category-menu key dispatch checked the pressed key against a hardcoded whitelist string *before* checking the real menu — any new uppercase option key (most recently `[B]` for the new "next scheduled workout" option) silently became unreachable, printing "Invalid selection" even though it was a real, listed menu entry. The whitelist is gone; the existing options-dict lookup right below it is now the sole (and already-correct) source of truth, so this class of bug can't recur.

### Added

- New `get_next_scheduled_workout()` — returns the earliest upcoming calendar-service workout (today or later), checking the current and next calendar month, since `get_scheduled_workouts(year, month)` already required callers to fetch and merge two months manually for a sensible "what's next" view. **Known limitation**: this only sees whatever Garmin's `calendar-service` endpoint has already committed to the visible calendar — for adaptive/Coach training plans, the Garmin Connect app can show upcoming sessions this endpoint doesn't return at all (confirmed live against a real account with an active Coach plan). That fuller view lives behind a different, session-cookie-authenticated API this client doesn't use. Documented on the method. (#429)
- `demo.py`: new interactive menu option `[B]` for `get_next_scheduled_workout()`.

### Docs

- README's "Total API Methods" wording corrected from "unique endpoints" to "methods" — `get_next_scheduled_workout()` composes two calls to the existing `get_scheduled_workouts` endpoint rather than adding a new remote endpoint. Method/category counts updated to 146+ across 14 categories.

## [0.3.13] - 2026-09-09

### Added

- `get_activities()` now accepts an `activitysubtype` filter (e.g. `activitytype="fitness_equipment"`, `activitysubtype="strength_training"`) for narrower activity searches. (#419)
- New `create_gear()` method to register a new piece of gear (e.g. a pair of shoes) directly via the API — previously only linking/unlinking *existing* gear was possible. (#418, #424)
- `get_personal_record()`'s docstring now documents the running `typeId` schema (1 km / 1 mile / 5 km / 10 km / half marathon / marathon / longest run) and what `value` means for each. (#423)

### Fixed

- `resume_login()` after a token-store login no longer permanently loses `display_name` on an incomplete/transient profile fetch — the fetch is retried, and the documented fallback behavior for genuinely new/empty accounts (no display name configured) is preserved. Previously this silently broke every endpoint that needs a display name (`get_rhr_day`, `get_sleep_data`, `get_personal_record`, etc.) for the rest of the client's lifetime. (#421, #422)
- `get_activities()` response handling normalized so a dict-shaped response (`{"activityList": [...]}`) is handled the same as a plain list. (#419 follow-up)
- `create_gear()` rejects non-finite (`inf`/`nan`) and sub-unit usage-limit values instead of raising an uncaught `OverflowError` or silently rounding to 0 (which collides with the "no threshold" sentinel), and rejects a non-list `activity_type_keys` instead of silently iterating it character-by-character.

### Demo (`demo.py`)

- New interactive menu option to create gear, prompting for type/brand/model/usage tracking/activity associations.
- New interactive activity type/subtype filter picker — pulls the live type list from `api.get_activity_types()` instead of requiring a config edit.
- "Get personal records" now decodes and formats values instead of dumping raw numbers: running records show as times (`m:ss`/`h:mm:ss`) or distance (`km`), and step-count/goal-streak records (most steps in a day/week/month, longest/current goal streak) are now decoded too — all confirmed against a real account. Anything outside the confirmed set is still shown in full (never hidden), just unlabeled.
- Lets you look up a personal record's source activity (needed for longest-run duration, which isn't in the record entry itself).

### Docs

- README's API coverage stats corrected — was significantly stale (missing an entire "Activity Editing" category, wrong Training Plans count); now 145+ methods across 14 categories, recomputed directly from `demo.py`.

## [0.3.12] - 2026-08-22

### Fixed

- `resume_login()` no longer discards the pending MFA session when a submitted code is wrong or the verification attempt is rate-limited, you can now retry with the correct code on the same client instead of the retry failing unconditionally. (#416)

## [0.3.11] - 2026-08-19

### Added

- Added `download_health_snapshot(requested_date)`, which downloads the Health Snapshot ZIP for a given calendar date — data not included in the regular activity/wellness export. (#415 by @LyzardKing)
- Wired into `demo.py` under System & Export ("Download Health Snapshot ZIP for today").

### Security

**Token storage**
- Token writes now use an unpredictable temp filename with exclusive (`O_EXCL`) creation instead of a fixed sibling name opened with `O_TRUNC`. Previously, a file pre-planted at the predictable temp path had its inode reused during the write, letting an attacker holding a read descriptor on it observe token contents as they were written.
- `login()` no longer calls `.resolve()` on the tokenstore path before validation. Resolving followed symlinks and substituted the target path before the ancestry symlink check ever ran, letting a pre-planted tokenstore symlink bypass that check entirely — potentially causing a victim to silently adopt an attacker-seeded token file or write fresh tokens into an attacker-controlled directory.

## [0.3.10] - 2026-08-11

This release is primarily a security-hardening pass covering authentication, token storage, and request handling.

### Security

**Token storage & session**
- Reject symlinked tokenstore paths, including intermediate directories anywhere in the path's ancestry and `~username` expansion — closes several local-attacker vectors that could redirect token read/write/delete to an attacker-controlled location.
- Token refresh and writes are now serialized with a lock and written atomically, preventing corrupted or raced token files.
- `logout()` now fully clears session cookies, MFA state, and wrapper fields instead of leaving stale credentials behind.
- Plaintext password is cleared from memory after a successful login.

**Authentication flow**
- `login()` clears stale auth state on entry, so a failed or partial login can no longer leave a mismatched token active.
- Two-step MFA (`resume_login`) now verifies the resulting token and fails closed instead of silently succeeding with a broken session.
- Interleaved MFA logins on a shared client instance no longer corrupt each other's pending state.
- JWT handling rejects unsigned (`alg: none`) tokens and malformed/adversarial `exp` claims that could otherwise crash every subsequent API call.

**Request & URL handling**
- All identifier-bearing API methods now validate their inputs (positive integers, UUIDs, sport keys, dates) before building request URLs, closing several path-traversal and query-injection gaps.
- The request-path guard now correctly decodes percent-encoded paths before validating them, and no longer misfires on legitimate encoded characters.
- `domain=` is now checked against an allowlist of official Garmin domains, preventing credential exfiltration via a malicious value.

**Reliability / DoS**
- Pagination in `get_activities_by_date` / `get_goals` is now capped, so a misbehaving or hostile server can no longer hang the client or exhaust memory.
- A 401 during upload retry now rewinds the file body correctly instead of silently re-uploading an empty or truncated file.

**Logging & data hygiene**
- Exception messages and debug logs no longer include raw server response bodies, CAS service tickets, or token contents.
- Hardened the VCR cassette sanitizer (JSON bodies, MFA codes, tickets) and the exercise-catalog generator script against recording or publishing session/account data.

[0.3.18]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.18
[0.3.17]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.17
[0.3.16]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.16
[0.3.15]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.15
[0.3.14]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.14
[0.3.13]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.13
[0.3.12]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.12
[0.3.11]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.11
[0.3.10]: https://github.com/cyberjunky/python-garminconnect/releases/tag/0.3.10
