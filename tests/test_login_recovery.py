"""Tests for login robustness: in-chain token validation, self-healing from
poisoned cached tokens, and the logout() helper.

All in-process — no network. We mock the strategy methods and ``connectapi``
on a real ``Client`` / ``Garmin`` instance.
"""

import json
import os
from unittest.mock import patch

import pytest

import garminconnect
from garminconnect import client as client_mod
from garminconnect.exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
)

# ----- _verify_token -----


def test_verify_token_true_on_success():
    c = client_mod.Client()
    with patch.object(c, "connectapi", return_value={"displayName": "x"}):
        assert c._verify_token() is True


def test_verify_token_false_on_401():
    c = client_mod.Client()
    with patch.object(
        c, "connectapi", side_effect=GarminConnectConnectionError("API Error 401 - x")
    ):
        assert c._verify_token() is False


def test_verify_token_false_on_403():
    c = client_mod.Client()
    with patch.object(
        c, "connectapi", side_effect=GarminConnectConnectionError("API Error 403 - x")
    ):
        assert c._verify_token() is False


def test_verify_token_inconclusive_keeps_token():
    """A transient 5xx must not reject an otherwise-working token."""
    c = client_mod.Client()
    with patch.object(
        c, "connectapi", side_effect=GarminConnectConnectionError("API Error 503 - x")
    ):
        assert c._verify_token() is True


# ----- _clear_auth_state -----


def test_clear_auth_state_wipes_tokens():
    c = client_mod.Client()
    c.di_token = "a"
    c.di_refresh_token = "b"
    c.di_client_id = "c"
    c.jwt_web = "d"
    c.csrf_token = "e"
    c._clear_auth_state()
    assert not any(
        [c.di_token, c.di_refresh_token, c.di_client_id, c.jwt_web, c.csrf_token]
    )


# ----- in-chain validation falls through a rejected token -----


def test_chain_falls_through_rejected_token():
    """A strategy that gets a token the API rejects must not win the chain;
    the next strategy that validates should.
    """
    c = client_mod.Client()
    # Only exercise the two mobile strategies for a deterministic 2-step chain.
    c.skip_strategies = {"widget+cffi", "portal+cffi", "portal+requests"}

    def first_strategy(_email, _password):
        c.di_token = "poisoned"

    def second_strategy(_email, _password):
        c.di_token = "good"

    # First strategy's token is rejected (401), second's is accepted.
    verify_results = iter([False, True])

    with (
        patch.object(c, "_mobile_login_cffi", side_effect=first_strategy),
        patch.object(c, "_mobile_login_requests", side_effect=second_strategy),
        patch.object(c, "_verify_token", side_effect=lambda: next(verify_results)),
    ):
        c.login("e@x.com", "pw")

    assert c.di_token == "good"


def test_verify_login_false_accepts_first_token():
    """With verify_login=False, the first strategy to get a token wins, even
    if it would have been rejected — legacy behavior.
    """
    c = client_mod.Client(verify_login=False)
    c.skip_strategies = {"widget+cffi", "portal+cffi", "portal+requests"}

    def first_strategy(_email, _password):
        c.di_token = "first"

    with (
        patch.object(c, "_mobile_login_cffi", side_effect=first_strategy),
        patch.object(c, "_verify_token") as verify,
    ):
        c.login("e@x.com", "pw")

    assert c.di_token == "first"
    verify.assert_not_called()


# ----- logout() -----


def test_http_post_uses_default_timeout():
    c = client_mod.Client()
    with (
        patch.object(client_mod, "HAS_CFFI", False),
        patch.object(client_mod.requests, "post") as post,
    ):
        c._http_post("https://example.invalid/token")

    post.assert_called_once_with("https://example.invalid/token", timeout=30)


def test_logout_clears_state_and_tokens(tmp_path):
    tokenfile = tmp_path / "garmin_tokens.json"
    tokenfile.write_text("{}")
    unrelated_file = tmp_path / "keep-me.txt"
    unrelated_file.write_text("important")
    g = garminconnect.Garmin("e@x.com", "pw")
    g.client.di_token = "tok"

    g.logout(str(tmp_path))

    assert g.client.di_token is None
    assert tmp_path.exists()
    assert not tokenfile.exists()
    assert unrelated_file.read_text() == "important"


@pytest.mark.parametrize("filename", ["tokens.json", "tokens.JSON"])
def test_logout_removes_explicit_token_file_only(tmp_path, filename):
    tokenfile = tmp_path / filename
    tokenfile.write_text("{}")
    g = garminconnect.Garmin("e@x.com", "pw")

    g.logout(str(tokenfile))

    assert not tokenfile.exists()
    assert tmp_path.exists()


def test_logout_no_tokenstore_is_safe():
    g = garminconnect.Garmin("e@x.com", "pw")
    g.client.di_token = "tok"
    # No path, no GARMINTOKENS — must not raise, still clears memory.
    with patch.dict("os.environ", {}, clear=False):
        import os

        os.environ.pop("GARMINTOKENS", None)
        g.logout()
    assert g.client.di_token is None


# ----- disk-token symlink protection -----


def test_load_refuses_symlink(tmp_path, make_symlink):
    """A pre-planted symlink at the token path must not redirect the read."""
    real_target = tmp_path / "attacker_tokens.json"
    real_target.write_text('{"di_token": "x"}')
    link = tmp_path / "garmin_tokens.json"
    make_symlink(real_target, link)

    c = client_mod.Client(verify_login=False)
    with pytest.raises(GarminConnectConnectionError):
        c.load(str(link))


def test_login_refuses_symlinked_tokenstore_write(tmp_path, make_symlink):
    """Garmin.login() must not resolve() a tokenstore symlink before the
    anti-symlink validation runs: after a fresh credential login, the
    persisted tokens must not be written through the symlink into the
    attacker-controlled target.
    """
    attacker_dir = tmp_path / "attacker_controlled"
    attacker_dir.mkdir()
    link = tmp_path / "victim-tokenstore"
    make_symlink(attacker_dir, link)

    g = garminconnect.Garmin("e@x.com", "pw")
    with (
        patch.object(g.client, "login", return_value=(None, None)) as chain,
        patch.object(g, "_load_profile_and_settings"),
    ):
        g.login(str(link))

    chain.assert_called_once()  # loading through the symlink failed closed
    assert not any(attacker_dir.iterdir())  # nothing written into the target


def test_login_refuses_auth_state_injection_via_symlink(tmp_path, make_symlink):
    """An attacker-seeded token file inside a symlinked tokenstore target
    must not be adopted by Garmin.login().
    """
    attacker_dir = tmp_path / "attacker_controlled"
    attacker_dir.mkdir()
    (attacker_dir / "garmin_tokens.json").write_text(
        json.dumps(
            {
                "di_token": "ATTACKER_TOKEN",
                "di_refresh_token": "ATTACKER_REFRESH",
                "di_client_id": "c",
            }
        )
    )
    link = tmp_path / "victim-tokenstore"
    make_symlink(attacker_dir, link)

    g = garminconnect.Garmin("e@x.com", "pw")
    with (
        patch.object(g.client, "login", return_value=(None, None)) as chain,
        patch.object(g, "_load_profile_and_settings"),
    ):
        g.login(str(link))

    # Credential login ran instead of silently adopting the attacker's tokens.
    chain.assert_called_once()
    assert g.client.di_token != "ATTACKER_TOKEN"


def test_load_reads_regular_file(tmp_path):
    """A normal token file should load cleanly."""
    tokenfile = tmp_path / "garmin_tokens.json"
    tokenfile.write_text('{"di_token": "t", "di_refresh_token": "r", "di_client_id": "c"}')

    c = client_mod.Client(verify_login=False)
    c.load(str(tokenfile))

    assert c.di_token == "t"
    assert c.di_refresh_token == "r"
    assert c.di_client_id == "c"


# ----- constructor validation -----


def test_verify_login_rejects_non_bool():
    with pytest.raises(ValueError):
        garminconnect.Garmin("e@x.com", "pw", verify_login="yes")


def test_verify_login_default_true():
    g = garminconnect.Garmin("e@x.com", "pw")
    assert g.client.verify_login is True


# ----- disk-token self-healing -----


def test_poisoned_cached_tokens_trigger_fresh_login():
    """If resumed cached tokens are rejected, login() discards them and runs
    the credential strategy chain, then succeeds.
    """
    g = garminconnect.Garmin("e@x.com", "pw")

    # Pretend cached tokens loaded successfully...
    with (
        patch.object(g.client, "load"),
        patch.object(g.client, "_token_expires_soon", return_value=False),
    ):
        # ...but the first profile fetch (resumed token) fails auth, and after
        # a fresh login the retry succeeds.
        load_calls = {"n": 0}

        def fake_load_profile():
            load_calls["n"] += 1
            if load_calls["n"] == 1:
                raise GarminConnectAuthenticationError(
                    "Failed to retrieve social profile"
                )
            # second call (after fresh login) succeeds
            return None

        with (
            patch.object(
                g, "_load_profile_and_settings", side_effect=fake_load_profile
            ),
            patch.object(g.client, "login", return_value=(None, None)) as chain,
            patch.object(g.client, "dump"),
        ):
            g.login("/tmp/faketokens")

        chain.assert_called_once()  # fresh strategy chain was run
        assert load_calls["n"] == 2  # retried profile after re-login
