"""Repository-level MCP server for Garmin Connect.

This server intentionally starts with a read-only tool surface so callers can
inspect account data without mutating Garmin state.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectNotFoundError,
    GarminConnectTooManyRequestsError,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - import-time guidance
    raise ImportError(
        "The Garmin MCP server requires the 'mcp' package. "
        "Install it with: pip install 'garminconnect[mcp]'"
    ) from exc


def _validate_date(date_value: str) -> str:
    """Validate YYYY-MM-DD format used by Garmin endpoints."""
    try:
        datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            "Invalid date format. Use YYYY-MM-DD, e.g. 2026-07-26."
        ) from exc
    return date_value


def _normalize_tokenstore(tokenstore: str | None) -> str:
    raw = tokenstore or os.getenv("GARMINTOKENS") or "~/.garminconnect"
    return str(Path(raw).expanduser())


class GarminSession:
    """Holds one shared Garmin client session for MCP tools."""

    def __init__(self) -> None:
        self.client: Garmin | None = None
        self.tokenstore: str = _normalize_tokenstore(None)

    @property
    def is_authenticated(self) -> bool:
        return self.client is not None and self.client.client.is_authenticated

    def ensure_client(self) -> Garmin:
        if self.client is None:
            self.client = Garmin()
        return self.client

    def require_authenticated(self) -> Garmin:
        if not self.is_authenticated:
            raise GarminConnectAuthenticationError(
                "Not authenticated. Call login_with_tokens or login_with_credentials first."
            )
        assert self.client is not None  # noqa: S101 - type narrowing for mypy
        return self.client


SESSION = GarminSession()
mcp = FastMCP("garmin-connect")


def _api_call(method: str, func: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        payload = func(*args, **kwargs)
        return {"ok": True, "method": method, "data": payload}
    except GarminConnectAuthenticationError as exc:
        return {"ok": False, "method": method, "error_type": "auth", "error": str(exc)}
    except GarminConnectTooManyRequestsError as exc:
        return {
            "ok": False,
            "method": method,
            "error_type": "rate_limit",
            "error": str(exc),
        }
    except GarminConnectNotFoundError as exc:
        return {
            "ok": False,
            "method": method,
            "error_type": "not_found",
            "error": str(exc),
        }
    except GarminConnectConnectionError as exc:
        return {
            "ok": False,
            "method": method,
            "error_type": "connection",
            "error": str(exc),
        }


@mcp.tool()
def auth_status() -> dict[str, Any]:
    """Return current authentication state and token store path."""
    return {
        "ok": True,
        "authenticated": SESSION.is_authenticated,
        "tokenstore": SESSION.tokenstore,
    }


@mcp.tool()
def login_with_tokens(tokenstore: str | None = None) -> dict[str, Any]:
    """Authenticate using cached Garmin tokens from tokenstore path."""
    SESSION.tokenstore = _normalize_tokenstore(tokenstore)
    client = SESSION.ensure_client()
    result = _api_call("login_with_tokens", client.login, SESSION.tokenstore)
    if result["ok"]:
        return {
            "ok": True,
            "authenticated": SESSION.is_authenticated,
            "tokenstore": SESSION.tokenstore,
            "mfa_status": result["data"][0] if isinstance(result["data"], tuple) else None,
        }
    return result


@mcp.tool()
def login_with_credentials(
    email: str,
    password: str,
    tokenstore: str | None = None,
) -> dict[str, Any]:
    """Authenticate with Garmin credentials and persist tokens locally.

    Use only in trusted local environments because this tool receives secrets.
    """
    SESSION.tokenstore = _normalize_tokenstore(tokenstore)
    SESSION.client = Garmin(email=email, password=password)
    assert SESSION.client is not None  # noqa: S101 - type narrowing for mypy
    result = _api_call("login_with_credentials", SESSION.client.login, SESSION.tokenstore)
    if result["ok"]:
        return {
            "ok": True,
            "authenticated": SESSION.is_authenticated,
            "tokenstore": SESSION.tokenstore,
            "mfa_status": result["data"][0] if isinstance(result["data"], tuple) else None,
        }
    return result


@mcp.tool()
def logout_local(tokenstore: str | None = None) -> dict[str, Any]:
    """Clear in-memory auth and delete local cached token file."""
    store = _normalize_tokenstore(tokenstore or SESSION.tokenstore)
    client = SESSION.ensure_client()
    result = _api_call("logout_local", client.logout, store)
    SESSION.client = None
    SESSION.tokenstore = store
    if result["ok"]:
        return {"ok": True, "authenticated": False, "tokenstore": store}
    return result


@mcp.tool()
def get_user_summary(date: str) -> dict[str, Any]:
    """Return daily user summary for date (YYYY-MM-DD)."""
    day = _validate_date(date)
    client = SESSION.require_authenticated()
    return _api_call("get_user_summary", client.get_user_summary, day)


@mcp.tool()
def get_heart_rates(date: str) -> dict[str, Any]:
    """Return heart-rate data for date (YYYY-MM-DD)."""
    day = _validate_date(date)
    client = SESSION.require_authenticated()
    return _api_call("get_heart_rates", client.get_heart_rates, day)


@mcp.tool()
def get_sleep_data(date: str) -> dict[str, Any]:
    """Return sleep data for date (YYYY-MM-DD)."""
    day = _validate_date(date)
    client = SESSION.require_authenticated()
    return _api_call("get_sleep_data", client.get_sleep_data, day)


@mcp.tool()
def get_activities(
    start: int = 0,
    limit: int = 20,
    activity_type: str | None = None,
) -> dict[str, Any]:
    """Return activities page (read-only) from Garmin Connect."""
    client = SESSION.require_authenticated()
    return _api_call(
        "get_activities",
        client.get_activities,
        start=start,
        limit=limit,
        activitytype=activity_type,
    )


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
