from typing import Dict, List


# Prototype assumptions for development/testing.
# These are NOT real market contract quotes.

CONTRACT_DISCOUNTS = {
    1: 0.00,   # 1 month
    3: 0.02,   # 2% discount
    6: 0.04,   # 4% discount
    12: 0.06,  # 6% discount
}


def calculate_spot_cost(
    cargo_quantity_mt: float,
    voyages: int,
    spot_rate_usd_per_mt: float,
) -> float:
    """
    Calculate total cost when every voyage is booked
    separately at the spot rate.
    """

    if cargo_quantity_mt <= 0:
        raise ValueError(
            "cargo_quantity_mt must be greater than 0"
        )

    if voyages <= 0:
        raise ValueError(
            "voyages must be greater than 0"
        )

    if spot_rate_usd_per_mt < 0:
        raise ValueError(
            "spot_rate_usd_per_mt cannot be negative"
        )

    return (
        cargo_quantity_mt
        * voyages
        * spot_rate_usd_per_mt
    )


def calculate_contract_rate(
    spot_rate_usd_per_mt: float,
    contract_months: int,
) -> float:
    """
    Estimate a multiple-voyage contract rate using a
    prototype duration-based discount.
    """

    if spot_rate_usd_per_mt < 0:
        raise ValueError(
            "spot_rate_usd_per_mt cannot be negative"
        )

    if contract_months not in CONTRACT_DISCOUNTS:
        raise ValueError(
            "contract_months must be 1, 3, 6, or 12"
        )

    discount = CONTRACT_DISCOUNTS[
        contract_months
    ]

    return spot_rate_usd_per_mt * (1 - discount)


def calculate_contract_cost(
    cargo_quantity_mt: float,
    voyages: int,
    spot_rate_usd_per_mt: float,
    contract_months: int,
) -> Dict:
    """
    Calculate total cost under a multiple-voyage contract.
    """

    contract_rate = calculate_contract_rate(
        spot_rate_usd_per_mt=spot_rate_usd_per_mt,
        contract_months=contract_months,
    )

    total_contract_cost = (
        cargo_quantity_mt
        * voyages
        * contract_rate
    )

    total_spot_cost = calculate_spot_cost(
        cargo_quantity_mt=cargo_quantity_mt,
        voyages=voyages,
        spot_rate_usd_per_mt=spot_rate_usd_per_mt,
    )

    savings = (
        total_spot_cost
        - total_contract_cost
    )

    savings_percent = (
        savings / total_spot_cost * 100
        if total_spot_cost > 0
        else 0.0
    )

    return {
        "contract_months": contract_months,
        "spot_rate_usd_per_mt": round(
            spot_rate_usd_per_mt,
            2,
        ),
        "contract_rate_usd_per_mt": round(
            contract_rate,
            2,
        ),
        "total_spot_cost_usd": round(
            total_spot_cost,
            2,
        ),
        "total_contract_cost_usd": round(
            total_contract_cost,
            2,
        ),
        "estimated_savings_usd": round(
            savings,
            2,
        ),
        "estimated_savings_percent": round(
            savings_percent,
            2,
        ),
    }


def compare_contracts(
    cargo_quantity_mt: float,
    voyages: int,
    spot_rate_usd_per_mt: float,
    contract_durations: List[int] = None,
) -> Dict:
    """
    Compare spot booking with multiple-voyage contracts.
    """

    if contract_durations is None:
        contract_durations = [1, 3, 6, 12]

    results = []

    for months in contract_durations:

        result = calculate_contract_cost(
            cargo_quantity_mt=cargo_quantity_mt,
            voyages=voyages,
            spot_rate_usd_per_mt=spot_rate_usd_per_mt,
            contract_months=months,
        )

        results.append(result)

    best_contract = min(
        results,
        key=lambda x: x[
            "total_contract_cost_usd"
        ],
    )

    return {
        "cargo_quantity_mt": cargo_quantity_mt,
        "voyages": voyages,
        "spot_rate_usd_per_mt": spot_rate_usd_per_mt,
        "contracts": results,
        "best_contract_months": best_contract[
            "contract_months"
        ],
        "best_contract_cost_usd": best_contract[
            "total_contract_cost_usd"
        ],
    }


def recommend_contract(
    spot_rate_usd_per_mt: float,
    current_index_change_percent: float,
    minimum_savings_percent: float = 2.0,
) -> Dict:
    """
    Prototype contract recommendation.

    Rising market:
        Prefer fixing through a multiple-voyage contract.

    Falling market:
        Prefer spot / wait.

    Stable market:
        Use savings threshold.
    """

    if current_index_change_percent >= 5:
        action = "FIX_CONTRACT"
        reason = (
            "Market index is expected to rise significantly; "
            "locking a multiple-voyage contract can reduce "
            "exposure to future rate increases."
        )

    elif current_index_change_percent <= -5:
        action = "SPOT_OR_WAIT"
        reason = (
            "Market index is expected to decline significantly; "
            "avoid locking a long contract at the current rate."
        )

    else:
        action = "COMPARE"
        reason = (
            "Market movement is moderate; compare the contract "
            "discount with the expected market risk."
        )

    return {
        "action": action,
        "reason": reason,
        "market_change_percent": round(
            current_index_change_percent,
            2,
        ),
        "minimum_savings_percent": (
            minimum_savings_percent
        ),
    }


if __name__ == "__main__":

    # Example:
    # 60,000 MT cargo
    # 6 planned voyages
    # Prototype current spot rate = $18/MT
    result = compare_contracts(
        cargo_quantity_mt=60_000,
        voyages=6,
        spot_rate_usd_per_mt=18.0,
    )

    print("\nCONTRACT COMPARISON")
    print("=" * 70)

    print(
        f"Cargo quantity: "
        f"{result['cargo_quantity_mt']:,} MT"
    )

    print(
        f"Planned voyages: "
        f"{result['voyages']}"
    )

    print(
        f"Current spot rate: "
        f"${result['spot_rate_usd_per_mt']:.2f}/MT"
    )

    print("\nContract Options:")

    for contract in result["contracts"]:

        print("\n" + "-" * 70)

        print(
            f"Contract duration: "
            f"{contract['contract_months']} months"
        )

        print(
            f"Contract rate: "
            f"${contract['contract_rate_usd_per_mt']:.2f}/MT"
        )

        print(
            f"Spot cost: "
            f"${contract['total_spot_cost_usd']:,.2f}"
        )

        print(
            f"Contract cost: "
            f"${contract['total_contract_cost_usd']:,.2f}"
        )

        print(
            f"Savings: "
            f"${contract['estimated_savings_usd']:,.2f}"
        )

        print(
            f"Savings %: "
            f"{contract['estimated_savings_percent']:.2f}%"
        )

    print("\nBest Contract:")
    print(
        f"{result['best_contract_months']} months"
    )

    print(
        f"Cost: "
        f"${result['best_contract_cost_usd']:,.2f}"
    )

    recommendation = recommend_contract(
        spot_rate_usd_per_mt=18.0,
        current_index_change_percent=11.72,
    )

    print("\nStrategy Recommendation:")
    print(
        f"Action: "
        f"{recommendation['action']}"
    )

    print(
        f"Reason: "
        f"{recommendation['reason']}"
    )