"""Tests for the MFA "shelving" behavior in login().

A strategy that reaches MFA but can't be trusted to have actually made
Garmin deliver an OTP (currently: widget+cffi's email/SMS page -- see
_mfa_delivery_uncertain in client.py) must not permanently stop the chain.
Its MFA state is shelved so remaining strategies get a chance; it's only
used as a fallback if nothing later does better.

All in-process -- no network. Strategy methods are patched with side
effects that mimic the real ones (setting _mfa_flow / raising _MFARequired
/ raising the fallthrough errors the real code would raise).
"""

from unittest.mock import patch

from garminconnect import client as client_mod
from garminconnect.exceptions import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


def _uncertain_widget_mfa(c):
    """Mimic widget+cffi hitting the email/SMS MFA page."""

    def strategy(_email, _password):
        c._mfa_flow = "widget"
        c._mfa_delivery_uncertain = True
        raise client_mod._MFARequired()

    return strategy


def _trusted_mfa(c, flow_name):
    """Mimic mobile/portal hitting MFA via the JSON login API (trusted:
    Garmin's own MFA_REQUIRED response is the send trigger).
    """

    def strategy(_email, _password):
        c._mfa_flow = flow_name
        raise client_mod._MFARequired()

    return strategy


def test_uncertain_widget_mfa_falls_through_to_later_success():
    """widget+cffi hits unconfirmed email MFA; portal+cffi succeeds outright
    -- the shelved widget MFA state must never be used.
    """
    c = client_mod.Client(verify_login=False)
    c.skip_strategies = {"mobile+cffi", "mobile+requests", "portal+requests"}

    def portal_strategy(_email, _password):
        c.di_token = "portal-token"  # noqa: S105

    with (
        patch.object(c, "_widget_web_login", side_effect=_uncertain_widget_mfa(c)),
        patch.object(c, "_portal_web_login_cffi", side_effect=portal_strategy),
    ):
        c.login("e@x.com", "pw")

    assert c.di_token == "portal-token"  # noqa: S105


def test_uncertain_widget_mfa_prefers_later_trusted_mfa():
    """widget+cffi hits unconfirmed email MFA; portal+cffi also needs MFA,
    but via the trusted JSON API -- the chain must prompt using portal's
    MFA context, not widget's shelved one.
    """
    c = client_mod.Client(verify_login=False)
    c.skip_strategies = {"mobile+cffi", "mobile+requests", "portal+requests"}

    prompted_flows = []

    def prompt_mfa():
        prompted_flows.append(c._mfa_flow)
        return "123456"

    def fake_complete_mfa(_code):
        c.di_token = f"{c._mfa_flow}-token"

    with (
        patch.object(c, "_widget_web_login", side_effect=_uncertain_widget_mfa(c)),
        patch.object(
            c, "_portal_web_login_cffi", side_effect=_trusted_mfa(c, "portal")
        ),
        patch.object(c, "_complete_mfa", side_effect=fake_complete_mfa),
    ):
        c.login("e@x.com", "pw", prompt_mfa=prompt_mfa)

    assert prompted_flows == ["portal"]
    assert c.di_token == "portal-token"  # noqa: S105


def test_uncertain_widget_mfa_falls_back_when_nothing_better():
    """widget+cffi hits unconfirmed email MFA; every later strategy fails
    outright (429 / connection error, never reaching MFA or success) --
    the chain must fall back to the shelved widget MFA state rather than
    reporting a hard failure.
    """
    c = client_mod.Client(verify_login=False)
    c.skip_strategies = {"mobile+cffi", "mobile+requests"}

    def portal_cffi_strategy(_email, _password):
        raise GarminConnectConnectionError("blocked")

    def portal_requests_strategy(_email, _password):
        raise GarminConnectTooManyRequestsError("429")

    prompted_flows = []

    def prompt_mfa():
        prompted_flows.append(c._mfa_flow)
        return "000000"

    def fake_complete_mfa(_code):
        c.di_token = f"{c._mfa_flow}-token"

    with (
        patch.object(c, "_widget_web_login", side_effect=_uncertain_widget_mfa(c)),
        patch.object(c, "_portal_web_login_cffi", side_effect=portal_cffi_strategy),
        patch.object(
            c, "_portal_web_login_requests", side_effect=portal_requests_strategy
        ),
        patch.object(c, "_complete_mfa", side_effect=fake_complete_mfa),
    ):
        c.login("e@x.com", "pw", prompt_mfa=prompt_mfa)

    assert prompted_flows == ["widget"]
    assert c.di_token == "widget-token"  # noqa: S105


def test_uncertain_mfa_as_last_strategy_resolves_immediately():
    """If the uncertain-delivery strategy is the last one left in the
    chain, there's nothing to fall through to -- it must resolve right
    away, same as before this change.
    """
    c = client_mod.Client(verify_login=False)
    c.skip_strategies = {
        "mobile+cffi",
        "mobile+requests",
        "portal+cffi",
        "portal+requests",
    }

    prompted_flows = []

    def prompt_mfa():
        prompted_flows.append(c._mfa_flow)
        return "000000"

    def fake_complete_mfa(_code):
        c.di_token = f"{c._mfa_flow}-token"

    with (
        patch.object(c, "_widget_web_login", side_effect=_uncertain_widget_mfa(c)),
        patch.object(c, "_complete_mfa", side_effect=fake_complete_mfa),
    ):
        c.login("e@x.com", "pw", prompt_mfa=prompt_mfa)

    assert prompted_flows == ["widget"]
    assert c.di_token == "widget-token"  # noqa: S105


def test_uncertain_widget_mfa_with_return_on_mfa_falls_through_first():
    """return_on_mfa=True must also give later strategies a chance before
    reporting "needs_mfa" for the uncertain widget state.
    """
    c = client_mod.Client(verify_login=False)
    c.skip_strategies = {"mobile+cffi", "mobile+requests", "portal+requests"}

    def portal_strategy(_email, _password):
        c.di_token = "portal-token"  # noqa: S105

    with (
        patch.object(c, "_widget_web_login", side_effect=_uncertain_widget_mfa(c)),
        patch.object(c, "_portal_web_login_cffi", side_effect=portal_strategy),
    ):
        status, _ = c.login("e@x.com", "pw", return_on_mfa=True)

    assert status is None
    assert c.di_token == "portal-token"  # noqa: S105
