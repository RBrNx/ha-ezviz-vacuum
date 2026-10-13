"""Tests for building complete setting writes."""

from __future__ import annotations

import unittest

from _loader import load
import fixtures

settings = load("settings")
helpers = load("helpers")


class FieldSettingTests(unittest.TestCase):
    """Object settings keep their other fields."""

    def test_read(self) -> None:
        setting = settings.FieldSetting("SweeperCleanTask", "CarpetCleanCfg", "turboClean")
        self.assertIs(setting.read(fixtures.device()), True)

    def test_write_keeps_companions_and_drops_timestamp(self) -> None:
        setting = settings.FieldSetting(
            "SweeperCleanTask", "DustCollectionCfg", "enabled"
        )
        domain, identifier, payload = setting.write(fixtures.device(), None, False)
        self.assertEqual((domain, identifier), ("SweeperCleanTask", "DustCollectionCfg"))
        self.assertEqual(payload, {"frequencyAfterClean": 1, "enabled": False})

    def test_write_does_not_touch_the_coordinator_data(self) -> None:
        device = fixtures.device()
        setting = settings.FieldSetting("SweeperCleanTask", "WashMopCfg", "interval")
        setting.write(device, None, 30)
        self.assertEqual(
            helpers.feature(device, "SweeperCleanTask", "WashMopCfg")["interval"], 15
        )

    def test_missing_feature_is_unavailable(self) -> None:
        setting = settings.FieldSetting("SweeperMgr", "Unknown", "enabled")
        self.assertFalse(setting.available(fixtures.device()))


class ScalarSettingTests(unittest.TestCase):
    """Plain values are sent as they are."""

    def test_read_and_write(self) -> None:
        setting = settings.ScalarSetting("SoundSetting", "PromptToneVolume")
        self.assertEqual(setting.read(fixtures.device()), 100)
        self.assertEqual(
            setting.write(fixtures.device(), None, 40),
            ("SoundSetting", "PromptToneVolume", 40),
        )


class MapCleanSettingTests(unittest.TestCase):
    """Whole-home settings belong to the active map."""

    def test_reads_active_map_not_default_entry(self) -> None:
        setting = settings.MapCleanSetting("fanMode")
        self.assertEqual(setting.read(fixtures.device(), fixtures.task()), "super")

    def test_write_changes_only_the_active_map(self) -> None:
        setting = settings.MapCleanSetting("fanMode")
        _, _, payload = setting.write(fixtures.device(), fixtures.task(), "quiet")
        by_map = {entry["mapID"]: entry for entry in payload}
        self.assertEqual(by_map[2]["fanMode"], "quiet")
        self.assertEqual(by_map[0]["fanMode"], "normal")
        self.assertEqual(by_map[2]["waterQuantity"], "middle")

    def test_write_adds_missing_map(self) -> None:
        setting = settings.MapCleanSetting("waterQuantity")
        _, _, payload = setting.write(
            fixtures.device(), fixtures.task(currentMapID=7), "high"
        )
        added = [entry for entry in payload if entry["mapID"] == 7]
        self.assertEqual(added[0]["waterQuantity"], "high")
        self.assertEqual(len(payload), 3)


class RoomCleanSettingTests(unittest.TestCase):
    """Per-room settings change one room of the active map."""

    def test_read(self) -> None:
        setting = settings.RoomCleanSetting(9, "fanMode")
        self.assertEqual(setting.read(fixtures.device(), fixtures.task()), "normal")

    def test_write_one_room(self) -> None:
        setting = settings.RoomCleanSetting(8, "cleanTimes")
        domain, identifier, payload = setting.write(
            fixtures.device(), fixtures.task(), 2
        )
        self.assertEqual((domain, identifier), ("SweeperMapMgr", "RoomCustomCleanCfg"))
        rooms = {room["roomID"]: room for room in payload[0]["room"]}
        self.assertEqual(rooms[8]["cleanTimes"], 2)
        self.assertEqual(rooms[9]["cleanTimes"], 1)
        self.assertEqual(rooms[8]["order"], 3)

    def test_unknown_room_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            settings.RoomCleanSetting(99, "fanMode").write(
                fixtures.device(), fixtures.task(), "quiet"
            )


class RestPlanSettingTests(unittest.TestCase):
    """Do-not-disturb keeps the rest of the period."""

    def test_read(self) -> None:
        self.assertEqual(
            settings.RestPlanSetting("endTime").read(fixtures.device()), "07:00:00"
        )

    def test_write(self) -> None:
        _, identifier, payload = settings.RestPlanSetting("startTime").write(
            fixtures.device(), None, "23:30:00"
        )
        self.assertEqual(identifier, "RestPlan")
        self.assertEqual(
            payload,
            {"plan": [{"startTime": "23:30:00", "ID": 0, "endTime": "07:00:00",
                       "enabled": True, "cleanContinue": False}]},
        )

    def test_write_creates_a_period(self) -> None:
        device = fixtures.device()
        device["FEATURE_INFO"]["0"]["SweepingRobot"]["SweeperMgr"]["RestPlan"] = {
            "plan": []
        }
        _, _, payload = settings.RestPlanSetting("enabled").write(device, None, True)
        self.assertTrue(payload["plan"][0]["enabled"])
        self.assertEqual(payload["plan"][0]["ID"], 0)


class ApplyWriteTests(unittest.TestCase):
    """Local updates mirror what was sent."""

    def test_apply_write_updates_a_copy(self) -> None:
        device = fixtures.device()
        setting = settings.FieldSetting("SweeperCleanTask", "WashMopCfg", "interval")
        updated = settings.apply_write(device, setting.write(device, None, 30))
        self.assertEqual(setting.read(updated), 30)
        self.assertEqual(setting.read(device), 15)
        self.assertIn(
            "ts", helpers.feature(updated, "SweeperCleanTask", "WashMopCfg")
        )

    def test_apply_scalar(self) -> None:
        device = fixtures.device()
        setting = settings.ScalarSetting("SweeperCleanTask", "SweepMopMode")
        updated = settings.apply_write(device, setting.write(device, None, "mop"))
        self.assertEqual(setting.read(updated), "mop")

    def test_every_setting_targets_an_allowed_feature(self) -> None:
        const = load("const")
        self.assertNotIn(("SweeperMgr", "CliffDetectionSwitch"), const.WRITABLE_FEATURES)


if __name__ == "__main__":
    unittest.main()
