"""Authenticated HTTP transport for the Garmin Connect API tier (connectapi)."""

import logging
from collections.abc import Iterator, Mapping
from typing import Any
from urllib.parse import unquote

from ..exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectNotFoundError,
)
from ._base import _ClientState
from .constants import (
    _QUERY_VALUE_RE,
    NATIVE_API_USER_AGENT,
    NATIVE_X_GARMIN_USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


def _sanitize_exception_text(err: Exception) -> str:
    """Render an exception for logs/messages with URL query values redacted.

    ``requests`` embeds the full request URL — query string included — in its
    exception text. On the login fallback path that URL carries the CAS
    service ticket (``?ticket=ST-...``), so logging or re-raising the raw
    exception would leak a credential into application logs and bug reports.
    """
    return _QUERY_VALUE_RE.sub(r"\1<redacted>", f"{type(err).__name__}: {err}")


def _iter_file_objects(kwargs: dict[str, Any]) -> Iterator[Any]:
    """Yield file-like objects referenced by request kwargs (files/data)."""
    files = kwargs.get("files")
    if isinstance(files, Mapping):
        values = list(files.values())
    elif isinstance(files, list | tuple):
        values = [v for _, v in files]
    else:
        values = []
    for value in values:
        # requests accepts fileobj or (name, fileobj[, content_type[, headers]])
        fileobj = (
            value[1] if isinstance(value, tuple | list) and len(value) >= 2 else value
        )
        if hasattr(fileobj, "read"):
            yield fileobj
    data = kwargs.get("data")
    if hasattr(data, "read"):
        yield data


def _capture_file_positions(
    kwargs: dict[str, Any],
) -> list[tuple[Any, int]] | None:
    """Record the stream position of each file-like body before a request.

    Returns None when any body cannot be repositioned, meaning a retry
    would re-read from EOF and silently send empty/truncated content.
    """
    positions: list[tuple[Any, int]] = []
    for fileobj in _iter_file_objects(kwargs):
        try:
            if not fileobj.seekable():
                return None
            positions.append((fileobj, fileobj.tell()))
        except (OSError, ValueError, AttributeError):
            return None
    data = kwargs.get("data")
    if data is not None and not hasattr(data, "read") and isinstance(data, Iterator):
        # Streamed iterable body (e.g. a generator): attempt #1 consumes it
        # and it cannot be rewound, so a retry must not be attempted.
        return None
    return positions


def _restore_file_positions(positions: list[tuple[Any, int]]) -> bool:
    """Rewind file-like bodies to their pre-request positions. False on failure."""
    try:
        for fileobj, pos in positions:
            fileobj.seek(pos)
    except (OSError, ValueError, AttributeError):
        return False
    return True


def _native_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers: dict[str, str] = {
        "User-Agent": NATIVE_API_USER_AGENT,
        "X-Garmin-User-Agent": NATIVE_X_GARMIN_USER_AGENT,
        "X-Garmin-Paired-App-Version": "10861",
        "X-Garmin-Client-Platform": "Android",
        "X-App-Ver": "10861",
        "X-Lang": "en",
        "X-GCExperience": "GC5",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra:
        headers.update(extra)
    return headers


class _EmptyJSONResp:
    """Stand-in response for HTTP 204 so callers can still call ``.json()``."""

    status_code = 204
    content = b""

    def json(self) -> Any:
        return {}

    def __repr__(self) -> str:
        return "{}"

    def __str__(self) -> str:
        return "{}"


class ApiTransportMixin(_ClientState):
    """Send authenticated requests to connectapi and translate failures."""

    def get_api_headers(self) -> dict[str, str]:
        if not self.is_authenticated:
            raise GarminConnectAuthenticationError(
                "Not authenticated - call Garmin.login() first"
            )
        if self.di_token:
            return _native_headers(
                {
                    "Authorization": f"Bearer {self.di_token}",
                    "Accept": "application/json",
                }
            )
        # JWT_WEB fallback
        headers: dict[str, str] = {
            "Accept": "application/json",
            "NK": "NT",
            "Origin": self._connect,
            "Referer": f"{self._connect}/modern/",
            "DI-Backend": f"connectapi.{self.domain}",
            "Cookie": f"JWT_WEB={self.jwt_web}",
        }
        if self.csrf_token:
            headers["connect-csrf-token"] = str(self.csrf_token)
        return headers

    def connectapi(self, path: str, **kwargs: Any) -> Any:
        return self._run_request("GET", path, **kwargs).json()

    def request(self, method: str, _domain: str, path: str, **kwargs: Any) -> Any:
        kwargs.pop("api", None)
        return self._run_request(method, path, **kwargs)

    def _api_call(self, method: str, path: str, **kwargs: Any) -> Any:
        """Run a write request; with ``api=True`` return its parsed JSON body."""
        api = kwargs.pop("api", False)
        resp = self._run_request(method, path, **kwargs)
        if api:
            return resp.json() if hasattr(resp, "json") else None
        return resp

    def post(self, _domain: str, path: str, **kwargs: Any) -> Any:
        return self._api_call("POST", path, **kwargs)

    def put(self, _domain: str, path: str, **kwargs: Any) -> Any:
        return self._api_call("PUT", path, **kwargs)

    def delete(self, _domain: str, path: str, **kwargs: Any) -> Any:
        return self._api_call("DELETE", path, **kwargs)

    def download(self, path: str, **kwargs: Any) -> bytes:
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update({"Accept": "*/*"})
        return self._run_request("GET", path, **kwargs).content

    def _resolve_url(self, path: str) -> str:
        """Validate an API path (or full Garmin URL) and return the absolute URL."""
        # Defense-in-depth: callers must pass clean path components; query strings
        # belong in the `params` kwarg, not embedded in the path. Validate the
        # percent-decoded form: requests' requote_uri() decodes unreserved
        # characters (e.g. %2e -> .) after this check, so a literal-only match
        # would let a %2e%2e traversal slip through.
        decoded_path = unquote(path)
        # A quoted display name may legitimately contain a run of dots (e.g.
        # "first..last"); only a path *segment* that is exactly ".." (or
        # "..;<matrix-params>", a known filter-bypass trick) is traversal.
        has_traversal_segment = any(
            segment.split(";", 1)[0] == ".." for segment in decoded_path.split("/")
        )
        if (
            has_traversal_segment
            or "?" in decoded_path
            or "#" in decoded_path
            or "\\" in decoded_path
        ):
            raise ValueError(f"Invalid API path: {path!r}")

        if path.startswith("https://"):
            # A few Garmin services live on sibling hosts (e.g. the ECG
            # service on ghs.<domain>); allow a full URL on the Garmin domain.
            host = path.split("/", 3)[2]
            if not host.endswith("." + self._domain) or "@" in host:
                raise ValueError(f"Invalid API host: {host!r}")
            return path
        return f"{self._connectapi}/{path.lstrip('/')}"

    def _run_request(self, method: str, path: str, **kwargs: Any) -> Any:
        with self._token_lock:
            if self.is_authenticated and self._token_expires_soon():
                self._refresh_session()

        url = self._resolve_url(path)

        if "timeout" not in kwargs:
            kwargs["timeout"] = 15

        headers = self.get_api_headers()
        custom_headers = kwargs.pop("headers", {})
        headers.update(custom_headers)

        sess = self._api_session
        # Snapshot stream positions of any file bodies so a 401 retry can
        # rewind them; attempt #1 reads file handles to EOF, and re-sending
        # the same kwargs would otherwise upload an empty/truncated body.
        file_positions = _capture_file_positions(kwargs)
        resp = sess.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            with self._token_lock:
                self._refresh_session()
            if file_positions is not None and _restore_file_positions(file_positions):
                headers = self.get_api_headers()
                headers.update(custom_headers)
                resp = sess.request(method, url, headers=headers, **kwargs)
            else:
                # Unseekable/unrewindable file body: retrying would silently
                # send an empty part. Fall through so the 401 raises below.
                _LOGGER.debug("Skipping 401 retry: request body is not rewindable")

        if resp.status_code == 204:
            return _EmptyJSONResp()

        if resp.status_code >= 400:
            error_msg = f"API Error {resp.status_code}"
            safe_detail = ""
            try:
                error_data = resp.json()
                if isinstance(error_data, dict):
                    detail = (
                        error_data.get("message")
                        or error_data.get("content")
                        or error_data.get("detailedImportResult", {})
                        .get("failures", [{}])[0]
                        .get("messages", [""])[0]
                    )
                    # Upload failures carry {"code": ..., "content": "..."};
                    # use the text, and never put other structures in errors.
                    if isinstance(detail, dict):
                        detail = detail.get("content") or detail.get("message")
                    safe_detail = detail if isinstance(detail, str) else ""
            except Exception as e:
                _LOGGER.debug("Could not extract safe error detail: %s", e)
            if safe_detail:
                error_msg += f" - {safe_detail}"
            # Log only the status, not the raw body: it may contain account
            # or session metadata the surrounding safe_detail extraction
            # above was specifically trying to avoid exposing.
            _LOGGER.debug("API error response: status=%s", resp.status_code)
            # A 404 is a missing resource, not a connectivity failure.
            error: GarminConnectConnectionError
            if resp.status_code == 404:
                error = GarminConnectNotFoundError(error_msg)
            else:
                error = GarminConnectConnectionError(error_msg)
            error.response = resp
            raise error

        return resp
