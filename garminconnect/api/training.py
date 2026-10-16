"""Training plans, calendar events, courses and PDF report export."""

import re
from datetime import date
from pathlib import Path
from typing import Any

from ..exceptions import GarminConnectNotFoundError
from ._common import (
    _coerce_positive_id,
    _validate_date_format,
    _validate_date_range,
    _validate_non_negative_integer,
    _validate_positive_integer,
    logger,
)
from .base import GarminBase


class TrainingMixin(GarminBase):
    """Training plans, calendar events, courses and PDF report export."""

    def get_active_training_plans(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the training plans active on a date (``trainingPlanList``).

        GET /trainingplan-service/trainingplan/active-plans?startDate=.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_training_plan_url}/active-plans"
        logger.debug("Requesting active training plans")
        return self.connectapi(url, params={"startDate": cdate})

    def get_training_plan_tasks(self, plan_id: int | str, locale: str = "en") -> Any:
        """Return the workout tasks of a training plan.

        GET /trainingplan-service/trainingplan/tasks/{planId}?localeKey=.
        """
        plan_id = _coerce_positive_id(plan_id, "plan_id")
        url = f"{self.garmin_connect_training_plan_url}/tasks/{plan_id}"
        logger.debug("Requesting training plan tasks %s", plan_id)
        return self.connectapi(url, params={"localeKey": locale})

    def search_training_plans(
        self,
        start: int = 1,
        limit: int = 20,
        locale: str = "en",
        **filters: Any,
    ) -> dict[str, Any]:
        """Browse the Garmin training plan catalogue (``trainingPlanList``).

        POST /trainingplan-service/trainingplan/search?start&limit&locale
        [&types&subTypes&categories&version] with an empty form body, as
        the web app does. Extra keywords are passed through as query filters.
        """
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        params: dict[str, Any] = {"start": start, "limit": limit, "locale": locale}
        for key, value in filters.items():
            if value is not None:
                if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", key):
                    raise ValueError(f"invalid filter name: {key!r}")
                params[key] = value
        url = f"{self.garmin_connect_training_plan_url}/search"
        logger.debug("Searching training plans")
        return self.client.post(
            "connectapi",
            url,
            params=params,
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            api=True,
        )

    def schedule_training_plan(self, plan_id: int | str, start_date: str) -> Any:
        """Schedule a training plan from the catalogue starting on ``start_date``.

        GET /trainingplan-service/trainingplan/schedule/{planId}?startDate=
        (Garmin implements this as a side-effecting GET).
        """
        plan_id = _coerce_positive_id(plan_id, "plan_id")
        start_date = _validate_date_format(start_date, "start_date")
        url = f"{self.garmin_connect_training_plan_url}/schedule/{plan_id}"
        logger.debug("Scheduling training plan %s from %s", plan_id, start_date)
        return self.connectapi(url, params={"startDate": start_date})

    def delete_training_plan(self, plan_id: int | str) -> Any:
        """Remove a scheduled training plan from the calendar.

        DELETE /trainingplan-service/trainingplan/trainingplan/{planId}.
        """
        plan_id = _coerce_positive_id(plan_id, "plan_id")
        url = f"{self.garmin_connect_training_plan_url}/trainingplan/{plan_id}"
        logger.debug("Deleting training plan %s", plan_id)
        return self._json_or_none(self.client.delete("connectapi", url))

    def get_calendar_year(self, year: int | str) -> dict[str, Any]:
        """Return the year overview (which days have items).

        GET /calendar-service/year/{year}.
        """
        year = _coerce_positive_id(year, "year")
        if year < 2000:
            raise ValueError(f"year must be 2000 or later, got: {year}")
        url = f"{self.garmin_connect_calendar_url}/year/{year}"
        logger.debug("Requesting calendar year %s", year)
        return self.connectapi(url)

    def get_calendar_week(
        self, cdate: str | None = None, first_day_of_week: int = 1
    ) -> dict[str, Any]:
        """Return the calendar items of the week containing ``cdate``.

        GET /calendar-service/year/{y}/month/{m0}/day/{d}/start/{firstDayOfWeek}
        — month is 0-based like the web app sends it; ``first_day_of_week`` is
        0 for Sunday, 1 for Monday (default), 6 for Saturday.
        """
        cdate = self._date_or_today(cdate)
        if first_day_of_week not in range(7):
            raise ValueError("first_day_of_week must be 0 (Sunday) .. 6 (Saturday)")
        d = date.fromisoformat(cdate)
        url = (
            f"{self.garmin_connect_calendar_url}/year/{d.year}/month/{d.month - 1}/"
            f"day/{d.day}/start/{first_day_of_week}"
        )
        logger.debug("Requesting calendar week of %s", cdate)
        return self.connectapi(url)

    def get_calendar_events(self, start: str, end: str) -> list[dict[str, Any]]:
        """Return race / goal events between two dates.

        GET /calendar-service/events?startDate&endDate.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_calendar_url}/events"
        logger.debug("Requesting calendar events")
        return self.connectapi(url, params={"startDate": start, "endDate": end})

    def get_upcoming_events(
        self, days_forward: int = 90, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Return upcoming race / goal events.

        GET /calendar-service/events/upcoming?numDaysForward&limit.
        """
        days_forward = _validate_positive_integer(days_forward, "days_forward")
        limit = _validate_positive_integer(limit, "limit")
        url = f"{self.garmin_connect_calendar_url}/events/upcoming"
        logger.debug("Requesting upcoming events")
        return self.connectapi(
            url, params={"numDaysForward": days_forward, "limit": limit}
        )

    def get_primary_event(self) -> dict[str, Any] | None:
        """Return the primary (focus) race event, or None when there is none.

        GET /calendar-service/event/primary (204/404 mean no primary event).
        """
        url = f"{self.garmin_connect_calendar_url}/event/primary"
        logger.debug("Requesting primary event")
        try:
            return self.connectapi(url) or None
        except GarminConnectNotFoundError:
            return None

    def get_calendar_event(self, event_id: int | str) -> dict[str, Any]:
        """Return one calendar event.

        GET /calendar-service/event/{eventId}.
        """
        event_id = _coerce_positive_id(event_id, "event_id")
        url = f"{self.garmin_connect_calendar_url}/event/{event_id}"
        logger.debug("Requesting calendar event %s", event_id)
        return self.connectapi(url)

    def create_calendar_event(self, event: dict[str, Any]) -> Any:
        """Create a race / goal event from a full event object (see ``get_calendar_event``).

        POST /calendar-service/event.
        """
        if not isinstance(event, dict) or not event:
            raise ValueError("event must be a non-empty dictionary")
        url = f"{self.garmin_connect_calendar_url}/event"
        logger.debug("Creating calendar event")
        return self.client.post("connectapi", url, json=event, api=True)

    def update_calendar_event(self, event_id: int | str, event: dict[str, Any]) -> Any:
        """Update a calendar event with a full event object.

        PUT /calendar-service/event/{eventId}.
        """
        event_id = _coerce_positive_id(event_id, "event_id")
        if not isinstance(event, dict) or not event:
            raise ValueError("event must be a non-empty dictionary")
        url = f"{self.garmin_connect_calendar_url}/event/{event_id}"
        logger.debug("Updating calendar event %s", event_id)
        return self._json_or_none(self.client.put("connectapi", url, json=event))

    def delete_calendar_event(self, event_id: int | str) -> Any:
        """Delete a calendar event.

        DELETE /calendar-service/event/{eventId}.
        """
        event_id = _coerce_positive_id(event_id, "event_id")
        url = f"{self.garmin_connect_calendar_url}/event/{event_id}"
        logger.debug("Deleting calendar event %s", event_id)
        return self._json_or_none(self.client.delete("connectapi", url))

    def move_calendar_item(
        self,
        item_type: str,
        item_id: int | str,
        cdate: str,
        item: dict[str, Any] | None = None,
    ) -> Any:
        """Move a calendar item (workout, note, ...) to another date.

        PUT /calendar-service/calendarItem/{itemType}/{id}/date/{date} with
        the item plus its new ``date``; ``item_type`` is the calendar item's
        ``itemType`` (e.g. ``workout``).
        """
        item_id = _coerce_positive_id(item_id, "item_id")
        cdate = _validate_date_format(cdate, "cdate")
        if not re.fullmatch(r"[A-Za-z_-]+", item_type or ""):
            raise ValueError("item_type must be an item type key such as 'workout'")
        url = f"{self.garmin_connect_calendar_url}/calendarItem/{item_type}/{item_id}/date/{cdate}"
        payload = {**(item or {}), "date": cdate}
        logger.debug("Moving calendar item %s/%s to %s", item_type, item_id, cdate)
        return self._json_or_none(self.client.put("connectapi", url, json=payload))

    def create_calendar_note(
        self, cdate: str, name: str, content: str = ""
    ) -> dict[str, Any]:
        """Add a note to a calendar day.

        POST /calendar-service/note ``{"noteName", "content", "date"}``;
        returns the note with its ``id``. Verified live.
        """
        cdate = _validate_date_format(cdate, "cdate")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        url = f"{self.garmin_connect_calendar_url}/note"
        payload = {"noteName": name, "content": content, "date": cdate}
        logger.debug("Creating calendar note on %s", cdate)
        return self.client.post("connectapi", url, json=payload, api=True)

    def update_calendar_note(
        self, note_id: int | str, cdate: str, name: str, content: str = ""
    ) -> Any:
        """Change a calendar note's date, name or content.

        PUT /calendar-service/note/{id} ``{"id", "noteName", "content", "date"}``.
        """
        note_id = _coerce_positive_id(note_id, "note_id")
        cdate = _validate_date_format(cdate, "cdate")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        url = f"{self.garmin_connect_calendar_url}/note/{note_id}"
        payload = {"id": note_id, "noteName": name, "content": content, "date": cdate}
        logger.debug("Updating calendar note %s", note_id)
        return self._json_or_none(self.client.put("connectapi", url, json=payload))

    def delete_calendar_note(self, note_id: int | str) -> Any:
        """Delete a calendar note.

        DELETE /calendar-service/note/{id}. Verified live.
        """
        note_id = _coerce_positive_id(note_id, "note_id")
        url = f"{self.garmin_connect_calendar_url}/note/{note_id}"
        logger.debug("Deleting calendar note %s", note_id)
        return self._json_or_none(self.client.delete("connectapi", url))

    def get_courses(self) -> list[dict[str, Any]]:
        """Return the user's courses.

        GET /course-service/course/owner/{displayName}.
        """
        url = f"{self.garmin_connect_course_url}/owner/{self._require_display_name()}"
        logger.debug("Requesting courses")
        return self.connectapi(url)

    def get_course(self, course_id: int | str) -> dict[str, Any]:
        """Return a course with its geo points.

        GET /course-service/course/{courseId}.
        """
        course_id = _coerce_positive_id(course_id, "course_id")
        url = f"{self.garmin_connect_course_url}/{course_id}"
        logger.debug("Requesting course %s", course_id)
        return self.connectapi(url)

    def create_course(self, course: dict[str, Any]) -> Any:
        """Create a course from a full course object (see ``get_course``).

        POST /course-service/course.
        """
        if not isinstance(course, dict) or not course:
            raise ValueError("course must be a non-empty dictionary")
        logger.debug("Creating course")
        return self.client.post(
            "connectapi",
            self.garmin_connect_course_url,
            json=course,
            api=True,
            timeout=30,
        )

    def update_course(self, course_id: int | str, course: dict[str, Any]) -> Any:
        """Update a course with a full course object.

        PUT /course-service/course/{courseId}.
        """
        course_id = _coerce_positive_id(course_id, "course_id")
        if not isinstance(course, dict) or not course:
            raise ValueError("course must be a non-empty dictionary")
        url = f"{self.garmin_connect_course_url}/{course_id}"
        logger.debug("Updating course %s", course_id)
        return self._json_or_none(
            self.client.put("connectapi", url, json=course, timeout=30)
        )

    def delete_course(self, course_id: int | str) -> Any:
        """Delete a course.

        DELETE /course-service/course/{courseId}.
        """
        course_id = _coerce_positive_id(course_id, "course_id")
        url = f"{self.garmin_connect_course_url}/{course_id}"
        logger.debug("Deleting course %s", course_id)
        return self._json_or_none(self.client.delete("connectapi", url))

    def download_course(self, course_id: int | str, fmt: str = "gpx") -> bytes:
        """Download a course as GPX or FIT.

        GET /course-service/course/gpx/{courseId} or
        GET /course-service/course/fit/{courseId}/0?elevation=true.
        """
        course_id = _coerce_positive_id(course_id, "course_id")
        fmt = fmt.strip().lower()
        if fmt == "gpx":
            url = f"{self.garmin_connect_course_url}/gpx/{course_id}"
            params = None
        elif fmt == "fit":
            url = f"{self.garmin_connect_course_url}/fit/{course_id}/0"
            params = {"elevation": "true"}
        else:
            raise ValueError("fmt must be 'gpx' or 'fit'")
        logger.debug("Downloading course %s as %s", course_id, fmt)
        return self.download(url, params=params)

    def import_course(self, file_path: str) -> Any:
        """Import a course from a GPX, TCX or FIT file.

        POST /course-service/course/import (multipart ``file``).
        """
        path = Path(file_path)
        if path.suffix.lower() not in {".gpx", ".tcx", ".fit"}:
            raise ValueError("file_path must be a .gpx, .tcx or .fit file")
        url = f"{self.garmin_connect_course_url}/import"
        logger.debug("Importing course from %s", path.name)
        with path.open("rb") as fh:
            return self.client.post(
                "connectapi", url, files={"file": (path.name, fh)}, api=True, timeout=60
            )

    def convert_activity_to_course(self, activity_id: int | str) -> dict[str, Any]:
        """Return a course object built from an activity's track (not yet saved).

        GET /course-service/course/convert/activity/{activityId}; pass the
        result to ``create_course`` to save it.
        """
        activity_id = _coerce_positive_id(activity_id, "activity_id")
        url = f"{self.garmin_connect_course_url}/convert/activity/{activity_id}"
        logger.debug("Converting activity %s to course", activity_id)
        return self.connectapi(url)

    def get_course_favorites(self) -> list[dict[str, Any]]:
        """Return courses marked as favorite.

        GET /course-service/course/favorites.
        """
        url = f"{self.garmin_connect_course_url}/favorites"
        logger.debug("Requesting course favorites")
        return self.connectapi(url)

    def set_course_favorite(self, course_id: int | str, favorite: bool = True) -> Any:
        """Mark or unmark a course as favorite.

        POST /course-service/course/favorites ``{"courseId": id}`` or
        DELETE /course-service/course/favorites/course/{courseId}.
        """
        course_id = _coerce_positive_id(course_id, "course_id")
        if favorite:
            url = f"{self.garmin_connect_course_url}/favorites"
            logger.debug("Adding course %s to favorites", course_id)
            return self._json_or_none(
                self.client.post("connectapi", url, json={"courseId": course_id})
            )
        url = f"{self.garmin_connect_course_url}/favorites/course/{course_id}"
        logger.debug("Removing course %s from favorites", course_id)
        return self._json_or_none(self.client.delete("connectapi", url))

    def get_pace_bands(self) -> list[dict[str, Any]]:
        """Return the user's PacePro pace bands.

        GET /course-service/pacebands.
        """
        logger.debug("Requesting pace bands")
        return self.connectapi(self.garmin_connect_pacebands_url)

    def request_report(
        self,
        category: str,
        start: str,
        end: str,
        options: dict[str, Any] | None = None,
        locale: str = "en-US",
    ) -> dict[str, Any]:
        """Start a PDF report export and return ``{"reportId", "estimatedTimeForStatusCheck"}``.

        POST /reportexport-service/export/init/{category}/{start}/{end}?locale=.
        Categories seen in the web app: ``bloodPressure`` (options
        ``{"contentToSkip": [], "reportSubCategory": "DAILY|SEVEN_DAYS|
        FOUR_WEEKS|YEARLY", "reportFormat": "PDF", "requestedDateFormatKey":
        ...}``) and ``wellnessactivity`` (``{"supplementalId": <snapshot
        uuid>}``). Poll ``get_report_status`` until ``progress.status`` is
        ``READY``, then ``download_report``.
        """
        if not re.fullmatch(r"[A-Za-z]+", category or ""):
            raise ValueError("category must be an alphabetic report category key")
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_report_export_url}/init/{category}/{start}/{end}"
        logger.debug("Requesting %s report", category)
        return self.client.post(
            "connectapi", url, params={"locale": locale}, json=options or {}, api=True
        )

    def get_report_status(self, report_id: str) -> dict[str, Any]:
        """Return the progress of a report export (``progress.status``).

        GET /reportexport-service/export/reportStatus/{reportId}.
        """
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(report_id)):
            raise ValueError("report_id must be an alphanumeric identifier")
        url = f"{self.garmin_connect_report_export_url}/reportStatus/{report_id}"
        logger.debug("Requesting report status %s", report_id)
        return self.connectapi(url)

    def download_report(self, report_id: str) -> bytes:
        """Download a finished report as PDF bytes.

        GET /reportexport-service/export/reportContent/{reportId}.
        """
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(report_id)):
            raise ValueError("report_id must be an alphanumeric identifier")
        url = f"{self.garmin_connect_report_export_url}/reportContent/{report_id}"
        logger.debug("Downloading report %s", report_id)
        return self.download(url)

    def get_training_plans(
        self,
        limit: int | None = None,
        start: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Return the user's training plans (``{"trainingPlanList": [...]}``).

        The web app always sends ``limit`` (50 on the overview page) and
        optionally ``start`` and ``status``; all three are passed through
        when given, otherwise the server defaults apply as before.
        """
        url = f"{self.garmin_connect_training_plan_url}/plans"
        params: dict[str, str] = {}
        if limit is not None:
            params["limit"] = str(_validate_positive_integer(limit, "limit"))
        if start is not None:
            params["start"] = str(_validate_non_negative_integer(start, "start"))
        if status is not None:
            if not isinstance(status, str) or not status.strip():
                raise ValueError("status must be a non-empty string")
            params["status"] = status.strip()
        logger.debug("Requesting training plans.")
        return self.connectapi(url, params=params or None)

    def get_training_plan_by_id(self, plan_id: int | str) -> dict[str, Any]:
        """Return details for a specific training plan."""
        plan_id = _coerce_positive_id(plan_id, "plan_id")

        url = f"{self.garmin_connect_training_plan_url}/phased/{plan_id}"
        logger.debug("Requesting training plan details for %s", plan_id)
        return self.connectapi(url)

    def get_adaptive_training_plan_by_id(self, plan_id: int | str) -> dict[str, Any]:
        """Return details for a specific adaptive training plan."""
        plan_id = _coerce_positive_id(plan_id, "plan_id")
        url = f"{self.garmin_connect_training_plan_url}/fbt-adaptive/{plan_id}"

        logger.debug("Requesting adaptive training plan details for %s", plan_id)
        return self.connectapi(url)
