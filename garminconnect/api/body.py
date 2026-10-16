"""Weight, body composition and blood pressure."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from ..fit import FitEncoderWeight  # type: ignore[attr-defined]
from ._common import (
    DATE_FORMAT_STR,
    VALID_WEIGHT_UNITS,
    _coerce_positive_id,
    _fmt_ts,
    _validate_date_format,
    _validate_date_range,
    _validate_json_exists,
    _validate_positive_number,
    _validate_sport_key,
    logger,
)
from .base import GarminBase


class BodyMixin(GarminBase):
    """Weight, body composition and blood pressure."""

    def get_stats_and_body(self, cdate: str) -> dict[str, Any]:
        """Return the daily summary and body composition for a date."""
        # Validate input
        cdate = _validate_date_format(cdate, "cdate")
        stats = self.get_stats(cdate)
        body = self.get_body_composition(cdate)
        body_avg = body.get("totalAverage") or {}
        if not isinstance(body_avg, dict):
            body_avg = {}
        return {**stats, **body_avg}

    def get_body_composition(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """Return available body composition data for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'.
        """
        startdate = _validate_date_format(startdate, "startdate")
        enddate = (
            startdate if enddate is None else _validate_date_format(enddate, "enddate")
        )
        if (
            datetime.strptime(startdate, DATE_FORMAT_STR).date()
            > datetime.strptime(enddate, DATE_FORMAT_STR).date()
        ):
            raise ValueError("startdate cannot be after enddate")
        url = f"{self.garmin_connect_weight_url}/weight/dateRange"
        params = {"startDate": startdate, "endDate": enddate}
        logger.debug("Requesting body composition")

        return self.connectapi(url, params=params)

    def add_body_composition(
        self,
        timestamp: str | None,
        weight: float,
        percent_fat: float | None = None,
        percent_hydration: float | None = None,
        visceral_fat_mass: float | None = None,
        bone_mass: float | None = None,
        muscle_mass: float | None = None,
        basal_met: float | None = None,
        active_met: float | None = None,
        physique_rating: float | None = None,
        metabolic_age: float | None = None,
        visceral_fat_rating: float | None = None,
        bmi: float | None = None,
    ) -> dict[str, Any]:
        """Add a weigh-in with body composition values, uploaded as a FIT file."""
        weight = _validate_positive_number(weight, "weight")
        dt = (
            self._localize(datetime.fromisoformat(timestamp))
            if timestamp
            else self.now()
        )
        fitEncoder = FitEncoderWeight()
        fitEncoder.write_file_info()
        fitEncoder.write_file_creator()
        fitEncoder.write_device_info(dt)
        fitEncoder.write_weight_scale(
            dt,
            weight=weight,
            percent_fat=percent_fat,
            percent_hydration=percent_hydration,
            visceral_fat_mass=visceral_fat_mass,
            bone_mass=bone_mass,
            muscle_mass=muscle_mass,
            basal_met=basal_met,
            active_met=active_met,
            physique_rating=physique_rating,
            metabolic_age=metabolic_age,
            visceral_fat_rating=visceral_fat_rating,
            bmi=bmi,
        )
        fitEncoder.finish()

        url = self.garmin_connect_upload
        files = {
            "file": ("body_composition.fit", fitEncoder.getvalue()),
        }
        return self.client.post("connectapi", url, files=files, api=True)

    def add_weigh_in(
        self, weight: int | float, unitKey: str = "kg", timestamp: str = ""
    ) -> dict[str, Any] | None:
        """Add a weigh-in (kg by default)."""
        # Validate inputs
        weight = _validate_positive_number(weight, "weight")

        if unitKey not in VALID_WEIGHT_UNITS:
            raise ValueError(f"unitKey must be one of {VALID_WEIGHT_UNITS}")

        url = f"{self.garmin_connect_weight_url}/user-weight"

        try:
            dt = (
                self._localize(datetime.fromisoformat(timestamp))
                if timestamp
                else self.now()
            )
        except ValueError as e:
            raise ValueError(f"invalid timestamp format: {e}") from e

        # Apply timezone offset to get UTC/GMT time
        dtGMT = dt.astimezone(UTC)
        payload = {
            # The web app's weigh-in form sends the local calendar date too.
            "date": dt.date().isoformat(),
            "dateTimestamp": _fmt_ts(dt),
            "gmtTimestamp": _fmt_ts(dtGMT),
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }
        logger.debug("Adding weigh-in")
        return _validate_json_exists(self.client.post("connectapi", url, json=payload))

    def add_weigh_in_with_timestamps(
        self,
        weight: int | float,
        unitKey: str = "kg",
        dateTimestamp: str = "",
        gmtTimestamp: str = "",
    ) -> dict[str, Any] | None:
        """Add a weigh-in with explicit local and GMT timestamps (kg by default)."""
        url = f"{self.garmin_connect_weight_url}/user-weight"

        if unitKey not in VALID_WEIGHT_UNITS:
            raise ValueError(f"unitKey must be one of {VALID_WEIGHT_UNITS}")
        # Make local timestamp timezone-aware (naive = user's Garmin timezone)
        dt = (
            self._localize(datetime.fromisoformat(dateTimestamp))
            if dateTimestamp
            else self.now()
        )
        if gmtTimestamp:
            g = datetime.fromisoformat(gmtTimestamp)
            # Assume provided GMT is UTC if naive; otherwise convert to UTC
            if g.tzinfo is None:
                g = g.replace(tzinfo=UTC)
            dtGMT = g.astimezone(UTC)
        else:
            dtGMT = dt.astimezone(UTC)

        # Validate weight for consistency with add_weigh_in
        weight = _validate_positive_number(weight, "weight")
        # Build the payload
        payload = {
            "dateTimestamp": _fmt_ts(dt),  # Local time (ms)
            "gmtTimestamp": _fmt_ts(dtGMT),  # GMT/UTC time (ms)
            "unitKey": unitKey,
            "sourceType": "MANUAL",
            "value": weight,
        }

        # Debug log for payload
        logger.debug("Adding weigh-in with explicit timestamps: %s", payload)

        # Make the POST request
        return _validate_json_exists(self.client.post("connectapi", url, json=payload))

    def get_weigh_ins(self, startdate: str, enddate: str) -> dict[str, Any]:
        """Get weigh-ins between startdate and enddate using format 'YYYY-MM-DD'."""
        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_weight_url}/weight/range/{startdate}/{enddate}"
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def get_daily_weigh_ins(self, cdate: str) -> dict[str, Any]:
        """Get weigh-ins for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_weight_url}/weight/dayview/{cdate}"
        params = {"includeAll": True}
        logger.debug("Requesting weigh-ins")

        return self.connectapi(url, params=params)

    def delete_weigh_in(self, weight_pk: str, cdate: str) -> Any:
        """Delete one weigh-in."""
        cdate = _validate_date_format(cdate, "cdate")
        weight_pk = str(_coerce_positive_id(weight_pk, "weight_pk"))
        url = f"{self.garmin_connect_weight_url}/weight/{cdate}/byversion/{weight_pk}"
        logger.debug("Deleting weigh-in")

        return self.client.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def delete_weigh_ins(self, cdate: str, delete_all: bool = False) -> int | None:
        """Delete the weigh-ins on 'cdate' (all of them only with `delete_all=True`).
        Includes option to delete all weigh-ins for that date.
        """
        daily_weigh_ins = self.get_daily_weigh_ins(cdate)
        weigh_ins = daily_weigh_ins.get("dateWeightList", [])
        if not weigh_ins or len(weigh_ins) == 0:
            logger.warning(f"No weigh-ins found on {cdate}")
            return None
        if len(weigh_ins) > 1:
            logger.warning(f"Multiple weigh-ins found for {cdate}")
            if not delete_all:
                logger.warning(
                    f"Set delete_all to True to delete all {len(weigh_ins)} weigh-ins"
                )
                return None

        for w in weigh_ins:
            self.delete_weigh_in(w["samplePk"], cdate)

        return len(weigh_ins)

    def set_blood_pressure(
        self,
        systolic: int,
        diastolic: int,
        pulse: int | None = None,
        timestamp: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        """Add a blood pressure reading.

        pulse is optional - Garmin Connect's own UI accepts a blood
        pressure entry without a heart rate value (#426).
        """
        url = f"{self.garmin_connect_set_blood_pressure_endpoint}"
        dt = (
            self._localize(datetime.fromisoformat(timestamp))
            if timestamp
            else self.now()
        )
        # Apply timezone offset to get UTC/GMT time
        dtGMT = dt.astimezone(UTC)
        payload = {
            "measurementTimestampLocal": _fmt_ts(dt),
            "measurementTimestampGMT": _fmt_ts(dtGMT),
            "systolic": systolic,
            "diastolic": diastolic,
            "sourceType": "MANUAL",
            "notes": notes,
        }
        checks = [
            ("systolic", systolic, 70, 260),
            ("diastolic", diastolic, 40, 150),
        ]
        if pulse is not None:
            checks.append(("pulse", pulse, 20, 250))
            payload["pulse"] = pulse
        for name, val, lo, hi in checks:
            if not isinstance(val, int) or not (lo <= val <= hi):
                raise ValueError(f"{name} must be an int in [{lo}, {hi}]")
        logger.debug("Adding blood pressure")

        return self.client.post("connectapi", url, json=payload).json()

    def update_blood_pressure(
        self, measurement: dict[str, Any], *, notes: str
    ) -> dict[str, Any]:
        """Change the note of an existing blood pressure reading.

        PUT /bloodpressure-service/bloodpressure with the measurement object
        (an entry of ``get_blood_pressure()["measurementSummaries"][i]
        ["measurements"]``, identified by its ``version``) and the new
        ``notes``. Verified live: Garmin applies only the note on this call —
        changed systolic/diastolic/pulse values are echoed back but not
        stored — so to correct values use :meth:`delete_blood_pressure` and
        :meth:`set_blood_pressure`.
        """
        if not isinstance(measurement, dict) or not measurement.get("version"):
            raise ValueError(
                "measurement must be a blood pressure entry with a 'version' "
                "(see get_blood_pressure)"
            )
        if not isinstance(notes, str):
            raise ValueError("notes must be a string")
        payload = {**measurement, "notes": notes}
        logger.debug("Updating blood pressure note for %s", measurement["version"])
        return self.client.put(
            "connectapi", self.garmin_connect_set_blood_pressure_endpoint, json=payload
        ).json()

    def get_blood_pressure(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """Return blood pressure by day for 'startdate' format
        'YYYY-MM-DD' through enddate 'YYYY-MM-DD'.
        """
        startdate = _validate_date_format(startdate, "startdate")
        if enddate is None:
            enddate = startdate
        else:
            enddate = _validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_blood_pressure_endpoint}/{startdate}/{enddate}"
        params = {"includeAll": True}
        logger.debug("Requesting blood pressure data")

        return self.connectapi(url, params=params)

    def delete_blood_pressure(self, version: str, cdate: str) -> dict[str, Any]:
        """Delete one blood pressure reading."""
        cdate = _validate_date_format(cdate, "cdate")
        version = str(_coerce_positive_id(version, "version"))
        url = f"{self.garmin_connect_set_blood_pressure_endpoint}/{cdate}/{version}"
        logger.debug("Deleting blood pressure measurement")

        return self.client.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        ).json()

    def get_power_to_weight_range(
        self,
        start: str,
        end: str,
        aggregation: str = "daily",
        sport: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return power-to-weight history, one series per sport.

        GET /biometric-service/stats/powerToWeight/range/{start}/{end}
        ?aggregation[&sport]. Without ``sport`` all sports are returned.
        """
        start, end = _validate_date_range(start, end)
        url = (
            f"{self.garmin_connect_biometric_service_url}/stats/powerToWeight/range/"
            f"{start}/{end}"
        )
        params: dict[str, str] = {"aggregation": aggregation}
        if sport:
            params["sport"] = _validate_sport_key(sport)
        logger.debug("Requesting power-to-weight range")
        return self.connectapi(url, params=params)

    def get_latest_weight(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the most recent weigh-in as of ``cdate`` (default today).

        GET /weight-service/weight/latest?date=&ignorePriority=true.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_weight_url}/weight/latest"
        logger.debug("Requesting latest weight")
        return self.connectapi(url, params={"date": cdate, "ignorePriority": "true"})

    def get_first_weight(self) -> dict[str, Any]:
        """Return the first weigh-in ever recorded on the account.

        GET /weight-service/weight/first.
        """
        url = f"{self.garmin_connect_weight_url}/weight/first"
        logger.debug("Requesting first weight")
        return self.connectapi(url)

    def get_daily_last_weight(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return the last weigh-in of each day in a date range (chart series).

        GET /weight-service/weight/daily/last?startDate&endDate.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_weight_url}/weight/daily/last"
        logger.debug("Requesting daily last weight")
        return self.connectapi(url, params={"startDate": start, "endDate": end})

    def get_weight_snapshot(self, start: str, end: str) -> dict[str, Any]:
        """Return all weigh-ins in a range as ``dateWeightList`` entries.

        GET /weight-service/weight/daterangesnapshot?startDate&endDate.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_weight_url}/weight/daterangesnapshot"
        logger.debug("Requesting weight snapshot")
        return self.connectapi(url, params={"startDate": start, "endDate": end})

    def get_weekly_weight(self, end: str | None = None) -> Any:
        """Return weekly weight aggregates for the 52 weeks ending at ``end``.

        GET /weight-service/weight/weeklyRange/{start}/{end}; Garmin requires
        the range to span exactly 52 weeks (364 days inclusive), so ``start``
        is derived from ``end``.
        """
        end = self._date_or_today(end, "end")
        start = (date.fromisoformat(end) - timedelta(days=363)).isoformat()
        url = f"{self.garmin_connect_weight_url}/weight/weeklyRange/{start}/{end}"
        logger.debug("Requesting weekly weight")
        return self.connectapi(url)

    def get_blood_pressure_day(self, cdate: str | None = None) -> dict[str, Any]:
        """Return blood pressure readings for one day.

        GET /bloodpressure-service/bloodpressure/dayview/{date}.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_blood_pressure_url}/dayview/{cdate}"
        logger.debug("Requesting blood pressure day view")
        return self.connectapi(url)

    def get_daily_last_blood_pressure(
        self, start: str, end: str
    ) -> list[dict[str, Any]]:
        """Return the last blood pressure reading of each day in a range.

        GET /bloodpressure-service/bloodpressure/daily/last/{start}/{end}.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_blood_pressure_url}/daily/last/{start}/{end}"
        logger.debug("Requesting daily last blood pressure")
        return self.connectapi(url)

    def get_weekly_blood_pressure(self, end: str | None = None) -> Any:
        """Return weekly blood pressure aggregates for the 52 weeks ending at ``end``.

        GET /bloodpressure-service/bloodpressure/weeklyRange/{start}/{end};
        Garmin requires exactly 52 weeks (364 days inclusive), so ``start`` is
        derived from ``end``.
        """
        end = self._date_or_today(end, "end")
        start = (date.fromisoformat(end) - timedelta(days=363)).isoformat()
        url = f"{self.garmin_connect_blood_pressure_url}/weeklyRange/{start}/{end}"
        logger.debug("Requesting weekly blood pressure")
        return self.connectapi(url)
