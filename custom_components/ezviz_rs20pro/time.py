"""Time entities for EZVIZ robot settings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any, Final

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20SettingEntity
from .settings import RestPlanSetting, Setting


@dataclass(frozen=True, kw_only=True)
class Rs20TimeDescription(TimeEntityDescription):
    """Describe a time-of-day robot setting (``HH:MM:SS``)."""

    setting: Setting
    entity_category: EntityCategory | None = EntityCategory.CONFIG


TIMES: Final[tuple[Rs20TimeDescription, ...]] = (
    Rs20TimeDescription(
        key="do_not_disturb_start",
        translation_key="do_not_disturb_start",
        icon="mdi:weather-night",
        setting=RestPlanSetting("startTime"),
    ),
    Rs20TimeDescription(
        key="do_not_disturb_end",
        translation_key="do_not_disturb_end",
        icon="mdi:weather-sunset-up",
        setting=RestPlanSetting("endTime"),
    ),
)


def parse_time(value: Any) -> time | None:
    """Parse the robot's ``HH:MM[:SS]`` text."""
    if not isinstance(value, str):
        return None
    try:
        parts = [int(part) for part in value.split(":")]
        return time(*parts[:3])
    except (TypeError, ValueError):
        return None


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the robot time settings."""
    coordinator = entry.runtime_data
    async_add_entities(
        Rs20SettingTime(coordinator, description.key, description)
        for description in TIMES
    )


class Rs20SettingTime(Rs20SettingEntity, TimeEntity):
    """A time-of-day robot setting."""

    entity_description: Rs20TimeDescription

    def __init__(
        self,
        coordinator: EzvizRs20ProCoordinator,
        key: str,
        description: Rs20TimeDescription,
        placeholders: dict[str, str] | None = None,
    ) -> None:
        super().__init__(coordinator, key, description.setting)
        self.entity_description = description
        if placeholders:
            self._attr_translation_placeholders = placeholders

    @property
    def native_value(self) -> time | None:
        """Return the reported time."""
        return parse_time(self.setting_value)

    async def async_set_value(self, value: time) -> None:
        """Send the new time to the robot."""
        await self.async_write_setting(value.strftime("%H:%M:00"))
