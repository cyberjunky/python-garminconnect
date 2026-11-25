"""Dog profiles and dog activity statistics."""

from pathlib import Path
from typing import Any

from ..exceptions import (
    GarminConnectConnectionError,
    GarminConnectInvalidFileFormatError,
)
from ._common import (
    DOG_PHOTO_CONTENT_TYPES,
    VALID_DOG_GENDERS,
    VALID_DOG_STATS_METRICS,
    VALID_DOG_STATUSES,
    _coerce_positive_id,
    _validate_date_format,
    _validate_date_range,
    _validate_positive_number,
    logger,
)
from .base import GarminBase


def _dog_fields(
    *,
    name: str | None,
    primary_breed_id: int | str | None,
    secondary_breed_ids: list[int | str] | None,
    gender: str | None,
    is_neutered: bool | None,
    weight_grams: float | None,
    birthdate: str | None,
) -> dict[str, Any]:
    """Validate the given dog fields and return them keyed as Garmin names them."""
    fields: dict[str, Any] = {}
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        fields["name"] = name
    if primary_breed_id is not None:
        fields["primaryBreedId"] = _coerce_positive_id(
            primary_breed_id, "primary_breed_id"
        )
    if secondary_breed_ids is not None:
        if not isinstance(secondary_breed_ids, list):
            raise ValueError("secondary_breed_ids must be a list")
        fields["secondaryBreedIds"] = [
            _coerce_positive_id(b, "secondary_breed_id") for b in secondary_breed_ids
        ]
    if gender is not None:
        if not isinstance(gender, str):
            raise ValueError("gender must be a string")
        if gender not in VALID_DOG_GENDERS:
            raise ValueError(
                f"gender must be one of {sorted(VALID_DOG_GENDERS)}, got: {gender}"
            )
        fields["gender"] = gender
    if is_neutered is not None:
        if not isinstance(is_neutered, bool):
            raise ValueError("is_neutered must be a boolean")
        fields["isNeutered"] = is_neutered
    if weight_grams is not None:
        fields["weight"] = _validate_positive_number(weight_grams, "weight_grams")
    if birthdate is not None:
        fields["birthdate"] = _validate_date_format(birthdate, "birthdate")
        fields["birthdatePrecision"] = "day"
    return fields


class DogsMixin(GarminBase):
    """Dog profiles and dog activity statistics."""

    def get_dogs(self, status: str | None = None) -> list[dict[str, Any]]:
        """Return the dog profiles on the account (weight in grams).

        GET https://gcx.<domain>/family-api/profile-service/profile/pets[?status=active|retired].
        """
        params: dict[str, str] = {}
        if status is not None:
            if not isinstance(status, str):
                raise ValueError("status must be a string")
            if status not in VALID_DOG_STATUSES:
                raise ValueError(
                    f"status must be one of {sorted(VALID_DOG_STATUSES)}, got: {status}"
                )
            params["status"] = status
        logger.debug("Requesting dogs")
        return self.connectapi(self.garmin_connect_pet_profile_url, params=params)

    def get_dog(self, dog_id: int | str) -> dict[str, Any]:
        """Return one dog profile.

        GET https://gcx.<domain>/family-api/profile-service/profile/pets/{dogId}.
        """
        dog_id = _coerce_positive_id(dog_id, "dog_id")
        url = f"{self.garmin_connect_pet_profile_url}/{dog_id}"
        logger.debug("Requesting dog %s", dog_id)
        return self.connectapi(url)

    def get_dog_breeds(self) -> dict[str, str]:
        """Return the dog breeds as a map of breed id to breed key.

        GET https://gcx.<domain>/family-api/profile-service/profile/pets/dog/breeds.
        """
        url = f"{self.garmin_connect_pet_profile_url}/dog/breeds"
        logger.debug("Requesting dog breeds")
        return self.connectapi(url)

    def get_dog_lifetime_stats(self, metrics: list[str] | None = None) -> Any:
        """Return lifetime totals of activities with dogs.

        GET /fitnessstats-service/activity-animal/dog/stats/lifetime?metric&metric.
        ``metrics`` defaults to ``["distance", "duration"]``, the only ones the
        web app sends.
        """
        if metrics is None:
            metrics = ["distance", "duration"]
        if not isinstance(metrics, list) or not metrics:
            raise ValueError("metrics must be a non-empty list")
        for metric in metrics:
            if not isinstance(metric, str):
                raise ValueError("metrics must be strings")
            if metric not in VALID_DOG_STATS_METRICS:
                raise ValueError(
                    f"metrics must be one of {sorted(VALID_DOG_STATS_METRICS)}, "
                    f"got: {metric}"
                )
        url = (
            f"{self.garmin_connect_fitnessstats_service_url}"
            "/activity-animal/dog/stats/lifetime"
        )
        logger.debug("Requesting dog lifetime stats")
        return self.connectapi(url, params={"metric": metrics})

    def get_dog_stats(
        self, dog_ids: list[int | str], start: str, end: str
    ) -> list[dict[str, Any]]:
        """Return per-day activity stats for dogs over a date range.

        POST /fitnessstats-service/activity-animal/dog/stats/bulk?startDate&endDate
        with a list of dog ids as the body; the call only reads. Like the other
        read-only POSTs, errors are not mapped to the library's error types.
        """
        if not isinstance(dog_ids, list) or not dog_ids:
            raise ValueError("dog_ids must be a non-empty list")
        ids = [_coerce_positive_id(dog_id, "dog_id") for dog_id in dog_ids]
        start, end = _validate_date_range(start, end)
        url = (
            f"{self.garmin_connect_fitnessstats_service_url}"
            "/activity-animal/dog/stats/bulk"
        )
        logger.debug("Requesting dog stats %s to %s", start, end)
        return self.client.post(
            "connectapi",
            url,
            params={"startDate": start, "endDate": end},
            json=ids,
            api=True,
        )

    def get_dog_activities_enabled(self) -> Any:
        """Return whether the dog activities feature is enabled.

        GET /userprofile-service/userprofile/optional-feature/dog-activities.
        """
        url = f"{self.garmin_connect_userprofile_url}/optional-feature/dog-activities"
        logger.debug("Requesting dog activities feature")
        return self.connectapi(url)

    def create_dog(
        self,
        name: str,
        primary_breed_id: int | str | None = None,
        secondary_breed_ids: list[int | str] | None = None,
        gender: str | None = None,
        is_neutered: bool | None = None,
        weight_grams: float | None = None,
        birthdate: str | None = None,
    ) -> dict[str, Any]:
        """Create a dog profile and return it.

        POST https://gcx.<domain>/family-api/profile-service/profile/pets with
        the body the web app's "Add Dog" form sends. Breed ids come from
        :meth:`get_dog_breeds`, ``gender`` is ``female`` or ``male``,
        ``weight_grams`` is in grams whatever the account's unit setting, and
        ``birthdate`` is sent with day precision. Verified live.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        fields = _dog_fields(
            name=name,
            primary_breed_id=primary_breed_id,
            secondary_breed_ids=secondary_breed_ids,
            gender=gender,
            is_neutered=is_neutered,
            weight_grams=weight_grams,
            birthdate=birthdate,
        )
        payload = {
            "name": fields["name"],
            "primaryBreedId": fields.get("primaryBreedId"),
            "secondaryBreedIds": fields.get("secondaryBreedIds"),
            "gender": fields.get("gender"),
            "isNeutered": fields.get("isNeutered"),
            "weight": fields.get("weight"),
            "birthdate": fields.get("birthdate"),
            "birthdatePrecision": fields.get("birthdatePrecision"),
        }
        logger.debug("Creating dog")
        return self.client.post(
            "connectapi", self.garmin_connect_pet_profile_url, json=payload, api=True
        )

    def update_dog(
        self,
        dog_id: int | str,
        *,
        name: str | None = None,
        primary_breed_id: int | str | None = None,
        secondary_breed_ids: list[int | str] | None = None,
        gender: str | None = None,
        is_neutered: bool | None = None,
        weight_grams: float | None = None,
        birthdate: str | None = None,
    ) -> dict[str, Any]:
        """Edit a dog profile and return the updated dog.

        PUT https://gcx.<domain>/family-api/profile-service/profile/pets/{dogId}
        with every field, as the web app's edit form sends it: the current
        dog is fetched with :meth:`get_dog`, the given fields are replaced and
        the whole body is sent back. Only the given keyword arguments change;
        ``secondary_breed_ids=[]`` clears the secondary breeds. Units are as in
        :meth:`create_dog`. Like the web app, a retired dog cannot be edited;
        re-activate it with :meth:`set_dog_status` first. Verified live: only
        the given fields change.
        """
        dog_id = _coerce_positive_id(dog_id, "dog_id")
        changes = _dog_fields(
            name=name,
            primary_breed_id=primary_breed_id,
            secondary_breed_ids=secondary_breed_ids,
            gender=gender,
            is_neutered=is_neutered,
            weight_grams=weight_grams,
            birthdate=birthdate,
        )
        if not changes:
            raise ValueError("no fields to update")
        current = self.get_dog(dog_id)
        if not isinstance(current, dict) or not current:
            raise GarminConnectConnectionError(f"Dog {dog_id} not found")
        if current.get("status") == "retired":
            raise ValueError(
                "You must unretire this dog before you can edit its profile "
                "(set_dog_status(dog_id, 'active'))"
            )
        primary = current.get("primaryBreed") or {}
        payload = {
            "name": current.get("name"),
            "primaryBreedId": primary.get("id"),
            "secondaryBreedIds": [
                b.get("id") for b in current.get("secondaryBreeds") or []
            ],
            "gender": current.get("gender"),
            "isNeutered": current.get("isNeutered"),
            "weight": current.get("weight"),
            "birthdate": current.get("birthdate"),
            "birthdatePrecision": current.get("birthdatePrecision"),
            **changes,
        }
        url = f"{self.garmin_connect_pet_profile_url}/{dog_id}"
        logger.debug("Updating dog %s: %s", dog_id, sorted(changes))
        return self.client.put("connectapi", url, json=payload, api=True)

    def set_dog_status(self, dog_id: int | str, status: str) -> Any:
        """Retire or re-activate a dog.

        PUT https://gcx.<domain>/family-api/profile-service/profile/pets/{dogId}/status
        with ``{"status": "retired"|"active"}``; Garmin answers 204. Verified
        live in both directions.
        """
        dog_id = _coerce_positive_id(dog_id, "dog_id")
        if not isinstance(status, str):
            raise ValueError("status must be a string")
        if status not in VALID_DOG_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(VALID_DOG_STATUSES)}, got: {status}"
            )
        url = f"{self.garmin_connect_pet_profile_url}/{dog_id}/status"
        logger.debug("Setting dog %s status %s", dog_id, status)
        return self._json_or_none(
            self.client.put("connectapi", url, json={"status": status})
        )

    def delete_dog(self, dog_id: int | str) -> Any:
        """Delete a dog profile.

        DELETE https://gcx.<domain>/family-api/profile-service/profile/pets/{dogId}
        (the web app's "Delete dog"); a missing dog gives a 404. Verified live.
        """
        dog_id = _coerce_positive_id(dog_id, "dog_id")
        url = f"{self.garmin_connect_pet_profile_url}/{dog_id}"
        logger.debug("Deleting dog %s", dog_id)
        return self._json_or_none(self.client.delete("connectapi", url))

    def upload_dog_photo(self, dog_id: int | str, photo_path: str) -> dict[str, Any]:
        """Upload or replace a dog's profile photo (PNG, JPEG or GIF).

        POST https://gcx.<domain>/family-api/profile-service/profile/pet/{dogId}/photo
        (``pet``, singular) as multipart with one ``photo`` part, as the web
        app sends it. Returns ``mediaUuid`` and ``photoAccessList``, whose URLs
        are presigned and expire after about 24 hours. Verified live.
        """
        dog_id = _coerce_positive_id(dog_id, "dog_id")
        if not photo_path:
            raise ValueError("photo_path cannot be empty")
        if not isinstance(photo_path, str):
            raise ValueError("photo_path must be a string")
        p = Path(photo_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p.name}")
        if not p.is_file():
            raise ValueError(f"path is not a file: {p.name}")
        extension = p.suffix.lstrip(".").lower()
        content_type = DOG_PHOTO_CONTENT_TYPES.get(extension)
        if content_type is None:
            allowed_formats = ", ".join(sorted(DOG_PHOTO_CONTENT_TYPES))
            raise GarminConnectInvalidFileFormatError(
                f"Invalid file format '{extension}'. Allowed formats: {allowed_formats}"
            )
        try:
            data = p.read_bytes()
        except OSError as e:
            raise GarminConnectConnectionError(
                f"Failed to read file {p.name}: {e}"
            ) from e
        url = f"{self.garmin_connect_pet_photo_url}/{dog_id}/photo"
        files = {"photo": (f"pet-profile-photo.{extension}", data, content_type)}
        logger.debug("Uploading photo for dog %s", dog_id)
        return self.client.post("connectapi", url, files=files, api=True)
