"""Regression tests for demo.py's interactive gear/activity-filter helpers."""

import sys
from types import SimpleNamespace

sys.modules.setdefault("readchar", SimpleNamespace(readkey=lambda: "q"))  # type: ignore[arg-type]

import demo  # noqa: E402


class _FakeAPI:
    def __init__(self):
        self.activity_types = [
            {"typeId": 1, "typeKey": "running", "display": "Running"},
            {
                "typeId": 2,
                "typeKey": "fitness_equipment",
                "display": "Fitness Equipment",
            },
        ]
        self.get_activities_calls: list[dict] = []
        self.create_gear_calls: list[dict] = []
        self.create_gear_result: dict | None = {"uuid": "new-gear"}

    def get_activity_types(self):
        return self.activity_types

    def get_activities(self, start, limit, **kwargs):
        self.get_activities_calls.append({"start": start, "limit": limit, **kwargs})
        return []

    def create_gear(self, **kwargs):
        self.create_gear_calls.append(kwargs)
        if self.create_gear_result is None:
            raise ValueError("rejected by server")
        return self.create_gear_result


def _typed_inputs(*values):
    it = iter(values)
    return lambda prompt="": next(it)


def test_negative_activity_type_index_is_rejected(monkeypatch, capsys):
    """A negative index is valid Python list indexing (selects from the end)
    but must not silently apply an unintended filter.
    """
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs("-1"))

    demo.get_activities_filtered_data(api)

    assert api.get_activities_calls == [
        {"start": 0, "limit": 100, "activitytype": None, "activitysubtype": None}
    ]
    assert "Invalid index" in capsys.readouterr().out


def test_out_of_range_activity_type_index_is_rejected(monkeypatch):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs("99"))

    demo.get_activities_filtered_data(api)

    assert api.get_activities_calls[0]["activitytype"] is None


def test_valid_activity_type_index_applies_filter(monkeypatch):
    api = _FakeAPI()
    monkeypatch.setattr("builtins.input", _typed_inputs("0", ""))

    demo.get_activities_filtered_data(api)

    assert api.get_activities_calls[0]["activitytype"] == "running"


def test_create_gear_success_message_only_on_success(monkeypatch, capsys):
    api = _FakeAPI()
    monkeypatch.setattr(
        "builtins.input", _typed_inputs("", "", "", "", "", "", "", "", "")
    )

    demo.create_gear_data(api)

    assert "✅ Gear created!" in capsys.readouterr().out


def test_create_gear_no_success_message_when_request_fails(monkeypatch, capsys):
    """call_and_display() returns (False, None) on a rejected/failed request —
    the success message must not print unconditionally.
    """
    api = _FakeAPI()
    api.create_gear_result = None
    monkeypatch.setattr(
        "builtins.input", _typed_inputs("", "", "", "", "", "", "", "", "")
    )

    demo.create_gear_data(api)

    assert "✅ Gear created!" not in capsys.readouterr().out
