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


def _great_circle_nm(origin, destination):
    """Approximate great-circle distance in nautical miles."""
    lat1, lon1 = PORT_COORDINATES[origin]
    lat2, lon2 = PORT_COORDINATES[destination]

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


def estimate_sailing_days(
    origin_port: str,
    destination_port: str,
    speed_knots: float = DEFAULT_SPEED_KNOTS,
) -> float:
    """
    Estimate one-way sailing time for a port-to-port route.

    This is a prototype estimate based on great-circle distance,
    a configurable route factor, and average planning speed.
    It is not a live vessel schedule.
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

    distance_nm = _great_circle_nm(
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
