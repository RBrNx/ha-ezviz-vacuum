"""Vacuum platform for EZVIZ RS20 Pro."""

from __future__ import annotations

from typing import Any

from homeassistant.components.vacuum import (
    Segment,
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EzvizRs20ProCoordinator
from . import robot
from .helpers import find_value as _find_value

_ERROR_TRANSLATIONS = {
    "CR_CleanWaterBoxLow": "Clean water tank is low",
}






async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RS20 Pro vacuum entity."""
    async_add_entities([EzvizRs20ProVacuum(entry.runtime_data)])


class EzvizRs20ProVacuum(CoordinatorEntity[EzvizRs20ProCoordinator], StateVacuumEntity):
    """EZVIZ RS20 Pro vacuum entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        VacuumEntityFeature.STATE
        | VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.CLEAN_AREA
    )

    def __init__(self, coordinator: EzvizRs20ProCoordinator) -> None:
        super().__init__(coordinator)
        serial = coordinator.data["serial"]
        self._attr_unique_id = f"{serial}_vacuum"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer="EZVIZ",
            model="RS20 Pro",
            name="EZVIZ RS20 Pro",
            sw_version=str(
                _find_value(coordinator.data["device"], ("version",)) or ""
            ),
        )

    @property
    def activity(self) -> VacuumActivity:
        """Return the task state reported by the sweeper endpoint."""
        task = self.coordinator.data.get("task", {})
        task_state = str(
            _find_value(
                task,
                ("taskstate", "status", "cleantaskstatus", "currenttask"),
            )
            or ""
        ).casefold()
        if any(value in task_state for value in ("clean", "working", "start", "running")):
            return VacuumActivity.CLEANING
        if any(value in task_state for value in ("pause", "suspend")):
            return VacuumActivity.PAUSED
        if any(value in task_state for value in ("return", "chargeback", "backcharge")):
            return VacuumActivity.RETURNING
        if any(value in task_state for value in ("dock", "charging", "charge")):
            return VacuumActivity.DOCKED

        device = self.coordinator.data["device"]
        exception = _find_value(device, ("exception",))
        if exception not in (None, "", "none", "normal"):
            return VacuumActivity.ERROR
        in_charging = _find_value(task or device, ("incharging", "charging"))
        if in_charging in (True, 1, "1", "true"):
            return VacuumActivity.DOCKED
        status = _find_value(device, ("globalstatus", "onlinestatus", "status"))
        if status in (0, "0", False, "offline"):
            return VacuumActivity.ERROR
        return VacuumActivity.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose useful task and maintenance details."""
        device = self.coordinator.data["device"]
        error = _find_value(device, ("exception",))
        description = _find_value(device, ("exceptiondesc",))
        return {
            "cleaning_mode": _find_value(device, ("sweepmopmode",)),
            "error": error,
            "error_description": _ERROR_TRANSLATIONS.get(str(error), description),
            "current_task": _find_value(
                self.coordinator.data.get("task", {}),
                ("currenttask", "taskstate", "cleantaskstatus"),
            ),
            "query_error": self.coordinator.data.get("task_error"),
        }

    async def async_start(self) -> None:
        """Start or resume cleaning."""
        await self.coordinator.async_clean_control("start")

    async def async_pause(self) -> None:
        """Pause cleaning."""
        await self.coordinator.async_clean_control("pause")

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop cleaning."""
        await self.coordinator.async_clean_control("stop")

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Return the robot to its base."""
        await self.coordinator.async_clean_control("return_charge")

    async def async_get_segments(self) -> list[Segment]:
        """Return the rooms available on the active robot map."""
        await self.coordinator.async_request_refresh()
        device = self.coordinator.data.get("device", {})
        map_id = robot.active_map_id(device, self.coordinator.data.get("task"))
        group = robot.map_name(device, map_id)
        return [
            Segment(id=room_id, name=name, group=group)
            for room_id, name in robot.rooms(device, map_id)
        ]

    async def async_clean_segments(
        self, segment_ids: list[str], **kwargs: Any
    ) -> None:
        """Clean rooms selected through Home Assistant area mapping."""
        await self.coordinator.async_clean_segments(segment_ids)
