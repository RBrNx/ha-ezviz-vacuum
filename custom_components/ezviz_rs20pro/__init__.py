"""EZVIZ RS20 Pro integration."""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service
import voluptuous as vol

from .const import (
    DOMAIN,
    SERVICE_API_REQUEST,
    SERVICE_CAMERA_DIAGNOSTICS,
    SERVICE_FEATURE_REQUEST,
    SERVICE_INSPECT,
    SERVICE_MAP_DIAGNOSTICS,
    SERVICE_REFRESH_CAMERA,
)
from .coordinator import EzvizRs20ProCoordinator, get_source_entry

PLATFORMS = [Platform.IMAGE, Platform.SENSOR, Platform.SWITCH, Platform.VACUUM]

type EzvizRs20ProConfigEntry = ConfigEntry[EzvizRs20ProCoordinator]

_SENSITIVE_PARTS = (
    "accesscode",
    "authcode",
    "content",
    "encryptpwd",
    "key",
    "password",
    "pwd",
    "secret",
    "session",
    "token",
    "verificationcode",
)


def _sanitize(value: Any) -> Any:
    """Remove authentication material while preserving protocol metadata."""
    if isinstance(value, Mapping):
        return {
            str(key): "[redacted]"
            if any(part in str(key).casefold() for part in _SENSITIVE_PARTS)
            else _sanitize(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    return value


async def async_setup_entry(
    hass: HomeAssistant, entry: EzvizRs20ProConfigEntry
) -> bool:
    """Set up EZVIZ RS20 Pro from a config entry."""
    coordinator = EzvizRs20ProCoordinator(hass, entry, get_source_entry(hass, entry))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_INSPECT):

        async def async_inspect(call: ServiceCall) -> dict[str, Any]:
            """Return sanitized raw device data for protocol discovery."""
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                return {"error": "EZVIZ RS20 integration is not configured"}
            active = entries[0]
            runtime = getattr(active, "runtime_data", None)
            if not isinstance(runtime, EzvizRs20ProCoordinator):
                return {"error": "EZVIZ RS20 integration is not loaded"}
            await runtime.async_request_refresh()
            return _sanitize(runtime.data)

        hass.services.async_register(
            DOMAIN,
            SERVICE_INSPECT,
            async_inspect,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_MAP_DIAGNOSTICS):

        async def async_map_diagnostics(call: ServiceCall) -> dict[str, Any]:
            """Probe read-only map routes without returning authentication data."""
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                return {"error": "EZVIZ RS20 integration is not configured"}
            runtime = getattr(entries[0], "runtime_data", None)
            if not isinstance(runtime, EzvizRs20ProCoordinator):
                return {"error": "EZVIZ RS20 integration is not loaded"}
            if runtime.rs20_api is None:
                await runtime.async_request_refresh()
            if runtime.rs20_api is None:
                return {"error": "RS20 Pro client is not ready"}
            map_id = 5
            device = runtime.data.get("device", {})
            try:
                maps = device["FEATURE_INFO"]["0"]["SweepingRobot"]["SweeperMapMgr"]["MapBasicProperty"]
                if maps:
                    map_id = int(maps[0]["mapID"])
            except (KeyError, IndexError, TypeError, ValueError):
                pass
            result = await hass.async_add_executor_job(
                runtime.rs20_api.query_map_path_candidates,
                runtime.serial,
                map_id,
            )
            device = runtime.data.get("device", {})
            operation = {}
            try:
                operation = device["FEATURE_INFO"]["0"]["SweepingRobot"][
                    "OperationDiagnosis"
                ]["DeviceOperationParams"]
            except (KeyError, TypeError):
                pass
            return _sanitize(
                {
                    "map_id": map_id,
                    "candidates": result,
                    "client": runtime.rs20_api.client_diagnostics(),
                    "clean_history": runtime.rs20_api.decode_diagnostic_blob(
                        operation.get("cleanHistory")
                    ),
                    "abnormal_history": runtime.rs20_api.decode_diagnostic_blob(
                        operation.get("abnormalHistory")
                    ),
                }
            )

        hass.services.async_register(
            DOMAIN,
            SERVICE_MAP_DIAGNOSTICS,
            async_map_diagnostics,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CAMERA_DIAGNOSTICS):

        async def async_camera_diagnostics(call: ServiceCall) -> dict[str, Any]:
            """Verify encrypted cloud transport without returning media bytes."""
            entries = hass.config_entries.async_entries(DOMAIN)
            runtime = getattr(entries[0], "runtime_data", None) if entries else None
            if not isinstance(runtime, EzvizRs20ProCoordinator):
                return {"error": "EZVIZ RS20 integration is not loaded"}
            try:
                return _sanitize(await runtime.async_camera_trace())
            except Exception as err:
                return {"error": str(err)}

        hass.services.async_register(
            DOMAIN,
            SERVICE_CAMERA_DIAGNOSTICS,
            async_camera_diagnostics,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_CAMERA):

        async def async_refresh_camera(call: ServiceCall) -> None:
            """Capture a single robot-camera frame only when explicitly called."""
            entries = hass.config_entries.async_entries(DOMAIN)
            runtime = getattr(entries[0], "runtime_data", None) if entries else None
            if not isinstance(runtime, EzvizRs20ProCoordinator):
                raise HomeAssistantError("EZVIZ RS20 integration is not loaded")
            ffmpeg = hass.data.get("ffmpeg")
            ffmpeg_path = str(getattr(ffmpeg, "binary", "ffmpeg"))
            await runtime.async_refresh_camera_snapshot(ffmpeg_path)

        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_CAMERA,
            async_refresh_camera,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_FEATURE_REQUEST):

        async def async_feature_request(call: ServiceCall) -> dict[str, Any]:
            """Send one raw iot-feature request (protocol discovery)."""
            runtime = _first_coordinator(hass)
            if runtime.rs20_api is None:
                await runtime.async_request_refresh()
            result = await hass.async_add_executor_job(
                partial(
                    runtime.rs20_api.raw_feature_request,
                    runtime.serial,
                    method=call.data["method"],
                    endpoint=call.data["endpoint"],
                    domain=call.data["domain"],
                    identifier=call.data["identifier"],
                    payload=call.data.get("payload"),
                    resource=call.data.get("resource", "SweepingRobot"),
                    local_index=str(call.data.get("local_index", "0")),
                )
            )
            return _sanitize(result)

        async_register_admin_service(
            hass,
            DOMAIN,
            SERVICE_FEATURE_REQUEST,
            async_feature_request,
            schema=vol.Schema(
                {
                    vol.Required("method"): vol.In(["GET", "PUT"]),
                    vol.Required("endpoint"): vol.In(["feature", "action"]),
                    vol.Required("domain"): cv.string,
                    vol.Required("identifier"): cv.string,
                    vol.Optional("payload"): object,
                    vol.Optional("resource"): cv.string,
                    vol.Optional("local_index"): vol.Coerce(str),
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_API_REQUEST):

        async def async_api_request(call: ServiceCall) -> dict[str, Any]:
            """Send one raw request to the EZVIZ API host (protocol discovery)."""
            runtime = _first_coordinator(hass)
            if runtime.rs20_api is None:
                await runtime.async_request_refresh()
            result = await hass.async_add_executor_job(
                partial(
                    runtime.rs20_api.raw_api_request,
                    method=call.data["method"],
                    path=call.data["path"],
                    params=call.data.get("params"),
                    data=call.data.get("data"),
                )
            )
            return _sanitize(result)

        async_register_admin_service(
            hass,
            DOMAIN,
            SERVICE_API_REQUEST,
            async_api_request,
            schema=vol.Schema(
                {
                    vol.Required("method"): vol.In(["GET", "POST", "PUT"]),
                    vol.Required("path"): cv.string,
                    vol.Optional("params"): dict,
                    vol.Optional("data"): dict,
                }
            ),
            supports_response=SupportsResponse.ONLY,
        )

    return True


def _first_coordinator(hass: HomeAssistant) -> EzvizRs20ProCoordinator:
    """Return the coordinator of the first loaded robot entry."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if isinstance(runtime, EzvizRs20ProCoordinator):
            return runtime
    raise HomeAssistantError("EZVIZ RS20 integration is not loaded")


async def async_unload_entry(
    hass: HomeAssistant, entry: EzvizRs20ProConfigEntry
) -> bool:
    """Unload EZVIZ RS20 Pro."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and len(hass.config_entries.async_entries(DOMAIN)) <= 1:
        hass.services.async_remove(DOMAIN, SERVICE_INSPECT)
        hass.services.async_remove(DOMAIN, SERVICE_MAP_DIAGNOSTICS)
        hass.services.async_remove(DOMAIN, SERVICE_CAMERA_DIAGNOSTICS)
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH_CAMERA)
        hass.services.async_remove(DOMAIN, SERVICE_FEATURE_REQUEST)
        hass.services.async_remove(DOMAIN, SERVICE_API_REQUEST)
    return unloaded
