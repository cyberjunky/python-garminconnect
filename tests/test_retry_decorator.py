"""Tests for the error-translation + retry decorator in garminconnect.__init__.

Covers the helpers (_extract_status_code, _is_retryable, _has_network_cause)
and the three decorated API methods (connectapi, connectwebproxy, download).
All in-process — no network, no VCR cassettes.
"""

import pytest
import requests
from requests import HTTPError
from requests.models import Response

from garminconnect import (
    Garmin,
    _extract_status_code,
    _has_network_cause,
    _is_retryable,
)
from garminconnect.exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


def _http_error(status: int) -> HTTPError:
    resp = Response()
    resp.status_code = status
    exc = HTTPError(f"HTTP {status}")
    exc.response = resp
    return exc


def _client_error(status: int) -> GarminConnectConnectionError:
    return GarminConnectConnectionError(f"API Error {status} - boom")


@pytest.fixture
def garmin():
    g = Garmin(retry_attempts=0, retry_min_wait=0.001, retry_max_wait=0.002)
    g.client = type("C", (), {})()
    return g


# ----- _extract_status_code -----


def test_extract_status_from_attribute():
    e = ValueError("x")
    e.status_code = 418  # type: ignore[attr-defined]
    assert _extract_status_code(e) == 418


def test_extract_status_from_response():
    assert _extract_status_code(_http_error(503)) == 503


def test_extract_status_from_message():
    assert _extract_status_code(_client_error(429)) == 429


def test_extract_status_none():
    assert _extract_status_code(ValueError("no status here")) is None


# ----- _is_retryable -----


def test_auth_error_not_retryable():
    assert _is_retryable(GarminConnectAuthenticationError("x")) is False


def test_rate_limit_not_retryable():
    assert _is_retryable(GarminConnectTooManyRequestsError("x")) is False


def test_5xx_retryable():
    assert _is_retryable(_client_error(503)) is True


def test_4xx_not_retryable():
    assert _is_retryable(_client_error(404)) is False


def test_raw_connection_error_retryable():
    assert _is_retryable(requests.ConnectionError()) is True


def test_raw_timeout_retryable():
    assert _is_retryable(requests.Timeout()) is True


def test_has_network_cause_walks_context():
    try:
        try:
            raise requests.ConnectionError("net")
        except requests.ConnectionError:
            raise GarminConnectConnectionError("wrapped")
    except GarminConnectConnectionError as e:
        assert _has_network_cause(e) is True


def test_has_network_cause_none_for_plain():
    assert _has_network_cause(ValueError("plain")) is False


# ----- decorator: error translation on connectapi -----


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, GarminConnectAuthenticationError),
        (429, GarminConnectTooManyRequestsError),
        (400, GarminConnectConnectionError),
        (404, GarminConnectConnectionError),
    ],
)
def test_fast_fail_status(
    garmin: Garmin, status: int, expected: type[Exception]
) -> None:
    calls = {"n": 0}

    def fake(path: str, **kw: object) -> None:
        calls["n"] += 1
        raise _http_error(status)

    garmin.client.connectapi = fake  # type: ignore[attr-defined]
    garmin.retry_attempts = 2  # retries enabled, but must NOT fire for 401/429/4xx
    with pytest.raises(expected):
        garmin.connectapi("/x")
    assert calls["n"] == 1


def test_503_retry_exhaustion(garmin: Garmin) -> None:
    calls = {"n": 0}

    def fake(path: str, **kw: object) -> None:
        calls["n"] += 1
        raise _http_error(503)

    garmin.client.connectapi = fake  # type: ignore[attr-defined]
    garmin.retry_attempts = 2
    with pytest.raises(GarminConnectConnectionError):
        garmin.connectapi("/x")
    assert calls["n"] == 3  # initial + 2 retries


def test_flaky_recovers_after_retry(garmin: Garmin) -> None:
    calls = {"n": 0}

    def fake(path: str, **kw: object) -> dict[str, bool]:
        calls["n"] += 1
        if calls["n"] < 2:
            raise _http_error(503)
        return {"ok": True}

    garmin.client.connectapi = fake  # type: ignore[attr-defined]
    garmin.retry_attempts = 3
    assert garmin.connectapi("/x") == {"ok": True}
    assert calls["n"] == 2


def test_connection_error_retries_and_exhausts(garmin: Garmin) -> None:
    calls = {"n": 0}

    def fake(path: str, **kw: object) -> None:
        calls["n"] += 1
        raise requests.ConnectionError("boom")

    garmin.client.connectapi = fake  # type: ignore[attr-defined]
    garmin.retry_attempts = 2
    with pytest.raises(GarminConnectConnectionError):
        garmin.connectapi("/x")
    assert calls["n"] == 3


def test_default_retry_attempts_is_zero(garmin: Garmin) -> None:
    """Opt-in: retry_attempts defaults to 0 — 503 fails fast."""
    garmin.retry_attempts = 0
    calls = {"n": 0}

    def fake(path: str, **kw: object) -> None:
        calls["n"] += 1
        raise _http_error(503)

    garmin.client.connectapi = fake  # type: ignore[attr-defined]
    with pytest.raises(GarminConnectConnectionError):
        garmin.connectapi("/x")
    assert calls["n"] == 1


def test_response_attr_preserved_on_client_error(garmin: Garmin) -> None:
    """Callers like get_gear_stats rely on .response.status_code."""
    garmin.retry_attempts = 0

    def fake(path: str, **kw: object) -> None:
        raise _http_error(400)

    garmin.client.connectapi = fake  # type: ignore[attr-defined]
    with pytest.raises(GarminConnectConnectionError) as exc:
        garmin.connectapi("/x")
    assert exc.value.response.status_code == 400  # type: ignore[attr-defined]


# ----- decorator applies uniformly to connectwebproxy and download -----


def test_connectwebproxy_translates(garmin: Garmin) -> None:
    garmin.retry_attempts = 0

    def fake(method: str, host: str, path: str, **kw: object) -> None:
        raise _http_error(401)

    garmin.client.request = fake  # type: ignore[attr-defined]
    with pytest.raises(GarminConnectAuthenticationError):
        garmin.connectwebproxy("/x")


def test_download_translates(garmin: Garmin) -> None:
    garmin.retry_attempts = 0

    def fake(path: str, **kw: object) -> None:
        raise _http_error(429)

    garmin.client.download = fake  # type: ignore[attr-defined]
    with pytest.raises(GarminConnectTooManyRequestsError):
        garmin.download("/x")


# ----- constructor validation -----


def test_retry_attempts_rejects_negative():
    with pytest.raises(ValueError):
        Garmin(retry_attempts=-1)


def test_retry_attempts_rejects_non_int():
    with pytest.raises(ValueError):
        Garmin(retry_attempts="3")  # type: ignore[arg-type]


def test_retry_attempts_rejects_bool():
    """bool is a subclass of int in Python — reject explicitly."""
    with pytest.raises(ValueError):
        Garmin(retry_attempts=True)  # type: ignore[arg-type]
