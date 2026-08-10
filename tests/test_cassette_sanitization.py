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


def test_sanitize_request_scrubs_json_login_body():
    """Login strategies post credentials as JSON, not key=value form data.

    Regression test: the form-body regex never matches a JSON body, so the
    sanitiser was a no-op on exactly the requests carrying the credentials.
    """
    body = json.dumps(
        {
            "username": "victim@example.com",
            "password": "S3cr3t-Passw0rd",  # noqa: S105
            "rememberMe": True,
            "captchaToken": "captcha-secret",
        },
        separators=(",", ":"),
    ).encode()
    request = SimpleNamespace(body=body, headers={})

    sanitized = sanitize_request(request)

    parsed = json.loads(sanitized.body)
    assert parsed["username"] == "SANITIZED"
    assert parsed["password"] == "SANITIZED"
    assert parsed["captchaToken"] == "SANITIZED"
    assert parsed["rememberMe"] is True
    assert b"victim@example.com" not in sanitized.body
    assert b"S3cr3t-Passw0rd" not in sanitized.body


def test_sanitize_request_scrubs_mfa_code_json_body():
    body = json.dumps(
        {"mfaMethod": "email", "mfaVerificationCode": "123456"}
    ).encode()
    request = SimpleNamespace(body=body, headers={})

    sanitized = sanitize_request(request)

    assert b"123456" not in sanitized.body


def test_sanitize_request_scrubs_di_exchange_form_body():
    """The DI token exchange posts the CAS service ticket form-encoded."""
    request = SimpleNamespace(
        body=b"service_ticket=ST-12345-secret&grant_type=service_ticket",
        headers={},
    )

    sanitized = sanitize_request(request)

    body = sanitized.body.decode("utf8")
    assert "service_ticket=SANITIZED" in body
    assert "ST-12345-secret" not in body


def test_sanitize_request_scrubs_ticket_from_uri():
    """The ticket-consumption fallback carries ?ticket=ST-... in the URL."""
    request = SimpleNamespace(
        body=None,
        headers={},
        uri="https://connect.garmin.com/gcm/ios?ticket=ST-999-canary&x=1",
    )

    sanitized = sanitize_request(request)

    assert "ST-999-canary" not in sanitized.uri
    assert "ticket=SANITIZED" in sanitized.uri
