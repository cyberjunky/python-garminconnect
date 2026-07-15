"""Security regression tests for private VCR recordings."""

import json

from conftest import sanitize_response


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
