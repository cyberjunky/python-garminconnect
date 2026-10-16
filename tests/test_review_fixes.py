"""Regression tests for review findings in the client and health code."""

import logging
import math
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

import garminconnect
from garminconnect.client import session as session_mod
from garminconnect.client import tokens as tokens_mod


def _jar_with(name, value):
    jar = requests.Session().cookies
    jar.set(name, value, domain="connect.garmin.com")
    return jar


def test_jwt_web_found_in_requests_cookie_jar():
    """A plain requests session has no ``cookies.jar``; the jar is the object."""
    assert session_mod._jwt_web_from_cookies(_jar_with("JWT_WEB", "tok")) == "tok"


def test_jwt_web_found_in_wrapped_jar():
    """curl_cffi exposes the jar as ``cookies.jar``."""
    wrapper = MagicMock()
    wrapper.jar = _jar_with("JWT_WEB", "tok")
    assert session_mod._jwt_web_from_cookies(wrapper) == "tok"


def test_jwt_web_absent():
    assert session_mod._jwt_web_from_cookies(_jar_with("other", "x")) is None


def test_unexpected_sso_response_body_is_not_logged(caplog):
    client = garminconnect.Garmin().client
    resp = MagicMock(status_code=200)
    resp.json.return_value = {
        "responseStatus": {"type": "SOMETHING_NEW"},
        "customerMfaInfo": {"email": "secret@example.com"},
    }
    sess = MagicMock()
    sess.post.return_value = resp
    with (
        caplog.at_level(logging.DEBUG, logger="garminconnect"),
        pytest.raises(garminconnect.GarminConnectConnectionError),
    ):
        client._post_credentials(
            sess,
            "test",
            "https://sso.garmin.com/mobile/api/login",
            {},
            {},
            service_url="https://example.invalid",
            flow="mobile",
            email="e@x.com",
            password="pw",
        )
    assert "secret@example.com" not in caplog.text
    assert "responseStatus=SOMETHING_NEW" in caplog.text


@pytest.mark.parametrize("bad", [True, False, math.nan, math.inf, -math.inf])
def test_hydration_rejects_bool_and_non_finite(bad):
    g = garminconnect.Garmin()
    with pytest.raises(ValueError):
        g.add_hydration_data(bad, cdate="2026-10-01")


@pytest.mark.skipif(os.name != "posix", reason="root-owned symlinks are POSIX only")
def test_root_owned_symlink_in_ancestry_is_allowed(tmp_path, monkeypatch, make_symlink):
    """A system symlink such as /home -> var/home cannot be planted by a user."""
    real = tmp_path / "var-home"
    (real / "user").mkdir(parents=True)
    link = tmp_path / "home"
    make_symlink(real, link)
    real_lstat = os.lstat

    def lstat(p, *a, **k):
        st = real_lstat(p, *a, **k)
        if Path(p) == link:
            return os.stat_result(
                (st.st_mode, st.st_ino, st.st_dev, st.st_nlink, 0, *st[5:])
            )
        return st

    monkeypatch.setattr(tokens_mod.os, "lstat", lstat)
    result = tokens_mod.token_file_path(str(link / "user" / "tokens.json"))
    assert result == link / "user" / "tokens.json"


@pytest.mark.skipif(os.name != "posix", reason="ownership check is POSIX only")
def test_user_owned_symlink_in_ancestry_is_rejected(tmp_path, make_symlink):
    if os.geteuid() == 0:
        pytest.skip("as root every symlink is root-owned")
    real = tmp_path / "elsewhere"
    real.mkdir()
    link = tmp_path / "store"
    make_symlink(real, link)
    with pytest.raises(ValueError, match="symlink"):
        tokens_mod.token_file_path(str(link / "tokens.json"))
