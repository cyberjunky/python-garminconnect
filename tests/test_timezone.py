"""Tests for the user-timezone helpers and the defaults built on them."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from garminconnect import Garmin


class _FakeResp:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self._body = body

    def json(self) -> dict:
        return self._body


@pytest.fixture
def garmin(monkeypatch) -> Garmin:
    g = Garmin()
    g.display_name = "user-uuid"
    monkeypatch.setattr(
        g.client,
        "connectapi",
        lambda path, **kw: {"timeZone": "Pacific/Kiritimati", "locale": "en"},
    )
    return g


def test_not_logged_in_falls_back_to_machine_local_time():
    g = Garmin()
    assert g.get_user_timezone() is None
    assert g.now().utcoffset() == datetime.now().astimezone().utcoffset()
    # Bracket the call so a run across local midnight cannot fail.
    before = datetime.now().astimezone().date()
    result = g.today()
    assert result in {before, datetime.now().astimezone().date()}


def test_timezone_is_read_from_profile_and_cached(monkeypatch):
    g = Garmin()
    g.display_name = "user-uuid"
    calls: list[str] = []

    def fake_connectapi(path, **kw):
        calls.append(path)
        return {"timeZone": "Asia/Tokyo"}

    monkeypatch.setattr(g.client, "connectapi", fake_connectapi)
    assert g.get_user_timezone() == "Asia/Tokyo"
    assert g.get_user_timezone() == "Asia/Tokyo"
    assert calls == ["/userprofile-service/userprofile/personal-information/user-uuid"]


def test_today_and_now_use_profile_timezone(garmin: Garmin):
    # UTC+14 is the zone most likely to differ from the host's date.
    tz = ZoneInfo("Pacific/Kiritimati")
    assert garmin.now().tzinfo == tz
    before = datetime.now(tz).date()
    result = garmin.today()
    assert result in {before, datetime.now(tz).date()}


def test_failed_lookup_is_not_retried(monkeypatch):
    g = Garmin()
    g.display_name = "user-uuid"
    calls = 0

    def failing(path, **kw):
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    monkeypatch.setattr(g.client, "connectapi", failing)
    assert g.get_user_timezone() is None
    assert g.get_user_timezone() is None
    assert calls == 1
    # Falls back to machine local time instead of raising.
    # Bracket the call so a run across local midnight cannot fail.
    before = datetime.now().astimezone().date()
    result = g.today()
    assert result in {before, datetime.now().astimezone().date()}


def test_localize_keeps_aware_and_fixes_naive(garmin: Garmin):
    aware = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert garmin._localize(aware) is aware
    naive = datetime(2026, 1, 1, 12, 0)
    assert garmin._localize(naive).tzinfo == ZoneInfo("Pacific/Kiritimati")


def test_add_weigh_in_derives_gmt_from_profile_timezone(garmin: Garmin, monkeypatch):
    captured: dict = {}

    def fake_post(kind, url, **kw):
        captured.update(kw["json"])
        return _FakeResp(200, {"ok": True})

    monkeypatch.setattr(garmin.client, "post", fake_post)
    garmin.add_weigh_in(80.0, timestamp="2026-06-01T09:30:00")
    # Local wall time is kept; GMT is 14 hours earlier (UTC+14).
    assert captured["dateTimestamp"] == "2026-06-01T09:30:00.000"
    assert captured["gmtTimestamp"] == "2026-05-31T19:30:00.000"


def test_logout_clears_timezone(garmin: Garmin, monkeypatch):
    assert garmin.get_user_timezone() == "Pacific/Kiritimati"
    monkeypatch.setattr(garmin.client, "_clear_auth_state", lambda: None)
    garmin.logout(tokenstore='{"inline": "json"}')
    assert garmin.time_zone is None
    assert garmin.get_user_timezone() is None
