"""Binary sensors for EZVIZ robot vacuums."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import robot
from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20Entity


@dataclass(frozen=True, kw_only=True)
class Rs20BinarySensorDescription(BinarySensorEntityDescription):
    """Describe a yes/no value of the live task."""

    value_fn: Callable[[Mapping[str, Any]], Any]


BINARY_SENSORS: Final[tuple[Rs20BinarySensorDescription, ...]] = (
    Rs20BinarySensorDescription(
        key="on_base_station",
        translation_key="on_base_station",
        icon="mdi:home-import-outline",
        value_fn=lambda data: robot.task_data(data.get("task")).get("isOnBasestation"),
    ),
    Rs20BinarySensorDescription(
        key="do_not_disturb_active",
        translation_key="do_not_disturb_active",
        icon="mdi:sleep",
        value_fn=lambda data: robot.task_data(data.get("task")).get("inDNDMode"),
    ),
)


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the robot binary sensors."""
    async_add_entities(
        Rs20BinarySensor(entry.runtime_data, description)
        for description in BINARY_SENSORS
    )


class Rs20BinarySensor(Rs20Entity, BinarySensorEntity):
    """A yes/no value reported by the robot."""

    entity_description: Rs20BinarySensorDescription

    def __init__(
        self,
        coordinator: EzvizRs20ProCoordinator,
        description: Rs20BinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the reported value."""
        value = self.entity_description.value_fn(self.coordinator.data)
        return value if isinstance(value, bool) else None
