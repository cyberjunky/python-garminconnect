"""Workout library, typed workout uploads, scheduling and pushing to devices."""

from typing import Any

from ._common import (
    VALID_WORKOUT_ORDER_BY,
    _coerce_positive_id,
    _validate_date_format,
    _validate_date_range,
    _validate_non_negative_integer,
    _validate_positive_integer,
    logger,
)
from .base import GarminBase

_NO_WORKOUT_SPORT_TYPE = (
    "Garmin has no {sport} workout sport type, so the workout would be stored "
    "without one. Use a sport type from get_workout_types()['workoutSportTypes'] "
    "instead, such as running or other."
)


class WorkoutsMixin(GarminBase):
    """Workout library, typed workout uploads, scheduling and pushing to devices."""

    def get_workouts(
        self,
        start: int = 0,
        limit: int = 100,
        *,
        my_workouts_only: bool | None = None,
        shared_workouts_only: bool | None = None,
        include_atp: bool | None = None,
        order_by: str | None = None,
        order_seq: str | None = None,
        sport_type_keys: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return workouts starting at offset `start` with at most `limit` results.

        The keyword filters mirror the Garmin Connect workout library page and
        are only sent when given:

        Args:
            my_workouts_only / shared_workouts_only: restrict to own or shared
                workouts (the web app sends both as ``false`` by default).
            include_atp: include adaptive-training-plan workouts.
            order_by: ``WORKOUT_NAME``, ``WORKOUT_SPORT_PK``, ``CREATED_DATE``,
                ``UPDATE_DATE`` or ``WORKOUT_PROVIDER``.
            order_seq: ``ASC`` or ``DESC``.
            sport_type_keys: e.g. ``["running", "cycling"]``; sent as repeated
                ``sportTypeKey`` parameters.

        """
        url = f"{self.garmin_workouts}/workouts"
        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        logger.debug("Requesting workouts from %d with limit %d", start, limit)
        params: dict[str, Any] = {"start": start, "limit": limit}
        for key, value in (
            ("myWorkoutsOnly", my_workouts_only),
            ("sharedWorkoutsOnly", shared_workouts_only),
            ("includeAtp", include_atp),
        ):
            if value is not None:
                params[key] = str(bool(value)).lower()
        if order_by is not None:
            order_by = order_by.strip().upper()
            if order_by not in VALID_WORKOUT_ORDER_BY:
                raise ValueError(
                    f"order_by must be one of {sorted(VALID_WORKOUT_ORDER_BY)}"
                )
            params["orderBy"] = order_by
        if order_seq is not None:
            order_seq = order_seq.strip().upper()
            if order_seq not in {"ASC", "DESC"}:
                raise ValueError("order_seq must be 'ASC' or 'DESC'")
            params["orderSeq"] = order_seq
        if sport_type_keys:
            params["sportTypeKey"] = [str(k).strip().lower() for k in sport_type_keys]
        return self.connectapi(url, params=params)

    def get_workout_by_id(self, workout_id: int | str) -> dict[str, Any]:
        """Return one workout from the library."""
        workout_id = _coerce_positive_id(workout_id, "workout_id")
        url = f"{self.garmin_workouts}/workout/{workout_id}"
        return self.connectapi(url)

    def delete_workout(self, workout_id: int | str) -> Any:
        """Delete a workout template from the workout library."""
        workout_id = _coerce_positive_id(workout_id, "workout_id")
        url = f"{self.garmin_workouts}/workout/{workout_id}"
        logger.debug("Deleting workout %s", workout_id)
        return self.client.delete("connectapi", url, api=True)

    def download_workout(self, workout_id: int | str) -> bytes:
        """Download a workout as a FIT file."""
        workout_id = _coerce_positive_id(workout_id, "workout_id")
        url = f"{self.garmin_workouts}/workout/FIT/{workout_id}"
        logger.debug("Downloading workout from %s", url)

        return self.download(url)

    def upload_workout(
        self, workout_json: dict[str, Any] | list[Any] | str
    ) -> dict[str, Any]:
        """Upload a workout from a JSON dict or string."""
        url = f"{self.garmin_workouts}/workout"
        logger.debug("Uploading workout using %s", url)

        if isinstance(workout_json, str):
            import json as _json

            try:
                payload = _json.loads(workout_json)
            except Exception as e:
                raise ValueError(f"invalid workout_json string: {e}") from e
        else:
            payload = workout_json
        if not isinstance(payload, dict | list):
            raise ValueError("workout_json must be a JSON object or array")
        return self.client.post("connectapi", url, json=payload, api=True)

    def update_workout(
        self, workout_id: int | str, workout_json: dict[str, Any] | str
    ) -> dict[str, Any]:
        """Replace an existing workout in place, keeping its id.

        Garmin's workout endpoint replaces the whole workout via PUT, so
        ``workout_json`` must be the complete structure (as returned by
        ``get_workout_by_id`` or built the same way as for ``upload_workout``).
        The workout keeps its id, so any calendar schedules pointing at it stay
        valid. ``workoutId`` in the body is forced to match ``workout_id``.
        """
        workout_id = _coerce_positive_id(workout_id, "workout_id")
        url = f"{self.garmin_workouts}/workout/{workout_id}"
        logger.debug("Updating workout using %s", url)

        if isinstance(workout_json, str):
            import json as _json

            try:
                payload = _json.loads(workout_json)
            except Exception as e:
                raise ValueError(f"invalid workout_json string: {e}") from e
        else:
            payload = workout_json
        if not isinstance(payload, dict):
            raise ValueError("workout_json must be a JSON object")
        body = payload | {"workoutId": workout_id}
        return self.client.put("connectapi", url, json=body, api=True)

    def upload_running_workout(self, workout: Any) -> dict[str, Any]:
        """Upload a typed running workout.

        Args:
            workout: RunningWorkout instance from garminconnect.workout

        Returns:
            Dictionary containing the uploaded workout data

        Example:
            from garminconnect.workout import RunningWorkout, WorkoutSegment, create_warmup_step

            workout = RunningWorkout(
                workoutName="Easy Run",
                estimatedDurationInSecs=1800,
                workoutSegments=[
                    WorkoutSegment(
                        segmentOrder=1,
                        sportType={"sportTypeId": 1, "sportTypeKey": "running"},
                        workoutSteps=[create_warmup_step(300.0)]
                    )
                ]
            )
            api.upload_running_workout(workout)

        """
        try:
            from ..workout import RunningWorkout

            if not isinstance(workout, RunningWorkout):
                raise TypeError("workout must be a RunningWorkout instance")
            return self.upload_workout(workout.to_dict())
        except ImportError:
            raise ImportError(
                "Pydantic is required for typed workouts. "
                "Install it with: pip install pydantic or pip install garminconnect[workout]"
            ) from None

    def upload_cycling_workout(self, workout: Any) -> dict[str, Any]:
        """Upload a typed cycling workout.

        Args:
            workout: CyclingWorkout instance from garminconnect.workout

        Returns:
            Dictionary containing the uploaded workout data

        Example:
            from garminconnect.workout import CyclingWorkout, WorkoutSegment, create_warmup_step

            workout = CyclingWorkout(
                workoutName="Interval Ride",
                estimatedDurationInSecs=3600,
                workoutSegments=[
                    WorkoutSegment(
                        segmentOrder=1,
                        sportType={"sportTypeId": 2, "sportTypeKey": "cycling"},
                        workoutSteps=[create_warmup_step(600.0)]
                    )
                ]
            )
            api.upload_cycling_workout(workout)

        """
        try:
            from ..workout import CyclingWorkout

            if not isinstance(workout, CyclingWorkout):
                raise TypeError("workout must be a CyclingWorkout instance")
            return self.upload_workout(workout.to_dict())
        except ImportError:
            raise ImportError(
                "Pydantic is required for typed workouts. "
                "Install it with: pip install pydantic or pip install garminconnect[workout]"
            ) from None

    def upload_swimming_workout(self, workout: Any) -> dict[str, Any]:
        """Upload a typed swimming workout.

        Args:
            workout: SwimmingWorkout instance from garminconnect.workout

        Returns:
            Dictionary containing the uploaded workout data

        """
        try:
            from ..workout import SwimmingWorkout

            if not isinstance(workout, SwimmingWorkout):
                raise TypeError("workout must be a SwimmingWorkout instance")
            return self.upload_workout(workout.to_dict())
        except ImportError:
            raise ImportError(
                "Pydantic is required for typed workouts. "
                "Install it with: pip install pydantic or pip install garminconnect[workout]"
            ) from None

    def upload_walking_workout(self, workout: Any) -> dict[str, Any]:  # noqa: ARG002
        """Not supported: Garmin has no walking workout sport type; always raises.

        Garmin's workout dictionary (``get_workout_types()["workoutSportTypes"]``)
        has no walking type, so an uploaded walking workout was stored without a
        sport type. Build the workout with a type Garmin supports instead, for
        example ``RunningWorkout`` or a workout with the ``other`` sport type
        sent through :meth:`upload_workout`.

        Raises:
            ValueError: always.

        """
        raise ValueError(_NO_WORKOUT_SPORT_TYPE.format(sport="walking"))

    def upload_hiking_workout(self, workout: Any) -> dict[str, Any]:  # noqa: ARG002
        """Not supported: Garmin has no hiking workout sport type; always raises.

        Garmin's workout dictionary (``get_workout_types()["workoutSportTypes"]``)
        has no hiking type, so an uploaded hiking workout was stored without a
        sport type. Build the workout with a type Garmin supports instead, for
        example ``RunningWorkout`` or a workout with the ``other`` sport type
        sent through :meth:`upload_workout`.

        Raises:
            ValueError: always.

        """
        raise ValueError(_NO_WORKOUT_SPORT_TYPE.format(sport="hiking"))

    def upload_strength_workout(self, workout: Any) -> dict[str, Any]:
        """Upload a typed strength training workout.

        Args:
            workout: StrengthWorkout instance from garminconnect.workout

        Returns:
            Dictionary containing the uploaded workout data

        Example:
            from garminconnect.workout import StrengthWorkout, WorkoutSegment
            from garminconnect.workout import create_strength_set

            workout = StrengthWorkout(
                workoutName="Upper Body",
                estimatedDurationInSecs=0,
                workoutSegments=[
                    WorkoutSegment(
                        segmentOrder=1,
                        sportType={"sportTypeId": 5, "sportTypeKey": "strength_training"},
                        workoutSteps=[
                            create_strength_set("BENCH_PRESS", step_order=1,
                                                sets=4, reps=10, rest_seconds=120),
                        ],
                    )
                ],
            )
            api.upload_strength_workout(workout)

        """
        try:
            from ..workout import StrengthWorkout

            if not isinstance(workout, StrengthWorkout):
                raise TypeError("workout must be a StrengthWorkout instance")
            return self.upload_workout(workout.to_dict())
        except ImportError:
            raise ImportError(
                "Pydantic is required for typed workouts. "
                "Install it with: pip install pydantic or pip install garminconnect[workout]"
            ) from None

    def get_scheduled_workouts(
        self, year: int | str, month: int | str
    ) -> dict[str, Any]:
        """Return the scheduled workouts of a calendar month."""
        year = _coerce_positive_id(year, "year")
        if year < 2000:
            raise ValueError(f"year must be 2000 or later, got: {year}")

        month = _coerce_positive_id(month, "month")
        if month < 1 or month > 12:
            raise ValueError(f"month must be between 1 and 12, got: {month}")

        # Garmin's API uses 0-indexed months, so we need to subtract 1 from the month value
        url = f"{self.garmin_scheduled_workouts_url}/year/{year}/month/{month - 1}"
        logger.debug(
            "Requesting scheduled workout for year %d and month %d", year, month
        )
        return self.connectapi(url)

    def get_scheduled_workout_by_id(
        self, scheduled_workout_id: int | str
    ) -> dict[str, Any]:
        """Return one scheduled workout."""
        scheduled_workout_id = _coerce_positive_id(
            scheduled_workout_id, "scheduled_workout_id"
        )
        url = f"{self.garmin_workouts_schedule_url}/{scheduled_workout_id}"
        logger.debug("Requesting scheduled workout by id %d", scheduled_workout_id)
        return self.connectapi(url)

    def get_next_scheduled_workout(self) -> dict[str, Any]:
        """Return the earliest upcoming scheduled workout (today or later).

        Checks the current and next calendar month via
        ``get_scheduled_workouts`` and returns the first calendar item
        with ``itemType == "workout"`` whose date is today or later, or
        an empty dict if none is scheduled.

        Note: Garmin's calendar-service only returns workouts it has
        already committed to the visible calendar. For adaptive/Coach
        plans, use :meth:`get_scheduled_workouts_by_period` (the endpoint
        the web app's training-plan view reads) together with
        :meth:`get_active_training_plans`.
        """
        today = self.today()
        next_month = today.month + 1 if today.month < 12 else 1
        next_month_year = today.year if today.month < 12 else today.year + 1

        this_month = self.get_scheduled_workouts(today.year, today.month) or {}
        next_month_data = self.get_scheduled_workouts(next_month_year, next_month) or {}
        calendar_items = (this_month.get("calendarItems") or []) + (
            next_month_data.get("calendarItems") or []
        )

        today_str = today.isoformat()
        workouts = sorted(
            (
                item
                for item in calendar_items
                if item.get("itemType") == "workout"
                and (item.get("date") or "") >= today_str
            ),
            key=lambda item: item.get("date") or "",
        )
        return workouts[0] if workouts else {}

    def schedule_workout(self, workout_id: int | str, date_str: str) -> dict[str, Any]:
        """Schedule a workout on a specific date in the Garmin calendar.

        Args:
            workout_id: The workout ID returned after uploading.
            date_str: Target date in YYYY-MM-DD format.

        """
        workout_id = _coerce_positive_id(workout_id, "workout_id")
        date_str = _validate_date_format(date_str, "date_str")
        url = f"{self.garmin_workouts_schedule_url}/{workout_id}"
        logger.debug("Scheduling workout %s for %s", workout_id, date_str)
        payload = {"date": date_str}
        return self.client.post("connectapi", url, json=payload, api=True)

    def unschedule_workout(self, scheduled_workout_id: int | str) -> Any:
        """Remove a scheduled workout from the calendar without deleting the template."""
        scheduled_workout_id = _coerce_positive_id(
            scheduled_workout_id, "scheduled_workout_id"
        )
        url = f"{self.garmin_workouts_schedule_url}/{scheduled_workout_id}"
        logger.debug("Unscheduling workout %s", scheduled_workout_id)
        return self.client.delete("connectapi", url, api=True)

    def get_scheduled_workouts_by_period(
        self, start: str, end: str
    ) -> list[dict[str, Any]]:
        """Return all scheduled workouts between two dates, including adaptive plans.

        GET /workout-service/schedule/workoutScheduleByPeriod?startDate&endDate
        — the call behind the web app's upcoming-workouts view.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_workout_service_url}/schedule/workoutScheduleByPeriod"
        logger.debug("Requesting scheduled workouts by period")
        return self.connectapi(url, params={"startDate": start, "endDate": end})

    def get_workout_count(self, include_atp: bool = False) -> dict[str, Any]:
        """Return workout counts per sport (``totalCount``, ``runningCount``, ...).

        GET /workout-service/workouts/count?includeAtp=.
        """
        url = f"{self.garmin_connect_workout_service_url}/workouts/count"
        logger.debug("Requesting workout count")
        return self.connectapi(
            url, params={"includeAtp": str(bool(include_atp)).lower()}
        )

    def get_workout_sport_types(self) -> list[dict[str, Any]]:
        """Return the sport types that have workouts in the library.

        GET /workout-service/workouts/sport-types.
        """
        url = f"{self.garmin_connect_workout_service_url}/workouts/sport-types"
        logger.debug("Requesting workout sport types")
        return self.connectapi(url)

    def get_workout_types(self) -> dict[str, Any]:
        """Return the workout dictionaries (step, condition, target, sport, equipment types).

        GET /workout-service/workout/types — the source of the ids in
        :mod:`garminconnect.workout`.
        """
        url = f"{self.garmin_connect_workout_service_url}/workout/types"
        logger.debug("Requesting workout types")
        return self.connectapi(url)

    def get_strength_benchmarks(self) -> list[dict[str, Any]]:
        """Return the strength benchmark exercises (used for 1RM based targets).

        GET /workout-service/benchmarks.
        """
        url = f"{self.garmin_connect_workout_service_url}/benchmarks"
        logger.debug("Requesting strength benchmarks")
        return self.connectapi(url)

    def copy_workout(self, workout_id: int | str, name: str) -> Any:
        """Duplicate a workout under a new name and return the copy.

        POST /workout-service/workout/copy/{workoutId} with the new name as a
        ``text/plain`` body.
        """
        workout_id = _coerce_positive_id(workout_id, "workout_id")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        url = f"{self.garmin_connect_workout_service_url}/workout/copy/{workout_id}"
        logger.debug("Copying workout %s", workout_id)
        return self.client.post(
            "connectapi",
            url,
            data=name.strip().encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            api=True,
        )

    def reschedule_workout(self, scheduled_workout_id: int | str, cdate: str) -> Any:
        """Move a scheduled workout to another date.

        PUT /workout-service/schedule/{scheduleId} with the existing schedule
        entry plus ``calendarDate`` set to the new date.
        """
        cdate = _validate_date_format(cdate, "cdate")
        current = self.get_scheduled_workout_by_id(scheduled_workout_id) or {}
        scheduled_workout_id = _coerce_positive_id(
            scheduled_workout_id, "scheduled_workout_id"
        )
        workout = current.get("workout") or {}
        payload = {
            **current,
            "calendarDate": cdate,
            "workout": {"workoutId": workout.get("workoutId")} if workout else None,
        }
        url = f"{self.garmin_workouts_schedule_url}/{scheduled_workout_id}"
        logger.debug("Rescheduling workout %s to %s", scheduled_workout_id, cdate)
        return self._json_or_none(self.client.put("connectapi", url, json=payload))
