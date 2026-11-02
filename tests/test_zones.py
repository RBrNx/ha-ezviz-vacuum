"""Tests for zone and spot cleaning geometry."""

from __future__ import annotations

import unittest

from _loader import load

zones = load("zones")
mapdata = load("mapdata")
maprender = load("maprender")


class ZoneTests(unittest.TestCase):
    def test_corners_are_sorted(self) -> None:
        self.assertEqual(
            zones.normalize_zone([1288, 1034, 1254, 997]), (1254, 997, 1288, 1034)
        )

    def test_invalid_zones(self) -> None:
        for bad in ([1, 2, 3], [1, 2, 1, 5], ["a", 1, 2, 3]):
            with self.assertRaises(ValueError):
                zones.normalize_zone(bad)
        with self.assertRaises(ValueError):
            zones.normalize_zones([])
        with self.assertRaises(ValueError):
            zones.normalize_zones([[0, 0, 1, 1]] * (zones.MAX_ZONES + 1))

    def test_spot_is_centred_square(self) -> None:
        self.assertEqual(zones.spot_zone(1271, 1015, 36), (1253, 997, 1289, 1033))
        with self.assertRaises(ValueError):
            zones.spot_zone(0, 0, 0)

    def test_payload_matches_the_app(self) -> None:
        # Captured from the EZVIZ app (RE4, spot clean).
        self.assertEqual(
            zones.temp_region_payload(
                2,
                [(1254, 997, 1288, 1034)],
                fan_mode="strong",
                water_quantity="high",
                clean_times=2,
            ),
            {
                "mapID": 2,
                "tempRegion": [
                    {
                        "areaType": "rectangle",
                        "area": {"ltx": 1254, "lty": 997, "rbx": 1288, "rby": 1034},
                        "fanMode": "strong",
                        "waterQuantity": "high",
                        "cleanTimes": 2,
                    }
                ],
            },
        )

    def test_calibration_follows_the_svg(self) -> None:
        grid = mapdata.Grid(1138, 988, 396, 150)
        points = zones.calibration_points(grid)
        self.assertEqual(len(points), 3)
        pad, scale = maprender.PADDING, maprender.SCALE
        self.assertEqual(
            points[0],
            {
                "vacuum": {"x": 1138, "y": 988},
                "map": {"x": pad * scale, "y": pad * scale},
            },
        )
        self.assertEqual(points[1]["map"]["x"], (396 + pad) * scale)
        self.assertEqual(points[2]["map"]["y"], (150 + pad) * scale)
        self.assertEqual(zones.calibration_points(None), [])


if __name__ == "__main__":
    unittest.main()
