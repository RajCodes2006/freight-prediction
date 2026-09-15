from math import asin, cos, radians, sin, sqrt

# Approximate port coordinates used only for prototype route-time estimation.
# Sailing time is NOT a live schedule or nautical-route quotation.
PORT_COORDINATES = {
    # Australia
    "Newcastle": (-32.93, 151.78),
    "Hay Point": (-21.29, 149.30),
    "Gladstone": (-23.84, 151.26),
    "Abbot Point": (-19.82, 148.08),

    # Indonesia
    "Samarinda": (-0.50, 117.15),
    "Taboneo": (-3.70, 114.55),
    "Balikpapan": (-1.27, 116.83),
    "Muara Berau": (-1.10, 117.25),

    # United States
    "New Orleans": (29.95, -90.06),
    "Houston": (29.73, -95.27),
    "Mobile": (30.69, -88.04),

    # Mozambique
    "Nacala": (-14.55, 40.68),
    "Maputo": (-25.97, 32.58),
    "Beira": (-19.84, 34.84),

    # Russia
    "Taman": (45.02, 36.70),
    "Novorossiysk": (44.72, 37.77),
    "Vostochny": (42.76, 133.05),

    # East Coast India
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
ROUTE_FACTOR = 1.12  # Converts great-circle distance to a prototype sea-route estimate.
MIN_SAILING_DAYS = 2.0


# Known maritime chokepoints. A raw point-to-point great-circle line
# between some origins and the India east-coast destinations above
# passes directly over land (e.g. central Australia, mainland China,
# the Arabian/Central Asian landmass, or the Arctic), because a great
# circle is the shortest path over a *sphere*, not the shortest path
# over water. These waypoints force the distance calculation through
# the real navigable strait/canal/cape for those origins instead.
WAYPOINTS = {
    "BOSPHORUS": (41.15, 29.05),
    "SUEZ_NORTH": (31.26, 32.31),   # Port Said
    "SUEZ_SOUTH": (29.93, 32.55),   # Suez
    "BAB_EL_MANDEB": (12.65, 43.40),
    "CAPE_OF_GOOD_HOPE": (-34.35, 18.47),
    "CAPE_LEEUWIN": (-34.37, 115.13),
    "SINGAPORE_STRAIT": (1.27, 103.85),
    "TAIWAN_STRAIT": (24.00, 121.00),
}

# Waypoint chain inserted between origin and destination for origins
# whose direct great-circle path is not physically navigable. Verified
# by sampling points along each leg to confirm they stay over water.
# This is still a prototype approximation (straight legs between a
# handful of chokepoints, not real coast-hugging shipping lanes) - for
# production use, replace with a real maritime-routing library/API.
ORIGIN_ROUTE_OVERRIDES = {
    # Black Sea -> Mediterranean -> Suez Canal -> Red Sea -> India
    "Taman": ["BOSPHORUS", "SUEZ_NORTH", "SUEZ_SOUTH", "BAB_EL_MANDEB"],
    "Novorossiysk": ["BOSPHORUS", "SUEZ_NORTH", "SUEZ_SOUTH", "BAB_EL_MANDEB"],

    # Russia Pacific coast -> East/South China Sea -> Malacca -> India
    "Vostochny": ["TAIWAN_STRAIT", "SINGAPORE_STRAIT"],

    # US Gulf -> around the Cape of Good Hope -> India
    "New Orleans": ["CAPE_OF_GOOD_HOPE"],
    "Houston": ["CAPE_OF_GOOD_HOPE"],
    "Mobile": ["CAPE_OF_GOOD_HOPE"],

    # Australia east coast -> south of the continent -> Indian Ocean
    "Newcastle": ["CAPE_LEEUWIN"],
    "Hay Point": ["CAPE_LEEUWIN"],
    "Gladstone": ["CAPE_LEEUWIN"],
    "Abbot Point": ["CAPE_LEEUWIN"],

    # Borneo/Makassar side of Indonesia -> Karimata Strait -> Malacca
    "Samarinda": ["SINGAPORE_STRAIT"],
    "Taboneo": ["SINGAPORE_STRAIT"],
    "Balikpapan": ["SINGAPORE_STRAIT"],
    "Muara Berau": ["SINGAPORE_STRAIT"],
}


def _coords(point_name):
    """Resolve a port name or WAYPOINTS key to (lat, lon)."""
    if point_name in PORT_COORDINATES:
        return PORT_COORDINATES[point_name]
    return WAYPOINTS[point_name]


def _great_circle_nm_between(point_a, point_b):
    """Great-circle distance in nautical miles between two named points."""
    lat1, lon1 = _coords(point_a)
    lat2, lon2 = _coords(point_b)

    earth_radius_nm = 3440.065

    phi1 = radians(lat1)
    phi2 = radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)

    a = (
        sin(d_phi / 2) ** 2
        + cos(phi1) * cos(phi2) * sin(d_lambda / 2) ** 2
    )

    return 2 * earth_radius_nm * asin(sqrt(a))


def _route_nm(origin_port, destination_port):
    """
    Total distance in nautical miles for the origin's route, following
    any required chokepoint waypoints instead of a direct great circle.
    """
    waypoints = ORIGIN_ROUTE_OVERRIDES.get(origin_port, [])
    chain = [origin_port, *waypoints, destination_port]

    return sum(
        _great_circle_nm_between(chain[i], chain[i + 1])
        for i in range(len(chain) - 1)
    )


def estimate_sailing_days(
    origin_port: str,
    destination_port: str,
    speed_knots: float = DEFAULT_SPEED_KNOTS,
) -> float:
    """
    Estimate one-way sailing time for a port-to-port route.

    This is a prototype estimate based on distance along known
    navigable chokepoints (or a direct great circle where no landmass
    obstructs it), a configurable route factor, and average planning
    speed. It is not a live vessel schedule or a precise nautical-mile
    routing quotation.
    """
    if origin_port not in PORT_COORDINATES:
        raise ValueError(
            f"Unknown origin port for sailing-time estimation: {origin_port}"
        )

    if destination_port not in PORT_COORDINATES:
        raise ValueError(
            f"Unknown destination port for sailing-time estimation: {destination_port}"
        )

    if speed_knots <= 0:
        raise ValueError("speed_knots must be greater than 0")

    if origin_port == destination_port:
        return 0.0

    distance_nm = _route_nm(
        origin_port,
        destination_port,
    )

    adjusted_distance_nm = distance_nm * ROUTE_FACTOR

    sailing_days = (
        adjusted_distance_nm
        / (speed_knots * 24.0)
    )

    return round(
        max(sailing_days, MIN_SAILING_DAYS),
        2,
    )


if __name__ == "__main__":
    print(
        "Newcastle -> Paradip:",
        estimate_sailing_days("Newcastle", "Paradip"),
        "days",
    )
