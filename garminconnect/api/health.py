"""Daily health and wellness data: summaries, sleep, heart rate, stress, hydration, nutrition, Health Snapshot, ECG, jet lag."""

import math
import numbers
import re
from datetime import datetime, timedelta
from typing import Any

from ..exceptions import GarminConnectAuthenticationError, GarminConnectConnectionError
from ._common import (
    DATE_FORMAT_STR,
    MAX_HYDRATION_ML,
    VALID_DAILY_STATS_TYPES,
    _coerce_positive_id,
    _fmt_ts,
    _validate_date_format,
    _validate_date_range,
    _validate_jetlag_flights,
    _validate_non_negative_integer,
    _validate_positive_integer,
    _validate_uuid,
    logger,
)
from .base import GarminBase


class HealthMixin(GarminBase):
    """Daily health and wellness data: summaries, sleep, heart rate, stress, hydration, nutrition, Health Snapshot, ECG, jet lag."""

    def get_stats(self, cdate: str) -> dict[str, Any]:
        """Return the daily summary for 'cdate' format 'YYYY-MM-DD' (same as `get_user_summary`)."""
        # Validate input
        cdate = _validate_date_format(cdate, "cdate")
        return self.get_user_summary(cdate)

    def get_user_summary(self, cdate: str) -> dict[str, Any]:
        """Return user activity summary for 'cdate' format 'YYYY-MM-DD'.

        Args:
            cdate: The date to fetch the summary for.

        Returns:
            Dictionary containing the user activity summary.

        """
        # Validate input
        cdate = _validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_daily_summary_url}/{self._require_display_name()}"
        params = {"calendarDate": cdate}
        logger.debug("Requesting user summary")

        response = self.connectapi(url, params=params)

        if not response:
            raise GarminConnectConnectionError("No data received from server")

        if response.get("privacyProtected") is True:
            raise GarminConnectAuthenticationError("Authentication error")

        return response

    def get_steps_data(self, cdate: str) -> list[dict[str, Any]]:
        """Fetch available steps data 'cDate' format 'YYYY-MM-DD'."""
        # Validate input
        cdate = _validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_user_summary_chart}/{self._require_display_name()}"
        params = {"date": cdate}
        logger.debug("Requesting steps data")

        response = self.connectapi(url, params=params)

        if response is None:
            logger.warning("No steps data received")
            return []

        return response

    def get_floors(self, cdate: str) -> dict[str, Any]:
        """Fetch available floors data 'cDate' format 'YYYY-MM-DD'."""
        # Validate input
        cdate = _validate_date_format(cdate, "cdate")

        url = f"{self.garmin_connect_floors_chart_daily_url}/{cdate}"
        logger.debug("Requesting floors data")

        response = self.connectapi(url)

        if response is None:
            raise GarminConnectConnectionError("No floors data received")

        return response

    def get_daily_steps(self, start: str, end: str) -> list[dict[str, Any]]:
        """Fetch available steps data 'start' and 'end' format 'YYYY-MM-DD'.

        Note: The Garmin Connect API has a 28-day limit per request. For date ranges
        exceeding 28 days, this method automatically splits the range into chunks
        and makes multiple API calls, then merges the results.
        """
        # Validate inputs
        start = _validate_date_format(start, "start")
        end = _validate_date_format(end, "end")

        # Validate date range
        start_date = datetime.strptime(start, DATE_FORMAT_STR).date()
        end_date = datetime.strptime(end, DATE_FORMAT_STR).date()

        if start_date > end_date:
            raise ValueError("start date cannot be after end date")

        # Calculate date range (inclusive)
        days_diff = (end_date - start_date).days + 1

        # If range is 28 days or less, make single request
        if days_diff <= 28:
            url = f"{self.garmin_connect_daily_stats_steps_url}/{start}/{end}"
            logger.debug("Requesting daily steps data")
            return self.connectapi(url)

        # For ranges > 28 days, split into chunks
        logger.debug(
            f"Date range ({days_diff} days) exceeds 28-day limit, chunking requests"
        )
        all_results = []
        current_start = start_date

        while current_start <= end_date:
            # Calculate chunk end (max 28 days from current_start)
            chunk_end = min(current_start + timedelta(days=27), end_date)
            chunk_start_str = current_start.isoformat()
            chunk_end_str = chunk_end.isoformat()

            url = (
                f"{self.garmin_connect_daily_stats_steps_url}/"
                f"{chunk_start_str}/{chunk_end_str}"
            )
            logger.debug(
                f"Requesting daily steps data for chunk: "
                f"{chunk_start_str} to {chunk_end_str}"
            )

            chunk_results = self.connectapi(url)
            if chunk_results:
                all_results.extend(chunk_results)

            # Move to next chunk
            current_start = chunk_end + timedelta(days=1)

        return all_results

    def get_weekly_steps(self, end: str, weeks: int = 52) -> list[dict[str, Any]]:
        """Fetch weekly steps aggregates.

        Args:
            end: End date string in format 'YYYY-MM-DD'
            weeks: Number of weeks to fetch (default 52 = 1 year)

        Returns:
            List of weekly step aggregates containing:
            - totalSteps: Total steps for the week
            - averageSteps: Average daily steps
            - totalDistance: Total distance in meters
            - averageDistance: Average daily distance
            - wellnessDataDaysCount: Days with data

        """
        end = _validate_date_format(end, "end")
        weeks = _validate_positive_integer(weeks, "weeks")

        url = f"{self.garmin_connect_weekly_stats_steps_url}/{end}/{weeks}"
        logger.debug("Requesting weekly steps data for %d weeks ending %s", weeks, end)

        return self.connectapi(url)

    def get_weekly_stress(self, end: str, weeks: int = 52) -> list[dict[str, Any]]:
        """Fetch weekly stress aggregates.

        Args:
            end: End date string in format 'YYYY-MM-DD'
            weeks: Number of weeks to fetch (default 52 = 1 year)

        Returns:
            List of weekly stress aggregates containing:
            - value: Overall stress value for the week
            - calendarDate: Week start date

        """
        end = _validate_date_format(end, "end")
        weeks = _validate_positive_integer(weeks, "weeks")

        url = f"{self.garmin_connect_weekly_stats_stress_url}/{end}/{weeks}"
        logger.debug("Requesting weekly stress data for %d weeks ending %s", weeks, end)

        return self.connectapi(url)

    def get_weekly_intensity_minutes(
        self, start: str, end: str
    ) -> list[dict[str, Any]]:
        """Fetch weekly intensity minutes aggregates.

        Args:
            start: Start date string in format 'YYYY-MM-DD'
            end: End date string in format 'YYYY-MM-DD'

        Returns:
            List of weekly intensity minute aggregates containing:
            - weeklyGoal: Weekly intensity minutes goal
            - moderateValue: Moderate intensity minutes
            - vigorousValue: Vigorous intensity minutes
            - calendarDate: Week start date

        """
        start = _validate_date_format(start, "start")
        end = _validate_date_format(end, "end")

        url = f"{self.garmin_connect_weekly_stats_intensity_minutes_url}/{start}/{end}"
        logger.debug("Requesting weekly intensity minutes from %s to %s", start, end)

        return self.connectapi(url)

    def get_heart_rates(self, cdate: str) -> dict[str, Any]:
        """Fetch available heart rates data 'cDate' format 'YYYY-MM-DD'.

        Args:
            cdate: Date string in format 'YYYY-MM-DD'

        Returns:
            Dictionary containing heart rate data for the specified date

        Raises:
            ValueError: If cdate format is invalid
            GarminConnectConnectionError: If no data received
            GarminConnectAuthenticationError: If authentication fails

        """
        # Validate input
        cdate = _validate_date_format(cdate, "cdate")

        url = (
            f"{self.garmin_connect_heartrates_daily_url}/{self._require_display_name()}"
        )
        params = {"date": cdate}
        logger.debug("Requesting heart rates")

        response = self.connectapi(url, params=params)

        if response is None:
            raise GarminConnectConnectionError("No heart rate data received")

        return response

    def get_body_battery(
        self, startdate: str, enddate: str | None = None
    ) -> list[dict[str, Any]]:
        """Return body battery values by day for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'.
        """
        startdate = _validate_date_format(startdate, "startdate")
        if enddate is None:
            enddate = startdate
        else:
            enddate = _validate_date_format(enddate, "enddate")
        url = self.garmin_connect_daily_body_battery_url
        params = {"startDate": startdate, "endDate": enddate}
        logger.debug("Requesting body battery data")

        return self.connectapi(url, params=params)

    def get_body_battery_events(self, cdate: str) -> list[dict[str, Any]]:
        """Return body battery events for date 'cdate' format 'YYYY-MM-DD'.
        The return value is a list of dictionaries, where each dictionary contains event data for a specific event.
        Events can include sleep, recorded activities, auto-detected activities, and naps.
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_body_battery_events_url}/{cdate}"
        logger.debug("Requesting body battery event data")

        return self.connectapi(url)

    def add_hydration_data(
        self,
        value_in_ml: float,
        timestamp: str | None = None,
        cdate: str | None = None,
    ) -> dict[str, Any]:
        """Log a hydration intake in ml (negative values subtract).  Defaults to current date and current timestamp if left empty
        :param float required - value_in_ml: The number of ml of water you wish to add (positive) or subtract (negative)
        :param timestamp optional - timestamp: The timestamp of the hydration update, format 'YYYY-MM-DDThh:mm:ss.ms' Defaults to current timestamp
        :param date optional - cdate: The date of the weigh in, format 'YYYY-MM-DD'. Defaults to current date.
        """
        # Validate inputs
        if isinstance(value_in_ml, bool) or not isinstance(value_in_ml, numbers.Real):
            raise ValueError("value_in_ml must be a number")
        value_in_ml = float(value_in_ml)
        if not math.isfinite(value_in_ml):
            raise ValueError("value_in_ml must be a finite number")

        # Allow negative values for subtraction but validate reasonable range
        if abs(value_in_ml) > MAX_HYDRATION_ML:
            raise ValueError(
                f"value_in_ml seems unreasonably high (>{MAX_HYDRATION_ML}ml)"
            )

        url = self.garmin_connect_set_hydration_url

        if timestamp is None and cdate is None:
            # If both are null, use today and now in the user's Garmin timezone
            raw_ts = self.now()
            cdate = raw_ts.date().isoformat()
            timestamp = _fmt_ts(raw_ts)

        elif cdate is not None and timestamp is None:
            # If cdate is provided, validate and use midnight local time
            cdate = _validate_date_format(cdate, "cdate")
            raw_ts = datetime.strptime(cdate, DATE_FORMAT_STR)  # midnight local
            timestamp = _fmt_ts(raw_ts)

        elif cdate is None and timestamp is not None:
            # If timestamp is provided, normalize and set cdate to its date part
            if not isinstance(timestamp, str):
                raise ValueError("timestamp must be a string")
            try:
                try:
                    raw_ts = datetime.fromisoformat(timestamp)
                except ValueError:
                    raw_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                cdate = raw_ts.date().isoformat()
                timestamp = _fmt_ts(raw_ts)
            except ValueError as e:
                raise ValueError("invalid timestamp format (expected ISO 8601)") from e
        else:
            # Both provided - validate consistency and normalize
            if not isinstance(cdate, str):
                raise ValueError("cdate must be a string")
            cdate = _validate_date_format(cdate, "cdate")
            if not isinstance(timestamp, str):
                raise ValueError("timestamp must be a string")
            try:
                try:
                    raw_ts = datetime.fromisoformat(timestamp)
                except ValueError:
                    raw_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                ts_date = raw_ts.date().isoformat()
                if ts_date != cdate:
                    raise ValueError(
                        f"timestamp date ({ts_date}) doesn't match cdate ({cdate})"
                    )
                timestamp = _fmt_ts(raw_ts)
            except ValueError:
                raise

        payload: dict[str, Any] = {
            "calendarDate": cdate,
            "timestampLocal": timestamp,
            "valueInML": value_in_ml,
        }
        if self.profile_id is not None:
            # The web app includes the profile id in the hydration log entry.
            payload["userProfileId"] = self.profile_id

        logger.debug("Adding hydration data")
        return self.client.put("connectapi", url, json=payload).json()

    def get_hydration_data(self, cdate: str) -> dict[str, Any]:
        """Return available hydration data 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_hydration_url}/{cdate}"
        logger.debug("Requesting hydration data")

        return self.connectapi(url)

    def get_respiration_data(self, cdate: str) -> dict[str, Any]:
        """Return available respiration data 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_respiration_url}/{cdate}"
        logger.debug("Requesting respiration data")

        return self.connectapi(url)

    def get_spo2_data(self, cdate: str) -> dict[str, Any]:
        """Return available SpO2 data 'cdate' format 'YYYY-MM-DD'.

        The API occasionally returns ``lastSevenDaysAvgSpO2`` as a string; it is
        converted to ``float`` when that happens so the field is consistent with
        the other numeric SpO2 values.
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_spo2_url}/{cdate}"
        logger.debug("Requesting SpO2 data")

        data = self.connectapi(url)
        if isinstance(data, dict):
            value = data.get("lastSevenDaysAvgSpO2")
            if isinstance(value, str):
                data["lastSevenDaysAvgSpO2"] = float(value)
        return data

    def get_intensity_minutes_data(self, cdate: str) -> dict[str, Any]:
        """Return available Intensity Minutes data 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_intensity_minutes}/{cdate}"
        logger.debug("Requesting Intensity Minutes data")

        return self.connectapi(url)

    def get_all_day_stress(self, cdate: str) -> dict[str, Any]:
        """Return available all day stress data 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_stress_url}/{cdate}"
        logger.debug("Requesting all day stress data")

        return self.connectapi(url)

    def get_all_day_events(self, cdate: str) -> dict[str, Any]:
        """Return available daily events data 'cdate' format 'YYYY-MM-DD'.
        Includes autodetected activities, even if not recorded on the watch.
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = self.garmin_daily_events_url
        logger.debug("Requesting all day events data")

        return self.connectapi(url, params={"calendarDate": cdate})

    def get_sleep_data(self, cdate: str) -> dict[str, Any]:
        """Return sleep data for 'cdate' format 'YYYY-MM-DD'.

        The response is passed through exactly as Garmin returns it. Some users
        (notably China/UTC+8 accounts on connect.garmin.cn) have reported that
        ``sleepStartTimestampLocal`` / ``sleepEndTimestampLocal`` can be offset
        by the local timezone twice. When in doubt, use the ``*GMT`` fields and
        convert to local time yourself.
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_sleep_url}/{self._require_display_name()}"
        params = {"date": cdate, "nonSleepBufferMinutes": 60}
        logger.debug("Requesting sleep data")

        return self.connectapi(url, params=params)

    def get_sleep_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        """Fetch daily sleep summaries for 'start' and 'end' format 'YYYY-MM-DD'.

        Note: The Garmin Connect sleep-stats endpoint has a 28-day limit per
        request. For date ranges exceeding 28 days, this method automatically
        splits the range into chunks and makes multiple API calls, then merges
        the results, de-duplicating by calendar date.
        """
        start, end = _validate_date_range(start, end)
        start_date = datetime.strptime(start, DATE_FORMAT_STR).date()
        end_date = datetime.strptime(end, DATE_FORMAT_STR).date()

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        current_start = start_date

        while current_start <= end_date:
            chunk_end = min(current_start + timedelta(days=27), end_date)
            url = (
                "/sleep-service/stats/sleep/daily/"
                f"{current_start.isoformat()}/{chunk_end.isoformat()}"
            )
            logger.debug(
                f"Requesting daily sleep data for chunk: "
                f"{current_start.isoformat()} to {chunk_end.isoformat()}"
            )
            data = self.connectapi(url)
            for row in (data or {}).get("individualStats") or []:
                cal_date = row.get("calendarDate")
                if cal_date and cal_date not in seen:
                    seen.add(cal_date)
                    results.append(row)

            current_start = chunk_end + timedelta(days=1)

        results.sort(key=lambda r: r.get("calendarDate") or "")
        return results

    def get_stress_data(self, cdate: str) -> dict[str, Any]:
        """Return stress data for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_stress_url}/{cdate}"
        logger.debug("Requesting stress data")

        return self.connectapi(url)

    def get_lifestyle_logging_data(self, cdate: str) -> dict[str, Any]:
        """Return lifestyle logging data for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_lifestyle_logging_url}/{cdate}"
        logger.debug("Requesting lifestyle logging data")

        return self.connectapi(url)

    def get_rhr_day(self, cdate: str) -> dict[str, Any]:
        """Return resting heart rate data for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_rhr_url}/{self._require_display_name()}"
        params = {
            "fromDate": cdate,
            "untilDate": cdate,
            "metricId": 60,
        }
        logger.debug("Requesting resting heartrate data")

        return self.connectapi(url, params=params)

    def get_rhr_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return daily resting heart rate for a date range ('start'/'end' format 'YYYY-MM-DD').

        Unlike `get_rhr_day`, which is limited to a single day, this queries
        the same wellness-stats endpoint with distinct fromDate/untilDate to
        fetch a range (up to ~1 year) in a single request.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_rhr_url}/{self._require_display_name()}"
        params = {
            "fromDate": start,
            "untilDate": end,
            "metricId": 60,
        }
        logger.debug("Requesting resting heartrate data range")

        data = self.connectapi(url, params=params)
        rows = ((data or {}).get("allMetrics") or {}).get("metricsMap", {}).get(
            "WELLNESS_RESTING_HEART_RATE"
        ) or []
        return [
            {"calendarDate": row.get("calendarDate"), "value": row.get("value")}
            for row in rows
            if row.get("value") is not None
        ]

    def get_calories_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return daily active + resting (BMR) calories for a date range.

        'start'/'end' format 'YYYY-MM-DD'. Uses the same wellness-stats
        endpoint as `get_rhr_daily` (metric IDs 22 = active calories, 23 = BMR
        calories) to fetch both series for the range in a single request.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_rhr_url}/{self._require_display_name()}"
        params = {
            "fromDate": start,
            "untilDate": end,
            "metricId": [22, 23],
        }
        logger.debug("Requesting daily calories data range")

        data = self.connectapi(url, params=params)
        metrics = ((data or {}).get("allMetrics") or {}).get("metricsMap", {})

        def _by_date(key: str) -> dict[str, float]:
            return {
                row.get("calendarDate"): row.get("value")
                for row in (metrics.get(key) or [])
                if row.get("calendarDate") is not None and row.get("value") is not None
            }

        active = _by_date("WELLNESS_ACTIVE_CALORIES")
        resting = _by_date("WELLNESS_BMR_CALORIES")
        results: list[dict[str, Any]] = []
        for cal_date in sorted(set(active) | set(resting)):
            a = active.get(cal_date)
            r = resting.get(cal_date)
            if a is None and r is None:
                continue
            results.append(
                {
                    "calendarDate": cal_date,
                    "active": a,
                    "resting": r,
                    "total": (a or 0) + (r or 0),
                }
            )
        return results

    def get_hrv_data(self, cdate: str) -> dict[str, Any] | None:
        """Return HRV (Heart Rate Variability) data for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_hrv_url}/{cdate}"
        logger.debug("Requesting Heart Rate Variability (hrv) data")

        return self.connectapi(url)

    def get_hrv_data_range(self, start: str, end: str) -> dict[str, Any] | None:
        """Return HRV (Heart Rate Variability) data for a date range.

        'start'/'end' format 'YYYY-MM-DD'. Unlike `get_hrv_data`, which is
        limited to a single day, this queries the same endpoint with distinct
        start/end dates to fetch a range in one request.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_hrv_url}/daily/{start}/{end}"
        logger.debug("Requesting Heart Rate Variability (hrv) data range")

        return self.connectapi(url)

    def download_health_snapshot(self, requested_date: str) -> bytes:
        """Download the Health Snapshot ZIP file for a calendar date."""
        requested_date = _validate_date_format(requested_date, "requested_date")
        url = f"{self.garmin_connect_health_snapshot_download}/{requested_date}"

        logger.debug("Downloading Health Snapshot from %s", url)

        return self.download(url)

    def get_jetlag_trips(self) -> list[dict[str, Any]]:
        """Return all Jet Lag Adviser trips, each with its flights."""
        url = f"{self.garmin_connect_jetlag_trip_url}/all"
        logger.debug("Requesting jet lag trips")
        return self.connectapi(url)

    def _jetlag_trip_payload(
        self, start_date: str, end_date: str, flights: list[dict[str, Any]]
    ) -> dict[str, Any]:
        start_date, end_date = _validate_date_range(start_date, end_date)
        payload: dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "flights": _validate_jetlag_flights(flights),
        }
        if self.profile_id is not None:
            payload["userId"] = self.profile_id
        return payload

    def add_jetlag_trip(
        self, start_date: str, end_date: str, flights: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Create a Jet Lag Adviser trip.

        Each flight is a dict with ``originLocation``, ``originTimezone`` and
        ``originTimestamp``, and the same three ``destination*`` keys. A
        location is free text. A timezone is the UTC offset at that place on
        that date, such as ``"-07:00"``. A timestamp is the local time at that
        place without an offset, such as ``"2026-10-04T15:20:00.00"``. Garmin
        does not geocode the location, so the offset must be correct.

        Each flight is one leg, so a connection is two flights (PDX to MSP,
        then MSP to ATL). Garmin does not check that the legs connect or
        that a leg changes timezone. It also accepts dates in the past and a
        ``start_date`` before the first flight, which the web page does not
        allow. The web page names a trip after its first flight only, and
        shows the first departure to the last arrival. Garmin deletes a trip
        by itself after the trip ends and the user has adjusted to the home
        timezone. Garmin can refuse a trip whose dates overlap an existing
        trip, with HTTP 400 "A trip already exists for this date range".

        Returns the trip with its new ``tripId`` and a ``flightId`` on each
        flight. ``dailyStatus``, the guidance that Garmin calculates, is not
        in this response. It appears in :meth:`get_jetlag_trips` only after
        travel starts.
        """
        payload = self._jetlag_trip_payload(start_date, end_date, flights)
        logger.debug("Creating jet lag trip %s to %s", start_date, end_date)
        return self.client.post(
            "connectapi", self.garmin_connect_jetlag_trip_url, json=payload, api=True
        )

    def update_jetlag_trip(
        self,
        trip_id: int | str,
        start_date: str,
        end_date: str,
        flights: list[dict[str, Any]],
    ) -> Any:
        """Replace a Jet Lag Adviser trip.

        The PUT replaces the whole trip, so ``flights`` must hold every flight,
        in the format of :meth:`add_jetlag_trip`. Keep the ``flightId`` from
        :meth:`get_jetlag_trips` on each flight that stays. ``tripId`` is set
        to ``trip_id`` on the trip and on each flight. Garmin answers with an
        empty body.
        """
        trip_id = _coerce_positive_id(trip_id, "trip_id")
        payload = self._jetlag_trip_payload(start_date, end_date, flights)
        payload["tripId"] = trip_id
        payload["flights"] = [
            flight | {"tripId": trip_id} for flight in payload["flights"]
        ]
        logger.debug("Updating jet lag trip %s", trip_id)
        return self.client.put(
            "connectapi", self.garmin_connect_jetlag_trip_url, json=payload, api=True
        )

    def delete_jetlag_trip(self, trip_id: int | str) -> Any:
        """Delete a Jet Lag Adviser trip. Garmin answers with an empty body."""
        trip_id = _coerce_positive_id(trip_id, "trip_id")
        url = f"{self.garmin_connect_jetlag_trip_url}/{trip_id}"
        logger.debug("Deleting jet lag trip %s", trip_id)
        return self.client.delete("connectapi", url, api=True)

    def get_daily_stats(
        self,
        start: str,
        end: str,
        stats_type: str = "STEPS",
        current_date: str | None = None,
        aggregated: bool = False,
    ) -> dict[str, Any]:
        """Return a daily series of steps, pushes or calories with aggregations.

        GET /usersummary-service/stats/daily[/aggregated]/{start}/{end}
        ?statsType=STEPS|PUSHES|CALORIES&currentDate= — the endpoint the web
        app's reports use (the older ``stats/steps/daily`` behind
        ``get_daily_steps`` still works too). Returns ``{"values": [...],
        "aggregations": {...}}``.
        """
        start, end = _validate_date_range(start, end)
        stats_type = stats_type.strip().upper()
        if stats_type not in VALID_DAILY_STATS_TYPES:
            raise ValueError(
                f"stats_type must be one of {sorted(VALID_DAILY_STATS_TYPES)}"
            )
        current_date = self._date_or_today(current_date, "current_date")
        path = "daily/aggregated" if aggregated else "daily"
        url = f"{self.garmin_connect_usersummary_stats_url}/{path}/{start}/{end}"
        params = {"statsType": stats_type, "currentDate": current_date}
        logger.debug("Requesting daily %s stats", stats_type)
        return self.connectapi(url, params=params)

    def _usersummary_daily_series(self, series: str, start: str, end: str) -> Any:
        start, end = _validate_date_range(start, end)
        url = (
            f"{self.garmin_connect_usersummary_stats_url}/{series}/daily/{start}/{end}"
        )
        logger.debug("Requesting daily %s stats", series)
        return self.connectapi(url)

    def _usersummary_weekly_series(
        self, series: str, end: str | None, weeks: int
    ) -> Any:
        end = self._date_or_today(end, "end")
        weeks = _validate_positive_integer(weeks, "weeks")
        url = (
            f"{self.garmin_connect_usersummary_stats_url}/{series}/weekly/{end}/{weeks}"
        )
        logger.debug("Requesting weekly %s stats", series)
        return self.connectapi(url)

    def get_daily_heart_rate_stats(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return resting / min / max heart rate per day.

        GET /usersummary-service/stats/heartRate/daily/{start}/{end}.
        """
        return self._usersummary_daily_series("heartRate", start, end)

    def get_weekly_heart_rate_stats(
        self, end: str | None = None, weeks: int = 52
    ) -> list[dict[str, Any]]:
        """Return weekly heart rate averages (incl. abnormal HR alert counts).

        GET /usersummary-service/stats/heartRate/weekly/{end}/{weeks}.
        """
        return self._usersummary_weekly_series("heartRate", end, weeks)

    def get_daily_stress_stats(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return overall stress level and stress durations per day.

        GET /usersummary-service/stats/stress/daily/{start}/{end}.
        """
        return self._usersummary_daily_series("stress", start, end)

    def get_daily_body_battery_stats(
        self, start: str, end: str
    ) -> list[dict[str, Any]]:
        """Return the daily Body Battery low/high values.

        GET /usersummary-service/stats/bodybattery/daily/{start}/{end}.
        """
        return self._usersummary_daily_series("bodybattery", start, end)

    def get_daily_intensity_minutes_stats(
        self, start: str, end: str
    ) -> list[dict[str, Any]]:
        """Return moderate/vigorous intensity minutes per day with the weekly goal.

        GET /usersummary-service/stats/im/daily/{start}/{end}.
        """
        return self._usersummary_daily_series("im", start, end)

    def get_daily_respiration_stats(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return average waking and sleeping respiration per day.

        GET /usersummary-service/stats/respiration/daily/{start}/{end}.
        """
        return self._usersummary_daily_series("respiration", start, end)

    def get_daily_floors_stats(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return floors ascended/descended and the floors goal per day.

        GET /usersummary-service/stats/floors/daily/{start}/{end}.
        """
        return self._usersummary_daily_series("floors", start, end)

    def get_weekly_floors_stats(
        self, end: str | None = None, weeks: int = 52
    ) -> list[dict[str, Any]]:
        """Return weekly floors totals.

        GET /usersummary-service/stats/floors/weekly/{end}/{weeks}.
        """
        return self._usersummary_weekly_series("floors", end, weeks)

    def get_daily_hydration_stats(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return hydration intake per day.

        GET /usersummary-service/stats/hydration/daily/{start}/{end}.
        """
        return self._usersummary_daily_series("hydration", start, end)

    def get_weekly_hydration_stats(
        self, end: str | None = None, weeks: int = 52
    ) -> list[dict[str, Any]]:
        """Return weekly hydration totals.

        GET /usersummary-service/stats/hydration/weekly/{end}/{weeks}.
        """
        return self._usersummary_weekly_series("hydration", end, weeks)

    def get_weekly_calories_stats(
        self, end: str | None = None, weeks: int = 52
    ) -> list[dict[str, Any]]:
        """Return weekly resting/active/total calories.

        GET /usersummary-service/stats/calories/weekly/{end}/{weeks}.
        """
        return self._usersummary_weekly_series("calories", end, weeks)

    def get_monthly_steps(
        self, end: str | None = None, months: int = 12
    ) -> list[dict[str, Any]]:
        """Return monthly step totals for ``months`` months ending at ``end``.

        GET /usersummary-service/stats/steps/monthly/{end}/{months}.
        """
        end = self._date_or_today(end, "end")
        months = _validate_positive_integer(months, "months")
        url = (
            f"{self.garmin_connect_usersummary_stats_url}/steps/monthly/{end}/{months}"
        )
        logger.debug("Requesting monthly steps")
        return self.connectapi(url)

    def get_stats_averages(self, start: str, end: str) -> dict[str, Any]:
        """Return average steps and resting heart rate over a date range.

        GET /usersummary-service/stats/averages/{start}/{end}.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_usersummary_stats_url}/averages/{start}/{end}"
        logger.debug("Requesting stats averages")
        return self.connectapi(url)

    def get_lifetime_totals(self) -> dict[str, Any]:
        """Return lifetime totals (distance, steps, calories, active days, ...).

        GET /usersummary-service/stats/connectLifetimeTotals/{displayName}.
        """
        url = (
            f"{self.garmin_connect_usersummary_stats_url}/connectLifetimeTotals/"
            f"{self._require_display_name()}"
        )
        logger.debug("Requesting lifetime totals")
        return self.connectapi(url)

    def get_daily_summaries(self, start: str, end: str) -> dict[str, Any]:
        """Return full daily summaries for a date range in one call.

        GET /usersummary-service/v2/dailysummaries?startDate&endDate. Returns
        ``{"data": [...]}`` with one entry per day (same fields as
        ``get_user_summary``).
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_usersummary_v2_url}/dailysummaries"
        logger.debug("Requesting daily summaries")
        return self.connectapi(url, params={"startDate": start, "endDate": end})

    def get_week_average_resting_hr(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the 7-day average resting heart rate as of ``cdate``.

        GET /usersummary-service/usersummary/weekAverageRestingHR/{displayName}
        ?calendarDate=.
        """
        cdate = self._date_or_today(cdate)
        url = (
            f"{self.garmin_connect_usersummary_url}/weekAverageRestingHR/"
            f"{self._require_display_name()}"
        )
        logger.debug("Requesting week average resting HR")
        return self.connectapi(url, params={"calendarDate": cdate})

    def get_hydration_all_data(self, cdate: str | None = None) -> dict[str, Any]:
        """Return hydration intake, goal, sweat loss and container settings for a day.

        GET /usersummary-service/usersummary/hydration/allData/{date} — the
        web app's primary hydration read (``get_hydration_data`` is the
        lighter ``hydration/daily`` variant).
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_usersummary_url}/hydration/allData/{cdate}"
        logger.debug("Requesting hydration all data")
        return self.connectapi(url)

    def get_daily_movement(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the daily movement chart (movement per 15-minute block).

        GET /wellness-service/wellness/dailyMovement?calendarDate=.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_wellness_url}/dailyMovement"
        logger.debug("Requesting daily movement")
        return self.connectapi(url, params={"calendarDate": cdate})

    def set_steps_goal(
        self, steps: int | None, cdate: str | None = None
    ) -> dict[str, Any]:
        """Set a manual daily step goal, or return to the device's automatic goal.

        PUT /wellness-service/wellness/wellness-goals/consolidated/steps/{date}
        with the goal object from :meth:`get_steps_goal`. A positive ``steps``
        value sets ``userGoal`` (Garmin reports it back with
        ``userGoalCategory: "manual"``); ``None`` or ``0`` restores the
        automatic goal (``userGoal: 0``, ``userGoalCategory: "my-auto"``).
        Verified live in both directions.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_wellness_url}/wellness-goals/consolidated/steps/{cdate}"
        current = self.connectapi(url)  # same object get_steps_goal returns
        payload = dict(current) if isinstance(current, dict) else {"goalType": "STEPS"}
        if steps:
            payload["userGoal"] = _validate_positive_integer(steps, "steps")
            payload["userGoalCategory"] = "manual"
        else:
            payload["userGoal"] = 0
            payload["userGoalCategory"] = "my-auto"
        logger.debug("Setting steps goal to %s", payload["userGoal"])
        return self.client.put("connectapi", url, json=payload).json()

    def get_sync_timestamp(self) -> str | None:
        """Return the timestamp (UTC, no offset) of the last device sync.

        GET /wellness-service/wellness/syncTimestamp.
        """
        url = f"{self.garmin_connect_wellness_url}/syncTimestamp"
        logger.debug("Requesting sync timestamp")
        return self.connectapi(url)

    def get_hourly_intensity_minutes(
        self, end: str | None = None, days: int = 7
    ) -> Any:
        """Return intensity minutes per hour for up to 7 days ending at ``end``.

        GET /wellness-service/stats/hourly/im/{end}/{days}. Garmin only accepts
        1-7 days inside the current week.
        """
        end = self._date_or_today(end, "end")
        days = _validate_positive_integer(days, "days")
        if days > 7:
            raise ValueError("days must be between 1 and 7")
        url = f"{self.garmin_connect_wellness_stats_url}/hourly/im/{end}/{days}"
        logger.debug("Requesting hourly intensity minutes")
        return self.connectapi(url)

    def get_weekly_wellness_stats(
        self,
        start: str,
        end: str,
        metric_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Return weekly wellness metrics (default: resting heart rate, id 60).

        GET /userstats-service/wellness/weekly/{displayName}
        ?fromWeekStartDate&untilWeekStartDate&metricId[&metricId...]
        &grpParentActType=false. Dates should be week start dates.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_userstats_url}/wellness/weekly/{self._require_display_name()}"
        params: dict[str, Any] = {
            "fromWeekStartDate": start,
            "untilWeekStartDate": end,
            "metricId": [int(m) for m in (metric_ids or [60])],
            "grpParentActType": "false",
        }
        logger.debug("Requesting weekly wellness stats")
        return self.connectapi(url, params=params)

    def get_monthly_wellness_stats(
        self,
        start: str,
        end: str,
        metric_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Return monthly wellness metrics (default: resting heart rate, id 60).

        GET /userstats-service/wellness/monthly/{displayName}
        ?fromMonthStartDate&untilMonthStartDate&metricId&grpParentActType=false.
        Dates should be the first day of a month.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_userstats_url}/wellness/monthly/{self._require_display_name()}"
        params: dict[str, Any] = {
            "fromMonthStartDate": start,
            "untilMonthStartDate": end,
            "metricId": [int(m) for m in (metric_ids or [60])],
            "grpParentActType": "false",
        }
        logger.debug("Requesting monthly wellness stats")
        return self.connectapi(url, params=params)

    def get_user_statistics(self) -> dict[str, Any]:
        """Return the profile statistics block (totals per activity type).

        GET /userstats-service/statistics/{displayName}.
        """
        url = f"{self.garmin_connect_userstats_url}/statistics/{self._require_display_name()}"
        logger.debug("Requesting user statistics")
        return self.connectapi(url)

    def get_daily_sleep(
        self, cdate: str | None = None, non_sleep_buffer_minutes: int | None = 60
    ) -> dict[str, Any]:
        """Return sleep data for a day from the newer sleep-service endpoint.

        GET /sleep-service/sleep/dailySleepData?date[&nonSleepBufferMinutes]
        — the call the web app's Sleep page makes; ``get_sleep_data`` uses the
        older wellness-service variant with the same payload.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_sleep_service_url}/sleep/dailySleepData"
        params: dict[str, Any] = {"date": cdate}
        if non_sleep_buffer_minutes is not None:
            params["nonSleepBufferMinutes"] = _validate_non_negative_integer(
                non_sleep_buffer_minutes, "non_sleep_buffer_minutes"
            )
        logger.debug("Requesting daily sleep")
        return self.connectapi(url, params=params)

    def get_naps(
        self, cdate: str | None = None, include_overlaps: bool = True
    ) -> list[dict[str, Any]]:
        """Return naps recorded on a day.

        GET /sleep-service/sleep/naps/{date}?includeOverlaps=.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_sleep_service_url}/sleep/naps/{cdate}"
        params = {"includeOverlaps": str(bool(include_overlaps)).lower()}
        logger.debug("Requesting naps")
        return self.connectapi(url, params=params)

    def get_sleep_stats_weekly(
        self, end: str | None = None, weeks: int = 52
    ) -> dict[str, Any]:
        """Return weekly sleep statistics (``overallStats`` + per-week values).

        GET /sleep-service/stats/sleep/weekly/{end}/{weeks}.
        """
        end = self._date_or_today(end, "end")
        weeks = _validate_positive_integer(weeks, "weeks")
        url = (
            f"{self.garmin_connect_sleep_service_url}/stats/sleep/weekly/{end}/{weeks}"
        )
        logger.debug("Requesting weekly sleep stats")
        return self.connectapi(url)

    def get_sleep_stats_overall(self, start: str, end: str) -> dict[str, Any]:
        """Return overall sleep statistics (averages) for a date range.

        GET /sleep-service/stats/sleep/overall/{start}/{end}.
        """
        start, end = _validate_date_range(start, end)
        url = (
            f"{self.garmin_connect_sleep_service_url}/stats/sleep/overall/{start}/{end}"
        )
        logger.debug("Requesting overall sleep stats")
        return self.connectapi(url)

    def get_health_snapshots(self, cdate: str | None = None) -> list[dict[str, Any]]:
        """Return Health Snapshot sessions recorded on a day.

        GET /wellnessactivity-service/activity/summary/{date}.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_health_snapshot_url}/summary/{cdate}"
        logger.debug("Requesting health snapshots")
        return self.connectapi(url)

    def get_health_snapshots_range(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return Health Snapshot sessions recorded in a date range.

        GET /wellnessactivity-service/activity/summary/range/{start}/{end}.
        Each entry carries ``activityUuid.uuid`` for
        ``get_health_snapshot`` / ``download_health_snapshot_session``.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_health_snapshot_url}/summary/range/{start}/{end}"
        logger.debug("Requesting health snapshots range")
        return self.connectapi(url)

    def get_health_snapshot(self, cdate: str, snapshot_uuid: str) -> dict[str, Any]:
        """Return one Health Snapshot session summary.

        GET /wellnessactivity-service/activity/summary/{date}/{uuid}.
        """
        cdate = _validate_date_format(cdate, "cdate")
        snapshot_uuid = _validate_uuid(snapshot_uuid, "snapshot_uuid")
        url = (
            f"{self.garmin_connect_health_snapshot_url}/summary/{cdate}/{snapshot_uuid}"
        )
        logger.debug("Requesting health snapshot %s", snapshot_uuid)
        return self.connectapi(url)

    def get_health_snapshot_epochs(self, snapshot_uuid: str) -> Any:
        """Return the per-epoch samples (HR, HRV, SpO2, ...) of a Health Snapshot.

        GET /wellnessactivity-service/activity/epoch/{uuid}.
        """
        snapshot_uuid = _validate_uuid(snapshot_uuid, "snapshot_uuid")
        url = f"{self.garmin_connect_health_snapshot_url}/epoch/{snapshot_uuid}"
        logger.debug("Requesting health snapshot epochs %s", snapshot_uuid)
        return self.connectapi(url)

    def download_health_snapshot_session(self, cdate: str, snapshot_uuid: str) -> bytes:
        """Download one Health Snapshot session as a FIT file.

        GET /download-service/files/wellness/activity/{date}/{uuid}
        (``download_health_snapshot`` downloads the whole day).
        """
        cdate = _validate_date_format(cdate, "cdate")
        snapshot_uuid = _validate_uuid(snapshot_uuid, "snapshot_uuid")
        url = f"{self.garmin_connect_health_snapshot_download}/activity/{cdate}/{snapshot_uuid}"
        logger.debug("Downloading health snapshot session %s", snapshot_uuid)
        return self.download(url)

    def get_nutrition_status(self) -> dict[str, Any]:
        """Return whether nutrition tracking (or MyFitnessPal) is in use.

        GET /nutrition-service/user/nutritionCurrentStatus.
        """
        url = f"{self.garmin_connect_nutrition_url}/user/nutritionCurrentStatus"
        logger.debug("Requesting nutrition status")
        return self.connectapi(url)

    def get_calorie_summary(
        self, start: str, end: str, current_date: str | None = None
    ) -> dict[str, Any]:
        """Return daily nutrition totals per meal with goals for a date range.

        GET /nutrition-service/calorie/summary/daily?startDate&endDate
        &currentDate&isDataForReport=true.
        """
        start, end = _validate_date_range(start, end)
        current_date = self._date_or_today(current_date, "current_date")
        url = f"{self.garmin_connect_nutrition_url}/calorie/summary/daily"
        params = {
            "startDate": start,
            "endDate": end,
            "currentDate": current_date,
            "isDataForReport": "true",
        }
        logger.debug("Requesting calorie summary")
        return self.connectapi(url, params=params)

    def get_ecg_daily(self, start: str, end: str) -> dict[str, Any]:
        """Return ECG recordings per day for a date range.

        GET https://ghs.<domain>/ghs/ecg/v1/ecg/daily?firstDay&lastDay. The
        web app only calls this when the account has the ECG feature; others
        get a 404. Not verified against a live account with ECG data.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_ecg_url}/daily"
        logger.debug("Requesting ECG daily")
        return self.connectapi(url, params={"firstDay": start, "lastDay": end})

    def get_ecg_list(
        self,
        start: str = "2021-01-01",
        end: str | None = None,
        page_size: int = 20,
        page: str | None = None,
    ) -> dict[str, Any]:
        """Return a page of ECG recordings.

        GET https://ghs.<domain>/ghs/ecg/v1/ecg/list?firstDay&lastDay&pageSize
        [&page=<token>]. Not verified against a live account with ECG data.
        """
        end = self._date_or_today(end, "end")
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_ecg_url}/list"
        params: dict[str, Any] = {
            "firstDay": start,
            "lastDay": end,
            "pageSize": _validate_positive_integer(page_size, "page_size"),
        }
        if page:
            params["page"] = page
        logger.debug("Requesting ECG list")
        return self.connectapi(url, params=params)

    def get_ecg(self, ecg_id: str) -> dict[str, Any]:
        """Return one ECG recording with its waveform.

        GET https://ghs.<domain>/ghs/ecg/v1/ecg/{ecgId}. Not verified against
        a live account with ECG data.
        """
        if not isinstance(ecg_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", ecg_id):
            raise ValueError("ecg_id must be an alphanumeric identifier")
        url = f"{self.garmin_connect_ecg_url}/{ecg_id}"
        logger.debug("Requesting ECG %s", ecg_id)
        return self.connectapi(url)

    def get_jetlag_status(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the Jet Lag Adviser guidance for a day (empty dict without a trip).

        GET /jetlag-service/jetlag/status/daily/{date}.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_jetlag_url}/status/daily/{cdate}"
        logger.debug("Requesting jet lag status")
        return self.connectapi(url)

    def get_nutrition_daily_food_log(
        self,
        cdate: str,
        include_goals: bool = True,
        include_nutrition: bool = True,
        meal_id: int | str | None = None,
    ) -> dict[str, Any]:
        """Return food log summary for 'cdate' format 'YYYY-MM-DD'.

        ``includeGoals`` and ``includeNutrition`` are sent like the web app
        does (both ``true`` by default) so goals and nutrition totals are part
        of the response; ``meal_id`` limits the log to one meal.
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_nutrition_daily_food_logs}/{cdate}"
        params: dict[str, str] = {
            "includeGoals": str(bool(include_goals)).lower(),
            "includeNutrition": str(bool(include_nutrition)).lower(),
        }
        if meal_id is not None:
            params["mealId"] = str(_coerce_positive_id(meal_id, "meal_id"))
        logger.debug("Requesting nutrition food log data for date %s", cdate)
        return self.connectapi(url, params=params)

    def get_nutrition_daily_meals(self, cdate: str) -> dict[str, Any]:
        """Return meals summary for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_nutrition_daily_meals}/{cdate}"
        logger.debug("Requesting nutrition meals data for date %s", cdate)
        return self.connectapi(url)

    def get_nutrition_daily_settings(self, cdate: str) -> dict[str, Any]:
        """Return nutrition settings for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_nutrition_daily_settings}/{cdate}"
        logger.debug("Requesting nutrition settings data for date %s", cdate)
        return self.connectapi(url)
