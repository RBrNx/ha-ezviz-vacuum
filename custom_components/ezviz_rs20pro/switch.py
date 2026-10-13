"""Switches for EZVIZ robot settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20SettingEntity
from .settings import FieldSetting, RestPlanSetting, Setting


@dataclass(frozen=True, kw_only=True)
class Rs20SwitchDescription(SwitchEntityDescription):
    """Describe a boolean robot setting."""

    setting: Setting
    entity_category: EntityCategory | None = EntityCategory.CONFIG


def _enabled(domain: str, identifier: str) -> FieldSetting:
    return FieldSetting(domain, identifier, "enabled")


SWITCHES: Final[tuple[Rs20SwitchDescription, ...]] = (
    Rs20SwitchDescription(
        key="station_child_lock",
        translation_key="station_child_lock",
        icon="mdi:lock-outline",
        setting=_enabled("SweeperBaseStationMgr", "ChildLockSwitch"),
    ),
    Rs20SwitchDescription(
        key="station_automatic_dust_collection",
        translation_key="station_automatic_dust_collection",
        icon="mdi:delete-sweep-outline",
        setting=_enabled("SweeperCleanTask", "DustCollectionCfg"),
    ),
    Rs20SwitchDescription(
        key="station_automatic_cleaning_solution",
        translation_key="station_automatic_cleaning_solution",
        icon="mdi:bottle-tonic-outline",
        setting=_enabled("SweeperCleanTask", "CleaningSolutionCfg"),
    ),
    Rs20SwitchDescription(
        key="station_rotating_brush_self_clean",
        translation_key="station_rotating_brush_self_clean",
        icon="mdi:brush-outline",
        setting=_enabled("SweeperCleanTask", "RotatingBrushSelfCleanSwitch"),
    ),
    Rs20SwitchDescription(
        key="do_not_disturb",
        translation_key="do_not_disturb",
        icon="mdi:sleep",
        setting=RestPlanSetting("enabled"),
    ),
    Rs20SwitchDescription(
        key="do_not_disturb_resume",
        translation_key="do_not_disturb_resume",
        icon="mdi:play-pause",
        setting=RestPlanSetting("cleanContinue"),
    ),
)


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the robot setting switches."""
    async_add_entities(
        Rs20SettingSwitch(entry.runtime_data, description)
        for description in SWITCHES
    )


class Rs20SettingSwitch(Rs20SettingEntity, SwitchEntity):
    """A boolean robot setting."""

    entity_description: Rs20SwitchDescription

    def __init__(
        self,
        coordinator: EzvizRs20ProCoordinator,
        description: Rs20SwitchDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.setting)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the reported setting."""
        value = self.setting_value
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the setting."""
        await self.async_write_setting(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the setting."""
        await self.async_write_setting(False)
