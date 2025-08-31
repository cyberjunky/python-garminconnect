#!/usr/bin/env python3
"""
🏃‍♂️ Garmin Connect API Demo
=====================================

Dependencies:
pip3 install garth requests readchar

Environment Variables (optional):
export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>
export GARMINTOKENS=<path to token storage>
"""

import datetime
import json
import os
from contextlib import suppress
from datetime import timedelta
from getpass import getpass
from pathlib import Path
from typing import Any

import readchar
import requests
from garth.exc import GarthHTTPError

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

api: Garmin | None = None


class Config:
    """Configuration class for the Garmin Connect API demo."""

    def __init__(self):
        # Load environment variables
        self.email = os.getenv("EMAIL")
        self.password = os.getenv("PASSWORD")
        self.tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
        self.tokenstore_base64 = (
            os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
        )

        # Date settings
        self.today = datetime.date.today()
        self.week_start = self.today - timedelta(days=7)
        self.month_start = self.today - timedelta(days=30)

        # API call settings
        self.default_limit = 100
        self.start = 0
        self.start_badge = 1  # Badge related calls start counting at 1

        # Activity settings
        self.activitytype = ""  # Possible values: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
        self.activityfile = (
            "test_data/sample_activity.gpx"  # Supported file types: .fit .gpx .tcx
        )
        self.workoutfile = "test_data/sample_workout.json"  # Sample workout JSON file

        # Export settings
        self.export_dir = Path("your_data")
        self.export_dir.mkdir(exist_ok=True)


# Initialize configuration
config = Config()

# Organized menu categories
menu_categories = {
    "1": {
        "name": "👤 User & Profile",
        "options": {
            "1": {"desc": "Get full name", "key": "get_full_name"},
            "2": {"desc": "Get unit system", "key": "get_unit_system"},
            "3": {"desc": "Get user profile", "key": "get_user_profile"},
            "4": {
                "desc": "Get userprofile settings",
                "key": "get_userprofile_settings",
            },
        },
    },
    "2": {
        "name": "📊 Daily Health & Activity",
        "options": {
            "1": {
                "desc": f"Get activity data for '{config.today.isoformat()}'",
                "key": "get_stats",
            },
            "2": {
                "desc": f"Get user summary for '{config.today.isoformat()}'",
                "key": "get_user_summary",
            },
            "3": {
                "desc": f"Get stats and body composition for '{config.today.isoformat()}'",
                "key": "get_stats_and_body",
            },
            "4": {
                "desc": f"Get steps data for '{config.today.isoformat()}'",
                "key": "get_steps_data",
            },
            "5": {
                "desc": f"Get heart rate data for '{config.today.isoformat()}'",
                "key": "get_heart_rates",
            },
            "6": {
                "desc": f"Get resting heart rate for '{config.today.isoformat()}'",
                "key": "get_resting_heart_rate",
            },
            "7": {
                "desc": f"Get sleep data for '{config.today.isoformat()}'",
                "key": "get_sleep_data",
            },
            "8": {
                "desc": f"Get stress data for '{config.today.isoformat()}'",
                "key": "get_all_day_stress",
            },
        },
    },
    "3": {
        "name": "🔬 Advanced Health Metrics",
        "options": {
            "1": {
                "desc": f"Get training readiness for '{config.today.isoformat()}'",
                "key": "get_training_readiness",
            },
            "2": {
                "desc": f"Get training status for '{config.today.isoformat()}'",
                "key": "get_training_status",
            },
            "3": {
                "desc": f"Get respiration data for '{config.today.isoformat()}'",
                "key": "get_respiration_data",
            },
            "4": {
                "desc": f"Get SpO2 data for '{config.today.isoformat()}'",
                "key": "get_spo2_data",
            },
            "5": {
                "desc": f"Get max metrics (VO2, fitness age) for '{config.today.isoformat()}'",
                "key": "get_max_metrics",
            },
            "6": {
                "desc": f"Get Heart Rate Variability (HRV) for '{config.today.isoformat()}'",
                "key": "get_hrv_data",
            },
            "7": {
                "desc": f"Get Fitness Age data for '{config.today.isoformat()}'",
                "key": "get_fitnessage_data",
            },
            "8": {
                "desc": f"Get stress data for '{config.today.isoformat()}'",
                "key": "get_stress_data",
            },
            "9": {"desc": "Get lactate threshold data", "key": "get_lactate_threshold"},
            "0": {
                "desc": f"Get intensity minutes for '{config.today.isoformat()}'",
                "key": "get_intensity_minutes_data",
            },
        },
    },
    "4": {
        "name": "📈 Historical Data & Trends",
        "options": {
            "1": {
                "desc": f"Get daily steps from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_daily_steps",
            },
            "2": {
                "desc": f"Get body battery from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_body_battery",
            },
            "3": {
                "desc": f"Get floors data for '{config.week_start.isoformat()}'",
                "key": "get_floors",
            },
            "4": {
                "desc": f"Get blood pressure from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_blood_pressure",
            },
            "5": {
                "desc": f"Get progress summary from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_progress_summary_between_dates",
            },
            "6": {
                "desc": f"Get body battery events for '{config.week_start.isoformat()}'",
                "key": "get_body_battery_events",
            },
        },
    },
    "5": {
        "name": "🏃 Activities & Workouts",
        "options": {
            "1": {
                "desc": f"Get recent activities (limit {config.default_limit})",
                "key": "get_activities",
            },
            "2": {"desc": "Get last activity", "key": "get_last_activity"},
            "3": {
                "desc": f"Get activities for today '{config.today.isoformat()}'",
                "key": "get_activities_fordate",
            },
            "4": {
                "desc": f"Download activities by date range '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "download_activities",
            },
            "5": {
                "desc": "Get all activity types and statistics",
                "key": "get_activity_types",
            },
            "6": {
                "desc": f"Upload activity data from {config.activityfile}",
                "key": "upload_activity",
            },
            "7": {"desc": "Get workouts", "key": "get_workouts"},
            "8": {"desc": "Get activity splits (laps)", "key": "get_activity_splits"},
            "9": {
                "desc": "Get activity typed splits",
                "key": "get_activity_typed_splits",
            },
            "0": {
                "desc": "Get activity split summaries",
                "key": "get_activity_split_summaries",
            },
            "a": {"desc": "Get activity weather data", "key": "get_activity_weather"},
            "b": {
                "desc": "Get activity heart rate zones",
                "key": "get_activity_hr_in_timezones",
            },
            "c": {
                "desc": "Get detailed activity information",
                "key": "get_activity_details",
            },
            "d": {"desc": "Get activity gear information", "key": "get_activity_gear"},
            "e": {"desc": "Get single activity data", "key": "get_activity"},
            "f": {
                "desc": "Get strength training exercise sets",
                "key": "get_activity_exercise_sets",
            },
            "g": {"desc": "Get workout by ID", "key": "get_workout_by_id"},
            "h": {"desc": "Download workout to .FIT file", "key": "download_workout"},
            "i": {
                "desc": f"Upload workout from {config.workoutfile}",
                "key": "upload_workout",
            },
            "j": {
                "desc": f"Get activities by date range '{config.today.isoformat()}'",
                "key": "get_activities_by_date",
            },
            "k": {"desc": "Set activity name", "key": "set_activity_name"},
            "l": {"desc": "Set activity type", "key": "set_activity_type"},
            "m": {"desc": "Create manual activity", "key": "create_manual_activity"},
            "n": {"desc": "Delete activity", "key": "delete_activity"},
        },
    },
    "6": {
        "name": "⚖️ Body Composition & Weight",
        "options": {
            "1": {
                "desc": f"Get body composition for '{config.today.isoformat()}'",
                "key": "get_body_composition",
            },
            "2": {
                "desc": f"Get weigh-ins from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_weigh_ins",
            },
            "3": {
                "desc": f"Get daily weigh-ins for '{config.today.isoformat()}'",
                "key": "get_daily_weigh_ins",
            },
            "4": {"desc": "Add a weigh-in (interactive)", "key": "add_weigh_in"},
            "5": {
                "desc": f"Set body composition data for '{config.today.isoformat()}' (interactive)",
                "key": "set_body_composition",
            },
            "6": {
                "desc": f"Add body composition for '{config.today.isoformat()}' (interactive)",
                "key": "add_body_composition",
            },
            "7": {
                "desc": f"Delete all weigh-ins for '{config.today.isoformat()}'",
                "key": "delete_weigh_ins",
            },
            "8": {"desc": "Delete specific weigh-in", "key": "delete_weigh_in"},
        },
    },
    "7": {
        "name": "🏆 Goals & Achievements",
        "options": {
            "1": {"desc": "Get personal records", "key": "get_personal_records"},
            "2": {"desc": "Get earned badges", "key": "get_earned_badges"},
            "3": {"desc": "Get adhoc challenges", "key": "get_adhoc_challenges"},
            "4": {
                "desc": "Get available badge challenges",
                "key": "get_available_badge_challenges",
            },
            "5": {"desc": "Get active goals", "key": "get_active_goals"},
            "6": {"desc": "Get future goals", "key": "get_future_goals"},
            "7": {"desc": "Get past goals", "key": "get_past_goals"},
            "8": {"desc": "Get badge challenges", "key": "get_badge_challenges"},
            "9": {
                "desc": "Get non-completed badge challenges",
                "key": "get_non_completed_badge_challenges",
            },
            "0": {
                "desc": "Get virtual challenges in progress",
                "key": "get_inprogress_virtual_challenges",
            },
            "a": {"desc": "Get race predictions", "key": "get_race_predictions"},
            "b": {
                "desc": f"Get hill score from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_hill_score",
            },
            "c": {
                "desc": f"Get endurance score from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_endurance_score",
            },
            "d": {"desc": "Get available badges", "key": "get_available_badges"},
            "e": {"desc": "Get badges in progress", "key": "get_in_progress_badges"},
        },
    },
    "8": {
        "name": "⌚ Device & Technical",
        "options": {
            "1": {"desc": "Get all device information", "key": "get_devices"},
            "2": {"desc": "Get device alarms", "key": "get_device_alarms"},
            "3": {"desc": "Get solar data from your devices", "key": "get_solar_data"},
            "4": {
                "desc": f"Request data reload (epoch) for '{config.today.isoformat()}'",
                "key": "request_reload",
            },
            "5": {"desc": "Get device settings", "key": "get_device_settings"},
            "6": {"desc": "Get device last used", "key": "get_device_last_used"},
            "7": {
                "desc": "Get primary training device",
                "key": "get_primary_training_device",
            },
        },
    },
    "9": {
        "name": "🎽 Gear & Equipment",
        "options": {
            "1": {"desc": "Get user gear list", "key": "get_gear"},
            "2": {"desc": "Get gear defaults", "key": "get_gear_defaults"},
            "3": {"desc": "Get gear statistics", "key": "get_gear_stats"},
            "4": {"desc": "Get gear activities", "key": "get_gear_activities"},
            "5": {"desc": "Set gear default", "key": "set_gear_default"},
            "6": {
                "desc": "Track gear usage (total time used)",
                "key": "track_gear_usage",
            },
        },
    },
    "0": {
        "name": "💧 Hydration & Wellness",
        "options": {
            "1": {
                "desc": f"Get hydration data for '{config.today.isoformat()}'",
                "key": "get_hydration_data",
            },
            "2": {"desc": "Add hydration data", "key": "add_hydration_data"},
            "3": {
                "desc": "Set blood pressure and pulse (interactive)",
                "key": "set_blood_pressure",
            },
            "4": {"desc": "Get pregnancy summary data", "key": "get_pregnancy_summary"},
            "5": {
                "desc": f"Get all day events for '{config.week_start.isoformat()}'",
                "key": "get_all_day_events",
            },
            "6": {
                "desc": f"Get body battery events for '{config.week_start.isoformat()}'",
                "key": "get_body_battery_events",
            },
            "7": {
                "desc": f"Get menstrual data for '{config.today.isoformat()}'",
                "key": "get_menstrual_data_for_date",
            },
            "8": {
                "desc": f"Get menstrual calendar from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_menstrual_calendar_data",
            },
            "9": {
                "desc": "Delete blood pressure entry",
                "key": "delete_blood_pressure",
            },
        },
    },
    "a": {
        "name": "🔧 System & Export",
        "options": {
            "1": {"desc": "Create sample health report", "key": "create_health_report"},
            "2": {
                "desc": "Remove stored login tokens (logout)",
                "key": "remove_tokens",
            },
            "3": {"desc": "Disconnect from Garmin Connect", "key": "disconnect"},
            "4": {"desc": "Execute GraphQL query", "key": "query_garmin_graphql"},
        },
    },
}

current_category = None


def print_main_menu():
    """Print the main category menu."""
    print("\n" + "=" * 50)
    print("🏃‍♂️ Garmin Connect API Demo - Main Menu")
    print("=" * 50)
    print("Select a category:")
    print()

    for key, category in menu_categories.items():
        print(f"  [{key}] {category['name']}")

    print()
    print("  [q] Exit program")
    print()
    print("Make your selection: ", end="", flush=True)


def print_category_menu(category_key: str):
    """Print options for a specific category."""
    if category_key not in menu_categories:
        return False

    category = menu_categories[category_key]
    print(f"\n📋 #{category_key} {category['name']} - Options")
    print("-" * 40)

    for key, option in category["options"].items():
        print(f"  [{key}] {option['desc']}")

    print()
    print("  [q] Back to main menu")
    print()
    print("Make your selection: ", end="", flush=True)
    return True


def get_mfa() -> str:
    """Get MFA token."""
    return input("MFA one-time code: ")


class DataExporter:
    """Utilities for exporting data in various formats."""

    @staticmethod
    def save_json(data: Any, filename: str, pretty: bool = True) -> str:
        """Save data as JSON file."""
        filepath = config.export_dir / f"{filename}.json"
        with open(filepath, "w", encoding="utf-8") as f:
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
            "user_info": {"full_name": "N/A", "unit_system": "N/A"},
            "today_summary": {},
            "recent_activities": [],
            "health_metrics": {},
            "weekly_data": [],
            "device_info": [],
        }

        try:
            # Basic user info
            report_data["user_info"]["full_name"] = (
                api_instance.get_full_name() or "N/A"
            )
            report_data["user_info"]["unit_system"] = (
                api_instance.get_unit_system() or "N/A"
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
                except Exception:
                    pass  # Skip if data not available

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
            print(f"Error creating health report: {e}")

        # Save JSON version
        timestamp = config.today.strftime("%Y%m%d")
        json_filename = f"garmin_health_{timestamp}"

        # Create HTML version
        html_filepath = DataExporter.create_readable_health_report(report_data)

        print("📊 Reports created:")
        print(f"   HTML: {html_filepath}")

        return html_filepath

    @staticmethod
    def create_readable_health_report(report_data: dict) -> str:
        """Create a readable HTML report from comprehensive health data."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"health_report_{timestamp}.html"

        # Extract key information
        user_name = report_data.get("user_info", {}).get("full_name", "Unknown User")
        generated_at = report_data.get("generated_at", "Unknown")

        # Create HTML content with complete styling
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Garmin Health Report - {user_name}</title>
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
            <h1>🏃 Garmin Health Report</h1>
            <p><strong>{user_name}</strong></p>
        </div>

        <div class="meta-info">
            <p><strong>Generated:</strong> {generated_at}</p>
            <p><strong>Date:</strong> {config.today.isoformat()}</p>
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
            <h2>📈 Today's Activity Summary</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <h4>👟 Steps</h4>
                    <div class="metric-value">{steps:,} <span class="metric-unit">steps</span></div>
                </div>
                <div class="metric-card">
                    <h4>🔥 Calories</h4>
                    <div class="metric-value">{calories:,} <span class="metric-unit">total</span></div>
                    <div style="margin-top: 10px;">{active_calories:,} active</div>
                </div>
                <div class="metric-card">
                    <h4>📏 Distance</h4>
                    <div class="metric-value">{distance} <span class="metric-unit">km</span></div>
                </div>
            </div>
        </div>
"""
        else:
            html_content += """
        <div class="section">
            <h2>📈 Today's Activity Summary</h2>
            <div class="no-data">No activity data available for today</div>
        </div>
"""

        # Health Metrics Section
        health_metrics = report_data.get("health_metrics", {})
        if health_metrics and any(health_metrics.values()):
            html_content += """
        <div class="section">
            <h2>❤️ Health Metrics</h2>
            <div class="metric-grid">
"""

            # Heart Rate
            heart_rate = health_metrics.get("heart_rate", {})
            if heart_rate and isinstance(heart_rate, dict):
                resting_hr = heart_rate.get("restingHeartRate", "N/A")
                max_hr = heart_rate.get("maxHeartRate", "N/A")
                html_content += f"""
                <div class="metric-card">
                    <h4>💓 Heart Rate</h4>
                    <div class="metric-value">{resting_hr} <span class="metric-unit">bpm (resting)</span></div>
                    <div style="margin-top: 10px;">Max: {max_hr} bpm</div>
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
                    <h4>😴 Sleep</h4>
                    <div class="metric-value">{sleep_hours} <span class="metric-unit">hours</span></div>
                    <div style="margin-top: 10px;">Deep Sleep: {deep_hours} hours</div>
                </div>
"""

            # Steps
            steps_data = health_metrics.get("steps", {})
            if steps_data and isinstance(steps_data, dict):
                total_steps = steps_data.get("totalSteps", 0)
                goal = steps_data.get("dailyStepGoal", 10000)
                html_content += f"""
                <div class="metric-card">
                    <h4>🎯 Step Goal</h4>
                    <div class="metric-value">{total_steps:,} <span class="metric-unit">of {goal:,}</span></div>
                    <div style="margin-top: 10px;">Goal: {round((total_steps/goal)*100) if goal else 0}%</div>
                </div>
"""

            # Stress Data
            stress_data = health_metrics.get("stress", {})
            if stress_data and isinstance(stress_data, dict):
                avg_stress = stress_data.get("avgStressLevel", "N/A")
                max_stress = stress_data.get("maxStressLevel", "N/A")
                html_content += f"""
                <div class="metric-card">
                    <h4>😰 Stress Level</h4>
                    <div class="metric-value">{avg_stress} <span class="metric-unit">avg</span></div>
                    <div style="margin-top: 10px;">Max: {max_stress}</div>
                </div>
"""

            # Body Battery
            body_battery = health_metrics.get("body_battery", [])
            if body_battery and isinstance(body_battery, list) and body_battery:
                latest_bb = body_battery[-1] if body_battery else {}
                charged = latest_bb.get("charged", "N/A")
                drained = latest_bb.get("drained", "N/A")
                html_content += f"""
                <div class="metric-card">
                    <h4>🔋 Body Battery</h4>
                    <div class="metric-value">+{charged} <span class="metric-unit">charged</span></div>
                    <div style="margin-top: 10px;">-{drained} drained</div>
                </div>
"""

            html_content += "            </div>\n        </div>\n"
        else:
            html_content += """
        <div class="section">
            <h2>❤️ Health Metrics</h2>
            <div class="no-data">No health metrics data available</div>
        </div>
"""

        # Weekly Trends Section
        weekly_data = report_data.get("weekly_data", [])
        if weekly_data:
            html_content += """
        <div class="section">
            <h2>📊 Weekly Trends (Last 7 Days)</h2>
            <div class="metric-grid">
"""
            for daily in weekly_data[:7]:  # Show last 7 days
                date = daily.get("date", "Unknown")
                steps = daily.get("totalSteps", 0)
                calories = daily.get("totalKilocalories", 0)
                distance = (
                    round(daily.get("totalDistanceMeters", 0) / 1000, 2)
                    if daily.get("totalDistanceMeters")
                    else 0
                )

                html_content += f"""
                <div class="metric-card">
                    <h4>📅 {date}</h4>
                    <div class="metric-value">{steps:,} <span class="metric-unit">steps</span></div>
                    <div style="margin-top: 10px;">
                        <div>{calories:,} kcal</div>
                        <div>{distance} km</div>
                    </div>
                </div>
"""
            html_content += "            </div>\n        </div>\n"

        # Recent Activities Section
        activities = report_data.get("recent_activities", [])
        if activities:
            html_content += """
        <div class="section">
            <h2>🏃 Recent Activities</h2>
"""
            for activity in activities[:5]:  # Show last 5 activities
                name = activity.get("activityName", "Unknown Activity")
                activity_type = activity.get("activityType", {}).get(
                    "typeKey", "Unknown"
                )
                date = (
                    activity.get("startTimeLocal", "").split("T")[0]
                    if activity.get("startTimeLocal")
                    else "Unknown"
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
                    <h4>{name} ({activity_type})</h4>
                    <div class="activity-details">
                        <div><strong>Date:</strong> {date}</div>
                        <div><strong>Duration:</strong> {duration_min} min</div>
                        <div><strong>Distance:</strong> {distance} km</div>
                        <div><strong>Calories:</strong> {calories}</div>
                        <div><strong>Avg HR:</strong> {avg_hr} bpm</div>
                    </div>
                </div>
"""
            html_content += "        </div>\n"
        else:
            html_content += """
        <div class="section">
            <h2>🏃 Recent Activities</h2>
            <div class="no-data">No recent activities found</div>
        </div>
"""

        # Device Information
        device_info = report_data.get("device_info", [])
        if device_info:
            html_content += """
        <div class="section">
            <h2>⌚ Device Information</h2>
            <div class="metric-grid">
"""
            for device in device_info:
                device_name = device.get("displayName", "Unknown Device")
                model = device.get("productDisplayName", "Unknown Model")
                version = device.get("softwareVersion", "Unknown")

                html_content += f"""
                <div class="metric-card">
                    <h4>{device_name}</h4>
                    <div><strong>Model:</strong> {model}</div>
                    <div><strong>Software:</strong> {version}</div>
                </div>
"""
            html_content += "            </div>\n        </div>\n"

        # Footer
        html_content += f"""
        <div class="footer">
            <p>Generated by Garmin Connect API Demo on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>This report is for informational purposes only. Consult healthcare professionals for medical advice.</p>
        </div>
    </div>
</body>
</html>
"""

        # Save HTML file
        html_filepath = config.export_dir / html_filename
        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(html_filepath)


def display_json(api_call: str, output: Any):
    """Enhanced API output formatter with better visualization."""
    print(f"\n📡 API Call: {api_call}")
    print("-" * 50)

    if output is None:
        print("No data returned")
        # Save empty JSON to response.json in the export directory
        response_file = config.export_dir / "response.json"
        with open(response_file, "w", encoding="utf-8") as f:
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
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(response_content)

        print(formatted_output)
        print("-" * 77)

    except Exception as e:
        print(f"Error formatting output: {e}")
        print(output)


def format_timedelta(td):
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}"


def get_solar_data(api: Garmin) -> None:
    """Get solar data from all Garmin devices."""
    try:
        print("☀️ Getting solar data from devices...")

        # First get all devices
        devices = api.get_devices()
        display_json("api.get_devices()", devices)

        # Get device last used
        device_last_used = api.get_device_last_used()
        display_json("api.get_device_last_used()", device_last_used)

        # Get solar data for each device
        if devices:
            for device in devices:
                device_id = device.get("deviceId")
                if device_id:
                    try:
                        device_name = device.get("displayName", f"Device {device_id}")
                        print(
                            f"\n☀️ Getting solar data for device: {device_name} (ID: {device_id})"
                        )
                        solar_data = api.get_device_solar_data(
                            device_id, config.today.isoformat()
                        )
                        display_json(
                            f"api.get_device_solar_data({device_id}, '{config.today.isoformat()}')",
                            solar_data,
                        )
                    except Exception as e:
                        print(
                            f"❌ Error getting solar data for device {device_id}: {e}"
                        )
        else:
            print("ℹ️ No devices found")

    except Exception as e:
        print(f"❌ Error getting solar data: {e}")


def upload_activity_file(api: Garmin) -> None:
    """Upload activity data from file."""
    try:
        # Default activity file from config
        print(f"📤 Uploading activity from file: {config.activityfile}")

        # Check if file exists
        import os

        if not os.path.exists(config.activityfile):
            print(f"❌ File not found: {config.activityfile}")
            print(
                "ℹ️ Please place your activity file (.fit, .gpx, or .tcx) under the 'test_data' directory or update config.activityfile"
            )
            print("ℹ️ Supported formats: FIT, GPX, TCX")
            return

        # Upload the activity
        result = api.upload_activity(config.activityfile)

        if result:
            print("✅ Activity uploaded successfully!")
            display_json(f"api.upload_activity({config.activityfile})", result)
        else:
            print(f"❌ Failed to upload activity from {config.activityfile}")

    except FileNotFoundError:
        print(f"❌ File not found: {config.activityfile}")
        print("ℹ️ Please ensure the activity file exists in the current directory")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print(
                "⚠️ Activity already exists: This activity has already been uploaded to Garmin Connect"
            )
            print("ℹ️ Garmin Connect prevents duplicate activities from being uploaded")
            print(
                "💡 Try modifying the activity timestamps or creating a new activity file"
            )
        elif e.response.status_code == 413:
            print(
                "❌ File too large: The activity file exceeds Garmin Connect's size limit"
            )
            print("💡 Try compressing the file or reducing the number of data points")
        elif e.response.status_code == 422:
            print(
                "❌ Invalid file format: The activity file format is not supported or corrupted"
            )
            print("ℹ️ Supported formats: FIT, GPX, TCX")
            print("💡 Try converting to a different format or check file integrity")
        elif e.response.status_code == 400:
            print("❌ Bad request: Invalid activity data or malformed file")
            print(
                "💡 Check if the activity file contains valid GPS coordinates and timestamps"
            )
        elif e.response.status_code == 401:
            print("❌ Authentication failed: Please login again")
            print("💡 Your session may have expired")
        elif e.response.status_code == 429:
            print("❌ Rate limit exceeded: Too many upload requests")
            print("💡 Please wait a few minutes before trying again")
        else:
            print(f"❌ HTTP Error {e.response.status_code}: {e}")
    except GarminConnectAuthenticationError as e:
        print(f"❌ Authentication error: {e}")
        print("💡 Please check your login credentials and try again")
    except GarminConnectConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Please check your internet connection and try again")
    except GarminConnectTooManyRequestsError as e:
        print(f"❌ Too many requests: {e}")
        print("💡 Please wait a few minutes before trying again")
    except Exception as e:
        # Check if this is a wrapped HTTP error from the Garmin library
        error_str = str(e)
        if "409 Client Error: Conflict" in error_str:
            print(
                "⚠️ Activity already exists: This activity has already been uploaded to Garmin Connect"
            )
            print("ℹ️ Garmin Connect prevents duplicate activities from being uploaded")
            print(
                "💡 Try modifying the activity timestamps or creating a new activity file"
            )
        elif "413" in error_str and "Request Entity Too Large" in error_str:
            print(
                "❌ File too large: The activity file exceeds Garmin Connect's size limit"
            )
            print("💡 Try compressing the file or reducing the number of data points")
        elif "422" in error_str and "Unprocessable Entity" in error_str:
            print(
                "❌ Invalid file format: The activity file format is not supported or corrupted"
            )
            print("ℹ️ Supported formats: FIT, GPX, TCX")
            print("💡 Try converting to a different format or check file integrity")
        elif "400" in error_str and "Bad Request" in error_str:
            print("❌ Bad request: Invalid activity data or malformed file")
            print(
                "💡 Check if the activity file contains valid GPS coordinates and timestamps"
            )
        elif "401" in error_str and "Unauthorized" in error_str:
            print("❌ Authentication failed: Please login again")
            print("💡 Your session may have expired")
        elif "429" in error_str and "Too Many Requests" in error_str:
            print("❌ Rate limit exceeded: Too many upload requests")
            print("💡 Please wait a few minutes before trying again")
        else:
            print(f"❌ Unexpected error uploading activity: {e}")
            print("💡 Please check the file format and try again")


def download_activities_by_date(api: Garmin) -> None:
    """Download activities by date range in multiple formats."""
    try:
        print(
            f"📥 Downloading activities by date range ({config.week_start.isoformat()} to {config.today.isoformat()})..."
        )

        # Get activities for the date range (last 7 days as default)
        activities = api.get_activities_by_date(
            config.week_start.isoformat(), config.today.isoformat()
        )

        if not activities:
            print("ℹ️ No activities found in the specified date range")
            return

        print(f"📊 Found {len(activities)} activities to download")

        # Download each activity in multiple formats
        for activity in activities:
            activity_id = activity.get("activityId")
            activity_name = activity.get("activityName", "Unknown")
            start_time = activity.get("startTimeLocal", "").replace(":", "-")

            if not activity_id:
                continue

            print(f"📥 Downloading: {activity_name} (ID: {activity_id})")

            # Download formats: GPX, TCX, ORIGINAL, CSV
            formats = ["GPX", "TCX", "ORIGINAL", "CSV"]

            for fmt in formats:
                try:
                    filename = f"{start_time}_{activity_id}_ACTIVITY.{fmt.lower()}"
                    if fmt == "ORIGINAL":
                        filename = f"{start_time}_{activity_id}_ACTIVITY.zip"

                    filepath = config.export_dir / filename

                    if fmt == "CSV":
                        # Get activity details for CSV export
                        activity_details = api.get_activity_details(activity_id)
                        with open(filepath, "w", encoding="utf-8") as f:
                            import json

                            json.dump(activity_details, f, indent=2, ensure_ascii=False)
                        print(f"  ✅ {fmt}: {filename}")
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
                            with open(filepath, "wb") as f:
                                f.write(content)
                            print(f"  ✅ {fmt}: {filename}")
                        else:
                            print(f"  ❌ {fmt}: No content available")

                except Exception as e:
                    print(f"  ❌ {fmt}: Error downloading - {e}")

        print(f"✅ Activity downloads completed! Files saved to: {config.export_dir}")

    except Exception as e:
        print(f"❌ Error downloading activities: {e}")


def add_weigh_in_data(api: Garmin) -> None:
    """Add a weigh-in with timestamps."""
    try:
        # Get weight input from user
        print("⚖️ Adding weigh-in entry")
        print("-" * 30)

        # Weight input with validation
        while True:
            try:
                weight_str = input("Enter weight (30-300, default: 85.1): ").strip()
                if not weight_str:
                    weight = 85.1
                    break
                weight = float(weight_str)
                if 30 <= weight <= 300:
                    break
                else:
                    print("❌ Weight must be between 30 and 300")
            except ValueError:
                print("❌ Please enter a valid number")

        # Unit selection
        while True:
            unit_input = input("Enter unit (kg/lbs, default: kg): ").strip().lower()
            if not unit_input:
                weight_unit = "kg"
                break
            elif unit_input in ["kg", "lbs"]:
                weight_unit = unit_input
                break
            else:
                print("❌ Please enter 'kg' or 'lbs'")

        print(f"⚖️ Adding weigh-in: {weight} {weight_unit}")

        # Add a simple weigh-in
        result1 = api.add_weigh_in(weight=weight, unitKey=weight_unit)
        display_json(
            f"api.add_weigh_in(weight={weight}, unitKey={weight_unit})", result1
        )

        # Add a weigh-in with timestamps for yesterday
        import datetime
        from datetime import timezone

        yesterday = config.today - datetime.timedelta(days=1)  # Get yesterday's date
        weigh_in_date = datetime.datetime.strptime(yesterday.isoformat(), "%Y-%m-%d")
        local_timestamp = weigh_in_date.strftime("%Y-%m-%dT%H:%M:%S")
        gmt_timestamp = weigh_in_date.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )

        result2 = api.add_weigh_in_with_timestamps(
            weight=weight,
            unitKey=weight_unit,
            dateTimestamp=local_timestamp,
            gmtTimestamp=gmt_timestamp,
        )

        display_json(
            f"api.add_weigh_in_with_timestamps(weight={weight}, unitKey={weight_unit}, dateTimestamp={local_timestamp}, gmtTimestamp={gmt_timestamp})",
            result2,
        )

        print("✅ Weigh-in data added successfully!")

    except Exception as e:
        print(f"❌ Error adding weigh-in: {e}")


# Helper functions for the new API methods
def get_lactate_threshold_data(api: Garmin) -> None:
    """Get lactate threshold data."""
    try:
        # Get latest lactate threshold
        latest = api.get_lactate_threshold(latest=True)
        display_json("api.get_lactate_threshold(latest=True)", latest)

        # Get historical lactate threshold for past four weeks
        four_weeks_ago = config.today - datetime.timedelta(days=28)
        historical = api.get_lactate_threshold(
            latest=False,
            start_date=four_weeks_ago.isoformat(),
            end_date=config.today.isoformat(),
            aggregation="daily",
        )
        display_json(
            f"api.get_lactate_threshold(latest=False, start_date='{four_weeks_ago.isoformat()}', end_date='{config.today.isoformat()}', aggregation='daily')",
            historical,
        )
    except Exception as e:
        print(f"❌ Error getting lactate threshold data: {e}")


def get_activity_splits_data(api: Garmin) -> None:
    """Get activity splits for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            splits = api.get_activity_splits(activity_id)
            display_json(f"api.get_activity_splits({activity_id})", splits)
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity splits: {e}")


def get_activity_typed_splits_data(api: Garmin) -> None:
    """Get activity typed splits for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            typed_splits = api.get_activity_typed_splits(activity_id)
            display_json(f"api.get_activity_typed_splits({activity_id})", typed_splits)
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity typed splits: {e}")


def get_activity_split_summaries_data(api: Garmin) -> None:
    """Get activity split summaries for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            summaries = api.get_activity_split_summaries(activity_id)
            display_json(f"api.get_activity_split_summaries({activity_id})", summaries)
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity split summaries: {e}")


def get_activity_weather_data(api: Garmin) -> None:
    """Get activity weather data for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            weather = api.get_activity_weather(activity_id)
            display_json(f"api.get_activity_weather({activity_id})", weather)
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity weather: {e}")


def get_activity_hr_timezones_data(api: Garmin) -> None:
    """Get activity heart rate timezones for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            hr_zones = api.get_activity_hr_in_timezones(activity_id)
            display_json(f"api.get_activity_hr_in_timezones({activity_id})", hr_zones)
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity HR timezones: {e}")


def get_activity_details_data(api: Garmin) -> None:
    """Get detailed activity information for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            details = api.get_activity_details(activity_id)
            display_json(f"api.get_activity_details({activity_id})", details)
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity details: {e}")


def get_activity_gear_data(api: Garmin) -> None:
    """Get activity gear information for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            gear = api.get_activity_gear(activity_id)
            display_json(f"api.get_activity_gear({activity_id})", gear)
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity gear: {e}")


def get_single_activity_data(api: Garmin) -> None:
    """Get single activity data for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            activity = api.get_activity(activity_id)
            display_json(f"api.get_activity({activity_id})", activity)
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting single activity: {e}")


def get_activity_exercise_sets_data(api: Garmin) -> None:
    """Get exercise sets for strength training activities."""
    try:
        activities = api.get_activities(
            0, 20
        )  # Get more activities to find a strength training one
        strength_activity = None

        # Find strength training activities
        for activity in activities:
            activity_type = activity.get("activityType", {})
            type_key = activity_type.get("typeKey", "")
            if "strength" in type_key.lower() or "training" in type_key.lower():
                strength_activity = activity
                break

        if strength_activity:
            activity_id = strength_activity["activityId"]
            exercise_sets = api.get_activity_exercise_sets(activity_id)
            display_json(
                f"api.get_activity_exercise_sets({activity_id})", exercise_sets
            )
        else:
            # Return empty JSON response
            display_json("api.get_activity_exercise_sets()", {})
    except Exception:
        display_json("api.get_activity_exercise_sets()", {})


def get_workout_by_id_data(api: Garmin) -> None:
    """Get workout by ID for the last workout."""
    try:
        workouts = api.get_workouts()
        if workouts:
            workout_id = workouts[-1]["workoutId"]
            workout_name = workouts[-1]["workoutName"]
            workout = api.get_workout_by_id(workout_id)
            display_json(
                f"api.get_workout_by_id({workout_id}) - {workout_name}", workout
            )
        else:
            print("ℹ️ No workouts found")
    except Exception as e:
        print(f"❌ Error getting workout by ID: {e}")


def download_workout_data(api: Garmin) -> None:
    """Download workout to .FIT file."""
    try:
        workouts = api.get_workouts()
        if workouts:
            workout_id = workouts[-1]["workoutId"]
            workout_name = workouts[-1]["workoutName"]

            print(f"📥 Downloading workout: {workout_name}")
            workout_data = api.download_workout(workout_id)

            if workout_data:
                output_file = config.export_dir / f"{workout_name}_{workout_id}.fit"
                with open(output_file, "wb") as f:
                    f.write(workout_data)
                print(f"✅ Workout downloaded to: {output_file}")
            else:
                print("❌ No workout data available")
        else:
            print("ℹ️ No workouts found")
    except Exception as e:
        print(f"❌ Error downloading workout: {e}")


def upload_workout_data(api: Garmin) -> None:
    """Upload workout from JSON file."""
    try:
        print(f"📤 Uploading workout from file: {config.workoutfile}")

        # Check if file exists
        if not os.path.exists(config.workoutfile):
            print(f"❌ File not found: {config.workoutfile}")
            print(
                "ℹ️ Please ensure the workout JSON file exists in the test_data directory"
            )
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
                for _key, value in workout_segments.items():
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

        print(f"📤 Uploading workout: {workout_data['workoutName']}")

        # Upload the workout
        result = api.upload_workout(workout_data)

        if result:
            print("✅ Workout uploaded successfully!")
            display_json("api.upload_workout(workout_data)", result)
        else:
            print(f"❌ Failed to upload workout from {config.workoutfile}")

    except FileNotFoundError:
        print(f"❌ File not found: {config.workoutfile}")
        print("ℹ️ Please ensure the workout JSON file exists in the test_data directory")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format in {config.workoutfile}: {e}")
        print("ℹ️ Please check the JSON file format")
    except Exception as e:
        print(f"❌ Error uploading workout: {e}")
        # Check for common upload errors
        error_str = str(e)
        if "400" in error_str:
            print("💡 The workout data may be invalid or malformed")
        elif "401" in error_str:
            print("💡 Authentication failed - please login again")
        elif "403" in error_str:
            print("💡 Permission denied - check account permissions")
        elif "409" in error_str:
            print("💡 Workout may already exist")
        elif "422" in error_str:
            print("💡 Workout data validation failed")


def set_body_composition_data(api: Garmin) -> None:
    """Set body composition data."""
    try:
        print(f"⚖️ Setting body composition data for {config.today.isoformat()}")
        print("-" * 50)

        # Get weight input from user
        while True:
            try:
                weight_str = input(
                    "Enter weight in kg (30-300, default: 85.1): "
                ).strip()
                if not weight_str:
                    weight = 85.1
                    break
                weight = float(weight_str)
                if 30 <= weight <= 300:
                    break
                else:
                    print("❌ Weight must be between 30 and 300 kg")
            except ValueError:
                print("❌ Please enter a valid number")

        result = api.set_body_composition(
            timestamp=config.today.isoformat(),
            weight=weight,
            percent_fat=15.4,
            percent_hydration=54.8,
            bone_mass=2.9,
            muscle_mass=55.2,
        )
        display_json(
            f"api.set_body_composition({config.today.isoformat()}, weight={weight}, ...)",
            result,
        )
        print("✅ Body composition data set successfully!")
    except Exception as e:
        print(f"❌ Error setting body composition: {e}")


def add_body_composition_data(api: Garmin) -> None:
    """Add body composition data."""
    try:
        print(f"⚖️ Adding body composition data for {config.today.isoformat()}")
        print("-" * 50)

        # Get weight input from user
        while True:
            try:
                weight_str = input(
                    "Enter weight in kg (30-300, default: 85.1): "
                ).strip()
                if not weight_str:
                    weight = 85.1
                    break
                weight = float(weight_str)
                if 30 <= weight <= 300:
                    break
                else:
                    print("❌ Weight must be between 30 and 300 kg")
            except ValueError:
                print("❌ Please enter a valid number")

        result = api.add_body_composition(
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
        )
        display_json(
            f"api.add_body_composition({config.today.isoformat()}, weight={weight}, ...)",
            result,
        )
        print("✅ Body composition data added successfully!")
    except Exception as e:
        print(f"❌ Error adding body composition: {e}")


def delete_weigh_ins_data(api: Garmin) -> None:
    """Delete all weigh-ins for today."""
    try:
        result = api.delete_weigh_ins(config.today.isoformat(), delete_all=True)
        display_json(
            f"api.delete_weigh_ins({config.today.isoformat()}, delete_all=True)", result
        )
        print("✅ Weigh-ins deleted successfully!")
    except Exception as e:
        print(f"❌ Error deleting weigh-ins: {e}")


def delete_weigh_in_data(api: Garmin) -> None:
    """Delete a specific weigh-in."""
    try:
        all_weigh_ins = []

        # Find weigh-ins
        print(f"🔍 Checking daily weigh-ins for today ({config.today.isoformat()})...")
        try:
            daily_weigh_ins = api.get_daily_weigh_ins(config.today.isoformat())

            if daily_weigh_ins and "dateWeightList" in daily_weigh_ins:
                weight_list = daily_weigh_ins["dateWeightList"]
                for weigh_in in weight_list:
                    if isinstance(weigh_in, dict):
                        all_weigh_ins.append(weigh_in)
                print(f"📊 Found {len(all_weigh_ins)} weigh-in(s) for today")
            else:
                print("📊 No weigh-in data found in response")
        except Exception as e:
            print(f"⚠️ Could not fetch daily weigh-ins: {e}")

        if not all_weigh_ins:
            print("ℹ️ No weigh-ins found for today")
            print("💡 You can add a test weigh-in using menu option [4]")
            return

        print(f"\n⚖️ Found {len(all_weigh_ins)} weigh-in(s) available for deletion:")
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

            print(f"  [{i}] {weight} {unit} on {date} at {time_str}")

        print()
        try:
            selection = input(
                "Enter the index of the weigh-in to delete (or 'q' to cancel): "
            ).strip()

            if selection.lower() == "q":
                print("❌ Delete cancelled")
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
                        f"Delete weigh-in {weight} {unit} from {date}? (yes/no): "
                    ).lower()
                    if confirm == "yes":
                        result = api.delete_weigh_in(
                            weigh_in_id, config.today.isoformat()
                        )
                        display_json(
                            f"api.delete_weigh_in({weigh_in_id}, {config.today.isoformat()})",
                            result,
                        )
                        print("✅ Weigh-in deleted successfully!")
                    else:
                        print("❌ Delete cancelled")
                else:
                    print("❌ No weigh-in ID found for selected entry")
            else:
                print("❌ Invalid selection")

        except ValueError:
            print("❌ Invalid input - please enter a number")

    except Exception as e:
        print(f"❌ Error deleting weigh-in: {e}")


def get_device_settings_data(api: Garmin) -> None:
    """Get device settings for all devices."""
    try:
        devices = api.get_devices()
        if devices:
            for device in devices:
                device_id = device["deviceId"]
                device_name = device.get("displayName", f"Device {device_id}")
                try:
                    settings = api.get_device_settings(device_id)
                    display_json(
                        f"api.get_device_settings({device_id}) - {device_name}",
                        settings,
                    )
                except Exception as e:
                    print(f"❌ Error getting settings for device {device_name}: {e}")
        else:
            print("ℹ️ No devices found")
    except Exception as e:
        print(f"❌ Error getting device settings: {e}")


def get_gear_data(api: Garmin) -> None:
    """Get user gear list."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear = api.get_gear(user_profile_number)
            display_json(f"api.get_gear({user_profile_number})", gear)
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error getting gear: {e}")


def get_gear_defaults_data(api: Garmin) -> None:
    """Get gear defaults."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            defaults = api.get_gear_defaults(user_profile_number)
            display_json(f"api.get_gear_defaults({user_profile_number})", defaults)
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error getting gear defaults: {e}")


def get_gear_stats_data(api: Garmin) -> None:
    """Get gear statistics."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear = api.get_gear(user_profile_number)
            if gear:
                for gear_item in gear[:3]:  # Limit to first 3 items
                    gear_uuid = gear_item.get("uuid")
                    gear_name = gear_item.get("displayName", "Unknown")
                    if gear_uuid:
                        stats = api.get_gear_stats(gear_uuid)
                        display_json(
                            f"api.get_gear_stats({gear_uuid}) - {gear_name}", stats
                        )
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error getting gear stats: {e}")


def get_gear_activities_data(api: Garmin) -> None:
    """Get gear activities."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear = api.get_gear(user_profile_number)
            if gear:
                gear_uuid = gear[0].get("uuid")
                gear_name = gear[0].get("displayName", "Unknown")
                if gear_uuid:
                    activities = api.get_gear_activities(gear_uuid)
                    display_json(
                        f"api.get_gear_activities({gear_uuid}) - {gear_name}",
                        activities,
                    )
                else:
                    print("❌ No gear UUID found")
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error getting gear activities: {e}")


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
                    result = api.set_gear_default(activity_type, gear_uuid, True)
                    display_json(
                        f"api.set_gear_default({activity_type}, '{gear_uuid}', True) - {gear_name} for running",
                        result,
                    )
                    print("✅ Gear default set successfully!")
                else:
                    print("❌ No gear UUID found")
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error setting gear default: {e}")


def set_activity_name_data(api: Garmin) -> None:
    """Set activity name."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            print(f"Current name of fetched activity: {activities[0]['activityName']}")
            new_name = input("Enter new activity name: (or 'q' to cancel): ").strip()

            if new_name.lower() == "q":
                print("❌ Rename cancelled")
                return

            if new_name:
                result = api.set_activity_name(activity_id, new_name)
                display_json(
                    f"api.set_activity_name({activity_id}, '{new_name}')", result
                )
                print("✅ Activity name updated!")
            else:
                print("❌ No name provided")
        else:
            print("❌ No activities found")
    except Exception as e:
        print(f"❌ Error setting activity name: {e}")


def set_activity_type_data(api: Garmin) -> None:
    """Set activity type."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            activity_types = api.get_activity_types()

            # Show available types
            print("\nAvailable activity types: (limit=10)")
            for i, activity_type in enumerate(activity_types[:10]):  # Show first 10
                print(
                    f"{i}: {activity_type.get('typeKey', 'Unknown')} - {activity_type.get('display', 'No description')}"
                )

            try:
                print(
                    f"Current type of fetched activity '{activities[0]['activityName']}': {activities[0]['activityType']['typeKey']}"
                )
                type_index = input(
                    "Enter activity type index: (or 'q' to cancel): "
                ).strip()

                if type_index.lower() == "q":
                    print("❌ Type change cancelled")
                    return

                type_index = int(type_index)
                if 0 <= type_index < len(activity_types):
                    selected_type = activity_types[type_index]
                    type_id = selected_type["typeId"]
                    type_key = selected_type["typeKey"]
                    parent_type_id = selected_type.get(
                        "parentTypeId", selected_type["typeId"]
                    )

                    result = api.set_activity_type(
                        activity_id, type_id, type_key, parent_type_id
                    )
                    display_json(
                        f"api.set_activity_type({activity_id}, {type_id}, '{type_key}', {parent_type_id})",
                        result,
                    )
                    print("✅ Activity type updated!")
                else:
                    print("❌ Invalid index")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("❌ No activities found")
    except Exception as e:
        print(f"❌ Error setting activity type: {e}")


def create_manual_activity_data(api: Garmin) -> None:
    """Create manual activity."""
    try:
        print("Creating manual activity...")
        print("Enter activity details (press Enter for defaults):")

        activity_name = (
            input("Activity name [Manual Activity]: ").strip() or "Manual Activity"
        )
        type_key = input("Activity type key [running]: ").strip() or "running"
        duration_min = input("Duration in minutes [60]: ").strip() or "60"
        distance_km = input("Distance in kilometers [5]: ").strip() or "5"
        timezone = input("Timezone [UTC]: ").strip() or "UTC"

        try:
            duration_min = float(duration_min)
            distance_km = float(distance_km)

            # Use the current time as start time
            import datetime

            start_datetime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.00")

            result = api.create_manual_activity(
                start_datetime=start_datetime,
                time_zone=timezone,
                type_key=type_key,
                distance_km=distance_km,
                duration_min=duration_min,
                activity_name=activity_name,
            )
            display_json(
                f"api.create_manual_activity(start_datetime='{start_datetime}', time_zone='{timezone}', type_key='{type_key}', distance_km={distance_km}, duration_min={duration_min}, activity_name='{activity_name}')",
                result,
            )
            print("✅ Manual activity created!")
        except ValueError:
            print("❌ Invalid numeric input")
    except Exception as e:
        print(f"❌ Error creating manual activity: {e}")


def delete_activity_data(api: Garmin) -> None:
    """Delete activity."""
    try:
        activities = api.get_activities(0, 5)
        if activities:
            print("\nRecent activities:")
            for i, activity in enumerate(activities):
                activity_name = activity.get("activityName", "Unnamed")
                activity_id = activity.get("activityId")
                start_time = activity.get("startTimeLocal", "Unknown time")
                print(f"{i}: {activity_name} ({activity_id}) - {start_time}")

            try:
                activity_index = input(
                    "Enter activity index to delete: (or 'q' to cancel): "
                ).strip()

                if activity_index.lower() == "q":
                    print("❌ Delete cancelled")
                    return
                activity_index = int(activity_index)
                if 0 <= activity_index < len(activities):
                    activity_id = activities[activity_index]["activityId"]
                    activity_name = activities[activity_index].get(
                        "activityName", "Unnamed"
                    )

                    confirm = input(f"Delete '{activity_name}'? (yes/no): ").lower()
                    if confirm == "yes":
                        result = api.delete_activity(activity_id)
                        display_json(f"api.delete_activity({activity_id})", result)
                        print("✅ Activity deleted!")
                    else:
                        print("❌ Delete cancelled")
                else:
                    print("❌ Invalid index")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("❌ No activities found")
    except Exception as e:
        print(f"❌ Error deleting activity: {e}")


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
            print(f"\n📊 Found {len(entry_list)} blood pressure entries:")
            print("-" * 70)
            for i, (entry_id, display_text, _measurement_date) in enumerate(entry_list):
                print(f"  [{i}] {display_text} (ID: {entry_id})")

            try:
                entry_index = input(
                    "\nEnter entry index to delete: (or 'q' to cancel): "
                ).strip()

                if entry_index.lower() == "q":
                    print("❌ Entry deletion cancelled")
                    return

                entry_index = int(entry_index)
                if 0 <= entry_index < len(entry_list):
                    entry_id, display_text, measurement_date = entry_list[entry_index]
                    confirm = input(
                        f"Delete entry '{display_text}'? (yes/no): "
                    ).lower()
                    if confirm == "yes":
                        result = api.delete_blood_pressure(entry_id, measurement_date)
                        display_json(
                            f"api.delete_blood_pressure('{entry_id}', '{measurement_date}')",
                            result,
                        )
                        print("✅ Blood pressure entry deleted!")
                    else:
                        print("❌ Delete cancelled")
                else:
                    print("❌ Invalid index")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("❌ No blood pressure entries found for past week")
            print("💡 You can add a test measurement using menu option [3]")

    except Exception as e:
        print(f"❌ Error deleting blood pressure: {e}")


def query_garmin_graphql_data(api: Garmin) -> None:
    """Execute GraphQL query with a menu of available queries."""
    try:
        print("Available GraphQL queries:")
        print("  [1] Activities (recent activities with details)")
        print("  [2] Health Snapshot (comprehensive health data)")
        print("  [3] Weight Data (weight measurements)")
        print("  [4] Blood Pressure (blood pressure data)")
        print("  [5] Sleep Summaries (sleep analysis)")
        print("  [6] Heart Rate Variability (HRV data)")
        print("  [7] User Daily Summary (comprehensive daily stats)")
        print("  [8] Training Readiness (training readiness metrics)")
        print("  [9] Training Status (training status data)")
        print("  [10] Activity Stats (aggregated activity statistics)")
        print("  [11] VO2 Max (VO2 max data)")
        print("  [12] Endurance Score (endurance scoring)")
        print("  [13] User Goals (current goals)")
        print("  [14] Stress Data (epoch chart with stress)")
        print("  [15] Badge Challenges (available challenges)")
        print("  [16] Adhoc Challenges (adhoc challenges)")
        print("  [c] Custom query")

        choice = input("\nEnter choice (1-16, c): ").strip()

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
            print("\nEnter your custom GraphQL query:")
            print("Example: query{userGoalsScalar}")
            query = input("Query: ").strip()
        else:
            print("❌ Invalid choice")
            return

        if query:
            # GraphQL API expects a dictionary with the query as a string value
            graphql_payload = {"query": query}
            result = api.query_garmin_graphql(graphql_payload)
            display_json(f"api.query_garmin_graphql({graphql_payload})", result)
        else:
            print("❌ No query provided")
    except Exception as e:
        print(f"❌ Error executing GraphQL query: {e}")


def get_virtual_challenges_data(api: Garmin) -> None:
    """Get virtual challenges data with fallback to available alternatives."""
    print("🏆 Attempting to get virtual challenges data...")

    # Try in-progress virtual challenges first
    try:
        print("📋 Trying in-progress virtual challenges...")
        challenges = api.get_inprogress_virtual_challenges(
            config.week_start.isoformat(), 10
        )
        if challenges:
            display_json(
                f"api.get_inprogress_virtual_challenges('{config.week_start.isoformat()}', 10)",
                challenges,
            )
            return
        else:
            print("ℹ️ No in-progress virtual challenges found")
    except Exception as e:
        print(f"⚠️ In-progress virtual challenges not available: {e}")


def add_hydration_data_entry(api: Garmin) -> None:
    """Add hydration data entry."""
    try:
        import datetime

        value_in_ml = 240
        raw_date = config.today
        cdate = str(raw_date)
        raw_ts = datetime.datetime.now()
        timestamp = datetime.datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

        result = api.add_hydration_data(
            value_in_ml=value_in_ml, cdate=cdate, timestamp=timestamp
        )
        display_json(
            f"api.add_hydration_data(value_in_ml={value_in_ml}, cdate='{cdate}', timestamp='{timestamp}')",
            result,
        )
        print("✅ Hydration data added successfully!")
    except Exception as e:
        print(f"❌ Error adding hydration data: {e}")


def set_blood_pressure_data(api: Garmin) -> None:
    """Set blood pressure (and pulse) data."""
    try:
        print("🩸 Adding blood pressure (and pulse) measurement")
        print("Enter blood pressure values (press Enter for defaults):")

        # Get systolic pressure
        systolic_input = input("Systolic pressure [120]: ").strip()
        systolic = int(systolic_input) if systolic_input else 120

        # Get diastolic pressure
        diastolic_input = input("Diastolic pressure [80]: ").strip()
        diastolic = int(diastolic_input) if diastolic_input else 80

        # Get pulse
        pulse_input = input("Pulse rate [60]: ").strip()
        pulse = int(pulse_input) if pulse_input else 60

        # Get notes (optional)
        notes = input("Notes (optional): ").strip() or "Added via example.py"

        # Validate ranges
        if not (50 <= systolic <= 300):
            print("❌ Invalid systolic pressure (should be between 50-300)")
            return
        if not (30 <= diastolic <= 200):
            print("❌ Invalid diastolic pressure (should be between 30-200)")
            return
        if not (30 <= pulse <= 250):
            print("❌ Invalid pulse rate (should be between 30-250)")
            return

        print(f"📊 Recording: {systolic}/{diastolic} mmHg, pulse {pulse} bpm")

        result = api.set_blood_pressure(systolic, diastolic, pulse, notes=notes)
        display_json(
            f"api.set_blood_pressure({systolic}, {diastolic}, {pulse}, notes='{notes}')",
            result,
        )
        print("✅ Blood pressure data set successfully!")

    except ValueError:
        print("❌ Invalid input - please enter numeric values")
    except Exception as e:
        print(f"❌ Error setting blood pressure: {e}")


def track_gear_usage_data(api: Garmin) -> None:
    """Calculate total time of use of a piece of gear by going through all activities where said gear has been used."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear_list = api.get_gear(user_profile_number)
            # display_json(f"api.get_gear({user_profile_number})", gear_list)
            if gear_list and isinstance(gear_list, list):
                first_gear = gear_list[0]
                gear_uuid = first_gear.get("uuid")
                gear_name = first_gear.get("displayName", "Unknown")
                print(f"Tracking usage for gear: {gear_name} (UUID: {gear_uuid})")
                activityList = api.get_gear_activities(gear_uuid)
                if len(activityList) == 0:
                    print("No activities found for the given gear uuid.")
                else:
                    print("Found " + str(len(activityList)) + " activities.")

                D = 0
                for a in activityList:
                    print(
                        "Activity: "
                        + a["startTimeLocal"]
                        + (" | " + a["activityName"] if a["activityName"] else "")
                    )
                    print(
                        "  Duration: "
                        + format_timedelta(datetime.timedelta(seconds=a["duration"]))
                    )
                    D += a["duration"]
                print("")
                print(
                    "Total Duration: " + format_timedelta(datetime.timedelta(seconds=D))
                )
                print("")
            else:
                print("No gear found for this user.")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error getting gear for track_gear_usage_data: {e}")


def execute_api_call(api: Garmin, key: str) -> None:
    """Execute an API call based on the key."""
    if not api:
        print("API not available")
        return

    try:
        # Map of keys to API methods - this can be extended as needed
        api_methods = {
            # User & Profile
            "get_full_name": lambda: display_json(
                "api.get_full_name()", api.get_full_name()
            ),
            "get_unit_system": lambda: display_json(
                "api.get_unit_system()", api.get_unit_system()
            ),
            "get_user_profile": lambda: display_json(
                "api.get_user_profile()", api.get_user_profile()
            ),
            "get_userprofile_settings": lambda: display_json(
                "api.get_userprofile_settings()", api.get_userprofile_settings()
            ),
            # Daily Health & Activity
            "get_stats": lambda: display_json(
                f"api.get_stats('{config.today.isoformat()}')",
                api.get_stats(config.today.isoformat()),
            ),
            "get_user_summary": lambda: display_json(
                f"api.get_user_summary('{config.today.isoformat()}')",
                api.get_user_summary(config.today.isoformat()),
            ),
            "get_stats_and_body": lambda: display_json(
                f"api.get_stats_and_body('{config.today.isoformat()}')",
                api.get_stats_and_body(config.today.isoformat()),
            ),
            "get_steps_data": lambda: display_json(
                f"api.get_steps_data('{config.today.isoformat()}')",
                api.get_steps_data(config.today.isoformat()),
            ),
            "get_heart_rates": lambda: display_json(
                f"api.get_heart_rates('{config.today.isoformat()}')",
                api.get_heart_rates(config.today.isoformat()),
            ),
            "get_resting_heart_rate": lambda: display_json(
                f"api.get_rhr_day('{config.today.isoformat()}')",
                api.get_rhr_day(config.today.isoformat()),
            ),
            "get_sleep_data": lambda: display_json(
                f"api.get_sleep_data('{config.today.isoformat()}')",
                api.get_sleep_data(config.today.isoformat()),
            ),
            "get_all_day_stress": lambda: display_json(
                f"api.get_all_day_stress('{config.today.isoformat()}')",
                api.get_all_day_stress(config.today.isoformat()),
            ),
            # Advanced Health Metrics
            "get_training_readiness": lambda: display_json(
                f"api.get_training_readiness('{config.today.isoformat()}')",
                api.get_training_readiness(config.today.isoformat()),
            ),
            "get_training_status": lambda: display_json(
                f"api.get_training_status('{config.today.isoformat()}')",
                api.get_training_status(config.today.isoformat()),
            ),
            "get_respiration_data": lambda: display_json(
                f"api.get_respiration_data('{config.today.isoformat()}')",
                api.get_respiration_data(config.today.isoformat()),
            ),
            "get_spo2_data": lambda: display_json(
                f"api.get_spo2_data('{config.today.isoformat()}')",
                api.get_spo2_data(config.today.isoformat()),
            ),
            "get_max_metrics": lambda: display_json(
                f"api.get_max_metrics('{config.today.isoformat()}')",
                api.get_max_metrics(config.today.isoformat()),
            ),
            "get_hrv_data": lambda: display_json(
                f"api.get_hrv_data('{config.today.isoformat()}')",
                api.get_hrv_data(config.today.isoformat()),
            ),
            "get_fitnessage_data": lambda: display_json(
                f"api.get_fitnessage_data('{config.today.isoformat()}')",
                api.get_fitnessage_data(config.today.isoformat()),
            ),
            "get_stress_data": lambda: display_json(
                f"api.get_stress_data('{config.today.isoformat()}')",
                api.get_stress_data(config.today.isoformat()),
            ),
            "get_lactate_threshold": lambda: get_lactate_threshold_data(api),
            "get_intensity_minutes_data": lambda: display_json(
                f"api.get_intensity_minutes_data('{config.today.isoformat()}')",
                api.get_intensity_minutes_data(config.today.isoformat()),
            ),
            # Historical Data & Trends
            "get_daily_steps": lambda: display_json(
                f"api.get_daily_steps('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
                api.get_daily_steps(
                    config.week_start.isoformat(), config.today.isoformat()
                ),
            ),
            "get_body_battery": lambda: display_json(
                f"api.get_body_battery('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
                api.get_body_battery(
                    config.week_start.isoformat(), config.today.isoformat()
                ),
            ),
            "get_floors": lambda: display_json(
                f"api.get_floors('{config.week_start.isoformat()}')",
                api.get_floors(config.week_start.isoformat()),
            ),
            "get_blood_pressure": lambda: display_json(
                f"api.get_blood_pressure('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
                api.get_blood_pressure(
                    config.week_start.isoformat(), config.today.isoformat()
                ),
            ),
            "get_progress_summary_between_dates": lambda: display_json(
                f"api.get_progress_summary_between_dates('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
                api.get_progress_summary_between_dates(
                    config.week_start.isoformat(), config.today.isoformat()
                ),
            ),
            "get_body_battery_events": lambda: display_json(
                f"api.get_body_battery_events('{config.week_start.isoformat()}')",
                api.get_body_battery_events(config.week_start.isoformat()),
            ),
            # Activities & Workouts
            "get_activities": lambda: display_json(
                f"api.get_activities({config.start}, {config.default_limit})",
                api.get_activities(config.start, config.default_limit),
            ),
            "get_last_activity": lambda: display_json(
                "api.get_last_activity()", api.get_last_activity()
            ),
            "get_activities_fordate": lambda: display_json(
                f"api.get_activities_fordate('{config.today.isoformat()}')",
                api.get_activities_fordate(config.today.isoformat()),
            ),
            "get_activity_types": lambda: display_json(
                "api.get_activity_types()", api.get_activity_types()
            ),
            "get_workouts": lambda: display_json(
                "api.get_workouts()", api.get_workouts()
            ),
            "upload_activity": lambda: upload_activity_file(api),
            "download_activities": lambda: download_activities_by_date(api),
            "get_activity_splits": lambda: get_activity_splits_data(api),
            "get_activity_typed_splits": lambda: get_activity_typed_splits_data(api),
            "get_activity_split_summaries": lambda: get_activity_split_summaries_data(
                api
            ),
            "get_activity_weather": lambda: get_activity_weather_data(api),
            "get_activity_hr_in_timezones": lambda: get_activity_hr_timezones_data(api),
            "get_activity_details": lambda: get_activity_details_data(api),
            "get_activity_gear": lambda: get_activity_gear_data(api),
            "get_activity": lambda: get_single_activity_data(api),
            "get_activity_exercise_sets": lambda: get_activity_exercise_sets_data(api),
            "get_workout_by_id": lambda: get_workout_by_id_data(api),
            "download_workout": lambda: download_workout_data(api),
            "upload_workout": lambda: upload_workout_data(api),
            # Body Composition & Weight
            "get_body_composition": lambda: display_json(
                f"api.get_body_composition('{config.today.isoformat()}')",
                api.get_body_composition(config.today.isoformat()),
            ),
            "get_weigh_ins": lambda: display_json(
                f"api.get_weigh_ins('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
                api.get_weigh_ins(
                    config.week_start.isoformat(), config.today.isoformat()
                ),
            ),
            "get_daily_weigh_ins": lambda: display_json(
                f"api.get_daily_weigh_ins('{config.today.isoformat()}')",
                api.get_daily_weigh_ins(config.today.isoformat()),
            ),
            "add_weigh_in": lambda: add_weigh_in_data(api),
            "set_body_composition": lambda: set_body_composition_data(api),
            "add_body_composition": lambda: add_body_composition_data(api),
            "delete_weigh_ins": lambda: delete_weigh_ins_data(api),
            "delete_weigh_in": lambda: delete_weigh_in_data(api),
            # Goals & Achievements
            "get_personal_records": lambda: display_json(
                "api.get_personal_record()", api.get_personal_record()
            ),
            "get_earned_badges": lambda: display_json(
                "api.get_earned_badges()", api.get_earned_badges()
            ),
            "get_adhoc_challenges": lambda: display_json(
                f"api.get_adhoc_challenges({config.start}, {config.default_limit})",
                api.get_adhoc_challenges(config.start, config.default_limit),
            ),
            "get_available_badge_challenges": lambda: display_json(
                f"api.get_available_badge_challenges({config.start_badge}, {config.default_limit})",
                api.get_available_badge_challenges(
                    config.start_badge, config.default_limit
                ),
            ),
            "get_active_goals": lambda: display_json(
                f"api.get_goals(status='active', start={config.start}, limit={config.default_limit})",
                api.get_goals(
                    status="active", start=config.start, limit=config.default_limit
                ),
            ),
            "get_future_goals": lambda: display_json(
                f"api.get_goals(status='future', start={config.start}, limit={config.default_limit})",
                api.get_goals(
                    status="future", start=config.start, limit=config.default_limit
                ),
            ),
            "get_past_goals": lambda: display_json(
                f"api.get_goals(status='past', start={config.start}, limit={config.default_limit})",
                api.get_goals(
                    status="past", start=config.start, limit=config.default_limit
                ),
            ),
            "get_badge_challenges": lambda: display_json(
                f"api.get_badge_challenges({config.start_badge}, {config.default_limit})",
                api.get_badge_challenges(config.start_badge, config.default_limit),
            ),
            "get_non_completed_badge_challenges": lambda: display_json(
                f"api.get_non_completed_badge_challenges({config.start_badge}, {config.default_limit})",
                api.get_non_completed_badge_challenges(
                    config.start_badge, config.default_limit
                ),
            ),
            "get_inprogress_virtual_challenges": lambda: get_virtual_challenges_data(
                api
            ),
            "get_race_predictions": lambda: display_json(
                "api.get_race_predictions()", api.get_race_predictions()
            ),
            "get_hill_score": lambda: display_json(
                f"api.get_hill_score('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
                api.get_hill_score(
                    config.week_start.isoformat(), config.today.isoformat()
                ),
            ),
            "get_endurance_score": lambda: display_json(
                f"api.get_endurance_score('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
                api.get_endurance_score(
                    config.week_start.isoformat(), config.today.isoformat()
                ),
            ),
            "get_available_badges": lambda: display_json(
                "api.get_available_badges()", api.get_available_badges()
            ),
            "get_in_progress_badges": lambda: display_json(
                "api.get_in_progress_badges()", api.get_in_progress_badges()
            ),
            # Device & Technical
            "get_devices": lambda: display_json("api.get_devices()", api.get_devices()),
            "get_device_alarms": lambda: display_json(
                "api.get_device_alarms()", api.get_device_alarms()
            ),
            "get_solar_data": lambda: get_solar_data(api),
            "request_reload": lambda: display_json(
                f"api.request_reload('{config.today.isoformat()}')",
                api.request_reload(config.today.isoformat()),
            ),
            "get_device_settings": lambda: get_device_settings_data(api),
            "get_device_last_used": lambda: display_json(
                "api.get_device_last_used()", api.get_device_last_used()
            ),
            "get_primary_training_device": lambda: display_json(
                "api.get_primary_training_device()", api.get_primary_training_device()
            ),
            # Gear & Equipment
            "get_gear": lambda: get_gear_data(api),
            "get_gear_defaults": lambda: get_gear_defaults_data(api),
            "get_gear_stats": lambda: get_gear_stats_data(api),
            "get_gear_activities": lambda: get_gear_activities_data(api),
            "set_gear_default": lambda: set_gear_default_data(api),
            "track_gear_usage": lambda: track_gear_usage_data(api),
            # Hydration & Wellness
            "get_hydration_data": lambda: display_json(
                f"api.get_hydration_data('{config.today.isoformat()}')",
                api.get_hydration_data(config.today.isoformat()),
            ),
            "get_pregnancy_summary": lambda: display_json(
                "api.get_pregnancy_summary()", api.get_pregnancy_summary()
            ),
            "get_all_day_events": lambda: display_json(
                f"api.get_all_day_events('{config.week_start.isoformat()}')",
                api.get_all_day_events(config.week_start.isoformat()),
            ),
            "add_hydration_data": lambda: add_hydration_data_entry(api),
            "set_blood_pressure": lambda: set_blood_pressure_data(api),
            "get_menstrual_data_for_date": lambda: display_json(
                f"api.get_menstrual_data_for_date('{config.today.isoformat()}')",
                api.get_menstrual_data_for_date(config.today.isoformat()),
            ),
            "get_menstrual_calendar_data": lambda: display_json(
                f"api.get_menstrual_calendar_data('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
                api.get_menstrual_calendar_data(
                    config.week_start.isoformat(), config.today.isoformat()
                ),
            ),
            # Blood Pressure Management
            "delete_blood_pressure": lambda: delete_blood_pressure_data(api),
            # Activity Management
            "set_activity_name": lambda: set_activity_name_data(api),
            "set_activity_type": lambda: set_activity_type_data(api),
            "create_manual_activity": lambda: create_manual_activity_data(api),
            "delete_activity": lambda: delete_activity_data(api),
            "get_activities_by_date": lambda: display_json(
                f"api.get_activities_by_date('{config.today.isoformat()}', '{config.today.isoformat()}')",
                api.get_activities_by_date(
                    config.today.isoformat(), config.today.isoformat()
                ),
            ),
            # System & Export
            "create_health_report": lambda: DataExporter.create_health_report(api),
            "remove_tokens": lambda: remove_stored_tokens(),
            "disconnect": lambda: disconnect_api(api),
            # GraphQL Queries
            "query_garmin_graphql": lambda: query_garmin_graphql_data(api),
        }

        if key in api_methods:
            print(f"\n🔄 Executing: {key}")
            api_methods[key]()
        else:
            print(f"❌ API method '{key}' not implemented yet. You can add it later!")

    except Exception as e:
        print(f"❌ Error executing {key}: {e}")


def remove_stored_tokens():
    """Remove stored login tokens."""
    try:
        import os
        import shutil

        token_path = os.path.expanduser(config.tokenstore)
        if os.path.isdir(token_path):
            shutil.rmtree(token_path)
            print("✅ Stored login tokens directory removed")
        else:
            print("ℹ️ No stored login tokens found")
    except Exception as e:
        print(f"❌ Error removing stored login tokens: {e}")


def disconnect_api(api: Garmin):
    """Disconnect from Garmin Connect."""
    api.logout()
    print("✅ Disconnected from Garmin Connect")


def init_api(email: str | None = None, password: str | None = None) -> Garmin | None:
    """Initialize Garmin API with smart error handling and recovery."""
    try:
        print(f"Attempting to login using stored tokens from: {config.tokenstore}")

        garmin = Garmin()
        garmin.login(config.tokenstore)
        print("Successfully logged in using stored tokens!")
        return garmin

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        print("No valid tokens found. Requesting fresh login credentials.")

        try:
            # Get credentials if not provided
            if not email or not password:
                email = input("Email address: ").strip()
                password = getpass("Password: ")

            print("Logging in with credentials...")
            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()

            if result1 == "needs_mfa":
                print("Multi-factor authentication required")
                mfa_code = get_mfa()
                garmin.resume_login(result2, mfa_code)

            # Save tokens for future use
            garmin.garth.dump(config.tokenstore)
            print(f"Login successful! Tokens saved to: {config.tokenstore}")

            return garmin

        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            print(f"Login failed: {err}")
            return None


def main():
    """Main program loop with funny health status in menu prompt."""
    # Display export directory information on startup
    print(f"📁 Exported data will be saved to the directory: '{config.export_dir}'")
    print("📄 All API responses are written to: 'response.json'")

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
                        steps = summary.get("totalSteps", 0)
                        calories = summary.get("totalKilocalories", 0)

                        # Build stats string with hydration if available
                        stats_parts = [f"{steps:,} steps", f"{calories} kcal"]

                        if hydration_data and hydration_data.get("valueInML"):
                            hydration_ml = int(hydration_data.get("valueInML", 0))
                            hydration_cups = round(hydration_ml / 240, 1)
                            hydration_goal = hydration_data.get("goalInML", 0)

                            if hydration_goal > 0:
                                hydration_percent = round(
                                    (hydration_ml / hydration_goal) * 100
                                )
                                stats_parts.append(
                                    f"{hydration_ml}ml water ({hydration_percent}% of goal)"
                                )
                            else:
                                stats_parts.append(
                                    f"{hydration_ml}ml water ({hydration_cups} cups)"
                                )

                        stats_string = " | ".join(stats_parts)
                        print(f"\n📊 Your Stats Today: {stats_string}")

                        if steps < 5000:
                            print("🐌 Time to get those legs moving!")
                        elif steps > 15000:
                            print("🏃‍♂️ You're crushing it today!")
                        else:
                            print("👍 Nice progress! Keep it up!")
                except Exception:
                    # Silently skip if stats can't be fetched
                    pass

            # Display appropriate menu
            if current_category is None:
                print_main_menu()
                option = readchar.readkey()

                # Handle main menu options
                if option == "q":
                    print("Be active, generate some data to fetch next time ;-) Bye!")
                    break
                elif option in menu_categories:
                    current_category = option
                else:
                    print(
                        f"❌ Invalid selection. Use {', '.join(menu_categories.keys())} for categories or 'q' to quit"
                    )
            else:
                # In a category - show category menu
                print_category_menu(current_category)
                option = readchar.readkey()

                # Handle category menu options
                if option == "q":
                    current_category = None  # Back to main menu
                elif option in "0123456789abcdefghijklmnopqrstuvwxyz":
                    try:
                        category_data = menu_categories[current_category]
                        category_options = category_data["options"]
                        if option in category_options:
                            api_key = category_options[option]["key"]
                            execute_api_call(api_instance, api_key)
                        else:
                            valid_keys = ", ".join(category_options.keys())
                            print(
                                f"❌ Invalid option selection. Valid options: {valid_keys}"
                            )
                    except Exception as e:
                        print(f"❌ Error processing option {option}: {e}")
                else:
                    print(
                        "❌ Invalid selection. Use numbers/letters for options or 'q' to go back/quit"
                    )

        except KeyboardInterrupt:
            print("\nInterrupted by user. Press q to quit.")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
