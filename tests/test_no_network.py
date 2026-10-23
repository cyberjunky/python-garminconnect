"""Unit tests must never reach the network (see conftest._block_network)."""

import pytest
import requests

BLOCKED = "network access in a unit test"


def test_requests_is_blocked():
    with pytest.raises(RuntimeError, match=BLOCKED):
        requests.get("https://sso.garmin.com/mobile/api/login", timeout=5)


def test_curl_cffi_is_blocked():
    cffi_requests = pytest.importorskip("curl_cffi.requests")
    with pytest.raises(RuntimeError, match=BLOCKED):
        cffi_requests.Session(impersonate="chrome").get(
            "https://sso.garmin.com/mobile/api/login", timeout=5
        )


def test_login_strategies_cannot_reach_garmin():
    """A login with no strategy patched fails locally instead of contacting Garmin."""
    from garminconnect import client as client_mod

    c = client_mod.Client(verify_login=False)
    c.skip_strategies = {"widget+cffi", "portal+cffi", "portal+requests"}
    with pytest.raises(Exception, match=BLOCKED):
        c.login("e@x.com", "pw")
