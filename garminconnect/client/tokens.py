"""Token storage and JWT helpers for the Garmin Connect client."""

import base64
import contextlib
import json
import logging
import math
import os
import secrets
import time
from pathlib import Path
from typing import Any

from ..exceptions import GarminConnectAuthenticationError, GarminConnectConnectionError
from ._base import _ClientState
from .constants import _OTHER_USER_HOME_RE

_LOGGER = logging.getLogger(__name__)


def token_file_path(path: str) -> Path:
    """Return the token file represented by a directory or JSON path.

    Rejects paths that expand into another user's home directory via
    ``~username`` syntax. Bare ``~`` and ``~/...`` are allowed because they
    resolve to the current user's home.

    Also rejects symlinked tokenstore paths so a pre-planted symlink cannot
    redirect load/dump/logout to an attacker-controlled location.
    """
    if _OTHER_USER_HOME_RE.match(path):
        raise ValueError(
            f"Token path must not reference another user's home directory: {path!r}"
        )
    token_path = Path(path).expanduser()
    # Reject symlinks anywhere in the tokenstore ancestry (e.g.
    # ~/.garminconnect -> /attacker/dir). O_NOFOLLOW on the final open()
    # only covers the last component; an intermediate symlinked directory
    # would still redirect load/dump/logout into an attacker-controlled tree.
    # A root-owned symlink (Fedora Silverblue's /home -> var/home, FreeBSD's
    # /home -> usr/home) can only be planted by root, so it is allowed on
    # POSIX; Windows reports st_uid 0 for everything, so it never qualifies.
    for check_path in (token_path, *token_path.parents):
        try:
            if check_path.is_symlink() and not (
                os.name == "posix" and os.lstat(check_path).st_uid == 0
            ):
                raise ValueError(f"Token path must not be a symlink: {path!r}")
        except OSError as e:
            raise ValueError(
                f"Token path cannot be checked for symlinks: {path!r}"
            ) from e
    if token_path.is_dir() or token_path.suffix.casefold() != ".json":
        return token_path / "garmin_tokens.json"
    return token_path


def _build_basic_auth(client_id: str) -> str:
    return "Basic " + base64.b64encode(f"{client_id}:".encode()).decode()


def _decode_jwt_payload(token: str) -> dict[str, Any] | None:
    """Decode a JWT payload without verifying the signature.

    Garmin signs tokens on the server side; the client does not have the
    signing key, so full signature verification is not possible here. We do
    reject tokens that claim ``alg: none`` or otherwise look structurally
    invalid, preventing the most trivial client-side spoofing of unsigned
    payloads.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        header_b64 = parts[0] + "=" * (-len(parts[0]) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_b64).decode())
        if header.get("alg") == "none":
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    except Exception:
        return None


class TokenStoreMixin(_ClientState):
    """Serialize, persist and inspect the DI tokens."""

    def _extract_client_id_from_jwt(self, token: str) -> str | None:
        payload = _decode_jwt_payload(token)
        if not payload:
            return None
        value = payload.get("client_id")
        return str(value) if value else None

    def _token_expires_soon(self) -> bool:
        token = self.di_token or self.jwt_web
        if not token:
            return False
        payload = _decode_jwt_payload(str(token))
        if not payload:
            return False
        # 'exp' is a server-controlled claim from an unverified JWT payload, so
        # coerce it defensively: a non-numeric string, container, boolean,
        # non-finite or overflowing value must not raise (TypeError/ValueError/
        # OverflowError) and take down every request.
        raw_exp = payload.get("exp")
        if isinstance(raw_exp, bool):
            return False
        try:
            exp = float(raw_exp)  # type: ignore[arg-type]
        except (TypeError, ValueError, OverflowError):
            return False
        if not math.isfinite(exp):
            return False
        return time.time() > exp - 900

    def dumps(self) -> str:
        """Serialize session state to JSON string."""
        data: dict[str, Any] = {
            "di_token": self.di_token,
            "di_refresh_token": self.di_refresh_token,
            "di_client_id": self.di_client_id,
        }
        return json.dumps(data)

    def dump(self, path: str) -> None:
        """Write tokens safely to disk with owner-only permissions.

        The token file contains the DI refresh token, which grants persistent
        account access. It is written as 0o600 inside a 0o700 directory so a
        permissive process umask can't leave it world-readable on a shared host
        (GHSA-wjhr-76vg-2hvc).

        Writes to a sibling temporary file and atomically replaces the target so
        a concurrent reader never sees a truncated or partial token file.
        """
        p = token_file_path(path)
        # Serialize with token mutation so the serialized snapshot is consistent
        # (e.g. not torn across a concurrent refresh).
        with self._token_lock:
            payload = self.dumps()
        p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        # mkdir's mode is subject to umask and a no-op if the dir already
        # exists; chmod enforces 0o700 unconditionally.
        with contextlib.suppress(OSError):
            p.parent.chmod(0o700)
        # Open with O_CREAT|O_EXCL mode 0o600 (and O_NOFOLLOW where available)
        # instead of write_text, which would create the file under the umask
        # first. The temp name is unpredictable and O_EXCL is required (not
        # just O_TRUNC): a fixed sibling name is guessable, and without
        # O_EXCL a pre-planted file's inode would be reused for the write
        # instead of a fresh one being created, letting whoever holds a
        # descriptor on that pre-planted inode observe the token payload.
        tmp = p.with_name(f".{p.name}.{secrets.token_hex(8)}.tmp")
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(tmp, flags, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as token_file:
                token_file.write(payload)
            # Enforce 0o600 even if the file pre-existed with looser permissions.
            with contextlib.suppress(OSError):
                tmp.chmod(0o600)
            tmp.replace(p)
        except Exception:
            with contextlib.suppress(OSError):
                tmp.unlink()
            raise

    def load(self, path: str) -> None:
        """Read tokens from disk, refusing to follow symlinks.

        A pre-planted symlink must not redirect the read to an attacker-controlled
        file, so this mirrors the write-side hardening in ``dump()``.
        """
        try:
            self._tokenstore_path = path
            p = token_file_path(path)
            flags = os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(p, flags)
            with os.fdopen(fd, encoding="utf-8") as token_file:
                self.loads(token_file.read())
        except Exception as e:
            raise GarminConnectConnectionError(
                f"Token path not loading cleanly: {e}"
            ) from e

    def loads(self, tokenstore: str) -> None:
        try:
            data = json.loads(tokenstore)
            self.di_token = data.get("di_token")
            self.di_refresh_token = data.get("di_refresh_token")
            self.di_client_id = data.get("di_client_id")
            if not self.is_authenticated:
                raise GarminConnectAuthenticationError("Missing tokens from dict load")
        except Exception as e:
            _LOGGER.debug("Token extraction loads() structurally failed: %s", e)
            raise GarminConnectConnectionError(
                "Token extraction loads() structurally failed"
            ) from e
