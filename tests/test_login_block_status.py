"""Login blocks answered with HTTP 427 must be treated like 429 rate limits."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

import garminconnect
from garminconnect import client as client_mod
from garminconnect.client import sso as sso_mod
from garminconnect.exceptions import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


@pytest.mark.parametrize("status", [427, 429])
def test_block_statuses_raise_too_many_requests(status):
    with pytest.raises(GarminConnectTooManyRequestsError, match=f"returned {status}"):
        sso_mod._raise_if_rate_limited(SimpleNamespace(status_code=status), "x")


@pytest.mark.parametrize("status", [200, 403, 428, 500])
def test_other_statuses_are_not_blocks(status):
    sso_mod._raise_if_rate_limited(SimpleNamespace(status_code=status), "x")


def test_mixed_427_and_429_count_as_all_strategies_blocked():
    """A widget 427 among 429s must still yield the 'all blocked' error."""
    c = client_mod.Client()
    c.skip_strategies = {"portal+cffi", "portal+requests"}

    def blocked(status):
        def run(_email, _password):
            sso_mod._raise_if_rate_limited(SimpleNamespace(status_code=status), "x")

        return run

    with (
        patch.object(c, "_mobile_login_cffi", side_effect=blocked(429)),
        patch.object(c, "_mobile_login_requests", side_effect=blocked(429)),
        patch.object(c, "_widget_web_login", side_effect=blocked(427)),
        pytest.raises(
            GarminConnectTooManyRequestsError, match="rate limited or blocked"
        ),
    ):
        c.login("e@x.com", "pw")


def test_garmin_login_maps_a_427_failure_to_too_many_requests():
    """When the chain ends on a 427, callers still see a rate-limit error."""
    g = garminconnect.Garmin("e@x.com", "pw")
    with (
        patch.object(
            g.client,
            "login",
            side_effect=GarminConnectConnectionError(
                "All login strategies exhausted: Widget embed GET returned 427"
            ),
        ),
        pytest.raises(GarminConnectTooManyRequestsError),
    ):
        g.login()
