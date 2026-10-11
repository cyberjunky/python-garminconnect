"""Unit tests for Supabase garmin_tokens synchronization and auth integration.

Covers:
- get_garmin_tokens_from_supabase and upsert_garmin_tokens_to_supabase
- Non-destructive validation for empty/invalid token payloads (REQ-005)
- restore_tokens_from_supabase and persist_tokens_to_supabase in scripts.garmin_auth
- login_client integration with Supabase restore and persist flows
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from garminconnect.client import token_file_path
from scripts.garmin_auth import (
    login_client,
    persist_tokens_to_supabase,
    restore_tokens_from_supabase,
)
from services.collector.supabase_client import (
    DEFAULT_USER_ID,
    get_garmin_tokens_from_supabase,
    upsert_garmin_tokens_to_supabase,
)


def test_get_garmin_tokens_from_supabase_success():
    mock_client = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [
        {
            "token_data": {
                "di_token": "jwt_access_123",
                "di_refresh_token": "refresh_456",
                "di_client_id": "CLIENT_ID",
            }
        }
    ]
    (
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute
    ) = MagicMock(return_value=mock_execute)

    with patch("services.collector.supabase_client.get_supabase", return_value=mock_client):
        tokens = get_garmin_tokens_from_supabase(DEFAULT_USER_ID)

    assert tokens is not None
    assert tokens["di_token"] == "jwt_access_123"
    assert tokens["di_refresh_token"] == "refresh_456"
    assert tokens["di_client_id"] == "CLIENT_ID"
    mock_client.table.assert_called_with("garmin_tokens")


def test_get_garmin_tokens_from_supabase_not_found():
    mock_client = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = []
    (
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute
    ) = MagicMock(return_value=mock_execute)

    with patch("services.collector.supabase_client.get_supabase", return_value=mock_client):
        tokens = get_garmin_tokens_from_supabase(DEFAULT_USER_ID)

    assert tokens is None


def test_upsert_garmin_tokens_to_supabase_success():
    mock_client = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [{"user_id": DEFAULT_USER_ID, "status": "ok"}]
    mock_client.table.return_value.upsert.return_value.execute.return_value = mock_execute

    valid_payload = {
        "di_token": "jwt_access_123",
        "di_refresh_token": "refresh_456",
        "di_client_id": "CLIENT_ID",
    }

    with patch("services.collector.supabase_client.get_supabase", return_value=mock_client):
        res = upsert_garmin_tokens_to_supabase(valid_payload, user_id=DEFAULT_USER_ID)

    assert res is not None
    mock_client.table.assert_called_with("garmin_tokens")
    call_args = mock_client.table.return_value.upsert.call_args
    assert call_args[0][0]["user_id"] == DEFAULT_USER_ID
    assert call_args[0][0]["token_data"] == valid_payload
    assert "updated_at" in call_args[0][0]
    assert call_args[1]["on_conflict"] == "user_id"


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {},
        None,
        "not-a-dict",
        [],
        {"random_key": "some_value"},
        {"di_token": ""},
        {"di_refresh_token": ""},
        {"di_token": "", "di_refresh_token": ""},
        {"di_token": None, "di_refresh_token": None},
        {"di_token": "   ", "di_refresh_token": "   "},
    ],
)
def test_upsert_garmin_tokens_req005_nondestructive_validation(invalid_payload):
    mock_client = MagicMock()

    with patch("services.collector.supabase_client.get_supabase", return_value=mock_client):
        res = upsert_garmin_tokens_to_supabase(invalid_payload)

    assert res is None
    # Must NOT call Supabase table or upsert when payload is invalid (REQ-005)
    mock_client.table.assert_not_called()


def test_restore_tokens_from_supabase_success(tmp_path):
    tokens = {
        "di_token": "tok_restore",
        "di_refresh_token": "ref_restore",
        "di_client_id": "cid_restore",
    }
    store_dir = tmp_path / "tokens"

    with patch(
        "services.collector.supabase_client.get_garmin_tokens_from_supabase",
        return_value=tokens,
    ):
        ok = restore_tokens_from_supabase(dest_store=str(store_dir))

    assert ok is True
    target_file = token_file_path(str(store_dir))
    assert target_file.is_file()
    saved = json.loads(target_file.read_text(encoding="utf-8"))
    assert saved["di_token"] == "tok_restore"
    assert saved["di_refresh_token"] == "ref_restore"
    assert saved["di_client_id"] == "cid_restore"


def test_restore_tokens_from_supabase_empty_or_error(tmp_path):
    store_dir = tmp_path / "tokens"

    with patch(
        "services.collector.supabase_client.get_garmin_tokens_from_supabase",
        return_value=None,
    ):
        ok = restore_tokens_from_supabase(dest_store=str(store_dir))

    assert ok is False
    assert not (store_dir / "garmin_tokens.json").exists()


def test_persist_tokens_to_supabase_success(tmp_path):
    store_dir = tmp_path / "tokens"
    target_file = token_file_path(str(store_dir))
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(
        json.dumps({"di_token": "tok_save", "di_refresh_token": "ref_save"}),
        encoding="utf-8",
    )

    with patch(
        "services.collector.supabase_client.upsert_garmin_tokens_to_supabase",
        return_value={"status": "ok"},
    ) as mock_upsert:
        ok = persist_tokens_to_supabase(src_store=str(store_dir))

    assert ok is True
    mock_upsert.assert_called_once_with(
        {"di_token": "tok_save", "di_refresh_token": "ref_save"}
    )


def test_persist_tokens_to_supabase_no_file(tmp_path):
    store_dir = tmp_path / "nonexistent"
    ok = persist_tokens_to_supabase(src_store=str(store_dir))
    assert ok is False


def test_login_client_restores_from_supabase_when_no_local_tokens(tmp_path):
    store_dir = tmp_path / "tokens"

    mock_garmin = MagicMock()
    mock_garmin.login.return_value = (None, None)

    with (
        patch("scripts.garmin_auth.tokenstore_path", return_value=str(store_dir)),
        patch("scripts.garmin_auth.restore_tokens_from_supabase", return_value=True) as mock_restore,
        patch("scripts.garmin_auth.persist_tokens_to_supabase", return_value=True) as mock_persist,
        patch("scripts.garmin_auth.Garmin", return_value=mock_garmin),
    ):
        client = login_client(prompt=False)

    assert client is mock_garmin
    mock_restore.assert_called_once_with(str(store_dir))
    mock_garmin.login.assert_called_once_with(str(store_dir))
    mock_persist.assert_called_once_with(str(store_dir))


def test_login_client_persists_after_credential_login(tmp_path):
    store_dir = tmp_path / "tokens"

    mock_client_token_fail = MagicMock()
    mock_client_token_fail.login.side_effect = Exception("No local tokens")

    mock_client_cred_success = MagicMock()
    mock_client_cred_success.login.return_value = (None, None)

    with (
        patch("scripts.garmin_auth.tokenstore_path", return_value=str(store_dir)),
        patch("scripts.garmin_auth.restore_tokens_from_supabase", return_value=False) as mock_restore,
        patch("scripts.garmin_auth.persist_tokens_to_supabase", return_value=True) as mock_persist,
        patch(
            "scripts.garmin_auth.Garmin",
            side_effect=[mock_client_token_fail, mock_client_cred_success],
        ),
        patch(
            "scripts.garmin_auth.get_credentials",
            return_value=("user@example.com", "pass123"),
        ),
    ):
        client = login_client(prompt=False)

    assert client is mock_client_cred_success
    mock_restore.assert_called_once_with(str(store_dir))
    mock_client_cred_success.login.assert_called_once_with(str(store_dir))
    mock_persist.assert_called_once_with(str(store_dir))


def test_refresh_garmin_session_persists_tokens_after_session_ok(capsys):
    from scripts.refresh_garmin_session import main as refresh_main

    mock_client = MagicMock()
    mock_client.get_user_summary.return_value = {
        "totalSteps": 8500,
        "totalKilocalories": 2100,
        "totalDistanceMeters": 6000,
    }

    with (
        patch("scripts.refresh_garmin_session.login_client", return_value=mock_client),
        patch("scripts.refresh_garmin_session.persist_tokens_to_supabase", return_value=True) as mock_persist,
    ):
        code = refresh_main()

    assert code == 0
    mock_persist.assert_called_once()
    captured = capsys.readouterr()
    assert "SESSION_OK" in captured.out
    assert "SUPABASE_TOKENS_OK" in captured.out


def test_workflow_coaching_daily_collect_token_sync_config():
    from pathlib import Path
    import yaml

    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/coaching-daily-collect.yml"
    assert workflow_path.is_file()
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    steps = data["jobs"]["collect"]["steps"]
    step_names = {s.get("name"): s for s in steps}

    restore_step = step_names.get("Restore Garmin tokens")
    assert restore_step is not None
    assert "SUPABASE_URL" in restore_step.get("env", {})
    assert "SUPABASE_SERVICE_ROLE_KEY" in restore_step.get("env", {})
    assert "restore_tokens_from_supabase" in restore_step.get("run", "")
    assert "GARMINTOKENS_B64" in restore_step.get("run", "")

    collect_step = step_names.get("Collect and upsert to Supabase")
    assert collect_step is not None
    assert "SUPABASE_URL" in collect_step.get("env", {})
    assert "persist_tokens_to_supabase" in collect_step.get("run", "")


def test_publish_garmin_tokens_secret_script_has_supabase_sync():
    from pathlib import Path

    script_path = Path(__file__).resolve().parents[1] / "scripts/publish_garmin_tokens_secret.sh"
    assert script_path.is_file()
    content = script_path.read_text(encoding="utf-8")

    assert "persist_tokens_to_supabase" in content
    assert "SUPABASE_URL" in content
    assert "SUPABASE_SERVICE_ROLE_KEY" in content
    assert ".env.local" in content
