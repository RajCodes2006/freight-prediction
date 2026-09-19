"""Maritime route and sailing-time estimation.

Primary routing uses the ``searoute`` maritime network when installed. A
deterministic waypoint fallback is retained for environments where the
package cannot be installed or cannot return a usable route.

Port coordinates are stored as ``(latitude, longitude)``. The searoute
library expects ``(longitude, latitude)``.
"""

from __future__ import annotations

from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from typing import Any

try:
    import searoute as sr
    SEAROUTE_AVAILABLE = True
except ImportError:
    sr = None
    SEAROUTE_AVAILABLE = False

PORT_COORDINATES = {
    "Newcastle": (-32.93, 151.78),
    "Hay Point": (-21.29, 149.30),
    "Gladstone": (-23.84, 151.26),
    "Abbot Point": (-19.82, 148.08),
    "Samarinda": (-0.50, 117.15),
    "Taboneo": (-3.70, 114.55),
    "Balikpapan": (-1.27, 116.83),
    "Muara Berau": (-1.10, 117.25),
    "New Orleans": (29.95, -90.06),
    "Houston": (29.73, -95.27),
    "Mobile": (30.69, -88.04),
    "Nacala": (-14.55, 40.68),
    "Maputo": (-25.97, 32.58),
    "Beira": (-19.84, 34.84),
    "Taman": (45.02, 36.70),
    "Novorossiysk": (44.72, 37.77),
    "Vostochny": (42.76, 133.05),
    "Paradip": (20.27, 86.70),
    "Visakhapatnam": (17.69, 83.22),
    "Gangavaram": (17.63, 83.22),
    "Gopalpur": (19.26, 84.91),
    "Dhamra": (20.78, 86.98),
    "Sagar": (21.65, 88.05),
    "Sandheads": (21.08, 87.89),
    "Haldia": (22.03, 88.06),
}

DEFAULT_SPEED_KNOTS = 12.0
FALLBACK_ROUTE_FACTOR = 1.12
MIN_SAILING_DAYS = 2.0

# Used only when the searoute network is unavailable.
WAYPOINTS = {
    "BOSPHORUS": (41.15, 29.05),
    "DARDANELLES": (40.20, 26.40),
    "EAST_MED": (35.00, 25.00),
    "SUEZ_NORTH": (31.26, 32.31),
    "SUEZ_SOUTH": (29.93, 32.55),
    "BAB_EL_MANDEB": (12.65, 43.40),
    "CAPE_OF_GOOD_HOPE": (-34.35, 18.47),
    "AUSTRALIA_SOUTH_EAST_OFFSHORE": (-39.00, 153.00),
    "AUSTRALIA_SOUTH_OFFSHORE": (-40.00, 140.00),
    "CAPE_LEEUWIN": (-34.37, 115.13),
    "GULF_EXIT": (18.00, -75.00),
    "ATLANTIC_OFFSHORE": (8.00, -45.00),
    "EAST_CHINA_SEA_OFFSHORE": (30.00, 132.00),
    "TAIWAN_STRAIT": (24.30, 119.60),
    "KARIMATA_STRAIT": (-2.50, 108.50),
    "MALACCA_STRAIT": (2.50, 101.50),
    "SINGAPORE_STRAIT": (1.27, 103.85),
}

ORIGIN_ROUTE_OVERRIDES = {
    "Taman": ["BOSPHORUS", "DARDANELLES", "EAST_MED", "SUEZ_NORTH", "SUEZ_SOUTH", "BAB_EL_MANDEB"],
    "Novorossiysk": ["BOSPHORUS", "DARDANELLES", "EAST_MED", "SUEZ_NORTH", "SUEZ_SOUTH", "BAB_EL_MANDEB"],
    "Vostochny": ["EAST_CHINA_SEA_OFFSHORE", "TAIWAN_STRAIT", "SINGAPORE_STRAIT"],
    "New Orleans": ["GULF_EXIT", "ATLANTIC_OFFSHORE", "CAPE_OF_GOOD_HOPE"],
    "Houston": ["GULF_EXIT", "ATLANTIC_OFFSHORE", "CAPE_OF_GOOD_HOPE"],
    "Mobile": ["GULF_EXIT", "ATLANTIC_OFFSHORE", "CAPE_OF_GOOD_HOPE"],
    "Newcastle": ["AUSTRALIA_SOUTH_EAST_OFFSHORE", "AUSTRALIA_SOUTH_OFFSHORE", "CAPE_LEEUWIN"],
    "Hay Point": ["AUSTRALIA_SOUTH_EAST_OFFSHORE", "AUSTRALIA_SOUTH_OFFSHORE", "CAPE_LEEUWIN"],
    "Gladstone": ["AUSTRALIA_SOUTH_EAST_OFFSHORE", "AUSTRALIA_SOUTH_OFFSHORE", "CAPE_LEEUWIN"],
    "Abbot Point": ["AUSTRALIA_SOUTH_EAST_OFFSHORE", "AUSTRALIA_SOUTH_OFFSHORE", "CAPE_LEEUWIN"],
    "Samarinda": ["KARIMATA_STRAIT", "MALACCA_STRAIT"],
    "Taboneo": ["KARIMATA_STRAIT", "MALACCA_STRAIT"],
    "Balikpapan": ["KARIMATA_STRAIT", "MALACCA_STRAIT"],
    "Muara Berau": ["KARIMATA_STRAIT", "MALACCA_STRAIT"],
}

def _coords(point_name: str) -> tuple[float, float]:
    if point_name in PORT_COORDINATES:
        return PORT_COORDINATES[point_name]
    if point_name in WAYPOINTS:
        return WAYPOINTS[point_name]
    raise ValueError(f"Unknown route point: {point_name}")


def _great_circle_nm_between(point_a: str, point_b: str) -> float:
    lat1, lon1 = _coords(point_a)
    lat2, lon2 = _coords(point_b)
    earth_radius_nm = 3440.065
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2) ** 2
    return 2 * earth_radius_nm * asin(sqrt(a))


def _fallback_route(origin_port: str, destination_port: str) -> dict[str, Any]:
    waypoints = ORIGIN_ROUTE_OVERRIDES.get(origin_port, [])
    chain = [origin_port, *waypoints, destination_port]
    distance_nm = sum(
        _great_circle_nm_between(chain[index], chain[index + 1])
        for index in range(len(chain) - 1)
    )
    return {
        "distance_nm": round(distance_nm, 2),
        "coordinates": [_coords(point) for point in chain],
        "route_points": chain,
        "routing_source": "WAYPOINT_FALLBACK",
        "traversed_passages": [],
    }


def _route_attr(route: Any, key: str, default: Any = None) -> Any:
    properties = getattr(route, "properties", None)
    if properties is None and isinstance(route, dict):
        properties = route.get("properties")
    if isinstance(properties, dict):
        return properties.get(key, default)
    return default


def _route_geometry(route: Any) -> list[list[float]]:
    geometry = getattr(route, "geometry", None)
    if geometry is None and isinstance(route, dict):
        geometry = route.get("geometry")
    if isinstance(geometry, dict):
        coordinates = geometry.get("coordinates", [])
    else:
        coordinates = getattr(geometry, "coordinates", [])
    return [
        coordinate
        for coordinate in coordinates
        if isinstance(coordinate, (list, tuple)) and len(coordinate) >= 2
    ]


def _calculate_searoute(origin_port: str, destination_port: str) -> dict[str, Any] | None:
    if not SEAROUTE_AVAILABLE or sr is None:
        return None
    origin_lat, origin_lon = PORT_COORDINATES[origin_port]
    destination_lat, destination_lon = PORT_COORDINATES[destination_port]
    route = sr.searoute(
        [origin_lon, origin_lat],
        [destination_lon, destination_lat],
        units="naut",
        append_orig_dest=True,
        return_passages=True,
    )
    if route is None:
        return None
    distance_nm = _route_attr(route, "length")
    geometry = _route_geometry(route)
    if distance_nm is None or len(geometry) < 2:
        return None
    coordinates = [(float(point[1]), float(point[0])) for point in geometry]
    passages = _route_attr(route, "traversed_passages", [])
    if not isinstance(passages, list):
        passages = [passages] if passages else []
    return {
        "distance_nm": round(float(distance_nm), 2),
        "coordinates": coordinates,
        "route_points": [origin_port, destination_port],
        "routing_source": "SEAROUTE",
        "traversed_passages": passages,
    }


@lru_cache(maxsize=128)
def get_maritime_route(origin_port: str, destination_port: str) -> dict[str, Any]:
    if origin_port not in PORT_COORDINATES:
        raise ValueError(f"Unknown origin port for sailing-time estimation: {origin_port}")
    if destination_port not in PORT_COORDINATES:
        raise ValueError(f"Unknown destination port for sailing-time estimation: {destination_port}")
    if origin_port == destination_port:
        return {
            "distance_nm": 0.0,
            "coordinates": [PORT_COORDINATES[origin_port]],
            "route_points": [origin_port, destination_port],
            "routing_source": "SEAROUTE" if SEAROUTE_AVAILABLE else "WAYPOINT_FALLBACK",
            "traversed_passages": [],
        }
    try:
        route = _calculate_searoute(origin_port, destination_port)
        if route is not None:
            return route
    except Exception:
        pass
    return _fallback_route(origin_port, destination_port)


def get_route_distance_nm(origin_port: str, destination_port: str) -> float:
    return float(get_maritime_route(origin_port, destination_port)["distance_nm"])


def get_route_routing_source(origin_port: str, destination_port: str) -> str:
    return str(get_maritime_route(origin_port, destination_port)["routing_source"])


def _sample_route_coordinates(coordinates: list[tuple[float, float]], max_points: int = 24) -> list[tuple[float, float]]:
    if len(coordinates) <= max_points:
        return coordinates
    indices = {
        round(index * (len(coordinates) - 1) / (max_points - 1))
        for index in range(max_points)
    }
    return [coordinates[index] for index in sorted(indices)]


def get_route_coordinates(origin_port: str, destination_port: str, max_points: int = 24) -> list[tuple[float, float]]:
    if max_points < 2:
        raise ValueError("max_points must be at least 2")
    coordinates = get_maritime_route(origin_port, destination_port)["coordinates"]
    return _sample_route_coordinates(coordinates, max_points=max_points)


def get_route_points(origin_port: str, destination_port: str) -> list[str]:
    if origin_port not in PORT_COORDINATES:
        raise ValueError(f"Unknown origin port: {origin_port}")
    if destination_port not in PORT_COORDINATES:
        raise ValueError(f"Unknown destination port: {destination_port}")
    return [origin_port, *ORIGIN_ROUTE_OVERRIDES.get(origin_port, []), destination_port]


def estimate_sailing_days(origin_port: str, destination_port: str, speed_knots: float = DEFAULT_SPEED_KNOTS) -> float:
    if speed_knots <= 0:
        raise ValueError("speed_knots must be greater than 0")
    route = get_maritime_route(origin_port, destination_port)
    distance_nm = float(route["distance_nm"])
    if route["routing_source"] == "WAYPOINT_FALLBACK":
        distance_nm *= FALLBACK_ROUTE_FACTOR
    if distance_nm <= 0:
        return 0.0
    sailing_days = distance_nm / (speed_knots * 24.0)
    return round(max(sailing_days, MIN_SAILING_DAYS), 2)


if __name__ == "__main__":
    print("Newcastle -> Paradip:", estimate_sailing_days("Newcastle", "Paradip"), "days")
