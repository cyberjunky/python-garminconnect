"""Security regression tests for token-store file permissions.

Guards against GHSA-wjhr-76vg-2hvc: ``Client.dump()`` must write the token
file (which holds the DI refresh token) owner-only (0o600) inside an
owner-only directory (0o700), regardless of the process umask, so it can't be
left world-readable on a shared host.

POSIX-only — file mode bits are not meaningful on Windows.
"""

import os
import stat
import sys
from pathlib import Path

import pytest

from garminconnect.client import Client

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes only")


def _make_client() -> Client:
    c = Client()
    c.di_token = "ACCESS_TOKEN_EXAMPLE"
    c.di_refresh_token = "REFRESH_TOKEN_EXAMPLE"
    c.di_client_id = "CLIENT_ID_EXAMPLE"
    return c


def _mode(path) -> int:
    return stat.S_IMODE(Path(path).stat().st_mode)


def test_dump_creates_owner_only_token_file(tmp_path):
    """Under a permissive umask the token file must still be 0o600."""
    old_umask = os.umask(0o022)
    try:
        token_dir = tmp_path / "tokens"
        _make_client().dump(str(token_dir))
        token_file = token_dir / "garmin_tokens.json"

        assert _mode(token_file) == 0o600, oct(_mode(token_file))
        assert _mode(token_dir) == 0o700, oct(_mode(token_dir))
        # World/group bits must be clear
        assert not (_mode(token_file) & (stat.S_IRWXG | stat.S_IRWXO))
        assert not (_mode(token_dir) & (stat.S_IRWXG | stat.S_IRWXO))
    finally:
        os.umask(old_umask)


def test_dump_tightens_preexisting_loose_permissions(tmp_path):
    """A pre-existing world-readable dir/file is tightened on dump."""
    old_umask = os.umask(0o022)
    try:
        token_dir = tmp_path / "tokens"
        token_dir.mkdir(mode=0o755)
        token_file = token_dir / "garmin_tokens.json"
        token_file.write_text("{}")
        token_file.chmod(0o644)

        _make_client().dump(str(token_dir))

        assert _mode(token_file) == 0o600, oct(_mode(token_file))
        assert _mode(token_dir) == 0o700, oct(_mode(token_dir))
    finally:
        os.umask(old_umask)


@pytest.mark.parametrize("filename", ["garmin_tokens.json", "garmin_tokens.JSON"])
def test_dump_explicit_json_path(tmp_path, filename):
    """A direct ``*.json`` path is also written owner-only."""
    old_umask = os.umask(0o022)
    try:
        token_file = tmp_path / "store" / filename
        _make_client().dump(str(token_file))
        assert _mode(token_file) == 0o600, oct(_mode(token_file))
    finally:
        os.umask(old_umask)
