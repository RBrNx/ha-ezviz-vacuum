"""Unit tests for the RS20 Pro request adapter."""

from __future__ import annotations

import base64
import gzip
import json
import unittest

from _loader import load

EzvizRs20ProApi = load("api").EzvizRs20ProApi


class FakeResponse:
    """Small requests.Response stand-in."""

    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.status_code = 200
        self.headers = {"Content-Type": "application/json"}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class FakeSession:
    """Capture PUT calls."""

    def __init__(self) -> None:
        self.headers = {"sessionId": "secret"}
        self.calls: list[dict] = []

    def put(self, url: str, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return FakeResponse({"meta": {"code": 200}, "data": {"ok": True}})

    def post(self, url: str, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return FakeResponse({"meta": {"code": 200}, "data": {"path": []}})


class FakeClient:
    """Minimum pyezviz-compatible client."""

    def __init__(self) -> None:
        self._session = FakeSession()
        self._token = {"api_url": "api.example.test"}
        self._timeout = 25


class ApiTests(unittest.TestCase):
    """Verify routes and JSON string bodies."""

    def setUp(self) -> None:
        self.client = FakeClient()
        self.api = EzvizRs20ProApi(self.client)

    def test_query_current_task(self) -> None:
        self.api.query_current_task("ab1234567")
        call = self.client._session.calls[0]
        self.assertTrue(call["url"].endswith(
            "/AB1234567/SweepingRobot/0/SweeperTaskMgr/QueryCurrentTask"
        ))
        self.assertEqual(call["data"], "{}")

    def test_clean_control_uses_json_string(self) -> None:
        self.api.clean_control("AB1234567", "return_charge")
        call = self.client._session.calls[0]
        self.assertTrue(call["url"].endswith(
            "/AB1234567/SweepingRobot/0/SweeperCleanTask/CleanControl"
        ))
        self.assertEqual(json.loads(call["data"]), "return_charge")

    def test_unknown_command_is_rejected_locally(self) -> None:
        with self.assertRaises(ValueError):
            self.api.clean_control("AB1234567", "factory_reset")
        self.assertEqual(self.client._session.calls, [])

    def test_station_feature_uses_feature_endpoint(self) -> None:
        self.api.set_station_feature(
            "ab1234567",
            domain="SweeperBaseStationMgr",
            identifier="ChildLockSwitch",
            value={"enabled": True},
        )
        call = self.client._session.calls[0]
        self.assertTrue(call["url"].endswith(
            "/AB1234567/SweepingRobot/0/SweeperBaseStationMgr/ChildLockSwitch"
        ))
        self.assertEqual(json.loads(call["data"]), {"enabled": True})

    def test_unknown_station_feature_is_rejected_locally(self) -> None:
        with self.assertRaises(ValueError):
            self.api.set_station_feature(
                "ab1234567",
                domain="SweeperBaseStationMgr",
                identifier="FactoryReset",
                value={"enabled": True},
            )
        self.assertEqual(self.client._session.calls, [])

    def test_map_path_candidates_are_read_only_posts(self) -> None:
        result = self.api.query_map_path_candidates("ab1234567", 5)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(self.client._session.calls), 2)
        for call in self.client._session.calls:
            self.assertEqual(
                call["data"],
                {"deviceSerial": "AB1234567", "mapId": "5"},
            )

    def test_start_region_clean_uses_native_room_action(self) -> None:
        room = {
            "fanMode": "normal",
            "cleanTimes": 1,
            "regionType": "room",
            "customRegionID": 0,
            "waterQuantity": "middle",
            "roomID": 8,
            "order": 1,
        }
        self.api.start_region_clean("ab1234567", map_id=5, rooms=[room])
        call = self.client._session.calls[0]
        self.assertTrue(call["url"].endswith(
            "/AB1234567/SweepingRobot/0/SweeperCleanTask/StartRegionClean"
        ))
        self.assertEqual(json.loads(call["data"])["region"], [room])

    def test_clean_mode_accepts_robot_enum(self) -> None:
        for mode in ("sweep", "mop", "sweepAndMop", "sweepThenMop"):
            self.api.set_clean_mode("ab1234567", mode)
        sent = [json.loads(call["data"]) for call in self.client._session.calls]
        self.assertEqual(sent, ["sweep", "mop", "sweepAndMop", "sweepThenMop"])
        with self.assertRaises(ValueError):
            self.api.set_clean_mode("ab1234567", "sweepMop")

    def test_decode_diagnostic_blob(self) -> None:
        content = base64.b64encode(gzip.compress(b'{"path":[1,2,3]}')).decode()
        result = self.api.decode_diagnostic_blob(
            {"encodeType": "gzip/base64", "content": content}
        )
        self.assertEqual(result, {"path": [1, 2, 3]})


if __name__ == "__main__":
    unittest.main()
