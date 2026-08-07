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
    GarminConnectTooManyRequestsError,
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


def _mfa_page(title, mfa_method, code_sent_to=None, customer_guid="cg-123"):
    """Build a widget page with the inline JS vars Garmin uses for MFA."""
    vars_ = [
        f'var customerGuid = "{customer_guid}";',
        f'var mfaMethod = "{mfa_method}";',
        'var locale = "en-US";',
        'var clientId = "";',
    ]
    if code_sent_to is not None:
        vars_.append(f'var codeSentTo = "{code_sent_to}";')
    return (
        f'<html><head><title>{title}</title></head><body>'
        f'<script>{" ".join(vars_)}</script></body></html>'
    )


class _FakeSession:
    """Minimal stand-in for curl_cffi's Session for the widget flow.

    Every GET returns a CSRF-bearing page (covers both the embed and signin
    GETs). The credential POST returns the caller-supplied MFA page; any
    ``verifyMFA/mfaCode`` POST returns a 200 unless a per-URL response is set.
    """

    def __init__(self, post_text, per_url=None):
        self._post_text = post_text
        self._per_url = per_url or {}
        self.post_urls = []

    def get(self, url, **kwargs):
        return _resp(text=_CSRF_HTML)

    def post(self, url, **kwargs):
        self.post_urls.append(url)
        for key, value in self._per_url.items():
            if key in url:
                return value
        return _resp(text=self._post_text)


@contextlib.contextmanager
def _widget_session(post_text, per_url=None):
    """Patch the widget flow to drive ``_FakeSession`` with no real network/delay."""
    cm = SimpleNamespace(session=None)

    def make_session(*args, **kwargs):
        sess = _FakeSession(post_text, per_url=per_url)
        cm.session = sess
        return sess

    with (
        patch.object(client_mod, "HAS_CFFI", True),
        patch.object(
            client_mod,
            "cffi_requests",
            SimpleNamespace(Session=make_session),
        ),
        patch.object(client_mod.time, "sleep"),
    ):
        yield cm


@pytest.mark.parametrize(
    "title, method",
    [
        ("GARMIN Authentication Application", "email"),  # email OTP MFA
        ("Enter MFA code for login", "totp"),  # authenticator-app MFA
    ],
)
def test_mfa_titles_trigger_mfa(title, method):
    """Both MFA page-title variants must enter the MFA completion flow."""
    c = client_mod.Client()
    with _widget_session(_mfa_page(title, method)) as cm, pytest.raises(_MFARequired):
        c._widget_web_login("e@x.com", "pw")

    assert c._mfa_flow == "widget"
    assert c._widget_last_resp is not None


def test_email_mfa_requests_code_when_not_already_sent():
    """Email/SMS MFA pages that have not yet delivered a code must trigger the
    same ``/sso/verifyMFA/mfaCode`` request the browser's "Request a new code"
    link uses.
    """
    c = client_mod.Client()
    page = _mfa_page("GARMIN Authentication Application", "email")
    with _widget_session(page) as cm, pytest.raises(_MFARequired):
        c._widget_web_login("e@x.com", "pw")

    assert any("/sso/verifyMFA/mfaCode" in url for url in cm.session.post_urls)
    assert c._mfa_method == "email"


def test_email_mfa_does_not_request_code_when_already_sent():
    """If the signin POST already sent a code, do not request another one."""
    c = client_mod.Client()
    page = _mfa_page(
        "Enter MFA code for login", "email", code_sent_to="x@example.com"
    )
    with _widget_session(page) as cm, pytest.raises(_MFARequired):
        c._widget_web_login("e@x.com", "pw")

    assert not any("/sso/verifyMFA/mfaCode" in url for url in cm.session.post_urls)


def test_totp_mfa_does_not_request_code():
    """Authenticator/TOTP codes are user-generated, not delivered by Garmin."""
    c = client_mod.Client()
    page = _mfa_page("Enter MFA code for login", "totp")
    with _widget_session(page) as cm, pytest.raises(_MFARequired):
        c._widget_web_login("e@x.com", "pw")

    assert not any("/sso/verifyMFA/mfaCode" in url for url in cm.session.post_urls)


def test_mfa_code_request_rate_limit_falls_through():
    """A 429 on the explicit code-request endpoint falls through to the next
    strategy, not a misleading MFA prompt.
    """
    c = client_mod.Client()
    page = _mfa_page("GARMIN Authentication Application", "email")
    per_url = {
        "/sso/verifyMFA/mfaCode": _resp(
            text="rate limited", status_code=429, url="https://sso.garmin.com/sso/verifyMFA/mfaCode"
        )
    }
    with _widget_session(page, per_url=per_url), pytest.raises(
        GarminConnectTooManyRequestsError
    ):
        c._widget_web_login("e@x.com", "pw")


def test_signin_page_title_not_mfa():
    """The bare signin page is also titled "GARMIN Authentication Application".
    Without the MFA JS variables it must not be mistaken for an MFA challenge.
    """
    c = client_mod.Client()
    page = "<html><head><title>GARMIN Authentication Application</title></head><body></body></html>"
    with _widget_session(page), pytest.raises(
        GarminConnectConnectionError, match="unexpected title"
    ):
        c._widget_web_login("e@x.com", "pw")


def test_unexpected_title_still_errors():
    """A genuinely unknown page must NOT be misread as an MFA challenge."""
    c = client_mod.Client()
    page = "<html><head><title>Some Unrelated Page</title></head><body></body></html>"
    with _widget_session(page), pytest.raises(
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
    _set_widget_mfa_context(c, _mfa_page("Enter MFA code for login", "totp"))
    with pytest.raises(GarminConnectAuthenticationError, match="Widget MFA failed"):
        c._complete_mfa_widget("000000")
