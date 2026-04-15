"""Regression tests for ``_handle_api_errors`` decorator.

Covers the critical bug where a generic ``except Exception`` at the end of
the decorator was swallowing domain-specific ``GarminConnectAuthenticationError``
and ``GarminConnectTooManyRequestsError`` raised directly by
``client._run_request`` (and the login flow) and wrapping them as
``GarminConnectConnectionError`` — silently losing the specific error type.
See PR #352 review.
"""

import pytest
from requests import HTTPError
from requests.models import Response

from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    _handle_api_errors,
)


def _http_error(status: int, message: str = "boom") -> HTTPError:
    resp = Response()
    resp.status_code = status
    exc = HTTPError(message)
    exc.response = resp  # type: ignore[attr-defined]
    return exc


class _Dummy:
    """Stand-in for ``Garmin`` — the decorator only needs ``self`` to be any
    object so it can forward the call through."""


def test_propagates_too_many_requests_unchanged() -> None:
    """A ``GarminConnectTooManyRequestsError`` raised from inside the wrapped
    function must propagate unchanged — not be wrapped as a generic
    connection error. This is the exact bug from CodeRabbit on PR #352."""

    @_handle_api_errors("API call")
    def inner(self: object, path: str) -> None:
        raise GarminConnectTooManyRequestsError("rate limited directly")

    with pytest.raises(GarminConnectTooManyRequestsError) as excinfo:
        inner(_Dummy(), "/foo")
    assert "rate limited directly" in str(excinfo.value)


def test_propagates_authentication_error_unchanged() -> None:
    """A ``GarminConnectAuthenticationError`` raised from inside the wrapped
    function must propagate unchanged."""

    @_handle_api_errors("API call")
    def inner(self: object, path: str) -> None:
        raise GarminConnectAuthenticationError("auth failed directly")

    with pytest.raises(GarminConnectAuthenticationError) as excinfo:
        inner(_Dummy(), "/foo")
    assert "auth failed directly" in str(excinfo.value)


def test_http_401_maps_to_authentication_error() -> None:
    @_handle_api_errors("API call")
    def inner(self: object, path: str) -> None:
        raise _http_error(401, "unauthorized")

    with pytest.raises(GarminConnectAuthenticationError) as excinfo:
        inner(_Dummy(), "/foo")
    assert "Authentication failed" in str(excinfo.value)


def test_http_429_maps_to_too_many_requests() -> None:
    @_handle_api_errors("API call")
    def inner(self: object, path: str) -> None:
        raise _http_error(429, "slow down")

    with pytest.raises(GarminConnectTooManyRequestsError) as excinfo:
        inner(_Dummy(), "/foo")
    assert "Rate limit exceeded" in str(excinfo.value)


def test_http_404_maps_to_client_error() -> None:
    @_handle_api_errors("Download")
    def inner(self: object, path: str) -> None:
        raise _http_error(404, "nope")

    with pytest.raises(GarminConnectConnectionError) as excinfo:
        inner(_Dummy(), "/foo")
    assert "Download client error (404)" in str(excinfo.value)


def test_http_500_maps_to_generic_http_error() -> None:
    @_handle_api_errors("API call")
    def inner(self: object, path: str) -> None:
        raise _http_error(500, "server")

    with pytest.raises(GarminConnectConnectionError) as excinfo:
        inner(_Dummy(), "/foo")
    assert "HTTP error" in str(excinfo.value)


def test_existing_connection_error_without_status_still_wrapped() -> None:
    """A plain ``GarminConnectConnectionError`` with no ``.response`` still
    falls through to the HTTP-error wrap branch."""

    @_handle_api_errors("API call")
    def inner(self: object, path: str) -> None:
        raise GarminConnectConnectionError("original message")

    with pytest.raises(GarminConnectConnectionError) as excinfo:
        inner(_Dummy(), "/foo")
    assert "original message" in str(excinfo.value)


def test_generic_exception_wrapped_as_connection_error() -> None:
    @_handle_api_errors("API call")
    def inner(self: object, path: str) -> None:
        raise ValueError("something unexpected")

    with pytest.raises(GarminConnectConnectionError) as excinfo:
        inner(_Dummy(), "/foo")
    assert "Connection error" in str(excinfo.value)
    assert "something unexpected" in str(excinfo.value)


def test_successful_call_returns_value_unchanged() -> None:
    @_handle_api_errors("API call")
    def inner(self: object, path: str, extra: int = 0) -> dict[str, int]:
        return {"path": len(path), "extra": extra}

    result = inner(_Dummy(), "/foo", extra=5)
    assert result == {"path": 4, "extra": 5}
