"""Tests for decoding map layers (synthetic data)."""

from __future__ import annotations

import base64
import gzip
import unittest

from _loader import load
import fixtures

mapdata = load("mapdata")
robot = load("robot")


def pack(text: str) -> str:
    return base64.b64encode(gzip.compress(text.encode())).decode()


class GridTests(unittest.TestCase):
    """me2: one character per cell, bit flags for the cell type."""

    def test_me2_runs(self) -> None:
        # 3 x 2 grid: row 0 floor floor wall, row 1 empty obstacle floor
        cells = chr(4) + chr(4) + chr(2) + chr(0) + chr(8) + chr(4)
        grid = mapdata.decode_grid(
            {"x": 10, "y": 20, "w": 3, "h": 2, "mapData": pack(cells),
             "extra": {"mapEncodeType": "me2/gzip/base64"}}
        )
        self.assertEqual(grid.runs["floor"], [(10, 20, 2), (12, 21, 1)])
        self.assertEqual(grid.runs["wall"], [(12, 20, 1)])
        self.assertEqual(grid.runs["obstacle"], [(11, 21, 1)])

    def test_legacy_rle(self) -> None:
        # 'S' = 18 = 0b010010 -> floor, floor; '(5)' repeats it
        grid = mapdata.decode_grid(
            {"x": 0, "y": 0, "w": 10, "h": 1, "mapData": "S(5)"}
        )
        self.assertEqual(grid.runs["floor"], [(0, 0, 10)])

    def test_bad_layer(self) -> None:
        self.assertIsNone(mapdata.decode_grid({"x": 0}))


class OutlineTests(unittest.TestCase):
    """Room outlines and paths are delta encoded when compressed."""

    def test_compressed_room_is_delta_encoded(self) -> None:
        rooms = mapdata.decode_rooms(
            {"room": [{"roomID": 8, "coordinate": pack("10,10;5,0;0,5;-5,0")}]}
        )
        self.assertEqual(rooms[8], [(10, 10), (15, 10), (15, 15), (10, 15)])

    def test_plain_room_is_absolute(self) -> None:
        rooms = mapdata.decode_rooms(
            {"room": [{"roomID": 9, "coordinate": "1,1;4,1;4,4"}]}
        )
        self.assertEqual(rooms[9], [(1, 1), (4, 1), (4, 4)])

    def test_path_segments_continue_deltas(self) -> None:
        path = mapdata.decode_path({"pathdata": pack("0,0;1,0|0,2;1,0")})
        self.assertEqual(path, [[(0, 0), (1, 0)], [(1, 2), (2, 2)]])

    def test_empty_path(self) -> None:
        self.assertEqual(mapdata.decode_path({"pathdata": ""}), [])

    def test_build_layers(self) -> None:
        layers = mapdata.build_layers(
            {"x": 0, "y": 0, "w": 1, "h": 1, "mapData": pack(chr(4)),
             "chargerX": 5, "chargerY": 6, "extra": {"chargerDegree": 179}},
            None,
            {"pathdata": "", "currentPosition": {"x": 5, "y": 6, "degree": -174}},
        )
        self.assertEqual(layers.charger, (5.0, 6.0))
        self.assertEqual(layers.charger_degree, 179.0)
        self.assertEqual(layers.robot, (5.0, 6.0))
        self.assertEqual(layers.robot_degree, -174.0)


class VersionTests(unittest.TestCase):
    def test_map_versions_from_task(self) -> None:
        self.assertEqual(
            robot.map_versions(fixtures.task(), 2),
            {"map": 6126, "region": 1359, "path": 204225},
        )
        self.assertEqual(robot.map_versions(fixtures.task(), 3), {})


if __name__ == "__main__":
    unittest.main()
