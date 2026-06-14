"""Tests for SSO widget-login MFA detection.

In-process, no network: a fake ``curl_cffi`` session feeds the widget login
strategy canned HTML so we can assert how each post-login page title is
handled. Covers both MFA variants and guards against over-broad detection.
"""

import contextlib
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from garminconnect import client as client_mod
from garminconnect.client import _MFARequired
from garminconnect.exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
)

# The signin GET must yield a CSRF token for the flow to reach the POST.
_CSRF_HTML = '<input name="_csrf" value="tok123"/>'


def _resp(text="", status_code=200, url="https://sso.garmin.com/sso/signin"):
    return SimpleNamespace(
        text=text,
        status_code=status_code,
        url=url,
        ok=200 <= status_code < 400,
    )


def _page(title):
    return f"<html><head><title>{title}</title></head><body></body></html>"


class _FakeSession:
    """Minimal stand-in for curl_cffi's Session for the widget flow.

    Every GET returns a CSRF-bearing page (covers both the embed and signin
    GETs); the credential POST returns the caller-supplied page carrying the
    title under test.
    """

    def __init__(self, post_text):
        self._post_text = post_text

    def get(self, url, **kwargs):
        return _resp(text=_CSRF_HTML)

    def post(self, url, **kwargs):
        return _resp(text=self._post_text)


@contextlib.contextmanager
def _widget_session(post_text):
    """Patch the widget flow to drive ``_FakeSession`` with no real network/delay."""
    with (
        patch.object(client_mod, "HAS_CFFI", True),
        patch.object(
            client_mod,
            "cffi_requests",
            SimpleNamespace(Session=lambda *a, **k: _FakeSession(post_text)),
        ),
        patch.object(client_mod.time, "sleep"),
    ):
        yield


@pytest.mark.parametrize(
    "title",
    [
        "GARMIN Authentication Application",  # email one-time-code MFA
        "Enter MFA code for login",  # authenticator-app (TOTP) MFA
    ],
)
def test_mfa_titles_trigger_mfa(title):
    """Both MFA page-title variants must enter the MFA completion flow."""
    c = client_mod.Client()
    with _widget_session(_page(title)), pytest.raises(_MFARequired):
        c._widget_web_login("e@x.com", "pw")

    assert c._mfa_flow == "widget"
    assert c._widget_last_resp is not None


def test_unexpected_title_still_errors():
    """A genuinely unknown page must NOT be misread as an MFA challenge."""
    c = client_mod.Client()
    with _widget_session(_page("Some Unrelated Page")), pytest.raises(
        GarminConnectConnectionError, match="unexpected title"
    ):
        c._widget_web_login("e@x.com", "pw")


# ---------------------------------------------------------------------------
# Completion side: _complete_mfa_widget (covers what detection alone doesn't —
# the step that actually logs an email-/TOTP-MFA user in).
# ---------------------------------------------------------------------------


def _set_widget_mfa_context(c, verify_text):
    """Prime the widget-MFA state as ``_widget_web_login`` leaves it on MFA."""
    c._widget_last_resp = _resp(text=_CSRF_HTML)  # carries the CSRF token
    c._mfa_session = _FakeSession(verify_text)  # POST returns the verify page
    c._mfa_login_params = {}
    c._mfa_post_headers = {}


def test_complete_mfa_widget_success():
    """A valid code yields a Success page + ticket, which is exchanged."""
    c = client_mod.Client()
    success_page = (
        "<html><head><title>Success</title></head><body>"
        '<a href="https://sso.garmin.com/sso/embed?ticket=ST-12345-abc"></a>'
        "</body></html>"
    )
    _set_widget_mfa_context(c, success_page)
    with patch.object(c, "_establish_session") as establish:
        c._complete_mfa_widget("123456")
    establish.assert_called_once()
    assert establish.call_args.args[0] == "ST-12345-abc"


def test_complete_mfa_widget_missing_context():
    """No pending widget MFA session -> clear error, no crash."""
    c = client_mod.Client()
    with pytest.raises(
        GarminConnectAuthenticationError, match="Missing widget MFA context"
    ):
        c._complete_mfa_widget("123456")


def test_complete_mfa_widget_rejects_bad_code():
    """A non-Success verify page (e.g. wrong/expired code) raises auth error."""
    c = client_mod.Client()
    _set_widget_mfa_context(c, _page("Enter MFA code for login"))
    with pytest.raises(GarminConnectAuthenticationError, match="Widget MFA failed"):
        c._complete_mfa_widget("000000")
