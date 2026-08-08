"""Security regression tests for private VCR recordings."""

import json
from types import SimpleNamespace

from conftest import sanitize_request, sanitize_response


def test_sanitize_response_recurses_through_nested_personal_data():
    response = {
        "headers": {},
        "body": {
            "string": json.dumps(
                {
                    "profile": {
                        "id": 123,
                        "profileId": 456,
                        "garminGUID": "private-guid",
                        "userName": "person@example.com",
                    },
                    "activities": [
                        {
                            "activityId": 789,
                            "startLatitude": 32.1,
                            "startLongitude": 34.8,
                        }
                    ],
                }
            )
        },
    }

    sanitized = sanitize_response(response)
    body = json.loads(sanitized["body"]["string"])

    assert body["profile"] == {
        "id": "SANITIZED",
        "profileId": "SANITIZED",
        "garminGUID": "SANITIZED",
        "userName": "SANITIZED",
    }
    assert body["activities"][0] == {
        "activityId": "SANITIZED",
        "startLatitude": None,
        "startLongitude": None,
    }


def test_sanitize_response_updates_non_json_token_body():
    response = {
        "headers": {},
        "body": {"string": b"oauth_token=secret&mfa_token=private"},
    }

    sanitized = sanitize_response(response)

    assert sanitized["body"]["string"] == (b"oauth_token=SANITIZED&mfa_token=SANITIZED")


def test_sanitize_response_scrubs_set_cookie_case_insensitively():
    response = {
        "headers": {"SET-COOKIE": ["session=private-value; Path=/"]},
        "body": {"string": "{}"},
    }

    sanitized = sanitize_response(response)

    assert "private-value" not in sanitized["headers"]["SET-COOKIE"][0]


def test_sanitize_response_scrubs_widget_mfa_html_vars():
    """Widget MFA embeds PII as JS variables in HTML bodies; those must be redacted."""
    response = {
        "headers": {"Content-Type": ["text/html"]},
        "body": {
            "string": (
                '<script>var customerGuid = "real-guid-1234"; '
                'var codeSentTo = "user@example.com"; '
                'var clientId = "client-456"; '
                'var mfaMethod = "EMAIL";</script>'
            )
        },
    }

    sanitized = sanitize_response(response)
    body = sanitized["body"]["string"]

    assert "real-guid-1234" not in body
    assert "user@example.com" not in body
    assert "client-456" not in body
    assert 'var customerGuid = "SANITIZED";' in body
    assert 'var codeSentTo = "SANITIZED";' in body
    assert 'var clientId = "SANITIZED";' in body


def test_sanitize_request_scrubs_oauth_exchange_body():
    """The OAuth exchange request body must have its credentials sanitized.

    Regression test for exposed mfa_token values in VCR cassettes.
    """
    request = SimpleNamespace(
        body=b"oauth_token=secret&mfa_token=private-token&access_token=abc",
        headers={"Cookie": "session=secret-value"},
    )

    sanitized = sanitize_request(request)

    body = sanitized.body.decode("utf8")
    assert "oauth_token=SANITIZED" in body
    assert "mfa_token=SANITIZED" in body
    assert "access_token=SANITIZED" in body
    assert "private-token" not in body
    assert "secret-value" not in sanitized.headers["Cookie"]
