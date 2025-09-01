import json
import os
import re
from typing import Any

import pytest


@pytest.fixture
def vcr(vcr: Any) -> Any:
    # Set default GARMINTOKENS path if not already set
    if "GARMINTOKENS" not in os.environ:
        os.environ["GARMINTOKENS"] = "~/.garminconnect"
    return vcr


def sanitize_cookie(cookie_value: str) -> str:
    return re.sub(r"=[^;]*", "=SANITIZED", cookie_value)


def scrub_dates(response: Any) -> Any:
    """Scrub ISO datetime strings to make cassettes more stable."""
    body = response.get("body", {}).get("string")
    if isinstance(body, str):
        # Replace ISO datetime strings with a fixed timestamp
        body = re.sub(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+", "1970-01-01T00:00:00.000", body
        )
        response["body"]["string"] = body
    elif isinstance(body, bytes):
        # Handle bytes body
        body_str = body.decode("utf-8", errors="ignore")
        body_str = re.sub(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+",
            "1970-01-01T00:00:00.000",
            body_str,
        )
        response["body"]["string"] = body_str.encode("utf-8")
    return response


def sanitize_request(request: Any) -> Any:
    if request.body:
        try:
            body = request.body.decode("utf8")
        except UnicodeDecodeError:
            ...
        else:
            for key in ["username", "password", "refresh_token"]:
                body = re.sub(key + r"=[^&]*", f"{key}=SANITIZED", body)
            request.body = body.encode("utf8")

    if "Cookie" in request.headers:
        cookies = request.headers["Cookie"].split("; ")
        sanitized_cookies = [sanitize_cookie(cookie) for cookie in cookies]
        request.headers["Cookie"] = "; ".join(sanitized_cookies)
    return request


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

    for key in ["set-cookie", "Set-Cookie"]:
        if key in response["headers"]:
            cookies = response["headers"][key]
            sanitized_cookies = [sanitize_cookie(cookie) for cookie in cookies]
            response["headers"][key] = sanitized_cookies

    body = response["body"]["string"]
    if isinstance(body, bytes):
        body = body.decode("utf8")

    patterns = [
        "oauth_token=[^&]*",
        "oauth_token_secret=[^&]*",
        "mfa_token=[^&]*",
    ]
    for pattern in patterns:
        body = re.sub(pattern, pattern.split("=")[0] + "=SANITIZED", body)
    try:
        body_json = json.loads(body)
    except json.JSONDecodeError:
        pass
    else:
        for field in [
            "access_token",
            "refresh_token",
            "jti",
            "consumer_key",
            "consumer_secret",
        ]:
            if field in body_json:
                body_json[field] = "SANITIZED"

        body = json.dumps(body_json)

    if isinstance(response["body"]["string"], bytes):
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
