"""Login strategies and MFA completion against Garmin SSO.

Strategy chain (each strategy is tried in order; only auth errors stop the chain):
1. Mobile iOS + curl_cffi  (TLS fingerprint rotation, no delay needed)
2. Mobile iOS + requests   (plain HTTP fallback)
3. SSO embed widget + cffi (HTML form flow, bypasses clientId rate limits)
4. Portal web + curl_cffi  (TLS fingerprint rotation, 10-20s anti-WAF delay)
5. Portal web + requests   (plain HTTP last resort)

The mobile and portal flows post the same JSON credential payload and get the
same ``responseStatus`` answers back, so they share one request/response
handler (``_post_credentials``) and one TLS-fingerprint rotation loop
(``_login_with_impersonations``); only the URLs, headers and pre-steps differ.
"""

import logging
import random
import time
from collections.abc import Callable
from typing import Any, cast

import requests

from ..exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from ._base import _ClientState
from .constants import (
    _CSRF_RE,
    _TICKET_RE,
    _TITLE_RE,
    _WIDGET_MFA_VARS_RE,
    DESKTOP_USER_AGENT,
    IOS_LOGIN_UA,
    IOS_SSO_CLIENT_ID,
    LOGIN_DELAY_MAX_S,
    LOGIN_DELAY_MIN_S,
    MOBILE_IMPERSONATIONS,
    PORTAL_IMPERSONATIONS,
    PORTAL_SSO_CLIENT_ID,
    WIDGET_DELAY_MAX_S,
    WIDGET_DELAY_MIN_S,
)
from .transport import _sanitize_exception_text

_LOGGER = logging.getLogger(__name__)


class _MFARequired(Exception):
    """Internal sentinel — raised by login strategies when MFA is needed.

    Stops the strategy chain immediately. The caller (login()) handles it via
    prompt_mfa / return_on_mfa.
    """


def _pkg() -> Any:
    """Return the ``garminconnect.client`` package.

    The optional dependencies (``HAS_CFFI``, ``cffi_requests``, ``HAS_UA_GEN``)
    are imported once on the package so callers and tests can toggle them in a
    single place; reading them through the package at call time honours that.
    """
    from garminconnect import client as pkg

    return pkg


def _parse_widget_mfa_vars(html: str) -> dict[str, str]:
    """Extract the inline JS variables Garmin uses for widget MFA."""
    return {m.group(1): m.group(2) for m in _WIDGET_MFA_VARS_RE.finditer(html)}


def _random_browser_headers() -> dict[str, str]:
    """Generate a random browser User-Agent + sec-ch-ua headers.

    Falls back to a static desktop Chrome UA if ua_generator is not installed.
    """
    pkg = _pkg()
    if pkg.HAS_UA_GEN:
        ua = pkg._generate_ua()
        return dict(ua.headers.get())
    return {"User-Agent": DESKTOP_USER_AGENT}


def _page_title(html: str) -> str:
    """Return the ``<title>`` of an SSO page, or an empty string."""
    match = _TITLE_RE.search(html)
    return match.group(1) if match else ""


def _raise_if_rate_limited(resp: Any, what: str) -> None:
    if resp.status_code == 429:
        raise GarminConnectTooManyRequestsError(f"{what} returned 429")


class LoginMixin(_ClientState):
    """Credential login strategies and MFA completion."""

    def login(
        self,
        email: str,
        password: str,
        prompt_mfa: Any = None,
        return_on_mfa: bool = False,
    ) -> tuple[str | None, Any]:
        """Log in using a cascading 5-strategy chain (ha-garmin order).

        Tries each strategy in order.  Only credential errors (GarminConnectAuthenticationError)
        and MFA requirements stop the chain immediately — all other failures
        (429 rate limits, transport errors, HTML challenges) fall through to
        the next strategy. MFA requirements are resolved immediately via
        prompt_mfa / return_on_mfa.

        Args:
            email: Garmin account email.
            password: Garmin account password.
            prompt_mfa: Callable that returns an MFA code string when invoked.
            return_on_mfa: When True, return ("needs_mfa", None) instead of
                           calling prompt_mfa; caller must call resume_login().

        Returns:
            (None, None) on success; ("needs_mfa", None) when return_on_mfa=True.

        """
        if self._mfa_pending:
            raise GarminConnectAuthenticationError(
                "MFA login already in progress; complete it with resume_login() "
                "or call logout() first"
            )

        # Start every credential login from a clean slate. A stale di_token
        # from a previous login/token-load must not survive this call: it
        # would keep is_authenticated True after all strategies fail, and
        # get_api_headers() prefers di_token, so it would silently shadow a
        # fresh jwt_web obtained by a web strategy (and _verify_token would
        # then "verify" the old identity instead of the new login).
        self._clear_auth_state(keep_tokenstore_path=True)

        strategies: list[tuple[str, Any]] = [
            ("mobile+cffi", lambda: self._mobile_login_cffi(email, password)),
            ("mobile+requests", lambda: self._mobile_login_requests(email, password)),
            ("widget+cffi", lambda: self._widget_web_login(email, password)),
            ("portal+cffi", lambda: self._portal_web_login_cffi(email, password)),
            (
                "portal+requests",
                lambda: self._portal_web_login_requests(email, password),
            ),
        ]
        has_cffi = _pkg().HAS_CFFI
        if not has_cffi:
            _LOGGER.warning(
                "curl_cffi is not installed: the browser-impersonating login "
                "strategies (mobile+cffi, widget+cffi, portal+cffi) are "
                "unavailable and the plain-requests fallbacks are usually "
                "blocked by Cloudflare. Install it with: pip install curl_cffi"
            )
        if self.skip_strategies:
            strategies = [
                (n, fn) for n, fn in strategies if n not in self.skip_strategies
            ]
            _LOGGER.debug("Skipping login strategies: %s", self.skip_strategies)

        last_err: Exception | None = None
        rate_limited_count = 0

        def resolve_mfa(name: str) -> tuple[str | None, Any]:
            if return_on_mfa:
                self._mfa_pending = True
                return "needs_mfa", None
            if prompt_mfa:
                mfa_code = prompt_mfa()
                self._complete_mfa(mfa_code)
                if self.verify_login and not self._verify_token():
                    self._clear_auth_state(keep_tokenstore_path=True)
                    raise GarminConnectConnectionError(
                        self._token_rejected_message(
                            f"{name}: token rejected by API tier after MFA"
                        )
                    )
                self._mfa_pending = False
                return None, None
            raise GarminConnectAuthenticationError(
                "MFA Required but no prompt_mfa mechanism supplied"
            )

        for name, run in strategies:
            try:
                _LOGGER.debug("Trying login strategy: %s", name)
                run()
                # Strategy got a token — make sure the API tier accepts it
                # before declaring success (else fall through to the next).
                if self.verify_login and not self._verify_token():
                    _LOGGER.warning(
                        "%s obtained a token the API rejected; trying next strategy",
                        name,
                    )
                    self._clear_auth_state(keep_tokenstore_path=True)
                    last_err = GarminConnectConnectionError(
                        self._token_rejected_message(
                            f"{name}: token rejected by API tier"
                        )
                    )
                    continue
                return None, None
            except GarminConnectAuthenticationError:
                # Wrong credentials — stop immediately, no point trying further
                raise
            except _MFARequired:
                # Resolve MFA immediately; the strategy is responsible for
                # triggering code delivery (widget flow does so explicitly).
                try:
                    return resolve_mfa(name)
                except GarminConnectConnectionError as e:
                    last_err = e
                    continue
            except GarminConnectTooManyRequestsError as e:
                _LOGGER.warning(
                    "%s returned 429: %s", name, _sanitize_exception_text(e)
                )
                rate_limited_count += 1
                last_err = e
                continue
            except Exception as e:
                _LOGGER.warning("%s failed: %s", name, _sanitize_exception_text(e))
                last_err = e
                continue

        if rate_limited_count == len(strategies):
            raise GarminConnectTooManyRequestsError(
                "All login strategies rate limited (429). "
                "Garmin may be blocking this client or network rather than "
                "rate limiting; try again later or from another network."
            )
        raise GarminConnectConnectionError(
            "All login strategies exhausted: "
            + (_sanitize_exception_text(last_err) if last_err else "no strategies ran")
            + (
                "; curl_cffi is not installed (pip install curl_cffi), which "
                "is the likely cause"
                if not has_cffi
                else ""
            )
        )

    def resume_login(self, _client_state: Any, mfa_code: str) -> tuple[str | None, Any]:
        """Complete a previously initiated MFA login.

        A failed verification code (or a rate-limited attempt) leaves the
        pending MFA session intact so the caller can retry with a corrected
        code on the same instance. Only success, or a non-retryable failure
        after MFA itself succeeded, clears the pending state.
        """
        self._complete_mfa(mfa_code)
        if self.verify_login and not self._verify_token():
            self._clear_auth_state()
            raise GarminConnectConnectionError(
                self._token_rejected_message("token rejected by API tier after MFA")
            )
        self._clear_mfa_pending_state()
        return None, None

    # ------------------------------------------------------------------ #
    #  Shared pieces of the mobile and portal JSON login flows            #
    # ------------------------------------------------------------------ #

    def _login_with_impersonations(
        self,
        label: str,
        impersonations: tuple[str, ...],
        do_login: Callable[[Any, str, str], None],
        email: str,
        password: str,
    ) -> None:
        """Run ``do_login`` with a curl_cffi session per TLS fingerprint.

        Different TLS fingerprints land in different Cloudflare rate-limit
        buckets, so rotating through them gives multiple shots. Credential
        errors and MFA stop the rotation immediately; anything else moves on
        to the next fingerprint and the last error is re-raised at the end.
        """
        pkg = _pkg()
        if not pkg.HAS_CFFI:
            raise GarminConnectConnectionError("curl_cffi not available")
        last_err: Exception | None = None
        for imp in impersonations:
            try:
                _LOGGER.debug("%s trying impersonation=%s", label, imp)
                sess: Any = pkg.cffi_requests.Session(impersonate=cast("Any", imp))
                do_login(sess, email, password)
                return
            except (GarminConnectAuthenticationError, _MFARequired):
                raise
            except GarminConnectTooManyRequestsError as e:
                _LOGGER.debug("%s(%s) 429: %s", label, imp, _sanitize_exception_text(e))
                last_err = e
                continue
            except Exception as e:
                _LOGGER.debug(
                    "%s(%s) failed: %s", label, imp, _sanitize_exception_text(e)
                )
                last_err = e
                continue
        if last_err:
            raise last_err
        raise GarminConnectConnectionError(f"{label}: no impersonations available")

    def _post_credentials(
        self,
        sess: Any,
        label: str,
        url: str,
        params: dict[str, str],
        headers: dict[str, str],
        *,
        service_url: str,
        flow: str,
        email: str,
        password: str,
    ) -> None:
        """POST the credentials and act on Garmin's ``responseStatus``.

        Shared by the mobile (``/mobile/api/login``) and portal
        (``/portal/api/login``) flows, which answer with the same JSON shape.
        On ``MFA_REQUIRED`` the session and request details are kept on
        ``self`` so ``_complete_mfa`` can continue the same SSO session.
        """
        r = sess.post(
            url,
            params=params,
            headers=headers,
            json={
                "username": email,
                "password": password,
                "rememberMe": True,
                "captchaToken": "",
            },
            timeout=30,
        )

        if r.status_code == 429:
            raise GarminConnectTooManyRequestsError(
                f"{label} returned 429 — rate limited or blocked by Garmin "
                "(can be triggered by the client fingerprint, not only the IP)"
            )

        if r.status_code == 403:
            raise GarminConnectConnectionError(
                f"{label}: HTTP 403 (Cloudflare bot challenge) — "
                "falling through to next strategy"
            )

        try:
            res = r.json()
        except Exception as err:
            raise GarminConnectConnectionError(
                f"{label} failed (non-JSON): HTTP {r.status_code}"
            ) from err

        resp_type = res.get("responseStatus", {}).get("type")

        if resp_type == "MFA_REQUIRED":
            self._mfa_method = res.get("customerMfaInfo", {}).get(
                "mfaLastMethodUsed", "email"
            )
            self._mfa_session = sess
            self._mfa_login_params = params
            self._mfa_post_headers = headers
            self._mfa_service_url = service_url
            self._mfa_flow = flow
            raise _MFARequired()

        if resp_type == "SUCCESSFUL":
            self._establish_session(
                res["serviceTicketId"], sess=sess, service_url=service_url
            )
            return

        if resp_type == "INVALID_USERNAME_PASSWORD":
            raise GarminConnectAuthenticationError(
                "401 Unauthorized (Invalid Username or Password)"
            )

        # Check for 429 buried inside JSON error body
        if res.get("error", {}).get("status-code") == "429":
            raise GarminConnectTooManyRequestsError(f"{label}: 429 in JSON body")

        if resp_type == "CAPTCHA_REQUIRED":
            raise GarminConnectConnectionError(
                f"{label}: CAPTCHA required (bot challenge) — "
                "falling through to next strategy"
            )

        # Status only: the body can carry account data (customerMfaInfo, ids).
        _LOGGER.debug(
            "%s unexpected response: HTTP %s, responseStatus=%s",
            label,
            r.status_code,
            resp_type or "unknown",
        )
        raise GarminConnectConnectionError(
            f"{label} failed: HTTP {r.status_code}, "
            f"responseStatus={resp_type or 'unknown'}"
        )

    # ------------------------------------------------------------------ #
    #  STRATEGIES 1 & 2 — Mobile iOS (curl_cffi rotation / plain requests) #
    # ------------------------------------------------------------------ #

    def _mobile_login_cffi(self, email: str, password: str) -> None:
        """Mobile login with curl_cffi TLS fingerprint rotation."""
        self._login_with_impersonations(
            "mobile+cffi", MOBILE_IMPERSONATIONS, self._do_mobile_login, email, password
        )

    def _mobile_login_requests(self, email: str, password: str) -> None:
        """Mobile login with plain requests (no TLS fingerprinting)."""
        self._do_mobile_login(requests.Session(), email, password)

    def _do_mobile_login(self, sess: Any, email: str, password: str) -> None:
        """Login via sso.garmin.com/mobile/api/login (iOS app flow)."""
        self._post_credentials(
            sess,
            "Mobile login",
            f"{self._sso}/mobile/api/login",
            {
                "clientId": IOS_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": self._ios_service_url,
            },
            {
                "User-Agent": IOS_LOGIN_UA,
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": self._sso,
            },
            service_url=self._ios_service_url,
            flow="ios",
            email=email,
            password=password,
        )

    # ------------------------------------------------------------------ #
    #  STRATEGY 3 — SSO Embed Widget + curl_cffi                         #
    # ------------------------------------------------------------------ #

    def _widget_web_login(self, email: str, password: str) -> None:
        """Login via the SSO embed HTML widget.

        Uses HTML form flow which bypasses clientId-based rate limits.
        Uses curl_cffi for TLS fingerprinting.
        """
        pkg = _pkg()
        if not pkg.HAS_CFFI:
            raise GarminConnectConnectionError("curl_cffi not available")
        sess: Any = pkg.cffi_requests.Session(impersonate="chrome", timeout=30)
        sso_base = f"{self._sso}/sso"
        sso_embed = f"{sso_base}/embed"
        embed_params = {
            "id": "gauth-widget",
            "embedWidget": "true",
            "gauthHost": sso_base,
        }
        signin_params = {
            **embed_params,
            "gauthHost": sso_embed,
            "service": sso_embed,
            "source": sso_embed,
            "redirectAfterAccountLoginUrl": sso_embed,
            "redirectAfterAccountCreationUrl": sso_embed,
        }

        # Step 1: GET embed page to establish session cookies
        r = sess.get(sso_embed, params=embed_params)
        _raise_if_rate_limited(r, "Widget embed GET")
        if not r.ok:
            raise GarminConnectConnectionError(f"Widget embed returned {r.status_code}")

        # Step 2: GET signin page for CSRF token
        r = sess.get(
            f"{sso_base}/signin",
            params=signin_params,
            headers={"Referer": sso_embed},
        )
        _raise_if_rate_limited(r, "Widget signin GET")

        csrf_match = _CSRF_RE.search(r.text)
        if not csrf_match:
            raise GarminConnectConnectionError("Widget login: missing CSRF token")

        # Anti-WAF delay between GET and POST
        delay_s = random.uniform(WIDGET_DELAY_MIN_S, WIDGET_DELAY_MAX_S)  # noqa: S311
        _LOGGER.debug("Widget login: waiting %.0fs anti-WAF delay...", delay_s)
        time.sleep(delay_s)

        # Step 3: POST credentials
        r = sess.post(
            f"{sso_base}/signin",
            params=signin_params,
            headers={"Referer": r.url},
            data={
                "username": email,
                "password": password,
                "embed": "true",
                "_csrf": csrf_match.group(1),
            },
            timeout=30,
        )
        _raise_if_rate_limited(r, "Widget signin POST")

        title = _page_title(r.text)
        title_lower = title.lower()

        # Detect server/infrastructure errors — fall through to next strategy
        if any(
            hint in title_lower
            for hint in (
                "bad gateway",
                "service unavailable",
                "cloudflare",
                "502",
                "503",
            )
        ):
            raise GarminConnectConnectionError(f"Widget login: server error '{title}'")

        # Early credential detection — don't waste remaining strategies
        if any(
            hint in title_lower
            for hint in ("locked", "invalid", "incorrect", "account error")
        ):
            raise GarminConnectAuthenticationError(
                f"Widget authentication failed: '{title}'"
            )

        # Child/family accounts are restricted from web SSO — log clearly and
        # fall through so the remaining strategies still get a chance.
        if "unable to sign in" in title_lower or "unable to login" in title_lower:
            _LOGGER.warning(
                "Widget login: '%s' — account may be a Garmin child/family account "
                "restricted from web SSO; child accounts are not supported.",
                title,
            )
            raise GarminConnectConnectionError(
                f"Widget login: account restricted '{title}'"
            )

        # MFA challenge. The signin page itself is also titled "GARMIN
        # Authentication Application", so rely on the inline JS variables
        # Garmin emits for the MFA page (mfaMethod, customerGuid, etc.) rather
        # than the title alone. Email/SMS MFA pages may not actually send the
        # code during the credential POST, so we explicitly request delivery via
        # the same endpoint the browser's "Request a new code" link uses.
        mfa_vars = _parse_widget_mfa_vars(r.text)
        mfa_method = mfa_vars.get("mfaMethod", "").lower()
        looks_like_mfa = "mfa" in title_lower or (
            "authentication application" in title_lower and mfa_method
        )
        if looks_like_mfa:
            self._widget_request_mfa_code(sess, r.text, r.url)
            self._mfa_session = sess
            self._mfa_login_params = signin_params
            self._mfa_post_headers = {"Referer": r.url}
            self._mfa_flow = "widget"
            self._mfa_method = mfa_vars.get("mfaMethod", "")
            self._widget_last_resp = r
            raise _MFARequired()

        if title != "Success":
            raise GarminConnectConnectionError(
                f"Widget login: unexpected title '{title}'"
            )

        # Step 4: Extract service ticket — ticket may appear under any service URL
        ticket_match = _TICKET_RE.search(r.text)
        if not ticket_match:
            raise GarminConnectConnectionError("Widget login: missing service ticket")

        self._establish_session(ticket_match.group(1), sess=sess, service_url=sso_embed)

    def _complete_mfa_widget(self, mfa_code: str) -> None:
        """Complete MFA for widget flow."""
        sess = getattr(self, "_mfa_session", None)
        r = getattr(self, "_widget_last_resp", None)
        if not sess or not r:
            raise GarminConnectAuthenticationError("Missing widget MFA context")

        csrf_match = _CSRF_RE.search(r.text)
        if not csrf_match:
            raise GarminConnectAuthenticationError("Widget MFA: missing CSRF token")

        r = sess.post(
            f"{self._sso}/sso/verifyMFA/loginEnterMfaCode",
            params=getattr(self, "_mfa_login_params", {}),
            headers=getattr(self, "_mfa_post_headers", {}),
            data={
                "mfa-code": mfa_code,
                "embed": "true",
                "_csrf": csrf_match.group(1),
                "fromPage": "setupEnterMfaCode",
            },
            timeout=30,
        )
        _raise_if_rate_limited(r, "Widget MFA verify")

        title = _page_title(r.text)
        if title != "Success":
            raise GarminConnectAuthenticationError(f"Widget MFA failed: {title}")

        ticket_match = _TICKET_RE.search(r.text)
        if not ticket_match:
            raise GarminConnectAuthenticationError("Widget MFA: missing service ticket")

        self._establish_session(
            ticket_match.group(1),
            sess=sess,
            service_url=f"{self._sso}/sso/embed",
        )

    def _widget_request_mfa_code(self, sess: Any, page_html: str, referer: str) -> None:
        """Request Garmin to send an email/SMS MFA code for this widget session.

        The widget's own JavaScript calls ``/sso/verifyMFA/mfaCode`` when the
        user clicks "Request a new code". We use the same endpoint to ensure
        the code is actually delivered before prompting the user.
        """
        mfa_vars = _parse_widget_mfa_vars(page_html)
        mfa_method = mfa_vars.get("mfaMethod", "").lower()
        if mfa_method not in ("email", "sms"):
            # Nothing to trigger for TOTP/authenticator apps.
            return

        if mfa_vars.get("codeSentTo"):
            # Garmin already sent a code during the signin POST.
            return

        client_id = mfa_vars.get("clientId", "")
        payload = {
            "customerGuid": mfa_vars.get("customerGuid", ""),
            "mfaMethod": mfa_vars.get("mfaMethod", ""),
            "locale": mfa_vars.get("locale", ""),
        }

        _LOGGER.debug(
            "Widget MFA: explicitly requesting %s code from Garmin", mfa_method
        )
        r = sess.post(
            f"{self._sso}/sso/verifyMFA/mfaCode",
            params={"clientId": client_id},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Referer": referer,
            },
            json=payload,
            timeout=30,
        )
        _raise_if_rate_limited(r, "Widget MFA code request")
        if not r.ok:
            raise GarminConnectConnectionError(
                f"Widget MFA code request returned {r.status_code}"
            )

    # ------------------------------------------------------------------ #
    #  STRATEGIES 4 & 5 — Portal web (curl_cffi rotation / plain requests) #
    # ------------------------------------------------------------------ #

    def _portal_web_login_cffi(self, email: str, password: str) -> None:
        """Portal login with curl_cffi TLS fingerprint rotation."""
        self._login_with_impersonations(
            "portal+cffi",
            PORTAL_IMPERSONATIONS,
            self._do_portal_web_login,
            email,
            password,
        )

    def _portal_web_login_requests(self, email: str, password: str) -> None:
        """Portal login with plain requests (no TLS fingerprinting)."""
        self._do_portal_web_login(requests.Session(), email, password)

    def _do_portal_web_login(self, sess: Any, email: str, password: str) -> None:
        """Login via /portal/api/login — desktop browser flow."""
        signin_url = f"{self._sso}/portal/sso/en-US/sign-in"
        browser_hdrs = _random_browser_headers()

        # Step 1: GET the signin page to grab initial cookies
        get_resp = sess.get(
            signin_url,
            params={
                "clientId": PORTAL_SSO_CLIENT_ID,
                "service": self._portal_service_url,
            },
            headers={
                **browser_hdrs,
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30,
        )
        if get_resp.status_code == 429:
            raise GarminConnectTooManyRequestsError(
                "Portal login GET returned 429 — Cloudflare blocking this request."
            )

        # Anti-WAF delay: 10-20s mimics real browser "read then type" behaviour.
        delay_s = random.uniform(LOGIN_DELAY_MIN_S, LOGIN_DELAY_MAX_S)  # noqa: S311
        _LOGGER.info(
            "Portal login: waiting %.0fs to avoid Cloudflare rate limiting...",
            delay_s,
        )
        time.sleep(delay_s)

        # Step 2: POST credentials
        self._post_credentials(
            sess,
            "Portal login",
            f"{self._sso}/portal/api/login",
            {
                "clientId": PORTAL_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": self._portal_service_url,
            },
            {
                **browser_hdrs,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Origin": self._sso,
                "Referer": (
                    f"{signin_url}?clientId={PORTAL_SSO_CLIENT_ID}"
                    f"&service={self._portal_service_url}"
                ),
            },
            service_url=self._portal_service_url,
            flow="portal",
            email=email,
            password=password,
        )

    # ------------------------------------------------------------------ #
    #  MFA COMPLETION — dual-endpoint fallback                           #
    # ------------------------------------------------------------------ #

    def _complete_mfa(self, mfa_code: str) -> None:
        """Complete MFA — routes to the handler matching the login flow.

        For portal/ios flows, tries both /portal and /mobile MFA verify
        endpoints as they may be on different rate-limit buckets.
        """
        # getattr's default only applies when the attribute is absent, not
        # when it's present-but-None (e.g. right after a state reset) — the
        # `or` catches that case too.
        flow = getattr(self, "_mfa_flow", None) or "portal"
        if flow == "widget":
            self._complete_mfa_widget(mfa_code)
            return

        sess = self._mfa_session

        mfa_json: dict[str, Any] = {
            "mfaMethod": getattr(self, "_mfa_method", "email"),
            "mfaVerificationCode": mfa_code,
            "rememberMyBrowser": True,
            "reconsentList": [],
            "mfaSetup": False,
        }

        # Map flow name to SSO path segment ("ios" flow uses /mobile/ endpoint)
        flow_path = "mobile" if flow == "ios" else flow

        # Try both MFA endpoints — they share SSO session cookies but may be
        # on different rate-limit buckets.
        mfa_endpoints: list[tuple[str, dict[str, str], dict[str, str]]] = [
            (
                f"{self._sso}/{flow_path}/api/mfa/verifyCode",
                self._mfa_login_params,
                self._mfa_post_headers,
            ),
        ]
        # Add the other path as fallback
        if flow_path == "mobile":
            alt_endpoint = f"{self._sso}/portal/api/mfa/verifyCode"
            alt_params: dict[str, str] = {
                "clientId": PORTAL_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": self._portal_service_url,
            }
        else:
            alt_endpoint = f"{self._sso}/mobile/api/mfa/verifyCode"
            alt_params = {
                "clientId": IOS_SSO_CLIENT_ID,
                "locale": "en-US",
                "service": self._ios_service_url,
            }
        mfa_endpoints.append((alt_endpoint, alt_params, self._mfa_post_headers))

        failures: list[str] = []
        rate_limited_count = 0

        for mfa_url, params, headers in mfa_endpoints:
            try:
                r = sess.post(
                    mfa_url,
                    params=params,
                    headers=headers,
                    json=mfa_json,
                    timeout=30,
                )
            except Exception as e:
                failures.append(f"{mfa_url}: connection error {e}")
                continue

            if r.status_code == 429:
                failures.append(f"{mfa_url}: HTTP 429")
                rate_limited_count += 1
                continue

            try:
                res = r.json()
            except Exception:
                # Non-JSON response is almost always a Cloudflare HTML challenge
                failures.append(f"{mfa_url}: HTTP {r.status_code} non-JSON")
                continue

            if res.get("error", {}).get("status-code") == "429":
                failures.append(f"{mfa_url}: 429 in JSON body")
                rate_limited_count += 1
                continue

            if res.get("responseStatus", {}).get("type") == "SUCCESSFUL":
                ticket = res["serviceTicketId"]
                svc_url = (
                    self._ios_service_url
                    if flow == "ios"
                    else getattr(self, "_mfa_service_url", self._portal_service_url)
                )
                self._establish_session(ticket, sess=sess, service_url=svc_url)
                return

            # Non-success JSON response — could be auth failure. The status is
            # captured in `failures` below for the eventual exception message;
            # no separate debug log here (data flowing through this function
            # trips code-scanning's clear-text-logging heuristic).
            status = res.get("responseStatus", {}).get("type") or res.get(
                "error", {}
            ).get("status-code", "unknown")
            failures.append(f"{mfa_url}: {status}")

        # All endpoints failed
        if rate_limited_count == len(mfa_endpoints):
            raise GarminConnectTooManyRequestsError(
                f"MFA verification rate limited on all endpoints: {failures}"
            )
        raise GarminConnectAuthenticationError(f"MFA verification failed: {failures}")
