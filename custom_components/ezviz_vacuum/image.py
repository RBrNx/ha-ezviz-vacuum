"""Robot map and the explicitly refreshed robot-camera image."""

from __future__ import annotations

from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import robot
from .coordinator import EzvizVacuumCoordinator
from .entity import RobotEntity


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizVacuumCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the cached snapshot image."""
    async_add_entities(
        [
            EzvizVacuumMapImage(hass, entry.runtime_data),
            EzvizVacuumCameraImage(hass, entry.runtime_data),
        ]
    )


class EzvizVacuumCameraImage(RobotEntity, ImageEntity):
    """Last image captured after an explicit service call."""

    _attr_translation_key = "camera_snapshot"
    _attr_content_type = "image/jpeg"

    def __init__(self, hass: Any, coordinator: EzvizVacuumCoordinator) -> None:
        ImageEntity.__init__(self, hass)
        RobotEntity.__init__(self, coordinator, "camera_snapshot")

    @property
    def image_last_updated(self):
        """Return when the user last requested a snapshot."""
        return self.coordinator.camera_snapshot_updated

    async def async_image(self) -> bytes | None:
        """Return the cached image without opening the robot camera."""
        return self.coordinator.camera_snapshot


class EzvizVacuumMapImage(RobotEntity, ImageEntity):
    """The robot's map with rooms, path, charger and robot position."""

    _attr_translation_key = "map"
    _attr_content_type = "image/svg+xml"
    # The vector geometry is large and the robot/path move constantly while
    # cleaning; keep it out of the recorder (clients read it live).
    _unrecorded_attributes = frozenset({"bounds", "rooms", "charger", "robot", "path"})

    def __init__(self, hass: Any, coordinator: EzvizVacuumCoordinator) -> None:
        ImageEntity.__init__(self, hass)
        RobotEntity.__init__(self, coordinator, "map")

    @property
    def image_last_updated(self):
        """Return when the map last changed."""
        return self.coordinator.map_image_updated

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the map layer versions and the last read error."""
        data = self.coordinator.data
        device, task = data.get("device"), data.get("task")
        map_id = robot.active_map_id(device, task)
        return {
            "map_id": map_id,
            "map_name": robot.map_name(device, map_id),
            "versions": robot.map_versions(task, map_id),
            "error": self.coordinator.map_error,
            **self.coordinator.map_geometry,
        }

    async def async_image(self) -> bytes | None:
        """Return the last drawn map."""
        return self.coordinator.map_image
