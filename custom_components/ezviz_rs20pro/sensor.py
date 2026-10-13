"""Sensors for EZVIZ robot vacuums."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import re
from typing import Any, Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfArea, UnitOfTime
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20Entity
from .helpers import (
    feature,
    find_mapping as _find_mapping,
    find_scalar as _find_scalar,
)

Data = Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class Rs20SensorDescription(SensorEntityDescription):
    """Describe a value in the RS20 response."""

    source_key: str = ""
    remaining_percent: bool = False
    value_field: str | None = None
    value_fn: Callable[[Data], Any] | None = None
    attributes_fn: Callable[[Data], dict[str, Any] | None] | None = None


def _permanent(field: str) -> Callable[[Data], Any]:
    """Read a lifetime counter from InfoMgr/DeviceDescription."""

    def read(data: Data) -> Any:
        block = feature(data.get("device"), "InfoMgr", "DeviceDescription")
        basic = block.get("basic") if isinstance(block, Mapping) else None
        permanent = basic.get("permanent") if isinstance(basic, Mapping) else None
        return permanent.get(field) if isinstance(permanent, Mapping) else None

    return read


def _battery_cycles(data: Data) -> Any:
    block = feature(data.get("device"), "InfoMgr", "DeviceDescription")
    basic = block.get("basic") if isinstance(block, Mapping) else {}
    runtime = basic.get("runtime") if isinstance(basic, Mapping) else {}
    battery = runtime.get("bat") if isinstance(runtime, Mapping) else {}
    return battery.get("cycleCount") if isinstance(battery, Mapping) else None


SENSORS: Final = (
    Rs20SensorDescription(
        key="battery",
        translation_key="battery",
        source_key="SurplusPower",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    Rs20SensorDescription(
        key="total_clean_area",
        translation_key="total_clean_area",
        source_key="totalCleanArea",
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:texture-box",
    ),
    Rs20SensorDescription(
        key="total_clean_time",
        translation_key="total_clean_time",
        value_fn=_permanent("totalCleanTimeMin"),
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-outline",
    ),
    Rs20SensorDescription(
        key="total_clean_count",
        translation_key="total_clean_count",
        value_fn=_permanent("totalCleanCount"),
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    Rs20SensorDescription(
        key="total_dust_collections",
        translation_key="total_dust_collections",
        value_fn=_permanent("totalCollectDustCount"),
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:delete-sweep-outline",
    ),
    Rs20SensorDescription(
        key="total_mop_washes",
        translation_key="total_mop_washes",
        value_fn=_permanent("totalWashMopCount"),
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:washing-machine",
    ),
    Rs20SensorDescription(
        key="battery_cycles",
        translation_key="battery_cycles",
        value_fn=_battery_cycles,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-sync-outline",
    ),
    Rs20SensorDescription(
        key="main_brush",
        translation_key="main_brush",
        source_key="RotatingBrushWorkingTime",
        remaining_percent=True,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:brush",
    ),
    Rs20SensorDescription(
        key="side_brush",
        translation_key="side_brush",
        source_key="EdgeBrushWorkingTime",
        remaining_percent=True,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:brush-outline",
    ),
    Rs20SensorDescription(
        key="hepa_filter",
        translation_key="hepa_filter",
        source_key="HepaWorkingTime",
        remaining_percent=True,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:air-filter",
    ),
    Rs20SensorDescription(
        key="mop",
        translation_key="mop",
        source_key="MopWorkingTime",
        remaining_percent=True,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water",
    ),
    Rs20SensorDescription(
        key="dust_bag",
        translation_key="dust_bag",
        source_key="DustBagWorkingTime",
        remaining_percent=True,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:delete-variant",
    ),
    Rs20SensorDescription(
        key="sensors",
        translation_key="sensors",
        source_key="SensorWorkingTime",
        remaining_percent=True,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:radar",
    ),
    Rs20SensorDescription(
        key="cleaning_solution",
        translation_key="cleaning_solution",
        source_key="CleaningSolutionStatus",
        remaining_percent=True,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:bottle-tonic-outline",
    ),
    Rs20SensorDescription(
        key="station_mop_washing",
        translation_key="station_mop_washing",
        source_key="CleanMopStatus",
        value_field="status",
        icon="mdi:washing-machine",
    ),
    Rs20SensorDescription(
        key="station_mop_drying",
        translation_key="station_mop_drying",
        source_key="DryMopStatus",
        value_field="status",
        icon="mdi:hair-dryer-outline",
    ),
    Rs20SensorDescription(
        key="station_dust_collection",
        translation_key="station_dust_collection",
        source_key="DustCollectionStatus",
        value_field="status",
        icon="mdi:delete-sweep-outline",
    ),
    Rs20SensorDescription(
        key="station_water_tank_drain",
        translation_key="station_water_tank_drain",
        source_key="EmptyBaseStationWaterTankStatus",
        value_field="status",
        icon="mdi:water-sync",
    ),
    Rs20SensorDescription(
        key="station_plumbing_module",
        translation_key="station_plumbing_module",
        source_key="WaterInletAndOutletModule",
        value_field="installed",
        icon="mdi:pipe",
    ),
)


_STATUS_PREFIXES = ("clean_mop_", "dry_mop_", "collect_", "empty_")


def _normalize_station_value(value: Any) -> str | None:
    """Convert vendor station values to stable, translatable states."""
    if isinstance(value, bool):
        return "installed" if value else "not_installed"
    if value in (None, ""):
        return None
    normalized = re.sub(r"(?<!^)(?=[A-Z])", "_", str(value)).casefold()
    for prefix in _STATUS_PREFIXES:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    aliases = {
        "working": "running",
        "washing": "running",
        "drying": "running",
        "collecting": "running",
        "none": "idle",
        "stop": "idle",
        "stopped": "idle",
        "failed": "error",
        "fail": "error",
    }
    return aliases.get(normalized, normalized)

def _consumable_attributes(
    block: Mapping[str, Any] | None, hours: bool
) -> dict[str, Any] | None:
    """Return remaining and used life (hours for wear parts)."""
    if block is None:
        return None
    suffix = "_hours" if hours else ""
    return {
        f"remaining{suffix}": block.get("rest"),
        f"used{suffix}": block.get("used"),
    }


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RS20 Pro sensors."""
    async_add_entities(
        Rs20Sensor(entry.runtime_data, description) for description in SENSORS
    )


class Rs20Sensor(Rs20Entity, SensorEntity):
    """A sensor sourced from the RS20 feature report."""

    entity_description: Rs20SensorDescription

    def __init__(
        self,
        coordinator: EzvizRs20ProCoordinator,
        description: Rs20SensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> int | float | str | None:
        """Return the current value."""
        device = self.coordinator.data["device"]
        if self.entity_description.value_fn is not None:
            value = self.entity_description.value_fn(self.coordinator.data)
            if isinstance(value, bool) or value is None:
                return None
            return value
        if self.entity_description.value_field is not None:
            block = _find_mapping(device, self.entity_description.source_key)
            if block is None:
                return None
            return _normalize_station_value(
                block.get(self.entity_description.value_field)
            )
        if self.entity_description.remaining_percent:
            block = _find_mapping(device, self.entity_description.source_key)
            if block is None:
                return None
            try:
                rest = float(block["rest"])
                used = float(block["used"])
            except (KeyError, TypeError, ValueError):
                return None
            total = rest + used
            return round(rest * 100 / total) if total > 0 else 0

        raw = _find_scalar(device, self.entity_description.source_key)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        return int(value) if value.is_integer() else value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose extra details and the original vendor station state."""
        if self.entity_description.attributes_fn is not None:
            return self.entity_description.attributes_fn(self.coordinator.data)
        if self.entity_description.remaining_percent:
            return _consumable_attributes(
                _find_mapping(
                    self.coordinator.data["device"],
                    self.entity_description.source_key,
                ),
                self.entity_description.source_key.endswith("WorkingTime"),
            )
        if self.entity_description.value_field is None:
            return None
        block = _find_mapping(
            self.coordinator.data["device"], self.entity_description.source_key
        )
        if block is None:
            return None
        return {"raw_value": block.get(self.entity_description.value_field)}
