#!/usr/bin/env python3
"""Upload and schedule a weekend readiness plan to Garmin Connect.

Default schedule (relative to --start-date):
- Fri: walk Z1-Z2
- Sat: run Z2
- Sun: road bike Z2
- Mon: rest (not scheduled)
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from garmin_auth import login_client

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from garminconnect.workout import (
    CyclingWorkout,
    RunningWorkout,
    WalkingWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_interval_step,
    create_warmup_step,
)


@dataclass(frozen=True)
class ScheduledWorkout:
    day: date
    key: str
    upload: str


def build_workouts() -> dict[str, WalkingWorkout | RunningWorkout | CyclingWorkout]:
    walk = WalkingWorkout(
        workoutName="Caminata Z1-Z2 45min",
        estimatedDurationInSecs=2700,
        description=(
            "Readiness plan. FC 100-127 bpm, techo 128. RPE 2-3. "
            "5 min calentamiento + 35 min constante + 5 min vuelta a la calma."
        ),
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 4,
                    "sportTypeKey": "walking",
                    "displayOrder": 4,
                },
                workoutSteps=[
                    create_warmup_step(300.0, step_order=1),
                    create_interval_step(2100.0, step_order=2),
                    create_cooldown_step(300.0, step_order=3),
                ],
            )
        ],
    )

    run = RunningWorkout(
        workoutName="Running Z2 48min",
        estimatedDurationInSecs=2880,
        description=(
            "Readiness plan. FC 115-135 bpm, techo 141. Sin calidad. "
            "5 min calentamiento + 38 min Z2 + 5 min enfriamiento."
        ),
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 1,
                    "sportTypeKey": "running",
                    "displayOrder": 1,
                },
                workoutSteps=[
                    create_warmup_step(300.0, step_order=1),
                    create_interval_step(2280.0, step_order=2),
                    create_cooldown_step(300.0, step_order=3),
                ],
            )
        ],
    )

    bike = CyclingWorkout(
        workoutName="Road Bike Z2 80min",
        estimatedDurationInSecs=4800,
        description=(
            "Readiness plan. FC 115-138 bpm, techo 141. Rodado Z2. "
            "10 min calentamiento + 60 min constante + 10 min vuelta a la calma."
        ),
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 2,
                    "sportTypeKey": "cycling",
                    "displayOrder": 2,
                },
                workoutSteps=[
                    create_warmup_step(600.0, step_order=1),
                    create_interval_step(3600.0, step_order=2),
                    create_cooldown_step(600.0, step_order=3),
                ],
            )
        ],
    )

    return {"walk": walk, "run": run, "bike": bike}


def weekend_schedule(start: date) -> list[ScheduledWorkout]:
    """Build Fri-Sun schedule from the Friday of the week containing start."""
    # Align to Friday of the week: weekday 4 = Friday
    days_until_friday = (4 - start.weekday()) % 7
    friday = start + timedelta(days=days_until_friday)
    return [
        ScheduledWorkout(friday, "walk", "upload_walking_workout"),
        ScheduledWorkout(friday + timedelta(days=1), "run", "upload_running_workout"),
        ScheduledWorkout(friday + timedelta(days=2), "bike", "upload_cycling_workout"),
    ]


def upload_and_schedule(
    api: Garmin, start: date, dry_run: bool
) -> list[tuple[str, str, int]]:
    workouts = build_workouts()
    upload_methods = {
        "walk": api.upload_walking_workout,
        "run": api.upload_running_workout,
        "bike": api.upload_cycling_workout,
    }
    log: list[tuple[str, str, int]] = []

    for item in weekend_schedule(start):
        workout = workouts[item.key]
        day_str = item.day.isoformat()

        if dry_run:
            print(
                f"[DRY-RUN] Would upload and schedule {workout.workoutName} on {day_str}"
            )
            log.append((day_str, workout.workoutName, -1))
            continue

        result = upload_methods[item.key](workout)
        workout_id = int(result["workoutId"])
        api.schedule_workout(workout_id, day_str)
        print(f"Scheduled {workout.workoutName} on {day_str} (workoutId={workout_id})")
        log.append((day_str, workout.workoutName, workout_id))

    return log


def push_to_device(api: Garmin, workout_ids: list[int], dry_run: bool) -> None:
    unique_ids = sorted({wid for wid in workout_ids if wid > 0})
    if not unique_ids:
        return

    device_id = int(api.get_device_last_used()["userDeviceId"])
    if dry_run:
        print(f"[DRY-RUN] Would push {len(unique_ids)} workouts to device {device_id}")
        return

    for wid in unique_ids:
        api.push_workout_to_device(wid, device_id)
        print(f"Pushed workoutId={wid} to deviceId={device_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--start-date",
        default=date.today().isoformat(),
        help="Reference date; schedules Fri-Sun of that week (default: today)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without uploading"
    )
    parser.add_argument("--skip-push", action="store_true", help="Do not push to watch")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = date.fromisoformat(args.start_date)
    api = login_client(prompt=False)
    log = upload_and_schedule(api, start, dry_run=args.dry_run)

    if not args.skip_push:
        push_to_device(api, [wid for _, _, wid in log], dry_run=args.dry_run)

    rest_day = weekend_schedule(start)[-1].day + timedelta(days=1)
    print("\nWeekend plan summary")
    print("--------------------")
    for day_str, name, wid in log:
        print(f"{day_str} | {name} | workoutId={wid}")
    print(f"{rest_day.isoformat()} | REST | (not scheduled)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GarminConnectTooManyRequestsError as exc:
        print(f"Rate limit from Garmin: {exc}")
        raise SystemExit(2) from exc
    except GarminConnectAuthenticationError as exc:
        print(f"Authentication error: {exc}")
        raise SystemExit(3) from exc
    except GarminConnectConnectionError as exc:
        print(f"Connection error: {exc}")
        raise SystemExit(4) from exc
