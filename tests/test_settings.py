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
