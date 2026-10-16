"""Performance metrics: VO2 max, training status and readiness, thresholds, zones, acclimation, fitness age."""

from datetime import date, datetime
from typing import Any

from ._common import (
    DATE_FORMAT_STR,
    _validate_date_format,
    _validate_date_range,
    _validate_positive_integer,
    _validate_sport_key,
    logger,
)
from .base import GarminBase


class MetricsMixin(GarminBase):
    """Performance metrics: VO2 max, training status and readiness, thresholds, zones, acclimation, fitness age."""

    def get_max_metrics(self, cdate: str) -> dict[str, Any]:
        """Return available max metric data for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_metrics_url}/{cdate}/{cdate}"
        logger.debug("Requesting max metrics")

        return self.connectapi(url)

    def get_max_metrics_range(
        self,
        start: str,
        end: str,
        aggregation: str = "daily",
        sport: str | None = None,
    ) -> dict[str, Any]:
        """Return max metric data for a date range ('start'/'end' format 'YYYY-MM-DD').

        Unlike `get_max_metrics`, which is limited to a single day, this
        queries the same endpoint with distinct start/end dates to fetch a
        range in one request.

        Args:
            aggregation: ``daily`` (default), ``weekly`` or ``monthly``; the
                web app's VO2 max reports use the latter two for long ranges.
            sport: optional sport filter (e.g. ``running``, ``cycling``), sent
                as the ``sport`` query parameter like the web app does.

        """
        start, end = _validate_date_range(start, end)
        if aggregation not in {"daily", "weekly", "monthly"}:
            raise ValueError("aggregation must be 'daily', 'weekly' or 'monthly'")
        base = self.garmin_connect_metrics_url
        if aggregation != "daily":
            base = base.rsplit("/", 1)[0] + f"/{aggregation}"
        url = f"{base}/{start}/{end}"
        params = {"sport": sport.strip().lower()} if sport else None
        logger.debug("Requesting max metrics range")

        return self.connectapi(url, params=params)

    def get_functional_threshold_power_range(
        self,
        start: str,
        end: str,
        *,
        sport: str = "RUNNING",
        aggregation: str = "daily",
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Return historic functional threshold power for a Garmin sport.

        This uses Garmin Connect's undocumented biometric statistics range
        endpoint. It is useful for FTP history because the existing
        ``get_cycling_ftp`` endpoint returns only the latest cycling value.

        Args:
            start: First date in the range, format 'YYYY-MM-DD'.
            end: Last date in the range, format 'YYYY-MM-DD'.
            sport: Garmin sport key (e.g. ``RUNNING``, ``CYCLING``).
            aggregation: One of ``daily``, ``weekly``, ``monthly``, ``yearly``.

        """
        start, end = _validate_date_range(start, end)

        valid_aggregations = {"daily", "weekly", "monthly", "yearly"}
        if aggregation not in valid_aggregations:
            raise ValueError(f"aggregation must be one of {valid_aggregations}")

        normalized_sport = _validate_sport_key(sport)
        url = (
            f"{self.garmin_connect_biometric_stats_url}"
            f"/functionalThresholdPower/range/{start}/{end}"
        )
        params = {
            "sport": normalized_sport,
            "aggregation": aggregation,
            "aggregationStrategy": "LATEST",
        }
        logger.debug(
            "Requesting functional threshold power from %s to %s for sport %s",
            start,
            end,
            normalized_sport,
        )
        return self.connectapi(url, params=params)

    def get_lactate_threshold(
        self,
        *,
        latest: bool = True,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        aggregation: str = "daily",
    ) -> dict[str, Any]:
        """Return running lactate threshold information, including heart rate, power, and speed.

        :param bool (Required) - latest: Whether to query for the latest Lactate Threshold info or a range.  False if querying a range
        :param date (Optional) - start_date: The first date in the range to query, format 'YYYY-MM-DD'.  Required if `latest` is False.  Ignored if `latest` is True
        :param date (Optional) - end_date: The last date in the range to query, format 'YYYY-MM-DD'. Defaults to current data. Ignored if `latest` is True
        :param str (Optional) - aggregation: How to aggregate the data. Must be one of `daily`, `weekly`, `monthly`, `yearly`.
        """
        if latest:
            speed_and_heart_rate_url = (
                f"{self.garmin_connect_biometric_url}/latestLactateThreshold"
            )
            power_url = f"{self.garmin_connect_biometric_url}/powerToWeight/latest/{self.today()}"

            power = self.connectapi(power_url, params={"sport": "Running"})
            if isinstance(power, list) and power:
                power_dict = power[0]
            elif isinstance(power, dict):
                power_dict = power
            else:
                power_dict = {}

            speed_and_heart_rate = self.connectapi(speed_and_heart_rate_url)

            speed_and_heart_rate_dict = {
                "userProfilePK": None,
                "version": None,
                "calendarDate": None,
                "sequence": None,
                "speed": None,
                "heartRate": None,
                "heartRateCycling": None,
            }

            # Garmin /latestLactateThreshold endpoint returns a list of two
            # (or more, if cyclingHeartRate ever gets values) nearly identical dicts.
            # We're combining them here
            for entry in speed_and_heart_rate:
                speed = entry.get("speed")
                if speed is not None:
                    speed_and_heart_rate_dict["userProfilePK"] = entry["userProfilePK"]
                    speed_and_heart_rate_dict["version"] = entry["version"]
                    speed_and_heart_rate_dict["calendarDate"] = entry["calendarDate"]
                    speed_and_heart_rate_dict["sequence"] = entry["sequence"]
                    speed_and_heart_rate_dict["speed"] = speed

                # Prefer correct key; fall back to Garmin's historical typo ("hearRate")
                hr = entry.get("heartRate") or entry.get("hearRate")
                if hr is not None:
                    speed_and_heart_rate_dict["heartRate"] = hr

                # Doesn't exist for me but adding it just in case.  We'll check for each entry
                hrc = entry.get("heartRateCycling")
                if hrc is not None:
                    speed_and_heart_rate_dict["heartRateCycling"] = hrc
            return {
                "speed_and_heart_rate": speed_and_heart_rate_dict,
                "power": power_dict,
            }

        if start_date is None:
            raise ValueError("you must either specify 'latest=True' or a start_date")

        if end_date is None:
            end_date = self.today().isoformat()

        # Normalize and validate
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        else:
            start_date = _validate_date_format(start_date, "start_date")
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        else:
            end_date = _validate_date_format(end_date, "end_date")

        _valid_aggregations = {"daily", "weekly", "monthly", "yearly"}
        if aggregation not in _valid_aggregations:
            raise ValueError(f"aggregation must be one of {_valid_aggregations}")

        power = self.get_functional_threshold_power_range(
            start_date,
            end_date,
            sport="RUNNING",
            aggregation=aggregation,
        )

        params = {
            "sport": "RUNNING",
            "aggregation": aggregation,
            "aggregationStrategy": "LATEST",
        }
        speed_url = (
            f"{self.garmin_connect_biometric_stats_url}"
            f"/lactateThresholdSpeed/range/{start_date}/{end_date}"
        )

        heart_rate_url = (
            f"{self.garmin_connect_biometric_stats_url}"
            f"/lactateThresholdHeartRate/range/{start_date}/{end_date}"
        )

        speed = self.connectapi(speed_url, params=params)
        heart_rate = self.connectapi(heart_rate_url, params=params)

        return {"speed": speed, "heart_rate": heart_rate, "power": power}

    def get_training_readiness(self, cdate: str) -> list[dict[str, Any]]:
        """Return training readiness data for 'cdate' format 'YYYY-MM-DD'."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_training_readiness_url}/{cdate}"
        logger.debug("Requesting training readiness data")

        return self.connectapi(url)

    def get_morning_training_readiness(self, cdate: str) -> dict[str, Any] | None:
        """Return morning training readiness data for current user.

        This returns the Training Readiness score calculated immediately after
        waking up, which is shown in Garmin's Morning Report feature. It filters
        for entries with inputContext == 'AFTER_WAKEUP_RESET'.

        Args:
            cdate: Date string in format 'YYYY-MM-DD'

        Returns:
            Dictionary containing morning training readiness data, or None if
            no morning data is available for the specified date.

        Note:
            Not all devices/firmware versions populate the inputContext field.
            If inputContext is null for all entries, this method returns the
            first entry as a fallback (typically the morning reading).

        """
        data = self.get_training_readiness(cdate)

        if not data:
            return None

        # The endpoint normally returns a list of snapshots, but stay defensive:
        # some responses (or callers stubbing this) hand back a single dict.
        if isinstance(data, dict):
            return data

        morning_entry = next(
            (
                entry
                for entry in data
                if entry.get("inputContext") == "AFTER_WAKEUP_RESET"
            ),
            None,
        )

        if morning_entry is None:
            logger.debug(
                "No AFTER_WAKEUP_RESET context found, using first entry as fallback"
            )
            return data[0]

        return morning_entry

    def get_training_four_week_load_balance(self, cdate: str) -> dict[str, Any]:
        """Return training load balance (load focus) data for the current user.

        The date identifies the end of the trailing four-week load-focus period.
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_training_load_balance_url}/latest/{cdate}"
        logger.debug("Requesting training load balance data")

        return self.connectapi(url)

    def get_daily_training_status(self, cdate: str) -> dict[str, Any]:
        """Return the training status for a single day for the current user.

        Includes the training status phrase and the acute/chronic training
        load (ACWR) as of the given date.
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_daily_training_status_url}/{cdate}"
        logger.debug("Requesting daily training status data")

        return self.connectapi(url)

    def get_endurance_score(
        self,
        startdate: str,
        enddate: str | None = None,
        aggregation: str = "weekly",
    ) -> dict[str, Any]:
        """Return endurance score by day for 'startdate' format 'YYYY-MM-DD'
        through enddate 'YYYY-MM-DD'.
        Using a single day returns the precise values for that day.
        Using a range returns values aggregated per ``aggregation`` period
        (``weekly`` by default; the web app uses ``daily`` for its 4- and
        12-week reports).
        """
        startdate = _validate_date_format(startdate, "startdate")
        if enddate is None:
            url = self.garmin_connect_endurance_score_url
            params = {"calendarDate": startdate}
            logger.debug("Requesting endurance score data for a single day")

            return self.connectapi(url, params=params)
        url = f"{self.garmin_connect_endurance_score_url}/stats"
        enddate = _validate_date_format(enddate, "enddate")
        if aggregation not in {"daily", "weekly"}:
            raise ValueError("aggregation must be 'daily' or 'weekly'")
        params = {
            "startDate": startdate,
            "endDate": enddate,
            "aggregation": aggregation,
        }
        logger.debug("Requesting endurance score data for a range of days")

        return self.connectapi(url, params=params)

    def get_running_tolerance(
        self, startdate: str, enddate: str, aggregation: str = "weekly"
    ) -> list[dict[str, Any]]:
        """Return running tolerance data for date range.

        Args:
            startdate: Start date in 'YYYY-MM-DD' format.
            enddate: End date in 'YYYY-MM-DD' format.
            aggregation: 'daily' or 'weekly' (default: 'weekly').

        Returns:
            List of running tolerance data points.

        """
        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        if aggregation not in ("daily", "weekly"):
            raise ValueError(
                f"invalid aggregation '{aggregation}', must be 'daily' or 'weekly'"
            )
        url = self.garmin_connect_running_tolerance_url
        params = {
            "startDate": startdate,
            "endDate": enddate,
            "aggregation": aggregation,
        }
        logger.debug(
            "Requesting running tolerance data (%s) from %s to %s",
            aggregation,
            startdate,
            enddate,
        )

        return self.connectapi(url, params=params)

    def get_race_predictions(
        self,
        startdate: str | None = None,
        enddate: str | None = None,
        _type: str | None = None,
    ) -> dict[str, Any]:
        """Return race predictions for the 5k, 10k, half marathon and marathon.
        Accepts either 0 parameters or all three:
        If all parameters are empty, returns the race predictions for the current date
        Or returns the race predictions for each day or month in the range provided.

        Keyword Arguments:
        'startdate' the date of the earliest race predictions
        Cannot be more than one year before 'enddate'
        'enddate' the date of the last race predictions
        '_type' either 'daily' (the predictions for each day in the range) or
        'monthly' (the aggregated monthly prediction for each month in the range)

        """
        valid = {"daily", "monthly", None}
        if _type not in valid:
            raise ValueError(f"results: _type must be one of {valid!r}.")

        if _type is None and startdate is None and enddate is None:
            url = (
                self.garmin_connect_race_predictor_url
                + f"/latest/{self._require_display_name()}"
            )
            return self.connectapi(url)

        if _type is not None and startdate is not None and enddate is not None:
            startdate = _validate_date_format(startdate, "startdate")
            enddate = _validate_date_format(enddate, "enddate")
            if (
                datetime.strptime(enddate, DATE_FORMAT_STR).date()
                - datetime.strptime(startdate, DATE_FORMAT_STR).date()
            ).days > 366:
                raise ValueError(
                    "startdate cannot be more than one year before enddate"
                )
            url = (
                self.garmin_connect_race_predictor_url
                + f"/{_type}/{self._require_display_name()}"
            )
            params = {"fromCalendarDate": startdate, "toCalendarDate": enddate}
            return self.connectapi(url, params=params)

        raise ValueError("you must either provide all parameters or no parameters")

    def get_training_status(self, cdate: str) -> dict[str, Any]:
        """Return training status data for current user."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_training_status_url}/{cdate}"
        logger.debug("Requesting training status data")

        return self.connectapi(url)

    def get_fitnessage_data(self, cdate: str) -> dict[str, Any]:
        """Return Fitness Age data for current user."""
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_fitnessage}/{cdate}"
        logger.debug("Requesting Fitness Age data")

        return self.connectapi(url)

    def get_hill_score(
        self, startdate: str, enddate: str | None = None
    ) -> dict[str, Any]:
        """Return hill score by day from 'startdate' format 'YYYY-MM-DD'
        to enddate 'YYYY-MM-DD'.
        """
        if enddate is None:
            url = self.garmin_connect_hill_score_url
            startdate = _validate_date_format(startdate, "startdate")
            params = {"calendarDate": startdate}
            logger.debug("Requesting hill score data for a single day")

            return self.connectapi(url, params=params)

        url = f"{self.garmin_connect_hill_score_url}/stats"
        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        params = {
            "startDate": startdate,
            "endDate": enddate,
            "aggregation": "daily",
        }
        logger.debug("Requesting hill score data for a range of days")

        return self.connectapi(url, params=params)

    def get_cycling_ftp(
        self,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Return cycling Functional Threshold Power (FTP) information."""
        url = f"{self.garmin_connect_biometric_url}/latestFunctionalThresholdPower/CYCLING"
        logger.debug("Requesting latest cycling FTP")
        return self.connectapi(url)

    def get_heart_rate_zones(self) -> list[dict[str, Any]]:
        """Return configured heart rate zones for all sport profiles."""
        logger.debug("Requesting heart rate zones")
        return self.connectapi(self.garmin_connect_heart_rate_zones_url)

    def get_power_zones(self) -> list[dict[str, Any]]:
        """Return configured power zones for all supported sports."""
        url = f"{self.garmin_connect_power_zones_url}/sports/all"
        logger.debug("Requesting power zones for all sports")
        return self.connectapi(url)

    def get_power_zones_for_sport(self, sport: str) -> dict[str, Any]:
        """Return configured power zones for a Garmin sport key."""
        normalized_sport = _validate_sport_key(sport)
        url = f"{self.garmin_connect_power_zones_url}/sport/{normalized_sport}"
        logger.debug("Requesting power zones for sport %s", normalized_sport)
        return self.connectapi(url)

    def get_max_metrics_latest(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the latest VO2 max record as of ``cdate`` (default today).

        GET /metrics-service/metrics/maxmet/latest/{date}. The response has
        ``generic`` (running), ``cycling`` and ``heatAltitudeAcclimation``.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_metrics_base_url}/maxmet/latest/{cdate}"
        logger.debug("Requesting latest max metrics")
        return self.connectapi(url)

    def get_training_readiness_range(
        self, start: str, end: str
    ) -> list[dict[str, Any]]:
        """Return training readiness entries for a date range.

        GET /metrics-service/metrics/trainingreadiness/{start}/{end}. Several
        entries per day are possible (one per recalculation); see
        ``inputContext``.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_metrics_base_url}/trainingreadiness/{start}/{end}"
        logger.debug("Requesting training readiness range")
        return self.connectapi(url)

    def get_weekly_training_status(self, start: str, end: str) -> dict[str, Any]:
        """Return the weekly training status / load history for a date range.

        GET /metrics-service/metrics/trainingstatus/weekly/{displayName}
        ?fromCalendarDate&toCalendarDate — the series behind the web app's
        Training Status page.
        """
        start, end = _validate_date_range(start, end)
        url = (
            f"{self.garmin_connect_metrics_base_url}/trainingstatus/weekly/"
            f"{self._require_display_name()}"
        )
        params = {"fromCalendarDate": start, "toCalendarDate": end}
        logger.debug("Requesting weekly training status")
        return self.connectapi(url, params=params)

    def get_heat_altitude_acclimation(self, cdate: str | None = None) -> dict[str, Any]:
        """Return heat and altitude acclimation as of ``cdate`` (default today).

        GET /metrics-service/metrics/heataltitudeacclimation/latest/{date}.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_metrics_base_url}/heataltitudeacclimation/latest/{cdate}"
        logger.debug("Requesting heat/altitude acclimation")
        return self.connectapi(url)

    def get_heat_altitude_acclimation_range(
        self, start: str, end: str, aggregation: str = "daily"
    ) -> list[dict[str, Any]]:
        """Return heat and altitude acclimation history for a date range.

        GET /metrics-service/metrics/heataltitudeacclimation/{aggregation}/{start}/{end}
        with ``aggregation`` one of ``daily``, ``weekly``, ``monthly``.
        """
        start, end = _validate_date_range(start, end)
        if aggregation not in {"daily", "weekly", "monthly"}:
            raise ValueError("aggregation must be 'daily', 'weekly' or 'monthly'")
        url = (
            f"{self.garmin_connect_metrics_base_url}/heataltitudeacclimation/"
            f"{aggregation}/{start}/{end}"
        )
        logger.debug("Requesting heat/altitude acclimation range")
        return self.connectapi(url)

    def get_cycling_ability(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the latest Cycling Ability profile as of ``cdate`` (default today).

        GET /metrics-service/metrics/cycling-ability/latest?calendarDate=.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_metrics_base_url}/cycling-ability/latest"
        logger.debug("Requesting cycling ability")
        return self.connectapi(url, params={"calendarDate": cdate})

    def get_cycling_ability_range(
        self, start: str, end: str, aggregation: str = "DAILY"
    ) -> dict[str, Any]:
        """Return Cycling Ability history (``cyclingAbilitiesMap`` keyed by date).

        GET /metrics-service/metrics/cycling-ability?startDate&endDate&aggregation.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_metrics_base_url}/cycling-ability"
        params = {
            "startDate": start,
            "endDate": end,
            "aggregation": aggregation.strip().upper(),
        }
        logger.debug("Requesting cycling ability range")
        return self.connectapi(url, params=params)

    def get_running_economy(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the latest Running Economy score as of ``cdate`` (default today).

        GET /metrics-service/metrics/runningeconomy/latest/{date}. Empty dict
        when the account has no running-economy capable device.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_metrics_base_url}/runningeconomy/latest/{cdate}"
        logger.debug("Requesting running economy")
        return self.connectapi(url)

    def get_running_economy_range(
        self, start: str, end: str, aggregation: str = "daily"
    ) -> list[dict[str, Any]]:
        """Return Running Economy history for a date range.

        GET /metrics-service/metrics/runningeconomy/{daily|weekly}?startDate&endDate.
        """
        start, end = _validate_date_range(start, end)
        if aggregation not in {"daily", "weekly"}:
            raise ValueError("aggregation must be 'daily' or 'weekly'")
        url = f"{self.garmin_connect_metrics_base_url}/runningeconomy/{aggregation}"
        logger.debug("Requesting running economy range")
        return self.connectapi(url, params={"startDate": start, "endDate": end})

    def get_stamina_curve(
        self, cdate: str | None = None, sport_type: str = "running"
    ) -> dict[str, Any]:
        """Return the latest stamina curve for ``sport_type`` (``running``/``cycling``).

        GET /metrics-service/metrics/stamina-curve/latest?calendarDate&sportType.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_metrics_base_url}/stamina-curve/latest"
        params = {"calendarDate": cdate, "sportType": sport_type.strip().lower()}
        logger.debug("Requesting stamina curve")
        return self.connectapi(url, params=params)

    def update_heart_rate_zones(self, zones: list[dict[str, Any]]) -> Any:
        """Write heart rate zones for one or more sports.

        PUT /biometric-service/heartRateZones/ with a list of the per-sport
        zone objects as returned by :meth:`get_heart_rate_zones_v2` (fields
        ``sport``, ``trainingMethod`` HR_MAX | HR_RESERVE | LACTATE_THRESHOLD,
        ``maxHeartRateUsed``, ``restingHeartRateUsed``,
        ``lactateThresholdHeartRateUsed``, ``zone1Floor`` … ``zone5Floor``).
        Read the current objects, change the fields you need and pass only the
        changed sports. Verified live with an unchanged object (204).
        """
        if (
            not isinstance(zones, list)
            or not zones
            or not all(isinstance(z, dict) for z in zones)
        ):
            raise ValueError("zones must be a non-empty list of zone objects")
        url = f"{self.garmin_connect_biometric_service_url}/heartRateZones/"
        logger.debug("Updating heart rate zones for %d sport(s)", len(zones))
        return self._json_or_none(self.client.put("connectapi", url, json=zones))

    def update_power_zones(self, zones: list[dict[str, Any]]) -> Any:
        """Write power zones for one or more sports.

        PUT /biometric-service/powerZones/all with a list of the per-sport
        objects as returned by :meth:`get_power_zones` (``sport``,
        ``functionalThresholdPower``, ``zone1Floor`` … ``zone7Floor``).
        Verified live with the unchanged list (204).
        """
        if (
            not isinstance(zones, list)
            or not zones
            or not all(isinstance(z, dict) for z in zones)
        ):
            raise ValueError("zones must be a non-empty list of zone objects")
        url = f"{self.garmin_connect_biometric_service_url}/powerZones/all"
        logger.debug("Updating power zones for %d sport(s)", len(zones))
        return self._json_or_none(self.client.put("connectapi", url, json=zones))

    def get_heart_rate_zones_v2(
        self, generate_defaults: bool = False
    ) -> list[dict[str, Any]]:
        """Return heart rate zones per sport from the v2 endpoint the web app uses.

        GET /biometric-service/heartRateZones/v2?generateDefaults=.
        """
        url = f"{self.garmin_connect_biometric_service_url}/heartRateZones/v2"
        params = {"generateDefaults": str(bool(generate_defaults)).lower()}
        logger.debug("Requesting heart rate zones (v2)")
        return self.connectapi(url, params=params)

    def get_biometric_stats(
        self,
        start: str,
        end: str,
        aggregation: str = "daily",
        user_first_day: str = "monday",
    ) -> list[dict[str, Any]]:
        """Return aggregated biometric statistics (weight, body fat, LT, ...) per period.

        GET /biometric-service/stats?aggregation&userFirstDay&startDate&endDate.
        """
        start, end = _validate_date_range(start, end)
        if aggregation not in {"daily", "weekly", "monthly", "yearly"}:
            raise ValueError("aggregation must be daily, weekly, monthly or yearly")
        url = f"{self.garmin_connect_biometric_service_url}/stats"
        params = {
            "aggregation": aggregation,
            "userFirstDay": user_first_day.strip().lower(),
            "startDate": start,
            "endDate": end,
        }
        logger.debug("Requesting biometric stats")
        return self.connectapi(url, params=params)

    def get_critical_swim_speed(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the latest Critical Swim Speed as of ``cdate`` (default today).

        GET /biometric-service/criticalSwimSpeed/latest/{date}. Empty dict when
        no CSS has been recorded.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_biometric_service_url}/criticalSwimSpeed/latest/{cdate}"
        logger.debug("Requesting critical swim speed")
        return self.connectapi(url)

    def get_critical_swim_speed_range(
        self, start: str, end: str, aggregation: str | None = None
    ) -> list[dict[str, Any]]:
        """Return Critical Swim Speed history for a date range.

        GET /biometric-service/criticalSwimSpeed/range/{start}/{end}[?aggregation].
        """
        start, end = _validate_date_range(start, end)
        url = (
            f"{self.garmin_connect_biometric_service_url}/criticalSwimSpeed/range/"
            f"{start}/{end}"
        )
        params = {"aggregation": aggregation} if aggregation else None
        logger.debug("Requesting critical swim speed range")
        return self.connectapi(url, params=params)

    def get_glucose_data(self, cdate: str) -> dict[str, Any]:
        """Return logged glucose readings for a day (``glucoseList``).

        GET /biometric-service/biometric/glucose/{date}.
        """
        cdate = _validate_date_format(cdate, "cdate")
        url = f"{self.garmin_connect_biometric_service_url}/biometric/glucose/{cdate}"
        logger.debug("Requesting glucose data")
        return self.connectapi(url)

    def get_glucose_data_range(self, start: str, end: str) -> dict[str, Any]:
        """Return logged glucose readings for a date range.

        GET /biometric-service/biometric/glucose/{start}/{end}.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_biometric_service_url}/biometric/glucose/{start}/{end}"
        logger.debug("Requesting glucose data range")
        return self.connectapi(url)

    def get_current_biometrics(self) -> dict[str, Any]:
        """Return the current biometric profile (height, weight, VO2 max, LT, FTP).

        GET /userprofile-service/biometric/current/{displayName}.
        """
        url = (
            f"{self.garmin_connect_userprofile_service_url}/biometric/current/"
            f"{self._require_display_name()}"
        )
        logger.debug("Requesting current biometrics")
        return self.connectapi(url)

    def get_power_curve(
        self, start: str, end: str, sport: str = "cycling"
    ) -> dict[str, Any]:
        """Return the power curve (best power per duration) for a date range.

        GET /fitnessstats-service/powerCurve?startDate&endDate&sport.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_fitnessstats_service_url}/powerCurve"
        params = {"startDate": start, "endDate": end, "sport": sport.strip().lower()}
        logger.debug("Requesting power curve")
        return self.connectapi(url, params=params)

    def get_one_rep_max(
        self, cdate: str | None = None, exercise_type: str | None = None
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Return current estimated one-rep-max values (strength training).

        GET /fitnessstats-service/vbt-stats/one-rep-max/current/{date} for all
        exercises, or .../one-rep-max/{exerciseType}/current/{date} for one.
        """
        cdate = self._date_or_today(cdate)
        base = f"{self.garmin_connect_fitnessstats_service_url}/vbt-stats/one-rep-max"
        if exercise_type:
            url = f"{base}/{exercise_type.strip().upper()}/current/{cdate}"
        else:
            url = f"{base}/current/{cdate}"
        logger.debug("Requesting one-rep-max estimates")
        return self.connectapi(url)

    def get_one_rep_max_history(
        self,
        exercise_type: str,
        start: str,
        end: str,
        aggregation: str = "daily",
    ) -> list[dict[str, Any]]:
        """Return one-rep-max history for an exercise (``daily`` or ``monthly``).

        GET /fitnessstats-service/vbt-stats/one-rep-max/{exerciseType}/{daily|monthly}
        ?startDate&endDate.
        """
        start, end = _validate_date_range(start, end)
        if aggregation not in {"daily", "monthly"}:
            raise ValueError("aggregation must be 'daily' or 'monthly'")
        url = (
            f"{self.garmin_connect_fitnessstats_service_url}/vbt-stats/one-rep-max/"
            f"{exercise_type.strip().upper()}/{aggregation}"
        )
        logger.debug("Requesting one-rep-max history")
        return self.connectapi(url, params={"startDate": start, "endDate": end})

    def get_fitness_age_details(self, cdate: str | None = None) -> dict[str, Any]:
        """Return Fitness Age with its components and achievable targets.

        GET /fitnessage-service/fitnessage/v2/{date} — the newer, richer
        variant of ``get_fitnessage_data`` the web app's Achievements card uses.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_fitnessage_service_url}/fitnessage/v2/{cdate}"
        logger.debug("Requesting fitness age details")
        return self.connectapi(url)

    def get_fitness_age_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return daily Fitness Age history (fitness age, RHR, body fat, ...).

        GET /fitnessage-service/stats/daily/{start}/{end}.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_fitnessage_service_url}/stats/daily/{start}/{end}"
        logger.debug("Requesting fitness age daily history")
        return self.connectapi(url)

    def get_fitness_age_weekly(
        self, end: str | None = None, weeks: int = 52
    ) -> list[dict[str, Any]]:
        """Return weekly Fitness Age history for ``weeks`` weeks ending at ``end``.

        GET /fitnessage-service/stats/weekly/{endDate}/{numberOfWeeks}.
        """
        end = self._date_or_today(end, "end")
        weeks = _validate_positive_integer(weeks, "weeks")
        url = f"{self.garmin_connect_fitnessage_service_url}/stats/weekly/{end}/{weeks}"
        logger.debug("Requesting fitness age weekly history")
        return self.connectapi(url)

    def get_spo2_acclimation_data(self, cdate: str | None = None) -> dict[str, Any]:
        """Return daily pulse ox readings together with acclimation values.

        GET /wellness-service/wellness/daily/spo2acclimation/{date} — the
        endpoint the web app now uses for the Pulse Ox page; a superset of
        ``get_spo2_data``.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_wellness_url}/daily/spo2acclimation/{cdate}"
        logger.debug("Requesting SpO2 acclimation data")
        return self.connectapi(url)

    def get_acclimation_stats(self, start: str, end: str) -> dict[str, Any]:
        """Return SpO2 acclimation statistics over a date range.

        GET /wellness-service/stats/daily/acclimation?fromDate&untilDate.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_wellness_stats_url}/daily/acclimation"
        logger.debug("Requesting acclimation stats")
        return self.connectapi(url, params={"fromDate": start, "untilDate": end})

    def get_activity_power_curve(self, activity_id: int | str) -> dict[str, Any]:
        """Return the power curve of one activity (empty without power data).

        GET /activity-service/activity/{activityId}/powerCurve.
        """
        return self._activity_subresource(activity_id, "powerCurve")
