"""Personal records, badges, challenges and goals."""

from typing import Any

from ..exceptions import GarminConnectConnectionError
from ._common import (
    MAX_PAGINATED_REQUESTS,
    _coerce_positive_id,
    _validate_date_range,
    _validate_non_negative_integer,
    _validate_positive_integer,
    _validate_positive_number,
    _validate_sport_key,
    _validate_uuid,
    logger,
)
from .base import GarminBase


class AchievementsMixin(GarminBase):
    """Personal records, badges, challenges and goals."""

    def get_personal_record(
        self, include_history: bool | None = None, months: int | None = None
    ) -> dict[str, Any]:
        """Return personal records for current user.

        Returns raw personal record entries from Garmin Connect.
        For running records (activityType == 'running'), typeId maps to:
          - 1: 1 km
          - 2: 1 mile
          - 3: 5 km
          - 4: 10 km
          - 5: Half marathon
          - 6: Marathon
          - 7: Longest run (distance in meters; duration requires
            calling activity-service/activity/{activityId})

        Args:
            include_history: When set, sent as ``includeHistory`` (the web app
                sends ``true`` to get previous record holders as well).
            months: When set, limits the records to the last ``months`` months.

        """
        url = (
            f"{self.garmin_connect_personal_record_url}/{self._require_display_name()}"
        )
        params: dict[str, str] = {}
        if include_history is not None:
            params["includeHistory"] = str(bool(include_history)).lower()
        if months is not None:
            params["months"] = str(_validate_positive_integer(months, "months"))
        logger.debug("Requesting personal records for user")

        return self.connectapi(url, params=params or None)

    def get_earned_badges(self) -> list[dict[str, Any]]:
        """Return all earned badges for the current user."""
        url = self.garmin_connect_earned_badges_url
        logger.debug("Requesting earned badges for user")

        return self.connectapi(url)

    def get_available_badges(self) -> list[dict[str, Any]]:
        """Return available (not yet earned) badges for the current user."""
        url = self.garmin_connect_available_badges_url
        logger.debug("Requesting available badges for user")

        return self.connectapi(url, params={"showExclusiveBadge": "true"})

    def get_in_progress_badges(self) -> list[dict[str, Any]]:
        """Return all badges currently in progress for the current user."""
        logger.debug("Requesting in progress badges for user")

        earned_badges = self.get_earned_badges()
        available_badges = self.get_available_badges()

        # Filter out badges that are not in progress
        def is_badge_in_progress(badge: dict) -> bool:
            """Return True if the badge is in progress."""
            progress = badge.get("badgeProgressValue")
            if not progress:
                return False
            if progress == 0:
                return False
            target = badge.get("badgeTargetValue")
            if progress == target:
                if badge.get("badgeLimitCount") is None:
                    return False
                return badge.get("badgeEarnedNumber", 0) < badge["badgeLimitCount"]
            return True

        earned_in_progress_badges = list(filter(is_badge_in_progress, earned_badges))
        available_in_progress_badges = list(
            filter(is_badge_in_progress, available_badges)
        )

        combined = {b["badgeId"]: b for b in earned_in_progress_badges}
        combined.update({b["badgeId"]: b for b in available_in_progress_badges})
        return list(combined.values())

    def get_adhoc_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return adhoc challenges for the current user."""
        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_adhoc_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting adhoc challenges for user")

        return self.connectapi(url, params=params)

    def get_badge_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return badge challenges for the current user."""
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_available_badge_challenges(self, start: int, limit: int) -> dict[str, Any]:
        """Return available badge challenges."""
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_available_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting available badge challenges")

        return self.connectapi(url, params=params)

    def get_non_completed_badge_challenges(
        self, start: int, limit: int
    ) -> dict[str, Any]:
        """Return badge challenges that are not completed yet."""
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_non_completed_badge_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting badge challenges for user")

        return self.connectapi(url, params=params)

    def get_inprogress_virtual_challenges(
        self, start: int, limit: int
    ) -> dict[str, Any]:
        """Return in-progress virtual challenges for current user."""
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = self.garmin_connect_inprogress_virtual_challenges_url
        params = {"start": str(start), "limit": str(limit)}
        logger.debug("Requesting in-progress virtual challenges for user")

        return self.connectapi(url, params=params)

    def get_goals(
        self, status: str = "active", start: int = 1, limit: int = 30
    ) -> list[dict[str, Any]]:
        """Return goals by status (active, future or past).
        :param status: Status of goals (valid options are "active", "future", or "past")
        :type status: str
        :param start: 1-based index of the first goal to retrieve
        :type start: int
        :param limit: Pagination limit when retrieving goals
        :type limit: int
        :return: list of goals in JSON format.
        """
        goals = []
        url = self.garmin_connect_goals_url
        valid_statuses = {"active", "future", "past"}
        if status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        params = {
            "status": status,
            "start": str(start),
            "limit": str(limit),
            "sortOrder": "asc",
        }
        # goal-service silently returns [] for newer goal types (custom
        # accumulation goals with a date range, created via the current
        # Connect UI) unless this fetch-metadata header is present - #431.
        # Browsers always send it on a same-origin XHR; this client doesn't
        # send any Sec-Fetch-* headers otherwise, so it has to be explicit.
        headers = {"Sec-Fetch-Site": "same-origin"}

        logger.debug("Requesting %s goals", status)
        for _ in range(MAX_PAGINATED_REQUESTS):
            params["start"] = str(start)
            logger.debug(
                "Requesting %s goals %d to %d", status, start, start + limit - 1
            )
            goals_json = self.connectapi(url, params=params, headers=headers)
            if goals_json:
                goals.extend(goals_json)
                start = start + limit
            else:
                break
        else:
            # A server that never returns an empty page would otherwise loop
            # the client forever (DoS); fail loudly instead of truncating.
            raise GarminConnectConnectionError(
                f"Pagination exceeded {MAX_PAGINATED_REQUESTS} requests; aborting"
            )

        return goals

    def get_personal_record_candidates(self) -> list[dict[str, Any]]:
        """Return personal-record candidates awaiting confirmation.

        GET /personalrecord-service/personalrecordcandidate/{displayName}.
        """
        url = (
            f"{self.garmin_connect_personal_record_service_url}/personalrecordcandidate/"
            f"{self._require_display_name()}"
        )
        logger.debug("Requesting personal record candidates")
        return self.connectapi(url)

    def get_personal_record_types(self) -> list[dict[str, Any]]:
        """Return the personal-record type definitions (id, key, sport, bounds).

        GET /personalrecord-service/personalrecordtype/prtypes/{displayName}.
        """
        url = (
            f"{self.garmin_connect_personal_record_service_url}/personalrecordtype/prtypes/"
            f"{self._require_display_name()}"
        )
        logger.debug("Requesting personal record types")
        return self.connectapi(url)

    def get_personal_records_for_activity(
        self, activity_id: int | str
    ) -> list[dict[str, Any]]:
        """Return personal records set by one activity.

        GET /personalrecord-service/personalrecord/prByActivityId/{activityId}.
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = (
            f"{self.garmin_connect_personal_record_service_url}/personalrecord/"
            f"prByActivityId/{activity_id}"
        )
        logger.debug("Requesting personal records for activity %s", activity_id)
        return self.connectapi(url)

    def get_steps_goal(self, cdate: str | None = None) -> dict[str, Any]:
        """Return the effective step goal for a day (device vs. user goal).

        GET /wellness-service/wellness/wellness-goals/consolidated/steps/{date}.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_wellness_url}/wellness-goals/consolidated/steps/{cdate}"
        logger.debug("Requesting steps goal")
        return self.connectapi(url)

    def get_effective_goals(self, cdate: str | None = None) -> list[dict[str, Any]]:
        """Return the daily goals in effect on a day (intensity minutes, floors, hydration, ...).

        GET /goal-service/goal/user/effective/{date}.
        """
        cdate = self._date_or_today(cdate)
        url = f"{self.garmin_connect_goal_service_url}/user/effective/{cdate}"
        logger.debug("Requesting effective goals")
        return self.connectapi(url)

    def get_user_goals(self) -> list[dict[str, Any]]:
        """Return the user's wellness goals (steps, weight, calories, ...).

        GET /goal-service/goal/user.
        """
        url = f"{self.garmin_connect_goal_service_url}/user"
        logger.debug("Requesting user goals")
        return self.connectapi(url)

    def get_weight_goal(self, start: str, end: str) -> dict[str, Any]:
        """Return the weight goal(s) in effect over a date range.

        GET /goal-service/goal/user/effective/weightgoal/{start}/{end}.
        """
        start, end = _validate_date_range(start, end)
        url = f"{self.garmin_connect_goal_service_url}/user/effective/weightgoal/{start}/{end}"
        logger.debug("Requesting weight goal")
        return self.connectapi(url)

    def set_daily_goal(
        self, goal_type: str, value: float, cdate: str | None = None
    ) -> dict[str, Any]:
        """Set a daily wellness goal such as intensity minutes, floors or hydration.

        PUT /goal-service/goal/user/effective/{goal-type}/{date} with
        ``{"goalValue": value, "goalType": GOAL_TYPE}``, as the web app's goal
        editor does. ``goal_type`` is a key from :meth:`get_effective_goals`
        (``INTENSITY_MINUTES``, ``FLOORS_CLIMBED``, ``HYDRATION`` (ml),
        ``WEIGHT_GRAMS``); in the path Garmin uses the lower-case dashed form
        (``floors-climbed``) except for ``WEIGHT_GRAMS``. Verified live for
        ``FLOORS_CLIMBED``. For steps use :meth:`set_steps_goal`.
        """
        goal_type = _validate_sport_key(goal_type, "goal_type")
        value = _validate_positive_number(value, "value")
        cdate = self._date_or_today(cdate)
        slug = (
            goal_type
            if goal_type == "WEIGHT_GRAMS"
            else goal_type.lower().replace("_", "-")
        )
        url = f"{self.garmin_connect_goal_service_url}/user/effective/{slug}/{cdate}"
        payload = {"goalValue": value, "goalType": goal_type}
        logger.debug("Setting %s goal to %s", goal_type, value)
        return self.client.put("connectapi", url, json=payload).json()

    def get_badge_attributes(self) -> dict[str, Any]:
        """Return badge metadata: types, categories, difficulties.

        GET /badge-service/badge/attributes.
        """
        url = f"{self.garmin_connect_badge_url}/attributes"
        logger.debug("Requesting badge attributes")
        return self.connectapi(url)

    def get_badge_detail(self, badge_id: int | str) -> dict[str, Any]:
        """Return the details of one badge.

        GET /badge-service/badge/detail/v3/{badgeId}.
        """
        badge_id = _coerce_positive_id(badge_id, "badge_id")
        url = f"{self.garmin_connect_badge_url}/detail/v3/{badge_id}"
        logger.debug("Requesting badge detail %s", badge_id)
        return self.connectapi(url)

    def get_latest_earned_badges(self, limit: int = 5) -> list[dict[str, Any]]:
        """Return the most recently earned badges.

        GET /badge-service/badge/earned/latest/{displayName}?limit=.
        """
        limit = _validate_positive_integer(limit, "limit")
        url = f"{self.garmin_connect_badge_url}/earned/latest/{self._require_display_name()}"
        logger.debug("Requesting latest earned badges")
        return self.connectapi(url, params={"limit": limit})

    def get_badges_for_activity(self, activity_id: int | str) -> list[dict[str, Any]]:
        """Return badges earned by one activity.

        GET /badge-service/badge/{displayName}/earned/activity/{activityId}.
        """
        activity_id = _coerce_positive_id(activity_id, "activity_id")
        url = (
            f"{self.garmin_connect_badge_url}/{self._require_display_name()}/earned/"
            f"activity/{activity_id}"
        )
        logger.debug("Requesting badges for activity %s", activity_id)
        return self.connectapi(url)

    def get_badges_for_day(self, cdate: str | None = None) -> list[dict[str, Any]]:
        """Return badges earned on a day.

        GET /badge-service/badge/{displayName}/earned/dailysummary/{date}.
        """
        cdate = self._date_or_today(cdate)
        url = (
            f"{self.garmin_connect_badge_url}/{self._require_display_name()}/earned/"
            f"dailysummary/{cdate}"
        )
        logger.debug("Requesting badges for day")
        return self.connectapi(url)

    def get_available_virtual_challenges(
        self, start: int = 1, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Return virtual (expedition) challenges that can be joined.

        GET /badgechallenge-service/virtualChallenge/available?start&limit.
        """
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = f"{self.garmin_connect_badge_challenge_url}/virtualChallenge/available"
        logger.debug("Requesting available virtual challenges")
        return self.connectapi(url, params={"start": start, "limit": limit})

    def get_completed_virtual_challenges(
        self, start: int = 1, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Return completed virtual (expedition) challenges.

        GET /badgechallenge-service/virtualChallenge/completed?desc=true&start&limit.
        """
        start = _validate_positive_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = f"{self.garmin_connect_badge_challenge_url}/virtualChallenge/completed"
        params = {"desc": "true", "start": start, "limit": limit}
        logger.debug("Requesting completed virtual challenges")
        return self.connectapi(url, params=params)

    def get_badge_challenge(self, challenge_uuid: str) -> dict[str, Any]:
        """Return one badge challenge.

        GET /badgechallenge-service/badgeChallenge/{uuid}.
        """
        challenge_uuid = _validate_uuid(challenge_uuid, "challenge_uuid")
        url = (
            f"{self.garmin_connect_badge_challenge_url}/badgeChallenge/{challenge_uuid}"
        )
        logger.debug("Requesting badge challenge %s", challenge_uuid)
        return self.connectapi(url)

    def get_active_adhoc_challenges(self) -> list[dict[str, Any]]:
        """Return ad-hoc (friend) challenges that are still running.

        GET /adhocchallenge-service/adHocChallenge/nonCompleted
        (``get_adhoc_challenges`` returns the historical ones).
        """
        url = f"{self.garmin_connect_adhoc_challenge_url}/nonCompleted"
        logger.debug("Requesting active ad-hoc challenges")
        return self.connectapi(url)
