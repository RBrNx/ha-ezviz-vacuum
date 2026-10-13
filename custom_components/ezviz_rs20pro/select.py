"""Selects for EZVIZ robot cleaning settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import robot
from .const import CLEAN_MODES
from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20SettingEntity
from .settings import (
    FAN_SPEEDS,
    ROOM_SETTING_MODES,
    WATER_LEVELS,
    FieldSetting,
    MapCleanSetting,
    RoomCleanSetting,
    ScalarSetting,
    Setting,
)


@dataclass(frozen=True, kw_only=True)
class Rs20SelectDescription(SelectEntityDescription):
    """Describe a robot setting with a fixed set of values."""

    setting: Setting
    entity_category: EntityCategory | None = EntityCategory.CONFIG


SELECTS: Final[tuple[Rs20SelectDescription, ...]] = (
    Rs20SelectDescription(
        key="water_level",
        translation_key="water_level",
        icon="mdi:water-outline",
        options=list(WATER_LEVELS),
        setting=MapCleanSetting("waterQuantity"),
    ),
    Rs20SelectDescription(
        key="cleaning_mode",
        translation_key="cleaning_mode",
        icon="mdi:broom",
        options=list(CLEAN_MODES),
        setting=ScalarSetting("SweeperCleanTask", "SweepMopMode"),
        entity_category=None,
    ),
    Rs20SelectDescription(
        key="room_settings",
        translation_key="room_settings",
        icon="mdi:floor-plan",
        options=list(ROOM_SETTING_MODES),
        setting=MapCleanSetting("cleanConfigType"),
    ),
    Rs20SelectDescription(
        key="mop_wash_trigger",
        translation_key="mop_wash_trigger",
        icon="mdi:washing-machine",
        options=["time", "region"],
        setting=FieldSetting("SweeperCleanTask", "WashMopCfg", "type"),
    ),
)


def room_selects(
    device: Any, task: Any
) -> list[tuple[str, Rs20SelectDescription, str]]:
    """Return ``(key, description, room name)`` for every room of the active map."""
    map_id = robot.active_map_id(device, task)
    configured = {
        str(room.get("roomID")) for room in robot.room_clean_configs(device, map_id)
    }
    result = []
    for room_id, name in robot.rooms(device, map_id):
        if room_id not in configured:
            continue
        for field, suffix, options, icon in (
            ("fanMode", "suction", FAN_SPEEDS, "mdi:fan"),
            ("waterQuantity", "water_level", WATER_LEVELS, "mdi:water-outline"),
        ):
            description = Rs20SelectDescription(
                key=f"room_{room_id}_{suffix}",
                translation_key=f"room_{suffix}",
                icon=icon,
                options=list(options),
                setting=RoomCleanSetting(int(room_id), field),
            )
            result.append((description.key, description, name))
    return result


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the robot setting selects."""
    coordinator = entry.runtime_data
    entities = [
        Rs20SettingSelect(coordinator, description.key, description)
        for description in SELECTS
    ]
    # Rooms are read once; reload the integration after editing the map.
    entities.extend(
        Rs20SettingSelect(coordinator, key, description, {"room": name})
        for key, description, name in room_selects(
            coordinator.data.get("device"), coordinator.data.get("task")
        )
    )
    async_add_entities(entities)


class Rs20SettingSelect(Rs20SettingEntity, SelectEntity):
    """A robot setting with a fixed set of values."""

    entity_description: Rs20SelectDescription

    def __init__(
        self,
        coordinator: EzvizRs20ProCoordinator,
        key: str,
        description: Rs20SelectDescription,
        placeholders: dict[str, str] | None = None,
    ) -> None:
        super().__init__(coordinator, key, description.setting)
        self.entity_description = description
        if placeholders:
            self._attr_translation_placeholders = placeholders

    @property
    def current_option(self) -> str | None:
        """Return the reported value when it is a known option."""
        value = self.setting_value
        return value if value in self.options else None

    async def async_select_option(self, option: str) -> None:
        """Send the chosen value to the robot."""
        await self.async_write_setting(option)
