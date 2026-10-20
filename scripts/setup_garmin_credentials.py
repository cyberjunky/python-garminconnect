#!/usr/bin/env python3
"""Save Garmin credentials securely for local scripts in this repository."""

from __future__ import annotations

import sys
from datetime import date
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garmin_auth import (
    KEYCHAIN_SERVICE,
    login_client,
    save_credentials,
    tokenstore_path,
)


def main() -> int:
    print("Garmin credential setup")
    print("-----------------------")
    print(f"Credentials will be stored in macOS Keychain (service: {KEYCHAIN_SERVICE}).")
    print("They are never written to git.")

    email = input("Garmin email: ").strip()
    password = getpass("Garmin password (hidden): ")
    if not email or not password:
        print("ERROR: email and password are required.")
        return 2

    try:
        save_credentials(email, password)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 3

    try:
        client = login_client(prompt=False)
        summary = client.get_user_summary(date.today().isoformat())
    except Exception as exc:
        print(f"ERROR: saved credentials but login failed: {exc}")
        return 4

    print("SETUP_OK")
    print(
        {
            "email": email,
            "tokenstore": tokenstore_path(),
            "steps_today": summary.get("totalSteps"),
        }
    )
    print("\nFuture script runs will reuse Keychain credentials when tokens expire.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
