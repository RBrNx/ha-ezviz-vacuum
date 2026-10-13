"""Payload fragments captured from an RS20 Max (values trimmed)."""

from __future__ import annotations

import copy
from typing import Any

_ROBOT: dict[str, Any] = {
    "SweeperMapMgr": {
        "MapBasicProperty": [
            {"isFinishedClean": True, "isExplored": True, "inUse": False,
             "mapID": 2, "mapName": "Home.Ciubi"}
        ],
        "RegionBasicInfo": {
            "mapList": [
                {"mapID": 2, "regionList": [
                    {"regionType": "room", "name": "#@WoS#", "ID": 8},
                    {"regionType": "room", "name": "#@KeT#", "ID": 9},
                    {"regionType": "room", "name": "#@WeiYJ#", "ID": 10},
                    {"regionType": "room", "name": "#@ZouL#", "ID": 11},
                ]}
            ]
        },
        "RoomCustomCleanCfg": [
            {"mapID": 2, "room": [
                {"fanMode": "normal", "cleanTimes": 1, "regionType": "room",
                 "customRegionID": 0, "waterQuantity": "middle", "roomID": 8,
                 "order": 3},
                {"fanMode": "normal", "cleanTimes": 1, "regionType": "room",
                 "customRegionID": 0, "waterQuantity": "middle", "roomID": 9,
                 "order": 2},
            ]}
        ],
        "StdCleanCfg": [
            {"fanMode": "normal", "cleanTimes": 1, "cleanConfigType": "universal",
             "mapID": 0, "waterQuantity": "middle"},
            {"fanMode": "super", "cleanTimes": 1, "cleanConfigType": "universal",
             "mapID": 2, "waterQuantity": "middle"},
        ],
    },
    "SweeperCleanTask": {"SweepMopMode": "sweepThenMop"},
}

_DEVICE: dict[str, Any] = {
    "FEATURE_INFO": {"0": {"SweepingRobot": _ROBOT}},
    "deviceInfos": {
        "name": "RS20 Max",
        "deviceSerial": "BH3261413",
        "deviceType": "CS-RS20-MAX-TGA",
        "version": "V2.0.2417 build 250331",
        "deviceCategory": "SweepingRobot",
        "deviceSubCategory": "RS20 Max",
    },
}

_TASK: dict[str, Any] = {
    "meta": {"code": 200},
    "data": {"currentMapID": 2, "currentTask": "charging", "preTask": "standby",
             "exception": "", "exceptionCode": "", "battery": 100,
             "isOnBasestation": True, "inCharging": False},
}


def device() -> dict[str, Any]:
    """Return a fresh copy of the device payload."""
    return copy.deepcopy(_DEVICE)


def task(**overrides: Any) -> dict[str, Any]:
    """Return a fresh task payload with ``data`` overrides."""
    result = copy.deepcopy(_TASK)
    result["data"].update(overrides)
    return result
