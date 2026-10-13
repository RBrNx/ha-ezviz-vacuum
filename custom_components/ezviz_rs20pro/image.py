"""Cached, explicitly refreshed robot-camera image."""

from __future__ import annotations

from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import EzvizRs20ProCoordinator
from .entity import Rs20Entity


async def async_setup_entry(
    hass: Any,
    entry: ConfigEntry[EzvizRs20ProCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the cached snapshot image."""
    async_add_entities([EzvizRs20ProCameraImage(hass, entry.runtime_data)])


class EzvizRs20ProCameraImage(Rs20Entity, ImageEntity):
    """Last image captured after an explicit service call."""

    _attr_translation_key = "camera_snapshot"
    _attr_content_type = "image/jpeg"

    def __init__(self, hass: Any, coordinator: EzvizRs20ProCoordinator) -> None:
        ImageEntity.__init__(self, hass)
        Rs20Entity.__init__(self, coordinator, "camera_snapshot")

    @property
    def image_last_updated(self):
        """Return when the user last requested a snapshot."""
        return self.coordinator.camera_snapshot_updated

    async def async_image(self) -> bytes | None:
        """Return the cached image without opening the robot camera."""
        return self.coordinator.camera_snapshot
