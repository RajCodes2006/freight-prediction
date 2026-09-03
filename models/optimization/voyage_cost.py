from typing import Dict


# Prototype freight-rate assumptions in USD/MT.
# These are temporary values for testing the optimization pipeline.
# They will later be replaced by the ML forecast.
PROTOTYPE_FREIGHT_RATE_USD_PER_MT = {
    "Handysize": 22.0,
    "Supramax": 20.0,
    "Panamax": 18.0,
    "Capesize": 16.0,
}


# Prototype additional voyage costs in USD.
# These are assumptions for development/testing.
PROTOTYPE_BUNKER_COST_USD = {
    "Handysize": 30_000,
    "Supramax": 40_000,
    "Panamax": 50_000,
    "Capesize": 65_000,
}


PROTOTYPE_PORT_CHARGES_USD = {
    "Handysize": 10_000,
    "Supramax": 15_000,
    "Panamax": 20_000,
    "Capesize": 30_000,
}


def get_freight_rate(vessel_type: str) -> float:
    """Return prototype freight rate in USD/MT."""

    if vessel_type not in PROTOTYPE_FREIGHT_RATE_USD_PER_MT:
        raise ValueError(
            f"Unknown vessel type: {vessel_type}"
        )

    return PROTOTYPE_FREIGHT_RATE_USD_PER_MT[vessel_type]


def get_bunker_cost(vessel_type: str) -> float:
    """Return prototype bunker/fuel cost."""

    if vessel_type not in PROTOTYPE_BUNKER_COST_USD:
        raise ValueError(
            f"Unknown vessel type: {vessel_type}"
        )

    return PROTOTYPE_BUNKER_COST_USD[vessel_type]


def get_port_charges(vessel_type: str) -> float:
    """Return prototype port charges."""

    if vessel_type not in PROTOTYPE_PORT_CHARGES_USD:
        raise ValueError(
            f"Unknown vessel type: {vessel_type}"
        )

    return PROTOTYPE_PORT_CHARGES_USD[vessel_type]


def calculate_freight_cost(
    cargo_quantity_mt: float,
    vessel_type: str,
) -> float:
    """
    Freight cost = cargo quantity × freight rate.
    """

    if cargo_quantity_mt <= 0:
        raise ValueError(
            "cargo_quantity_mt must be greater than 0"
        )

    rate = get_freight_rate(vessel_type)

    return cargo_quantity_mt * rate


def calculate_total_voyage_cost(
    cargo_quantity_mt: float,
    vessel_type: str,
    vessel_time_cost_usd: float,
) -> Dict:
    """
    Calculate total estimated voyage cost.

    Total voyage cost =
        Freight cost
        + Vessel time cost
        + Bunker cost
        + Port charges
    """

    if cargo_quantity_mt <= 0:
        raise ValueError(
            "cargo_quantity_mt must be greater than 0"
        )

    if vessel_time_cost_usd < 0:
        raise ValueError(
            "vessel_time_cost_usd cannot be negative"
        )

    freight_rate = get_freight_rate(vessel_type)
    bunker_cost = get_bunker_cost(vessel_type)
    port_charges = get_port_charges(vessel_type)

    freight_cost = calculate_freight_cost(
        cargo_quantity_mt=cargo_quantity_mt,
        vessel_type=vessel_type,
    )

    total_cost = (
        freight_cost
        + vessel_time_cost_usd
        + bunker_cost
        + port_charges
    )

    cost_per_mt = (
        total_cost / cargo_quantity_mt
    )

    return {
        "vessel_type": vessel_type,
        "cargo_quantity_mt": cargo_quantity_mt,
        "freight_rate_usd_per_mt": freight_rate,
        "freight_cost_usd": round(freight_cost, 2),
        "vessel_time_cost_usd": round(
            vessel_time_cost_usd,
            2,
        ),
        "bunker_cost_usd": round(
            bunker_cost,
            2,
        ),
        "port_charges_usd": round(
            port_charges,
            2,
        ),
        "total_voyage_cost_usd": round(
            total_cost,
            2,
        ),
        "total_cost_per_mt_usd": round(
            cost_per_mt,
            2,
        ),
    }


if __name__ == "__main__":

    # Example test:
    # 60,000 MT using a Supramax.
    result = calculate_total_voyage_cost(
        cargo_quantity_mt=60_000,
        vessel_type="Supramax",
        vessel_time_cost_usd=127_200,
    )

    print("\nVoyage Cost Calculation:")
    print("=" * 65)

    for key, value in result.items():
        print(f"{key}: {value}")