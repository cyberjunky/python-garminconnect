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
from garminconnect.exceptions import GarminConnectConnectionError

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
