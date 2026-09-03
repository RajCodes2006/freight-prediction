from typing import Dict, Optional

from models.inference.predict import predict
from models.optimization.vessel_optimizer import optimize_vessel
from models.optimization.voyage_cost import calculate_total_voyage_cost


VESSEL_TO_MODEL_CLASS = {
    "Handysize": "HSI",
    "Supramax": "SI",
    "Panamax": "PI",
    "Capesize": "CI",
}


def calculate_action(change_percent: float) -> str:
    """
    Prototype chartering decision.

    >= +5%  -> FIX_NOW
    <= -5%  -> WAIT
    else    -> MONITOR
    """

    if change_percent >= 5:
        return "FIX_NOW"

    if change_percent <= -5:
        return "WAIT"

    return "MONITOR"


def get_forecast_for_horizon(
    vessel_type: str,
    horizon_days: int,
) -> Optional[Dict]:
    """
    Get the existing ML forecast for one vessel class
    and one forecast horizon.
    """

    if vessel_type not in VESSEL_TO_MODEL_CLASS:
        raise ValueError(
            f"Unknown vessel type: {vessel_type}"
        )

    model_class = VESSEL_TO_MODEL_CLASS[vessel_type]

    # Use the existing prediction engine.
    return predict(
        vessel_type=model_class,
        horizon_days=horizon_days,
    )


def build_chartering_strategy(
    cargo_quantity_mt: float,
    origin_port: str,
    destination_port: str,
    sailing_days: float = 3.0,
    loading_queue_days: float = 1.0,
    discharge_queue_days: float = 1.5,
    verified_only: bool = False,
) -> Dict:
    """
    Build a prototype chartering strategy.

    Combines:
        - vessel feasibility
        - port handling time
        - idle time
        - vessel-time cost
        - voyage cost
        - ML market-index forecast
        - FIX_NOW / WAIT / MONITOR signal
    """

    # ------------------------------------------------------
    # 1. Vessel optimization
    # ------------------------------------------------------

    vessel_result = optimize_vessel(
        cargo_quantity_mt=cargo_quantity_mt,
        origin_port=origin_port,
        destination_port=destination_port,
        sailing_days=sailing_days,
        verified_only=verified_only,
        loading_queue_days=loading_queue_days,
        discharge_queue_days=discharge_queue_days,
    )

    candidates = []

    # ------------------------------------------------------
    # 2. Evaluate each vessel
    # ------------------------------------------------------

    for candidate in vessel_result["candidates"]:

        candidate_result = dict(candidate)

        if not candidate.get("feasible"):
            candidates.append(candidate_result)
            continue

        vessel_type = candidate["vessel_type"]

        model_class = VESSEL_TO_MODEL_CLASS[
            vessel_type
        ]

        # --------------------------------------------------
        # 3. ML forecasts: 7 / 30 / 60 / 90 days
        # --------------------------------------------------

        forecast_results = {}

        for horizon in [7, 30, 60, 90]:

            try:

                forecast = get_forecast_for_horizon(
                    vessel_type=vessel_type,
                    horizon_days=horizon,
                )

                change_percent = forecast[
                    "change_percent"
                ]

                action = calculate_action(
                    change_percent
                )

                forecast_results[str(horizon)] = {
                    "model_class": model_class,
                    "model_used": forecast[
                        "model_used"
                    ],
                    "current_index": forecast[
                        "current_index"
                    ],
                    "predicted_index": forecast[
                        "predicted_index"
                    ],
                    "change": forecast[
                        "change"
                    ],
                    "change_percent": change_percent,
                    "trend": forecast[
                        "trend"
                    ],
                    "action": action,
                }

            except Exception as exc:

                forecast_results[str(horizon)] = {
                    "status": "Forecast unavailable",
                    "error": str(exc),
                }

        candidate_result[
            "forecast_signal"
        ] = forecast_results

        # --------------------------------------------------
        # 4. Voyage economics
        # --------------------------------------------------

        vessel_time_cost = candidate.get(
            "estimated_vessel_time_cost_usd"
        )

        if vessel_time_cost is not None:

            voyage_cost = calculate_total_voyage_cost(
                cargo_quantity_mt=cargo_quantity_mt,
                vessel_type=vessel_type,
                vessel_time_cost_usd=vessel_time_cost,
            )

            candidate_result[
                "voyage_cost"
            ] = voyage_cost

        candidates.append(candidate_result)

    # ------------------------------------------------------
    # 5. Select lowest-cost feasible vessel
    # ------------------------------------------------------

    feasible_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("feasible") is True
        and candidate.get("voyage_cost") is not None
    ]

    recommended_vessel = None
    recommended_cost = None

    if feasible_candidates:

        best_candidate = min(
            feasible_candidates,
            key=lambda x: x["voyage_cost"][
                "total_voyage_cost_usd"
            ],
        )

        recommended_vessel = (
            best_candidate["vessel_type"]
        )

        recommended_cost = (
            best_candidate["voyage_cost"][
                "total_voyage_cost_usd"
            ]
        )

    # ------------------------------------------------------
    # 6. Primary strategy signal
    # ------------------------------------------------------

    strategy = "MONITOR"

    strategy_reason = (
        "No strong 30-day market-index movement "
        "detected."
    )

    if recommended_vessel is not None:

        recommended_candidate = next(
            (
                candidate
                for candidate in candidates
                if candidate.get("vessel_type")
                == recommended_vessel
            ),
            None,
        )

        if recommended_candidate:

            forecasts = (
                recommended_candidate.get(
                    "forecast_signal",
                    {}
                )
            )

            signal_30 = forecasts.get(
                "30",
                {}
            )

            if "action" in signal_30:

                strategy = signal_30[
                    "action"
                ]

                strategy_reason = (
                    f"30-day {recommended_vessel} "
                    f"market-index forecast is "
                    f"{signal_30.get('trend', 'UNKNOWN')} "
                    f"with an expected change of "
                    f"{signal_30.get('change_percent', 0):.2f}%."
                )

    return {
        "cargo_quantity_mt": cargo_quantity_mt,
        "origin_port": origin_port,
        "destination_port": destination_port,
        "sailing_days": sailing_days,
        "recommended_vessel": recommended_vessel,
        "recommended_voyage_cost_usd": recommended_cost,
        "strategy": strategy,
        "strategy_reason": strategy_reason,
        "forecast_basis": (
            "Baltic vessel-class market index. "
            "It is not a route-specific USD/MT freight quote."
        ),
        "candidates": candidates,
    }


if __name__ == "__main__":

    result = build_chartering_strategy(
        cargo_quantity_mt=60_000,
        origin_port="Paradip",
        destination_port="Visakhapatnam",
        sailing_days=3.0,
        loading_queue_days=1.0,
        discharge_queue_days=1.5,
        verified_only=False,
    )

    print("\nCHARTERING STRATEGY")
    print("=" * 70)

    print(
        f"Cargo: "
        f"{result['cargo_quantity_mt']:,} MT"
    )

    print(
        f"Route: "
        f"{result['origin_port']} -> "
        f"{result['destination_port']}"
    )

    print(
        f"Sailing days: "
        f"{result['sailing_days']}"
    )

    print(
        f"Recommended vessel: "
        f"{result['recommended_vessel']}"
    )

    if result["recommended_voyage_cost_usd"] is not None:

        print(
            f"Recommended voyage cost: "
            f"${result['recommended_voyage_cost_usd']:,.2f}"
        )

    else:

        print(
            "Recommended voyage cost: unavailable"
        )

    print(
        f"Strategy: "
        f"{result['strategy']}"
    )

    print(
        f"Reason: "
        f"{result['strategy_reason']}"
    )

    print(
        f"\nForecast basis: "
        f"{result['forecast_basis']}"
    )

    print("\nVessel Candidates:")

    for candidate in result["candidates"]:

        print("\n" + "-" * 70)

        print(
            f"Vessel: "
            f"{candidate.get('vessel_type')}"
        )

        print(
            f"Feasible: "
            f"{candidate.get('feasible')}"
        )

        if candidate.get("reason"):
            print(
                f"Reason: "
                f"{candidate.get('reason')}"
            )

        voyage_cost = candidate.get(
            "voyage_cost"
        )

        if voyage_cost:

            print(
                f"Total voyage cost: "
                f"${voyage_cost['total_voyage_cost_usd']:,.2f}"
            )

            print(
                f"Cost per MT: "
                f"${voyage_cost['total_cost_per_mt_usd']:.2f}"
            )

        forecasts = candidate.get(
            "forecast_signal",
            {}
        )

        if forecasts:

            print("\nForecast Signals:")

            for horizon, signal in forecasts.items():

                print(
                    f"  {horizon}d: "
                    f"{signal}"
                )