#!/usr/bin/env python3
"""End-to-end MCP smoke test against the local Garmin MCP server.

Flow:
1. Start server over stdio
2. List tools
3. Call auth_status
4. Call login_with_tokens
5. If authenticated, call get_user_summary for a target date
"""

from __future__ import annotations

import argparse
import os
from datetime import date, datetime

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _validate_date(value: str) -> str:
    datetime.strptime(value, "%Y-%m-%d")
    return value


def _payload(result: object) -> dict:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    return {"ok": False, "error": "Missing structuredContent"}


async def _run(day: str, allow_env_credentials: bool) -> int:
    params = StdioServerParameters(command="python", args=["-m", "garmin_mcp.server"], cwd=".")

    async with (
        stdio_client(params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]
        print("MCP_E2E_TOOLS", tool_names)

        status_result = await session.call_tool("auth_status", {})
        status = _payload(status_result)
        print("MCP_E2E_AUTH_STATUS", status)

        login_result = await session.call_tool("login_with_tokens", {})
        login = _payload(login_result)
        print("MCP_E2E_LOGIN_WITH_TOKENS", login)

        if not login.get("ok") or not login.get("authenticated"):
            if allow_env_credentials:
                email = os.getenv("GARMIN_EMAIL")
                password = os.getenv("GARMIN_PASSWORD")
                if email and password:
                    cred_result = await session.call_tool(
                        "login_with_credentials",
                        {"email": email, "password": password},
                    )
                    login = _payload(cred_result)
                    print("MCP_E2E_LOGIN_WITH_CREDENTIALS", login)
                else:
                    print(
                        "MCP_E2E_NO_ENV_CREDS: --allow-env-credentials enabled, "
                        "but GARMIN_EMAIL or GARMIN_PASSWORD is missing."
                    )

            if not login.get("ok") or not login.get("authenticated"):
                print(
                    "MCP_E2E_NEEDS_TOKENS: login_with_tokens did not authenticate. "
                    "Run credential login once to create ~/.garminconnect/garmin_tokens.json."
                )
                return 2

        summary_result = await session.call_tool("get_user_summary", {"date": day})
        summary = _payload(summary_result)
        print("MCP_E2E_SUMMARY", summary)

        if not summary.get("ok"):
            print("MCP_E2E_FAIL: summary call failed")
            return 3

        print("MCP_E2E_OK")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MCP end-to-end smoke test")
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Target date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--allow-env-credentials",
        action="store_true",
        help=(
            "If token login fails, try login_with_credentials using GARMIN_EMAIL "
            "and GARMIN_PASSWORD from environment variables."
        ),
    )
    args = parser.parse_args()

    try:
        day = _validate_date(args.date)
    except ValueError:
        print("Invalid --date format. Use YYYY-MM-DD.")
        return 4

    return anyio.run(_run, day, args.allow_env_credentials)


if __name__ == "__main__":
    raise SystemExit(main())
