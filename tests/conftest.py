import json
import os
import re
from pathlib import Path
from typing import Any

import pytest


SENSITIVE_FIELDS = {
    "access_token",
    "activityId",
    "consumer_key",
    "consumer_secret",
    "di_refresh_token",
    "di_token",
    "displayName",
    "emailAddress",
    "fullName",
    "garminGUID",
    "jti",
    "locationName",
    "mfa_token",
    "oauth_token",
    "oauth_token_secret",
    "ownerId",
    "ownerDisplayName",
    "ownerFullName",
    "password",
    "profileId",
    "profileImageUrlLarge",
    "profileImageUrlMedium",
    "profileImageUrlSmall",
    "refresh_token",
    "token",
    "userId",
    "userName",
    "userProfileFullName",
    "userProfileId",
}
LOCATION_FIELDS = {
    "endLatitude",
    "endLongitude",
    "latitude",
    "longitude",
    "startLatitude",
    "startLongitude",
}


@pytest.fixture
def make_symlink() -> Any:
    """Create a symlink, or skip the test where that needs privileges (Windows)."""

    def _make(target: Path, link: Path) -> None:
        try:
            link.symlink_to(target)
        except OSError:
            pytest.skip("symlink creation requires elevated privileges here")

    return _make


@pytest.fixture
def vcr(vcr: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    # Set default GARMINTOKENS path if not already set
    if "GARMINTOKENS" not in os.environ:
        monkeypatch.setenv("GARMINTOKENS", str(Path("~/.garminconnect").expanduser()))
    return vcr


def sanitize_cookie(cookie_value: str) -> str:
    return re.sub(r"=[^;]*", "=SANITIZED", cookie_value)


def scrub_dates(response: Any) -> Any:
    """Scrub ISO datetime strings to make cassettes more stable."""
    body_container = response.get("body") or {}
    body = body_container.get("string")
    if isinstance(body, str):
        # Replace ISO datetime strings with a fixed timestamp
        body = re.sub(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+", "1970-01-01T00:00:00.000", body
        )
        body_container["string"] = body
    elif isinstance(body, bytes):
        # Handle bytes body
        body_str = body.decode("utf-8", errors="ignore")
        body_str = re.sub(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+",
            "1970-01-01T00:00:00.000",
            body_str,
        )
        body_container["string"] = body_str.encode("utf-8")
    response["body"] = body_container
    return response


# Form-encoded body parameters that must never be recorded, even in request
# bodies. Keep in sync with the regex patterns used in sanitize_response.
SENSITIVE_FORM_PARAMS = [
    "access_token",
    "mfa_token",
    "oauth_token",
    "oauth_token_secret",
    "password",
    "refresh_token",
    "username",
]

# JavaScript variable names produced by Garmin's widget MFA flow that contain
# PII (email/phone) or stable identifiers. Embedded in HTML response bodies.
SENSITIVE_JS_VARS = {"customerGuid", "clientId", "codeSentTo", "mfaMethod"}
_JS_VAR_RE = re.compile(
    r"(var\s+)("
    + "|".join(re.escape(name) for name in SENSITIVE_JS_VARS)
    + r")(\s*=\s*['\"])([^'\"]*)(['\"]\s*;)"
)


def _sanitize_form_body(body: str) -> str:
    """Scrub sensitive parameters from application/x-www-form-urlencoded bodies."""
    for key in SENSITIVE_FORM_PARAMS:
        body = re.sub(re.escape(key) + r"=[^&]*", f"{key}=SANITIZED", body)
    return body


def _sanitize_html_body(body: str) -> str:
    """Scrub sensitive JS variables embedded in HTML response bodies."""
    return _JS_VAR_RE.sub(
        lambda m: f'{m.group(1)}{m.group(2)}{m.group(3)}SANITIZED{m.group(5)}', body
    )


def sanitize_request(request: Any) -> Any:
    if request.body:
        try:
            body = request.body.decode("utf8")
        except UnicodeDecodeError:
            return request  # leave as-is; binary bodies not sanitized
        else:
            request.body = _sanitize_form_body(body).encode("utf8")

    if "Cookie" in request.headers:
        cookies = request.headers["Cookie"].split("; ")
        sanitized_cookies = [sanitize_cookie(cookie) for cookie in cookies]
        request.headers["Cookie"] = "; ".join(sanitized_cookies)
    return request


def sanitize_json(value: Any) -> Any:
    """Recursively remove identifiers and precise locations from JSON."""
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    if not isinstance(value, dict):
        return value

    profile_object = any(
        key in value for key in ("profileId", "garminGUID", "userProfileId")
    )
    sanitized: dict[str, Any] = {}
    for key, item in value.items():
        normalized_key = key.casefold()
        if (
            key in SENSITIVE_FIELDS
            or (key == "id" and profile_object)
            or "profileimage" in normalized_key
            or normalized_key.endswith(("email", "guid"))
        ):
            sanitized[key] = "SANITIZED"
        elif key in LOCATION_FIELDS or normalized_key.endswith(
            ("latitude", "longitude")
        ):
            sanitized[key] = None
        else:
            sanitized[key] = sanitize_json(item)
    return sanitized


def sanitize_response(response: Any) -> Any:
    # First scrub dates to normalize timestamps
    response = scrub_dates(response)

    # Remove variable headers that can change between requests
    headers_to_remove = {
        "date",
        "cf-ray",
        "cf-cache-status",
        "alt-svc",
        "nel",
        "report-to",
        "transfer-encoding",
        "pragma",
        "content-encoding",
    }
    if "headers" in response:
        response["headers"] = {
            k: v
            for k, v in response["headers"].items()
            if k.lower() not in headers_to_remove
        }

    for key in response["headers"]:
        if key.casefold() == "set-cookie":
            cookies = response["headers"][key]
            response["headers"][key] = [sanitize_cookie(cookie) for cookie in cookies]

    body = response["body"]["string"]
    if isinstance(body, bytes):
        body = body.decode("utf8")

    # Scrub sensitive form-encoded parameters from response bodies using the
    # same deny-list applied to requests, so a field added to one is always
    # covered by the other.
    body = _sanitize_form_body(body)
    # Scrub sensitive JS variables embedded in HTML bodies (e.g., Garmin widget
    # MFA flow: customerGuid, codeSentTo, clientId).
    body = _sanitize_html_body(body)
    body_was_bytes = isinstance(response["body"]["string"], bytes)
    try:
        body_json = json.loads(body)
    except json.JSONDecodeError:
        pass
    else:
        body = json.dumps(sanitize_json(body_json))

    if body_was_bytes:
        response["body"]["string"] = body.encode("utf8")
    else:
        response["body"]["string"] = body
    return response


@pytest.fixture(scope="session")
def vcr_config() -> dict[str, Any]:
    return {
        "filter_headers": [
            ("Authorization", "Bearer SANITIZED"),
            ("Cookie", "SANITIZED"),
        ],
        "before_record_request": sanitize_request,
        "before_record_response": sanitize_response,
    }
