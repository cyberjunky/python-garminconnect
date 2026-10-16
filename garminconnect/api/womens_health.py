"""Menstrual cycle and pregnancy tracking."""

from datetime import datetime
from typing import Any

from ._common import (
    DATE_FORMAT_STR,
    VALID_MENSTRUAL_DISCHARGE,
    VALID_MENSTRUAL_FLOW,
    VALID_MENSTRUAL_MOODS,
    VALID_MENSTRUAL_REPORT_CYCLES,
    VALID_MENSTRUAL_SEX_DRIVE,
    VALID_MENSTRUAL_SEXUAL_ACTIVITY,
    VALID_MENSTRUAL_SYMPTOMS,
    _clean_menstrual_daily_log,
    _fmt_ts_utc,
    _validate_date_format,
    _validate_date_group_list,
    _validate_menstrual_enum,
    _validate_menstrual_enum_list,
    _validate_positive_integer,
    logger,
)
from .base import GarminBase


class WomensHealthMixin(GarminBase):
    """Menstrual cycle and pregnancy tracking."""

    def get_menstrual_data_for_date(
        self, fordate: str, today_date: str | None = None
    ) -> dict[str, Any]:
        """Return the menstrual day view for a date.

        ``today_date`` is sent as ``todayDate`` like the web app always does
        (it defaults to today in the user's Garmin timezone); Garmin uses it to
        decide which days are predictions.
        """
        fordate = _validate_date_format(fordate, "fordate")
        if today_date is None:
            today_date = self.today().isoformat()
        today_date = _validate_date_format(today_date, "today_date")
        url = f"{self.garmin_connect_menstrual_dayview_url}/{fordate}"
        logger.debug("Requesting menstrual data for date %s", fordate)

        return self.connectapi(url, params={"todayDate": today_date})

    def get_menstrual_calendar_data(
        self, startdate: str, enddate: str
    ) -> dict[str, Any]:
        """Return summaries of cycles that have days between startdate and enddate.

        Garmin rejects windows of 92 inclusive days; keep the range at 90 days
        or fewer.
        """
        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        url = f"{self.garmin_connect_menstrual_calendar_url}/{startdate}/{enddate}"
        logger.debug(
            "Requesting menstrual data for dates %s through %s", startdate, enddate
        )

        return self.connectapi(url)

    def get_menstrual_last_confirmed(self, fordate: str) -> dict[str, Any]:
        """Return the last confirmed menstrual cycle as of ``fordate``."""
        fordate = _validate_date_format(fordate, "fordate")
        url = f"{self.garmin_connect_menstrual_lastconfirmed_url}/{fordate}"
        logger.debug("Requesting last confirmed menstrual cycle for %s", fordate)
        return self.connectapi(url)

    def get_menstrual_cycle_summary(self, fordate: str) -> dict[str, Any]:
        """Return the menstrual cycle summary for ``fordate``."""
        fordate = _validate_date_format(fordate, "fordate")
        url = f"{self.garmin_connect_menstrual_summary_url}/{fordate}"
        logger.debug("Requesting menstrual cycle summary for %s", fordate)
        return self.connectapi(url)

    def get_menstrual_reports(
        self,
        fordate: str,
        number_of_cycles: int = 6,
        *,
        next_report: bool = False,
        report_type: str = "CYCLE",
        today_calendar_date: str | None = None,
    ) -> dict[str, Any]:
        """Return menstrual cycle reports for 1, 6, or 12 cycles ending at date.

        Garmin only accepts ``number_of_cycles`` of 1, 6, or 12.
        """
        fordate = _validate_date_format(fordate, "fordate")
        if not isinstance(number_of_cycles, int) or isinstance(number_of_cycles, bool):
            raise ValueError("number_of_cycles must be an integer")
        if number_of_cycles not in VALID_MENSTRUAL_REPORT_CYCLES:
            raise ValueError(
                "number_of_cycles must be one of "
                f"{sorted(VALID_MENSTRUAL_REPORT_CYCLES)}, got: {number_of_cycles}"
            )
        if not isinstance(next_report, bool):
            raise ValueError("next_report must be a boolean")
        if not isinstance(report_type, str) or not report_type.strip():
            raise ValueError("report_type must be a non-empty string")
        if today_calendar_date is None:
            today_calendar_date = self.today().isoformat()
        today_calendar_date = _validate_date_format(
            today_calendar_date, "today_calendar_date"
        )
        url = (
            f"{self.garmin_connect_menstrual_reports_url}/{number_of_cycles}/{fordate}"
        )
        params = {
            "next": str(next_report).lower(),
            "reportType": report_type.strip(),
            "todayCalendarDate": today_calendar_date,
        }
        logger.debug(
            "Requesting menstrual reports for %s cycles ending %s",
            number_of_cycles,
            fordate,
        )
        return self.connectapi(url, params=params)

    def get_pregnancy_summary(self) -> dict[str, Any]:
        """Return pregnancy summary for the current user."""
        url = f"{self.garmin_connect_pregnancy_snapshot_url}"
        logger.debug("Requesting pregnancy snapshot data")

        return self.connectapi(url)

    def update_menstrual_daily_log(
        self,
        calendar_date: str,
        *,
        symptoms: list[str] | None = None,
        moods: list[str] | None = None,
        flow: str | None = None,
        discharge: list[str] | None = None,
        sex_drive: str | None = None,
        sexual_activity: str | None = None,
        notes: str | None = None,
        ovulation_day: bool | None = None,
    ) -> dict[str, Any]:
        """Replace the menstrual daily log for ``calendar_date``.

        This is a full-day snapshot, not a field-level merge. Garmin clears
        omitted lists and scalar enums (``flow``, ``sex_drive``,
        ``sexual_activity``). ``notes=None`` keeps the existing note;
        ``notes=""`` clears it. ``ovulation_day`` is always sent; omitting it
        is stored as ``false``.

        To change one field, read ``get_menstrual_data_for_date`` first and
        pass every value you want to keep. At least one log field must be
        provided so a no-argument call cannot wipe the day.
        """
        calendar_date = _validate_date_format(calendar_date, "calendar_date")
        if not any(
            value is not None
            for value in (
                symptoms,
                moods,
                flow,
                discharge,
                sex_drive,
                sexual_activity,
                notes,
                ovulation_day,
            )
        ):
            raise ValueError(
                "at least one daily-log field must be provided; "
                "omitted lists and scalars are cleared on the server"
            )
        if notes is not None and not isinstance(notes, str):
            raise ValueError("notes must be a string")
        if ovulation_day is not None and not isinstance(ovulation_day, bool):
            raise ValueError("ovulation_day must be a boolean")

        symptoms = _validate_menstrual_enum_list(
            symptoms, VALID_MENSTRUAL_SYMPTOMS, "symptoms"
        )
        moods = _validate_menstrual_enum_list(moods, VALID_MENSTRUAL_MOODS, "moods")
        discharge = _validate_menstrual_enum_list(
            discharge, VALID_MENSTRUAL_DISCHARGE, "discharge"
        )
        if (
            discharge is not None
            and "NO_DISCHARGE" in discharge
            and any(value != "NO_DISCHARGE" for value in discharge)
        ):
            raise ValueError("discharge cannot combine NO_DISCHARGE with other values")
        if flow is not None:
            flow = _validate_menstrual_enum(flow, VALID_MENSTRUAL_FLOW, "flow")
        if sex_drive is not None:
            sex_drive = _validate_menstrual_enum(
                sex_drive, VALID_MENSTRUAL_SEX_DRIVE, "sex_drive"
            )
        if sexual_activity is not None:
            sexual_activity = _validate_menstrual_enum(
                sexual_activity,
                VALID_MENSTRUAL_SEXUAL_ACTIVITY,
                "sexual_activity",
            )

        payload: dict[str, Any] = {
            "calendarDate": calendar_date,
            "symptoms": symptoms,
            "moods": moods,
            "flow": flow,
            "discharge": discharge,
            "sexDrive": sex_drive,
            "sexualActivity": sexual_activity,
            "notes": notes,
            "ovulationDay": False if ovulation_day is None else ovulation_day,
            "reportTimestamp": _fmt_ts_utc(),
        }
        if self.profile_id is not None:
            payload["userProfilePk"] = self.profile_id
        payload = _clean_menstrual_daily_log(payload)

        url = f"{self.garmin_connect_menstrual_dailylog_url}/{calendar_date}"
        logger.debug("Updating menstrual daily log for %s", calendar_date)
        return self.client.post("connectapi", url, json=payload, api=True)

    def update_menstrual_calendar(
        self,
        startdate: str,
        enddate: str,
        cycle_dates_lists: list[list[str]],
        *,
        today_calendar_date: str | None = None,
    ) -> dict[str, Any]:
        """Replace menstrual period dates in ``startdate``..``enddate``.

        ``cycle_dates_lists`` is the Garmin Connect calendar snapshot: each
        inner list is one period of consecutive YYYY-MM-DD dates. This is not
        a merge; omitted previously confirmed days in range are removed.
        Predicted cycles should not be posted as confirmed period dates.
        """
        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        start_day = datetime.strptime(startdate, DATE_FORMAT_STR).date()
        end_day = datetime.strptime(enddate, DATE_FORMAT_STR).date()
        if start_day > end_day:
            raise ValueError("startdate cannot be after enddate")
        cycle_dates_lists = _validate_date_group_list(
            cycle_dates_lists, "cycle_dates_lists"
        )
        for group_index, group in enumerate(cycle_dates_lists):
            for day_index, day in enumerate(group):
                parsed = datetime.strptime(day, DATE_FORMAT_STR).date()
                if parsed < start_day or parsed > end_day:
                    raise ValueError(
                        "cycle_dates_lists"
                        f"[{group_index}][{day_index}] must be within "
                        "startdate and enddate"
                    )
        if today_calendar_date is None:
            today_calendar_date = self.today().isoformat()
        today_calendar_date = _validate_date_format(
            today_calendar_date, "today_calendar_date"
        )

        payload: dict[str, Any] = {
            "todayCalendarDate": today_calendar_date,
            "startDate": startdate,
            "endDate": enddate,
            "reportTimestamp": _fmt_ts_utc(),
            "cycleDatesLists": cycle_dates_lists,
            "futureEditsByFE": True,
        }
        if self.profile_id is not None:
            payload["userProfilePk"] = self.profile_id

        logger.debug(
            "Updating menstrual calendar dates for %s through %s", startdate, enddate
        )
        return self.client.post(
            "connectapi",
            self.garmin_connect_menstrual_calendar_updates_url,
            json=payload,
            api=True,
        )

    def init_menstrual_cycle_setup(
        self,
        period_start_date: str,
        period_length: int,
        cycle_length: int,
    ) -> dict[str, Any]:
        """Initialize menstrual cycle tracking with the first confirmed period.

        Garmin Connect's first-run wizard also PUTs user menstrual settings
        in the same save. Call :meth:`update_menstrual_settings` separately
        when those tracking flags should change. Do not use this to edit an
        already configured account.
        """
        period_start_date = _validate_date_format(
            period_start_date, "period_start_date"
        )
        period_length = _validate_positive_integer(period_length, "period_length")
        cycle_length = _validate_positive_integer(cycle_length, "cycle_length")

        payload: dict[str, Any] = {
            "periodStartDate": period_start_date,
            "periodLength": period_length,
            "cycleLength": cycle_length,
            "reportTimestamp": _fmt_ts_utc(),
        }
        if self.profile_id is not None:
            payload["userProfilePk"] = self.profile_id

        logger.debug("Initializing menstrual cycle setup from %s", period_start_date)
        return self.client.post(
            "connectapi",
            self.garmin_connect_menstrual_init_cycle_setup_url,
            json=payload,
            api=True,
        )

    def confirm_menstrual_period_start(
        self,
        period_start_date: str,
        period_length: int,
        cycle_length: int,
        *,
        predicted_cycle: bool = False,
    ) -> dict[str, Any]:
        """Confirm a menstrual period start date, including a prediction.

        This can convert a predicted cycle into a confirmed period. Pass the
        lengths shown on that day summary rather than inventing new ones.
        """
        period_start_date = _validate_date_format(
            period_start_date, "period_start_date"
        )
        period_length = _validate_positive_integer(period_length, "period_length")
        cycle_length = _validate_positive_integer(cycle_length, "cycle_length")
        if not isinstance(predicted_cycle, bool):
            raise ValueError("predicted_cycle must be a boolean")

        payload: dict[str, Any] = {
            "periodStartDate": period_start_date,
            "periodLength": period_length,
            "cycleLength": cycle_length,
            "predictedCycle": predicted_cycle,
            "hasSpecifiedCycleLength": True,
            "hasSpecifiedPeriodLength": True,
            "reportTimestamp": _fmt_ts_utc(),
        }
        if self.profile_id is not None:
            payload["userProfilePk"] = self.profile_id

        url = f"{self.garmin_connect_menstrual_cycle_url}/{period_start_date}"
        logger.debug("Confirming menstrual period start date %s", period_start_date)
        return self.client.post("connectapi", url, json=payload, api=True)

    def update_menstrual_settings(
        self,
        settings: dict[str, Any],
        *,
        user_settings_id: int | None = None,
    ) -> dict[str, Any]:
        """Update ``userMenstrualCycleSettings`` on the user profile.

        ``settings`` overlays the current menstrual settings from
        :meth:`get_user_profile`. Omitted keys are preserved; passed keys
        replace stored values. Pregnancy-only fields are not modeled here.
        """
        if not isinstance(settings, dict) or not settings:
            raise ValueError("settings must be a non-empty dictionary")
        if user_settings_id is not None:
            user_settings_id = _validate_positive_integer(
                user_settings_id, "user_settings_id"
            )

        profile = self.get_user_profile()
        current: dict[str, Any] = {}
        if isinstance(profile, dict):
            stored = profile.get("userMenstrualCycleSettings")
            if isinstance(stored, dict):
                current = dict(stored)
            if user_settings_id is None:
                profile_settings_id = profile.get("id")
                if isinstance(profile_settings_id, int) and not isinstance(
                    profile_settings_id, bool
                ):
                    user_settings_id = profile_settings_id

        payload: dict[str, Any] = {"userMenstrualCycleSettings": current | settings}
        if user_settings_id is not None:
            payload["id"] = user_settings_id

        logger.debug("Updating menstrual cycle tracking settings")
        return self.client.put(
            "connectapi",
            self.garmin_connect_user_settings_url,
            json=payload,
            api=True,
        )
