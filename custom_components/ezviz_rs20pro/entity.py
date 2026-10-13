"""Base entity shared by all robot platforms."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import robot
from .const import DOMAIN
from .coordinator import EzvizRs20ProCoordinator


class Rs20Entity(CoordinatorEntity[EzvizRs20ProCoordinator]):
    """Entity attached to one robot device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EzvizRs20ProCoordinator, key: str) -> None:
        super().__init__(coordinator)
        serial = coordinator.data["serial"]
        self._attr_unique_id = f"{serial}_{key}"
        details = robot.device_details(coordinator.data.get("device"))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer="EZVIZ",
            model=details["model"],
            model_id=details["model_id"],
            name=details["name"],
            sw_version=details["sw_version"],
            serial_number=serial,
        )
