"""Regression tests for the split into the ``api`` and ``client`` packages."""

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest

import garminconnect
from garminconnect import client as client_mod

pytest.importorskip("pydantic")

TEST_DATA = Path(__file__).parent.parent / "test_data"

TYPED_UPLOADS = ["running", "cycling", "swimming", "strength"]


@pytest.mark.parametrize("kind", TYPED_UPLOADS)
def test_typed_workout_upload_sends_the_workout(kind, monkeypatch):
    """Each upload_<kind>_workout() accepts its typed workout and posts it.

    The methods import the workout classes lazily; after the move into
    ``garminconnect.api`` a wrong relative import made every call fail with a
    misleading "Pydantic is required" error.
    """
    monkeypatch.syspath_prepend(str(TEST_DATA))
    sample = importlib.import_module(f"sample_{kind}_workout")
    workout = getattr(sample, f"create_sample_{kind}_workout")()

    garmin = garminconnect.Garmin("test@example.com", "password")
    with patch.object(garmin, "upload_workout", return_value={"workoutId": 1}) as up:
        result = getattr(garmin, f"upload_{kind}_workout")(workout)

    assert result == {"workoutId": 1}
    up.assert_called_once_with(workout.to_dict())


@pytest.mark.parametrize("kind", TYPED_UPLOADS)
def test_typed_workout_upload_rejects_other_types(kind):
    garmin = garminconnect.Garmin("test@example.com", "password")
    with pytest.raises(TypeError, match="Workout instance"):
        getattr(garmin, f"upload_{kind}_workout")({"workoutName": "plain dict"})


@pytest.mark.parametrize("kind", ["walking", "hiking"])
def test_walking_and_hiking_uploads_raise(kind):
    """Garmin has no walking/hiking workout sport type; nothing is sent."""
    from garminconnect import workout as workout_mod

    cls = getattr(workout_mod, f"{kind.capitalize()}Workout")
    w = cls(workoutName="w", estimatedDurationInSecs=60, workoutSegments=[])
    garmin = garminconnect.Garmin("test@example.com", "password")
    with (
        patch.object(garmin, "upload_workout") as up,
        pytest.raises(ValueError, match=f"no {kind} workout sport type"),
    ):
        getattr(garmin, f"upload_{kind}_workout")(w)
    up.assert_not_called()


@pytest.mark.parametrize(
    "name",
    [
        "GarminConnectAuthenticationError",
        "GarminConnectConnectionError",
        "GarminConnectNotFoundError",
        "GarminConnectTooManyRequestsError",
    ],
)
def test_client_still_exports_exceptions(name):
    """The single-module client exposed these; imports from it keep working."""
    assert getattr(client_mod, name) is getattr(garminconnect, name)


@pytest.mark.parametrize(
    "name",
    [
        "_API_ERROR_STATUS_RE",
        "_API_REJECTION_HINT",
        "_CSRF_RE",
        "_OTHER_USER_HOME_RE",
        "_QUERY_VALUE_RE",
        "_TITLE_RE",
        "_WIDGET_MFA_VARS_RE",
    ],
)
def test_client_still_exports_private_constants(name):
    assert hasattr(client_mod, name)
