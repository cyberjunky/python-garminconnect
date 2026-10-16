"""Gear (shoes, bikes, ...) and its link to activities."""

from typing import Any

from ..exceptions import GarminConnectConnectionError
from ._common import (
    MAX_ACTIVITY_LIMIT,
    _coerce_positive_id,
    _validate_date_format,
    _validate_non_negative_integer,
    _validate_positive_integer,
    _validate_positive_number,
    _validate_sport_key,
    _validate_uuid,
    logger,
)
from .base import GarminBase

# Fields of a gear-service v2 gear object that ``update_gear`` lets callers
# change; everything else (uuid, usage counters, images, ...) is read-only.
_GEAR_EDITABLE_FIELDS = frozenset(
    {
        "gearType",
        "brand",
        "model",
        "name",
        "firstUseDate",
        "usageType",
        "maxUsageDistanceMeters",
        "maxUsageDurationSeconds",
        "notes",
        "associatedActivityTypes",
    }
)


def _gear_distance_meters(max_usage_distance_km: float) -> int:
    """Convert a retirement threshold in km to the integer meters Garmin stores."""
    meters = round(
        _validate_positive_number(max_usage_distance_km, "max_usage_distance_km") * 1000
    )
    if meters < 1:
        raise ValueError(
            "max_usage_distance_km must be at least 0.001 (1 meter) — "
            "a smaller value would round down to 0, which means "
            "'no threshold' rather than the value requested"
        )
    return meters


def _gear_duration_seconds(max_usage_duration_min: float) -> int:
    """Convert a retirement threshold in minutes to the integer seconds Garmin stores."""
    seconds = round(
        _validate_positive_number(max_usage_duration_min, "max_usage_duration_min") * 60
    )
    if seconds < 1:
        raise ValueError(
            "max_usage_duration_min must be at least 1/60 (1 second) — "
            "a smaller value would round down to 0, which means "
            "'no threshold' rather than the value requested"
        )
    return seconds


def _gear_activity_types(activity_type_keys: list[str] | None) -> list[dict[str, Any]]:
    """Build the ``associatedActivityTypes`` list from lowercase activity type keys."""
    if activity_type_keys is not None and not isinstance(activity_type_keys, list):
        raise ValueError("activity_type_keys must be a list of strings")
    result = []
    for key in activity_type_keys or []:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("activity_type_keys entries must be non-empty strings")
        result.append(
            {"activityTypeKey": key, "defaultGear": True, "preferredGear": False}
        )
    return result


class GearMixin(GarminBase):
    """Gear (shoes, bikes, ...) and its link to activities."""

    def get_gear(self, userProfileNumber: str) -> dict[str, Any]:
        """Return the gear of a user profile number (legacy ``filterGear`` endpoint).

        This record does not include ``notes``; use :meth:`get_gear_list` or
        :meth:`get_gear_details` (gear-service v2) for the full gear object.
        """
        userProfileNumber = str(
            _coerce_positive_id(userProfileNumber, "userProfileNumber")
        )
        url = self.garmin_connect_gear
        logger.debug("Requesting gear for user %s", userProfileNumber)

        return self.connectapi(url, params={"userProfilePk": userProfileNumber})

    def create_gear(
        self,
        gear_type: str,
        brand: str,
        model: str,
        name: str,
        first_use_date: str,
        usage_type: str = "DISTANCE",
        max_usage_distance_km: float | None = None,
        max_usage_duration_min: float | None = None,
        notes: str = "",
        activity_type_keys: list[str] | None = None,
    ) -> Any:
        """Create a new piece of gear (e.g. a pair of shoes) and return it.

        Mirrors the payload the Garmin Connect web "Add Gear" form sends to
        ``gear-service/gear/v2``. Only ``gear_type="SHOES"`` and
        ``usage_type="DISTANCE"`` have been confirmed against a real
        account; other gear/usage type values are almost certainly also
        SCREAMING_SNAKE_CASE (e.g. "BIKE", "TIME") but are unverified — if
        one is rejected, check the "Gear Type"/"Usage Tracking" dropdown
        option values on the Garmin Connect "Add Gear" page.

        :param gear_type: Gear category, e.g. "SHOES".
        :param brand: Brand/make name, e.g. "Anta".
        :param model: Model name, e.g. "A-Flash".
        :param name: Nickname shown in Garmin Connect, e.g. "Test".
        :param first_use_date: Date gear was first used, "YYYY-MM-DD".
        :param usage_type: How usage is tracked, e.g. "DISTANCE" or "TIME".
        :param max_usage_distance_km: Optional retirement threshold in km.
        :param max_usage_duration_min: Optional retirement threshold in minutes.
        :param notes: Optional free-text notes.
        :param activity_type_keys: Optional activity type keys (e.g.
            ["running"], lowercase — matching :meth:`get_activities`'
            ``activitytype``, not :meth:`set_gear_default`'s uppercase
            convention) to associate as default gear for those activities.
        :return: The created gear record from Garmin.
        """
        gear_type = _validate_sport_key(gear_type, "gear_type")
        usage_type = _validate_sport_key(usage_type, "usage_type")
        if not isinstance(brand, str) or not brand.strip():
            raise ValueError("brand must be a non-empty string")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        first_use_date = _validate_date_format(first_use_date, "first_use_date")

        payload = {
            "uuid": None,
            "gearType": gear_type,
            "brand": brand,
            "model": model,
            "name": name,
            "firstUseDate": first_use_date,
            "maxUsageDate": None,
            "maxUsageDistanceMeters": (
                _gear_distance_meters(max_usage_distance_km)
                if max_usage_distance_km is not None
                else 0
            ),
            "maxUsageDurationSeconds": (
                _gear_duration_seconds(max_usage_duration_min)
                if max_usage_duration_min is not None
                else 0
            ),
            "usageType": usage_type,
            "notes": notes,
            "associatedActivityTypes": _gear_activity_types(activity_type_keys),
        }

        url = f"{self.garmin_connect_gear_baseurl}/v2"
        logger.debug("Creating gear: %s", payload)
        return self.client.post("connectapi", url, json=payload, api=True)

    def get_gear_stats(self, gearUUID: str) -> dict[str, Any]:
        """Return statistics (e.g. distance) for specific gear UUID."""
        gearUUID = _validate_uuid(gearUUID, "gearUUID")
        url = f"{self.garmin_connect_gear_baseurl}/stats/{gearUUID}"
        logger.debug("Requesting gear stats for gearUUID %s", gearUUID)

        try:
            return self.connectapi(url)
        except GarminConnectConnectionError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 404:
                logger.warning(
                    "Gear stats not found for UUID %s (likely retired/removed gear)",
                    gearUUID,
                )
                return {}
            raise

    def get_gear_defaults(self, userProfileNumber: str) -> dict[str, Any]:
        """Return the default gear per activity type."""
        userProfileNumber = str(
            _coerce_positive_id(userProfileNumber, "userProfileNumber")
        )
        url = (
            f"{self.garmin_connect_gear_baseurl}/user/{userProfileNumber}/activityTypes"
        )
        logger.debug("Requesting gear defaults for user %s", userProfileNumber)
        return self.connectapi(url)

    def set_gear_default(
        self, activityType: str, gearUUID: str, defaultGear: bool = True
    ) -> Any:
        """Make gear the default for an activity type, or remove it as the default.

        Uses the legacy ``gear-service/gear/{uuid}/activityType/...`` endpoint
        with the undashed uuid from :meth:`get_gear`. Gear created through the
        v2 API (``create_gear`` / the current web app) is not found there
        (404); for such gear set ``activity_type_keys`` with
        :meth:`update_gear` instead, which writes ``associatedActivityTypes``.
        """
        activityType = _validate_sport_key(activityType, "activityType")
        gearUUID = _validate_uuid(gearUUID, "gearUUID")
        defaultGearString = "/default/true" if defaultGear else ""
        method_override = "PUT" if defaultGear else "DELETE"
        url = (
            f"{self.garmin_connect_gear_baseurl}/{gearUUID}/"
            f"activityType/{activityType}{defaultGearString}"
        )

        try:
            return self.client.request(method_override, "connectapi", url, api=True)
        except GarminConnectConnectionError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 404:
                raise GarminConnectConnectionError(
                    f"Cannot set gear default for UUID {gearUUID}: gear not found (likely retired/removed)"
                ) from e
            raise

    def get_activity_gear(self, activity_id: int | str) -> dict[str, Any]:
        """Return the gear linked to an activity."""
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        params = {
            "activityId": activity_id,
        }
        url = self.garmin_connect_gear
        logger.debug("Requesting gear for activity_id %s", activity_id)

        return self.connectapi(url, params=params)

    def get_gear_activities(
        self, gearUUID: str, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Return the activities a piece of gear was used in.
        :param gearUUID: UUID of the gear to get activities for
        :param limit: Maximum number of activities to return (default: 1000)
        :return: List of activities where the specified gear was used.
        """
        gearUUID = _validate_uuid(gearUUID, "gearUUID")
        limit = _validate_positive_integer(limit, "limit")
        # Optional: enforce a reasonable ceiling to avoid heavy responses
        limit = min(limit, MAX_ACTIVITY_LIMIT)
        url = f"{self.garmin_connect_activities_baseurl}{gearUUID}/gear"
        logger.debug("Requesting activities for gearUUID %s", gearUUID)

        try:
            return self.connectapi(url, params={"start": 0, "limit": limit})
        except GarminConnectConnectionError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 404:
                logger.warning(
                    "Gear activities not found for UUID %s (likely retired/removed gear)",
                    gearUUID,
                )
                return []
            raise

    def add_gear_to_activity(
        self, gearUUID: str, activity_id: int | str
    ) -> dict[str, Any]:
        """Link gear to an activity. Requires a gearUUID and an activity_id.

        Args:
            gearUUID: UID for gear to add to activity. Findable though the get_gear function
            activity_id: Integer ID for the activity to add the gear to

        Returns:
            Dictionary containing information for the added gear

        """
        gearUUID = _validate_uuid(gearUUID, "gearUUID")
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))

        url = (
            f"{self.garmin_connect_gear_baseurl}/link/{gearUUID}/activity/{activity_id}"
        )
        logger.debug("Linking gear %s to activity %s", gearUUID, activity_id)

        try:
            return self.client.put("connectapi", url).json()
        except GarminConnectConnectionError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 404:
                raise GarminConnectConnectionError(
                    f"Cannot add gear {gearUUID} to activity {activity_id}: gear not found (likely retired/removed)"
                ) from e
            raise

    def remove_gear_from_activity(
        self, gearUUID: str, activity_id: int | str
    ) -> dict[str, Any]:
        """Unlink gear from an activity. Requires a gearUUID and an activity_id.

        Args:
            gearUUID: UID for gear to remove from activity. Findable though the get_gear method.
            activity_id: Integer ID for the activity to remove the gear from

        Returns:
            Dictionary containing information about the removed gear

        """
        gearUUID = _validate_uuid(gearUUID, "gearUUID")
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))

        url = f"{self.garmin_connect_gear_baseurl}/unlink/{gearUUID}/activity/{activity_id}"
        logger.debug("Unlinking gear %s from activity %s", gearUUID, activity_id)

        try:
            return self.client.put("connectapi", url).json()
        except GarminConnectConnectionError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 404:
                raise GarminConnectConnectionError(
                    f"Cannot remove gear {gearUUID} from activity {activity_id}: gear not found (likely retired/removed)"
                ) from e
            raise

    def get_gear_list(
        self,
        start: int = 0,
        limit: int = 20,
        gear_statuses: list[str] | None = None,
        gear_type: str | None = None,
        sort_order: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return the user's gear from the v2 endpoint the web app uses.

        GET /gear-service/gear/v2/list?start&limit[&gearStatuses][&gearType]
        [&sortOrder]. Entries carry a dashed ``uuid`` for the other v2 calls
        (``get_gear`` returns the legacy undashed uuids).
        """
        start = _validate_non_negative_integer(start, "start")
        limit = _validate_positive_integer(limit, "limit")
        url = f"{self.garmin_connect_gear_service_url}/gear/v2/list"
        params: dict[str, Any] = {"start": start, "limit": limit}
        if gear_statuses:
            params["gearStatuses"] = [str(s).strip().upper() for s in gear_statuses]
        if gear_type:
            params["gearType"] = gear_type.strip().upper()
        if sort_order:
            params["sortOrder"] = sort_order.strip().upper()
        logger.debug("Requesting gear list")
        return self.connectapi(url, params=params)

    def get_gear_details(self, gear_uuid: str) -> dict[str, Any]:
        """Return one piece of gear (v2, dashed uuid).

        GET /gear-service/gear/v2/{uuid}.
        """
        gear_uuid = _validate_uuid(gear_uuid, "gear_uuid")
        url = f"{self.garmin_connect_gear_service_url}/gear/v2/{gear_uuid}"
        logger.debug("Requesting gear %s", gear_uuid)
        return self.connectapi(url)

    def set_gear_status(self, gear_uuid: str, status: str) -> Any:
        """Retire or re-activate gear.

        PUT /gear-service/gear/v2/{uuid}/status/{ACTIVE|RETIRED} with no body.
        """
        gear_uuid = _validate_uuid(gear_uuid, "gear_uuid")
        status = status.strip().upper()
        if status not in {"ACTIVE", "RETIRED"}:
            raise ValueError("status must be 'ACTIVE' or 'RETIRED'")
        url = f"{self.garmin_connect_gear_service_url}/gear/v2/{gear_uuid}/status/{status}"
        logger.debug("Setting gear %s status %s", gear_uuid, status)
        return self._json_or_none(self.client.put("connectapi", url))

    def update_gear(
        self,
        gear_uuid: str,
        *,
        name: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        gear_type: str | None = None,
        first_use_date: str | None = None,
        usage_type: str | None = None,
        max_usage_distance_km: float | None = None,
        max_usage_duration_min: float | None = None,
        notes: str | None = None,
        activity_type_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Edit a piece of gear and return the updated gear object.

        PUT /gear-service/gear/v2/{uuid} with the **complete** gear object —
        Garmin rejects partial bodies (HTTP 400), so the current object is
        fetched with :meth:`get_gear_details`, the given fields are replaced
        and the whole thing is sent back, exactly like the web app's edit
        form. Only the given keyword arguments change; ``notes=""`` clears the
        note, ``max_usage_distance_km=0`` / ``max_usage_duration_min=0``
        remove a retirement threshold. Use :meth:`set_gear_status` to retire
        or re-activate gear. Verified live: the note persists and is shown
        in Garmin Connect.

        Args:
            gear_uuid: dashed uuid from :meth:`get_gear_list` /
                :meth:`get_gear_details`.
            activity_type_keys: lowercase activity type keys (e.g.
                ``["running"]``) this gear is the default for; replaces the
                current association list.

        """
        gear_uuid = _validate_uuid(gear_uuid, "gear_uuid")
        current = self.get_gear_details(gear_uuid)
        if not isinstance(current, dict) or not current:
            raise GarminConnectConnectionError(f"Gear {gear_uuid} not found")
        payload = dict(current)

        for key, value in (("name", name), ("brand", brand), ("model", model)):
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{key} must be a non-empty string")
                payload[key] = value
        if gear_type is not None:
            payload["gearType"] = _validate_sport_key(gear_type, "gear_type")
        if usage_type is not None:
            payload["usageType"] = _validate_sport_key(usage_type, "usage_type")
        if first_use_date is not None:
            payload["firstUseDate"] = _validate_date_format(
                first_use_date, "first_use_date"
            )
        if max_usage_distance_km is not None:
            payload["maxUsageDistanceMeters"] = (
                0
                if max_usage_distance_km == 0
                else _gear_distance_meters(max_usage_distance_km)
            )
        if max_usage_duration_min is not None:
            payload["maxUsageDurationSeconds"] = (
                0
                if max_usage_duration_min == 0
                else _gear_duration_seconds(max_usage_duration_min)
            )
        if notes is not None:
            if not isinstance(notes, str):
                raise ValueError("notes must be a string")
            payload["notes"] = notes
        if activity_type_keys is not None:
            payload["associatedActivityTypes"] = _gear_activity_types(
                activity_type_keys
            )

        url = f"{self.garmin_connect_gear_service_url}/gear/v2/{gear_uuid}"
        logger.debug("Updating gear %s", gear_uuid)
        self.client.put("connectapi", url, json=payload)
        return self.get_gear_details(gear_uuid)

    def delete_gear(self, gear_uuid: str) -> Any:
        """Delete a piece of gear.

        DELETE /gear-service/gear/v2/{uuid} (the web app's "Delete gear").
        """
        gear_uuid = _validate_uuid(gear_uuid, "gear_uuid")
        url = f"{self.garmin_connect_gear_service_url}/gear/v2/{gear_uuid}"
        logger.debug("Deleting gear %s", gear_uuid)
        return self._json_or_none(self.client.delete("connectapi", url))

    def get_gear_types(self) -> list[dict[str, Any]]:
        """Return the gear types Garmin knows (shoes, bike, ...).

        GET /gear-service/gear/types.
        """
        url = f"{self.garmin_connect_gear_service_url}/gear/types"
        logger.debug("Requesting gear types")
        return self.connectapi(url)

    def get_user_gear_types(self) -> dict[str, Any]:
        """Return the gear types the user actually has (``activeGearTypes``).

        GET /gear-service/gear/v2/user-gear-types.
        """
        url = f"{self.garmin_connect_gear_service_url}/gear/v2/user-gear-types"
        logger.debug("Requesting user gear types")
        return self.connectapi(url)

    def get_gear_make_models(self, keywords: str) -> Any:
        """Search Garmin's make/model catalogue for the gear form's autocomplete.

        GET /gear-service/gear/makemodels?keywords=.
        """
        if not isinstance(keywords, str) or not keywords.strip():
            raise ValueError("keywords must be a non-empty string")
        url = f"{self.garmin_connect_gear_service_url}/gear/makemodels"
        logger.debug("Requesting gear make/models")
        return self.connectapi(url, params={"keywords": keywords.strip()})

    def get_activity_gear_v2(self, activity_id: int | str) -> list[dict[str, Any]]:
        """Return the gear linked to an activity (v2 endpoint).

        GET /gear-service/activity/v2/{activityId} (``get_activity_gear`` is
        the legacy ``filterGear?activityId=`` variant).
        """
        activity_id = str(_coerce_positive_id(activity_id, "activity_id"))
        url = f"{self.garmin_connect_gear_service_url}/activity/v2/{activity_id}"
        logger.debug("Requesting gear for activity %s (v2)", activity_id)
        return self.connectapi(url)
