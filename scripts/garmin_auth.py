"""Garmin login helpers for repository scripts.

Credential resolution order:
1. Environment variables (GARMIN_EMAIL / GARMIN_PASSWORD)
2. macOS Keychain (service: python-garminconnect)
3. Repo-local .env.local (gitignored)
4. Optional interactive prompt
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from getpass import getpass
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from garminconnect import Garmin, GarminConnectAuthenticationError
from garminconnect.client import Client, token_file_path

if TYPE_CHECKING:
    from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)

KEYCHAIN_SERVICE = "python-garminconnect"
REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_LOCAL_PATH = REPO_ROOT / ".env.local"


def _load_env_local() -> dict[str, str]:
    if not ENV_LOCAL_PATH.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in ENV_LOCAL_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _load_keychain() -> tuple[str | None, str | None]:
    try:
        password_proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],  # noqa: S607 - macOS Keychain CLI
            capture_output=True,
            text=True,
            check=True,
        )
        account_proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE],  # noqa: S607 - macOS Keychain CLI
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None

    password = password_proc.stdout.strip()
    account = None
    for line in account_proc.stdout.splitlines():
        match = re.search(r'="([^"]+)"', line)
        if match and ("acct" in line or '"acct"' in line):
            account = match.group(1)
            break

    if account and password:
        return account, password
    return None, None


def save_credentials(email: str, password: str) -> None:
    """Persist Garmin credentials in macOS Keychain."""
    email = email.strip()
    password = password.strip()
    if not email or not password:
        raise ValueError("Email and password are required.")

    try:
        subprocess.run(  # noqa: S603 - fixed argv, no shell
            [  # noqa: S607 - macOS Keychain CLI
                "security",
                "add-generic-password",
                "-a",
                email,
                "-s",
                KEYCHAIN_SERVICE,
                "-w",
                password,
                "-U",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(f"Failed to save credentials to Keychain: {detail}") from exc


def credentials_configured() -> bool:
    """Return True when credentials are available without prompting."""
    try:
        get_credentials(prompt=False)
        return True
    except GarminConnectAuthenticationError:
        return False


def get_credentials(*, prompt: bool = True) -> tuple[str, str]:
    email = os.getenv("GARMIN_EMAIL") or os.getenv("EMAIL")
    password = os.getenv("GARMIN_PASSWORD") or os.getenv("PASSWORD")
    if email and password:
        return email.strip(), password

    keychain_email, keychain_password = _load_keychain()
    if keychain_email and keychain_password:
        return keychain_email, keychain_password

    env_local = _load_env_local()
    email = email or env_local.get("GARMIN_EMAIL") or env_local.get("EMAIL")
    password = password or env_local.get("GARMIN_PASSWORD") or env_local.get("PASSWORD")
    if email and password:
        return email.strip(), password.strip()

    if not prompt:
        raise GarminConnectAuthenticationError(
            "Garmin credentials not found. Run: "
            "./.venv/bin/python scripts/setup_garmin_credentials.py"
        )

    email = input("Garmin email: ").strip()
    password = getpass("Garmin password (hidden): ")
    if not email or not password:
        raise GarminConnectAuthenticationError("Email and password are required.")
    return email, password


def tokenstore_path() -> str:
    return str(Path(os.getenv("GARMINTOKENS", "~/.garminconnect")).expanduser())


def _ensure_env_local_in_os_environ() -> None:
    for k, v in _load_env_local().items():
        if k not in os.environ:
            os.environ[k] = v


def restore_tokens_from_supabase(dest_store: str | None = None) -> bool:
    """Restore Garmin tokens from Supabase to local store."""
    try:
        _ensure_env_local_in_os_environ()
        from services.collector.supabase_client import get_garmin_tokens_from_supabase

        tokens = get_garmin_tokens_from_supabase()
        if not tokens or not isinstance(tokens, dict):
            return False
        if not (tokens.get("di_token") or tokens.get("di_refresh_token")):
            return False

        store = dest_store or tokenstore_path()
        client = Client()
        client.di_token = tokens.get("di_token")
        client.di_refresh_token = tokens.get("di_refresh_token")
        client.di_client_id = tokens.get("di_client_id")
        client.dumps = lambda: json.dumps(tokens)
        client.dump(store)
        return True
    except Exception as exc:
        _LOGGER.debug("Failed to restore tokens from Supabase: %s", exc)
        return False


def persist_tokens_to_supabase(src_store: str | None = None) -> bool:
    """Persist local Garmin tokens to Supabase garmin_tokens table."""
    try:
        _ensure_env_local_in_os_environ()
        store = src_store or tokenstore_path()
        p = token_file_path(store)
        if not p.is_file():
            return False
        raw_text = p.read_text(encoding="utf-8")
        token_data = json.loads(raw_text)
        from services.collector.supabase_client import upsert_garmin_tokens_to_supabase

        res = upsert_garmin_tokens_to_supabase(token_data)
        return res is not None
    except Exception as exc:
        _LOGGER.debug("Failed to persist tokens to Supabase: %s", exc)
        return False


def login_client(
    *,
    prompt: bool = True,
    prompt_mfa: Callable[[], str] | None = None,
) -> Garmin:
    """Return an authenticated Garmin client using tokens or stored credentials."""
    store = tokenstore_path()
    mfa = prompt_mfa or (lambda: input("MFA code (if prompted): ").strip())

    token_file = token_file_path(store)
    if not token_file.is_file():
        restore_tokens_from_supabase(store)

    client = Garmin()
    try:
        client.login(store)
        try:  # noqa: SIM105 - kept explicit; T-0040 replaces with logging
            persist_tokens_to_supabase(store)
        except Exception:  # noqa: S110 - best effort; T-0040 replaces with logging
            pass
        return client
    except Exception:  # noqa: S110 - best effort; T-0040 replaces with logging
        pass

    if token_file.is_file() and restore_tokens_from_supabase(store):
        try:
            client = Garmin()
            client.login(store)
            try:  # noqa: SIM105 - kept explicit; T-0040 replaces with logging
                persist_tokens_to_supabase(store)
            except Exception:  # noqa: S110 - best effort; T-0040 replaces with logging
                pass
            return client
        except Exception:  # noqa: S110 - best effort; T-0040 replaces with logging
            pass

    email, password = get_credentials(prompt=prompt)
    client = Garmin(email=email, password=password, prompt_mfa=mfa)
    client.login(store)
    try:  # noqa: SIM105 - kept explicit; T-0040 replaces with logging
        persist_tokens_to_supabase(store)
    except Exception:  # noqa: S110 - best effort; T-0040 replaces with logging
        pass
    return client
