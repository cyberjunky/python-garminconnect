"""Request-shape tests for the endpoints mapped from the Garmin Connect web app.

These tests stub the client so no network access happens; they pin the exact
path and query parameters each method sends, which is what matters for
compatibility with Garmin's undocumented API.
"""

from datetime import date

import pytest

from garminconnect import Garmin


class _Recorder:
    def __init__(self, result=None):
        self.calls: list[tuple[str, str, dict]] = []
        self.result = result if result is not None else {}

    def connectapi(self, path, **kwargs):
        self.calls.append(("GET", path, kwargs))
        return self.result


@pytest.fixture
def api(monkeypatch) -> tuple[Garmin, _Recorder]:
    g = Garmin()
    g.display_name = "user-uuid"
    g.time_zone = "Europe/Amsterdam"
    rec = _Recorder()
    monkeypatch.setattr(g, "connectapi", rec.connectapi)
    monkeypatch.setattr(g, "today", lambda: date(2026, 10, 16))
    return g, rec


def _last(rec: _Recorder):
    return rec.calls[-1]


def test_daily_stats_sends_type_and_current_date(api):
    g, rec = api
    g.get_daily_stats("2026-10-01", "2026-10-16", "calories")
    _, path, kw = _last(rec)
    assert path == "/usersummary-service/stats/daily/2026-10-01/2026-10-16"
    assert kw["params"] == {"statsType": "CALORIES", "currentDate": "2026-10-16"}


def test_daily_stats_rejects_unknown_type(api):
    g, _ = api
    with pytest.raises(ValueError):
        g.get_daily_stats("2026-10-01", "2026-10-16", "FLOORS")


def test_weekly_weight_uses_364_day_inclusive_window(api):
    g, rec = api
    g.get_weekly_weight("2026-10-16")
    assert _last(rec)[1] == "/weight-service/weight/weeklyRange/2025-10-18/2026-10-16"


def test_weekly_blood_pressure_defaults_to_today(api):
    g, rec = api
    g.get_weekly_blood_pressure()
    assert (
        _last(rec)[1]
        == "/bloodpressure-service/bloodpressure/weeklyRange/2025-10-18/2026-10-16"
    )


def test_calendar_week_uses_zero_based_month(api):
    g, rec = api
    g.get_calendar_week("2026-10-16", first_day_of_week=1)
    assert _last(rec)[1] == "/calendar-service/year/2026/month/9/day/16/start/1"


def test_calendar_week_rejects_bad_first_day(api):
    g, _ = api
    with pytest.raises(ValueError):
        g.get_calendar_week("2026-10-16", first_day_of_week=7)


def test_search_activities_lowercases_bools_and_validates_dates(api):
    g, rec = api
    g.search_activities(
        0, 5, activityType="running", favorite=True, startDate="2026-01-01"
    )
    _, path, kw = _last(rec)
    assert path == "/activitylist-service/activities/search/activities"
    assert kw["params"] == {
        "start": 0,
        "limit": 5,
        "activityType": "running",
        "favorite": "true",
        "startDate": "2026-01-01",
    }
    with pytest.raises(ValueError):
        g.search_activities(startDate="01-01-2026")
    with pytest.raises(ValueError):
        g.search_activities(**{"bad key": 1})


def test_max_metrics_range_aggregation_and_sport(api):
    g, rec = api
    g.get_max_metrics_range(
        "2026-09-01", "2026-10-16", aggregation="weekly", sport="Running"
    )
    _, path, kw = _last(rec)
    assert path == "/metrics-service/metrics/maxmet/weekly/2026-09-01/2026-10-16"
    assert kw["params"] == {"sport": "running"}
    g.get_max_metrics_range("2026-09-01", "2026-10-16")
    assert (
        _last(rec)[1] == "/metrics-service/metrics/maxmet/daily/2026-09-01/2026-10-16"
    )


def test_weekly_training_status_uses_display_name(api):
    g, rec = api
    g.get_weekly_training_status("2026-09-01", "2026-10-16")
    _, path, kw = _last(rec)
    assert path == "/metrics-service/metrics/trainingstatus/weekly/user-uuid"
    assert kw["params"] == {
        "fromCalendarDate": "2026-09-01",
        "toCalendarDate": "2026-10-16",
    }


def test_personal_record_optional_params(api):
    g, rec = api
    g.get_personal_record()
    assert _last(rec)[2]["params"] is None
    g.get_personal_record(include_history=True, months=6)
    assert _last(rec)[2]["params"] == {"includeHistory": "true", "months": "6"}


def test_get_workouts_filters(api):
    g, rec = api
    g.get_workouts(
        0,
        10,
        my_workouts_only=True,
        order_by="update_date",
        order_seq="desc",
        sport_type_keys=["Running", "cycling"],
    )
    assert _last(rec)[2]["params"] == {
        "start": 0,
        "limit": 10,
        "myWorkoutsOnly": "true",
        "orderBy": "UPDATE_DATE",
        "orderSeq": "DESC",
        "sportTypeKey": ["running", "cycling"],
    }
    with pytest.raises(ValueError):
        g.get_workouts(order_by="RANDOM")


def test_training_plans_params_only_when_given(api):
    g, rec = api
    g.get_training_plans()
    assert _last(rec)[2]["params"] is None
    g.get_training_plans(limit=50, start=0, status="Scheduled")
    assert _last(rec)[2]["params"] == {
        "limit": "50",
        "start": "0",
        "status": "Scheduled",
    }


def test_menstrual_dayview_sends_today_date(api):
    g, rec = api
    g.get_menstrual_data_for_date("2026-10-10")
    _, path, kw = _last(rec)
    assert path.endswith("/menstrualcycle/dayview/2026-10-10")
    assert kw["params"] == {"todayDate": "2026-10-16"}


def test_adjacent_activities_combines_prev_and_next(api, monkeypatch):
    g, _ = api
    answers = {"prev": {"activityId": 1}, "next": {"activityId": None}}
    monkeypatch.setattr(
        g, "connectapi", lambda path, **kw: answers[path.rsplit("/", 1)[1]]
    )
    assert g.get_adjacent_activities(42) == {"previous": 1, "next": None}


def test_ecg_uses_ghs_host(api):
    g, rec = api
    g.get_ecg_daily("2026-10-01", "2026-10-16")
    _, path, kw = _last(rec)
    assert path == "https://ghs.garmin.com/ghs/ecg/v1/ecg/daily"
    assert kw["params"] == {"firstDay": "2026-10-01", "lastDay": "2026-10-16"}
    with pytest.raises(ValueError):
        g.get_ecg("../etc")


def test_client_accepts_only_garmin_hosts_for_absolute_urls():
    from garminconnect.client import Client

    c = Client(domain="garmin.com")
    seen = {}

    class _Sess:
        def request(self, method, url, headers=None, **kw):
            seen["url"] = url

            class R:
                status_code = 200
                content = b"{}"

                def json(self):
                    return {}

            return R()

    c._api_session = _Sess()
    c.get_api_headers = dict  # type: ignore[assignment]
    c._run_request("GET", "https://ghs.garmin.com/ghs/ecg/v1/ecg/daily")
    assert seen["url"] == "https://ghs.garmin.com/ghs/ecg/v1/ecg/daily"
    with pytest.raises(ValueError):
        c._run_request("GET", "https://evil.example.com/x")
    with pytest.raises(ValueError):
        c._run_request("GET", "https://ghs.garmin.com@evil.example.com/x")
