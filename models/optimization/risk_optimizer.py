from typing import Dict, List


def calculate_rate_scenarios(
    current_rate_usd_per_mt: float,
    forecast_change_percent: float,
) -> Dict:
    """
    Create simple future freight-rate scenarios from the
    current rate and the forecasted market movement.

    This is a prototype risk model.
    """

    if current_rate_usd_per_mt <= 0:
        raise ValueError(
            "current_rate_usd_per_mt must be greater than 0"
        )

    # Central forecast
    forecast_rate = (
        current_rate_usd_per_mt
        * (1 + forecast_change_percent / 100)
    )

    # Downside scenario:
    # market falls 10 percentage points relative to current rate
    downside_rate = current_rate_usd_per_mt * 0.90

    # Upside scenario:
    # market rises another 10 percentage points relative to current rate
    upside_rate = current_rate_usd_per_mt * 1.10

    return {
        "current_rate_usd_per_mt": round(
            current_rate_usd_per_mt,
            2,
        ),
        "forecast_rate_usd_per_mt": round(
            forecast_rate,
            2,
        ),
        "downside_rate_usd_per_mt": round(
            downside_rate,
            2,
        ),
        "upside_rate_usd_per_mt": round(
            upside_rate,
            2,
        ),
    }


def calculate_spot_scenario_cost(
    cargo_quantity_mt: float,
    voyages: int,
    rate_usd_per_mt: float,
) -> float:
    """
    Total cost if every voyage is booked at the future rate.
    """

    return (
        cargo_quantity_mt
        * voyages
        * rate_usd_per_mt
    )


def calculate_contract_scenario_cost(
    cargo_quantity_mt: float,
    voyages: int,
    contract_rate_usd_per_mt: float,
) -> float:
    """
    Total cost of a fixed-rate multiple-voyage contract.
    """

    return (
        cargo_quantity_mt
        * voyages
        * contract_rate_usd_per_mt
    )


def calculate_risk_exposure(
    spot_upside_cost_usd: float,
    contract_cost_usd: float,
) -> float:
    """
    Positive value means the contract protects against
    higher future spot rates.

    Negative value means the contract is more expensive
    than the upside scenario.
    """

    return (
        spot_upside_cost_usd
        - contract_cost_usd
    )


def calculate_risk_adjusted_cost(
    contract_cost_usd: float,
    downside_spot_cost_usd: float,
    upside_spot_cost_usd: float,
    downside_probability: float = 0.25,
    central_probability: float = 0.50,
    upside_probability: float = 0.25,
) -> float:
    """
    Calculate an expected risk-adjusted cost.

    For a contract:
        cost is fixed in every scenario.

    For spot:
        cost varies with the future market.

    The probabilities are prototype assumptions.
    """

    total_probability = (
        downside_probability
        + central_probability
        + upside_probability
    )

    if abs(total_probability - 1.0) > 0.0001:
        raise ValueError(
            "Scenario probabilities must sum to 1.0"
        )

    expected_spot_cost = (
        downside_probability
        * downside_spot_cost_usd
        +
        central_probability
        * contract_cost_usd
        +
        upside_probability
        * upside_spot_cost_usd
    )

    return expected_spot_cost


def evaluate_contract_risk(
    cargo_quantity_mt: float,
    voyages: int,
    current_rate_usd_per_mt: float,
    forecast_change_percent: float,
    contract_rate_usd_per_mt: float,
) -> Dict:
    """
    Compare a fixed-rate contract against future spot
    scenarios and calculate risk-adjusted economics.
    """

    scenarios = calculate_rate_scenarios(
        current_rate_usd_per_mt=current_rate_usd_per_mt,
        forecast_change_percent=forecast_change_percent,
    )

    current_rate = scenarios[
        "current_rate_usd_per_mt"
    ]

    forecast_rate = scenarios[
        "forecast_rate_usd_per_mt"
    ]

    downside_rate = scenarios[
        "downside_rate_usd_per_mt"
    ]

    upside_rate = scenarios[
        "upside_rate_usd_per_mt"
    ]

    current_spot_cost = calculate_spot_scenario_cost(
        cargo_quantity_mt=cargo_quantity_mt,
        voyages=voyages,
        rate_usd_per_mt=current_rate,
    )

    forecast_spot_cost = calculate_spot_scenario_cost(
        cargo_quantity_mt=cargo_quantity_mt,
        voyages=voyages,
        rate_usd_per_mt=forecast_rate,
    )

    downside_spot_cost = calculate_spot_scenario_cost(
        cargo_quantity_mt=cargo_quantity_mt,
        voyages=voyages,
        rate_usd_per_mt=downside_rate,
    )

    upside_spot_cost = calculate_spot_scenario_cost(
        cargo_quantity_mt=cargo_quantity_mt,
        voyages=voyages,
        rate_usd_per_mt=upside_rate,
    )

    contract_cost = calculate_contract_scenario_cost(
        cargo_quantity_mt=cargo_quantity_mt,
        voyages=voyages,
        contract_rate_usd_per_mt=contract_rate_usd_per_mt,
    )

    protection_value = calculate_risk_exposure(
        spot_upside_cost_usd=upside_spot_cost,
        contract_cost_usd=contract_cost,
    )

    expected_spot_cost = (
        0.25 * downside_spot_cost
        + 0.50 * forecast_spot_cost
        + 0.25 * upside_spot_cost
    )

    expected_savings_from_contract = (
        expected_spot_cost
        - contract_cost
    )

    expected_savings_percent = (
        expected_savings_from_contract
        / expected_spot_cost
        * 100
        if expected_spot_cost > 0
        else 0.0
    )

    return {
        "current_rate_usd_per_mt": round(
            current_rate,
            2,
        ),
        "forecast_rate_usd_per_mt": round(
            forecast_rate,
            2,
        ),
        "downside_rate_usd_per_mt": round(
            downside_rate,
            2,
        ),
        "upside_rate_usd_per_mt": round(
            upside_rate,
            2,
        ),
        "current_spot_cost_usd": round(
            current_spot_cost,
            2,
        ),
        "forecast_spot_cost_usd": round(
            forecast_spot_cost,
            2,
        ),
        "downside_spot_cost_usd": round(
            downside_spot_cost,
            2,
        ),
        "upside_spot_cost_usd": round(
            upside_spot_cost,
            2,
        ),
        "contract_rate_usd_per_mt": round(
            contract_rate_usd_per_mt,
            2,
        ),
        "contract_cost_usd": round(
            contract_cost,
            2,
        ),
        "protection_value_usd": round(
            protection_value,
            2,
        ),
        "expected_spot_cost_usd": round(
            expected_spot_cost,
            2,
        ),
        "expected_savings_from_contract_usd": round(
            expected_savings_from_contract,
            2,
        ),
        "expected_savings_percent": round(
            expected_savings_percent,
            2,
        ),
    }


def recommend_risk_strategy(
    forecast_change_percent: float,
    expected_savings_from_contract_usd: float,
) -> Dict:
    """
    Recommend a strategy using both market direction
    and expected economic benefit.

    Strongly rising market + positive contract value:
        FIX_CONTRACT

    Strongly falling market:
        SPOT_OR_WAIT

    Otherwise:
        MONITOR
    """

    if (
        forecast_change_percent >= 5
        and expected_savings_from_contract_usd > 0
    ):
        action = "FIX_CONTRACT"

        reason = (
            "The market is forecast to rise and the fixed-rate "
            "contract has positive expected economic value."
        )

    elif forecast_change_percent <= -5:
        action = "SPOT_OR_WAIT"

        reason = (
            "The market is forecast to decline, so locking a "
            "long-term contract may increase expected cost."
        )

    elif expected_savings_from_contract_usd > 0:
        action = "CONSIDER_CONTRACT"

        reason = (
            "The contract provides positive expected savings, "
            "but the forecast does not show a strong market move."
        )

    else:
        action = "MONITOR"

        reason = (
            "Neither the market forecast nor the contract "
            "economics provide a strong reason to fix immediately."
        )

    return {
        "action": action,
        "reason": reason,
    }


if __name__ == "__main__":

    result = evaluate_contract_risk(
        cargo_quantity_mt=60_000,
        voyages=6,
        current_rate_usd_per_mt=18.0,
        forecast_change_percent=11.72,
        contract_rate_usd_per_mt=17.64,
    )

    print("\nRISK-ADJUSTED CONTRACT ANALYSIS")
    print("=" * 70)

    for key, value in result.items():
        print(f"{key}: {value}")

    recommendation = recommend_risk_strategy(
        forecast_change_percent=11.72,
        expected_savings_from_contract_usd=(
            result[
                "expected_savings_from_contract_usd"
            ]
        ),
    )

    print("\nStrategy Recommendation:")
    print(
        f"Action: {recommendation['action']}"
    )
    print(
        f"Reason: {recommendation['reason']}"
    )