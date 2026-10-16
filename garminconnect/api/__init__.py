"""The :class:`Garmin` class, assembled from one mixin per data domain."""

from .achievements import AchievementsMixin
from .activities import ActivitiesMixin
from .base import GarminBase
from .body import BodyMixin
from .devices import DevicesMixin
from .gear import GearMixin
from .golf import GolfMixin
from .health import HealthMixin
from .metrics import MetricsMixin
from .training import TrainingMixin
from .womens_health import WomensHealthMixin
from .workouts import WorkoutsMixin


class Garmin(
    ActivitiesMixin,
    HealthMixin,
    MetricsMixin,
    BodyMixin,
    AchievementsMixin,
    GearMixin,
    DevicesMixin,
    WorkoutsMixin,
    TrainingMixin,
    WomensHealthMixin,
    GolfMixin,
    GarminBase,
):
    """Class for fetching data from Garmin Connect."""


__all__ = ["Garmin"]
