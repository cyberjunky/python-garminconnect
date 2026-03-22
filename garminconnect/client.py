"""State-of-the-art authentication engine for Garmin Connect."""

import json
import logging
from pathlib import Path
from typing import Any

import requests

_LOGGER = logging.getLogger(__name__)

CLIENT_ID = "GarminConnect"
SSO_SERVICE_URL = "https://connect.garmin.com/app/"


from .exceptions import (  # noqa: E402
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


class Client:
    """A client to communicate with Garmin Connect."""

    def __init__(self, domain: str = "garmin.com", **kwargs: Any) -> None:
        self.domain = domain
        self._sso = f"https://sso.{domain}"
        self._connect = f"https://connect.{domain}"

        self.jwt_web: str | None = None
        self.csrf_token: str | None = None

        # Garth backward compatibility properties
        self.profile: dict | None = None

        self.cs: requests.Session = requests.Session()
        pool_connections = kwargs.get("pool_connections", 20)
        pool_maxsize = kwargs.get("pool_maxsize", 20)

        adapter = requests.adapters.HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
        )
        self.cs.mount("https://", adapter)
        self.cs.mount("http://", adapter)

        self._tokenstore_path: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.jwt_web and self.csrf_token)

    def get_api_headers(self) -> dict[str, str]:
        if not self.is_authenticated:
            raise GarminConnectAuthenticationError("Not authenticated")
        return {
            "Accept": "application/json",
            "connect-csrf-token": str(self.csrf_token),
            "Origin": self._connect,
            "Referer": f"{self._connect}/modern/",
            "DI-Backend": f"connectapi.{self.domain}",
        }

    def login(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Logs into Mobile API to perfectly bypass CF, then trades for Web JWT."""
        sess: requests.Session = requests.Session()
        sess.headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TQ3A.230901.001) GarminConnect/4.74.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        sess.get(
            f"{self._sso}/mobile/sso/en/sign-in",
            params={"clientId": CLIENT_ID},
        )

        r = sess.post(
            f"{self._sso}/mobile/api/login",
            params={
                "clientId": CLIENT_ID,
                "locale": "en-US",
                "service": SSO_SERVICE_URL,
            },
            json={
                "username": email,
                "password": password,
                "rememberMe": False,
                "captchaToken": "",
            },
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
                "clientId": CLIENT_ID,
                "locale": "en-US",
                "service": SSO_SERVICE_URL,
            },
            json={
                "mfaMethod": getattr(self, "_mfa_method", "email"),
                "mfaVerificationCode": mfa_code,
                "rememberMyBrowser": False,
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

    def _establish_session(self, ticket: str) -> None:
        if not hasattr(self, "cs") or self.cs is None:
            self.cs = requests.Session()
        self.cs.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        self.cs.get(SSO_SERVICE_URL, params={"ticket": ticket}, allow_redirects=True)
        r_tok = self.cs.post(
            f"{self._connect}/services/auth/token/di-oauth/refresh",
            headers={
                "Accept": "application/json",
                "NK": "NT",
                "Referer": f"{self._connect}/modern/",
            },
        )

        if r_tok.status_code not in (200, 201):
            raise GarminConnectConnectionError("Failed JWT extraction")

        jwt_data = r_tok.json()
        self.jwt_web = jwt_data.get("encryptedToken")
        self.csrf_token = jwt_data.get("csrfToken")

        if not self.jwt_web or not self.csrf_token:
            raise GarminConnectAuthenticationError(
                "Missing required JWT or CSRF tokens in response payload."
            )

        self.cs.cookies.set("JWT_WEB", self.jwt_web, domain=f".{self.domain}", path="/")

    def _refresh_session(self) -> None:
        """Silently grab fresh JWT behind the scenes."""
        if not self.is_authenticated:
            return
        try:
            r_tok = self.cs.post(
                f"{self._connect}/services/auth/token/di-oauth/refresh",
                headers={
                    "Accept": "application/json",
                    "NK": "NT",
                    "connect-csrf-token": self.csrf_token,
                    "Referer": f"{self._connect}/modern/",
                },
                timeout=10,
            )
            if r_tok.status_code in (200, 201):
                jwt_data = r_tok.json()
                self.jwt_web = jwt_data.get("encryptedToken")
                self.csrf_token = jwt_data.get("csrfToken")
                self.cs.cookies.set(
                    "JWT_WEB", self.jwt_web, domain=f".{self.domain}", path="/"
                )
                if self._tokenstore_path:
                    try:
                        self.dump(self._tokenstore_path)
                        _LOGGER.debug(
                            f"Seamlessly auto-saved refreshed API tokens proactively to {self._tokenstore_path}"
                        )
                    except Exception as dump_err:
                        _LOGGER.exception(
                            f"Proactive refresh auto-saving tokens failed gracefully natively: {dump_err}"
                        )
        except Exception as err:
            _LOGGER.debug(f"Refresh silently failed: {err}")

    def dumps(self) -> str:
        """Drop-in implementation for saving native payload cleanly."""
        data: dict[str, Any] = {
            "jwt_web": self.jwt_web,
            "csrf_token": self.csrf_token,
            "cookies": self.cs.cookies.get_dict(),
        }
        return json.dumps(data)

    def dump(self, path: str) -> None:
        """Write tokens safely natively to disk format."""
        p = Path(path).expanduser()
        if p.is_dir() or not p.name.endswith(".json"):
            p = p / "garmin_tokens.json"

        # Ensure parent directories exist
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
            self.jwt_web = data.get("jwt_web")
            self.csrf_token = data.get("csrf_token")
            raw_cookies = data.get("cookies", {})
            for k, v in raw_cookies.items():
                self.cs.cookies.set(k, v, domain=f".{self.domain}", path="/")

            if not self.is_authenticated:
                raise GarminConnectAuthenticationError("Missing tokens from dict load")
        except Exception as e:
            raise GarminConnectConnectionError(
                f"Token extraction loads() structurally failed: {e}"
            ) from e

    def connectapi(self, path: str, **kwargs: Any) -> Any:
        return self._run_request("GET", path, **kwargs).json()

    def request(self, method: str, _domain: str, path: str, **kwargs: Any) -> Any:
        # Legacy garth used this to distinguish API vs WEB
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

    def resume_login(self, client_state: Any, mfa_code: str) -> tuple[str | None, Any]:
        _ = client_state
        self._complete_mfa(mfa_code)
        return None, None

    def download(self, path: str, **kwargs: Any) -> bytes:
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        # Ensure we politely accept any binary format Garmin transmits
        kwargs["headers"].update({"Accept": "*/*"})
        return self._run_request("GET", path, **kwargs).content

    def _run_request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not path.startswith("/gc-api"):
            path = f"/gc-api{path if path.startswith('/') else '/' + path}"

        url = f"{self._connect}{path}"

        if "timeout" not in kwargs:
            kwargs["timeout"] = 15

        headers = self.get_api_headers()
        custom_headers = kwargs.pop("headers", {})
        headers.update(custom_headers)

        resp = self.cs.request(method, url, headers=headers, **kwargs)

        # Implement 401 refresh intercept universally
        if resp.status_code == 401:
            self._refresh_session()
            resp = self.cs.request(
                method, url, headers=self.get_api_headers(), **kwargs
            )

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
                # If it's short, just attach the text
                if len(resp.text) < 500:
                    error_msg += f" - {resp.text}"
            raise GarminConnectConnectionError(error_msg)

        return resp
