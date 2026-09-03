from typing import Dict


# Prototype daily vessel costs in USD/day.
# These are configurable assumptions, not market quotes.
DAILY_VESSEL_COST_USD = {
    "Handysize": 12_000,
    "Supramax": 16_000,
    "Panamax": 20_000,
    "Capesize": 28_000,
}


def get_daily_vessel_cost(vessel_type: str) -> float:
    """
    Return the assumed daily vessel cost for a vessel class.
    """

    if vessel_type not in DAILY_VESSEL_COST_USD:
        raise ValueError(
            f"Unknown vessel type: {vessel_type}"
        )

    return DAILY_VESSEL_COST_USD[vessel_type]


def calculate_port_cost(
    vessel_type: str,
    total_port_time_days: float,
) -> Dict:
    """
    Calculate vessel cost associated with port time.

    Formula:
        port_cost = total_port_time × daily vessel cost
    """

    if total_port_time_days < 0:
        raise ValueError(
            "total_port_time_days cannot be negative"
        )

    daily_cost = get_daily_vessel_cost(vessel_type)

    port_cost = (
        total_port_time_days
        * daily_cost
    )

    return {
        "vessel_type": vessel_type,
        "daily_vessel_cost_usd": daily_cost,
        "total_port_time_days": total_port_time_days,
        "estimated_port_cost_usd": round(port_cost, 2),
    }


def calculate_total_vessel_time_cost(
    vessel_type: str,
    sailing_days: float,
    total_port_time_days: float,
) -> Dict:
    """
    Calculate total vessel time cost.

    Formula:
        total time = sailing time + port time

        total cost =
            total time × daily vessel cost
    """

    if sailing_days < 0:
        raise ValueError(
            "sailing_days cannot be negative"
        )

    if total_port_time_days < 0:
        raise ValueError(
            "total_port_time_days cannot be negative"
        )

    daily_cost = get_daily_vessel_cost(vessel_type)

    total_time_days = (
        sailing_days
        + total_port_time_days
    )

    total_cost = (
        total_time_days
        * daily_cost
    )

    return {
        "vessel_type": vessel_type,
        "daily_vessel_cost_usd": daily_cost,
        "sailing_days": round(sailing_days, 2),
        "port_time_days": round(total_port_time_days, 2),
        "total_vessel_time_days": round(
            total_time_days,
            2,
        ),
        "estimated_vessel_time_cost_usd": round(
            total_cost,
            2,
        ),
    }


if __name__ == "__main__":

    result = calculate_total_vessel_time_cost(
        vessel_type="Supramax",
        sailing_days=3.0,
        total_port_time_days=4.95,
    )

    print("\nVessel Cost Calculation:")
    print("=" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")