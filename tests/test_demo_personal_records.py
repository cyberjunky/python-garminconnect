"""Regression tests for demo.py's personal-records interactive helper."""

import sys
from types import SimpleNamespace

sys.modules.setdefault("readchar", SimpleNamespace(readkey=lambda: "q"))  # type: ignore[arg-type]

import demo  # noqa: E402


class _FakeAPI:
    def __init__(self):
        self.records = [
            {
                "typeId": 4,
                "activityType": "running",
                "value": 2400,
                "activityId": 111,
            },
            {"typeId": 7, "activityType": "running", "value": 5000},
            {"typeId": 12, "activityType": None, "value": 26246.0},
            {"typeId": 15, "activityType": None, "value": 1.0},
            {"typeId": 1, "activityType": "cycling", "value": 999},
            {"typeId": 99, "activityType": None, "value": 42.0},
        ]
        self.get_activity_calls: list[str] = []

    def get_personal_record(self):
        return self.records

    def get_activity(self, activity_id):
        self.get_activity_calls.append(activity_id)
        return {"activityId": activity_id}


def _typed_inputs(*values):
    it = iter(values)
    return lambda prompt="": next(it)


def test_decodes_running_time_record(monkeypatch, capsys):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs(""))

    demo.get_personal_records_data(api)

    out = capsys.readouterr().out
    assert "10 km — 40:00" in out
    assert "typeId=4, raw value=2400" in out


def test_decodes_running_distance_record(monkeypatch, capsys):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs(""))

    demo.get_personal_records_data(api)

    out = capsys.readouterr().out
    assert "Longest run — 5.00 km" in out


def test_decodes_step_count_record(monkeypatch, capsys):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs(""))

    demo.get_personal_records_data(api)

    out = capsys.readouterr().out
    assert "Most steps in a day — 26,246" in out


def test_decodes_goal_streak_singular_day(monkeypatch, capsys):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs(""))

    demo.get_personal_records_data(api)

    out = capsys.readouterr().out
    assert "Longest goal streak — 1 day " in out
    assert "1 days" not in out


def test_unconfirmed_types_are_shown_not_hidden(monkeypatch, capsys):
    """Records outside both confirmed typeId tables must still be printed
    in full (typeId + raw value), not dropped or given a made-up label.
    """
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs(""))

    demo.get_personal_records_data(api)

    out = capsys.readouterr().out
    assert (
        "Unconfirmed record type (typeId=1, activityType='cycling', raw value=999)"
        in out
    )
    assert (
        "Unconfirmed record type (typeId=99, activityType=None, raw value=42.0)" in out
    )


def test_looks_up_source_activity_by_index(monkeypatch):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs("0"))

    demo.get_personal_records_data(api)

    assert api.get_activity_calls == ["111"]


def test_negative_index_is_rejected(monkeypatch, capsys):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs("-1"))

    demo.get_personal_records_data(api)

    assert api.get_activity_calls == []
    assert "Invalid index" in capsys.readouterr().out


def test_entry_without_activity_id_is_reported(monkeypatch, capsys):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs("1"))

    demo.get_personal_records_data(api)

    assert api.get_activity_calls == []
    assert "no activityId" in capsys.readouterr().out
