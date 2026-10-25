"""The integration's own EZVIZ cloud session (no Home Assistant imports).

Login, token refresh, the device list and camera keys come from pyezvizapi's
public client API. Robot endpoints that pyezvizapi has no method for (the
iot-feature calls with their error details, map layers, plugin catalogue) go
through a separate HTTP session of this integration, authenticated with the
session ID from the client's public ``export_token()``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pyezvizapi import EzvizClient
from pyezvizapi.constants import DEFAULT_TIMEOUT, REQUEST_HEADER
import requests

EU_URL = "apiieu.ezvizlife.com"
RUSSIA_URL = "apirus.ezvizru.com"


class EzvizCloudError(Exception):
    """Raised when there is no usable EZVIZ session."""


def _meta_code(response: requests.Response) -> Any:
    try:
        body = response.json()
    except ValueError:
        return None
    meta = body.get("meta") if isinstance(body, dict) else None
    return meta.get("code") if isinstance(meta, dict) else None


class EzvizCloud:
    """One logged-in EZVIZ account."""

    def __init__(
        self,
        client: EzvizClient,
        *,
        timeout: int = DEFAULT_TIMEOUT,
        on_token_updated: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.client = client
        self.timeout = timeout
        self._http = requests.Session()
        self._on_token_updated = on_token_updated
        self._last_session: tuple[Any, Any] | None = None
        if on_token_updated is not None:
            self._last_session = self._session_key(self.token())

    @classmethod
    def from_token(
        cls,
        token: dict[str, Any],
        *,
        on_token_updated: Callable[[dict[str, Any]], None] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> EzvizCloud:
        """Resume a stored session; ``refresh()`` renews it."""
        # pyezvizapi releases before the token callback existed do not accept
        # ``on_token_updated``; this class reports token changes itself.
        client = EzvizClient(
            token=dict(token),
            url=str(token.get("api_url") or EU_URL),
            timeout=timeout,
        )
        return cls(client, timeout=timeout, on_token_updated=on_token_updated)

    @staticmethod
    def _session_key(token: dict[str, Any]) -> tuple[Any, Any]:
        return (token.get("session_id"), token.get("rf_session_id"))

    def _report_token_change(self) -> None:
        """Call ``on_token_updated`` when the client renewed its session."""
        if self._on_token_updated is None:
            return
        token = self.token()
        key = self._session_key(token)
        if key != self._last_session:
            self._last_session = key
            self._on_token_updated(token)

    def refresh(self) -> dict[str, Any]:
        """Renew the session from its refresh token; return the new token."""
        self.client.login()
        self._report_token_change()
        return self.token()

    def token(self) -> dict[str, Any]:
        """Return a copy of the current session token."""
        return self.client.export_token()

    def device_infos(self, serial: str | None = None) -> dict[str, Any]:
        """Return every device on the account keyed by serial, or one device."""
        try:
            if serial is None:
                return self.client.get_device_infos()
            return self.client.get_device_infos(serial)
        finally:
            # pyezvizapi re-logs in by itself when the session has expired.
            self._report_token_change()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
        retry: bool = True,
    ) -> requests.Response:
        """Send one request to the account's EZVIZ API host.

        An expired session is renewed once and the request repeated.
        """
        token = self.token()
        api_url = token.get("api_url")
        session_id = token.get("session_id")
        if not api_url or not session_id:
            raise EzvizCloudError("The EZVIZ session is not logged in")
        request_headers = {str(k): str(v) for k, v in REQUEST_HEADER.items()}
        request_headers["sessionId"] = str(session_id)
        request_headers.update(headers or {})
        response = self._http.request(
            method,
            f"https://{api_url}{path}",
            params=params,
            data=data,
            json=json_body,
            headers=request_headers,
            timeout=self.timeout,
        )
        if retry and (
            response.status_code == 401 or _meta_code(response) in (401, "401")
        ):
            self.refresh()
            return self.request(
                method,
                path,
                params=params,
                data=data,
                json_body=json_body,
                headers=headers,
                retry=False,
            )
        return response

    def get_url(self, url: str, *, params: dict[str, Any] | None = None) -> Any:
        """GET an absolute URL on another EZVIZ host (camera token server)."""
        response = self._http.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close this integration's HTTP session."""
        self._http.close()
        self.client.close_session()


def new_client(username: str, password: str, url: str) -> EzvizClient:
    """Create a client for signing in with the account's own credentials."""
    return EzvizClient(username, password, url or EU_URL, DEFAULT_TIMEOUT)


def sign_in(client: EzvizClient, sms_code: int | None = None) -> dict[str, Any]:
    """Log in and return the session token (never the password).

    When EZVIZ asks for a verification code, call again with the same client
    and ``sms_code``.
    """
    client.login(sms_code=sms_code)
    return client.export_token()
