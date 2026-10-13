"""Base-station switches for EZVIZ RS20 Pro."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20Entity
from .helpers import find_mapping as _find_mapping


@dataclass(frozen=True, kw_only=True)
class Rs20StationSwitchDescription(SwitchEntityDescription):
    """Describe a station feature switch."""

    domain_id: str
    identifier: str


STATION_SWITCHES: Final = (
    Rs20StationSwitchDescription(
        key="station_child_lock",
        translation_key="station_child_lock",
        icon="mdi:lock-outline",
        domain_id="SweeperBaseStationMgr",
        identifier="ChildLockSwitch",
    ),
    Rs20StationSwitchDescription(
        key="station_automatic_dust_collection",
        translation_key="station_automatic_dust_collection",
        icon="mdi:delete-sweep-outline",
        domain_id="SweeperCleanTask",
        identifier="DustCollectionCfg",
    ),
    Rs20StationSwitchDescription(
        key="station_automatic_cleaning_solution",
        translation_key="station_automatic_cleaning_solution",
        icon="mdi:bottle-tonic-outline",
        domain_id="SweeperCleanTask",
        identifier="CleaningSolutionCfg",
    ),
    Rs20StationSwitchDescription(
        key="station_rotating_brush_self_clean",
        translation_key="station_rotating_brush_self_clean",
        icon="mdi:brush-outline",
        domain_id="SweeperCleanTask",
        identifier="RotatingBrushSelfCleanSwitch",
    ),
)





async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RS20 Pro station switches."""
    async_add_entities(
        Rs20StationSwitch(entry.runtime_data, description)
        for description in STATION_SWITCHES
    )


class Rs20StationSwitch(Rs20Entity, SwitchEntity):
    """A configurable RS20 Pro station feature."""

    entity_description: Rs20StationSwitchDescription

    def __init__(
        self,
        coordinator: EzvizRs20ProCoordinator,
        description: Rs20StationSwitchDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the reported station setting."""
        block = _find_mapping(
            self.coordinator.data.get("device", {}),
            self.entity_description.identifier,
        )
        enabled = block.get("enabled") if block is not None else None
        return enabled if isinstance(enabled, bool) else None

    async def _async_set(self, enabled: bool) -> None:
        """Preserve companion fields while changing only enabled."""
        block = _find_mapping(
            self.coordinator.data.get("device", {}),
            self.entity_description.identifier,
        )
        value = {
            str(key): item
            for key, item in (block or {}).items()
            if key != "ts"
        }
        value["enabled"] = enabled
        await self.coordinator.async_set_station_feature(
            domain=self.entity_description.domain_id,
            identifier=self.entity_description.identifier,
            value=value,
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the station setting."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the station setting."""
        await self._async_set(False)
