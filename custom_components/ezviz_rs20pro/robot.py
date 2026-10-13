"""Interpretation of EZVIZ robot payloads (no Home Assistant imports)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import CLEAN_MODES
from .helpers import feature

# Preset room names are stored by the robot as pinyin codes.
ROOM_NAMES = {
    "#@ChuF#": "Kitchen",
    "#@KeT#": "Living Room",
    "#@WoS#": "Bedroom",
    "#@ZhuW#": "Master Bedroom",
    "#@CiW#": "Guest Bedroom",
    "#@ErTF#": "Kids Room",
    "#@XuanG#": "Entrance",
    "#@WeiYJ#": "Bathroom",
    "#@ZouL#": "Hallway",
    "#@CanT#": "Dining Room",
    "#@ShuF#": "Study",
    "#@YangT#": "Balcony",
    "#@YiMJ#": "Closet",
}


def task_data(task: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return the ``data`` block of a QueryCurrentTask response."""
    if isinstance(task, Mapping):
        data = task.get("data")
        if isinstance(data, Mapping):
            return data
    return {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _map_id(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def active_map_id(
    device: Mapping[str, Any] | None, task: Mapping[str, Any] | None = None
) -> int | None:
    """Return the map the robot is using.

    The live task reports ``currentMapID``. Without it, prefer a map marked
    ``inUse``, then any map that has rooms, then the first known map.
    """
    current = _map_id(task_data(task).get("currentMapID"))
    if current is not None and current > 0:
        return current
    maps = [
        item
        for item in _as_list(feature(device, "SweeperMapMgr", "MapBasicProperty"))
        if isinstance(item, Mapping) and _map_id(item.get("mapID")) is not None
    ]
    for item in maps:
        if item.get("inUse") is True:
            return _map_id(item["mapID"])
    for map_id in room_map_ids(device):
        return map_id
    if maps:
        return _map_id(maps[0]["mapID"])
    return current


def room_map_ids(device: Mapping[str, Any] | None) -> list[int]:
    """Return the IDs of maps that have room information."""
    info = feature(device, "SweeperMapMgr", "RegionBasicInfo")
    result = []
    for item in _as_list(info.get("mapList") if isinstance(info, Mapping) else None):
        if isinstance(item, Mapping) and (map_id := _map_id(item.get("mapID"))):
            result.append(map_id)
    return result


def map_name(device: Mapping[str, Any] | None, map_id: int | None) -> str:
    """Return the user-given map name, or ``Map N``."""
    for item in _as_list(feature(device, "SweeperMapMgr", "MapBasicProperty")):
        if (
            isinstance(item, Mapping)
            and _map_id(item.get("mapID")) == map_id
            and item.get("mapName")
        ):
            return str(item["mapName"])
    return f"Map {map_id}" if map_id is not None else "Map"


def room_name(raw_name: Any, room_id: Any) -> str:
    """Translate a robot room name; preset codes become English names."""
    name = str(raw_name or "").strip()
    if not name:
        return f"Room {room_id}"
    return ROOM_NAMES.get(name, name)


def rooms(
    device: Mapping[str, Any] | None, map_id: int | None
) -> list[tuple[str, str]]:
    """Return ``(room_id, name)`` for the rooms of ``map_id``."""
    info = feature(device, "SweeperMapMgr", "RegionBasicInfo")
    for item in _as_list(info.get("mapList") if isinstance(info, Mapping) else None):
        if not isinstance(item, Mapping) or _map_id(item.get("mapID")) != map_id:
            continue
        return [
            (str(region["ID"]), room_name(region.get("name"), region["ID"]))
            for region in _as_list(item.get("regionList"))
            if isinstance(region, Mapping)
            and region.get("regionType") == "room"
            and region.get("ID") is not None
        ]
    return []


def room_clean_configs(
    device: Mapping[str, Any] | None, map_id: int | None
) -> list[dict[str, Any]]:
    """Return the per-room cleaning settings of ``map_id``."""
    for item in _as_list(feature(device, "SweeperMapMgr", "RoomCustomCleanCfg")):
        if isinstance(item, Mapping) and _map_id(item.get("mapID")) == map_id:
            return [dict(room) for room in _as_list(item.get("room"))
                    if isinstance(room, Mapping)]
    return []


def clean_mode(device: Mapping[str, Any] | None) -> str | None:
    """Return the configured sweep/mop mode, if it is a known value."""
    mode = feature(device, "SweeperCleanTask", "SweepMopMode")
    return mode if mode in CLEAN_MODES else None


def device_details(device: Mapping[str, Any] | None) -> dict[str, str | None]:
    """Return model, name and firmware for the device registry."""
    info = device.get("deviceInfos") if isinstance(device, Mapping) else None
    info = info if isinstance(info, Mapping) else {}
    version = info.get("version")
    return {
        "model": "RS20 Pro",
        "name": "EZVIZ RS20 Pro",
        "sw_version": str(version) if version else None,
    }
