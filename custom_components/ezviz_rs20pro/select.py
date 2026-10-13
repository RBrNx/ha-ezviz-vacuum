"""Selects for EZVIZ robot cleaning settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20SettingEntity
from .settings import WATER_LEVELS, MapCleanSetting, Setting


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
)


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the robot setting selects."""
    coordinator = entry.runtime_data
    async_add_entities(
        Rs20SettingSelect(coordinator, description.key, description)
        for description in SELECTS
    )


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
