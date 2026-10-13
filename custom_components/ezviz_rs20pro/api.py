"""EZVIZ robot requests layered on the authenticated pyezviz client."""

from __future__ import annotations

import base64
import gzip
from importlib import metadata
import json
from typing import Any
import zlib

from .const import CLEAN_MODES, WRITABLE_FEATURES


class EzvizRs20ProApiError(Exception):
    """Raised when the robot endpoint rejects a request."""


# Details the cloud sends in Chinese when it refuses a request.
_REJECTIONS = {
    "设备不支持该功能": "the robot does not support this",
    "设备功能未报备": "this model does not declare this function",
    "设备不在线": "the robot is offline",
    "设备响应超时": "the robot did not answer in time",
}


def rejection_reason(result: dict[str, Any], code: Any) -> str:
    """Return a readable reason for a refused request."""
    meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
    message = meta.get("message") or result.get("msg") or "request refused"
    more = meta.get("moreInfo")
    detail = more.get("msgDetail") if isinstance(more, dict) else None
    if isinstance(detail, str) and detail:
        detail = _REJECTIONS.get(detail.strip(), detail.strip())
        if len(detail) > 300:
            detail = detail[:300] + "..."
        return f"{message} ({detail}, code {code})"
    return f"{message} (code {code})"


class EzvizRs20ProApi:
    """Use the official integration's session without copying credentials."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def query_current_task(self, serial: str) -> dict[str, Any]:
        """Query current task; this action does not move or configure the robot."""
        return self._iot_request(
            serial,
            endpoint="action",
            domain="SweeperTaskMgr",
            identifier="QueryCurrentTask",
            payload={},
        )

    def clean_control(self, serial: str, command: str) -> dict[str, Any]:
        """Run one of the documented cleaning controls."""
        if command not in {"start", "pause", "stop", "return_charge"}:
            raise ValueError(f"Unsupported robot command: {command}")
        return self._iot_request(
            serial,
            endpoint="action",
            domain="SweeperCleanTask",
            identifier="CleanControl",
            payload=command,
        )

    def set_clean_mode(self, serial: str, mode: str) -> dict[str, Any]:
        """Set the sweep/mop mode used by future cleaning runs."""
        if mode not in CLEAN_MODES:
            raise ValueError(f"Unsupported cleaning mode: {mode}")
        return self._iot_request(
            serial,
            endpoint="feature",
            domain="SweeperCleanTask",
            identifier="SweepMopMode",
            payload=mode,
        )

    def set_feature(
        self,
        serial: str,
        *,
        domain: str,
        identifier: str,
        value: Any,
    ) -> dict[str, Any]:
        """Write the complete value of an allow-listed robot setting."""
        if (domain, identifier) not in WRITABLE_FEATURES:
            raise ValueError(f"Unsupported robot setting: {domain}/{identifier}")
        if value is None:
            raise ValueError(f"No value for {domain}/{identifier}")
        return self._iot_request(
            serial,
            endpoint="feature",
            domain=domain,
            identifier=identifier,
            payload=value,
        )

    def start_region_clean(
        self,
        serial: str,
        *,
        map_id: int,
        rooms: list[dict[str, Any]],
        clean_mode: str = "sweep",
    ) -> dict[str, Any]:
        """Start cleaning selected map rooms using the robot's native action."""
        if not rooms:
            raise ValueError("No room selected")
        if clean_mode not in CLEAN_MODES:
            raise ValueError(f"Unsupported cleaning mode: {clean_mode}")
        payload = {
            "cleanMode": clean_mode,
            "mapID": int(map_id),
            "region": rooms,
            "edgeDeepClean": False,
        }
        return self._iot_request(
            serial,
            endpoint="action",
            domain="SweeperCleanTask",
            identifier="StartRegionClean",
            payload=payload,
        )

    def client_diagnostics(self) -> dict[str, Any]:
        """Return non-secret client capability and service-host information."""
        token = getattr(self._client, "_token", None)
        service_urls: dict[str, Any] = {}
        if isinstance(token, dict) and isinstance(token.get("service_urls"), dict):
            service_urls = token["service_urls"]
        version = "unknown"
        try:
            version = metadata.version("pyezvizapi")
        except metadata.PackageNotFoundError:
            pass
        return {
            "pyezvizapi_version": version,
            "client_module": type(self._client).__module__,
            "capabilities": {
                name: hasattr(self._client, name)
                for name in (
                    "_api_get_pagelist",
                    "_http_request",
                    "_parse_json",
                    "_request_json",
                    "get_cam_key",
                    "get_service_urls",
                )
            },
            "service_urls": service_urls,
        }

    def query_map_path_candidates(self, serial: str, map_id: int) -> list[dict[str, Any]]:
        """Probe known read-only map-path routes used by EZVIZ applications."""
        session = getattr(self._client, "_session", None)
        token = getattr(self._client, "_token", None)
        if session is None or not isinstance(token, dict):
            raise EzvizRs20ProApiError("Active EZVIZ session is unavailable")
        api_url = token.get("api_url")
        if not api_url:
            raise EzvizRs20ProApiError("No API address in the active EZVIZ session")

        routes = (
            "/v3/specialBizs/sweeprobot/v3/rule/path",
            "/api/specialbiz/v3/sweeprobot/v3/rule/path",
        )
        payload = {"deviceSerial": serial.upper(), "mapId": str(map_id)}
        results: list[dict[str, Any]] = []
        for route in routes:
            try:
                response = session.post(
                    f"https://{api_url}{route}",
                    data=payload,
                    timeout=getattr(self._client, "_timeout", 25),
                )
                parsed: Any
                try:
                    parsed = response.json()
                except ValueError:
                    parsed = {"response_type": response.headers.get("Content-Type", "")}
                results.append(
                    {
                        "route": route,
                        "http_status": response.status_code,
                        "response": parsed,
                    }
                )
            except Exception as err:
                results.append({"route": route, "error": str(err)})
        return results

    @staticmethod
    def decode_diagnostic_blob(blob: Any) -> Any:
        """Decode the gzip/base64 diagnostic fields reported by the robot."""
        if not isinstance(blob, dict) or not isinstance(blob.get("content"), str):
            return None
        try:
            raw = base64.b64decode(blob["content"], validate=True)
        except (ValueError, TypeError):
            return {"error": "Invalid base64 encoding"}

        decoded: bytes | None = None
        for decoder in (
            gzip.decompress,
            zlib.decompress,
            lambda data: zlib.decompress(data, -zlib.MAX_WBITS),
        ):
            try:
                decoded = decoder(raw)
                break
            except (OSError, zlib.error):
                continue
        if decoded is None:
            decoded = raw
        try:
            text = decoded.decode("utf-8")
        except UnicodeDecodeError:
            return {"binary_bytes": len(decoded)}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text[:4000], "truncated": len(text) > 4000}

    def raw_feature_request(
        self,
        serial: str,
        *,
        method: str,
        endpoint: str,
        domain: str,
        identifier: str,
        payload: Any = None,
        resource: str = "SweepingRobot",
        local_index: str = "0",
    ) -> dict[str, Any]:
        """Send one iot-feature request and return the raw response.

        Used by the admin-only protocol diagnostics service. Errors reported
        by the cloud are returned instead of raised so they can be inspected.
        """
        method = method.upper()
        if method not in {"GET", "PUT"}:
            raise ValueError("Only GET and PUT are supported")
        if endpoint not in {"feature", "action"}:
            raise ValueError("Endpoint must be 'feature' or 'action'")
        session, api_url = self._session_and_host()
        url = (
            f"https://{api_url}/v3/iot-feature/{endpoint}/"
            f"{serial.upper()}/{resource}/{local_index}/{domain}/{identifier}"
        )
        headers = dict(session.headers)
        kwargs: dict[str, Any] = {
            "headers": headers,
            "timeout": getattr(self._client, "_timeout", 25),
        }
        if method == "PUT":
            headers["Content-Type"] = "application/json"
            kwargs["data"] = json.dumps(payload, separators=(",", ":"))
        response = session.request(method, url, **kwargs)
        try:
            body: Any = response.json()
        except ValueError:
            body = {"text": response.text[:2000]}
        return {"http_status": response.status_code, "response": body}

    def raw_api_request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send one request to the EZVIZ API host of the active session."""
        method = method.upper()
        if method not in {"GET", "POST", "PUT"}:
            raise ValueError("Only GET, POST and PUT are supported")
        if not path.startswith("/") or "://" in path:
            raise ValueError("Path must be relative to the EZVIZ API host")
        session, api_url = self._session_and_host()
        response = session.request(
            method,
            f"https://{api_url}{path}",
            params=params,
            data=data,
            json=json_body,
            headers={str(k): str(v) for k, v in (headers or {}).items()} or None,
            timeout=getattr(self._client, "_timeout", 25),
        )
        try:
            body: Any = response.json()
        except ValueError:
            body = {
                "content_type": response.headers.get("Content-Type", ""),
                "bytes": len(response.content or b""),
            }
        return {"http_status": response.status_code, "response": body}

    def _session_and_host(self) -> tuple[Any, str]:
        session = getattr(self._client, "_session", None)
        token = getattr(self._client, "_token", None)
        if session is None or not isinstance(token, dict):
            raise EzvizRs20ProApiError("Active EZVIZ session is unavailable")
        api_url = token.get("api_url")
        if not api_url:
            raise EzvizRs20ProApiError("No API address in the active EZVIZ session")
        return session, str(api_url)

    def _iot_request(
        self,
        serial: str,
        *,
        endpoint: str,
        domain: str,
        identifier: str,
        payload: Any,
    ) -> dict[str, Any]:
        session, api_url = self._session_and_host()

        url = (
            f"https://{api_url}/v3/iot-feature/{endpoint}/"
            f"{serial.upper()}/SweepingRobot/0/{domain}/{identifier}"
        )
        headers = dict(session.headers)
        headers["Content-Type"] = "application/json"
        response = session.put(
            url,
            headers=headers,
            data=json.dumps(payload, separators=(",", ":")),
            timeout=getattr(self._client, "_timeout", 25),
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise EzvizRs20ProApiError("EZVIZ returned an invalid response")

        meta = result.get("meta")
        code = meta.get("code") if isinstance(meta, dict) else result.get("code")
        if code not in (None, 0, 200, "0", "200"):
            raise EzvizRs20ProApiError(
                f"{domain}/{identifier}: {rejection_reason(result, code)}"
            )
        return result
