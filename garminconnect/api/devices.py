"""Devices, their settings, sensors and solar data."""

from typing import Any

from ..exceptions import GarminConnectConnectionError
from ._common import (
    _coerce_positive_id,
    _validate_date_format,
    _validate_date_range,
    logger,
)
from .base import GarminBase


class DevicesMixin(GarminBase):
    """Devices, their settings, sensors and solar data."""

    def get_devices(self) -> list[dict[str, Any]]:
        """Return available devices for the current user account."""
        url = self.garmin_connect_devices_url
        logger.debug("Requesting devices")

        return self.connectapi(url)

    def get_device_settings(self, device_id: str) -> dict[str, Any]:
        """Return device settings for device with 'device_id'."""
        device_id = str(_coerce_positive_id(device_id, "device_id"))
        url = f"{self.garmin_connect_device_url}/device-info/settings/{device_id}"
        logger.debug("Requesting device settings")

        return self.connectapi(url)

    def get_primary_training_device(self) -> dict[str, Any]:
        """Return the primary training device and the priority order of all devices."""
        url = self.garmin_connect_primary_device_url
        logger.debug("Requesting primary training device information")

        return self.connectapi(url)

    def get_device_solar_data(
        self, device_id: str, startdate: str, enddate: str | None = None
    ) -> list[dict[str, Any]]:
        """Return solar data for compatible device with 'device_id'."""
        if enddate is None:
            enddate = startdate
            single_day = True
        else:
            single_day = False

        startdate = _validate_date_format(startdate, "startdate")
        enddate = _validate_date_format(enddate, "enddate")
        device_id = str(_coerce_positive_id(device_id, "device_id"))
        params = {"singleDayView": single_day}

        url = f"{self.garmin_connect_solar_url}/{device_id}/{startdate}/{enddate}"

        resp = self.connectapi(url, params=params)
        if not resp or "deviceSolarInput" not in resp:
            raise GarminConnectConnectionError("No device solar input data received")
        return resp["deviceSolarInput"]

    def get_device_alarms(self) -> list[Any]:
        """Return the active alarms of all devices."""
        logger.debug("Requesting device alarms")

        alarms = []
        devices = self.get_devices()
        for device in devices:
            device_settings = self.get_device_settings(device["deviceId"])
            device_alarms = device_settings.get("alarms")
            if device_alarms is not None:
                alarms += device_alarms
        return alarms

    def get_device_last_used(self) -> dict[str, Any]:
        """Return the device that synced last."""
        url = f"{self.garmin_connect_device_url}/mylastused"
        logger.debug("Requesting device last used")

        return self.connectapi(url)

    def push_workout_to_device(
        self, workout_id: int | str | None = None, device_id: int | str | None = None
    ) -> dict[str, Any]:
        """Push a workout to a device.

        Args:
            workout_id: The workout ID returned after uploading. If not provided, will push last workout in the library.
            device_id: Optional device ID to push the workout to. If not provided,  will choose the last used device.

        Returns:
            Dictionary containing the result of the push operation.

        """
        if device_id is None:
            device_id = self.get_device_last_used()["userDeviceId"]

        device_id = _coerce_positive_id(device_id, "device_id")

        if workout_id is None:
            workouts = self.get_workouts(start=0, limit=1)
            if not workouts:
                raise ValueError("No workouts found to push.")
            workout_id = workouts[0]["workoutId"]

        workout_id = _coerce_positive_id(workout_id, "workout_id")
        workout_name = self.get_workout_by_id(workout_id)["workoutName"]

        url = self.garmin_connect_devicemessage_url

        payload = [
            {
                "deviceId": device_id,
                "messageUrl": f"workout-service/workout/FIT/{workout_id}",
                "messageType": "workouts",
                "groupName": None,
                "messageName": workout_name,
                "priority": 1,
                "fileType": "FIT",
                "metaDataId": workout_id,
            }
        ]

        logger.debug("Pushing workout %s to device %s", workout_id, device_id)
        return self.client.post("connectapi", url, json=payload, api=True)

    def get_all_devices(self) -> list[dict[str, Any]]:
        """Return all registered devices including inactive ones.

        GET /device-service/deviceregistration/devices/all/{displayName}.
        """
        url = (
            f"{self.garmin_connect_device_service_url}/deviceregistration/devices/all/"
            f"{self._require_display_name()}"
        )
        logger.debug("Requesting all devices")
        return self.connectapi(url)

    def get_historical_devices(self) -> list[dict[str, Any]]:
        """Return devices that were registered in the past.

        GET /device-service/deviceregistration/devices/historical.
        """
        url = f"{self.garmin_connect_device_service_url}/deviceregistration/devices/historical"
        logger.debug("Requesting historical devices")
        return self.connectapi(url)

    def get_active_devices(self) -> list[dict[str, Any]]:
        """Return device info for the currently active devices.

        GET /device-service/deviceservice/device-info/active/{displayName}.
        """
        url = (
            f"{self.garmin_connect_device_url}/device-info/active/"
            f"{self._require_display_name()}"
        )
        logger.debug("Requesting active devices")
        return self.connectapi(url)

    def get_user_device(self, device_id: int | str) -> dict[str, Any]:
        """Return the device's registration record (last upload/download times).

        GET /device-service/deviceservice/user-device/{deviceId}.
        """
        device_id = _coerce_positive_id(device_id, "device_id")
        url = f"{self.garmin_connect_device_url}/user-device/{device_id}"
        logger.debug("Requesting user device %s", device_id)
        return self.connectapi(url)

    def get_device_app_info(self, device_id: int | str) -> dict[str, Any]:
        """Return device type and software information.

        GET /device-service/deviceservice/app-info/device/{deviceId}.
        """
        device_id = _coerce_positive_id(device_id, "device_id")
        url = f"{self.garmin_connect_device_url}/app-info/device/{device_id}"
        logger.debug("Requesting device app info %s", device_id)
        return self.connectapi(url)

    def get_sensors(self) -> list[dict[str, Any]]:
        """Return paired external sensors (HRM, power meters, ...).

        GET /device-service/sensors.
        """
        url = f"{self.garmin_connect_device_service_url}/sensors"
        logger.debug("Requesting sensors")
        return self.connectapi(url)

    def get_device_messages(self) -> dict[str, Any]:
        """Return the queue of pending device messages (software updates, pushed workouts, ...).

        GET /device-service/devicemessage/messages.
        """
        logger.debug("Requesting device messages")
        return self.connectapi(self.garmin_connect_devicemessage_url)

    def get_device_displayed_activities(self, device_id: int | str) -> Any:
        """Return which activity profiles are shown on a device.

        GET /devicesettings-service/device/displayed-activities/{deviceId}.
        """
        device_id = _coerce_positive_id(device_id, "device_id")
        url = (
            f"{self.garmin_connect_devicesettings_url}/displayed-activities/{device_id}"
        )
        logger.debug("Requesting displayed activities for %s", device_id)
        return self.connectapi(url)

    def update_device_settings(
        self, device_id: int | str, settings: dict[str, Any]
    ) -> Any:
        """Write (partial) device settings, e.g. alarms or activity tracking options.

        PUT /device-service/deviceservice/device-info/settings/{deviceId} with
        a partial settings object such as
        ``{"activityTracking": {"moveAlertEnabled": True}}``. Start from
        ``get_device_settings`` and send only what you change. Not verified
        against a live device.
        """
        device_id = _coerce_positive_id(device_id, "device_id")
        if not isinstance(settings, dict) or not settings:
            raise ValueError("settings must be a non-empty dictionary")
        url = f"{self.garmin_connect_device_url}/device-info/settings/{device_id}"
        logger.debug("Updating device settings for %s", device_id)
        return self._json_or_none(self.client.put("connectapi", url, json=settings))

    def get_device_solar_gain(
        self, device_id: int | str, start: str, end: str
    ) -> dict[str, Any]:
        """Return daily solar gain for a device over a date range.

        GET /device-service/devicemonitoring/solargain/{deviceId}/{start}/{end}
        — the endpoint the web app uses for multi-day solar charts
        (``get_device_solar_data`` uses the web-gateway single-day view).
        """
        device_id = _coerce_positive_id(device_id, "device_id")
        start, end = _validate_date_range(start, end)
        url = (
            f"{self.garmin_connect_device_service_url}/devicemonitoring/solargain/"
            f"{device_id}/{start}/{end}"
        )
        logger.debug("Requesting solar gain for %s", device_id)
        return self.connectapi(url)

    def send_scheduled_workouts_to_devices(self) -> Any:
        """Push all scheduled workouts to the user's devices.

        PUT /workout-service/schedule/sendtodevices with no body.
        """
        url = f"{self.garmin_workouts_schedule_url}/sendtodevices"
        logger.debug("Sending scheduled workouts to devices")
        return self._json_or_none(self.client.put("connectapi", url))
