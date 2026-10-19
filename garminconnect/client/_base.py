"""Shared state and cross-module contract of the Garmin Connect client.

``Client`` is assembled from mixins that each cover one concern (login
strategies, session/token exchange, token storage, API transport). The mixins
need each other's attributes and a handful of each other's methods; this base
class declares that contract once so every mixin is type-checked against the
same state and no mixin has to know which sibling implements a method.
"""

import threading
from typing import Any


class _ClientState:
    """Attributes set by ``Client.__init__`` and methods shared between mixins."""

    # Domain-aware endpoints
    domain: str
    _domain: str
    _sso: str
    _connect: str
    _connectapi: str
    _ios_service_url: str
    _mobile_sso_service_url: str
    _portal_service_url: str
    _di_token_url: str

    # Native Bearer tokens (primary auth)
    di_token: str | None
    di_refresh_token: str | None
    di_client_id: str | None
    # JWT_WEB cookie auth (fallback when the DI token exchange fails)
    jwt_web: str | None
    csrf_token: str | None

    # Sessions: ``cs`` carries SSO/CAS cookies, ``_api_session`` never does.
    cs: Any
    _api_session: Any

    _tokenstore_path: str | None
    _token_lock: threading.RLock
    _mfa_pending: bool
    skip_strategies: set[str]
    verify_login: bool
    _last_rejection_status: int | None

    # MFA-in-progress bookkeeping (None when no MFA is pending)
    _mfa_session: Any
    _mfa_login_params: Any
    _mfa_post_headers: Any
    _mfa_service_url: Any
    _mfa_flow: Any
    _mfa_method: Any
    _widget_csrf_token: str | None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.di_token or self.jwt_web)

    # --- implemented by the transport mixin ---------------------------------
    def connectapi(self, path: str, **kwargs: Any) -> Any:
        raise NotImplementedError

    def get_api_headers(self) -> dict[str, str]:
        raise NotImplementedError

    # --- implemented by the token-store mixin -------------------------------
    def dump(self, path: str) -> None:
        raise NotImplementedError

    def _token_expires_soon(self) -> bool:
        raise NotImplementedError

    def _extract_client_id_from_jwt(self, token: str) -> str | None:
        raise NotImplementedError

    # --- implemented by the session mixin -----------------------------------
    def _establish_session(
        self, ticket: str, sess: Any = None, service_url: str | None = None
    ) -> None:
        raise NotImplementedError

    def _refresh_session(self) -> None:
        raise NotImplementedError

    def _verify_token(self) -> bool:
        raise NotImplementedError

    def _clear_auth_state(self, *, keep_tokenstore_path: bool = False) -> None:
        raise NotImplementedError

    def _clear_mfa_pending_state(self) -> None:
        raise NotImplementedError

    def _token_rejected_message(self, message: str) -> str:
        raise NotImplementedError

    # --- implemented by the login mixin -------------------------------------
    def _complete_mfa(self, mfa_code: str) -> None:
        raise NotImplementedError
