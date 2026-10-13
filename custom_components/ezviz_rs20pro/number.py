"""Numbers for EZVIZ robot settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import robot
from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20SettingEntity
from .settings import FieldSetting, MapCleanSetting, RoomCleanSetting, Setting

MAX_PASSES = 3


@dataclass(frozen=True, kw_only=True)
class Rs20NumberDescription(NumberEntityDescription):
    """Describe a numeric robot setting."""

    setting: Setting
    entity_category: EntityCategory | None = EntityCategory.CONFIG
    mode: NumberMode = NumberMode.BOX
    native_step: float | None = 1


NUMBERS: Final[tuple[Rs20NumberDescription, ...]] = (
    Rs20NumberDescription(
        key="cleaning_passes",
        translation_key="cleaning_passes",
        icon="mdi:repeat",
        native_min_value=1,
        native_max_value=MAX_PASSES,
        setting=MapCleanSetting("cleanTimes"),
    ),
    Rs20NumberDescription(
        key="mop_wash_interval",
        translation_key="mop_wash_interval",
        icon="mdi:washing-machine",
        native_min_value=5,
        native_max_value=60,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        setting=FieldSetting("SweeperCleanTask", "WashMopCfg", "interval"),
    ),
    Rs20NumberDescription(
        key="mop_drying_time",
        translation_key="mop_drying_time",
        icon="mdi:sun-thermometer-outline",
        native_min_value=30,
        native_max_value=720,
        native_step=30,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        setting=FieldSetting("SweeperCleanTask", "DryMopDuration", "duration"),
    ),
    Rs20NumberDescription(
        key="dust_collection_frequency",
        translation_key="dust_collection_frequency",
        icon="mdi:delete-clock-outline",
        native_min_value=1,
        native_max_value=10,
        setting=FieldSetting(
            "SweeperCleanTask", "DustCollectionCfg", "frequencyAfterClean"
        ),
    ),
)


def room_numbers(device: Any, task: Any) -> list[tuple[str, Rs20NumberDescription, str]]:
    """Return ``(key, description, room name)`` for per-room passes."""
    map_id = robot.active_map_id(device, task)
    configured = {
        str(room.get("roomID")) for room in robot.room_clean_configs(device, map_id)
    }
    return [
        (
            f"room_{room_id}_cleaning_passes",
            Rs20NumberDescription(
                key=f"room_{room_id}_cleaning_passes",
                translation_key="room_cleaning_passes",
                icon="mdi:repeat",
                native_min_value=1,
                native_max_value=MAX_PASSES,
                setting=RoomCleanSetting(int(room_id), "cleanTimes"),
            ),
            name,
        )
        for room_id, name in robot.rooms(device, map_id)
        if room_id in configured
    ]


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the robot setting numbers."""
    coordinator = entry.runtime_data
    entities = [
        Rs20SettingNumber(coordinator, description.key, description)
        for description in NUMBERS
    ]
    entities.extend(
        Rs20SettingNumber(coordinator, key, description, {"room": name})
        for key, description, name in room_numbers(
            coordinator.data.get("device"), coordinator.data.get("task")
        )
    )
    async_add_entities(entities)


class Rs20SettingNumber(Rs20SettingEntity, NumberEntity):
    """A numeric robot setting."""

    entity_description: Rs20NumberDescription

    def __init__(
        self,
        coordinator: EzvizRs20ProCoordinator,
        key: str,
        description: Rs20NumberDescription,
        placeholders: dict[str, str] | None = None,
    ) -> None:
        super().__init__(coordinator, key, description.setting)
        self.entity_description = description
        if placeholders:
            self._attr_translation_placeholders = placeholders

    @property
    def native_value(self) -> float | None:
        """Return the reported value."""
        value = self.setting_value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return value

    async def async_set_native_value(self, value: float) -> None:
        """Send a new whole-number value to the robot."""
        await self.async_write_setting(int(value))
