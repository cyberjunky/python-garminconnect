import json
import os
import re

import pytest


@pytest.fixture
def vcr(vcr):
    assert "GARMINTOKENS" in os.environ
    return vcr


def sanitize_cookie(cookie_value) -> str:
    return re.sub(r"=[^;]*", "=SANITIZED", cookie_value)


def sanitize_request(request):
    if request.body:
        body = request.body.decode("utf8")
        for key in ["username", "password", "refresh_token"]:
            body = re.sub(key + r"=[^&]*", f"{key}=SANITIZED", body)
        request.body = body.encode("utf8")

    if "Cookie" in request.headers:
        cookies = request.headers["Cookie"].split("; ")
        sanitized_cookies = [sanitize_cookie(cookie) for cookie in cookies]
        request.headers["Cookie"] = "; ".join(sanitized_cookies)
    return request


def sanitize_response(response):
    for key in ["set-cookie", "Set-Cookie"]:
        if key in response["headers"]:
            cookies = response["headers"][key]
            sanitized_cookies = [sanitize_cookie(cookie) for cookie in cookies]
            response["headers"][key] = sanitized_cookies

    body = response["body"]["string"].decode("utf8")
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
    response["body"]["string"] = body.encode("utf8")

    return response


@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [("Authorization", "Bearer SANITIZED")],
        "before_record_request": sanitize_request,
        "before_record_response": sanitize_response,
    }
