"""Zone and spot cleaning geometry (no Home Assistant imports).

``SweeperCleanTask/StartTempRegionClean`` takes rectangles in the same
coordinates as the map grid: cell ``(x, y)`` of the grid is point ``(x, y)``.
The map image draws that grid, so a point on the image converts to a robot
point with a fixed offset and scale (see :func:`calibration_points`).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from .mapdata import Grid
from .maprender import PADDING, SCALE

# The EZVIZ app sends a box of about 34 x 37 cells for a spot clean.
DEFAULT_SPOT_SIZE = 36
MAX_ZONES = 10

Zone = tuple[int, int, int, int]


def normalize_zone(zone: Sequence[Any]) -> Zone:
    """Return ``(left, top, right, bottom)`` from two opposite corners."""
    if len(zone) != 4:
        raise ValueError("A zone needs four numbers: x1, y1, x2, y2")
    try:
        x1, y1, x2, y2 = (round(float(value)) for value in zone)
    except (TypeError, ValueError) as err:
        raise ValueError("Zone coordinates must be numbers") from err
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    if left == right or top == bottom:
        raise ValueError("A zone must have a width and a height")
    return left, top, right, bottom


def normalize_zones(zones: Iterable[Sequence[Any]]) -> list[Zone]:
    """Validate a list of zones."""
    result = [normalize_zone(zone) for zone in zones]
    if not result:
        raise ValueError("No zone given")
    if len(result) > MAX_ZONES:
        raise ValueError(f"At most {MAX_ZONES} zones can be cleaned at once")
    return result


def spot_zone(x: float, y: float, size: float = DEFAULT_SPOT_SIZE) -> Zone:
    """Return a square zone of ``size`` cells centred on a point."""
    if size <= 0:
        raise ValueError("The spot size must be positive")
    half = size / 2
    return normalize_zone((x - half, y - half, x + half, y + half))


def temp_region_payload(
    map_id: int,
    zones: Iterable[Zone],
    *,
    fan_mode: str,
    water_quantity: str,
    clean_times: int,
) -> dict[str, Any]:
    """Build the body the EZVIZ app sends for a zone or spot clean."""
    return {
        "mapID": int(map_id),
        "tempRegion": [
            {
                "areaType": "rectangle",
                "area": {"ltx": left, "lty": top, "rbx": right, "rby": bottom},
                "fanMode": fan_mode,
                "waterQuantity": water_quantity,
                "cleanTimes": int(clean_times),
            }
            for left, top, right, bottom in zones
        ],
    }


def calibration_points(grid: Grid | None) -> list[dict[str, dict[str, float]]]:
    """Map image pixels to robot coordinates, for map cards.

    The format is the one the Xiaomi Vacuum Map Card reads from an attribute:
    three ``{"vacuum": {x, y}, "map": {x, y}}`` pairs. The SVG's intrinsic size
    is ``SCALE`` pixels per cell, starting ``PADDING`` cells before the grid.
    """
    if grid is None:
        return []
    min_x, min_y = grid.x - PADDING, grid.y - PADDING
    corners = (
        (grid.x, grid.y),
        (grid.x + grid.w, grid.y),
        (grid.x, grid.y + grid.h),
    )
    return [
        {
            "vacuum": {"x": x, "y": y},
            "map": {"x": (x - min_x) * SCALE, "y": (y - min_y) * SCALE},
        }
        for x, y in corners
    ]
