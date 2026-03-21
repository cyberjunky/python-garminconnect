"""State-of-the-art authentication engine bypassing Cloudflare and mimicking garth's legacy API."""

import json
import logging
from pathlib import Path
from typing import Any

import requests

_LOGGER = logging.getLogger(__name__)

CLIENT_ID = "GarminConnect"
SSO_SERVICE_URL = "https://connect.garmin.com/app/"


class GarthHTTPError(Exception):
    """Exception to proxy legacy garth errors natively."""

    def __init__(self, error: Exception, msg: str = ""):
        self.error = error
        super().__init__(msg or str(error))


class Client:
    """A drop-in replacement for garth.Client natively powered by JWT_WEB and curl_cffi."""

    def __init__(self, domain: str = "garmin.com", **_kwargs: Any) -> None:
        self.domain = domain
        self._sso = f"https://sso.{domain}"
        self._connect = f"https://connect.{domain}"

        self.jwt_web: str | None = None
        self.csrf_token: str | None = None

        # Garth backward compatibility properties
        self.profile: dict | None = None

        # Impersonate Android Chrome for mobile API, Desktop Chrome for Web API
        self.cs: requests.Session = requests.Session()

    @property
    def is_authenticated(self) -> bool:
        return bool(self.jwt_web and self.csrf_token)

    def get_api_headers(self) -> dict[str, str]:
        if not self.is_authenticated:
            raise GarthHTTPError(Exception("Not authenticated"))
        return {
            "Accept": "application/json",
            "connect-csrf-token": self.csrf_token,
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
    ) -> tuple[None, None]:
        """Logs into Mobile API to perfectly bypass CF, then trades for Web JWT."""
        import random
        ios_version = f"17_{random.randint(0, 9)}"
        sess: requests.Session = requests.Session()
        sess.headers = {
            "User-Agent": (
                f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version} like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Site": "none",
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
            raise GarthHTTPError(
                err, f"Login failed (Not JSON): HTTP {r.status_code}"
            ) from err

        resp_type = res.get("responseStatus", {}).get("type")

        if resp_type == "MFA_REQUIRED":
            self._mfa_method = res.get("customerMfaInfo", {}).get(
                "mfaLastMethodUsed", "email"
            )
            self._mfa_session = sess

            if return_on_mfa:
                raise GarthHTTPError(Exception("mfa_required"))

            if prompt_mfa:
                mfa_code = prompt_mfa()
                self._complete_mfa(mfa_code)
                return None, None
            raise GarthHTTPError(
                Exception("MFA Required but no prompt_mfa mechanism supplied")
            )

        if resp_type == "SUCCESSFUL":
            ticket = res["serviceTicketId"]
            self._establish_session(ticket)
            return None, None

        if (
            "status-code" in res.get("error", {})
            and res["error"]["status-code"] == "429"
        ):
            # Pass up as a fake 429 response so the caller triggers TooManyRequests error
            class FakeRespRate(Exception):
                status_code = 429

            raise GarthHTTPError(FakeRespRate(), "429 Rate Limit")

        if resp_type == "INVALID_USERNAME_PASSWORD":
            class FakeRespAuth(Exception):
                status_code = 401
            raise GarthHTTPError(FakeRespAuth(), "401 Unauthorized (Invalid Username or Password)")

        raise GarthHTTPError(Exception("Unhandled Garmin Login JSON"), f"Login failed: {res}")

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
        raise GarthHTTPError(Exception(f"MFA Verification failed: {res}"))

    def _establish_session(self, ticket: str) -> None:
        self.cs: requests.Session = requests.Session()
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

            class FakeRespToken(Exception):
                status_code = r_tok.status_code

            raise GarthHTTPError(FakeRespToken(), "Failed JWT extraction")

        jwt_data = r_tok.json()
        self.jwt_web = jwt_data.get("encryptedToken")
        self.csrf_token = jwt_data.get("csrfToken")

        if not self.jwt_web or not self.csrf_token:
            raise GarthHTTPError(
                Exception("Missing required JWT or CSRF tokens in response payload.")
            )

        self.cs.cookies.set("JWT_WEB", self.jwt_web, domain=f".{self.domain}", path="/")

        # Emulate older OAuth storage
        self.oauth1_token = self.jwt_web
        self.oauth2_token = self.csrf_token

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
        except Exception as err:
            _LOGGER.debug(f"Refresh silently failed: {err}")

    def dumps(self) -> str:
        """Drop-in implementation for saving native payload cleanly."""
        data: dict[str, Any] = {
            "jwt_web": self.jwt_web,
            "csrf_token": self.csrf_token,
            "cookies": getattr(self.cs.cookies, "get_dict", dict)(),
        }
        if not data["cookies"]:
            data["cookies"] = {c.name: c.value for c in self.cs.cookies.jar}
        return json.dumps(data)

    def dump(self, path: str) -> None:
        """Write tokens safely natively to disk format."""
        p = Path(path).expanduser()
        if p.is_dir():
            p = p / ".garmin_tokens.json"

        # Ensure parent directories exist
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.dumps())

    def load(self, path: str) -> None:
        try:
            p = Path(path).expanduser()
            if p.is_dir():
                p = p / ".garmin_tokens.json"
            self.loads(p.read_text())
        except Exception as e:
            raise GarthHTTPError(e, "Token path not loading cleanly") from e

    def loads(self, tokenstore: str) -> None:
        try:
            data = json.loads(tokenstore)
            self.jwt_web = data.get("jwt_web")
            self.csrf_token = data.get("csrf_token")
            raw_cookies = data.get("cookies", {})
            for k, v in raw_cookies.items():
                self.cs.cookies.set(k, v, domain=f".{self.domain}", path="/")

            # Allow fallback backwards compatibility where Home Assistant uses OAuth structures
            self.oauth1_token = self.jwt_web
            self.oauth2_token = self.csrf_token

            if not self.is_authenticated:
                raise GarthHTTPError(Exception("Missing tokens from dict load"))
        except Exception as e:
            raise GarthHTTPError(
                e, "Token extraction loads() structurally failed"
            ) from e

    def connectapi(self, path: str, **kwargs: Any) -> Any:
        return self._run_request("GET", path, **kwargs).json()

    def request(self, method: str, _domain: str, path: str, **kwargs: Any) -> Any:
        # Legacy garth used this to distinguish API vs WEB
        return self._run_request(method, path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self._run_request("POST", path, **kwargs).json()

    def put(self, path: str, **kwargs: Any) -> Any:
        return self._run_request("PUT", path, **kwargs).json()

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self._run_request("DELETE", path, **kwargs).json()

    def resume_login(self, client_state: Any, mfa_code: str) -> tuple[None, None]:
        self._complete_mfa(mfa_code)
        return None, None

    def download(self, path: str, **kwargs: Any) -> bytes:
        return self._run_request("GET", path, **kwargs).content

    def _run_request(self, method: str, path: str, **kwargs: Any) -> Any:
        # Trap legacy deprecated endpoints that were removed from the React /gc-api/ interface entirely natively
        # Redirect legacy deprecated profile endpoint to the active modern equivalent directly natively!
        if "userprofile/profile" in path:
            path = path.replace("userprofile/profile", "socialProfile")

        if "userprofile/user-settings" in path:

            class MockSettings:
                status_code = 200

                def json(self) -> Any:
                    return {"userData": {"measurementSystem": "metric"}}

            return MockSettings()

        # Redirect all modern/proxy traffic directly into gc-api natively!
        if path.startswith("/modern/proxy"):
            path = path.replace("/modern/proxy", "/gc-api", 1)
        elif not path.startswith("/gc-api"):
            path = f"/gc-api{path if path.startswith('/') else '/' + path}"

        url = f"{self._connect}{path}"

        if "timeout" not in kwargs:
            kwargs["timeout"] = 15

        resp = self.cs.request(method, url, headers=self.get_api_headers(), **kwargs)

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
                    return None

            return EmptyJSONResp()

        if resp.status_code >= 400:
            resp.request = (
                None  # strip mock missing properties for GarthHTTPError compat
            )
            raise GarthHTTPError(resp, f"API Error {resp.status_code}")

        return resp
