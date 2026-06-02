#!/usr/bin/env python3
"""Interactive login strategy tester.

Runs a single login strategy in isolation (or all of them) so you can see
exactly which authentication path works and which fails on your account /
network.  Handy for diagnosing login issues: rate limits (429), Cloudflare
bot challenges (403 / CAPTCHA), MFA, or token-audience rejections.

The five strategies, in the order the library tries them:
    1. mobile+cffi      iOS mobile API via curl_cffi (TLS impersonation)
    2. mobile+requests  iOS mobile API via plain requests
    3. widget+cffi      SSO embed widget via curl_cffi
    4. portal+cffi      Connect portal via curl_cffi
    5. portal+requests  Connect portal via plain requests

Usage:
    python3 test_strategy.py
    EMAIL=you@example.com PASSWORD=secret python3 test_strategy.py
    GARMINTOKENS=~/.garminconnect python3 test_strategy.py

All output (console + debug logs) is also written to strategy_<name>.log.
"""

import logging
import os
import shutil
import sys
from datetime import datetime
from getpass import getpass
from pathlib import Path

import garminconnect

ALL_STRATEGIES = [
    "mobile+cffi",
    "mobile+requests",
    "widget+cffi",
    "portal+cffi",
    "portal+requests",
]


class _Tee:
    """Write to both a stream and a file simultaneously."""

    def __init__(self, stream: object, file: object) -> None:
        self._stream = stream
        self._file = file

    def write(self, data: str) -> None:
        self._stream.write(data)
        self._file.write(data)

    def flush(self) -> None:
        self._stream.flush()
        self._file.flush()

    def __getattr__(self, attr: str) -> object:
        return getattr(self._stream, attr)


def _setup_logging(strategy: str) -> Path:
    slug = strategy.replace("+", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(f"strategy_{slug}_{ts}.log")
    log_file = log_path.open("w", buffering=1)

    sys.stdout = _Tee(sys.__stdout__, log_file)  # type: ignore[assignment]
    sys.stderr = _Tee(sys.__stderr__, log_file)  # type: ignore[assignment]

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        stream=sys.stderr,
    )
    return log_path


def pick_strategy() -> str:
    print("\nAvailable strategies:")
    for i, name in enumerate(ALL_STRATEGIES, 1):
        print(f"  {i}. {name}")
    print(f"  {len(ALL_STRATEGIES) + 1}. Run ALL (normal login, no skipping)")
    while True:
        raw = input("\nPick a number: ").strip()
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(ALL_STRATEGIES):
                return ALL_STRATEGIES[n - 1]
            if n == len(ALL_STRATEGIES) + 1:
                return "all"
        print("Invalid choice, try again.")


def get_credentials() -> tuple[str, str]:
    email = os.environ.get("EMAIL") or input("Garmin email: ").strip()
    password = os.environ.get("PASSWORD") or getpass("Garmin password: ")
    return email, password


def get_tokenstore() -> str:
    default = str(Path("~/.garminconnect").expanduser())
    path = os.environ.get("GARMINTOKENS", default)
    print(f"Token store: {path}")
    return path


def clear_tokens(tokenstore: str) -> None:
    p = Path(tokenstore).expanduser()
    if not p.exists():
        print(f"No token store at {p} (will do a fresh login anyway)")
    elif p.is_dir():
        shutil.rmtree(p)
        print(f"Deleted directory {p}")
    else:
        p.unlink()
        print(f"Deleted {p}")


def run(strategy: str) -> None:
    email, password = get_credentials()
    tokenstore = get_tokenstore()

    answer = (
        input("\nDelete existing tokens to force a fresh login? [Y/n]: ")
        .strip()
        .lower()
    )
    if answer != "n":
        clear_tokens(tokenstore)

    g = garminconnect.Garmin(
        email, password, prompt_mfa=lambda: input("MFA code: ").strip()
    )

    if strategy != "all":
        skip = set(ALL_STRATEGIES) - {strategy}
        g.client.skip_strategies = skip
        print(f"\nRunning ONLY: {strategy}")
        print(f"Skipping:     {', '.join(sorted(skip))}\n")
    else:
        print("\nRunning all strategies (normal login)\n")

    try:
        g.login(tokenstore)
        print(f"\n✓  Login succeeded via {strategy}")
        print(f"   display_name : {g.display_name}")
        print(f"   full_name    : {g.full_name}")
        print(f"   di_token set : {bool(g.client.di_token)}")
        print(f"   jwt_web set  : {bool(g.client.jwt_web)}")
    except garminconnect.GarminConnectAuthenticationError as e:
        print(f"\n✗  Authentication error: {e}", file=sys.stderr)
    except garminconnect.GarminConnectTooManyRequestsError as e:
        print(f"\n✗  Rate limited (429): {e}", file=sys.stderr)
    except garminconnect.GarminConnectConnectionError as e:
        print(f"\n✗  Connection/API error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"\n✗  Unexpected error ({type(e).__name__}): {e}", file=sys.stderr)


if __name__ == "__main__":
    # Pick strategy before setting up logging so the menu stays clean
    strategy = pick_strategy()
    log_path = _setup_logging(strategy)
    print(f"Logging to: {log_path}\n")
    run(strategy)
