"""Open-Meteo marine weather URL helpers.

Builds marine-weather API URLs dynamically from the same port/waypoint
coordinates used by the prototype route estimator.

The generated URLs are intended for non-commercial prototype use. Open-Meteo
supports comma-separated coordinates and returns one JSON structure per
coordinate. The service requires no API key for the public non-commercial tier.
"""

from __future__ import annotations

from itertools import product
from urllib.parse import urlencode

from models.optimization.route_sailing import (
    PORT_COORDINATES,
    WAYPOINTS,
    ORIGIN_ROUTE_OVERRIDES,
)

MARINE_API_BASE_URL = "https://marine-api.open-meteo.com/v1/marine"

MARINE_HOURLY_VARIABLES = (
    "wave_height",
    "wave_direction",
    "wave_period",
    "wind_wave_height",
    "wind_wave_direction",
    "wind_wave_period",
    "swell_wave_height",
    "swell_wave_direction",
    "swell_wave_period",
    "ocean_current_velocity",
    "ocean_current_direction",
    "sea_level_height_msl",
)

DEFAULT_FORECAST_DAYS = 7
DEFAULT_CELL_SELECTION = "sea"


def _coords(point_name: str) -> tuple[float, float]:
    """Resolve a port or waypoint to latitude/longitude."""
    if point_name in PORT_COORDINATES:
        return PORT_COORDINATES[point_name]
    if point_name in WAYPOINTS:
        return WAYPOINTS[point_name]
    raise ValueError(f"Unknown route point: {point_name}")


def get_route_points(origin_port: str, destination_port: str) -> list[str]:
    """Return the prototype route chain used for weather sampling."""
    if origin_port not in PORT_COORDINATES:
        raise ValueError(f"Unknown origin port: {origin_port}")
    if destination_port not in PORT_COORDINATES:
        raise ValueError(f"Unknown destination port: {destination_port}")

    waypoints = ORIGIN_ROUTE_OVERRIDES.get(origin_port, [])
    return [origin_port, *waypoints, destination_port]


def build_marine_weather_url(
    origin_port: str,
    destination_port: str,
    forecast_days: int = DEFAULT_FORECAST_DAYS,
) -> str:
    """Build one Open-Meteo Marine API URL for a complete route."""
    if not 1 <= forecast_days <= 8:
        raise ValueError("forecast_days must be between 1 and 8")

    route_points = get_route_points(origin_port, destination_port)
    coordinates = [_coords(point) for point in route_points]

    params = [
        ("latitude", ",".join(f"{lat:.5f}" for lat, _ in coordinates)),
        ("longitude", ",".join(f"{lon:.5f}" for _, lon in coordinates)),
        ("hourly", ",".join(MARINE_HOURLY_VARIABLES)),
        ("forecast_days", str(forecast_days)),
        ("cell_selection", DEFAULT_CELL_SELECTION),
        ("timezone", "GMT"),
    ]

    return f"{MARINE_API_BASE_URL}?{urlencode(params)}"


def build_all_route_urls(
    origin_ports: list[str],
    destination_ports: list[str],
    forecast_days: int = DEFAULT_FORECAST_DAYS,
) -> dict[str, str]:
    """Build URLs for every origin/destination combination."""
    return {
        f"{origin} -> {destination}": build_marine_weather_url(
            origin,
            destination,
            forecast_days=forecast_days,
        )
        for origin, destination in product(origin_ports, destination_ports)
    }


if __name__ == "__main__":
    origins = sorted(ORIGIN_ROUTE_OVERRIDES)
    destinations = [
        port for port in PORT_COORDINATES
        if port not in origins and port in {
            "Paradip",
            "Visakhapatnam",
            "Gangavaram",
            "Gopalpur",
            "Dhamra",
            "Sagar",
            "Sandheads",
            "Haldia",
        }
    ]

    routes = build_all_route_urls(origins, destinations)

    print(f"Generated {len(routes)} route URLs.")
    for route, url in routes.items():
        print(f"\n{route}\n{url}")
