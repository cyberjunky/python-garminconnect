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
                "value": 2400.5,
                "activityId": 111,
            },
            {"typeId": 1, "activityType": "cycling", "value": 999},
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


def test_decodes_running_typeid_label(monkeypatch, capsys):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs(""))

    demo.get_personal_records_data(api)

    out = capsys.readouterr().out
    assert "typeId=4 (10 km)" in out
    # Non-running entries are shown undecoded, not mislabeled.
    assert "typeId=1 activityType='cycling'" in out


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
