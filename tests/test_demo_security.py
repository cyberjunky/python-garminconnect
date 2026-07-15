"""Security regression tests for demo exports."""

import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.modules.setdefault("readchar", SimpleNamespace(readkey=lambda: "q"))

import demo  # noqa: E402


def test_health_report_escapes_garmin_data_and_is_private(tmp_path, monkeypatch):
    monkeypatch.setattr(demo.config, "export_dir", tmp_path)
    payload = '<script>alert("health-data")</script>'
    report_path = Path(
        demo.DataExporter.create_readable_health_report(
            {
                "generated_at": payload,
                "user_info": {"full_name": payload},
                "recent_activities": [
                    {
                        "activityName": payload,
                        "activityType": {"typeKey": payload},
                    }
                ],
                "device_info": [{"displayName": payload}],
            }
        )
    )

    report = report_path.read_text()
    assert payload not in report
    assert "&lt;script&gt;" in report
    if sys.platform != "win32":
        assert stat.S_IMODE(report_path.stat().st_mode) == 0o600


def test_save_json_cannot_escape_export_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(demo.config, "export_dir", tmp_path)

    export_path = Path(demo.DataExporter.save_json({"private": True}, "../../outside"))

    assert export_path.parent == tmp_path
    assert export_path.name == "_.._outside.json"
    assert not (tmp_path.parent / "outside.json").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes only")
def test_config_tightens_export_directory_permissions(tmp_path, monkeypatch):
    export_dir = tmp_path / "your_data"
    export_dir.mkdir(mode=0o755)
    export_dir.chmod(0o755)
    monkeypatch.chdir(tmp_path)

    config = demo.Config()

    assert stat.S_IMODE(config.export_dir.stat().st_mode) == 0o700
