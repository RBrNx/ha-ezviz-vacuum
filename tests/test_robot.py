"""Tests for payload interpretation in robot.py."""

from __future__ import annotations

import unittest

import fixtures
from _loader import load

robot = load("robot")


class MapTests(unittest.TestCase):
    """Active map, rooms and room settings."""

    def test_active_map_comes_from_live_task(self) -> None:
        self.assertEqual(robot.active_map_id(fixtures.device(), fixtures.task()), 2)

    def test_active_map_without_task_skips_settings_only_map_zero(self) -> None:
        # StdCleanCfg also lists map 0, which is not a real map.
        self.assertEqual(robot.active_map_id(fixtures.device(), None), 2)

    def test_map_name_and_fallback(self) -> None:
        device = fixtures.device()
        self.assertEqual(robot.map_name(device, 2), "Home.Ciubi")
        self.assertEqual(robot.map_name(device, 7), "Map 7")

    def test_rooms_are_translated(self) -> None:
        self.assertEqual(
            robot.rooms(fixtures.device(), 2),
            [("8", "Bedroom"), ("9", "Living Room"), ("10", "Bathroom"),
             ("11", "Hallway")],
        )
        self.assertEqual(robot.rooms(fixtures.device(), 3), [])

    def test_custom_room_names_are_kept(self) -> None:
        self.assertEqual(robot.room_name("Office", 4), "Office")
        self.assertEqual(robot.room_name("", 4), "Room 4")

    def test_room_clean_configs_for_map(self) -> None:
        configs = robot.room_clean_configs(fixtures.device(), 2)
        self.assertEqual([room["roomID"] for room in configs], [8, 9])
        self.assertEqual(robot.room_clean_configs(fixtures.device(), 0), [])


if __name__ == "__main__":
    unittest.main()
