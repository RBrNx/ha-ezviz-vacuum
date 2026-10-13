"""Coordinator for EZVIZ RS20 Pro."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from functools import partial
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import robot
from .api import EzvizRs20ProApi, EzvizRs20ProApiError
from .cloud_camera import capture_cloud_snapshot, trace_cloud_stream
from .const import (
    CONF_SERIAL,
    CONF_SOURCE_ENTRY_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def _find_api(runtime_data: Any) -> Any | None:
    """Find the pyezviz client without depending on HA's private data class."""
    candidates = (
        runtime_data,
        getattr(runtime_data, "coordinator", None),
        getattr(runtime_data, "data", None),
    )
    for candidate in candidates:
        if candidate is None:
            continue
        for attribute in ("api", "client", "ezviz_client"):
            api = getattr(candidate, attribute, None)
            if api is not None and hasattr(api, "get_device_infos"):
                return api
        if hasattr(candidate, "get_device_infos"):
            return candidate
    return None


class EzvizRs20ProCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch RS20 Pro data through the already authenticated EZVIZ client."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        source_entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.entry = entry
        self.source_entry = source_entry
        self.serial: str = entry.data.get(CONF_SERIAL, "")
        self.rs20_api: EzvizRs20ProApi | None = None
        self.camera_snapshot: bytes | None = None
        self.camera_snapshot_updated: datetime | None = None

    def _api(self) -> Any:
        if self.source_entry.state is not ConfigEntryState.LOADED:
            raise ConfigEntryNotReady("Official EZVIZ integration is not loaded")
        api = _find_api(getattr(self.source_entry, "runtime_data", None))
        if api is None:
            raise ConfigEntryNotReady("No active EZVIZ session found")
        return api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            source_api = self._api()
            raw = await self.hass.async_add_executor_job(source_api.get_device_infos)
        except ConfigEntryNotReady:
            raise
        except Exception as err:
            raise UpdateFailed(f"EZVIZ read error: {err}") from err

        if not isinstance(raw, Mapping):
            raise UpdateFailed("EZVIZ returned an invalid device list")

        selected_serial = self.serial
        if selected_serial:
            selected = raw.get(selected_serial)
            if not isinstance(selected, Mapping):
                raise UpdateFailed(f"Device not found: {selected_serial}")
        else:
            matches = [
                (str(serial), payload)
                for serial, payload in raw.items()
                if isinstance(payload, Mapping) and robot.is_robot(payload)
            ]
            if not matches:
                raise UpdateFailed("No EZVIZ robot vacuum found on the account")
            selected_serial, selected = matches[0]
            self.serial = selected_serial

        self.rs20_api = EzvizRs20ProApi(source_api)
        task: dict[str, Any] = {}
        task_error: str | None = None
        try:
            task = await self.hass.async_add_executor_job(
                self.rs20_api.query_current_task,
                selected_serial,
            )
        except Exception as err:
            task_error = str(err)

        return {
            "serial": selected_serial,
            "device": dict(selected),
            "task": task,
            "task_error": task_error,
        }

    async def _async_call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Run a blocking API call and turn failures into HA errors."""
        if self.rs20_api is None:
            raise HomeAssistantError("The robot client is not ready yet")
        try:
            return await self.hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        except EzvizRs20ProApiError as err:
            raise HomeAssistantError(f"EZVIZ rejected the command: {err}") from err
        except Exception as err:
            raise HomeAssistantError(
                f"Could not reach the EZVIZ cloud: {err}"
            ) from err

    async def async_clean_control(self, command: str) -> None:
        """Send a documented robot control and refresh state."""
        await self._async_call(self.rs20_api.clean_control, self.serial, command)
        await self.async_request_refresh()

    async def async_set_clean_mode(self, mode: str) -> None:
        """Set cleaning mode and refresh state."""
        await self._async_call(self.rs20_api.set_clean_mode, self.serial, mode)
        await self.async_request_refresh()

    async def async_set_station_feature(
        self,
        *,
        domain: str,
        identifier: str,
        value: dict[str, Any],
    ) -> None:
        """Update an allow-listed station setting and refresh device state."""
        await self._async_call(
            self.rs20_api.set_station_feature,
            self.serial,
            domain=domain,
            identifier=identifier,
            value=value,
        )
        await self.async_request_refresh()

    async def async_clean_segments(self, segment_ids: list[str]) -> None:
        """Start a native room-cleaning task for selected segment IDs."""
        if self.rs20_api is None:
            raise HomeAssistantError("The robot client is not ready yet")
        device = self.data.get("device", {})
        map_id = robot.active_map_id(device, self.data.get("task"))
        configs = robot.room_clean_configs(device, map_id)
        if map_id is None or not configs:
            raise HomeAssistantError("The robot has not reported its rooms yet")

        requested = {str(item) for item in segment_ids}
        rooms = [dict(item) for item in configs if str(item.get("roomID")) in requested]
        found = {str(item.get("roomID")) for item in rooms}
        missing = requested - found
        if missing:
            raise ServiceValidationError(
                f"Unknown robot rooms: {', '.join(sorted(missing))}"
            )
        for order, room in enumerate(rooms, start=1):
            room["order"] = order
        await self._async_call(
            self.rs20_api.start_region_clean,
            self.serial,
            map_id=map_id,
            rooms=rooms,
            clean_mode=robot.clean_mode(device) or "sweep",
        )
        await self.async_request_refresh()

    async def async_camera_trace(self) -> dict[str, Any]:
        """Open a short, body-free camera transport diagnostic."""
        return await self.hass.async_add_executor_job(
            trace_cloud_stream,
            self._api(),
            self.serial,
        )

    async def async_refresh_camera_snapshot(self, ffmpeg_path: str) -> None:
        """Capture one image on demand and immediately close the video stream."""
        from homeassistant.util import dt as dt_util

        try:
            self.camera_snapshot = await self.hass.async_add_executor_job(
                partial(
                    capture_cloud_snapshot,
                    self._api(),
                    self.serial,
                    ffmpeg_path,
                )
            )
        except ConfigEntryNotReady as err:
            raise HomeAssistantError(str(err)) from err
        except Exception as err:
            raise HomeAssistantError(f"Could not capture a snapshot: {err}") from err
        self.camera_snapshot_updated = dt_util.utcnow()
        self.async_update_listeners()


def get_source_entry(hass: HomeAssistant, entry: ConfigEntry) -> ConfigEntry:
    """Resolve the official EZVIZ config entry."""
    source_id = entry.data[CONF_SOURCE_ENTRY_ID]
    source = hass.config_entries.async_get_entry(source_id)
    if source is None:
        raise ConfigEntryNotReady("Referenced EZVIZ integration not found")
    return source
