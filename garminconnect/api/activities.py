"""Activities: listing, search, details, uploads and edits."""

import re
from pathlib import Path
from typing import Any

from requests import HTTPError

from ..exceptions import (
    GarminConnectConnectionError,
    GarminConnectInvalidFileFormatError,
)
from ._common import (
    MAX_ACTIVITY_LIMIT,
    MAX_PAGINATED_REQUESTS,
    _coerce_positive_id,
    _validate_date_format,
    _validate_date_range,
    _validate_non_negative_integer,
    _validate_positive_integer,
    logger,
)
from .base import GarminBase

# Nested enum of GarminBase, aliased for the default argument of download_activity.
ActivityDownloadFormat = GarminBase.ActivityDownloadFormat


class ActivitiesMixin(GarminBase):
    """Activities: listing, search, details, uploads and edits."""

    def count_activities(self) -> int:
        """Return total number of activities for the current user account."""
        url = f"{self.garmin_connect_activities_count}"
        logger.debug("Requesting activities count")

        activities_count = self.connectapi(url)
        if not activities_count or "totalCount" not in activities_count:
            raise GarminConnectConnectionError("No activities count data received")
        return activities_count["totalCount"]

    def get_activities(
        self,
        start: int = 0,
        limit: int = 20,
        activitytype: str | None = None,
        activitysubtype: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Return a page of activities, newest first, optionally filtered by type.
        :param start: Starting activity offset, where 0 means the most recent activity
        :param limit: Number of activities to return
        :param activitytype: (Optional) Filter activities by type
        :param activitysubtype: (Optional) Filter activities further by sub-type.
        :return: List of activities from Garmin.
        """
        # Validate inputs
        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")

        if limit > MAX_ACTIVITY_LIMIT:
            raise ValueError(f"limit cannot exceed {MAX_ACTIVITY_LIMIT}")

        url = self.garmin_connect_activities
        params = {"start": str(start), "limit": str(limit)}
        if activitytype:
            params["activityType"] = activitytype

            if activitysubtype:
                params["activitySubType"] = activitysubtype

        logger.debug("Requesting activities from %d with limit %d", start, limit)

        activities = self.connectapi(url, params=params)

        if activities is None:
            logger.warning("No activities data received")
            return []

        return activities

    def get_activities_fordate(self, fordate: str) -> dict[str, Any]:
        """Return available activities for date."""
        fordate = _validate_date_format(fordate, "fordate")
        url = f"{self.garmin_connect_activity_fordate}/{fordate}"
        logger.debug("Requesting activities for date %s", fordate)

        return self.connectapi(url)

    def update_activity(self, activity_id: int | str, fields: dict[str, Any]) -> Any:
        """Change one or more fields of an activity in a single call.

        PUT /activity-service/activity/{activityId} with ``{"activityId": id,
        **fields}`` — the partial update the web app's activity editor sends
        and that :meth:`set_activity_name`, :meth:`set_activity_description`,
        :meth:`set_activity_type` and :meth:`set_activity_favorite` each use
        for one field. ``fields`` may hold e.g. ``activityName``,
        ``description``, ``activityTypeDTO``, ``eventTypeDTO``,
        ``metadataDTO`` (``favorite``) or ``accessControlRuleDTO`` (privacy),
        with the value shapes seen in :meth:`get_activity`. Verified live.
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        if not isinstance(fields, dict) or not fields:
            raise ValueError("fields must be a non-empty dictionary")
        if any(not isinstance(k, str) or not k for k in fields):
            raise ValueError("fields must be keyed by non-empty strings")
        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {**fields, "activityId": activity_id}
        logger.debug("Updating activity %s: %s", activity_id, sorted(fields))
        return self.client.put("connectapi", url, json=payload, api=True)

    def set_activity_name(self, activity_id: str, title: str) -> Any:
        """Set the name of an activity."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {"activityId": activity_id, "activityName": title}

        return self.client.put("connectapi", url, json=payload, api=True)

    def set_activity_type(
        self,
        activity_id: str,
        type_id: int,
        type_key: str,
        parent_type_id: int,
    ) -> Any:
        """Change the activity type of an activity."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {
            "activityId": activity_id,
            "activityTypeDTO": {
                "typeId": type_id,
                "typeKey": type_key,
                "parentTypeId": parent_type_id,
            },
        }
        logger.debug("Changing activity type: %s", payload)
        return self.client.put("connectapi", url, json=payload, api=True)

    def set_activity_description(self, activity_id: str, description: str) -> Any:
        """Set the description of an activity."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {"activityId": activity_id, "description": description}

        return self.client.put("connectapi", url, json=payload, api=True)

    def create_manual_activity_from_json(self, payload: dict[str, Any]) -> Any:
        """Create a manual activity from a complete activity payload."""
        url = f"{self.garmin_connect_activity}"
        logger.debug("Uploading manual activity: %s", str(payload))
        return self.client.post("connectapi", url, json=payload, api=True)

    def create_manual_activity(
        self,
        start_datetime: str,
        time_zone: str,
        type_key: str,
        distance_km: float,
        duration_min: int,
        activity_name: str,
    ) -> Any:
        """Create a private activity manually with a few basic parameters.
        type_key - Garmin field representing type of activity. See https://connect.garmin.com/modern/main/js/properties/activity_types/activity_types.properties
                    Value to use is the key without 'activity_type_' prefix, e.g. 'resort_skiing'
        start_datetime - timestamp in this pattern "2023-12-02T10:00:00.000"
        time_zone - local timezone of the activity, e.g. 'Europe/Paris'
        distance_km - distance of the activity in kilometers
        duration_min - duration of the activity in minutes
        activity_name - the title.
        """
        payload = {
            "activityTypeDTO": {"typeKey": type_key},
            "accessControlRuleDTO": {"typeId": 2, "typeKey": "private"},
            "timeZoneUnitDTO": {"unitKey": time_zone},
            "activityName": activity_name,
            "metadataDTO": {
                "autoCalcCalories": True,
            },
            "summaryDTO": {
                "startTimeLocal": start_datetime,
                "distance": distance_km * 1000,
                "duration": duration_min * 60,
            },
        }
        return self.create_manual_activity_from_json(payload)

    def get_last_activity(self) -> dict[str, Any] | None:
        """Return the most recent activity."""
        activities = self.get_activities(0, 1)
        if activities and isinstance(activities, list) and len(activities) > 0:
            return activities[-1]
        if activities and isinstance(activities, dict) and "activityList" in activities:
            activity_list = activities["activityList"]
            if activity_list and len(activity_list) > 0:
                return activity_list[-1]

        return None

    def upload_activity(self, activity_path: str) -> Any:
        """Upload an activity file (FIT, GPX or TCX)."""
        # This code is borrowed from python-garminconnect-enhanced ;-)

        # Validate input
        if not activity_path:
            raise ValueError("activity_path cannot be empty")

        if not isinstance(activity_path, str):
            raise ValueError("activity_path must be a string")

        # Check if file exists
        p = Path(activity_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {activity_path}")

        # Check if it's actually a file
        if not p.is_file():
            raise ValueError(f"path is not a file: {activity_path}")

        file_base_name = p.name

        if not file_base_name:
            raise ValueError("invalid file path - no filename found")

        # More robust extension checking
        file_parts = file_base_name.split(".")
        if len(file_parts) < 2:
            raise GarminConnectInvalidFileFormatError(
                f"File has no extension: {activity_path}"
            )

        file_extension = file_parts[-1]
        allowed_file_extension = (
            file_extension.upper() in GarminBase.ActivityUploadFormat.__members__
        )

        if allowed_file_extension:
            try:
                # Use context manager for file handling
                with p.open("rb") as file_handle:
                    files = {"file": (file_base_name, file_handle)}
                    url = self.garmin_connect_upload
                    return self.client.post("connectapi", url, files=files, api=True)
            except OSError as e:
                raise GarminConnectConnectionError(
                    f"Failed to read file {activity_path}: {e}"
                ) from e
        else:
            allowed_formats = ", ".join(
                GarminBase.ActivityUploadFormat.__members__.keys()
            )
            raise GarminConnectInvalidFileFormatError(
                f"Invalid file format '{file_extension}'. Allowed formats: {allowed_formats}"
            )

    def import_activity(self, activity_path: str) -> dict[str, Any]:
        """Upload activity as an import (not re-exported to third parties like Strava).

        Uses the Garmin import endpoint with headers matching Garmin Connect
        Mobile, so imported activities are treated as imports rather than
        device-synced activities.

        Args:
            activity_path: Path to the activity file (FIT, TCX, or GPX).

        Returns:
            Dictionary containing the DetailedImportResult with successes,
            failures, and activity IDs.

        Raises:
            FileNotFoundError: If the activity file does not exist.
            GarminConnectInvalidFileFormatError: If the file format is invalid.
            GarminConnectConnectionError: If the upload fails.

        """
        if not activity_path:
            raise ValueError("activity_path cannot be empty")

        if not isinstance(activity_path, str):
            raise ValueError("activity_path must be a string")

        p = Path(activity_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {activity_path}")

        if not p.is_file():
            raise ValueError(f"path is not a file: {activity_path}")

        file_base_name = p.name
        if not file_base_name:
            raise ValueError("invalid file path - no filename found")

        file_parts = file_base_name.split(".")
        if len(file_parts) < 2:
            raise GarminConnectInvalidFileFormatError(
                f"File has no extension: {activity_path}"
            )

        file_extension = file_parts[-1].lower()
        if file_extension.upper() not in GarminBase.ActivityUploadFormat.__members__:
            allowed_formats = ", ".join(
                GarminBase.ActivityUploadFormat.__members__.keys()
            )
            raise GarminConnectInvalidFileFormatError(
                f"Invalid file format '{file_extension}'. "
                f"Allowed formats: {allowed_formats}"
            )

        url = f"{self.garmin_connect_upload}/{file_extension}"
        headers = {
            "NK": "NT",
            "origin": "https://sso.garmin.com",
            "User-Agent": "GCM-iOS-5.7.2.1",
        }

        try:
            with p.open("rb") as file_handle:
                files = {
                    "file": (
                        file_base_name,
                        file_handle,
                        "application/octet-stream",
                    )
                }
                logger.debug("Importing activity file %s via %s", file_base_name, url)
                response = self.client.post(
                    "connectapi", url, files=files, headers=headers, api=True
                )
                if hasattr(response, "json"):
                    result: dict[str, Any] = response.json()
                    return result
                return {"status": "uploaded", "fileName": file_base_name}
        except (HTTPError, GarminConnectConnectionError) as e:
            if isinstance(e, GarminConnectConnectionError):
                status = getattr(getattr(e, "response", None), "status_code", None)
            else:
                status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 409:
                logger.info("Activity already exists (duplicate): %s", file_base_name)
                raise GarminConnectConnectionError(
                    f"Activity already exists (duplicate): {file_base_name}"
                ) from e
            logger.exception(
                "Import failed for '%s' (status=%s)", activity_path, status
            )
            raise GarminConnectConnectionError(f"Import error: {e}") from e
        except OSError as e:
            raise GarminConnectConnectionError(
                f"Failed to read file {activity_path}: {e}"
            ) from e

    def delete_activity(self, activity_id: str) -> Any:
        """Delete activity with specified id."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_delete_activity_url}/{activity_id}"
        logger.debug("Deleting activity with id %s", activity_id)

        return self.client.request(
            "DELETE",
            "connectapi",
            url,
            api=True,
        )

    def get_activities_by_date(
        self,
        startdate: str,
        enddate: str | None = None,
        activitytype: str | None = None,
        sortorder: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return activities between two dates, optionally filtered by type.
        :param startdate: String in the format YYYY-MM-DD
        :param enddate: (Optional) String in the format YYYY-MM-DD
        :param activitytype: (Optional) Type of activity you are searching
                             Possible values are [cycling, running, swimming,
                             multi_sport, fitness_equipment, hiking, walking, other]
        :param sortorder: (Optional) sorting direction. By default, Garmin uses descending order by startLocal field.
                          Use "asc" to get activities from oldest to newest.
        :return: list of JSON activities.
        """
        activities = []
        start = 0
        limit = 20
        # mimicking the behavior of the web interface that fetches
        # 20 activities at a time
        # and automatically loads more on scroll
        url = self.garmin_connect_activities
        startdate = _validate_date_format(startdate, "startdate")
        if enddate is not None:
            enddate = _validate_date_format(enddate, "enddate")
        params = {
            "startDate": startdate,
            "start": str(start),
            "limit": str(limit),
        }
        if enddate:
            params["endDate"] = enddate
        if activitytype:
            params["activityType"] = activitytype
        if sortorder:
            params["sortOrder"] = sortorder

        logger.debug("Requesting activities by date from %s to %s", startdate, enddate)
        for _ in range(MAX_PAGINATED_REQUESTS):
            params["start"] = str(start)
            logger.debug("Requesting activities %d to %d", start, start + limit)
            act = self.connectapi(url, params=params)
            if act:
                activities.extend(act)
                start = start + limit
            else:
                break
        else:
            # A server that never returns an empty page would otherwise loop
            # the client forever (DoS); fail loudly instead of truncating.
            raise GarminConnectConnectionError(
                f"Pagination exceeded {MAX_PAGINATED_REQUESTS} requests; aborting"
            )

        return activities

    def get_progress_summary_between_dates(
        self,
        startdate: str,
        enddate: str,
        metric: str = "distance",
        groupbyactivities: bool = True,
    ) -> dict[str, Any]:
        """Return progress totals (distance, duration, ...) between two dates.
        :param startdate: String in the format YYYY-MM-DD
        :param enddate: String in the format YYYY-MM-DD
        :param metric: metric to be calculated in the summary:
            "elevationGain", "duration", "distance", "movingDuration"
        :param groupbyactivities: group the summary by activity type
        :return: list of JSON activities with their aggregated progress summary.
        """
        url = self.garmin_connect_fitnessstats
        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        params = {
            "startDate": startdate,
            "endDate": enddate,
            "aggregation": "lifetime",
            # Garmin's own client serializes booleans lowercase
            "groupByParentActivityType": str(bool(groupbyactivities)).lower(),
            "metric": metric,
        }

        logger.debug(
            "Requesting fitnessstats by date from %s to %s", startdate, enddate
        )
        return self.connectapi(url, params=params)

    def get_training_load_activities(
        self,
        startdate: str,
        enddate: str,
        *,
        metrics: list[str] | None = None,
        activitytype: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch individual activities and their training load metrics for a date range.

        :param startdate: range start "YYYY-MM-DD"
        :param enddate: range end "YYYY-MM-DD"
        :param metrics: metric fields to request; None uses defaults and [] is preserved
        :param activitytype: optional activity type filter
        :return: list of activities with the requested metrics
        """
        startdate, enddate = _validate_date_range(startdate, enddate)
        url = f"{self.garmin_connect_fitnessstats}/all"
        requested_metrics = (
            [
                "activityTrainingLoad",
                "trainingEffectLabel",
                "trainingEffectLabelSrvrCalc",
            ]
            if metrics is None
            else metrics
        )
        params: dict[str, Any] = {
            "startDate": startdate,
            "endDate": enddate,
            "metric": requested_metrics,
        }
        if activitytype:
            params["activityType"] = activitytype

        logger.debug(
            "Requesting training load activities from %s to %s", startdate, enddate
        )
        return self.connectapi(url, params=params)

    def get_activity_types(self) -> dict[str, Any]:
        """Return all activity types and their parent types."""
        url = self.garmin_connect_activity_types
        logger.debug("Requesting activity types")
        return self.connectapi(url)

    def download_activity(
        self,
        activity_id: str,
        dl_fmt: ActivityDownloadFormat = ActivityDownloadFormat.TCX,
    ) -> bytes:
        """Download an activity as the original file (zip), TCX, GPX, KML or CSV. For
        "Original" will return the zip file content, up to user to extract it.
        "CSV" will return a csv of the splits.
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        urls = {
            GarminBase.ActivityDownloadFormat.ORIGINAL: f"{self.garmin_connect_fit_download}/{activity_id}",
            GarminBase.ActivityDownloadFormat.TCX: f"{self.garmin_connect_tcx_download}/{activity_id}",
            GarminBase.ActivityDownloadFormat.GPX: f"{self.garmin_connect_gpx_download}/{activity_id}",
            GarminBase.ActivityDownloadFormat.KML: f"{self.garmin_connect_kml_download}/{activity_id}",
            GarminBase.ActivityDownloadFormat.CSV: f"{self.garmin_connect_csv_download}/{activity_id}",
        }
        if dl_fmt not in urls:
            raise ValueError(f"unexpected value {dl_fmt} for dl_fmt")
        url = urls[dl_fmt]

        logger.debug("Downloading activity from %s", url)

        return self.download(url)

    def get_activity_splits(self, activity_id: str) -> dict[str, Any]:
        """Return activity splits."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/splits"
        logger.debug("Requesting splits for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_typed_splits(self, activity_id: str) -> dict[str, Any]:
        """Return typed activity splits. Contains similar info to `get_activity_splits`, but for certain activity types
        (e.g., Bouldering), this contains more detail.
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/typedsplits"
        logger.debug("Requesting typed splits for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_split_summaries(self, activity_id: str) -> dict[str, Any]:
        """Return activity split summaries."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/split_summaries"
        logger.debug("Requesting split summaries for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_weather(self, activity_id: str) -> dict[str, Any]:
        """Return activity weather."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/weather"
        logger.debug("Requesting weather for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_hr_in_timezones(self, activity_id: str) -> dict[str, Any]:
        """Return the time spent in each heart rate zone during an activity."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/hrTimeInZones"
        logger.debug("Requesting HR time-in-zones for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_power_in_timezones(self, activity_id: str) -> dict[str, Any]:
        """Return the time spent in each power zone during an activity."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/powerTimeInZones"
        logger.debug("Requesting Power time-in-zones for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity(self, activity_id: str) -> dict[str, Any]:
        """Return activity summary, including basic splits."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}"
        logger.debug("Requesting activity summary data for activity id %s", activity_id)

        return self.connectapi(url)

    def get_activity_details(
        self, activity_id: str, maxchart: int = 2000, maxpoly: int = 4000
    ) -> dict[str, Any]:
        """Return activity details."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        maxchart = _validate_positive_integer(maxchart, "maxchart")
        maxpoly = _validate_non_negative_integer(maxpoly, "maxpoly")
        params = {"maxChartSize": str(maxchart), "maxPolylineSize": str(maxpoly)}
        url = f"{self.garmin_connect_activity}/{activity_id}/details"
        logger.debug("Requesting details for activity id %s", activity_id)

        return self.connectapi(url, params=params)

    def get_activity_images(self, activity_id: int | str) -> list[dict[str, Any]]:
        """Return the photos attached to an activity.

        Photos are surfaced in ``metadataDTO.activityImages`` of the
        `get_activity` response; there is no separate images endpoint.
        Each entry contains ``imageId``, ``url``, and ``photoDate``.

        Note: the ``url`` values are presigned S3 links
        (``X-Amz-Expires=86400``) that expire after 24 hours, so download
        the images promptly rather than storing the URLs. The
        ``hasImages`` flag in `get_activities` results is not a reliable
        indicator that an activity has photos attached.
        """
        activity = self.get_activity(str(activity_id)) or {}
        return (activity.get("metadataDTO") or {}).get("activityImages") or []

    def get_activity_exercise_sets(self, activity_id: int | str) -> dict[str, Any]:
        """Return activity exercise sets."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/exerciseSets"
        logger.debug("Requesting exercise sets for activity id %s", activity_id)

        return self.connectapi(url)

    def set_activity_exercise_sets(
        self, activity_id: int | str, payload: dict[str, Any]
    ) -> Any:
        """Replace the exercise sets of a strength activity.

        `payload` is the full body sent to the server, in the same shape as the
        response from `get_activity_exercise_sets`. Replace-all semantics — the
        existing `exerciseSets` array is overwritten. Garmin validates the
        `exercises[].category` (parent) and `exercises[].name` (sub-category)
        against its FIT enum and returns 400 "Invalid Sub-Category Passed" for
        unknown values; `name=None` is always accepted under a known parent.
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/exerciseSets"
        logger.debug("Replacing exercise sets for activity id %s", activity_id)

        return self.client.put("connectapi", url, json=payload, api=True)

    def get_available_metrics(
        self, start: str, end: str, activity_types: list[str] | None = None
    ) -> dict[str, Any]:
        """Return which progress-summary metrics have data per activity type.

        GET /fitnessstats-service/activity/availableMetrics?startDate&endDate
        [&activityType=...]. Useful before ``get_progress_summary_between_dates``.
        """
        start, end = _validate_date_range(start, end)
        url = (
            f"{self.garmin_connect_fitnessstats_service_url}/activity/availableMetrics"
        )
        params: dict[str, Any] = {"startDate": start, "endDate": end}
        if activity_types:
            params["activityType"] = [str(t).strip() for t in activity_types]
        logger.debug("Requesting available fitness metrics")
        return self.connectapi(url, params=params)

    def get_weekly_activity_stats(
        self, start: str, end: str, group_by_activity_type: bool = True
    ) -> dict[str, Any]:
        """Return weekly activity aggregates (VO2 max, distance, duration, ...).

        GET /userstats-service/activities/weekly/{displayName}
        ?fromWeekStartDate&untilWeekStartDate&grpActType=.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_userstats_url}/activities/weekly/{self._require_display_name()}"
        params = {
            "fromWeekStartDate": start,
            "untilWeekStartDate": end,
            "grpActType": str(bool(group_by_activity_type)).lower(),
        }
        logger.debug("Requesting weekly activity stats")
        return self.connectapi(url, params=params)

    def search_activities(
        self,
        start: int = 0,
        limit: int = 20,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Search activities with the full filter set of the web app's activity list.

        GET /activitylist-service/activities/search/activities?start&limit&...
        Any keyword is passed through as a query parameter; the web app uses
        ``activityType``, ``activitySubType``, ``startDate``, ``endDate``,
        ``search`` (free text), ``favorite=1``, ``sortBy``/``sortOrder``,
        ``minDistance``/``maxDistance`` (m), ``minDuration``/``maxDuration``
        (s), ``minElevation``/``maxElevation``, ``eventType``,
        ``excludeChildren``. Booleans are sent lowercase; ``None`` values are
        skipped. ``get_activities``/``get_activities_by_date`` remain the
        simple variants.
        """
        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        params: dict[str, Any] = {"start": start, "limit": limit}
        for key, raw in filters.items():
            if raw is None:
                continue
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", key):
                raise ValueError(f"invalid filter name: {key!r}")
            value = (
                _validate_date_format(raw, key)
                if key in {"startDate", "endDate"}
                else raw
            )
            params[key] = str(value).lower() if isinstance(value, bool) else value
        url = self.garmin_connect_activities
        logger.debug("Searching activities")
        return self.connectapi(url, params=params)

    def get_fastest_splits(
        self,
        start: str,
        end: str,
        activity_type: str = "running",
        number_of_bests: int = 10,
    ) -> list[dict[str, Any]]:
        """Return the fastest splits (best times per distance) in a date range.

        GET /activitylist-service/activities/fastest-splits
        ?numberOfBests&startDate&endDate&activityType.
        """
        start, end = _validate_date_range(start, end)
        number_of_bests = _validate_positive_integer(number_of_bests, "number_of_bests")
        url = f"{self.garmin_connect_activitylist_url}/fastest-splits"
        params = {
            "numberOfBests": number_of_bests,
            "startDate": start,
            "endDate": end,
            "activityType": activity_type.strip().lower(),
        }
        logger.debug("Requesting fastest splits")
        return self.connectapi(url, params=params)

    def get_favorite_activities(self, limit: int = 5) -> dict[str, Any]:
        """Return activities marked as favorite (``activityList``).

        GET /activitylist-service/activities/favorite/{displayName}?limit=.
        """
        limit = _validate_positive_integer(limit, "limit")
        url = f"{self.garmin_connect_activitylist_url}/favorite/{self._require_display_name()}"
        logger.debug("Requesting favorite activities")
        return self.connectapi(url, params={"limit": limit})

    def set_activity_favorite(
        self, activity_id: int | str, favorite: bool = True
    ) -> Any:
        """Mark or unmark an activity as favorite.

        PUT /activity-service/activity/{activityId} with
        ``{"activityId": ..., "metadataDTO": {"favorite": bool}}`` — the same
        partial-update call ``set_activity_name`` uses.
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}"
        payload = {
            "activityId": activity_id,
            "metadataDTO": {"favorite": bool(favorite)},
        }
        logger.debug("Setting favorite=%s on activity %s", favorite, activity_id)
        return self.client.put("connectapi", url, json=payload, api=True)

    def _activity_subresource(
        self, activity_id: int | str, sub: str, **kwargs: Any
    ) -> Any:
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/{activity_id}/{sub}"
        logger.debug("Requesting activity %s for %s", sub, activity_id)
        return self.connectapi(url, **kwargs)

    def get_activity_laps(self, activity_id: int | str) -> dict[str, Any]:
        """Return the laps of an activity (``lapDTOs``).

        GET /activity-service/activity/{activityId}/laps.
        """
        return self._activity_subresource(activity_id, "laps")

    def get_activity_rounds(self, activity_id: int | str) -> dict[str, Any]:
        """Return rounds with their exercise sets (HIIT, boxing, ...).

        GET /activity-service/activity/{activityId}/rounds.
        """
        return self._activity_subresource(activity_id, "rounds")

    def get_activity_step_details(self, activity_id: int | str) -> dict[str, Any]:
        """Return the per-workout-step details of a structured workout activity.

        GET /activity-service/activity/{activityId}/stepdetails.
        """
        return self._activity_subresource(activity_id, "stepdetails")

    def get_activity_jump_details(self, activity_id: int | str) -> list[dict[str, Any]]:
        """Return jump data (jump rope and similar; empty when ``jumpCount`` is 0).

        GET /activity-service/activity/{activityId}/jumpDetails.
        """
        return self._activity_subresource(activity_id, "jumpDetails")

    def get_activity_subsecond_details(
        self, activity_id: int | str, maxchart: int = 2000
    ) -> dict[str, Any]:
        """Return sub-second samples (only when ``metadataDTO.hasSubsecondData``).

        GET /activity-service/activity/{activityId}/subseconddetails?maxChartSize=.
        """
        maxchart = _validate_positive_integer(maxchart, "maxchart")
        return self._activity_subresource(
            activity_id, "subseconddetails", params={"maxChartSize": maxchart}
        )

    def get_activity_swim_details(
        self, activity_id: int | str, maxchart: int = 2000, maxpoly: int = 4000
    ) -> dict[str, Any]:
        """Return details for a lap-swimming activity.

        GET /activity-service/activity/{activityId}/swimDetails?maxChartSize
        &maxPolylineSize — the web app calls this instead of ``/details`` for
        pool swims.
        """
        maxchart = _validate_positive_integer(maxchart, "maxchart")
        maxpoly = _validate_non_negative_integer(maxpoly, "maxpoly")
        return self._activity_subresource(
            activity_id,
            "swimDetails",
            params={"maxChartSize": maxchart, "maxPolylineSize": maxpoly},
        )

    def get_activity_map_details(
        self,
        activity_id: int | str,
        maxpoly: int = 4000,
        max_heat_map: int = 4000,
    ) -> dict[str, Any]:
        """Return the polyline and heat map of an activity without the charts.

        GET /activity-service/activity/{activityId}/mapdetails
        ?maxPolylineSize&maxHeatMapSize.
        """
        maxpoly = _validate_non_negative_integer(maxpoly, "maxpoly")
        max_heat_map = _validate_non_negative_integer(max_heat_map, "max_heat_map")
        return self._activity_subresource(
            activity_id,
            "mapdetails",
            params={"maxPolylineSize": maxpoly, "maxHeatMapSize": max_heat_map},
        )

    def get_activity_polyline(self, activity_id: int | str) -> dict[str, Any]:
        """Return the encoded track polyline of an activity (``gPolyline``).

        GET /activity-service/activity/polyline/{activityId}.
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_activity}/polyline/{activity_id}"
        logger.debug("Requesting polyline for %s", activity_id)
        return self.connectapi(url)

    def get_adjacent_activities(self, activity_id: int | str) -> dict[str, Any]:
        """Return the ids of the previous and next activity (``None`` when absent).

        GET /activity-service/activity/{activityId}/prev and .../next.
        """
        prev = self._activity_subresource(activity_id, "prev") or {}
        nxt = self._activity_subresource(activity_id, "next") or {}
        return {"previous": prev.get("activityId"), "next": nxt.get("activityId")}

    def get_activity_event_types(self) -> list[dict[str, Any]]:
        """Return the activity event types (race, training, recreation, ...).

        GET /activity-service/activity/eventTypes.
        """
        url = f"{self.garmin_connect_activity}/eventTypes"
        logger.debug("Requesting activity event types")
        return self.connectapi(url)

    def get_activity_segments(self, activity_id: int | str) -> list[dict[str, Any]]:
        """Return the segments matched in an activity.

        GET /segment-service/segment/list/{activityId}.
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_segment_url}/segment/list/{activity_id}"
        logger.debug("Requesting segments for %s", activity_id)
        return self.connectapi(url)
