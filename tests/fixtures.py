"""Payload fragments captured from an RS20 Max (values trimmed)."""

from __future__ import annotations

import copy
from typing import Any

# gzip/base64 history blobs (two entries each).
_CLEAN = (
    "H4sIAK9mzmoC/72QQYsCIRiG/4p4dkUdtdFbMJc9BLF0iz1Y2e6AM8qMEUv031Nh2qK6dhKe98WX5ztB144RarA+wc8mvaJCAI7RDLEx0ca2swlCSj6IALTWjGkhMaEKlpoPT1pKV0oLhimvc2vrrOm/TP9TOvuDc1e68LsCx6O1YfVrEwhw2l/9hRJ2ftM6O18up8kp6P3Qmf/PmsNgYuv7HFUcVeKazAdrCqWYI6awzElnQhFmZwQmd/7KXQI6S+KaKMxr8spd5gsJqjnF6mb+ze5MIsYf3JM2ye783v37fAGvVzSNAgIAAA=="
)
_ABNORMAL = (
    "H4sIAK9mzmoC/6tWysksLlGyUoiuVspLzE0FspSe7Oh9OmfF0/m7nq+e+bSz9+nseU9bW58u2fhiy1IlHQWlvHygIhNDQyAzJbEktSQTosvIwMhM19BA18AoxNDIysjMysRSz9zAUqlWRwFhNMTQlw2znuxf+GL/vGd9S5/uaXq6YwfCXANzXOaahhhaWBmaWBlb6BmYGSnVxgIVluSXJOYAVRnVAgDk8e/0yQAAAA=="
)

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
    "SweeperCleanTask": {
        "SweepMopMode": "sweepThenMop",
        "CarpetCleanCfg": {"detection": True, "turboClean": True,
                           "allowPassageWhenObstructed": False,
                           "additionalClean": True,
                           "ts": "2026-10-13T19:53:49.438+02:00"},
        "DustCollectionCfg": {"frequencyAfterClean": 1, "enabled": True,
                              "ts": "1970-01-01T00:00:53.270+02:00"},
        "WashMopCfg": {"interval": 15, "type": "time",
                       "ts": "1970-01-01T00:00:53.275+02:00"},
        "DryMopDuration": {"duration": 270,
                           "ts": "1970-01-01T00:00:53.266+02:00"},
        "CleanPlan": {
            "Plan": [
                {"Action": {"cleanMode": "sweepThenMop", "mapID": 0,
                            "cleanRange": "full", "region": []},
                 "name": "", "invalid": False, "planID": 0,
                 "startTime": "10:00:00", "RepeatPeriod": [1, 2, 3, 4, 5, 6, 7],
                 "enabled": False}
            ],
            "ts": "2026-10-13T19:25:36.234+02:00",
        },
    },
    "SweeperMgr": {
        "RestPlan": {"plan": [{"startTime": "22:00:00", "ID": 0,
                               "endTime": "07:00:00", "enabled": True,
                               "cleanContinue": False}],
                     "ts": "1970-01-01T00:00:53.292+02:00"},
        "CliffDetectionSwitch": True,
        "PetModeSwitch": {"enabled": False,
                          "ts": "1970-01-01T00:00:53.288+02:00"},
    },
    "SoundSetting": {"PromptToneVolume": 100},
    "OperationDiagnosis": {
        "DeviceOperationParams": {
            "cleanHistory": {"encodeType": "gzip/base64", "content": _CLEAN},
            "abnormalHistory": {"encodeType": "gzip/base64", "content": _ABNORMAL},
        }
    },
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
