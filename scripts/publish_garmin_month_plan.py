#!/usr/bin/env python3
"""Create and publish a date-range training plan to Garmin Connect.

This script:
1) logs in using saved tokens or credentials,
2) creates typed workouts,
3) uploads them to Garmin Connect,
4) schedules them on calendar dates,
5) pushes workouts to the last-used device (optional).

Plan rules baked in:
- Monday is always rest.
- Last 7 calendar days of each month are rest.
- Max 2 gym sessions per week (Tuesday and Friday templates).
 - Progressive load for 3-month outcomes: Thursday switches from mobility
     to threshold intervals after week 4.
"""

from __future__ import annotations

import argparse
import calendar
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

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
    StrengthWorkout,
    WalkingWorkout,
    WorkoutSegment,
    create_cooldown_step,
    create_interval_step,
    create_strength_set,
    create_warmup_step,
)


@dataclass(frozen=True)
class DayPlan:
    key: str
    name: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--start-date",
        type=str,
        default=date.today().isoformat(),
        help="Start date (YYYY-MM-DD), default: today",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD). If omitted, uses end of --year/--month",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=date.today().month,
        help="Fallback target month (1-12) when --end-date is omitted",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=date.today().year,
        help="Fallback target year when --end-date is omitted",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without uploading/scheduling",
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Do not push workouts to device",
    )
    return parser.parse_args()


def parse_iso_date(value: str) -> date:
    try:
        yyyy, mm, dd = value.split("-")
        return date(int(yyyy), int(mm), int(dd))
    except Exception as exc:
        raise ValueError(f"Invalid date '{value}', expected YYYY-MM-DD") from exc


def init_api() -> Garmin:
    return login_client()


def build_workouts() -> dict[str, Any]:
    gym_a = StrengthWorkout(
        workoutName="Gym A - Full Body 50min",
        estimatedDurationInSecs=0,
        description="Full body strength. RPE 6-7. 2-3 sets.",
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 5,
                    "sportTypeKey": "strength_training",
                    "displayOrder": 5,
                },
                workoutSteps=[
                    create_warmup_step(420.0, step_order=1),
                    create_strength_set(
                        "SQUAT", step_order=2, sets=3, reps=10, rest_seconds=90.0
                    ),
                    create_strength_set(
                        "BENCH_PRESS", step_order=5, sets=3, reps=10, rest_seconds=90.0
                    ),
                    create_strength_set(
                        "ROW",
                        step_order=8,
                        sets=3,
                        reps=10,
                        rest_seconds=90.0,
                        exercise_name="SEATED_CABLE_ROW",
                    ),
                    create_strength_set(
                        "PULL_UP",
                        step_order=11,
                        sets=3,
                        reps=10,
                        rest_seconds=90.0,
                        exercise_name="LAT_PULLDOWN",
                    ),
                ],
            )
        ],
    )

    gym_b = StrengthWorkout(
        workoutName="Gym B - Full Body 50min",
        estimatedDurationInSecs=0,
        description="Full body strength variant. RPE 6-7. 2-3 sets.",
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 5,
                    "sportTypeKey": "strength_training",
                    "displayOrder": 5,
                },
                workoutSteps=[
                    create_warmup_step(420.0, step_order=1),
                    create_strength_set(
                        "BENCH_PRESS", step_order=2, sets=4, reps=8, rest_seconds=120.0
                    ),
                    create_strength_set(
                        "ROW",
                        step_order=5,
                        sets=4,
                        reps=10,
                        rest_seconds=90.0,
                        exercise_name="SEATED_CABLE_ROW",
                    ),
                    create_strength_set(
                        "PULL_UP",
                        step_order=8,
                        sets=3,
                        reps=8,
                        rest_seconds=120.0,
                        exercise_name="LAT_PULLDOWN",
                    ),
                    create_strength_set(
                        "BENCH_PRESS", step_order=11, sets=3, reps=12, rest_seconds=90.0
                    ),
                ],
            )
        ],
    )

    z2_run = RunningWorkout(
        workoutName="Cardio Z2 50min",
        estimatedDurationInSecs=3000,
        description="Easy conversational aerobic run or jog-walk.",
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={
                    "sportTypeId": 1,
                    "sportTypeKey": "running",
                    "displayOrder": 1,
                },
                workoutSteps=[
                    create_warmup_step(600.0, step_order=1),
                    create_interval_step(2100.0, step_order=2),
                    create_cooldown_step(300.0, step_order=3),
                ],
            )
        ],
    )

    long_z2_ride = CyclingWorkout(
        workoutName="Cardio Largo Z2 75min",
        estimatedDurationInSecs=4500,
        description="Long aerobic endurance ride at easy steady effort.",
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
                    create_interval_step(3300.0, step_order=2),
                    create_cooldown_step(600.0, step_order=3),
                ],
            )
        ],
    )

    recovery_walk = WalkingWorkout(
        workoutName="Recuperacion Activa 35min",
        estimatedDurationInSecs=2100,
        description="Easy recovery walk and mobility focus.",
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
                    create_interval_step(1500.0, step_order=2),
                    create_cooldown_step(300.0, step_order=3),
                ],
            )
        ],
    )

    mobility_walk = WalkingWorkout(
        workoutName="Movilidad + Caminata 40min",
        estimatedDurationInSecs=2400,
        description="Low stress mobility and brisk walk.",
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
                    create_interval_step(1800.0, step_order=2),
                    create_cooldown_step(300.0, step_order=3),
                ],
            )
        ],
    )

    threshold_run = RunningWorkout(
        workoutName="Umbral 45min (4x4)",
        estimatedDurationInSecs=2700,
        description=(
            "Warm-up + 4x4 min a ritmo fuerte controlado con recuperaciones "
            "suaves. Enfocado en mejorar capacidad aerobica/metabolica."
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
                    create_warmup_step(600.0, step_order=1),
                    create_interval_step(960.0, step_order=2),
                    create_interval_step(840.0, step_order=3),
                    create_cooldown_step(300.0, step_order=4),
                ],
            )
        ],
    )

    return {
        "gym_a": gym_a,
        "z2": z2_run,
        "mobility": mobility_walk,
        "threshold": threshold_run,
        "gym_b": gym_b,
        "long": long_z2_ride,
        "recovery": recovery_walk,
    }


def upload_templates(
    api: Garmin, templates: dict[str, Any], dry_run: bool
) -> dict[str, int]:
    uploaded_ids: dict[str, int] = {}
    upload_method = {
        "gym_a": api.upload_strength_workout,
        "gym_b": api.upload_strength_workout,
        "z2": api.upload_running_workout,
        "mobility": api.upload_walking_workout,
        "threshold": api.upload_running_workout,
        "long": api.upload_cycling_workout,
        "recovery": api.upload_walking_workout,
    }

    for key, workout in templates.items():
        if dry_run:
            print(f"[DRY-RUN] Would upload template: {workout.workoutName}")
            uploaded_ids[key] = -1
            continue

        result = upload_method[key](workout)
        wid = int(result["workoutId"])
        uploaded_ids[key] = wid
        print(f"Uploaded {workout.workoutName} -> workoutId={wid}")

    return uploaded_ids


def last_week_start(year: int, month: int) -> date:
    month_last_day = calendar.monthrange(year, month)[1]
    end = date(year, month, month_last_day)
    return end - timedelta(days=6)


def is_last_week_of_month(d: date) -> bool:
    return d >= last_week_start(d.year, d.month)


def plan_for_day(d: date, program_start: date) -> DayPlan | None:
    if d.weekday() == 0:  # Monday
        return None
    if is_last_week_of_month(d):
        return None

    # Switch Thursday from mobility to threshold work after 4 weeks.
    in_build_phase = d >= (program_start + timedelta(days=28))

    weekday_map: dict[int, DayPlan] = {
        1: DayPlan("gym_a", "Gym A - Full Body"),
        2: DayPlan("z2", "Cardio Z2"),
        3: DayPlan(
            "threshold" if in_build_phase else "mobility",
            "Umbral 45min (4x4)" if in_build_phase else "Movilidad + Caminata",
        ),
        4: DayPlan("gym_b", "Gym B - Full Body"),
        5: DayPlan("long", "Cardio Largo Z2"),
        6: DayPlan("recovery", "Recuperacion Activa"),
    }
    return weekday_map.get(d.weekday())


def iter_dates(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def schedule_plan(
    api: Garmin,
    start_date: date,
    end_date: date,
    workout_ids: dict[str, int],
    dry_run: bool,
) -> list[tuple[str, str, str]]:
    if start_date > end_date:
        return []

    schedule_log: list[tuple[str, str, str]] = []

    for day in iter_dates(start_date, end_date):
        day_plan = plan_for_day(day, start_date)
        if day_plan is None:
            reason = "rest_day"
            if is_last_week_of_month(day):
                reason = "last_week_rest"
            schedule_log.append((day.isoformat(), "REST", reason))
            continue

        wid = workout_ids[day_plan.key]
        if dry_run:
            print(
                f"[DRY-RUN] Would schedule {day_plan.name} (workoutId={wid}) on {day.isoformat()}"
            )
        else:
            api.schedule_workout(wid, day.isoformat())
            print(f"Scheduled {day_plan.name} on {day.isoformat()} (workoutId={wid})")
        schedule_log.append((day.isoformat(), day_plan.name, str(wid)))

    return schedule_log


def push_workouts(api: Garmin, workout_ids: dict[str, int], dry_run: bool) -> None:
    unique_ids = sorted({wid for wid in workout_ids.values() if wid > 0})
    if not unique_ids:
        return

    device_id = int(api.get_device_last_used()["userDeviceId"])
    if dry_run:
        print(f"[DRY-RUN] Would push {len(unique_ids)} workouts to device {device_id}")
        return

    for wid in unique_ids:
        api.push_workout_to_device(wid, device_id)
        print(f"Pushed workoutId={wid} to deviceId={device_id}")


def main() -> int:
    args = parse_args()
    start_date = parse_iso_date(args.start_date)
    if args.end_date:
        end_date = parse_iso_date(args.end_date)
    else:
        year = int(args.year)
        month = int(args.month)
        if month < 1 or month > 12:
            raise ValueError("month must be in [1, 12]")
        month_last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, month_last_day)

    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    api = init_api()
    templates = build_workouts()
    workout_ids = upload_templates(api, templates, dry_run=args.dry_run)
    schedule = schedule_plan(
        api,
        start_date=start_date,
        end_date=end_date,
        workout_ids=workout_ids,
        dry_run=args.dry_run,
    )

    if not args.skip_push:
        push_workouts(api, workout_ids, dry_run=args.dry_run)

    print("\nPlan summary")
    print("------------")
    print(f"Range target: {start_date.isoformat()} -> {end_date.isoformat()}")
    print(f"Entries:      {len(schedule)}")
    print(f"Dry run:      {args.dry_run}")
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
