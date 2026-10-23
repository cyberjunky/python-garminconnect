"""The mobile login loads the sign-in page before posting credentials."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from garminconnect import client as client_mod
from garminconnect.exceptions import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


def _session(get_status=200):
    sess = MagicMock()
    sess.get.return_value = SimpleNamespace(status_code=get_status, text="")
    login = MagicMock(status_code=200)
    login.json.return_value = {"responseStatus": {"type": "INVALID_USERNAME_PASSWORD"}}
    sess.post.return_value = login
    return sess


def test_sign_in_page_is_loaded_before_the_credentials_post():
    """Without the page's cookies and Referer, Garmin answers the POST with 429."""
    c = client_mod.Client(verify_login=False)
    sess = _session()
    calls = []
    sess.get.side_effect = lambda *a, **k: calls.append("GET") or SimpleNamespace(
        status_code=200, text=""
    )
    sess.post.side_effect = lambda *a, **k: calls.append("POST") or sess.post.return_value
    with patch("garminconnect.client.sso.time.sleep"), pytest.raises(Exception):
        c._do_mobile_login(sess, "e@x.com", "pw")

    assert calls == ["GET", "POST"]
    get_url = sess.get.call_args.args[0]
    assert get_url == "https://sso.garmin.com/mobile/sso/en_US/sign-in"
    assert sess.get.call_args.kwargs["params"]["clientId"] == "GCM_IOS_DARK"
    post_headers = sess.post.call_args.kwargs["headers"]
    assert post_headers["Referer"].startswith(get_url + "?clientId=GCM_IOS_DARK")
    assert post_headers["Accept-Language"] == "en-US,en;q=0.9"


@pytest.mark.parametrize("status", [427, 429])
def test_blocked_sign_in_page_stops_before_posting(status):
    c = client_mod.Client(verify_login=False)
    sess = _session(get_status=status)
    with pytest.raises(GarminConnectTooManyRequestsError, match=f"returned {status}"):
        c._do_mobile_login(sess, "e@x.com", "pw")
    sess.post.assert_not_called()


def test_challenged_sign_in_page_stops_before_posting():
    c = client_mod.Client(verify_login=False)
    sess = _session(get_status=403)
    with pytest.raises(GarminConnectConnectionError, match="403"):
        c._do_mobile_login(sess, "e@x.com", "pw")
    sess.post.assert_not_called()
