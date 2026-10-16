"""Session establishment and refresh: CAS ticket → DI token (or JWT_WEB cookie)."""

import contextlib
import logging
from typing import Any

import requests

from ..exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from ._base import _ClientState
from .constants import (
    _API_ERROR_STATUS_RE,
    _API_REJECTION_HINT,
    DI_CLIENT_IDS,
    DI_GRANT_TYPE,
    MOBILE_SSO_CLIENT_ID,
)
from .tokens import _build_basic_auth
from .transport import _native_headers, _sanitize_exception_text

_LOGGER = logging.getLogger(__name__)


def _jwt_web_from_cookies(cookies: Any) -> str | None:
    """Return the JWT_WEB cookie value from a session's cookies, if present.

    curl_cffi wraps its jar (``cookies.jar``); a requests ``RequestsCookieJar``
    is the jar itself, so iterate whichever one the session has.
    """
    for c in getattr(cookies, "jar", cookies):
        if c.name == "JWT_WEB":
            return str(c.value)
    return None


class SessionMixin(_ClientState):
    """Turn a CAS service ticket into API credentials and keep them fresh."""

    def _clear_auth_state(self, *, keep_tokenstore_path: bool = False) -> None:
        """Wipe all in-memory auth tokens and session state so the next login starts clean.

        ``keep_tokenstore_path`` preserves the persistence target: login() sets
        it via the Garmin wrapper *before* the credential flow runs, and a
        fresh login should keep persisting to the same store.
        """
        self.di_token = None
        self.di_refresh_token = None
        self.di_client_id = None
        self.jwt_web = None
        self.csrf_token = None
        if not keep_tokenstore_path:
            self._tokenstore_path = None
        self._clear_mfa_pending_state()
        # Drop any SSO / CAS / JWT_WEB cookies so a stale session cannot be
        # silently refreshed after logout.
        self.cs.cookies.clear()

    def _clear_mfa_pending_state(self) -> None:
        """Clear MFA-in-progress bookkeeping only — leaves auth tokens alone.

        Used both by ``_clear_auth_state()`` (as part of a full reset) and by
        ``resume_login()`` on success, where the just-obtained tokens must
        survive.
        """
        self._mfa_pending = False
        for attr in (
            "_mfa_session",
            "_mfa_login_params",
            "_mfa_post_headers",
            "_mfa_service_url",
            "_mfa_flow",
            "_mfa_method",
            "_widget_last_resp",
        ):
            setattr(self, attr, None)

    def _token_rejected_message(self, message: str) -> str:
        """Append the client/network-block hint when the rejection was a 403."""
        if self._last_rejection_status == 403:
            return f"{message} ({_API_REJECTION_HINT})"
        return message

    def _verify_token(self) -> bool:
        """Check that the current token is actually accepted by the API tier.

        A strategy can obtain a DI token from the auth host (HTTP 200) that the
        API tier (connectapi) then rejects with 401 "Token is not active" —
        this is account/region dependent (see issue #369). We confirm the token
        works with one lightweight authenticated call.

        Returns True if accepted, or if the check is inconclusive. Only a
        definitive auth rejection (401/403) returns False, so a transient
        network error or 5xx never blocks an otherwise-working login.
        """
        self._last_rejection_status = None
        try:
            self.connectapi("/userprofile-service/socialProfile")
            return True
        except GarminConnectConnectionError as e:
            msg = str(e)
            match = _API_ERROR_STATUS_RE.match(msg)
            status = int(match.group(1)) if match else None
            if status in (401, 403):
                self._last_rejection_status = status
                _LOGGER.warning(
                    "%s: %s",
                    self._token_rejected_message("Token rejected by API tier"),
                    msg,
                )
                return False
            _LOGGER.debug("Token validation inconclusive (kept): %s", msg)
            return True
        except Exception as e:
            _LOGGER.debug(
                "Token validation inconclusive (kept): %s",
                _sanitize_exception_text(e),
            )
            return True

    # ------------------------------------------------------------------ #
    #  SESSION ESTABLISHMENT — DI token first, JWT_WEB fallback          #
    # ------------------------------------------------------------------ #

    def _establish_session(
        self, ticket: str, sess: Any = None, service_url: str | None = None
    ) -> None:
        """Consume a CAS service ticket — DI token exchange first,
        fall back to JWT_WEB cookie auth.
        """
        try:
            self._exchange_service_ticket(ticket, service_url=service_url)
            return
        except Exception as e:
            _LOGGER.warning(
                "DI token exchange failed (%s), falling back to JWT_WEB",
                _sanitize_exception_text(e),
            )

        # Fallback: consume ticket via connect.garmin.com for JWT_WEB cookie
        if sess is not None:
            self.cs = sess

        svc = service_url or self._ios_service_url
        self.cs.get(
            svc,
            params={"ticket": ticket},
            allow_redirects=True,
            timeout=30,
        )

        jwt_web = _jwt_web_from_cookies(self.cs.cookies)
        if not jwt_web:
            raise GarminConnectAuthenticationError(
                "JWT_WEB cookie not set after ticket consumption"
            )
        self.jwt_web = jwt_web

    def _http_post(self, url: str, **kwargs: Any) -> Any:
        """POST using curl_cffi if available, else plain requests."""
        from garminconnect import client as _pkg

        timeout = kwargs.pop("timeout", 30)
        if _pkg.HAS_CFFI:
            return _pkg.cffi_requests.post(
                url, impersonate="chrome", timeout=timeout, **kwargs
            )
        return requests.post(url, timeout=timeout, **kwargs)

    def _di_token_post(self, client_id: str, accept: str, data: dict[str, str]) -> Any:
        """POST to the DI OAuth2 token endpoint on behalf of ``client_id``."""
        return self._http_post(
            self._di_token_url,
            headers=_native_headers(
                {
                    "Authorization": _build_basic_auth(client_id),
                    "Accept": accept,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cache-Control": "no-cache",
                }
            ),
            data=data,
            timeout=30,
        )

    def _exchange_service_ticket(
        self, ticket: str, service_url: str | None = None
    ) -> None:
        """Exchange a CAS service ticket for a native DI OAuth2 Bearer token.

        POST to the DI auth host for the configured domain (diauth.garmin.com,
        or diauth.garmin.cn for China accounts), trying each DI client ID in
        turn, and store the access token and refresh token.
        """
        # service_url must match the one used during SSO login
        svc_url = service_url or self._mobile_sso_service_url

        di_token = None
        di_refresh = None
        di_client_id = None

        for client_id in DI_CLIENT_IDS:
            r = self._di_token_post(
                client_id,
                "application/json,text/html;q=0.9,*/*;q=0.8",
                {
                    "client_id": client_id,
                    "service_ticket": ticket,
                    "grant_type": DI_GRANT_TYPE,
                    "service_url": svc_url,
                },
            )
            if r.status_code == 429:
                raise GarminConnectTooManyRequestsError(
                    "DI token exchange rate limited"
                )
            if not r.ok:
                # Log only the status: the error body from the token endpoint
                # isn't needed to diagnose a failed exchange.
                _LOGGER.debug(
                    "DI exchange failed for %s: HTTP %s", client_id, r.status_code
                )
                continue
            try:
                data = r.json()
                di_token = data["access_token"]
                di_refresh = data.get("refresh_token")
                di_client_id = self._extract_client_id_from_jwt(di_token) or client_id
                break
            except Exception as e:
                _LOGGER.debug("DI token parse failed for %s: %s", client_id, e)
                continue

        if not di_token:
            raise GarminConnectAuthenticationError(
                "DI token exchange failed for all client IDs"
            )

        self.di_token = di_token
        self.di_refresh_token = di_refresh
        self.di_client_id = di_client_id

    def _refresh_di_token(self) -> None:
        """Refresh the DI Bearer token using the stored refresh token."""
        if not self.di_refresh_token or not self.di_client_id:
            raise GarminConnectAuthenticationError("No DI refresh token available")
        with self._token_lock:
            # Re-check under the lock in case another thread already refreshed
            # while we were waiting.
            if not self.di_refresh_token or not self.di_client_id:
                raise GarminConnectAuthenticationError("No DI refresh token available")
            r = self._di_token_post(
                self.di_client_id,
                "application/json",
                {
                    "grant_type": "refresh_token",
                    "client_id": self.di_client_id,
                    "refresh_token": self.di_refresh_token,
                },
            )
            if not r.ok:
                _LOGGER.debug(
                    "DI token refresh failed: status=%s body=%r",
                    r.status_code,
                    r.text[:200],
                )
                raise GarminConnectAuthenticationError(
                    f"DI token refresh failed: {r.status_code}"
                )
            data = r.json()
            access_token = data["access_token"]
            self.di_token = access_token
            self.di_refresh_token = data.get("refresh_token", self.di_refresh_token)
            self.di_client_id = (
                self._extract_client_id_from_jwt(access_token) or self.di_client_id
            )

    def _persist_tokens(self) -> None:
        """Best-effort write of the current tokens to the configured store."""
        if self._tokenstore_path:
            with contextlib.suppress(Exception):
                self.dump(self._tokenstore_path)

    def _refresh_session(self) -> None:
        """Refresh auth — DI token refresh or legacy JWT_WEB CAS refresh."""
        with self._token_lock:
            if self.di_token:
                try:
                    self._refresh_di_token()
                    self._persist_tokens()
                except Exception as err:
                    _LOGGER.debug(
                        "DI token refresh failed: %s", _sanitize_exception_text(err)
                    )
                return

            # JWT_WEB refresh via CAS TGT
            if not self.is_authenticated:
                return
            try:
                self.cs.get(
                    f"{self._sso}/mobile/sso/en_US/sign-in",
                    params={
                        "clientId": MOBILE_SSO_CLIENT_ID,
                        "service": self._mobile_sso_service_url,
                    },
                    allow_redirects=True,
                    timeout=15,
                )
                jwt_web = _jwt_web_from_cookies(self.cs.cookies)
                if jwt_web:
                    self.jwt_web = jwt_web
                    _LOGGER.debug("Session refreshed via CAS TGT")
                    self._persist_tokens()
                    return

                with contextlib.suppress(Exception):
                    self.cs.post(
                        f"{self._connect}/services/auth/token/di-oauth/refresh",
                        headers={
                            "Accept": "application/json",
                            "NK": "NT",
                            "Referer": f"{self._connect}/modern/",
                        },
                        timeout=10,
                    )
                jwt_web = _jwt_web_from_cookies(self.cs.cookies)
                if jwt_web:
                    self.jwt_web = jwt_web
            except Exception as err:
                _LOGGER.debug("Refresh failed: %s", _sanitize_exception_text(err))
