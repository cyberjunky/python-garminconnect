#!/usr/bin/env python3
"""🏃‍♂️ Comprehensive Garmin Connect API Demo.
==========================================

This is a comprehensive demonstration program showing ALL available API calls
and error handling patterns for python-garminconnect.

For a simple getting-started example, see example.py

Dependencies:
pip3 install requests readchar

Environment Variables (optional):
export GARMIN_EMAIL=<your garmin email address>
export GARMIN_PASSWORD=<your garmin password>
export GARMINTOKENS=<path to token storage>
"""

import argparse
import builtins
import datetime
import html
import json
import logging
import os
import re
import sys
import tempfile
import time
from contextlib import suppress
from datetime import timedelta
from getpass import getpass
from pathlib import Path
from typing import Any

import readchar
import requests

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectNotFoundError,
    GarminConnectTooManyRequestsError,
    parse_activity_detail_metrics,
)
from garminconnect.client import token_file_path
from garminconnect.i18n import (
    UnsupportedLanguageError,
    get_language,
    normalize_language,
    resolve_language,
    set_language,
    translate,
)

# Debug mode: enable with --debug / -d CLI flag or DEMO_DEBUG=1 env var.
# When active, shows timestamped DEBUG logs from garminconnect and the
# underlying HTTP stack (urllib3 / requests) so you can see where delays come
# from. Also consumes the flag from sys.argv so downstream code doesn't see it.
_DEBUG = bool(os.getenv("DEMO_DEBUG")) or any(a in sys.argv for a in ("-d", "--debug"))
for _flag in ("-d", "--debug"):
    while _flag in sys.argv:
        sys.argv.remove(_flag)

if _DEBUG:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    for _name in (
        "garminconnect",
        "urllib3",
        "urllib3.connectionpool",
        "requests",
    ):
        logging.getLogger(_name).setLevel(logging.DEBUG)
else:
    # Quiet known-noisy library errors to avoid double error messages
    logging.getLogger("garminconnect").setLevel(logging.CRITICAL)

_LOGGER = logging.getLogger("demo")

api: Garmin | None = None


def _open_private(path: str | Path, mode: str, encoding: str | None = None):
    """Open a new or existing export file with owner-only permissions."""
    if mode not in {"w", "wb"}:
        raise ValueError(f"Unsupported private file mode: {mode}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(Path(path), flags, 0o600)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(fd, 0o600)
        if "b" in mode:
            return os.fdopen(fd, mode)
        return os.fdopen(fd, mode, encoding=encoding or "utf-8")
    except Exception:
        os.close(fd)
        raise


def _html(value: Any) -> str:
    """Escape data returned by Garmin before inserting it into HTML."""
    return html.escape(str(value), quote=True)


def _safe_filename_component(value: Any) -> str:
    """Convert account-provided text into a single safe filename component."""
    component = re.sub(r"[^\w .-]", "_", str(value), flags=re.UNICODE).strip(" .")
    return component[:120] or "export"


def safe_readkey() -> str:
    """Safe wrapper around readchar.readkey() that handles non-TTY environments.

    This is particularly useful on macOS and in CI/CD environments where stdin
    might not be a TTY, which would cause readchar to fail with:
    termios.error: (25, 'Inappropriate ioctl for device')

    Returns:
        str: A single character input from the user

    """
    if not sys.stdin.isatty():
        print(translate("demo.not_tty"))
        user_input = input(translate("demo.enter_key"))
        return user_input[0] if user_input else ""
    try:
        return readchar.readkey()
    except Exception as e:
        print(translate("demo.readkey_failed", error=e))
        user_input = input(translate("demo.enter_key"))
        return user_input[0] if user_input else ""


class Config:
    """Configuration class for the Garmin Connect API demo."""

    def __init__(self):
        # Load environment variables
        self.email = os.getenv("GARMIN_EMAIL") or os.getenv("EMAIL")
        self.password = os.getenv("GARMIN_PASSWORD") or os.getenv("PASSWORD")
        self.tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"

        # Date settings
        self.today = datetime.date.today()
        self.week_start = self.today - timedelta(days=7)
        self.month_start = self.today - timedelta(days=30)

        # API call settings
        self.default_limit = 100
        self.start = 0
        self.start_badge = 1  # Badge related calls start counting at 1

        # Activity settings
        self.activityfile = "test_data/*.gpx"  # Supported file types: .fit .gpx .tcx
        self.workoutfile = "test_data/sample_workout.json"  # Sample workout JSON file

        # Export settings
        self.export_dir = Path("your_data")
        self.export_dir.mkdir(mode=0o700, exist_ok=True)
        if os.name != "nt":
            self.export_dir.chmod(0o700)


# Initialize configuration
config = Config()


def _demo_config_path() -> Path:
    """Return the path used for demo-only preferences."""
    return Path.home() / ".garminconnect" / "demo_config.json"


def load_persisted_language() -> str | None:
    """Load a valid persisted language without affecting authentication data."""
    try:
        with _demo_config_path().open(encoding="utf-8") as config_file:
            stored_config = json.load(config_file)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None

    if not isinstance(stored_config, dict):
        return None
    language = stored_config.get("language")
    if not isinstance(language, str):
        return None
    try:
        return normalize_language(language)
    except UnsupportedLanguageError:
        return None


def save_persisted_language(language: str) -> bool:
    """Persist only the demo language preference, using an atomic replacement."""
    path = _demo_config_path()
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump({"language": normalize_language(language)}, temporary_file)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, path)
        return True
    except (OSError, UnsupportedLanguageError, ValueError, TypeError):
        if temporary_path is not None:
            with suppress(OSError):
                temporary_path.unlink()
        return False


# Organized menu categories
menu_categories = {
    "1": {
        "name_key": "menu.user_profile",
        "options": {
            "1": {"desc_key": "menu.get_full_name", "key": "get_full_name"},
            "2": {"desc_key": "menu.get_unit_system", "key": "get_unit_system"},
            "3": {"desc_key": "menu.get_user_profile", "key": "get_user_profile"},
            "4": {
                "desc_key": "menu.get_userprofile_settings",
                "key": "get_userprofile_settings",
            },
        },
    },
    "2": {
        "name_key": "menu.daily_health",
        "options": {
            "1": {
                "desc_key": "menu.activity_data",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_stats",
            },
            "2": {
                "desc_key": "menu.user_summary",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_user_summary",
            },
            "3": {
                "desc_key": "menu.stats_body",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_stats_and_body",
            },
            "4": {
                "desc_key": "menu.steps_data",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_steps_data",
            },
            "5": {
                "desc_key": "menu.heart_rate",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_heart_rates",
            },
            "6": {
                "desc_key": "menu.resting_heart_rate",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_rhr_daily",
            },
            "7": {
                "desc_key": "menu.sleep_summaries",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_sleep_daily",
            },
            "8": {
                "desc_key": "menu.stress_data",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_all_day_stress",
            },
            "9": {
                "desc_key": "menu.lifestyle",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_lifestyle_logging_data",
            },
            "a": {
                "desc_key": "menu.daily_calories",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_calories_daily",
            },
        },
    },
    "3": {
        "name_key": "menu.advanced_health",
        "options": {
            "1": {
                "desc_key": "menu.training_readiness",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_training_readiness",
            },
            "2": {
                "desc_key": "menu.morning_training_readiness",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_morning_training_readiness",
            },
            "3": {
                "desc_key": "menu.training_status",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_training_status",
            },
            "4": {
                "desc_key": "menu.respiration",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_respiration_data",
            },
            "5": {
                "desc_key": "menu.spo2",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_spo2_data",
            },
            "6": {
                "desc_key": "menu.max_metrics",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_max_metrics_range",
            },
            "7": {
                "desc_key": "menu.hrv",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_hrv_data_range",
            },
            "8": {
                "desc_key": "menu.fitness_age",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_fitnessage_data",
            },
            "9": {
                "desc_key": "menu.stress_data",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_stress_data",
            },
            "0": {"desc_key": "menu.lactate", "key": "get_lactate_threshold"},
            "a": {
                "desc_key": "menu.intensity",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_intensity_minutes_data",
            },
            "b": {
                "desc_key": "menu.running_tolerance",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_running_tolerance",
            },
            "c": {
                "desc_key": "menu.heart_rate_zones",
                "key": "get_heart_rate_zones",
            },
            "d": {
                "desc_key": "menu.power_zones",
                "key": "get_power_zones",
            },
            "e": {
                "desc_key": "menu.cycling_power_zones",
                "key": "get_power_zones_for_sport",
            },
            "f": {
                "desc_key": "menu.ftp_range",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_functional_threshold_power_range",
            },
        },
    },
    "4": {
        "name_key": "menu.historical",
        "options": {
            "1": {
                "desc_key": "menu.daily_steps",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_daily_steps",
            },
            "2": {
                "desc_key": "menu.body_battery",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_body_battery",
            },
            "3": {
                "desc_key": "menu.floors",
                "desc_values": {"start": config.week_start.isoformat()},
                "key": "get_floors",
            },
            "4": {
                "desc_key": "menu.blood_pressure",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_blood_pressure",
            },
            "5": {
                "desc_key": "menu.progress",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_progress_summary_between_dates",
            },
            "6": {
                "desc_key": "menu.body_battery_events",
                "desc_values": {"start": config.week_start.isoformat()},
                "key": "get_body_battery_events",
            },
            "7": {
                "desc_key": "menu.weekly_steps",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_weekly_steps",
            },
            "8": {
                "desc_key": "menu.weekly_stress",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_weekly_stress",
            },
            "9": {
                "desc_key": "menu.weekly_intensity",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_weekly_intensity_minutes",
            },
        },
    },
    "5": {
        "name_key": "menu.activities",
        "options": {
            "1": {
                "desc_key": "menu.recent_activities",
                "desc_values": {"limit": config.default_limit},
                "key": "get_activities",
            },
            "2": {"desc_key": "menu.last_activity", "key": "get_last_activity"},
            "3": {
                "desc_key": "menu.activities_today",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_activities_fordate",
            },
            "4": {
                "desc_key": "menu.download_activities",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "download_activities",
            },
            "5": {
                "desc_key": "menu.activity_types",
                "key": "get_activity_types",
            },
            "6": {
                "desc_key": "menu.upload_activity",
                "desc_values": {"file": config.activityfile},
                "key": "upload_activity",
            },
            "7": {"desc_key": "menu.get_workouts", "key": "get_workouts"},
            "8": {"desc_key": "menu.activity_splits", "key": "get_activity_splits"},
            "9": {
                "desc_key": "menu.typed_splits",
                "key": "get_activity_typed_splits",
            },
            "0": {
                "desc_key": "menu.split_summaries",
                "key": "get_activity_split_summaries",
            },
            "a": {"desc_key": "menu.activity_weather", "key": "get_activity_weather"},
            "b": {
                "desc_key": "menu.activity_hr_zones",
                "key": "get_activity_hr_in_timezones",
            },
            "c": {
                "desc_key": "menu.activity_power_zones",
                "key": "get_activity_power_in_timezones",
            },
            "d": {
                "desc_key": "menu.cycling_ftp",
                "key": "get_cycling_ftp",
            },
            "e": {
                "desc_key": "menu.activity_details",
                "key": "get_activity_details",
            },
            "f": {"desc_key": "menu.activity_gear", "key": "get_activity_gear"},
            "g": {"desc_key": "menu.single_activity", "key": "get_activity"},
            "h": {
                "desc_key": "menu.strength_sets",
                "key": "get_activity_exercise_sets",
            },
            "i": {"desc_key": "menu.workout_by_id", "key": "get_workout_by_id"},
            "j": {"desc_key": "menu.download_fit", "key": "download_workout"},
            "k": {
                "desc_key": "menu.upload_workout",
                "desc_values": {"file": config.workoutfile},
                "key": "upload_workout",
            },
            "l": {
                "desc_key": "menu.activities_by_date",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_activities_by_date",
            },
            "m": {"desc_key": "menu.set_activity_name", "key": "set_activity_name"},
            "n": {"desc_key": "menu.set_activity_type", "key": "set_activity_type"},
            "o": {"desc_key": "menu.manual_activity", "key": "create_manual_activity"},
            "p": {"desc_key": "menu.delete_activity", "key": "delete_activity"},
            "r": {
                "desc_key": "menu.count_activities",
                "key": "count_activities",
            },
            "s": {
                "desc_key": "menu.schedule_workout",
                "key": "scheduled_workout",
            },
            "t": {
                "desc_key": "menu.import_activity",
                "desc_values": {"file": config.activityfile},
                "key": "import_activity",
            },
            "u": {
                "desc_key": "menu.scheduled_workouts",
                "key": "get_scheduled_workouts",
            },
            "v": {
                "desc_key": "menu.typed_running",
                "key": "upload_running_workout",
            },
            "w": {
                "desc_key": "menu.typed_cycling",
                "key": "upload_cycling_workout",
            },
            "x": {
                "desc_key": "menu.typed_swimming",
                "key": "upload_swimming_workout",
            },
            "y": {
                "desc_key": "menu.typed_walking",
                "key": "upload_walking_workout",
            },
            "z": {
                "desc_key": "menu.typed_hiking",
                "key": "upload_hiking_workout",
            },
            "A": {
                "desc_key": "menu.filtered_activities",
                "key": "get_activities_filtered",
            },
            "B": {
                "desc_key": "menu.next_workout",
                "key": "get_next_scheduled_workout",
            },
        },
    },
    "6": {
        "name_key": "menu.body_composition_category",
        "options": {
            "1": {
                "desc_key": "menu.body_composition",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_body_composition",
            },
            "2": {
                "desc_key": "menu.weigh_ins",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_weigh_ins",
            },
            "3": {
                "desc_key": "menu.daily_weigh_ins",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_daily_weigh_ins",
            },
            "4": {"desc_key": "menu.add_weigh_in", "key": "add_weigh_in"},
            "5": {
                "desc_key": "menu.add_body_composition",
                "desc_values": {"date": config.today.isoformat()},
                "key": "add_body_composition",
            },
            "6": {
                "desc_key": "menu.delete_weigh_ins",
                "desc_values": {"date": config.today.isoformat()},
                "key": "delete_weigh_ins",
            },
            "7": {"desc_key": "menu.delete_weigh_in", "key": "delete_weigh_in"},
        },
    },
    "7": {
        "name_key": "menu.goals",
        "options": {
            "1": {
                "desc_key": "menu.personal_records",
                "key": "get_personal_records",
            },
            "2": {"desc_key": "menu.earned_badges", "key": "get_earned_badges"},
            "3": {"desc_key": "menu.adhoc_challenges", "key": "get_adhoc_challenges"},
            "4": {
                "desc_key": "menu.available_badge_challenges",
                "key": "get_available_badge_challenges",
            },
            "5": {"desc_key": "menu.active_goals", "key": "get_active_goals"},
            "6": {"desc_key": "menu.future_goals", "key": "get_future_goals"},
            "7": {"desc_key": "menu.past_goals", "key": "get_past_goals"},
            "8": {"desc_key": "menu.badge_challenges", "key": "get_badge_challenges"},
            "9": {
                "desc_key": "menu.incomplete_badges",
                "key": "get_non_completed_badge_challenges",
            },
            "0": {
                "desc_key": "menu.virtual_challenges",
                "key": "get_inprogress_virtual_challenges",
            },
            "a": {"desc_key": "menu.race_predictions", "key": "get_race_predictions"},
            "b": {
                "desc_key": "menu.hill_score",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_hill_score",
            },
            "c": {
                "desc_key": "menu.endurance_score",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_endurance_score",
            },
            "d": {"desc_key": "menu.available_badges", "key": "get_available_badges"},
            "e": {"desc_key": "menu.badges_progress", "key": "get_in_progress_badges"},
        },
    },
    "8": {
        "name_key": "menu.device",
        "options": {
            "1": {"desc_key": "menu.devices", "key": "get_devices"},
            "2": {"desc_key": "menu.device_alarms", "key": "get_device_alarms"},
            "3": {"desc_key": "menu.solar", "key": "get_solar_data"},
            "4": {
                "desc_key": "menu.reload",
                "desc_values": {"date": config.today.isoformat()},
                "key": "request_reload",
            },
            "5": {"desc_key": "menu.device_settings", "key": "get_device_settings"},
            "6": {"desc_key": "menu.device_last_used", "key": "get_device_last_used"},
            "7": {
                "desc_key": "menu.primary_device",
                "key": "get_primary_training_device",
            },
        },
    },
    "9": {
        "name_key": "menu.gear",
        "options": {
            "1": {"desc_key": "menu.gear_list", "key": "get_gear"},
            "2": {"desc_key": "menu.gear_defaults", "key": "get_gear_defaults"},
            "3": {"desc_key": "menu.gear_stats", "key": "get_gear_stats"},
            "4": {"desc_key": "menu.gear_activities", "key": "get_gear_activities"},
            "5": {"desc_key": "menu.gear_default", "key": "set_gear_default"},
            "6": {
                "desc_key": "menu.track_gear",
                "key": "track_gear_usage",
            },
            "7": {
                "desc_key": "menu.activity_gear_edit",
                "key": "add_and_remove_gear_to_activity",
            },
            "8": {
                "desc_key": "menu.create_gear",
                "key": "create_gear",
            },
        },
    },
    "0": {
        "name_key": "menu.hydration_category",
        "options": {
            "1": {
                "desc_key": "menu.hydration",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_hydration_data",
            },
            "2": {"desc_key": "menu.add_hydration", "key": "add_hydration_data"},
            "3": {
                "desc_key": "menu.set_blood_pressure",
                "key": "set_blood_pressure",
            },
            "4": {"desc_key": "menu.pregnancy", "key": "get_pregnancy_summary"},
            "5": {
                "desc_key": "menu.all_day_events",
                "desc_values": {"start": config.week_start.isoformat()},
                "key": "get_all_day_events",
            },
            "6": {
                "desc_key": "menu.body_battery_events",
                "desc_values": {"start": config.week_start.isoformat()},
                "key": "get_body_battery_events",
            },
            "7": {
                "desc_key": "menu.menstrual_date",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_menstrual_data_for_date",
            },
            "8": {
                "desc_key": "menu.menstrual_calendar",
                "desc_values": {
                    "start": config.week_start.isoformat(),
                    "end": config.today.isoformat(),
                },
                "key": "get_menstrual_calendar_data",
            },
            "9": {
                "desc_key": "menu.delete_blood_pressure",
                "key": "delete_blood_pressure",
            },
            "a": {
                "desc_key": "menu.nutrition_log",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_nutrition_daily_food_log",
            },
            "b": {
                "desc_key": "menu.nutrition_meals",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_nutrition_daily_meals",
            },
            "c": {
                "desc_key": "menu.nutrition_settings",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_nutrition_daily_settings",
            },
            "d": {
                "desc_key": "menu.last_cycle",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_menstrual_last_confirmed",
            },
            "e": {
                "desc_key": "menu.cycle_summary",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_menstrual_cycle_summary",
            },
            "f": {
                "desc_key": "menu.menstrual_reports",
                "desc_values": {"date": config.today.isoformat()},
                "key": "get_menstrual_reports",
            },
            "g": {
                "desc_key": "menu.update_menstrual_log",
                "key": "update_menstrual_daily_log",
            },
            "h": {
                "desc_key": "menu.update_menstrual_calendar",
                "key": "update_menstrual_calendar",
            },
            "i": {
                "desc_key": "menu.init_cycle",
                "key": "init_menstrual_cycle_setup",
            },
            "j": {
                "desc_key": "menu.confirm_period",
                "key": "confirm_menstrual_period_start",
            },
            "k": {
                "desc_key": "menu.update_menstrual_settings",
                "key": "update_menstrual_settings",
            },
        },
    },
    "a": {
        "name_key": "menu.system",
        "options": {
            "1": {"desc_key": "menu.health_report", "key": "create_health_report"},
            "2": {
                "desc_key": "menu.remove_tokens",
                "key": "remove_tokens",
            },
            "3": {"desc_key": "menu.disconnect", "key": "disconnect"},
            "4": {"desc_key": "menu.graphql", "key": "query_garmin_graphql"},
            "5": {
                "desc_key": "menu.health_snapshot",
                "key": "download_health_snapshot",
            },
        },
    },
    "b": {
        "name_key": "menu.training_plans_category",
        "options": {
            "1": {"desc_key": "menu.get_training_plans", "key": "get_training_plans"},
            "2": {
                "desc_key": "menu.training_plan_by_id",
                "key": "get_training_plan_by_id",
            },
            "3": {
                "desc_key": "menu.typed_strength",
                "key": "upload_strength_workout",
            },
            "4": {
                "desc_key": "menu.exercise_catalog",
                "key": "search_exercise_catalog",
            },
            "5": {
                "desc_key": "menu.update_workout",
                "key": "update_workout",
            },
            "6": {
                "desc_key": "menu.push_workout",
                "key": "push_workout_to_device",
            },
            "7": {
                "desc_key": "menu.scheduled_workout_by_id",
                "key": "get_scheduled_workout_by_id",
            },
            "8": {
                "desc_key": "menu.delete_workout",
                "key": "delete_workout",
            },
            "9": {
                "desc_key": "menu.unschedule_workout",
                "key": "unschedule_workout",
            },
        },
    },
    "c": {
        "name_key": "menu.golf",
        "options": {
            "1": {"desc_key": "menu.golf_summary", "key": "get_golf_summary"},
            "2": {"desc_key": "menu.golf_scorecard", "key": "get_golf_scorecard"},
            "3": {
                "desc_key": "menu.golf_shots",
                "key": "get_golf_shot_data",
            },
            "4": {"desc_key": "menu.golf_club_stats", "key": "get_golf_club_stats"},
            "5": {"desc_key": "menu.golf_user_stats", "key": "get_golf_user_stats"},
        },
    },
    "d": {
        "name_key": "menu.editing",
        "options": {
            "1": {
                "desc_key": "menu.activity_description",
                "key": "set_activity_description",
            },
            "2": {
                "desc_key": "menu.activity_exercise_sets",
                "key": "set_activity_exercise_sets",
            },
        },
    },
}

current_category = None


def print_main_menu():
    """Print the main category menu."""
    print("\n" + "=" * 50)
    print(translate("demo.title"))
    print("=" * 50)
    print(translate("demo.select_category"))
    print()

    for key, category in menu_categories.items():
        name = translate(category["name_key"], **category.get("name_values", {}))
        print(translate("ui.indexed_item", index=key, name=name))

    print()
    print(translate("language.main_option"))
    print(translate("demo.exit"))
    print()
    print(translate("demo.selection"), end="", flush=True)


def print_category_menu(category_key: str):
    """Print options for a specific category."""
    if category_key not in menu_categories:
        return False

    category = menu_categories[category_key]
    category_name = translate(category["name_key"], **category.get("name_values", {}))
    print(
        translate(
            "ui.category_header",
            category_key=category_key,
            category_name=category_name,
        )
    )
    print("-" * 40)

    for key, option in category["options"].items():
        description = translate(option["desc_key"], **option.get("desc_values", {}))
        print(translate("ui.indexed_item", index=key, name=description))

    print()
    print(translate("demo.back"))
    print()
    print(translate("demo.selection"), end="", flush=True)
    return True


def _language_name(language: str) -> str:
    """Return the localized display name for a canonical language tag."""
    return translate(
        "language.option_en" if language == "en" else "language.option_pt_br"
    )


def select_language() -> None:
    """Show the language submenu and apply a selection immediately."""
    while True:
        print()
        print(translate("language.select"))
        print(
            translate(
                "ui.indexed_item",
                index="1",
                name=translate("language.option_en"),
            )
        )
        print(
            translate(
                "ui.indexed_item",
                index="2",
                name=translate("language.option_pt_br"),
            )
        )
        print(translate("language.back"))
        print(translate("demo.selection"), end="", flush=True)

        option = safe_readkey()
        if option == "q":
            return
        if option not in {"1", "2"}:
            print(translate("demo.invalid_selection"))
            continue

        selected_language = "en" if option == "1" else "pt-BR"
        set_language(selected_language)
        display_name = _language_name(selected_language)
        print(translate("language.changed", language=display_name))
        if save_persisted_language(selected_language):
            print(translate("language.saved"))
        else:
            print(translate("language.save_failed"))
        return


def get_mfa() -> str:
    """Get MFA token."""
    return input(translate("demo.mfa_code"))


class DataExporter:
    """Utilities for exporting data in various formats."""

    @staticmethod
    def save_json(data: Any, filename: str, pretty: bool = True) -> str:
        """Save data as JSON file."""
        filepath = config.export_dir / f"{_safe_filename_component(filename)}.json"
        with _open_private(filepath, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, indent=4, default=str, ensure_ascii=False)
            else:
                json.dump(data, f, default=str, ensure_ascii=False)
        return str(filepath)

    @staticmethod
    def create_health_report(api_instance: Garmin) -> str:
        """Create a comprehensive health report in JSON and HTML formats."""
        report_data = {
            "generated_at": datetime.datetime.now().isoformat(),
            "user_info": {
                "full_name": translate("report.not_available"),
                "unit_system": translate("report.not_available"),
            },
            "today_summary": {},
            "recent_activities": [],
            "health_metrics": {},
            "weekly_data": [],
            "device_info": [],
        }

        try:
            # Basic user info
            report_data["user_info"]["full_name"] = (
                api_instance.get_full_name() or translate("report.not_available")
            )
            report_data["user_info"]["unit_system"] = (
                api_instance.get_unit_system() or translate("report.not_available")
            )

            # Today's summary
            today_str = config.today.isoformat()
            report_data["today_summary"] = api_instance.get_user_summary(today_str)

            # Recent activities
            recent_activities = api_instance.get_activities(0, 10)
            report_data["recent_activities"] = recent_activities or []

            # Weekly data for trends
            for i in range(7):
                date = config.today - datetime.timedelta(days=i)
                try:
                    daily_data = api_instance.get_user_summary(date.isoformat())
                    if daily_data:
                        daily_data["date"] = date.isoformat()
                        report_data["weekly_data"].append(daily_data)
                except Exception as e:
                    print(
                        translate("ui.skipping", date=date.isoformat(), error=e)
                    )  # Skip if data not available

            # Health metrics for today
            health_metrics = {}
            metrics_to_fetch = [
                ("heart_rate", lambda: api_instance.get_heart_rates(today_str)),
                ("steps", lambda: api_instance.get_steps_data(today_str)),
                ("sleep", lambda: api_instance.get_sleep_data(today_str)),
                ("stress", lambda: api_instance.get_all_day_stress(today_str)),
                (
                    "body_battery",
                    lambda: api_instance.get_body_battery(
                        config.week_start.isoformat(), today_str
                    ),
                ),
            ]

            for metric_name, fetch_func in metrics_to_fetch:
                try:
                    health_metrics[metric_name] = fetch_func()
                except Exception:
                    health_metrics[metric_name] = None

            report_data["health_metrics"] = health_metrics

            # Device information
            try:
                report_data["device_info"] = api_instance.get_devices()
            except Exception:
                report_data["device_info"] = []

        except Exception as e:
            print(translate("ui.error_health_report", error=e))

        # Create HTML version
        html_filepath = DataExporter.create_readable_health_report(report_data)

        print(translate("demo.report_created", path=html_filepath))

        return html_filepath

    @staticmethod
    def create_readable_health_report(report_data: dict) -> str:
        """Create a readable HTML report from comprehensive health data."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"health_report_{timestamp}.html"

        # Extract key information
        user_name = report_data.get("user_info", {}).get(
            "full_name", translate("report.unknown_user")
        )
        generated_at = report_data.get("generated_at", translate("report.unknown"))

        # Create HTML content with complete styling
        html_content = f"""<!DOCTYPE html>
<html lang="{get_language()}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{translate("report.title", user=_html(user_name))}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007ACC;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007ACC;
            margin: 0;
            font-size: 2.5em;
        }}
        .meta-info {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #007ACC;
            border-bottom: 2px solid #007ACC;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007ACC;
        }}
        .metric-card h4 {{
            margin: 0 0 10px 0;
            color: #007ACC;
            font-size: 1.1em;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        .metric-unit {{
            color: #666;
            font-size: 0.9em;
        }}
        .activity-item {{
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }}
        .activity-item h4 {{
            margin: 0 0 10px 0;
            color: #28a745;
        }}
        .activity-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            font-size: 0.9em;
        }}
        .no-data {{
            color: #666;
            font-style: italic;
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏃 {translate("report.heading")}</h1>
            <p><strong>{_html(user_name)}</strong></p>
        </div>

        <div class="meta-info">
            <p><strong>{translate("report.generated")}</strong> {_html(generated_at)}</p>
            <p><strong>{translate("report.date")}</strong> {_html(config.today.isoformat())}</p>
        </div>
"""

        # Today's Summary Section
        today_summary = report_data.get("today_summary", {})
        if today_summary:
            steps = today_summary.get("totalSteps", 0)
            calories = today_summary.get("totalKilocalories", 0)
            distance = (
                round(today_summary.get("totalDistanceMeters", 0) / 1000, 2)
                if today_summary.get("totalDistanceMeters")
                else 0
            )
            active_calories = today_summary.get("activeKilocalories", 0)

            html_content += f"""
        <div class="section">
            <h2>📈 {translate("report.today_activity_summary")}</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <h4>👟 {translate("report.steps")}</h4>
                    <div class="metric-value">{_html(f"{steps:,}")} <span class="metric-unit">{translate("report.steps_unit")}</span></div>
                </div>
                <div class="metric-card">
                    <h4>🔥 {translate("report.calories")}</h4>
                    <div class="metric-value">{_html(f"{calories:,}")} <span class="metric-unit">{translate("report.total")}</span></div>
                    <div style="margin-top: 10px;">{_html(f"{active_calories:,}")} {translate("report.active")}</div>
                </div>
                <div class="metric-card">
                    <h4>📏 {translate("report.distance")}</h4>
                    <div class="metric-value">{_html(distance)} <span class="metric-unit">km</span></div>
                </div>
            </div>
        </div>
"""
        else:
            html_content += f"""
        <div class="section">
            <h2>📈 {translate("report.today_activity_summary")}</h2>
            <div class="no-data">{translate("report.no_activity_today")}</div>
        </div>
"""

        # Health Metrics Section
        health_metrics = report_data.get("health_metrics", {})
        if health_metrics and any(health_metrics.values()):
            html_content += f"""
        <div class="section">
            <h2>❤️ {translate("report.health_metrics")}</h2>
            <div class="metric-grid">
"""

            # Heart Rate
            heart_rate = health_metrics.get("heart_rate", {})
            if heart_rate and isinstance(heart_rate, dict):
                resting_hr = heart_rate.get(
                    "restingHeartRate", translate("report.not_available")
                )
                max_hr = heart_rate.get(
                    "maxHeartRate", translate("report.not_available")
                )
                html_content += f"""
                <div class="metric-card">
                    <h4>💓 {translate("report.heart_rate")}</h4>
                    <div class="metric-value">{_html(resting_hr)} <span class="metric-unit">{translate("report.resting_bpm")}</span></div>
                    <div style="margin-top: 10px;">{translate("report.max")} {_html(max_hr)} bpm</div>
                </div>
"""

            # Sleep Data
            sleep_data = health_metrics.get("sleep", {})
            if (
                sleep_data
                and isinstance(sleep_data, dict)
                and "dailySleepDTO" in sleep_data
            ):
                sleep_seconds = sleep_data["dailySleepDTO"].get("sleepTimeSeconds", 0)
                sleep_hours = round(sleep_seconds / 3600, 1) if sleep_seconds else 0
                deep_sleep = sleep_data["dailySleepDTO"].get("deepSleepSeconds", 0)
                deep_hours = round(deep_sleep / 3600, 1) if deep_sleep else 0

                html_content += f"""
                <div class="metric-card">
                    <h4>😴 {translate("report.sleep")}</h4>
                    <div class="metric-value">{_html(sleep_hours)} <span class="metric-unit">{translate("report.hours")}</span></div>
                    <div style="margin-top: 10px;">{translate("report.deep_sleep")} {_html(deep_hours)} {translate("report.hours")}</div>
                </div>
"""

            # Steps
            steps_data = health_metrics.get("steps", {})
            if steps_data and isinstance(steps_data, dict):
                total_steps = steps_data.get("totalSteps", 0)
                goal = steps_data.get("dailyStepGoal", 10000)
                html_content += f"""
                <div class="metric-card">
                    <h4>🎯 {translate("report.step_goal")}</h4>
                    <div class="metric-value">{_html(f"{total_steps:,}")} <span class="metric-unit">{translate("report.of")} {_html(f"{goal:,}")}</span></div>
                    <div style="margin-top: 10px;">{translate("report.goal")} {_html(round((total_steps / goal) * 100) if goal else 0)}%</div>
                </div>
"""

            # Stress Data
            stress_data = health_metrics.get("stress", {})
            if stress_data and isinstance(stress_data, dict):
                avg_stress = stress_data.get(
                    "avgStressLevel", translate("report.not_available")
                )
                max_stress = stress_data.get(
                    "maxStressLevel", translate("report.not_available")
                )
                html_content += f"""
                <div class="metric-card">
                    <h4>😰 {translate("report.stress_level")}</h4>
                    <div class="metric-value">{_html(avg_stress)} <span class="metric-unit">{translate("report.avg")}</span></div>
                    <div style="margin-top: 10px;">{translate("report.max")} {_html(max_stress)}</div>
                </div>
"""

            # Body Battery
            body_battery = health_metrics.get("body_battery", [])
            if body_battery and isinstance(body_battery, list) and body_battery:
                latest_bb = body_battery[-1] if body_battery else {}
                charged = latest_bb.get("charged", translate("report.not_available"))
                drained = latest_bb.get("drained", translate("report.not_available"))
                html_content += f"""
                <div class="metric-card">
                    <h4>🔋 {translate("report.body_battery")}</h4>
                    <div class="metric-value">+{_html(charged)} <span class="metric-unit">{translate("report.charged")}</span></div>
                    <div style="margin-top: 10px;">-{_html(drained)} {translate("report.drained")}</div>
                </div>
"""

            html_content += "            </div>\n        </div>\n"
        else:
            html_content += f"""
        <div class="section">
            <h2>❤️ {translate("report.health_metrics")}</h2>
            <div class="no-data">{translate("report.no_health_metrics")}</div>
        </div>
"""

        # Weekly Trends Section
        weekly_data = report_data.get("weekly_data", [])
        if weekly_data:
            html_content += f"""
        <div class="section">
            <h2>📊 {translate("report.weekly_trends")}</h2>
            <div class="metric-grid">
"""
            for daily in weekly_data[:7]:  # Show last 7 days
                date = daily.get("date", translate("report.unknown"))
                steps = daily.get("totalSteps", 0)
                calories = daily.get("totalKilocalories", 0)
                distance = (
                    round(daily.get("totalDistanceMeters", 0) / 1000, 2)
                    if daily.get("totalDistanceMeters")
                    else 0
                )

                html_content += f"""
                <div class="metric-card">
                    <h4>📅 {_html(date)}</h4>
                    <div class="metric-value">{_html(f"{steps:,}")} <span class="metric-unit">{translate("report.steps_unit")}</span></div>
                    <div style="margin-top: 10px;">
                        <div>{_html(f"{calories:,}")} kcal</div>
                        <div>{_html(distance)} km</div>
                    </div>
                </div>
"""
            html_content += "            </div>\n        </div>\n"

        # Recent Activities Section
        activities = report_data.get("recent_activities", [])
        if activities:
            html_content += f"""
        <div class="section">
            <h2>🏃 {translate("report.recent_activities")}</h2>
"""
            for activity in activities[:5]:  # Show last 5 activities
                name = activity.get(
                    "activityName", translate("report.unknown_activity")
                )
                activity_type = activity.get("activityType", {}).get(
                    "typeKey", translate("report.unknown")
                )
                date = (
                    activity.get("startTimeLocal", "").split("T")[0]
                    if activity.get("startTimeLocal")
                    else translate("report.unknown")
                )
                duration = activity.get("duration", 0)
                duration_min = round(duration / 60, 1) if duration else 0
                distance = (
                    round(activity.get("distance", 0) / 1000, 2)
                    if activity.get("distance")
                    else 0
                )
                calories = activity.get("calories", 0)
                avg_hr = activity.get("avgHR", 0)

                html_content += f"""
                <div class="activity-item">
                    <h4>{_html(name)} ({_html(activity_type)})</h4>
                    <div class="activity-details">
                        <div><strong>{translate("report.date")}</strong> {_html(date)}</div>
                        <div><strong>{translate("report.duration")}</strong> {_html(duration_min)} min</div>
                        <div><strong>{translate("report.distance")}</strong> {_html(distance)} km</div>
                        <div><strong>{translate("report.calories")}</strong> {_html(calories)}</div>
                        <div><strong>{translate("report.avg_hr")}</strong> {_html(avg_hr)} bpm</div>
                    </div>
                </div>
"""
            html_content += "        </div>\n"
        else:
            html_content += f"""
        <div class="section">
            <h2>🏃 {translate("report.recent_activities")}</h2>
            <div class="no-data">{translate("report.no_recent_activities")}</div>
        </div>
"""

        # Device Information
        device_info = report_data.get("device_info", [])
        if device_info:
            html_content += f"""
        <div class="section">
            <h2>⌚ {translate("report.device_information")}</h2>
            <div class="metric-grid">
"""
            for device in device_info:
                device_name = device.get(
                    "displayName", translate("report.unknown_device")
                )
                model = device.get(
                    "productDisplayName", translate("report.unknown_model")
                )
                version = device.get("softwareVersion", translate("report.unknown"))

                html_content += f"""
                <div class="metric-card">
                    <h4>{_html(device_name)}</h4>
                    <div><strong>{translate("report.model")}</strong> {_html(model)}</div>
                    <div><strong>{translate("report.software")}</strong> {_html(version)}</div>
                </div>
"""
            html_content += "            </div>\n        </div>\n"

        # Footer
        html_content += f"""
        <div class="footer">
            <p>{translate("report.footer_generated", timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}</p>
            <p>{translate("report.footer_disclaimer")}</p>
        </div>
    </div>
</body>
</html>
"""

        # Save HTML file
        html_filepath = config.export_dir / html_filename
        with _open_private(html_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(html_filepath)


def safe_api_call(api_method, *args, method_name: str | None = None, **kwargs):
    """Centralized API call wrapper with comprehensive error handling.

    This function provides unified error handling for all Garmin Connect API calls.
    It handles common HTTP errors (400, 401, 403, 404, 429, 500, 503) with
    user-friendly messages and provides consistent error reporting.

    Usage:
        success, result, error_msg = safe_api_call(api.get_user_summary)

    Args:
        api_method: The API method to call
        *args: Positional arguments for the API method
        method_name: Human-readable name for the API method (optional)
        **kwargs: Keyword arguments for the API method

    Returns:
        tuple: (success: bool, result: Any, error_message: str|None)

    """
    if method_name is None:
        method_name = getattr(api_method, "__name__", str(api_method))

    t0 = time.perf_counter()
    try:
        result = api_method(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        _LOGGER.debug("api.%s OK in %.1f ms", method_name, elapsed_ms)
        return True, result, None

    except GarminConnectNotFoundError as e:
        _LOGGER.debug(
            "api.%s FAIL in %.1f ms: %s",
            method_name,
            (time.perf_counter() - t0) * 1000,
            e,
        )
        error_msg = translate("error.endpoint_not_found")
        print(translate("ui.api_method_error", method=method_name, error=error_msg))
        return False, None, error_msg

    except GarminConnectConnectionError as e:
        _LOGGER.debug(
            "api.%s FAIL in %.1f ms: %s",
            method_name,
            (time.perf_counter() - t0) * 1000,
            e,
        )
        # Handle specific HTTP errors more gracefully
        error_str = str(e)

        # Extract status code more reliably
        status_code = None
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            status_code = e.response.status_code

        # Handle specific status codes
        if status_code == 400 or ("400" in error_str and "Bad Request" in error_str):
            error_msg = translate("error.endpoint_not_available")
            # Don't print for 400 errors as they're often expected for unavailable features
        elif status_code == 401 or "401" in error_str:
            error_msg = translate("error.authentication_required")
            print(translate("ui.api_method_error", method=method_name, error=error_msg))
        elif status_code == 403 or "403" in error_str:
            error_msg = translate("error.access_denied")
            print(translate("ui.api_method_error", method=method_name, error=error_msg))
        elif status_code == 410 or "410" in error_str:
            error_msg = translate("error.resource_unavailable")
            print(translate("ui.api_method_error", method=method_name, error=error_msg))
        elif status_code == 429 or "429" in error_str:
            error_msg = translate("error.rate_limit_exceeded")
            print(translate("ui.api_method_error", method=method_name, error=error_msg))
        elif status_code == 500 or "500" in error_str:
            error_msg = translate("error.server_error")
            print(translate("ui.api_method_error", method=method_name, error=error_msg))
        elif status_code == 503 or "503" in error_str:
            error_msg = translate("error.service_unavailable")
            print(translate("ui.api_method_error", method=method_name, error=error_msg))
        else:
            error_msg = translate("error.http", error=str(e))

        print(translate("ui.api_method_error", method=method_name, error=error_msg))
        return False, None, error_msg

    except GarminConnectAuthenticationError as e:
        _LOGGER.debug(
            "api.%s FAIL in %.1f ms: %s",
            method_name,
            (time.perf_counter() - t0) * 1000,
            e,
        )
        error_msg = translate("error.authentication_issue", error=str(e))
        print(translate("ui.api_method_error", method=method_name, error=error_msg))
        return False, None, error_msg

    except GarminConnectConnectionError as e:  # noqa: B025
        _LOGGER.debug(
            "api.%s FAIL in %.1f ms: %s",
            method_name,
            (time.perf_counter() - t0) * 1000,
            e,
        )
        error_str = str(e)
        # Extract a clean message by detecting common HTTP status codes
        if "410" in error_str:
            error_msg = translate("error.resource_unavailable")
        elif "403" in error_str:
            error_msg = translate("error.access_denied")
        elif "404" in error_str:
            error_msg = translate("error.endpoint_not_found")
        else:
            error_msg = translate("error.connection_issue", error=str(e))
        print(translate("ui.api_method_error", method=method_name, error=error_msg))
        return False, None, error_msg

    except Exception as e:
        _LOGGER.debug(
            "api.%s FAIL in %.1f ms: %s",
            method_name,
            (time.perf_counter() - t0) * 1000,
            e,
        )
        error_msg = translate("error.unexpected", error=str(e))
        print(translate("ui.api_method_error", method=method_name, error=error_msg))
        return False, None, error_msg


def call_and_display(
    api_method=None,
    *args,
    method_name: str | None = None,
    api_call_desc: str | None = None,
    group_name: str | None = None,
    api_responses: list | None = None,
    **kwargs,
):
    """Unified wrapper that calls API methods safely and displays results.
    Can handle both single API calls and grouped API responses.

    For single API calls:
        call_and_display(api.get_user_summary, "2024-01-01")

    For grouped responses:
        call_and_display(group_name="User Data", api_responses=[("api.get_user", data)])

    Args:
        api_method: The API method to call (for single calls)
        *args: Positional arguments for the API method
        method_name: Human-readable name for the API method (optional)
        api_call_desc: Description for display purposes (optional)
        group_name: Name for grouped display (when displaying multiple responses)
        api_responses: List of (api_call_desc, result) tuples for grouped display
        **kwargs: Keyword arguments for the API method

    Returns:
        For single calls: tuple: (success: bool, result: Any)
        For grouped calls: None

    """
    # Handle grouped display mode
    if group_name is not None and api_responses is not None:
        return _display_group(group_name, api_responses)

    # Handle single API call mode
    if api_method is None:
        raise ValueError(
            "Either api_method or (group_name + api_responses) must be provided"
        )

    if method_name is None:
        method_name = getattr(api_method, "__name__", str(api_method))

    if api_call_desc is None:
        # Try to construct a reasonable description
        args_str = ", ".join(str(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        api_call_desc = f"{method_name}({all_args})"

    success, result, error_msg = safe_api_call(
        api_method, *args, method_name=method_name, **kwargs
    )

    if success:
        _display_single(api_call_desc, result)
        return True, result
    # Display error in a consistent format
    _display_single(f"{api_call_desc} [ERROR]", {"error": error_msg})
    return False, None


def _display_single(api_call: str, output: Any):
    """Internal function to display single API response."""
    print(translate("demo.api_call", call=api_call))
    print("-" * 50)

    if output is None:
        print(translate("demo.no_data"))
        # Save empty JSON to response.json in the export directory
        response_file = config.export_dir / "response.json"
        with _open_private(response_file, "w", encoding="utf-8") as f:
            f.write(f"{'-' * 20} {api_call} {'-' * 20}\n{{}}\n{'-' * 77}\n")
        return

    try:
        # Format the output
        if isinstance(output, int | str | dict | list):
            formatted_output = json.dumps(output, indent=2, default=str)
        else:
            formatted_output = str(output)

        # Save to response.json in the export directory
        response_content = (
            f"{'-' * 20} {api_call} {'-' * 20}\n{formatted_output}\n{'-' * 77}\n"
        )

        response_file = config.export_dir / "response.json"
        with _open_private(response_file, "w", encoding="utf-8") as f:
            f.write(response_content)

        print(formatted_output)
        print("-" * 77)

    except Exception as e:
        print(translate("ui.format_error", error=e))
        print(output)


def _display_group(group_name: str, api_responses: list[tuple[str, Any]]):
    """Internal function to display grouped API responses."""
    print(translate("demo.api_group", group=group_name))

    # Collect all responses for saving
    all_responses = {}
    response_content_parts = []

    for api_call, output in api_responses:
        print(translate("demo.api_method_header", call=api_call))
        print("-" * 50)

        if output is None:
            print(translate("demo.no_data"))
            formatted_output = "{}"
        else:
            try:
                if isinstance(output, int | str | dict | list):
                    formatted_output = json.dumps(output, indent=2, default=str)
                else:
                    formatted_output = str(output)
                print(formatted_output)
            except Exception as e:
                print(translate("ui.format_error", error=e))
                formatted_output = str(output)
                print(output)

        # Store for grouped response file
        all_responses[api_call] = output
        response_content_parts.append(
            f"{'-' * 20} {api_call} {'-' * 20}\n{formatted_output}"
        )
        print("-" * 50)

    # Save grouped responses to file
    try:
        response_file = config.export_dir / "response.json"
        header = "=" * 20 + f" {group_name} " + "=" * 20
        footer = "=" * 77
        content_lines = [header, *response_content_parts, footer, ""]
        grouped_content = "\n".join(content_lines)
        with _open_private(response_file, "w", encoding="utf-8") as f:
            f.write(grouped_content)

        print(translate("demo.group_saved", path=response_file))
        print("=" * 77)

    except Exception as e:
        print(translate("ui.save_group_error", error=e))


def format_timedelta(td):
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}"


def safe_call_for_group(
    api_method,
    *args,
    method_name: str | None = None,
    api_call_desc: str | None = None,
    **kwargs,
):
    """Safe API call wrapper that returns result suitable for grouped display.

    Args:
        api_method: The API method to call
        *args: Positional arguments for the API method
        method_name: Human-readable name for the API method (optional)
        api_call_desc: Description for display purposes (optional)
        **kwargs: Keyword arguments for the API method

    Returns:
        tuple: (api_call_description: str, result: Any) - suitable for grouped display

    """
    if method_name is None:
        method_name = getattr(api_method, "__name__", str(api_method))

    if api_call_desc is None:
        # Try to construct a reasonable description
        args_str = ", ".join(str(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        api_call_desc = f"{method_name}({all_args})"

    success, result, error_msg = safe_api_call(
        api_method, *args, method_name=method_name, **kwargs
    )

    if success:
        return api_call_desc, result
    return f"{api_call_desc} [ERROR]", {"error": error_msg}


def get_solar_data(api: Garmin) -> None:
    """Get solar data from all Garmin devices using centralized error handling."""
    print(translate("demo.solar_loading"))

    # Collect all API responses for grouped display
    api_responses = []

    # Get all devices using centralized wrapper
    api_responses.append(
        safe_call_for_group(
            api.get_devices,
            method_name="get_devices",
            api_call_desc="api.get_devices()",
        )
    )

    # Get device last used using centralized wrapper
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get the device list to process solar data
    devices_success, devices, _ = safe_api_call(
        api.get_devices, method_name="get_devices"
    )

    # Get solar data for each device
    if devices_success and devices:
        for device in devices:
            device_id = device.get("deviceId")
            if device_id:
                device_name = device.get("displayName", f"Device {device_id}")
                print(
                    translate("ui.solar_device", name=device_name, device_id=device_id)
                )

                # Use centralized wrapper for each device's solar data
                api_responses.append(
                    safe_call_for_group(
                        api.get_device_solar_data,
                        device_id,
                        config.today.isoformat(),
                        method_name="get_device_solar_data",
                        api_call_desc=f"api.get_device_solar_data({device_id}, '{config.today.isoformat()}')",
                    )
                )
    else:
        print(translate("demo.device_missing"))

    # Display all responses as a group
    call_and_display(group_name="Solar Data Collection", api_responses=api_responses)


def import_activity_file(api: Garmin) -> None:
    """Import activity data from file (not re-exported to Strava)."""
    import glob

    try:
        activity_files = glob.glob(config.activityfile)
        if not activity_files:
            print(translate("demo.activity_file_missing"))
            print(translate("demo.add_activity_files"))
            return

        print(translate("demo.import_select"))
        for idx, fname in enumerate(activity_files, 1):
            print(translate("ui.file_number", index=idx, name=fname))

        while True:
            try:
                choice = int(
                    input(translate("prompt.enter_number", maximum=len(activity_files)))
                )
                if 1 <= choice <= len(activity_files):
                    selected_file = activity_files[choice - 1]
                    break
                print(translate("demo.invalid_selection"))
            except ValueError:
                print(translate("demo.valid_number"))

        print(translate("demo.activity_imported", path=selected_file))

        call_and_display(
            api.import_activity,
            selected_file,
            method_name="import_activity",
            api_call_desc=f"api.import_activity({selected_file})",
        )

    except FileNotFoundError:
        print(translate("demo.file_not_found", path=selected_file))
    except Exception as e:
        if "409" in str(e) or "duplicate" in str(e).lower():
            print(translate("demo.activity_duplicate"))
        else:
            print(translate("ui.import_error", error=e))


def upload_activity_file(api: Garmin) -> None:
    """Upload activity data from file."""
    import glob

    try:
        # List all .gpx files in test_data
        gpx_files = glob.glob(config.activityfile)
        if not gpx_files:
            print(translate("ui.gpx_missing"))
            print(translate("demo.add_gpx_files"))
            return

        print(translate("demo.gpx_select"))
        for idx, fname in enumerate(gpx_files, 1):
            print(translate("ui.file_number", index=idx, name=fname))

        while True:
            try:
                choice = int(
                    input(translate("prompt.enter_number", maximum=len(gpx_files)))
                )
                if 1 <= choice <= len(gpx_files):
                    selected_file = gpx_files[choice - 1]
                    break
                print(translate("demo.invalid_selection"))
            except ValueError:
                print(translate("demo.valid_number"))

        print(translate("demo.activity_uploaded", path=selected_file))

        call_and_display(
            api.upload_activity,
            selected_file,
            method_name="upload_activity",
            api_call_desc=f"api.upload_activity({selected_file})",
        )

    except FileNotFoundError:
        print(translate("demo.file_not_found", path=selected_file))
        print(translate("demo.activity_file_current_dir"))
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print(translate("error.duplicate_full"))
            print(translate("error.duplicate_info"))
            print(translate("error.modify_file"))
        elif e.response.status_code == 413:
            print(translate("error.file_too_large"))
            print(translate("error.compress_file"))
        elif e.response.status_code == 422:
            print(translate("error.file_format"))
            print(translate("error.supported_formats"))
            print(translate("ui.retry_file_format"))
        elif e.response.status_code == 400:
            print(translate("error.bad_request"))
            print(translate("error.check_gps"))
        elif e.response.status_code == 401:
            print(translate("ui.auth_failed_error"))
            print(translate("error.session_expired"))
        elif e.response.status_code == 429:
            print(translate("error.rate_limit_upload"))
            print(translate("error.wait"))
        else:
            print(translate("ui.http_error", status=e.response.status_code, error=e))
    except GarminConnectAuthenticationError as e:
        print(translate("error.authentication", error=e))
        print(translate("ui.check_credentials"))
    except GarminConnectConnectionError as e:
        print(translate("error.connection", error=e))
        print(translate("ui.check_connection"))
    except GarminConnectTooManyRequestsError as e:
        print(translate("error.too_many_requests", error=e))
        print(translate("error.wait"))
    except Exception as e:
        error_str = str(e)
        if "409 Client Error: Conflict" in error_str:
            print(translate("error.duplicate_full"))
            print(translate("error.duplicate_info"))
            print(translate("error.modify_file"))
        elif "413" in error_str and "Request Entity Too Large" in error_str:
            print(translate("error.file_too_large"))
            print(translate("error.compress_file"))
        elif "422" in error_str and "Unprocessable Entity" in error_str:
            print(translate("error.file_format"))
            print(translate("error.supported_formats"))
            print(translate("ui.retry_file_format"))
        elif "400" in error_str and "Bad Request" in error_str:
            print(translate("error.bad_request"))
            print(translate("error.check_gps"))
        elif "401" in error_str and "Unauthorized" in error_str:
            print(translate("ui.auth_failed_error"))
            print(translate("error.session_expired"))
        elif "429" in error_str and "Too Many Requests" in error_str:
            print(translate("error.rate_limit_upload"))
            print(translate("error.wait"))
        else:
            print(translate("ui.upload_error", error=e))
            print(translate("ui.check_format"))


def download_activities_by_date(api: Garmin) -> None:
    """Download activities by date range in multiple formats."""
    try:
        print(
            translate(
                "result.activity_download",
                start=config.week_start.isoformat(),
                end=config.today.isoformat(),
            )
        )

        # Get activities for the date range (last 7 days as default)
        activities = api.get_activities_by_date(
            config.week_start.isoformat(), config.today.isoformat()
        )

        if not activities:
            print(translate("error.no_data_range"))
            return

        print(translate("result.activities_found", count=len(activities)))

        # Download each activity in multiple formats
        for activity in activities:
            activity_id = activity.get("activityId")
            activity_name = activity.get("activityName", "Unknown")
            start_time = activity.get("startTimeLocal", "").replace(":", "-")

            if not activity_id:
                continue

            print(
                translate(
                    "ui.download_item", name=activity_name, activity_id=activity_id
                )
            )

            # Download formats: GPX, TCX, ORIGINAL, CSV
            formats = ["GPX", "TCX", "ORIGINAL", "CSV"]

            for fmt in formats:
                try:
                    safe_start = _safe_filename_component(start_time)
                    safe_activity_id = _safe_filename_component(activity_id)
                    filename = f"{safe_start}_{safe_activity_id}_ACTIVITY.{fmt.lower()}"
                    if fmt == "ORIGINAL":
                        filename = f"{safe_start}_{safe_activity_id}_ACTIVITY.zip"

                    filepath = config.export_dir / filename

                    if fmt == "CSV":
                        # Get activity details for CSV export
                        activity_details = api.get_activity_details(activity_id)
                        with _open_private(filepath, "w", encoding="utf-8") as f:
                            import json

                            json.dump(activity_details, f, indent=2, ensure_ascii=False)
                        print(
                            translate(
                                "ui.download_success", format=fmt, filename=filename
                            )
                        )
                    else:
                        # Download the file from Garmin using proper enum values
                        format_mapping = {
                            "GPX": api.ActivityDownloadFormat.GPX,
                            "TCX": api.ActivityDownloadFormat.TCX,
                            "ORIGINAL": api.ActivityDownloadFormat.ORIGINAL,
                        }

                        dl_fmt = format_mapping[fmt]
                        content = api.download_activity(activity_id, dl_fmt=dl_fmt)

                        if content:
                            with _open_private(filepath, "wb") as f:
                                f.write(content)
                            print(
                                translate(
                                    "ui.download_success", format=fmt, filename=filename
                                )
                            )
                        else:
                            print(translate("ui.workout_no_content", format=fmt))

                except Exception as e:
                    print(translate("ui.download_format_error", format=fmt, error=e))

        print(translate("result.download_complete", path=config.export_dir))

    except Exception as e:
        print(translate("error.download_activities", error=e))


def add_weigh_in_data(api: Garmin) -> None:
    """Add a weigh-in with timestamps."""
    try:
        # Get weight input from user
        print(translate("ui.weigh_in_loading"))
        print("-" * 30)

        # Weight input with validation
        while True:
            try:
                weight_str = input(translate("prompt.enter_weight")).strip()
                if not weight_str:
                    weight = 85.1
                    break
                weight = float(weight_str)
                if 30 <= weight <= 300:
                    break
                print(translate("error.weight"))
            except ValueError:
                print(translate("error.invalid_number"))

        # Unit selection
        while True:
            unit_input = input(translate("prompt.enter_unit")).strip().lower()
            if not unit_input:
                weight_unit = "kg"
                break
            if unit_input in ["kg", "lbs"]:
                weight_unit = unit_input
                break
            print(translate("error.kg_lbs"))

        print(translate("ui.weighing", weight=weight, unit=weight_unit))

        # Collect all API responses for grouped display
        api_responses = []

        # Add a simple weigh-in
        result1 = api.add_weigh_in(weight=weight, unitKey=weight_unit)
        api_responses.append(
            (f"api.add_weigh_in(weight={weight}, unitKey={weight_unit})", result1)
        )

        # Add a weigh-in with timestamps for yesterday
        import datetime

        yesterday = config.today - datetime.timedelta(days=1)  # Get yesterday's date
        weigh_in_date = datetime.datetime.strptime(yesterday.isoformat(), "%Y-%m-%d")
        local_timestamp = weigh_in_date.strftime("%Y-%m-%dT%H:%M:%S")
        gmt_timestamp = weigh_in_date.astimezone(datetime.UTC).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )

        result2 = api.add_weigh_in_with_timestamps(
            weight=weight,
            unitKey=weight_unit,
            dateTimestamp=local_timestamp,
            gmtTimestamp=gmt_timestamp,
        )
        api_responses.append(
            (
                f"api.add_weigh_in_with_timestamps(weight={weight}, unitKey={weight_unit}, dateTimestamp={local_timestamp}, gmtTimestamp={gmt_timestamp})",
                result2,
            )
        )

        # Display all responses as a group
        call_and_display(group_name="Weigh-in Data Entry", api_responses=api_responses)

        print(translate("result.weigh_in_added"))

    except Exception as e:
        print(translate("error.add_weigh_in_error", error=e))


# Helper functions for the new API methods
def get_lactate_threshold_data(api: Garmin) -> None:
    """Get lactate threshold data."""
    try:
        # Collect all API responses for grouped display
        api_responses = []

        # Get latest lactate threshold
        latest = api.get_lactate_threshold(latest=True)
        api_responses.append(("api.get_lactate_threshold(latest=True)", latest))

        # Get historical lactate threshold for past four weeks
        four_weeks_ago = config.today - datetime.timedelta(days=28)
        historical = api.get_lactate_threshold(
            latest=False,
            start_date=four_weeks_ago.isoformat(),
            end_date=config.today.isoformat(),
            aggregation="daily",
        )
        api_responses.append(
            (
                f"api.get_lactate_threshold(latest=False, start_date='{four_weeks_ago.isoformat()}', end_date='{config.today.isoformat()}', aggregation='daily')",
                historical,
            )
        )

        # Display all responses as a group
        call_and_display(
            group_name="Lactate Threshold Data", api_responses=api_responses
        )

    except Exception as e:
        print(translate("ui.lactate_error", error=e))


def get_activity_splits_data(api: Garmin) -> None:
    """Get activity splits for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_splits,
                activity_id,
                method_name="get_activity_splits",
                api_call_desc=f"api.get_activity_splits({activity_id})",
            )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.activity_splits_error", error=e))


def get_activity_typed_splits_data(api: Garmin) -> None:
    """Get activity typed splits for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_typed_splits,
                activity_id,
                method_name="get_activity_typed_splits",
                api_call_desc=f"api.get_activity_typed_splits({activity_id})",
            )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.typed_splits_error", error=e))


def get_activity_split_summaries_data(api: Garmin) -> None:
    """Get activity split summaries for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_split_summaries,
                activity_id,
                method_name="get_activity_split_summaries",
                api_call_desc=f"api.get_activity_split_summaries({activity_id})",
            )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.split_summaries_error", error=e))


def get_activity_weather_data(api: Garmin) -> None:
    """Get activity weather data for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_weather,
                activity_id,
                method_name="get_activity_weather",
                api_call_desc=f"api.get_activity_weather({activity_id})",
            )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.activity_weather_error", error=e))


def get_activity_hr_timezones_data(api: Garmin) -> None:
    """Get activity heart rate timezones for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_hr_in_timezones,
                activity_id,
                method_name="get_activity_hr_in_timezones",
                api_call_desc=f"api.get_activity_hr_in_timezones({activity_id})",
            )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.activity_hr_error", error=e))


def get_activity_power_timezones_data(api: Garmin) -> None:
    """Get activity power timezones for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_power_in_timezones,
                activity_id,
                method_name="get_activity_power_in_timezones",
                api_call_desc=f"api.get_activity_power_in_timezones({activity_id})",
            )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.activity_power_error", error=e))


def get_cycling_ftp_data(api: Garmin) -> None:
    """Get cycling Functional Threshold Power (FTP) information."""
    call_and_display(
        api.get_cycling_ftp,
        method_name="get_cycling_ftp",
        api_call_desc="api.get_cycling_ftp()",
    )


def get_functional_threshold_power_range_data(api: Garmin) -> None:
    """Get historic functional threshold power (FTP) range."""
    call_and_display(
        api.get_functional_threshold_power_range,
        config.week_start.isoformat(),
        config.today.isoformat(),
        sport="CYCLING",
        aggregation="daily",
        method_name="get_functional_threshold_power_range",
        api_call_desc=f"api.get_functional_threshold_power_range('{config.week_start.isoformat()}', '{config.today.isoformat()}', sport='CYCLING', aggregation='daily')",
    )


def get_activity_details_data(api: Garmin) -> None:
    """Get detailed activity information for the last activity, plus its
    per-sample metrics resolved from positional indices to metric names.
    """
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            success, details = call_and_display(
                api.get_activity_details,
                activity_id,
                method_name="get_activity_details",
                api_call_desc=f"api.get_activity_details({activity_id})",
            )
            if success:
                call_and_display(
                    parse_activity_detail_metrics,
                    details,
                    method_name="parse_activity_detail_metrics",
                    api_call_desc=(
                        f"parse_activity_detail_metrics(details) for activity {activity_id}"
                    ),
                )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.activity_details_error", error=e))


def get_activity_gear_data(api: Garmin) -> None:
    """Get activity gear information for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_gear,
                activity_id,
                method_name="get_activity_gear",
                api_call_desc=f"api.get_activity_gear({activity_id})",
            )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.activity_gear_error", error=e))


def get_single_activity_data(api: Garmin) -> None:
    """Get single activity data for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity,
                activity_id,
                method_name="get_activity",
                api_call_desc=f"api.get_activity({activity_id})",
            )
        else:
            print(translate("demo.no_activities"))
    except Exception as e:
        print(translate("ui.single_activity_error", error=e))


def get_activity_exercise_sets_data(api: Garmin) -> None:
    """Get exercise sets for strength training activities."""
    try:
        activities = api.get_activities(
            0, 1, activitytype="fitness_equipment", activitysubtype="strength_training"
        )
        activity_list = (
            activities.get("activityList", [])
            if isinstance(activities, dict)
            else activities
        )
        strength_activity = activity_list[0] if activity_list else None

        if strength_activity:
            activity_id = strength_activity["activityId"]
            call_and_display(
                api.get_activity_exercise_sets,
                activity_id,
                method_name="get_activity_exercise_sets",
                api_call_desc=f"api.get_activity_exercise_sets({activity_id})",
            )
        else:
            # Return empty JSON response
            print(translate("demo.no_strength"))
    except Exception:
        print(translate("demo.no_exercise_sets"))


def get_golf_scorecard_data(api: Garmin) -> None:
    """Get golf scorecard detail by ID."""
    try:
        # First get summary to find valid IDs
        summary = api.get_golf_summary(limit=20)
        if not summary:
            print(translate("demo.no_golf"))
            return

        scorecards = (
            summary
            if isinstance(summary, list)
            else summary.get("scorecardList", summary.get("items", [summary]))
        )
        if isinstance(scorecards, list) and scorecards:
            print(translate("demo.recent_golf"))
            for i, sc in enumerate(scorecards[:10], 1):
                sc_id = sc.get("scorecardId", sc.get("id", "?"))
                course = sc.get("courseName", sc.get("golfCourseName", "Unknown"))
                sc_date = sc.get("startTime", sc.get("date", "?"))
                print(
                    translate(
                        "ui.scorecard_row_with_date",
                        index=i,
                        scorecard_id=sc_id,
                        course=course,
                        date=sc_date,
                    )
                )

        scorecard_id = input(translate("demo.scorecard_id")).strip()
        if not scorecard_id:
            print(translate("demo.no_scorecard_id"))
            return

        call_and_display(
            api.get_golf_scorecard,
            int(scorecard_id),
            method_name="get_golf_scorecard",
            api_call_desc=f"api.get_golf_scorecard({scorecard_id})",
        )
    except Exception as e:
        print(translate("ui.golf_scorecard_error", error=e))


def get_golf_shot_data_entry(api: Garmin) -> None:
    """Get golf shot data by scorecard ID."""
    try:
        # First get summary to find valid IDs
        summary = api.get_golf_summary(limit=20)
        if not summary:
            print(translate("demo.no_golf"))
            return

        scorecards = (
            summary
            if isinstance(summary, list)
            else summary.get("scorecardList", summary.get("items", [summary]))
        )
        if isinstance(scorecards, list) and scorecards:
            print(translate("demo.recent_golf"))
            for i, sc in enumerate(scorecards[:10], 1):
                sc_id = sc.get("scorecardId", sc.get("id", "?"))
                course = sc.get("courseName", sc.get("golfCourseName", "Unknown"))
                print(
                    translate(
                        "ui.scorecard_short_row",
                        index=i,
                        scorecard_id=sc_id,
                        course=course,
                    )
                )

        scorecard_id = input(translate("demo.scorecard_id")).strip()
        if not scorecard_id:
            print(translate("demo.no_scorecard_id"))
            return

        holes = input(translate("prompt.holes")).strip()
        holes = holes or None

        call_and_display(
            api.get_golf_shot_data,
            int(scorecard_id),
            hole_numbers=holes,
            method_name="get_golf_shot_data",
            api_call_desc=f"api.get_golf_shot_data({scorecard_id}, hole_numbers={holes!r})",
        )
    except Exception as e:
        print(translate("ui.golf_shot_error", error=e))


def get_training_plan_by_id_data(api: Garmin) -> None:
    """Get training plan details by ID (routes FBT_ADAPTIVE plans to the adaptive endpoint)."""
    resp = api.get_training_plans() or {}
    training_plans = resp.get("trainingPlanList") or []

    if not training_plans:
        print(translate("demo.no_training_plans"))
        prompt_text = translate("demo.training_plan_id")
    else:
        prompt_text = translate("demo.training_plan_id_recent")

    user_input = input(prompt_text).strip()
    selected = None
    if user_input:
        try:
            wanted_id = int(user_input)
            selected = next(
                (
                    p
                    for p in training_plans
                    if int(p.get("trainingPlanId", 0)) == wanted_id
                ),
                None,
            )
            if not selected:
                print(translate("ui.plan_missing", plan_id=wanted_id))
                plan_id = wanted_id
                plan_name = f"Plan {wanted_id}"
                plan_category = None
            else:
                plan_id = int(selected["trainingPlanId"])
                plan_name = selected.get("name", str(plan_id))
                plan_category = selected.get("trainingPlanCategory")
        except ValueError:
            print(translate("error.invalid_plan"))
            return
    else:
        if not training_plans:
            print(translate("ui.no_plans_id"))
            return
        selected = training_plans[-1]
        plan_id = int(selected["trainingPlanId"])
        plan_name = selected.get("name", str(plan_id))
        plan_category = selected.get("trainingPlanCategory")

    if plan_category == "FBT_ADAPTIVE":
        call_and_display(
            api.get_adaptive_training_plan_by_id,
            plan_id,
            method_name="get_adaptive_training_plan_by_id",
            api_call_desc=f"api.get_adaptive_training_plan_by_id({plan_id}) - {plan_name}",
        )
    else:
        call_and_display(
            api.get_training_plan_by_id,
            plan_id,
            method_name="get_training_plan_by_id",
            api_call_desc=f"api.get_training_plan_by_id({plan_id}) - {plan_name}",
        )


def get_workout_by_id_data(api: Garmin) -> None:
    """Get workout by ID for the last workout."""
    try:
        workouts = api.get_workouts()
        if workouts:
            workout_id = workouts[-1]["workoutId"]
            workout_name = workouts[-1]["workoutName"]
            call_and_display(
                api.get_workout_by_id,
                workout_id,
                method_name="get_workout_by_id",
                api_call_desc=f"api.get_workout_by_id({workout_id}) - {workout_name}",
            )
        else:
            print(translate("demo.no_workouts"))
    except Exception as e:
        print(translate("ui.workout_by_id_error", error=e))


def download_workout_data(api: Garmin) -> None:
    """Download workout to .FIT file."""
    try:
        workouts = api.get_workouts()
        if workouts:
            workout_id = workouts[-1]["workoutId"]
            workout_name = workouts[-1]["workoutName"]

            print(translate("ui.plan_download", name=workout_name))
            workout_data = api.download_workout(workout_id)

            if workout_data:
                safe_name = _safe_filename_component(workout_name)
                safe_id = _safe_filename_component(workout_id)
                output_file = config.export_dir / f"{safe_name}_{safe_id}.fit"
                with _open_private(output_file, "wb") as f:
                    f.write(workout_data)
                print(translate("result.workout_downloaded", path=output_file))
            else:
                print(translate("result.no_workout_data"))
        else:
            print(translate("demo.no_workouts"))
    except Exception as e:
        print(translate("error.workout_download_error", error=e))


def upload_workout_data(api: Garmin) -> None:
    """Upload workout from JSON file."""
    try:
        print(translate("ui.workout_file_upload", path=config.workoutfile))

        # Check if file exists
        if not os.path.exists(config.workoutfile):
            print(translate("demo.file_not_found", path=config.workoutfile))
            print(translate("ui.workout_json_missing"))
            return

        # Load the workout JSON data
        import json

        with open(config.workoutfile, encoding="utf-8") as f:
            workout_data = json.load(f)

        # Get current timestamp in Garmin format
        current_time = datetime.datetime.now()
        garmin_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S.0")

        # Remove IDs that shouldn't be included when uploading a new workout
        fields_to_remove = ["workoutId", "ownerId", "updatedDate", "createdDate"]
        for field in fields_to_remove:
            if field in workout_data:
                del workout_data[field]

        # Add current timestamps
        workout_data["createdDate"] = garmin_timestamp
        workout_data["updatedDate"] = garmin_timestamp

        # Remove step IDs to ensure new ones are generated
        def clean_step_ids(workout_segments):
            """Recursively remove step IDs from workout structure."""
            if isinstance(workout_segments, list):
                for segment in workout_segments:
                    clean_step_ids(segment)
            elif isinstance(workout_segments, dict):
                # Remove stepId if present
                if "stepId" in workout_segments:
                    del workout_segments["stepId"]

                # Recursively clean nested structures
                if "workoutSteps" in workout_segments:
                    clean_step_ids(workout_segments["workoutSteps"])

                # Handle any other nested lists or dicts
                for value in workout_segments.values():
                    if isinstance(value, list | dict):
                        clean_step_ids(value)

        # Clean step IDs from workout segments
        if "workoutSegments" in workout_data:
            clean_step_ids(workout_data["workoutSegments"])

        # Update workout name to indicate it's uploaded with current timestamp
        original_name = workout_data.get("workoutName", "Workout")
        workout_data["workoutName"] = (
            f"Uploaded {original_name} - {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        print(translate("ui.workout_uploading", name=workout_data["workoutName"]))

        # Upload the workout
        result = api.upload_workout(workout_data)

        if result:
            print(translate("result.workout_uploaded"))
            call_and_display(
                lambda: result,  # Use a lambda to pass the result
                method_name="upload_workout",
                api_call_desc="api.upload_workout(workout_data)",
            )
        else:
            print(translate("ui.upload_workout_failed", path=config.workoutfile))

    except FileNotFoundError:
        print(translate("demo.file_not_found", path=config.workoutfile))
        print(translate("ui.workout_json_missing"))
    except json.JSONDecodeError as e:
        print(translate("ui.json_error", path=config.workoutfile, error=e))
        print(translate("ui.check_json"))
    except Exception as e:
        print(translate("error.workout_upload_error", error=e))
        # Check for common upload errors
        error_str = str(e)
        if "400" in error_str:
            print(translate("error.workout_invalid"))
        elif "401" in error_str:
            print(translate("error.auth_upload"))
        elif "403" in error_str:
            print(translate("error.permission"))
        elif "409" in error_str:
            print(translate("error.workout_exists"))
        elif "422" in error_str:
            print(translate("error.workout_validation"))


def upload_running_workout_data(api: Garmin) -> None:
    """Upload a typed running workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_running_workout import create_sample_running_workout

        print(translate("ui.running_upload"))
        workout = create_sample_running_workout()
        print(translate("ui.workout_uploading", name=workout.workoutName))

        result = api.upload_running_workout(workout)

        if result:
            print(translate("ui.running_uploaded"))
            call_and_display(
                lambda: result,
                method_name="upload_running_workout",
                api_call_desc="api.upload_running_workout(workout)",
            )
        else:
            print(translate("ui.running_failed"))
    except ImportError as e:
        print(translate("ui.generic_error", error=e))
        print(translate("error.pydantic"))
    except Exception as e:
        print(translate("ui.running_upload_error", error=e))


def upload_cycling_workout_data(api: Garmin) -> None:
    """Upload a typed cycling workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_cycling_workout import create_sample_cycling_workout

        print(translate("ui.cycling_upload"))
        workout = create_sample_cycling_workout()
        print(translate("ui.workout_uploading", name=workout.workoutName))

        result = api.upload_cycling_workout(workout)

        if result:
            print(translate("ui.cycling_uploaded"))
            call_and_display(
                lambda: result,
                method_name="upload_cycling_workout",
                api_call_desc="api.upload_cycling_workout(workout)",
            )
        else:
            print(translate("ui.cycling_failed"))
    except ImportError as e:
        print(translate("ui.generic_error", error=e))
        print(translate("error.pydantic"))
    except Exception as e:
        print(translate("ui.cycling_upload_error", error=e))


def upload_swimming_workout_data(api: Garmin) -> None:
    """Upload a typed swimming workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_swimming_workout import create_sample_swimming_workout

        print(translate("ui.swimming_upload"))
        workout = create_sample_swimming_workout()
        print(translate("ui.workout_uploading", name=workout.workoutName))

        result = api.upload_swimming_workout(workout)

        if result:
            print(translate("ui.swimming_uploaded"))
            call_and_display(
                lambda: result,
                method_name="upload_swimming_workout",
                api_call_desc="api.upload_swimming_workout(workout)",
            )
        else:
            print(translate("ui.swimming_failed"))
    except ImportError as e:
        print(translate("ui.generic_error", error=e))
        print(translate("error.pydantic"))
    except Exception as e:
        print(translate("ui.swimming_upload_error", error=e))


def upload_walking_workout_data(api: Garmin) -> None:
    """Upload a typed walking workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_walking_workout import create_sample_walking_workout

        print(translate("ui.walking_upload"))
        workout = create_sample_walking_workout()
        print(translate("ui.workout_uploading", name=workout.workoutName))

        result = api.upload_walking_workout(workout)

        if result:
            print(translate("ui.walking_uploaded"))
            call_and_display(
                lambda: result,
                method_name="upload_walking_workout",
                api_call_desc="api.upload_walking_workout(workout)",
            )
        else:
            print(translate("ui.walking_failed"))
    except ImportError as e:
        print(translate("ui.generic_error", error=e))
        print(translate("error.pydantic"))
    except Exception as e:
        print(translate("ui.walking_upload_error", error=e))


def upload_hiking_workout_data(api: Garmin) -> None:
    """Upload a typed hiking workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_hiking_workout import create_sample_hiking_workout

        print(translate("ui.hiking_upload"))
        workout = create_sample_hiking_workout()
        print(translate("ui.workout_uploading", name=workout.workoutName))

        result = api.upload_hiking_workout(workout)

        if result:
            print(translate("ui.hiking_uploaded"))
            call_and_display(
                lambda: result,
                method_name="upload_hiking_workout",
                api_call_desc="api.upload_hiking_workout(workout)",
            )
        else:
            print(translate("ui.hiking_failed"))
    except ImportError as e:
        print(translate("ui.generic_error", error=e))
        print(translate("error.pydantic"))
    except Exception as e:
        print(translate("ui.hiking_upload_error", error=e))


def search_exercise_catalog_data(api: Garmin) -> None:
    """Search the bundled strength-exercise catalog."""
    from garminconnect import exercises

    _ = api
    term = input(translate("prompt.exercise")).strip()
    if not term:
        print(translate("demo.no_search_term"))
        return

    exact = exercises.resolve(term)
    if exact:
        print(translate("ui.exact_exercise", term=term))
        print(
            translate(
                "ui.exercise_location",
                category=repr(exact["category"]),
                exercise=repr(exact["exercise"]),
            )
        )
        return

    matches = exercises.find(term)
    if not matches:
        print(translate("ui.no_exercises", term=term))
        return

    print(translate("ui.exercise_matches", count=len(matches), term=term))
    for e in matches[:20]:
        print(
            translate(
                "ui.exercise_item",
                name=repr(e["name"]),
                category=repr(e["category"]),
                exercise=repr(e["exercise"]),
            )
        )


def upload_strength_workout_data(api: Garmin) -> None:
    """Upload a typed strength workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_strength_workout import create_sample_strength_workout

        print(translate("ui.strength_upload"))
        workout = create_sample_strength_workout()
        print(translate("ui.workout_uploading", name=workout.workoutName))

        result = api.upload_strength_workout(workout)

        if result:
            print(translate("ui.strength_uploaded"))
            call_and_display(
                lambda: result,
                method_name="upload_strength_workout",
                api_call_desc="api.upload_strength_workout(workout)",
            )
        else:
            print(translate("ui.strength_failed"))
    except ImportError as e:
        print(translate("ui.generic_error", error=e))
        print(translate("error.pydantic"))
    except Exception as e:
        print(translate("ui.strength_upload_error", error=e))


def schedule_workout_data(api: Garmin) -> None:
    """Schedule a workout on a specific date."""
    try:
        workouts = api.get_workouts()
        if not workouts:
            print(translate("demo.no_workouts"))
            return

        print(translate("demo.available_workouts"))
        for i, workout in enumerate(workouts[:10]):
            workout_id = workout.get("workoutId")
            workout_name = workout.get("workoutName", "Unknown")
            print(
                translate(
                    "ui.indexed_workout",
                    index=i,
                    name=workout_name,
                    workout_id=workout_id,
                )
            )

        try:
            index_input = input(
                translate("prompt.workout_index", maximum=min(9, len(workouts) - 1))
            ).strip()

            if index_input.lower() == "q":
                print(translate("error.cancelled"))
                return

            workout_index = int(index_input)
            if not (0 <= workout_index < min(10, len(workouts))):
                print(translate("error.invalid_index"))
                return

            selected_workout = workouts[workout_index]
            workout_id = selected_workout["workoutId"]
            workout_name = selected_workout.get("workoutName", "Unknown")

            date_input = input(
                translate("prompt.schedule_date", name=workout_name)
            ).strip()
            schedule_date = date_input if date_input else config.today.isoformat()

            call_and_display(
                api.schedule_workout,
                workout_id,
                schedule_date,
                method_name="schedule_workout",
                api_call_desc=f"api.schedule_workout({workout_id}, '{schedule_date}') - {workout_name}",
            )

            print(translate("result.workout_scheduled"))

        except ValueError:
            print(translate("error.invalid_input"))

    except Exception as e:
        print(translate("ui.schedule_error", error=e))


def get_scheduled_workouts(api: Garmin) -> None:
    """Get scheduled workout by year and month."""
    try:
        year_input = input(translate("prompt.year")).strip()
        month_input = input(translate("prompt.month")).strip()

        if not year_input or not month_input:
            print(translate("ui.year_month_required"))
            return

        year = int(year_input)
        month = int(month_input)

        call_and_display(
            api.get_scheduled_workouts,
            year,
            month,
            method_name="get_scheduled_workouts",
            api_call_desc=f"api.get_scheduled_workouts({year}, {month})",
        )
    except Exception as e:
        print(translate("ui.scheduled_by_month_error", error=e))


def get_next_scheduled_workout_data(api: Garmin) -> None:
    """Get the earliest upcoming scheduled workout (today or later)."""
    try:
        call_and_display(
            api.get_next_scheduled_workout,
            method_name="get_next_scheduled_workout",
            api_call_desc="api.get_next_scheduled_workout()",
        )
    except Exception as e:
        print(translate("ui.next_workout_error", error=e))


def get_scheduled_workout_by_id_data(api: Garmin) -> None:
    """Get scheduled workout by ID."""
    try:
        scheduled_workout_id = input(translate("prompt.scheduled_id")).strip()

        if not scheduled_workout_id:
            print(translate("ui.scheduled_id_required"))
            return

        call_and_display(
            api.get_scheduled_workout_by_id,
            scheduled_workout_id,
            method_name="get_scheduled_workout_by_id",
            api_call_desc=f"api.get_scheduled_workout_by_id({scheduled_workout_id})",
        )
    except Exception as e:
        print(translate("ui.scheduled_by_id_error", error=e))


def delete_workout_data(api: Garmin) -> None:
    """Delete a workout template from the library."""
    try:
        workouts = api.get_workouts()
        if not workouts:
            print(translate("demo.no_workouts"))
            return

        print(translate("demo.available_workouts"))
        for i, workout in enumerate(workouts[:10]):
            workout_id = workout.get("workoutId")
            workout_name = workout.get("workoutName", "Unknown")
            print(
                translate(
                    "ui.indexed_workout",
                    index=i,
                    name=workout_name,
                    workout_id=workout_id,
                )
            )

        try:
            index_input = input(
                translate(
                    "prompt.delete_workout_index", maximum=min(9, len(workouts) - 1)
                )
            ).strip()

            if index_input.lower() == "q":
                print(translate("error.cancelled"))
                return

            workout_index = int(index_input)
            if not (0 <= workout_index < min(10, len(workouts))):
                print(translate("error.invalid_index"))
                return

            selected_workout = workouts[workout_index]
            workout_id = selected_workout["workoutId"]
            workout_name = selected_workout.get("workoutName", "Unknown")

            confirm = input(
                translate(
                    "prompt.delete_workout", name=workout_name, workout_id=workout_id
                )
            ).strip()
            if confirm.lower() != "y":
                print(translate("error.cancelled"))
                return

            call_and_display(
                api.delete_workout,
                workout_id,
                method_name="delete_workout",
                api_call_desc=f"api.delete_workout({workout_id}) - {workout_name}",
            )
            print(translate("result.workout_deleted"))

        except ValueError:
            print(translate("error.invalid_input"))

    except Exception as e:
        print(translate("error.delete_workout_error", error=e))


def update_workout_data(api: Garmin) -> None:
    """Edit a workout in place (rename it) via update_workout."""
    try:
        workouts = api.get_workouts()
        if not workouts:
            print(translate("demo.no_workouts"))
            return

        print(translate("demo.available_workouts"))
        for i, workout in enumerate(workouts[:10]):
            workout_id = workout.get("workoutId")
            workout_name = workout.get("workoutName", "Unknown")
            print(
                translate(
                    "ui.indexed_workout",
                    index=i,
                    name=workout_name,
                    workout_id=workout_id,
                )
            )

        try:
            index_input = input(
                translate(
                    "prompt.update_workout_index", maximum=min(9, len(workouts) - 1)
                )
            ).strip()

            if index_input.lower() == "q":
                print(translate("error.cancelled"))
                return

            workout_index = int(index_input)
            if not (0 <= workout_index < min(10, len(workouts))):
                print(translate("error.invalid_index"))
                return

            selected_workout = workouts[workout_index]
            workout_id = selected_workout["workoutId"]

            # update_workout replaces the whole workout, so start from the full
            # structure rather than the summary returned by get_workouts()
            workout_data = api.get_workout_by_id(workout_id)
            original_name = workout_data.get("workoutName", "Workout")

            new_name = input(
                translate("prompt.new_workout_name", name=original_name)
            ).strip()
            if new_name:
                workout_data["workoutName"] = new_name

            call_and_display(
                api.update_workout,
                workout_id,
                workout_data,
                method_name="update_workout",
                api_call_desc=f"api.update_workout({workout_id}, workout_data)",
            )
            print(translate("result.workout_updated"))

        except ValueError:
            print(translate("error.invalid_input"))

    except Exception as e:
        print(translate("error.update_workout_error", error=e))


def push_workout_to_device_data(api: Garmin) -> None:
    """Push a workout to a device, defaulting to the last workout/device."""
    try:
        workouts = api.get_workouts()
        if not workouts:
            print(translate("demo.no_workouts"))
            return

        print(translate("demo.available_workouts"))
        for i, workout in enumerate(workouts[:10]):
            workout_id = workout.get("workoutId")
            workout_name = workout.get("workoutName", "Unknown")
            print(
                translate(
                    "ui.indexed_workout",
                    index=i,
                    name=workout_name,
                    workout_id=workout_id,
                )
            )

        index_input = input(
            translate("prompt.push_workout_index", maximum=min(9, len(workouts) - 1))
        ).strip()

        if index_input.lower() == "q":
            print(translate("error.cancelled"))
            return

        workout_id = None
        if index_input:
            try:
                workout_index = int(index_input)
            except ValueError:
                print(translate("error.invalid_input"))
                return
            if not (0 <= workout_index < min(10, len(workouts))):
                print(translate("error.invalid_index"))
                return
            workout_id = workouts[workout_index]["workoutId"]

        devices = api.get_devices()
        device_id = None
        if devices:
            print(translate("demo.available_devices"))
            for i, device in enumerate(devices):
                d_id = device.get("deviceId")
                d_name = device.get("displayName", "Unknown")
                print(
                    translate(
                        "ui.indexed_workout", index=i, name=d_name, workout_id=d_id
                    )
                )

            device_input = input(
                translate("prompt.device_index", maximum=len(devices) - 1)
            ).strip()
            if device_input:
                try:
                    device_index = int(device_input)
                except ValueError:
                    print(translate("error.invalid_input"))
                    return
                if not (0 <= device_index < len(devices)):
                    print(translate("error.invalid_index"))
                    return
                device_id = devices[device_index]["deviceId"]

        call_and_display(
            api.push_workout_to_device,
            workout_id,
            device_id,
            method_name="push_workout_to_device",
            api_call_desc=f"api.push_workout_to_device({workout_id}, {device_id})",
        )
        print(translate("result.workout_pushed"))

    except Exception as e:
        print(translate("ui.push_error", error=e))


def unschedule_workout_data(api: Garmin) -> None:
    """Remove a scheduled workout from the calendar."""
    try:
        scheduled_id = input(translate("prompt.unschedule_id")).strip()

        if not scheduled_id:
            print(translate("ui.scheduled_id_required"))
            return

        call_and_display(
            api.unschedule_workout,
            scheduled_id,
            method_name="unschedule_workout",
            api_call_desc=f"api.unschedule_workout({scheduled_id})",
        )
        print(translate("result.workout_unscheduled"))

    except Exception as e:
        print(translate("ui.unschedule_error", error=e))


def add_body_composition_data(api: Garmin) -> None:
    """Add body composition data."""
    try:
        print(translate("ui.body_composition_loading", date=config.today.isoformat()))
        print("-" * 50)

        # Get weight input from user
        while True:
            try:
                weight_str = input(translate("prompt.enter_weight_kg")).strip()
                if not weight_str:
                    weight = 85.1
                    break
                weight = float(weight_str)
                if 30 <= weight <= 300:
                    break
                print(translate("error.weight_kg"))
            except ValueError:
                print(translate("error.invalid_number"))

        call_and_display(
            api.add_body_composition,
            config.today.isoformat(),
            weight=weight,
            percent_fat=15.4,
            percent_hydration=54.8,
            visceral_fat_mass=10.8,
            bone_mass=2.9,
            muscle_mass=55.2,
            basal_met=1454.1,
            active_met=None,
            physique_rating=None,
            metabolic_age=33.0,
            visceral_fat_rating=None,
            bmi=22.2,
            method_name="add_body_composition",
            api_call_desc=f"api.add_body_composition({config.today.isoformat()}, weight={weight}, ...)",
        )
        print(translate("result.body_added"))
    except Exception as e:
        print(translate("error.body_error", error=e))


def delete_weigh_ins_data(api: Garmin) -> None:
    """Delete all weigh-ins for today."""
    try:
        call_and_display(
            api.delete_weigh_ins,
            config.today.isoformat(),
            delete_all=True,
            method_name="delete_weigh_ins",
            api_call_desc=f"api.delete_weigh_ins({config.today.isoformat()}, delete_all=True)",
        )
        print(translate("result.weigh_ins_deleted"))
    except Exception as e:
        print(translate("error.delete_weigh_error", error=e))


def delete_weigh_in_data(api: Garmin) -> None:
    """Delete a specific weigh-in."""
    try:
        all_weigh_ins = []

        # Find weigh-ins
        print(translate("ui.daily_weigh_loading", date=config.today.isoformat()))
        try:
            daily_weigh_ins = api.get_daily_weigh_ins(config.today.isoformat())

            if daily_weigh_ins and "dateWeightList" in daily_weigh_ins:
                weight_list = daily_weigh_ins["dateWeightList"]
                for weigh_in in weight_list:
                    if isinstance(weigh_in, dict):
                        all_weigh_ins.append(weigh_in)
                print(translate("ui.stats_weighings", count=len(all_weigh_ins)))
            else:
                print(translate("ui.no_weigh_response"))
        except Exception as e:
            print(translate("ui.stats_weighings_error", error=e))

        if not all_weigh_ins:
            print(translate("error.no_weigh_today"))
            print(translate("ui.add_test_weigh"))
            return

        print(translate("ui.weighings_for_delete", count=len(all_weigh_ins)))
        print("-" * 70)

        # Display weigh-ins for user selection
        for i, weigh_in in enumerate(all_weigh_ins):
            # Extract weight data - Garmin API uses different field names
            weight = weigh_in.get("weight")
            if weight is None:
                weight = weigh_in.get("weightValue", "Unknown")

            # Convert weight from grams to kg if it's a number
            if isinstance(weight, int | float) and weight > 1000:
                weight = weight / 1000  # Convert from grams to kg
                weight = round(weight, 1)  # Round to 1 decimal place

            unit = weigh_in.get("unitKey", "kg")
            date = weigh_in.get("calendarDate", config.today.isoformat())

            # Try different timestamp fields
            timestamp = (
                weigh_in.get("timestampGMT")
                or weigh_in.get("timestamp")
                or weigh_in.get("date")
            )

            # Format timestamp for display
            if timestamp:
                try:
                    import datetime as dt

                    if isinstance(timestamp, str):
                        # Handle ISO format strings
                        datetime_obj = dt.datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
                    else:
                        # Handle millisecond timestamps
                        datetime_obj = dt.datetime.fromtimestamp(timestamp / 1000)
                    time_str = datetime_obj.strftime("%H:%M:%S")
                except Exception:
                    time_str = "Unknown time"
            else:
                time_str = "Unknown time"

            print(
                translate(
                    "ui.weighing_row",
                    index=i,
                    weight=weight,
                    unit=unit,
                    date=date,
                    time=time_str,
                )
            )

        print()
        try:
            selection = input(translate("prompt.weigh_in_delete")).strip()

            if selection.lower() == "q":
                print(translate("ui.delete_cancelled"))
                return

            weigh_in_index = int(selection)
            if 0 <= weigh_in_index < len(all_weigh_ins):
                selected_weigh_in = all_weigh_ins[weigh_in_index]

                # Get the weigh-in ID (Garmin uses 'samplePk' as the primary key)
                weigh_in_id = (
                    selected_weigh_in.get("samplePk")
                    or selected_weigh_in.get("id")
                    or selected_weigh_in.get("weightPk")
                    or selected_weigh_in.get("pk")
                    or selected_weigh_in.get("weightId")
                    or selected_weigh_in.get("uuid")
                )

                if weigh_in_id:
                    weight = selected_weigh_in.get("weight", "Unknown")

                    # Convert weight from grams to kg if it's a number
                    if isinstance(weight, int | float) and weight > 1000:
                        weight = weight / 1000  # Convert from grams to kg
                        weight = round(weight, 1)  # Round to 1 decimal place

                    unit = selected_weigh_in.get("unitKey", "kg")
                    date = selected_weigh_in.get(
                        "calendarDate", config.today.isoformat()
                    )

                    # Confirm deletion
                    confirm = input(
                        translate(
                            "prompt.delete_weigh_in_confirm",
                            weight=weight,
                            unit=unit,
                            date=date,
                        )
                    ).lower()
                    if confirm == "yes":
                        call_and_display(
                            api.delete_weigh_in,
                            weigh_in_id,
                            config.today.isoformat(),
                            method_name="delete_weigh_in",
                            api_call_desc=f"api.delete_weigh_in({weigh_in_id}, {config.today.isoformat()})",
                        )
                        print(translate("ui.weigh_deleted"))
                    else:
                        print(translate("ui.delete_cancelled"))
                else:
                    print(translate("ui.no_weigh_id"))
            else:
                print(translate("error.invalid_selection"))

        except ValueError:
            print(translate("ui.number_required"))

    except Exception as e:
        print(translate("error.delete_single_weigh_error", error=e))


def get_device_settings_data(api: Garmin) -> None:
    """Get device settings for all devices."""
    try:
        devices = api.get_devices()
        if devices:
            for device in devices:
                device_id = device["deviceId"]
                device_name = device.get("displayName", f"Device {device_id}")
                try:
                    call_and_display(
                        api.get_device_settings,
                        device_id,
                        method_name="get_device_settings",
                        api_call_desc=f"api.get_device_settings({device_id}) - {device_name}",
                    )
                except Exception as e:
                    print(
                        translate("ui.gear_settings_error", device=device_name, error=e)
                    )
        else:
            print(translate("error.no_devices"))
    except Exception as e:
        print(translate("ui.device_settings_error", error=e))


def get_gear_data(api: Garmin) -> None:
    """Get user gear list."""
    print(translate("ui.fetch_gear"))

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number from the first call
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )
        else:
            print(translate("error.no_profile"))

    call_and_display(group_name="User Gear List", api_responses=api_responses)


def get_gear_defaults_data(api: Garmin) -> None:
    """Get gear defaults."""
    print(translate("ui.fetch_gear_defaults"))

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number from the first call
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            api_responses.append(
                safe_call_for_group(
                    api.get_gear_defaults,
                    user_profile_number,
                    method_name="get_gear_defaults",
                    api_call_desc=f"api.get_gear_defaults({user_profile_number})",
                )
            )
        else:
            print(translate("error.no_profile"))

    call_and_display(group_name="Gear Defaults", api_responses=api_responses)


def get_gear_stats_data(api: Garmin) -> None:
    """Get gear statistics."""
    print(translate("ui.fetch_gear_stats"))

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number and gear list
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            # Get gear list
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )

            # Get gear data to extract UUIDs for stats
            gear_success, gear_data, _ = safe_api_call(
                api.get_gear, user_profile_number, method_name="get_gear"
            )

            if gear_success and gear_data:
                # Get stats for each gear item (limit to first 3)
                for gear_item in gear_data[:3]:
                    gear_uuid = gear_item.get("uuid")
                    gear_name = gear_item.get("displayName", "Unknown")
                    if gear_uuid:
                        api_responses.append(
                            safe_call_for_group(
                                api.get_gear_stats,
                                gear_uuid,
                                method_name="get_gear_stats",
                                api_call_desc=f"api.get_gear_stats('{gear_uuid}') - {gear_name}",
                            )
                        )
            else:
                print(translate("error.no_gear"))
        else:
            print(translate("error.no_profile"))

    call_and_display(group_name="Gear Statistics", api_responses=api_responses)


def get_gear_activities_data(api: Garmin) -> None:
    """Get gear activities."""
    print(translate("ui.fetch_gear_activities"))

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number and gear list
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            # Get gear list
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )

            # Get gear data to extract UUID for activities
            gear_success, gear_data, _ = safe_api_call(
                api.get_gear, user_profile_number, method_name="get_gear"
            )

            if gear_success and gear_data and len(gear_data) > 0:
                # Get activities for the first gear item
                gear_uuid = gear_data[0].get("uuid")
                gear_name = gear_data[0].get("displayName", "Unknown")

                if gear_uuid:
                    api_responses.append(
                        safe_call_for_group(
                            api.get_gear_activities,
                            gear_uuid,
                            method_name="get_gear_activities",
                            api_call_desc=f"api.get_gear_activities('{gear_uuid}') - {gear_name}",
                        )
                    )
                else:
                    print(translate("error.no_gear_uuid"))
            else:
                print(translate("error.no_gear"))
        else:
            print(translate("error.no_profile"))

    call_and_display(group_name="Gear Activities", api_responses=api_responses)


def set_gear_default_data(api: Garmin) -> None:
    """Set gear default."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear = api.get_gear(user_profile_number)
            if gear:
                gear_uuid = gear[0].get("uuid")
                gear_name = gear[0].get("displayName", "Unknown")
                if gear_uuid:
                    # Set as default for running (activity type ID 1)
                    # Correct method signature: set_gear_default(activityType, gearUUID, defaultGear=True)
                    activity_type = 1  # Running
                    call_and_display(
                        api.set_gear_default,
                        activity_type,
                        gear_uuid,
                        True,
                        method_name="set_gear_default",
                        api_call_desc=f"api.set_gear_default({activity_type}, '{gear_uuid}', True) - {gear_name} for running",
                    )
                    print(translate("result.gear_default"))
                else:
                    print(translate("error.no_gear_uuid"))
            else:
                print(translate("error.no_gear"))
        else:
            print(translate("error.no_profile"))
    except Exception as e:
        print(translate("error.gear_default_error", error=e))


def add_and_remove_gear_to_activity(api: Garmin) -> None:
    """Add gear to most recent activity, then remove."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear_list = api.get_gear(user_profile_number)
            if gear_list:
                activities = api.get_activities(0, 1)
                if activities:
                    activity_id = activities[0].get("activityId")
                    activity_name = activities[0].get("activityName")
                    for gear in gear_list:
                        if gear["gearStatusName"] == "active":
                            break
                    gear_uuid = gear.get("uuid")
                    gear_name = gear.get("displayName", "Unknown")
                    if gear_uuid:
                        # Add gear to an activity
                        # Correct method signature: add_gear_to_activity(gearUUID, activity_id)
                        call_and_display(
                            api.add_gear_to_activity,
                            gear_uuid,
                            activity_id,
                            method_name="add_gear_to_activity",
                            api_call_desc=f"api.add_gear_to_activity('{gear_uuid}', {activity_id}) - Add {gear_name} to {activity_name}",
                        )
                        print(translate("result.gear_added"))

                        # Wait for user to check gear, then continue
                        input(translate("ui.confirm_garmin"))

                        # Remove gear from an activity
                        # Correct method signature: remove_gear_from_activity(gearUUID, activity_id)
                        call_and_display(
                            api.remove_gear_from_activity,
                            gear_uuid,
                            activity_id,
                            method_name="remove_gear_from_activity",
                            api_call_desc=f"api.remove_gear_from_activity('{gear_uuid}', {activity_id}) - Remove {gear_name} from {activity_name}",
                        )
                        print(translate("result.gear_removed"))
                    else:
                        print(translate("ui.no_activity_error"))
                else:
                    print(translate("error.no_gear_uuid"))
            else:
                print(translate("error.no_gear"))
        else:
            print(translate("error.no_profile"))
    except Exception as e:
        print(translate("error.gear_add_error", error=e))


def get_activities_filtered_data(api: Garmin) -> None:
    """Get activities filtered by type/subtype, picked from the account's own activity type list."""
    try:
        activity_types = api.get_activity_types()
        print(translate("demo.available_activity_types"))
        for i, activity_type in enumerate(activity_types):
            print(
                translate(
                    "ui.activity_type_row",
                    index=i,
                    type_key=activity_type.get("typeKey", "Unknown"),
                    display=activity_type.get("display", "No description"),
                )
            )

        type_index = input(translate("prompt.activity_type_index")).strip()

        activitytype = None
        if type_index:
            try:
                idx = int(type_index)
                if 0 <= idx < len(activity_types):
                    activitytype = activity_types[idx]["typeKey"]
                else:
                    print(translate("ui.invalid_type_filter"))
            except ValueError:
                print(translate("ui.invalid_type_filter"))

        activitysubtype = None
        if activitytype:
            hint = (
                " (e.g. 'strength_training')"
                if activitytype == "fitness_equipment"
                else ""
            )
            activitysubtype = (
                input(translate("prompt.activity_subtype", hint=hint)).strip() or None
            )

        call_and_display(
            api.get_activities,
            config.start,
            config.default_limit,
            activitytype=activitytype,
            activitysubtype=activitysubtype,
            method_name="get_activities_filtered",
            api_call_desc=(
                f"api.get_activities({config.start}, {config.default_limit}, "
                f"activitytype={activitytype!r}, activitysubtype={activitysubtype!r})"
            ),
        )
    except Exception as e:
        print(translate("error.gear_filter_error", error=e))


def create_gear_data(api: Garmin) -> None:
    """Create a new piece of gear, e.g. a pair of shoes."""
    try:
        print(translate("demo.new_gear"))
        print(translate("demo.gear_details"))

        gear_type = input(translate("prompt.gear_type")).strip() or "SHOES"
        brand = input(translate("prompt.brand")).strip() or "Anta"
        model = input(translate("prompt.model")).strip() or "A-Flash"
        name = input(translate("prompt.nickname")).strip() or "Test"
        first_use_date = (
            input(translate("prompt.first_use", date=config.today.isoformat())).strip()
            or config.today.isoformat()
        )
        usage_type = input(translate("prompt.usage_type")).strip() or "DISTANCE"
        max_km = input(translate("prompt.gear_threshold")).strip()
        activity_types_input = input(translate("prompt.default_types")).strip()
        activity_type_keys = [
            key.strip()
            for key in (activity_types_input or "running").split(",")
            if key.strip()
        ]
        notes = input(translate("prompt.gear_notes")).strip()

        try:
            max_usage_distance_km = float(max_km) if max_km else None

            success, _ = call_and_display(
                api.create_gear,
                gear_type=gear_type,
                brand=brand,
                model=model,
                name=name,
                first_use_date=first_use_date,
                usage_type=usage_type,
                max_usage_distance_km=max_usage_distance_km,
                notes=notes,
                activity_type_keys=activity_type_keys,
                method_name="create_gear",
                api_call_desc=(
                    f"api.create_gear(gear_type='{gear_type}', brand='{brand}', "
                    f"model='{model}', name='{name}', "
                    f"first_use_date='{first_use_date}', usage_type='{usage_type}', "
                    f"max_usage_distance_km={max_usage_distance_km}, "
                    f"activity_type_keys={activity_type_keys})"
                ),
            )
            if success:
                print(translate("result.gear_created"))
        except ValueError:
            print(translate("error.invalid_numeric"))
    except Exception as e:
        print(translate("error.gear_create_error", error=e))


def _format_record_duration(seconds: float) -> str:
    """Format a personal-record time value (seconds) as h:mm:ss or m:ss."""
    total = round(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _format_record_distance(meters: float) -> str:
    """Format a personal-record distance value (meters) as km."""
    return f"{meters / 1000:.2f} km"


def _format_record_count(value: float) -> str:
    """Format a personal-record count value (e.g. steps) with thousands separators."""
    return f"{round(value):,}"


def _format_record_days(value: float) -> str:
    """Format a personal-record day-count value (e.g. a goal streak)."""
    days = round(value)
    return f"{days} day" if days == 1 else f"{days} days"


_RECORD_FORMATTERS = {
    "time": _format_record_duration,
    "distance": _format_record_distance,
    "count": _format_record_count,
    "days": _format_record_days,
}


def get_personal_records_data(api: Garmin) -> None:
    """Get personal records, decoding typeId into a human-readable label
    and value, and optionally looking up the source activity's details
    (needed for longest-run duration, which isn't included in the
    personal-record entry itself).

    Two typeId ranges are confirmed against a real account's Garmin
    Connect "Personal Records" page:
      - activityType == "running": typeIds 1-6 are best-time records for
        a fixed distance (value is a duration in seconds), typeId 7 is a
        distance record (value is meters).
      - activityType is None: typeIds 12-14 are step counts (day/week/
        month), 15-16 are goal-streak day counts.
    Anything else is shown as an unconfirmed raw value — check the Garmin
    Connect "Personal Records" page for what it actually is rather than
    trusting a guess here.
    """
    # (label, formatter key) — see _RECORD_FORMATTERS. Confirmed against a
    # real account; see docstring.
    running_type_info = {
        1: ("1 km", "time"),
        2: ("1 mile", "time"),
        3: ("5 km", "time"),
        4: ("10 km", "time"),
        5: ("Half marathon", "time"),
        6: ("Marathon", "time"),
        7: ("Longest run", "distance"),
    }
    # activityType is None for these — steps/streak records, not tied to a
    # specific sport.
    other_type_info = {
        12: ("Most steps in a day", "count"),
        13: ("Most steps in a week", "count"),
        14: ("Most steps in a month", "count"),
        15: ("Longest goal streak", "days"),
        16: ("Current goal streak", "days"),
    }
    try:
        success, records = call_and_display(
            api.get_personal_record,
            method_name="get_personal_record",
            api_call_desc="api.get_personal_record()",
        )
        if not success or not records:
            return

        entries = records if isinstance(records, list) else [records]
        if not entries:
            print(translate("error.no_records"))
            return

        print(translate("demo.personal_records"))
        for i, entry in enumerate(entries):
            type_id = entry.get("typeId")
            activity_type = entry.get("activityType")
            value = entry.get("value")
            if activity_type == "running":
                info = running_type_info.get(type_id)
            elif activity_type is None:
                info = other_type_info.get(type_id)
            else:
                info = None

            if info is not None and isinstance(value, int | float):
                label, kind = info
                formatted = _RECORD_FORMATTERS[kind](value)
                print(
                    translate(
                        "ui.record_row",
                        index=i,
                        label=label,
                        formatted=formatted,
                        type_id=type_id,
                        value=value,
                    )
                )
            else:
                print(
                    translate(
                        "ui.unconfirmed_record",
                        index=i,
                        type_id=type_id,
                        activity_type=repr(activity_type),
                        value=value,
                    )
                )

        choice = input(translate("ui.source_activity")).strip()
        if not choice:
            return

        try:
            idx = int(choice)
            if not (0 <= idx < len(entries)):
                print(translate("error.invalid_index"))
                return
        except ValueError:
            print(translate("error.invalid_index"))
            return

        activity_id = entries[idx].get("activityId") or entries[idx].get(
            "activityIdInt"
        )
        if not activity_id:
            print(translate("error.no_activity_id"))
            return

        call_and_display(
            api.get_activity,
            str(activity_id),
            method_name="get_activity",
            api_call_desc=f"api.get_activity('{activity_id}')",
        )
    except Exception as e:
        print(translate("error.record_error", error=e))


def set_activity_name_data(api: Garmin) -> None:
    """Set activity name."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            print(
                translate(
                    "ui.current_activity_name", name=activities[0]["activityName"]
                )
            )
            new_name = input(translate("prompt.new_activity_name")).strip()

            if new_name.lower() == "q":
                print(translate("ui.rename_cancelled"))
                return

            if new_name:
                call_and_display(
                    api.set_activity_name,
                    activity_id,
                    new_name,
                    method_name="set_activity_name",
                    api_call_desc=f"api.set_activity_name({activity_id}, '{new_name}')",
                )
                print(translate("result.activity_name_updated"))
            else:
                print(translate("ui.no_name"))
        else:
            print(translate("ui.no_activity_error"))
    except Exception as e:
        print(translate("error.activity_name_error", error=e))


def set_activity_type_data(api: Garmin) -> None:
    """Set activity type."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            activity_types = api.get_activity_types()

            # Show available types
            print(translate("ui.limit_activity_types"))
            for i, activity_type in enumerate(activity_types[:10]):  # Show first 10
                print(
                    translate(
                        "ui.activity_type_row",
                        index=i,
                        type_key=activity_type.get("typeKey", "Unknown"),
                        display=activity_type.get("display", "No description"),
                    )
                )

            try:
                print(
                    translate(
                        "ui.current_activity_type",
                        name=activities[0]["activityName"],
                        activity_type=activities[0]["activityType"]["typeKey"],
                    )
                )
                type_index = input(translate("prompt.activity_type")).strip()

                if type_index.lower() == "q":
                    print(translate("ui.type_cancelled"))
                    return

                type_index = int(type_index)
                if 0 <= type_index < len(activity_types):
                    selected_type = activity_types[type_index]
                    type_id = selected_type["typeId"]
                    type_key = selected_type["typeKey"]
                    parent_type_id = selected_type.get(
                        "parentTypeId", selected_type["typeId"]
                    )

                    call_and_display(
                        api.set_activity_type,
                        activity_id,
                        type_id,
                        type_key,
                        parent_type_id,
                        method_name="set_activity_type",
                        api_call_desc=f"api.set_activity_type({activity_id}, {type_id}, '{type_key}', {parent_type_id})",
                    )
                    print(translate("result.activity_type_updated"))
                else:
                    print(translate("error.invalid_index"))
            except ValueError:
                print(translate("error.invalid_input"))
        else:
            print(translate("ui.no_activity_error"))
    except Exception as e:
        print(translate("error.activity_type_error", error=e))


def set_activity_description_data(api: Garmin) -> None:
    """Set the description of the most recent activity."""
    try:
        activities = api.get_activities(0, 1)
        if not activities:
            print(translate("ui.no_activity_error"))
            return

        activity = activities[0]
        activity_id = activity["activityId"]
        current = activity.get("description") or "(none)"
        print(
            translate(
                "ui.activity_summary",
                name=activity.get("activityName"),
                activity_id=activity_id,
            )
        )
        print(translate("ui.current_description", description=current))

        new_desc = input(translate("prompt.new_description")).strip()
        if new_desc.lower() == "q":
            print(translate("error.cancelled"))
            return

        call_and_display(
            api.set_activity_description,
            activity_id,
            new_desc,
            method_name="set_activity_description",
            api_call_desc=f"api.set_activity_description({activity_id}, '{new_desc}')",
        )
        print(translate("result.description_updated"))
    except Exception as e:
        print(translate("error.description_error", error=e))


def set_activity_exercise_sets_data(api: Garmin) -> None:
    """Replace exercise sets on a strength-training activity.

    Demonstrates the round-trip: fetch the current sets, then re-submit the
    exact same payload (replace-all semantics). Re-submitting unchanged data
    is a safe no-op that proves the endpoint without altering the activity.
    """
    try:
        activities = api.get_activities(
            0, 1, activitytype="fitness_equipment", activitysubtype="strength_training"
        )
        activity_list = (
            activities.get("activityList", [])
            if isinstance(activities, dict)
            else activities
        )
        strength_activity = activity_list[0] if activity_list else None

        if not strength_activity:
            print(translate("demo.no_strength"))
            return

        activity_id = strength_activity["activityId"]
        current = api.get_activity_exercise_sets(activity_id)
        sets = current.get("exerciseSets") if isinstance(current, dict) else None
        if not sets:
            print(translate("ui.no_sets", activity_id=activity_id))
            return

        print(translate("ui.exercise_count", activity_id=activity_id, count=len(sets)))
        print(translate("ui.replace_sets"))
        confirm = input(translate("prompt.resubmit_sets")).strip().lower()
        if confirm != "yes":
            print(translate("error.cancelled"))
            return

        call_and_display(
            api.set_activity_exercise_sets,
            activity_id,
            {"exerciseSets": sets},
            method_name="set_activity_exercise_sets",
            api_call_desc=(
                f"api.set_activity_exercise_sets({activity_id}, "
                f"{{'exerciseSets': <{len(sets)} sets>}})"
            ),
        )
        print(translate("result.exercise_sets_submitted"))
    except Exception as e:
        print(translate("error.exercise_sets_error", error=e))


def create_manual_activity_data(api: Garmin) -> None:
    """Create manual activity."""
    try:
        print(translate("demo.manual_activity"))
        print(translate("demo.activity_details"))

        activity_name = (
            input(translate("prompt.activity_name")).strip() or "Manual Activity"
        )
        type_key = input(translate("prompt.activity_type_key")).strip() or "running"
        duration_min = input(translate("prompt.duration")).strip() or "60"
        distance_km = input(translate("prompt.distance")).strip() or "5"
        timezone = input(translate("prompt.timezone")).strip() or "UTC"

        try:
            duration_min = float(duration_min)
            distance_km = float(distance_km)

            # Use the current time as start time
            import datetime

            start_datetime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.00")

            call_and_display(
                api.create_manual_activity,
                start_datetime=start_datetime,
                time_zone=timezone,
                type_key=type_key,
                distance_km=distance_km,
                duration_min=duration_min,
                activity_name=activity_name,
                method_name="create_manual_activity",
                api_call_desc=f"api.create_manual_activity(start_datetime='{start_datetime}', time_zone='{timezone}', type_key='{type_key}', distance_km={distance_km}, duration_min={duration_min}, activity_name='{activity_name}')",
            )
            print(translate("result.manual_created"))
        except ValueError:
            print(translate("error.invalid_numeric"))
    except Exception as e:
        print(translate("error.manual_error", error=e))


def delete_activity_data(api: Garmin) -> None:
    """Delete activity."""
    try:
        activities = api.get_activities(0, 5)
        if activities:
            print(translate("ui.recent_activities"))
            for i, activity in enumerate(activities):
                activity_name = activity.get("activityName", "Unnamed")
                activity_id = activity.get("activityId")
                start_time = activity.get("startTimeLocal", "Unknown time")
                print(
                    translate(
                        "ui.activity_item",
                        index=i,
                        name=activity_name,
                        activity_id=activity_id,
                        start_time=start_time,
                    )
                )

            try:
                activity_index = input(translate("prompt.delete_activity")).strip()

                if activity_index.lower() == "q":
                    print(translate("ui.delete_cancelled"))
                    return
                activity_index = int(activity_index)
                if 0 <= activity_index < len(activities):
                    activity_id = activities[activity_index]["activityId"]
                    activity_name = activities[activity_index].get(
                        "activityName", "Unnamed"
                    )

                    confirm = input(
                        translate("prompt.delete_activity_confirm", name=activity_name)
                    ).lower()
                    if confirm == "yes":
                        call_and_display(
                            api.delete_activity,
                            activity_id,
                            method_name="delete_activity",
                            api_call_desc=f"api.delete_activity({activity_id})",
                        )
                        print(translate("result.activity_deleted"))
                    else:
                        print(translate("ui.delete_cancelled"))
                else:
                    print(translate("error.invalid_index"))
            except ValueError:
                print(translate("error.invalid_input"))
        else:
            print(translate("ui.no_activity_error"))
    except Exception as e:
        print(translate("error.activity_delete_error", error=e))


def delete_blood_pressure_data(api: Garmin) -> None:
    """Delete blood pressure entry."""
    try:
        # Get recent blood pressure entries
        bp_data = api.get_blood_pressure(
            config.week_start.isoformat(), config.today.isoformat()
        )
        entry_list = []

        # Parse the actual blood pressure data structure
        if bp_data and bp_data.get("measurementSummaries"):
            for summary in bp_data["measurementSummaries"]:
                if summary.get("measurements"):
                    for measurement in summary["measurements"]:
                        # Use 'version' as the identifier (this is what Garmin uses)
                        entry_id = measurement.get("version")
                        systolic = measurement.get("systolic")
                        diastolic = measurement.get("diastolic")
                        pulse = measurement.get("pulse")
                        timestamp = measurement.get("measurementTimestampLocal")
                        notes = measurement.get("notes", "")

                        # Extract date for deletion API (format: YYYY-MM-DD)
                        measurement_date = None
                        if timestamp:
                            try:
                                measurement_date = timestamp.split("T")[
                                    0
                                ]  # Get just the date part
                            except Exception:
                                measurement_date = summary.get(
                                    "startDate"
                                )  # Fallback to summary date
                        else:
                            measurement_date = summary.get(
                                "startDate"
                            )  # Fallback to summary date

                        if entry_id and systolic and diastolic and measurement_date:
                            # Format display text with more details
                            display_parts = [f"{systolic}/{diastolic}"]
                            if pulse:
                                display_parts.append(f"pulse {pulse}")
                            if timestamp:
                                display_parts.append(f"at {timestamp}")
                            if notes:
                                display_parts.append(f"({notes})")

                            display_text = " ".join(display_parts)
                            # Store both entry_id and measurement_date for deletion
                            entry_list.append(
                                (entry_id, display_text, measurement_date)
                            )

        if entry_list:
            print(translate("ui.bp_entries", count=len(entry_list)))
            print("-" * 70)
            for i, (entry_id, display_text, _measurement_date) in enumerate(entry_list):
                print(
                    translate(
                        "ui.indexed_workout",
                        index=i,
                        name=display_text,
                        workout_id=entry_id,
                    )
                )

            try:
                entry_index = input(translate("prompt.delete_entry")).strip()

                if entry_index.lower() == "q":
                    print(translate("ui.entry_cancelled"))
                    return

                entry_index = int(entry_index)
                if 0 <= entry_index < len(entry_list):
                    entry_id, display_text, measurement_date = entry_list[entry_index]
                    confirm = input(
                        translate("prompt.delete_entry_confirm", entry=display_text)
                    ).lower()
                    if confirm == "yes":
                        call_and_display(
                            api.delete_blood_pressure,
                            entry_id,
                            measurement_date,
                            method_name="delete_blood_pressure",
                            api_call_desc=f"api.delete_blood_pressure('{entry_id}', '{measurement_date}')",
                        )
                        print(translate("result.bp_deleted"))
                    else:
                        print(translate("ui.delete_cancelled"))
                else:
                    print(translate("error.invalid_index"))
            except ValueError:
                print(translate("error.invalid_input"))
        else:
            print(translate("error.no_blood_pressure"))
            print(translate("ui.add_test_measurement"))

    except Exception as e:
        print(translate("error.blood_pressure_delete_error", error=e))


def query_garmin_graphql_data(api: Garmin) -> None:
    """Execute GraphQL query with a menu of available queries."""
    try:
        print(translate("demo.graphql_queries"))
        print(translate("ui.graphql_activities"))
        print(translate("ui.graphql_health"))
        print(translate("ui.graphql_weight"))
        print(translate("ui.graphql_bp"))
        print(translate("ui.graphql_sleep"))
        print(translate("ui.graphql_hrv"))
        print(translate("ui.graphql_summary"))
        print(translate("ui.graphql_readiness"))
        print(translate("ui.graphql_status"))
        print(translate("ui.graphql_activity_stats"))
        print(translate("ui.graphql_vo2"))
        print(translate("ui.graphql_endurance"))
        print(translate("ui.graphql_goals"))
        print(translate("ui.graphql_stress"))
        print(translate("ui.graphql_badges"))
        print(translate("ui.graphql_adhoc"))
        print(translate("demo.custom_query"))

        choice = input(translate("prompt.query_choice")).strip()

        # Use today's date and date range for queries that need them
        today = config.today.isoformat()
        week_start = config.week_start.isoformat()
        start_datetime = f"{today}T00:00:00.00"
        end_datetime = f"{today}T23:59:59.999"

        if choice == "1":
            query = f'query{{activitiesScalar(displayName:"{api.display_name}", startTimestampLocal:"{start_datetime}", endTimestampLocal:"{end_datetime}", limit:10)}}'
        elif choice == "2":
            query = f'query{{healthSnapshotScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "3":
            query = (
                f'query{{weightScalar(startDate:"{week_start}", endDate:"{today}")}}'
            )
        elif choice == "4":
            query = f'query{{bloodPressureScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "5":
            query = f'query{{sleepSummariesScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "6":
            query = f'query{{heartRateVariabilityScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "7":
            query = f'query{{userDailySummaryV2Scalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "8":
            query = f'query{{trainingReadinessRangeScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "9":
            query = f'query{{trainingStatusDailyScalar(calendarDate:"{today}")}}'
        elif choice == "10":
            query = f'query{{activityStatsScalar(aggregation:"daily", startDate:"{week_start}", endDate:"{today}", metrics:["duration", "distance"], groupByParentActivityType:true, standardizedUnits:true)}}'
        elif choice == "11":
            query = (
                f'query{{vo2MaxScalar(startDate:"{week_start}", endDate:"{today}")}}'
            )
        elif choice == "12":
            query = f'query{{enduranceScoreScalar(startDate:"{week_start}", endDate:"{today}", aggregation:"weekly")}}'
        elif choice == "13":
            query = "query{userGoalsScalar}"
        elif choice == "14":
            query = f'query{{epochChartScalar(date:"{today}", include:["stress"])}}'
        elif choice == "15":
            query = "query{badgeChallengesScalar}"
        elif choice == "16":
            query = "query{adhocChallengesScalar}"
        elif choice.lower() == "c":
            print(translate("prompt.custom_query"))
            print(translate("demo.graphql_example"))
            query = input(translate("prompt.query")).strip()
        else:
            print(translate("error.invalid_choice"))
            return

        if query:
            # GraphQL API expects a dictionary with the query as a string value
            graphql_payload = {"query": query}
            call_and_display(
                api.query_garmin_graphql,
                graphql_payload,
                method_name="query_garmin_graphql",
                api_call_desc=f"api.query_garmin_graphql({graphql_payload})",
            )
        else:
            print(translate("error.no_query"))
    except Exception as e:
        print(translate("error.graphql_error", error=e))


def get_virtual_challenges_data(api: Garmin) -> None:
    """Get virtual challenges data with centralized error handling."""
    print(translate("ui.virtual_loading"))

    # Try in-progress virtual challenges - this endpoint often returns 400 for accounts
    # that don't have virtual challenges enabled, so handle it quietly
    try:
        challenges = api.get_inprogress_virtual_challenges(
            config.start_badge, config.default_limit
        )
        if challenges:
            print(translate("result.virtual_challenges"))
            call_and_display(
                api.get_inprogress_virtual_challenges,
                config.start_badge,
                config.default_limit,
                method_name="get_inprogress_virtual_challenges",
                api_call_desc=f"api.get_inprogress_virtual_challenges({config.start_badge}, {config.default_limit})",
            )
            return
        print(translate("demo.no_virtual_challenges"))
        return
    except GarminConnectConnectionError as e:
        # Handle the common 400 error case quietly - this is expected for many accounts
        error_str = str(e)
        if "400" in error_str and (
            "Bad Request" in error_str or "API client error" in error_str
        ):
            print(translate("error.virtual_unavailable"))
        else:
            # For unexpected connection errors, show them
            print(translate("ui.connection_virtual", error=error_str))
    except Exception as e:
        print(translate("ui.unexpected_virtual", error=e))

    # Since virtual challenges failed or returned no data, suggest alternatives
    print(translate("ui.challenge_alternatives"))
    print(translate("ui.badge_menu"))
    print(translate("ui.available_badge_menu"))
    print(translate("ui.adhoc_menu"))


def add_hydration_data_entry(api: Garmin) -> None:
    """Add hydration data entry."""
    try:
        import datetime

        value_in_ml = 240
        raw_date = config.today
        cdate = str(raw_date)
        raw_ts = datetime.datetime.now()
        timestamp = datetime.datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

        call_and_display(
            api.add_hydration_data,
            value_in_ml=value_in_ml,
            cdate=cdate,
            timestamp=timestamp,
            method_name="add_hydration_data",
            api_call_desc=f"api.add_hydration_data(value_in_ml={value_in_ml}, cdate='{cdate}', timestamp='{timestamp}')",
        )
        print(translate("demo.hydration_added"))
    except Exception as e:
        print(translate("error.hydration_error", error=e))


def _parse_csv_enums(raw: str) -> list[str] | None:
    raw = raw.strip()
    if not raw:
        return None
    return [part.strip() for part in raw.split(",") if part.strip()]


def update_menstrual_daily_log_entry(api: Garmin) -> None:
    """Write a menstrual daily-log snapshot."""
    try:
        print(translate("demo.menstrual_notes"))
        print(translate("demo.clear_notes"))
        calendar_date = (
            input(translate("prompt.date", date=config.today.isoformat())).strip()
            or config.today.isoformat()
        )
        symptoms = _parse_csv_enums(input(translate("prompt.symptoms")))
        moods = _parse_csv_enums(input(translate("prompt.moods")))
        flow = input(translate("prompt.flow")).strip() or None
        discharge = _parse_csv_enums(input(translate("prompt.discharge")))
        sex_drive = input(translate("prompt.sex_drive")).strip() or None
        sexual_activity = input(translate("prompt.sexual_activity")).strip() or None
        notes_raw = input(translate("prompt.notes"))
        if notes_raw == "":
            notes = None
        elif notes_raw.strip() == "-":
            notes = ""
        else:
            notes = notes_raw
        ovulation_raw = input(translate("prompt.ovulation")).strip().lower()
        ovulation_day = True if ovulation_raw == "y" else None

        call_and_display(
            api.update_menstrual_daily_log,
            calendar_date,
            symptoms=symptoms,
            moods=moods,
            flow=flow,
            discharge=discharge,
            sex_drive=sex_drive,
            sexual_activity=sexual_activity,
            notes=notes,
            ovulation_day=ovulation_day,
            method_name="update_menstrual_daily_log",
            api_call_desc=(f"api.update_menstrual_daily_log('{calendar_date}', ...)"),
        )
    except Exception as e:
        print(translate("error.menstrual_log_error", error=e))


def update_menstrual_calendar_entry(api: Garmin) -> None:
    """Replace period dates on the menstrual calendar."""
    try:
        print(translate("demo.period_warning"))
        print(translate("demo.period_groups"))
        startdate = input(translate("prompt.start_date")).strip()
        enddate = input(translate("prompt.end_date")).strip()
        raw_groups = input(translate("prompt.period_groups")).strip()
        cycle_dates_lists = [
            [day.strip() for day in group.split(",") if day.strip()]
            for group in raw_groups.split(";")
            if group.strip()
        ]
        call_and_display(
            api.update_menstrual_calendar,
            startdate,
            enddate,
            cycle_dates_lists,
            method_name="update_menstrual_calendar",
            api_call_desc=(
                "api.update_menstrual_calendar("
                f"'{startdate}', '{enddate}', {cycle_dates_lists})"
            ),
        )
    except Exception as e:
        print(translate("error.menstrual_calendar_error", error=e))


def init_menstrual_cycle_setup_entry(api: Garmin) -> None:
    """Initialize menstrual cycle tracking (first-run only)."""
    try:
        period_start_date = input(translate("prompt.period_start")).strip()
        period_length = int(input(translate("prompt.period_length")).strip())
        cycle_length = int(input(translate("prompt.cycle_length")).strip())
        call_and_display(
            api.init_menstrual_cycle_setup,
            period_start_date,
            period_length,
            cycle_length,
            method_name="init_menstrual_cycle_setup",
            api_call_desc=(
                "api.init_menstrual_cycle_setup("
                f"'{period_start_date}', {period_length}, {cycle_length})"
            ),
        )
    except Exception as e:
        print(translate("error.cycle_init_error", error=e))


def confirm_menstrual_period_start_entry(api: Garmin) -> None:
    """Confirm a period start date (may confirm a prediction)."""
    try:
        period_start_date = input(translate("prompt.period_start")).strip()
        period_length = int(input(translate("prompt.period_length")).strip())
        cycle_length = int(input(translate("prompt.cycle_length")).strip())
        predicted = input(translate("prompt.predicted_cycle")).strip().lower() == "y"
        call_and_display(
            api.confirm_menstrual_period_start,
            period_start_date,
            period_length,
            cycle_length,
            predicted_cycle=predicted,
            method_name="confirm_menstrual_period_start",
            api_call_desc=(
                "api.confirm_menstrual_period_start("
                f"'{period_start_date}', {period_length}, {cycle_length})"
            ),
        )
    except Exception as e:
        print(translate("error.period_confirm_error", error=e))


def update_menstrual_settings_entry(api: Garmin) -> None:
    """PUT menstrual tracking settings."""
    try:
        print(translate("demo.settings_json"))
        raw = input(translate("prompt.settings_json")).strip()
        settings = json.loads(raw)
        call_and_display(
            api.update_menstrual_settings,
            settings,
            method_name="update_menstrual_settings",
            api_call_desc="api.update_menstrual_settings({...})",
        )
    except Exception as e:
        print(translate("error.menstrual_settings_error", error=e))


def set_blood_pressure_data(api: Garmin) -> None:
    """Set blood pressure (and pulse) data."""
    try:
        print(translate("demo.blood_pressure"))
        print(translate("demo.blood_pressure_values"))

        # Get systolic pressure
        systolic_input = input(translate("prompt.systolic")).strip()
        systolic = int(systolic_input) if systolic_input else 120

        # Get diastolic pressure
        diastolic_input = input(translate("prompt.diastolic")).strip()
        diastolic = int(diastolic_input) if diastolic_input else 80

        # Get pulse (optional - Garmin Connect's own UI allows omitting it)
        pulse_input = input(translate("prompt.pulse")).strip()
        pulse = int(pulse_input) if pulse_input else None

        # Get notes (optional)
        notes = input(translate("prompt.notes_optional")).strip() or "Added via demo.py"

        # Validate ranges (must match Garmin.set_blood_pressure's own checks,
        # so a value the demo accepts never gets rejected by the API call)
        if not (70 <= systolic <= 260):
            print(translate("ui.bp_range"))
            return
        if not (40 <= diastolic <= 150):
            print(translate("ui.bp_diastolic_range"))
            return
        if pulse is not None and not (20 <= pulse <= 250):
            print(translate("ui.pulse_range"))
            return

        pulse_desc = f"pulse {pulse} bpm" if pulse is not None else "no pulse"
        print(
            translate(
                "ui.recording_bp",
                systolic=systolic,
                diastolic=diastolic,
                pulse=pulse_desc,
            )
        )

        call_and_display(
            api.set_blood_pressure,
            systolic,
            diastolic,
            pulse,
            notes=notes,
            method_name="set_blood_pressure",
            api_call_desc=f"api.set_blood_pressure({systolic}, {diastolic}, {pulse}, notes='{notes}')",
        )
        print(translate("result.bp_set"))

    except ValueError:
        print(translate("ui.numeric_values"))
    except Exception as e:
        print(translate("error.blood_pressure_error", error=e))


def track_gear_usage_data(api: Garmin) -> None:
    """Calculate total time of use of a piece of gear by going through all activities where said gear has been used."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear_list = api.get_gear(user_profile_number)
            # call_and_display(api.get_gear, user_profile_number, method_name="get_gear", api_call_desc=f"api.get_gear({user_profile_number})")
            if gear_list and isinstance(gear_list, list):
                first_gear = gear_list[0]
                gear_uuid = first_gear.get("uuid")
                gear_name = first_gear.get("displayName", "Unknown")
                print(translate("ui.tracking_gear", name=gear_name, uuid=gear_uuid))
                activityList = api.get_gear_activities(gear_uuid)
                if len(activityList) == 0:
                    print(translate("error.no_activities_gear"))
                else:
                    print(translate("demo.activity_count", count=len(activityList)))

                D = 0
                for a in activityList:
                    print(
                        translate(
                            "demo.activity_gear_row",
                            start_time=a["startTimeLocal"],
                            activity_name=(
                                " | " + a["activityName"] if a["activityName"] else ""
                            ),
                        )
                    )
                    print(
                        translate(
                            "demo.activity_gear_duration",
                            duration=format_timedelta(
                                datetime.timedelta(seconds=a["duration"])
                            ),
                        )
                    )
                    D += a["duration"]
                print("")
                print(
                    translate(
                        "demo.total_duration",
                        duration=format_timedelta(datetime.timedelta(seconds=D)),
                    )
                )
                print("")
            else:
                print(translate("error.no_gear_user"))
        else:
            print(translate("error.no_profile"))
    except Exception as e:
        print(translate("ui.profile_action_error", error=e))


def execute_api_call(api: Garmin, key: str) -> None:
    """Execute an API call based on the key."""
    if not api:
        print(translate("demo.api_unavailable"))
        return

    try:
        # Map of keys to API methods - this can be extended as needed
        api_methods = {
            # User & Profile
            "get_full_name": lambda: call_and_display(
                api.get_full_name,
                method_name="get_full_name",
                api_call_desc="api.get_full_name()",
            ),
            "get_unit_system": lambda: call_and_display(
                api.get_unit_system,
                method_name="get_unit_system",
                api_call_desc="api.get_unit_system()",
            ),
            "get_user_profile": lambda: call_and_display(
                api.get_user_profile,
                method_name="get_user_profile",
                api_call_desc="api.get_user_profile()",
            ),
            "get_userprofile_settings": lambda: call_and_display(
                api.get_userprofile_settings,
                method_name="get_userprofile_settings",
                api_call_desc="api.get_userprofile_settings()",
            ),
            # Daily Health & Activity
            "get_stats": lambda: call_and_display(
                api.get_stats,
                config.today.isoformat(),
                method_name="get_stats",
                api_call_desc=f"api.get_stats('{config.today.isoformat()}')",
            ),
            "get_user_summary": lambda: call_and_display(
                api.get_user_summary,
                config.today.isoformat(),
                method_name="get_user_summary",
                api_call_desc=f"api.get_user_summary('{config.today.isoformat()}')",
            ),
            "get_stats_and_body": lambda: call_and_display(
                api.get_stats_and_body,
                config.today.isoformat(),
                method_name="get_stats_and_body",
                api_call_desc=f"api.get_stats_and_body('{config.today.isoformat()}')",
            ),
            "get_steps_data": lambda: call_and_display(
                api.get_steps_data,
                config.today.isoformat(),
                method_name="get_steps_data",
                api_call_desc=f"api.get_steps_data('{config.today.isoformat()}')",
            ),
            "get_heart_rates": lambda: call_and_display(
                api.get_heart_rates,
                config.today.isoformat(),
                method_name="get_heart_rates",
                api_call_desc=f"api.get_heart_rates('{config.today.isoformat()}')",
            ),
            "get_rhr_daily": lambda: call_and_display(
                api.get_rhr_daily,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_rhr_daily",
                api_call_desc=f"api.get_rhr_daily('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_sleep_daily": lambda: call_and_display(
                api.get_sleep_daily,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_sleep_daily",
                api_call_desc=f"api.get_sleep_daily('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_all_day_stress": lambda: call_and_display(
                api.get_all_day_stress,
                config.today.isoformat(),
                method_name="get_all_day_stress",
                api_call_desc=f"api.get_all_day_stress('{config.today.isoformat()}')",
            ),
            "get_calories_daily": lambda: call_and_display(
                api.get_calories_daily,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_calories_daily",
                api_call_desc=f"api.get_calories_daily('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            # Advanced Health Metrics
            "get_running_tolerance": lambda: call_and_display(
                api.get_running_tolerance,
                config.week_start.isoformat(),
                config.today.isoformat(),
            ),
            "get_training_readiness": lambda: call_and_display(
                api.get_training_readiness,
                config.today.isoformat(),
                method_name="get_training_readiness",
                api_call_desc=f"api.get_training_readiness('{config.today.isoformat()}')",
            ),
            "get_morning_training_readiness": lambda: call_and_display(
                api.get_morning_training_readiness,
                config.today.isoformat(),
                method_name="get_morning_training_readiness",
                api_call_desc=f"api.get_morning_training_readiness('{config.today.isoformat()}')",
            ),
            "get_training_status": lambda: call_and_display(
                api.get_training_status,
                config.today.isoformat(),
                method_name="get_training_status",
                api_call_desc=f"api.get_training_status('{config.today.isoformat()}')",
            ),
            "get_respiration_data": lambda: call_and_display(
                api.get_respiration_data,
                config.today.isoformat(),
                method_name="get_respiration_data",
                api_call_desc=f"api.get_respiration_data('{config.today.isoformat()}')",
            ),
            "get_spo2_data": lambda: call_and_display(
                api.get_spo2_data,
                config.today.isoformat(),
                method_name="get_spo2_data",
                api_call_desc=f"api.get_spo2_data('{config.today.isoformat()}')",
            ),
            "get_max_metrics_range": lambda: call_and_display(
                api.get_max_metrics_range,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_max_metrics_range",
                api_call_desc=f"api.get_max_metrics_range('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_hrv_data_range": lambda: call_and_display(
                api.get_hrv_data_range,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_hrv_data_range",
                api_call_desc=f"api.get_hrv_data_range('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_fitnessage_data": lambda: call_and_display(
                api.get_fitnessage_data,
                config.today.isoformat(),
                method_name="get_fitnessage_data",
                api_call_desc=f"api.get_fitnessage_data('{config.today.isoformat()}')",
            ),
            "get_stress_data": lambda: call_and_display(
                api.get_stress_data,
                config.today.isoformat(),
                method_name="get_stress_data",
                api_call_desc=f"api.get_stress_data('{config.today.isoformat()}')",
            ),
            "get_lactate_threshold": lambda: get_lactate_threshold_data(api),
            "get_functional_threshold_power_range": lambda: (
                get_functional_threshold_power_range_data(api)
            ),
            "get_heart_rate_zones": lambda: call_and_display(
                api.get_heart_rate_zones,
                method_name="get_heart_rate_zones",
                api_call_desc="api.get_heart_rate_zones()",
            ),
            "get_power_zones": lambda: call_and_display(
                api.get_power_zones,
                method_name="get_power_zones",
                api_call_desc="api.get_power_zones()",
            ),
            "get_power_zones_for_sport": lambda: call_and_display(
                api.get_power_zones_for_sport,
                "CYCLING",
                method_name="get_power_zones_for_sport",
                api_call_desc="api.get_power_zones_for_sport('CYCLING')",
            ),
            "get_intensity_minutes_data": lambda: call_and_display(
                api.get_intensity_minutes_data,
                config.today.isoformat(),
                method_name="get_intensity_minutes_data",
                api_call_desc=f"api.get_intensity_minutes_data('{config.today.isoformat()}')",
            ),
            "get_lifestyle_logging_data": lambda: call_and_display(
                api.get_lifestyle_logging_data,
                config.today.isoformat(),
                method_name="get_lifestyle_logging_data",
                api_call_desc=f"api.get_lifestyle_logging_data('{config.today.isoformat()}')",
            ),
            # Historical Data & Trends
            "get_daily_steps": lambda: call_and_display(
                api.get_daily_steps,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_daily_steps",
                api_call_desc=f"api.get_daily_steps('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_body_battery": lambda: call_and_display(
                api.get_body_battery,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_body_battery",
                api_call_desc=f"api.get_body_battery('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_floors": lambda: call_and_display(
                api.get_floors,
                config.week_start.isoformat(),
                method_name="get_floors",
                api_call_desc=f"api.get_floors('{config.week_start.isoformat()}')",
            ),
            "get_blood_pressure": lambda: call_and_display(
                api.get_blood_pressure,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_blood_pressure",
                api_call_desc=f"api.get_blood_pressure('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_progress_summary_between_dates": lambda: call_and_display(
                api.get_progress_summary_between_dates,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_progress_summary_between_dates",
                api_call_desc=f"api.get_progress_summary_between_dates('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_body_battery_events": lambda: call_and_display(
                api.get_body_battery_events,
                config.week_start.isoformat(),
                method_name="get_body_battery_events",
                api_call_desc=f"api.get_body_battery_events('{config.week_start.isoformat()}')",
            ),
            "get_weekly_steps": lambda: call_and_display(
                api.get_weekly_steps,
                config.today.isoformat(),
                52,
                method_name="get_weekly_steps",
                api_call_desc=f"api.get_weekly_steps('{config.today.isoformat()}', 52)",
            ),
            "get_weekly_stress": lambda: call_and_display(
                api.get_weekly_stress,
                config.today.isoformat(),
                52,
                method_name="get_weekly_stress",
                api_call_desc=f"api.get_weekly_stress('{config.today.isoformat()}', 52)",
            ),
            "get_weekly_intensity_minutes": lambda: call_and_display(
                api.get_weekly_intensity_minutes,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_weekly_intensity_minutes",
                api_call_desc=f"api.get_weekly_intensity_minutes('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            # Activities & Workouts
            "get_activities": lambda: call_and_display(
                api.get_activities,
                config.start,
                config.default_limit,
                method_name="get_activities",
                api_call_desc=f"api.get_activities({config.start}, {config.default_limit})",
            ),
            "get_activities_filtered": lambda: get_activities_filtered_data(api),
            "get_next_scheduled_workout": lambda: get_next_scheduled_workout_data(api),
            "get_last_activity": lambda: call_and_display(
                api.get_last_activity,
                method_name="get_last_activity",
                api_call_desc="api.get_last_activity()",
            ),
            "get_activities_fordate": lambda: call_and_display(
                api.get_activities_fordate,
                config.today.isoformat(),
                method_name="get_activities_fordate",
                api_call_desc=f"api.get_activities_fordate('{config.today.isoformat()}')",
            ),
            "get_activity_types": lambda: call_and_display(
                api.get_activity_types,
                method_name="get_activity_types",
                api_call_desc="api.get_activity_types()",
            ),
            "get_workouts": lambda: call_and_display(
                api.get_workouts,
                method_name="get_workouts",
                api_call_desc="api.get_workouts()",
            ),
            "get_training_plan_by_id": lambda: get_training_plan_by_id_data(api),
            "get_training_plans": lambda: call_and_display(
                api.get_training_plans,
                method_name="get_training_plans",
                api_call_desc="api.get_training_plans()",
            ),
            # Golf
            "get_golf_summary": lambda: call_and_display(
                api.get_golf_summary,
                method_name="get_golf_summary",
                api_call_desc="api.get_golf_summary()",
            ),
            "get_golf_scorecard": lambda: get_golf_scorecard_data(api),
            "get_golf_shot_data": lambda: get_golf_shot_data_entry(api),
            "get_golf_club_stats": lambda: call_and_display(
                api.get_golf_club_stats,
                method_name="get_golf_club_stats",
                api_call_desc="api.get_golf_club_stats()",
            ),
            "get_golf_user_stats": lambda: call_and_display(
                api.get_golf_user_stats,
                method_name="get_golf_user_stats",
                api_call_desc="api.get_golf_user_stats()",
            ),
            "upload_activity": lambda: upload_activity_file(api),
            "import_activity": lambda: import_activity_file(api),
            "download_activities": lambda: download_activities_by_date(api),
            "get_activity_splits": lambda: get_activity_splits_data(api),
            "get_activity_typed_splits": lambda: get_activity_typed_splits_data(api),
            "get_activity_split_summaries": lambda: get_activity_split_summaries_data(
                api
            ),
            "get_activity_weather": lambda: get_activity_weather_data(api),
            "get_activity_hr_in_timezones": lambda: get_activity_hr_timezones_data(api),
            "get_activity_power_in_timezones": lambda: (
                get_activity_power_timezones_data(api)
            ),
            "get_cycling_ftp": lambda: get_cycling_ftp_data(api),
            "get_activity_details": lambda: get_activity_details_data(api),
            "get_activity_gear": lambda: get_activity_gear_data(api),
            "get_activity": lambda: get_single_activity_data(api),
            "get_activity_exercise_sets": lambda: get_activity_exercise_sets_data(api),
            "get_workout_by_id": lambda: get_workout_by_id_data(api),
            "download_workout": lambda: download_workout_data(api),
            "upload_workout": lambda: upload_workout_data(api),
            "upload_running_workout": lambda: upload_running_workout_data(api),
            "upload_cycling_workout": lambda: upload_cycling_workout_data(api),
            "upload_swimming_workout": lambda: upload_swimming_workout_data(api),
            "upload_walking_workout": lambda: upload_walking_workout_data(api),
            "upload_hiking_workout": lambda: upload_hiking_workout_data(api),
            "upload_strength_workout": lambda: upload_strength_workout_data(api),
            "search_exercise_catalog": lambda: search_exercise_catalog_data(api),
            "get_scheduled_workout_by_id": lambda: get_scheduled_workout_by_id_data(
                api
            ),
            "get_scheduled_workouts": lambda: get_scheduled_workouts(api),
            "scheduled_workout": lambda: schedule_workout_data(api),
            "delete_workout": lambda: delete_workout_data(api),
            "update_workout": lambda: update_workout_data(api),
            "push_workout_to_device": lambda: push_workout_to_device_data(api),
            "unschedule_workout": lambda: unschedule_workout_data(api),
            "count_activities": lambda: call_and_display(
                api.count_activities,
                method_name="count_activities",
                api_call_desc="api.count_activities()",
            ),
            # Body Composition & Weight
            "get_body_composition": lambda: call_and_display(
                api.get_body_composition,
                config.today.isoformat(),
                method_name="get_body_composition",
                api_call_desc=f"api.get_body_composition('{config.today.isoformat()}')",
            ),
            "get_weigh_ins": lambda: call_and_display(
                api.get_weigh_ins,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_weigh_ins",
                api_call_desc=f"api.get_weigh_ins('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_daily_weigh_ins": lambda: call_and_display(
                api.get_daily_weigh_ins,
                config.today.isoformat(),
                method_name="get_daily_weigh_ins",
                api_call_desc=f"api.get_daily_weigh_ins('{config.today.isoformat()}')",
            ),
            "add_weigh_in": lambda: add_weigh_in_data(api),
            "add_body_composition": lambda: add_body_composition_data(api),
            "delete_weigh_ins": lambda: delete_weigh_ins_data(api),
            "delete_weigh_in": lambda: delete_weigh_in_data(api),
            # Goals & Achievements
            "get_personal_records": lambda: get_personal_records_data(api),
            "get_earned_badges": lambda: call_and_display(
                api.get_earned_badges,
                method_name="get_earned_badges",
                api_call_desc="api.get_earned_badges()",
            ),
            "get_adhoc_challenges": lambda: call_and_display(
                api.get_adhoc_challenges,
                config.start,
                config.default_limit,
                method_name="get_adhoc_challenges",
                api_call_desc=f"api.get_adhoc_challenges({config.start}, {config.default_limit})",
            ),
            "get_available_badge_challenges": lambda: call_and_display(
                api.get_available_badge_challenges,
                config.start_badge,
                config.default_limit,
                method_name="get_available_badge_challenges",
                api_call_desc=f"api.get_available_badge_challenges({config.start_badge}, {config.default_limit})",
            ),
            "get_active_goals": lambda: call_and_display(
                api.get_goals,
                status="active",
                start=config.start,
                limit=config.default_limit,
                method_name="get_goals",
                api_call_desc=f"api.get_goals(status='active', start={config.start}, limit={config.default_limit})",
            ),
            "get_future_goals": lambda: call_and_display(
                api.get_goals,
                status="future",
                start=config.start,
                limit=config.default_limit,
                method_name="get_goals",
                api_call_desc=f"api.get_goals(status='future', start={config.start}, limit={config.default_limit})",
            ),
            "get_past_goals": lambda: call_and_display(
                api.get_goals,
                status="past",
                start=config.start,
                limit=config.default_limit,
                method_name="get_goals",
                api_call_desc=f"api.get_goals(status='past', start={config.start}, limit={config.default_limit})",
            ),
            "get_badge_challenges": lambda: call_and_display(
                api.get_badge_challenges,
                config.start_badge,
                config.default_limit,
                method_name="get_badge_challenges",
                api_call_desc=f"api.get_badge_challenges({config.start_badge}, {config.default_limit})",
            ),
            "get_non_completed_badge_challenges": lambda: call_and_display(
                api.get_non_completed_badge_challenges,
                config.start_badge,
                config.default_limit,
                method_name="get_non_completed_badge_challenges",
                api_call_desc=f"api.get_non_completed_badge_challenges({config.start_badge}, {config.default_limit})",
            ),
            "get_inprogress_virtual_challenges": lambda: get_virtual_challenges_data(
                api
            ),
            "get_race_predictions": lambda: call_and_display(
                api.get_race_predictions,
                method_name="get_race_predictions",
                api_call_desc="api.get_race_predictions()",
            ),
            "get_hill_score": lambda: call_and_display(
                api.get_hill_score,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_hill_score",
                api_call_desc=f"api.get_hill_score('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_endurance_score": lambda: call_and_display(
                api.get_endurance_score,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_endurance_score",
                api_call_desc=f"api.get_endurance_score('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_available_badges": lambda: call_and_display(
                api.get_available_badges,
                method_name="get_available_badges",
                api_call_desc="api.get_available_badges()",
            ),
            "get_in_progress_badges": lambda: call_and_display(
                api.get_in_progress_badges,
                method_name="get_in_progress_badges",
                api_call_desc="api.get_in_progress_badges()",
            ),
            # Device & Technical
            "get_devices": lambda: call_and_display(
                api.get_devices,
                method_name="get_devices",
                api_call_desc="api.get_devices()",
            ),
            "get_device_alarms": lambda: call_and_display(
                api.get_device_alarms,
                method_name="get_device_alarms",
                api_call_desc="api.get_device_alarms()",
            ),
            "get_solar_data": lambda: get_solar_data(api),
            "request_reload": lambda: call_and_display(
                api.request_reload,
                config.today.isoformat(),
                method_name="request_reload",
                api_call_desc=f"api.request_reload('{config.today.isoformat()}')",
            ),
            "get_device_settings": lambda: get_device_settings_data(api),
            "get_device_last_used": lambda: call_and_display(
                api.get_device_last_used,
                method_name="get_device_last_used",
                api_call_desc="api.get_device_last_used()",
            ),
            "get_primary_training_device": lambda: call_and_display(
                api.get_primary_training_device,
                method_name="get_primary_training_device",
                api_call_desc="api.get_primary_training_device()",
            ),
            # Gear & Equipment
            "get_gear": lambda: get_gear_data(api),
            "get_gear_defaults": lambda: get_gear_defaults_data(api),
            "get_gear_stats": lambda: get_gear_stats_data(api),
            "get_gear_activities": lambda: get_gear_activities_data(api),
            "set_gear_default": lambda: set_gear_default_data(api),
            "track_gear_usage": lambda: track_gear_usage_data(api),
            "add_and_remove_gear_to_activity": lambda: add_and_remove_gear_to_activity(
                api
            ),
            "create_gear": lambda: create_gear_data(api),
            # Hydration & Wellness
            "get_hydration_data": lambda: call_and_display(
                api.get_hydration_data,
                config.today.isoformat(),
                method_name="get_hydration_data",
                api_call_desc=f"api.get_hydration_data('{config.today.isoformat()}')",
            ),
            "get_pregnancy_summary": lambda: call_and_display(
                api.get_pregnancy_summary,
                method_name="get_pregnancy_summary",
                api_call_desc="api.get_pregnancy_summary()",
            ),
            "get_all_day_events": lambda: call_and_display(
                api.get_all_day_events,
                config.week_start.isoformat(),
                method_name="get_all_day_events",
                api_call_desc=f"api.get_all_day_events('{config.week_start.isoformat()}')",
            ),
            "add_hydration_data": lambda: add_hydration_data_entry(api),
            "set_blood_pressure": lambda: set_blood_pressure_data(api),
            "get_menstrual_data_for_date": lambda: call_and_display(
                api.get_menstrual_data_for_date,
                config.today.isoformat(),
                method_name="get_menstrual_data_for_date",
                api_call_desc=f"api.get_menstrual_data_for_date('{config.today.isoformat()}')",
            ),
            "get_menstrual_calendar_data": lambda: call_and_display(
                api.get_menstrual_calendar_data,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_menstrual_calendar_data",
                api_call_desc=f"api.get_menstrual_calendar_data('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_menstrual_last_confirmed": lambda: call_and_display(
                api.get_menstrual_last_confirmed,
                config.today.isoformat(),
                method_name="get_menstrual_last_confirmed",
                api_call_desc=(
                    f"api.get_menstrual_last_confirmed('{config.today.isoformat()}')"
                ),
            ),
            "get_menstrual_cycle_summary": lambda: call_and_display(
                api.get_menstrual_cycle_summary,
                config.today.isoformat(),
                method_name="get_menstrual_cycle_summary",
                api_call_desc=(
                    f"api.get_menstrual_cycle_summary('{config.today.isoformat()}')"
                ),
            ),
            "get_menstrual_reports": lambda: call_and_display(
                api.get_menstrual_reports,
                config.today.isoformat(),
                6,
                method_name="get_menstrual_reports",
                api_call_desc=(
                    f"api.get_menstrual_reports('{config.today.isoformat()}', 6)"
                ),
            ),
            "update_menstrual_daily_log": lambda: update_menstrual_daily_log_entry(api),
            "update_menstrual_calendar": lambda: update_menstrual_calendar_entry(api),
            "init_menstrual_cycle_setup": lambda: init_menstrual_cycle_setup_entry(api),
            "confirm_menstrual_period_start": (
                lambda: confirm_menstrual_period_start_entry(api)
            ),
            "update_menstrual_settings": lambda: update_menstrual_settings_entry(api),
            # Nutrition
            "get_nutrition_daily_food_log": lambda: call_and_display(
                api.get_nutrition_daily_food_log,
                config.today.isoformat(),
                method_name="get_nutrition_daily_food_log",
                api_call_desc=f"api.get_nutrition_daily_food_log('{config.today.isoformat()}')",
            ),
            "get_nutrition_daily_meals": lambda: call_and_display(
                api.get_nutrition_daily_meals,
                config.today.isoformat(),
                method_name="get_nutrition_daily_meals",
                api_call_desc=f"api.get_nutrition_daily_meals('{config.today.isoformat()}')",
            ),
            "get_nutrition_daily_settings": lambda: call_and_display(
                api.get_nutrition_daily_settings,
                config.today.isoformat(),
                method_name="get_nutrition_daily_settings",
                api_call_desc=f"api.get_nutrition_daily_settings('{config.today.isoformat()}')",
            ),
            # Blood Pressure Management
            "delete_blood_pressure": lambda: delete_blood_pressure_data(api),
            # Activity Management
            "set_activity_name": lambda: set_activity_name_data(api),
            "set_activity_type": lambda: set_activity_type_data(api),
            "set_activity_description": lambda: set_activity_description_data(api),
            "set_activity_exercise_sets": lambda: set_activity_exercise_sets_data(api),
            "create_manual_activity": lambda: create_manual_activity_data(api),
            "delete_activity": lambda: delete_activity_data(api),
            "get_activities_by_date": lambda: call_and_display(
                api.get_activities_by_date,
                config.today.isoformat(),
                config.today.isoformat(),
                method_name="get_activities_by_date",
                api_call_desc=f"api.get_activities_by_date('{config.today.isoformat()}', '{config.today.isoformat()}')",
            ),
            # System & Export
            "create_health_report": lambda: DataExporter.create_health_report(api),
            "remove_tokens": remove_stored_tokens,
            "disconnect": lambda: disconnect_api(api),
            "download_health_snapshot": lambda: download_health_snapshot_file(api),
            # GraphQL Queries
            "query_garmin_graphql": lambda: query_garmin_graphql_data(api),
        }

        if key in api_methods:
            print(translate("ui.executing", key=key))
            api_methods[key]()
        else:
            print(translate("ui.not_implemented", key=key))

    except Exception as e:
        print(translate("ui.error_execute", key=key, error=e))


def remove_stored_tokens():
    """Remove stored login tokens."""
    try:
        token_file = token_file_path(config.tokenstore)
        if not token_file.exists():
            print(translate("ui.no_tokens"))
            return
        Garmin().logout(config.tokenstore)
        print(translate("demo.tokens_removed"))
    except Exception as e:
        print(translate("error.token_remove_error", error=e))


def disconnect_api(api: Garmin):
    """Disconnect from Garmin Connect."""
    api.logout()
    print(translate("ui.disconnected"))


def download_health_snapshot_file(api: Garmin):
    """Download today's Health Snapshot ZIP and save it to the export directory."""
    requested_date = config.today.isoformat()
    try:
        content = api.download_health_snapshot(requested_date)
        if not content:
            print(translate("ui.no_snapshot"))
            return
        safe_date = _safe_filename_component(requested_date)
        filepath = config.export_dir / f"{safe_date}_HEALTH_SNAPSHOT.zip"
        with _open_private(filepath, "wb") as f:
            f.write(content)
        print(translate("demo.snapshot_saved", path=filepath))
    except Exception as e:
        print(translate("error.snapshot_error", error=e))


def init_api(email: str | None = None, password: str | None = None) -> Garmin | None:
    """Initialize Garmin API with smart error handling and recovery."""
    # First try to login with stored tokens
    try:
        print(translate("demo.login_tokens", path=config.tokenstore))

        garmin = Garmin()
        garmin.login(config.tokenstore)
        print(translate("demo.login_tokens_success"))
        return garmin

    except GarminConnectTooManyRequestsError as err:
        print(translate("ui.login_error", error=err))
        sys.exit(1)

    except (
        FileNotFoundError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
    ):
        print(translate("demo.fresh_login"))

    # Loop for credential entry with retry on auth failure
    while True:
        try:
            # Get credentials if not provided
            if not email or not password:
                email = input(translate("prompt.email")).strip()
                password = getpass(translate("demo.password"))

            print(translate("demo.logging_in"))
            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            # Don't keep the plaintext password in local scope longer than needed.
            password = None
            result1, result2 = garmin.login()

            if result1 == "needs_mfa":
                print(translate("demo.mfa_required"))

                mfa_code = get_mfa()
                print(translate("demo.mfa_submit"))

                try:
                    garmin.resume_login(result2, mfa_code)
                    print(translate("demo.mfa_success"))

                except GarminConnectTooManyRequestsError:
                    print(translate("demo.mfa_too_many"))
                    print(translate("demo.mfa_wait"))
                    sys.exit(1)
                except GarminConnectAuthenticationError as mfa_error:
                    # Handle specific errors from MFA
                    error_str = str(mfa_error)
                    print(translate("ui.mfa_debug", error=error_str))
                    if "401" in error_str or "403" in error_str:
                        print(translate("demo.mfa_invalid"))
                        print(translate("demo.mfa_check"))
                        continue
                    # Other HTTP errors - don't retry
                    print(translate("ui.mfa_error", error=mfa_error))
                    sys.exit(1)

            # Save tokens for future use
            garmin.client.dump(config.tokenstore)
            print(translate("ui.login_saved", path=config.tokenstore))

            return garmin

        except GarminConnectTooManyRequestsError as err:
            print(translate("ui.login_error", error=err))
            sys.exit(1)

        except GarminConnectAuthenticationError as err:
            print(translate("ui.login_error", error=err))
            print(translate("ui.credentials_check"))
            # Clear the provided credentials to force re-entry
            email = None
            password = None
            continue

        except (
            FileNotFoundError,
            GarminConnectConnectionError,
            requests.exceptions.HTTPError,
        ) as err:
            print(translate("error.connection", error=err))
            print(translate("ui.check_connection"))
            return None

        except KeyboardInterrupt:
            print(translate("demo.login_cancelled"))
            return None


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace | None:
    """Parse demo-only options and configure the selected interface language."""
    parser = argparse.ArgumentParser(
        description="Interactive Garmin Connect API demo",
    )
    parser.add_argument(
        "-l",
        "--lang",
        metavar="LANGUAGE",
        help="Interface language (default: en)",
    )
    args = parser.parse_args(argv)

    try:
        set_language(
            resolve_language(
                args.lang,
                os.getenv("GARMIN_LANG"),
                load_persisted_language(),
            )
        )
    except UnsupportedLanguageError as error:
        builtins.print(str(error), file=sys.stderr)
        return None
    return args


def main(argv: list[str] | None = None) -> int:
    """Main program loop with funny health status in menu prompt."""
    if _parse_args(argv) is None:
        return 2

    # Display export directory information on startup
    print(translate("prompt.exported", path=config.export_dir))
    print(translate("prompt.responses_file"))

    api_instance = init_api(config.email, config.password)
    current_category = None

    while True:
        try:
            if api_instance:
                # Add health status in menu prompt
                try:
                    summary = api_instance.get_user_summary(config.today.isoformat())
                    hydration_data = None
                    with suppress(Exception):
                        hydration_data = api_instance.get_hydration_data(
                            config.today.isoformat()
                        )

                    if summary:
                        steps = summary.get("totalSteps") or 0
                        calories = summary.get("totalKilocalories") or 0

                        # Build stats string with hydration if available
                        stats_parts = [
                            translate("stats.steps", value=f"{steps:,}"),
                            translate("stats.kcal", value=calories),
                        ]

                        if hydration_data and hydration_data.get("valueInML"):
                            hydration_ml = int(hydration_data.get("valueInML", 0))
                            hydration_cups = round(hydration_ml / 240, 1)
                            hydration_goal = hydration_data.get("goalInML", 0)

                            if hydration_goal > 0:
                                hydration_percent = round(
                                    (hydration_ml / hydration_goal) * 100
                                )
                                stats_parts.append(
                                    translate(
                                        "stats.water_goal",
                                        value=hydration_ml,
                                        percent=hydration_percent,
                                    )
                                )
                            else:
                                stats_parts.append(
                                    translate(
                                        "stats.water_cups",
                                        value=hydration_ml,
                                        cups=hydration_cups,
                                    )
                                )

                        stats_string = " | ".join(stats_parts)
                        print(translate("stats.today", stats=stats_string))

                        if steps < 5000:
                            print(translate("ui.move_legs"))
                        elif steps > 15000:
                            print(translate("ui.crushing_it"))
                        else:
                            print(translate("ui.nice_progress"))
                except Exception as e:
                    print(
                        translate("ui.stats_unavailable", error=e)
                    )  # Silently skip if stats can't be fetched

            # Display appropriate menu
            if current_category is None:
                print_main_menu()
                option = safe_readkey()

                # Handle main menu options
                if option == "q":
                    print(translate("demo.exit_message"))
                    break
                if option == "l":
                    select_language()
                    continue
                if option in menu_categories:
                    current_category = option
                else:
                    print(
                        translate(
                            "ui.invalid_selection_categories",
                            categories=", ".join(menu_categories.keys()),
                        )
                    )
            else:
                # In a category - show category menu
                print_category_menu(current_category)
                option = safe_readkey()

                # Handle category menu options. Validity is decided solely by
                # membership in the current category's own options dict —
                # no separate hardcoded character whitelist to keep in sync
                # whenever a new option key (e.g. an uppercase letter) is
                # added to menu_categories.
                if option == "q":
                    current_category = None  # Back to main menu
                else:
                    try:
                        category_data = menu_categories[current_category]
                        category_options = category_data["options"]
                        if option in category_options:
                            api_key = category_options[option]["key"]
                            execute_api_call(api_instance, api_key)
                        else:
                            valid_keys = ", ".join(category_options.keys())
                            print(translate("ui.invalid_option", options=valid_keys))
                    except Exception as e:
                        print(
                            translate("ui.error_execute_option", option=option, error=e)
                        )

        except KeyboardInterrupt:
            print(translate("demo.interrupted"))
        except Exception as e:
            print(translate("ui.unexpected", error=e))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
