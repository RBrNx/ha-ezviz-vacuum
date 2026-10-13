"""Shared, Home Assistant independent helpers for reading robot payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

ROBOT_RESOURCE = "SweepingRobot"


def find_value(value: Any, keys: tuple[str, ...]) -> Any | None:
    """Return the first non-empty value stored under one of ``keys``.

    Keys are compared case-insensitively. The search is depth first, but the
    keys of the current mapping are checked before descending into children.
    """
    wanted = {key.casefold() for key in keys}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).casefold() in wanted and item not in (None, ""):
                return item
        for item in value.values():
            found = find_value(item, keys)
            if found not in (None, ""):
                return found
    elif isinstance(value, (list, tuple)):
        for item in value:
            found = find_value(item, keys)
            if found not in (None, ""):
                return found
    return None


def find_mapping(value: Any, key: str) -> Mapping[str, Any] | None:
    """Return the first nested mapping stored under ``key``."""
    if isinstance(value, Mapping):
        for current_key, item in value.items():
            if str(current_key).casefold() == key.casefold() and isinstance(
                item, Mapping
            ):
                return item
        for item in value.values():
            found = find_mapping(item, key)
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for item in value:
            found = find_mapping(item, key)
            if found is not None:
                return found
    return None


def find_scalar(value: Any, key: str) -> Any | None:
    """Return the first nested scalar (non container) stored under ``key``."""
    if isinstance(value, Mapping):
        for current_key, item in value.items():
            if str(current_key).casefold() == key.casefold() and not isinstance(
                item, (Mapping, list, tuple)
            ):
                return item
        for item in value.values():
            found = find_scalar(item, key)
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for item in value:
            found = find_scalar(item, key)
            if found is not None:
                return found
    return None


def robot_features(device: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return the ``SweepingRobot`` feature tree of a device payload."""
    if not isinstance(device, Mapping):
        return {}
    info = device.get("FEATURE_INFO")
    if not isinstance(info, Mapping):
        return {}
    for channel in info.values():
        if isinstance(channel, Mapping) and isinstance(
            channel.get(ROBOT_RESOURCE), Mapping
        ):
            return channel[ROBOT_RESOURCE]
    return {}


def feature(
    device: Mapping[str, Any] | None, domain: str, identifier: str
) -> Any | None:
    """Return one robot feature value addressed by its domain and identifier."""
    block = robot_features(device).get(domain)
    if not isinstance(block, Mapping):
        return None
    return block.get(identifier)
