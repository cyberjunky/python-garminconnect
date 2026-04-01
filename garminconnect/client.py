"""Authentication engine for Garmin Connect."""

import base64
import contextlib
import json
import logging
from pathlib import Path
from typing import Any

import requests

try:
    from curl_cffi import requests as cffi_requests

    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

from .exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

_LOGGER = logging.getLogger(__name__)

# Auth constants (matching Android GCM app)
MOBILE_SSO_CLIENT_ID = "GCM_ANDROID_DARK"
MOBILE_SSO_SERVICE_URL = "https://mobile.integration.garmin.com/gcm/android"
MOBILE_SSO_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; sdk_gphone64_arm64 Build/TE1A.220922.025; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.0.0 Mobile Safari/537.36"
)
NATIVE_API_USER_AGENT = "GCM-Android-5.23"
NATIVE_X_GARMIN_USER_AGENT = (
    "com.garmin.android.apps.connectmobile/5.23; ; Google/sdk_gphone64_arm64/google; "
    "Android/33; Dalvik/2.1.0"
)
DI_TOKEN_URL = "https://diauth.garmin.com/di-oauth2-service/oauth/token"  # noqa: S105
IT_TOKEN_URL = "https://services.garmin.com/api/oauth/token"  # noqa: S105
DI_GRANT_TYPE = (
    "https://connectapi.garmin.com/di-oauth2-service/oauth/grant/service_ticket"
)
DI_CLIENT_IDS = (
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2024Q4",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI",
)
IT_CLIENT_IDS = (
    "GARMIN_CONNECT_MOBILE_ANDROID_2025Q2",
    "GARMIN_CONNECT_MOBILE_ANDROID_2024Q4",
    "GARMIN_CONNECT_MOBILE_ANDROID",
)


def _build_basic_auth(client_id: str) -> str:
    return "Basic " + base64.b64encode(f"{client_id}:".encode()).decode()


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


class Client:
    """A client to communicate with Garmin Connect."""

    def __init__(self, domain: str = "garmin.com", **kwargs: Any) -> None:
        self.domain = domain
        self._sso = f"https://sso.{domain}"
        self._connect = f"https://connect.{domain}"
        self._connectapi = f"https://connectapi.{domain}"

        # Native Bearer tokens (primary auth)
        self.di_token: str | None = None
        self.di_refresh_token: str | None = None
        self.di_client_id: str | None = None
        self.it_token: str | None = None
        self.it_refresh_token: str | None = None
        self.it_client_id: str | None = None

        # JWT_WEB cookie auth (fallback when DI token is unavailable)
        self.jwt_web: str | None = None
        self.csrf_token: str | None = None

        # curl_cffi session for login flows
        self.cs: Any = None
        if HAS_CFFI:
            self.cs = cffi_requests.Session(impersonate="chrome")
        else:
            self.cs = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=kwargs.get("pool_connections", 20),
                pool_maxsize=kwargs.get("pool_maxsize", 20),
            )
            self.cs.mount("https://", adapter)

        self._tokenstore_path: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.di_token or self.jwt_web)

    def get_api_headers(self) -> dict[str, str]:
        if not self.is_authenticated:
            raise GarminConnectAuthenticationError("Not authenticated")
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

    def login(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Log in to Garmin Connect."""
        # Try login with curl_cffi first (TLS impersonation)
        if HAS_CFFI:
            try:
                return self._portal_login(
                    email,
                    password,
                    prompt_mfa=prompt_mfa,
                    return_on_mfa=return_on_mfa,
                )
            except Exception as e:
                _LOGGER.warning("curl_cffi login failed (%s), trying plain requests", e)

        # Fallback: same flow without curl_cffi
        return self._mobile_login(
            email,
            password,
            prompt_mfa=prompt_mfa,
            return_on_mfa=return_on_mfa,
        )

    def _portal_login(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Login via mobile SSO API using curl_cffi for TLS impersonation."""
        sess: Any = cffi_requests.Session(impersonate="chrome")

        # Step 1: GET mobile sign-in page (sets SESSION cookies)
        signin_url = f"{self._sso}/mobile/sso/en_US/sign-in"
        sess.get(
            signin_url,
            params={
                "clientId": MOBILE_SSO_CLIENT_ID,
                "service": MOBILE_SSO_SERVICE_URL,
            },
            headers={
                "User-Agent": MOBILE_SSO_USER_AGENT,
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.9",
            },
            timeout=30,
        )

        # Step 2: POST credentials
        login_params = {
            "clientId": MOBILE_SSO_CLIENT_ID,
            "locale": "en-US",
            "service": MOBILE_SSO_SERVICE_URL,
        }
        post_headers = {
            "User-Agent": MOBILE_SSO_USER_AGENT,
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": self._sso,
            "referer": f"{signin_url}?clientId={MOBILE_SSO_CLIENT_ID}&service={MOBILE_SSO_SERVICE_URL}",
        }
        r = sess.post(
            f"{self._sso}/mobile/api/login",
            params=login_params,
            headers=post_headers,
            json={
                "username": email,
                "password": password,
                "rememberMe": True,
                "captchaToken": "",
            },
            timeout=30,
        )
        r.raise_for_status()
        res = r.json()
        resp_type = res.get("responseStatus", {}).get("type")

        if resp_type == "MFA_REQUIRED":
            self._mfa_method = res.get("customerMfaInfo", {}).get(
                "mfaLastMethodUsed", "email"
            )
            self._mfa_cffi_session = sess
            self._mfa_cffi_params = login_params
            self._mfa_cffi_headers = post_headers

            if return_on_mfa:
                return "needs_mfa", sess

            if prompt_mfa:
                mfa_code = prompt_mfa()
                self._complete_mfa_portal(mfa_code)
                return None, None
            raise GarminConnectAuthenticationError(
                "MFA Required but no prompt_mfa mechanism supplied"
            )

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket, sess=sess)
            return None, None

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        raise GarminConnectAuthenticationError(f"Portal login failed: {res}")

    def _complete_mfa_portal(self, mfa_code: str) -> None:
        """Complete MFA verification via mobile API with curl_cffi."""
        sess = self._mfa_cffi_session
        r = sess.post(
            f"{self._sso}/mobile/api/mfa/verifyCode",
            params=self._mfa_cffi_params,
            headers=self._mfa_cffi_headers,
            json={
                "mfaMethod": getattr(self, "_mfa_method", "email"),
                "mfaVerificationCode": mfa_code,
                "rememberMyBrowser": True,
                "reconsentList": [],
                "mfaSetup": False,
            },
            timeout=30,
        )
        res = r.json()
        if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket, sess=sess)
            return
        raise GarminConnectAuthenticationError(f"MFA Verification failed: {res}")

    def _mobile_login(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Login via mobile SSO API using plain requests (fallback)."""
        sess = requests.Session()
        sess.headers.update(
            {
                "User-Agent": MOBILE_SSO_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

        sess.get(
            f"{self._sso}/mobile/sso/en_US/sign-in",
            params={
                "clientId": MOBILE_SSO_CLIENT_ID,
                "service": MOBILE_SSO_SERVICE_URL,
            },
        )

        r = sess.post(
            f"{self._sso}/mobile/api/login",
            params={
                "clientId": MOBILE_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": MOBILE_SSO_SERVICE_URL,
            },
            json={
                "username": email,
                "password": password,
                "rememberMe": True,
                "captchaToken": "",
            },
        )

        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError(
                "Login failed (429 Rate Limit). Try again later."
            )

        try:
            res = r.json()
        except Exception as err:
            raise GarminConnectConnectionError(
                f"Login failed (Not JSON): HTTP {r.status_code}"
            ) from err

        resp_type = res.get("responseStatus", {}).get("type")

        if resp_type == "MFA_REQUIRED":
            self._mfa_method = res.get("customerMfaInfo", {}).get(
                "mfaLastMethodUsed", "email"
            )
            self._mfa_session = sess

            if return_on_mfa:
                return "needs_mfa", self._mfa_session

            if prompt_mfa:
                mfa_code = prompt_mfa()
                self._complete_mfa(mfa_code)
                return None, None
            raise GarminConnectAuthenticationError(
                "MFA Required but no prompt_mfa mechanism supplied"
            )

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket)
            return None, None

        if (
            "status-code" in res.get("error", {})
            and res["error"]["status-code"] == "429"
        ):
            raise GarminConnectTooManyRequestsError("429 Rate Limit")

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        raise GarminConnectAuthenticationError(
            f"Unhandled Garmin Login JSON, Login failed: {res}"
        )

    def _complete_mfa(self, mfa_code: str) -> None:
        r = self._mfa_session.post(
            f"{self._sso}/mobile/api/mfa/verifyCode",
            params={
                "clientId": MOBILE_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": MOBILE_SSO_SERVICE_URL,
            },
            json={
                "mfaMethod": getattr(self, "_mfa_method", "email"),
                "mfaVerificationCode": mfa_code,
                "rememberMyBrowser": True,
                "reconsentList": [],
                "mfaSetup": False,
            },
        )
        res = r.json()
        if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket)
            return
        raise GarminConnectAuthenticationError(f"MFA Verification failed: {res}")

    def _establish_session(self, ticket: str, sess: Any = None) -> None:
        """Consume a CAS service ticket — try native DI token exchange first,
        fall back to JWT_WEB cookie auth.
        """
        try:
            self._exchange_service_ticket(ticket)
            return
        except Exception as e:
            _LOGGER.warning("DI token exchange failed (%s), falling back to JWT_WEB", e)

        # Fallback: consume ticket via connect.garmin.com for JWT_WEB cookie
        if sess is not None:
            self.cs = sess

        self.cs.get(
            MOBILE_SSO_SERVICE_URL,
            params={"ticket": ticket},
            allow_redirects=True,
            timeout=30,
        )

        jwt_web = None
        for c in self.cs.cookies.jar:
            if c.name == "JWT_WEB":
                jwt_web = c.value
                break

        if not jwt_web:
            raise GarminConnectAuthenticationError(
                "JWT_WEB cookie not set after ticket consumption"
            )
        self.jwt_web = jwt_web

    def _exchange_service_ticket(self, ticket: str) -> None:
        """Exchange a CAS service ticket for native DI + IT Bearer tokens.

        POST to diauth.garmin.com to get a DI OAuth2 token, then exchange
        for an IT token via services.garmin.com.
        """
        di_token = None
        di_refresh = None
        di_client_id = None

        for client_id in DI_CLIENT_IDS:
            r = requests.post(
                DI_TOKEN_URL,
                headers=_native_headers(
                    {
                        "Authorization": _build_basic_auth(client_id),
                        "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Cache-Control": "no-cache",
                    }
                ),
                data={
                    "client_id": client_id,
                    "service_ticket": ticket,
                    "grant_type": DI_GRANT_TYPE,
                    "service_url": MOBILE_SSO_SERVICE_URL,
                },
                timeout=30,
            )
            if r.status_code == 429:
                raise GarminConnectTooManyRequestsError(
                    "DI token exchange rate limited"
                )
            if not r.ok:
                _LOGGER.debug(
                    "DI exchange failed for %s: %s %s",
                    client_id,
                    r.status_code,
                    r.text[:200],
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

        # Exchange DI for IT token
        it_candidates = self._it_client_id_candidates(di_client_id or DI_CLIENT_IDS[0])
        for client_id in it_candidates:
            r = requests.post(
                f"{IT_TOKEN_URL}?grant_type=connect2_exchange",
                headers=_native_headers(
                    {
                        "Accept": "application/json,text/plain,*/*",
                        "Content-Type": "application/x-www-form-urlencoded",
                    }
                ),
                data={
                    "client_id": client_id,
                    "connect_access_token": di_token,
                },
                timeout=30,
            )
            if not r.ok:
                _LOGGER.debug("IT exchange failed for %s: %s", client_id, r.status_code)
                continue
            try:
                data = r.json()
                self.it_token = data["access_token"]
                self.it_refresh_token = data.get("refresh_token")
                self.it_client_id = client_id
                break
            except Exception as e:
                _LOGGER.debug("IT token parse failed for %s: %s", client_id, e)
                continue

    def _refresh_di_token(self) -> None:
        """Refresh the DI Bearer token using the stored refresh token."""
        if not self.di_refresh_token or not self.di_client_id:
            raise GarminConnectAuthenticationError("No DI refresh token available")
        r = requests.post(
            DI_TOKEN_URL,
            headers=_native_headers(
                {
                    "Authorization": _build_basic_auth(self.di_client_id),
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cache-Control": "no-cache",
                }
            ),
            data={
                "grant_type": "refresh_token",
                "client_id": self.di_client_id,
                "refresh_token": self.di_refresh_token,
            },
            timeout=30,
        )
        if not r.ok:
            raise GarminConnectAuthenticationError(
                f"DI token refresh failed: {r.status_code} {r.text[:200]}"
            )
        data = r.json()
        self.di_token = data["access_token"]
        self.di_refresh_token = data.get("refresh_token", self.di_refresh_token)
        self.di_client_id = (
            self._extract_client_id_from_jwt(self.di_token) or self.di_client_id
        )

    def _extract_client_id_from_jwt(self, token: str) -> str | None:
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return None
            payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
            value = payload.get("client_id")
            return str(value) if value else None
        except Exception:
            return None

    def _it_client_id_candidates(self, di_client_id: str) -> tuple[str, ...]:
        derived = (
            di_client_id.replace("_DI_", "_")
            if "_DI_" in di_client_id
            else (
                di_client_id[:-3] if di_client_id.endswith("_DI") else IT_CLIENT_IDS[0]
            )
        )
        seen: list[str] = []
        for v in [self.it_client_id, derived, *IT_CLIENT_IDS]:
            if v and v not in seen:
                seen.append(v)
        return tuple(seen)

    def _token_expires_soon(self) -> bool:
        token = self.di_token or self.jwt_web
        if not token:
            return False
        try:
            import time as _time

            parts = str(token).split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
                payload = json.loads(
                    base64.urlsafe_b64decode(payload_b64.encode()).decode()
                )
                exp = payload.get("exp")
                if exp and _time.time() > (int(exp) - 900):
                    return True
        except Exception:
            _LOGGER.debug("Failed to check token expiry")
        return False

    def _refresh_session(self) -> None:
        """Refresh auth — DI token refresh or legacy JWT_WEB CAS refresh."""
        if self.di_token:
            try:
                self._refresh_di_token()
                if self._tokenstore_path:
                    with contextlib.suppress(Exception):
                        self.dump(self._tokenstore_path)
            except Exception as err:
                _LOGGER.debug("DI token refresh failed: %s", err)
            return

        # JWT_WEB refresh via CAS TGT
        if not self.is_authenticated:
            return
        try:
            self.cs.get(
                f"{self._sso}/mobile/sso/en_US/sign-in",
                params={
                    "clientId": MOBILE_SSO_CLIENT_ID,
                    "service": MOBILE_SSO_SERVICE_URL,
                },
                allow_redirects=True,
                timeout=15,
            )
            for c in self.cs.cookies.jar:
                if c.name == "JWT_WEB":
                    self.jwt_web = c.value
                    _LOGGER.debug("Session refreshed via CAS TGT")
                    if self._tokenstore_path:
                        with contextlib.suppress(Exception):
                            self.dump(self._tokenstore_path)
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
            for c in self.cs.cookies.jar:
                if c.name == "JWT_WEB":
                    self.jwt_web = c.value
                    break
        except Exception as err:
            _LOGGER.debug("Refresh failed: %s", err)

    def dumps(self) -> str:
        """Serialize session state to JSON string."""
        data: dict[str, Any] = {
            "di_token": self.di_token,
            "di_refresh_token": self.di_refresh_token,
            "di_client_id": self.di_client_id,
            "it_token": self.it_token,
            "it_refresh_token": self.it_refresh_token,
            "it_client_id": self.it_client_id,
            # JWT_WEB fields
            "jwt_web": self.jwt_web,
            "csrf_token": self.csrf_token,
            "cookies": {c.name: c.value for c in self.cs.cookies.jar},
        }
        return json.dumps(data)

    def dump(self, path: str) -> None:
        """Write tokens safely to disk."""
        p = Path(path).expanduser()
        if p.is_dir() or not p.name.endswith(".json"):
            p = p / "garmin_tokens.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.dumps())

    def load(self, path: str) -> None:
        try:
            self._tokenstore_path = path
            p = Path(path).expanduser()
            if p.is_dir() or not p.name.endswith(".json"):
                p = p / "garmin_tokens.json"
            self.loads(p.read_text())
        except Exception as e:
            raise GarminConnectConnectionError(
                f"Token path not loading cleanly: {e}"
            ) from e

    def loads(self, tokenstore: str) -> None:
        try:
            data = json.loads(tokenstore)
            self.di_token = data.get("di_token")
            self.di_refresh_token = data.get("di_refresh_token")
            self.di_client_id = data.get("di_client_id")
            self.it_token = data.get("it_token")
            self.it_refresh_token = data.get("it_refresh_token")
            self.it_client_id = data.get("it_client_id")
            self.jwt_web = data.get("jwt_web")
            self.csrf_token = data.get("csrf_token")

            # Restore cookies if no DI token
            if not self.di_token:
                sso_cookies = {"CASTGC", "CASRMC", "CASMFA", "SESSION", "__VCAP_ID__"}
                connect_cookies = {"JWT_WEB", "session", "__cflb"}
                for k, v in data.get("cookies", {}).items():
                    if k in sso_cookies:
                        self.cs.cookies.set(k, v, domain=f"sso.{self.domain}")
                    elif k in connect_cookies:
                        self.cs.cookies.set(k, v, domain=f".connect.{self.domain}")
                    else:
                        self.cs.cookies.set(k, v, domain=f".{self.domain}")

            if not self.is_authenticated:
                raise GarminConnectAuthenticationError("Missing tokens from dict load")
        except Exception as e:
            raise GarminConnectConnectionError(
                f"Token extraction loads() structurally failed: {e}"
            ) from e

    def connectapi(self, path: str, **kwargs: Any) -> Any:
        return self._run_request("GET", path, **kwargs).json()

    def request(self, method: str, _domain: str, path: str, **kwargs: Any) -> Any:
        kwargs.pop("api", None)
        return self._run_request(method, path, **kwargs)

    def post(self, _domain: str, path: str, **kwargs: Any) -> Any:
        api = kwargs.pop("api", False)
        resp = self._run_request("POST", path, **kwargs)
        if api:
            return resp.json() if hasattr(resp, "json") else None
        return resp

    def put(self, _domain: str, path: str, **kwargs: Any) -> Any:
        api = kwargs.pop("api", False)
        resp = self._run_request("PUT", path, **kwargs)
        if api:
            return resp.json() if hasattr(resp, "json") else None
        return resp

    def delete(self, _domain: str, path: str, **kwargs: Any) -> Any:
        api = kwargs.pop("api", False)
        resp = self._run_request("DELETE", path, **kwargs)
        if api:
            return resp.json() if hasattr(resp, "json") else None
        return resp

    def resume_login(self, _client_state: Any, mfa_code: str) -> tuple[str | None, Any]:
        if hasattr(self, "_mfa_cffi_session"):
            self._complete_mfa_portal(mfa_code)
        else:
            self._complete_mfa(mfa_code)
        return None, None

    def download(self, path: str, **kwargs: Any) -> bytes:
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update({"Accept": "*/*"})
        return self._run_request("GET", path, **kwargs).content

    def _fresh_api_session(self) -> requests.Session:
        """Create a fresh plain requests.Session for each API call."""
        sess = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
        sess.mount("https://", adapter)
        return sess

    def _run_request(self, method: str, path: str, **kwargs: Any) -> Any:
        if self.is_authenticated and self._token_expires_soon():
            self._refresh_session()

        url = f"{self._connectapi}/{path.lstrip('/')}"

        if "timeout" not in kwargs:
            kwargs["timeout"] = 15

        headers = self.get_api_headers()
        custom_headers = kwargs.pop("headers", {})
        headers.update(custom_headers)

        sess = self._fresh_api_session()
        resp = sess.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            self._refresh_session()
            resp = sess.request(method, url, headers=self.get_api_headers(), **kwargs)

        if resp.status_code == 204:

            class EmptyJSONResp:
                status_code = 204
                content = b""

                def json(self) -> Any:
                    return {}

                def __repr__(self) -> str:
                    return "{}"

                def __str__(self) -> str:
                    return "{}"

            return EmptyJSONResp()

        if resp.status_code >= 400:
            error_msg = f"API Error {resp.status_code}"
            try:
                error_data = resp.json()
                if isinstance(error_data, dict):
                    msg = (
                        error_data.get("message")
                        or error_data.get("content")
                        or error_data.get("detailedImportResult", {})
                        .get("failures", [{}])[0]
                        .get("messages", [""])[0]
                    )
                    if msg:
                        error_msg += f" - {msg}"
                    else:
                        error_msg += f" - {error_data}"
            except Exception:
                if len(resp.text) < 500:
                    error_msg += f" - {resp.text}"
            raise GarminConnectConnectionError(error_msg)

        return resp
