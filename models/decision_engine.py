from typing import Dict

from models.forecast_confidence import (
    get_forecast_confidence,
)

from models.optimization.vessel_optimizer import (
    optimize_vessel,
)

from models.optimization.port_congestion import (
    build_congestion_summary,
)

from models.optimization.risk_optimizer import (
    evaluate_contract_risk,
    recommend_risk_strategy,
)

from models.optimization.contract_optimizer import (
    calculate_contract_rate,
)

from models.optimization.voyage_cost import (
    get_freight_rate,
    calculate_total_voyage_cost,
)

from models.inference.predict import predict


# ============================================================
# VESSEL -> MODEL CLASS
# ============================================================

VESSEL_TO_MODEL_CLASS = {
    "Handysize": "HSI",
    "Supramax": "SI",
    "Panamax": "PI",
    "Capesize": "CI",
}


# ============================================================
# FORECAST ENGINE
# ============================================================

def get_forecasts(vessel_type: str) -> Dict:
    """
    Get 7/30/60/90 day forecasts plus historical
    validation confidence.

    The actual prediction comes from models.inference.predict.
    The confidence comes from the saved validation results.
    """

    model_class = VESSEL_TO_MODEL_CLASS.get(
        vessel_type
    )

    if model_class is None:
        raise ValueError(
            f"Unsupported vessel type: {vessel_type}"
        )

    forecasts = {}

    for horizon in [7, 30, 60, 90]:

        try:

            # ------------------------------------------------
            # Generate forecast
            # ------------------------------------------------

            forecast = predict(
                vessel_type=model_class,
                horizon_days=horizon,
            )

            # ------------------------------------------------
            # Determine model used
            # ------------------------------------------------

            model_used = forecast.get(
                "model_used",
                "Unknown",
            )

            # Remove development fallback suffix.
            confidence_model = model_used.replace(
                " (fallback)",
                "",
            )

            # ------------------------------------------------
            # Get validation confidence
            # ------------------------------------------------

            confidence = get_forecast_confidence(
                vessel_type=model_class,
                horizon_days=horizon,
                model_name=confidence_model,
            )

            # ------------------------------------------------
            # Add validation metrics
            # ------------------------------------------------

            forecast["confidence"] = (
                confidence["confidence"]
            )

            forecast["validation_mae"] = (
                confidence["mae"]
            )

            forecast["validation_rmse"] = (
                confidence["rmse"]
            )

            forecast["validation_r2"] = (
                confidence["r2"]
            )

            forecast["validation_mape"] = (
                confidence["mape"]
            )

            forecast[
                "walk_forward_improvement_percent"
            ] = confidence[
                "walk_forward_improvement_percent"
            ]

            forecasts[str(horizon)] = forecast

        except Exception as exc:

            forecasts[str(horizon)] = {
                "status": "unavailable",
                "error": str(exc),
            }

    return forecasts


# ============================================================
# VOYAGE COST
# ============================================================

def calculate_candidate_voyage_cost(
    candidate: Dict,
    cargo_quantity_mt: float,
) -> Dict:
    """
    Calculate the complete voyage cost for one feasible vessel.
    """

    vessel_type = candidate[
        "vessel_type"
    ]

    vessel_time_cost = candidate.get(
        "estimated_vessel_time_cost_usd"
    )

    if vessel_time_cost is None:

        raise RuntimeError(
            f"Vessel time cost unavailable for "
            f"{vessel_type}"
        )

    return calculate_total_voyage_cost(
        cargo_quantity_mt=cargo_quantity_mt,
        vessel_type=vessel_type,
        vessel_time_cost_usd=vessel_time_cost,
    )


# ============================================================
# CONFIDENCE-AWARE STRATEGY
# ============================================================

def calculate_confidence_aware_strategy(
    change_percent: float,
    confidence: str,
    expected_savings_usd: float,
) -> Dict:
    """
    Combine:
        - market direction
        - forecast confidence
        - contract economics

    Decision rules:

        Strong rise + HIGH confidence + savings
            -> FIX_CONTRACT

        Strong rise + MEDIUM confidence + savings
            -> CONSIDER_CONTRACT

        Strong rise + LOW confidence
            -> MONITOR

        Strong decline
            -> SPOT_OR_WAIT

        Positive savings without strong signal
            -> CONSIDER_CONTRACT

        Otherwise
            -> MONITOR
    """

    change_percent = change_percent or 0.0
    expected_savings_usd = (
        expected_savings_usd or 0.0
    )

    # --------------------------------------------------------
    # Strong upward market + high confidence
    # --------------------------------------------------------

    if (
        change_percent >= 5
        and confidence == "HIGH"
        and expected_savings_usd > 0
    ):

        return {
            "action": "FIX_CONTRACT",
            "reason": (
                "The market is forecast to rise, the forecast "
                "has high validation confidence, and the fixed "
                "contract has positive expected economic value."
            ),
        }

    # --------------------------------------------------------
    # Strong upward market + medium confidence
    # --------------------------------------------------------

    if (
        change_percent >= 5
        and confidence == "MEDIUM"
        and expected_savings_usd > 0
    ):

        return {
            "action": "CONSIDER_CONTRACT",
            "reason": (
                "The market is forecast to rise and the fixed "
                "contract has positive expected economic value, "
                "but forecast confidence is only medium."
            ),
        }

    # --------------------------------------------------------
    # Strong upward market + low confidence
    # --------------------------------------------------------

    if (
        change_percent >= 5
        and confidence == "LOW"
    ):

        return {
            "action": "MONITOR",
            "reason": (
                "The market is forecast to rise, but historical "
                "validation confidence is low. The forecast "
                "should not alone trigger a contract commitment."
            ),
        }

    # --------------------------------------------------------
    # Strong downward market
    # --------------------------------------------------------

    if change_percent <= -5:

        return {
            "action": "SPOT_OR_WAIT",
            "reason": (
                "The market is forecast to decline, so waiting "
                "or using spot exposure may be preferable."
            ),
        }

    # --------------------------------------------------------
    # Stable/moderate market + positive contract economics
    # --------------------------------------------------------

    if expected_savings_usd > 0:

        return {
            "action": "CONSIDER_CONTRACT",
            "reason": (
                "The contract has positive expected economic "
                "value, but the market signal is not strong "
                "enough for an immediate fix."
            ),
        }

    # --------------------------------------------------------
    # No strong signal
    # --------------------------------------------------------

    return {
        "action": "MONITOR",
        "reason": (
            "Neither the market signal nor the contract "
            "economics justify an immediate commitment."
        ),
    }


# ============================================================
# MASTER DECISION ENGINE
# ============================================================

def build_decision(
    cargo_quantity_mt: float,
    origin_port: str,
    destination_port: str,
    contract_duration_months: int = 6,
    planned_voyages: int = 6,
    sailing_days: float = 3.0,
    loading_queue_days: float = 1.0,
    discharge_queue_days: float = 1.5,
    verified_only: bool = False,
) -> Dict:
    """
    Master Freight Prediction decision engine.

    Pipeline:

        Input
          ↓
        Vessel feasibility
          ↓
        Full voyage economics
          ↓
        Cheapest feasible vessel
          ↓
        ML forecast
          ↓
        Forecast confidence
          ↓
        Contract economics
          ↓
        Risk analysis
          ↓
        Final recommendation
    """

    # ========================================================
    # 1. Get ALL vessel feasibility results
    # ========================================================
    congestion_summary = build_congestion_summary(
    origin_port=origin_port,
    destination_port=destination_port,
    )

    vessel_result = optimize_vessel(
    cargo_quantity_mt=cargo_quantity_mt,
    origin_port=origin_port,
    destination_port=destination_port,
    sailing_days=sailing_days,
    verified_only=verified_only,
    )

    raw_candidates = vessel_result[
        "candidates"
    ]

    # ========================================================
    # 2. Calculate full voyage cost for EVERY feasible vessel
    # ========================================================

    candidates = []

    for raw_candidate in raw_candidates:

        candidate = dict(
            raw_candidate
        )

        # ----------------------------------------------------
        # Infeasible vessel
        # ----------------------------------------------------

        if not candidate.get("feasible"):

            candidates.append(
                candidate
            )

            continue

        # ----------------------------------------------------
        # Feasible vessel
        # ----------------------------------------------------

        try:

            voyage_cost = (
                calculate_candidate_voyage_cost(
                    candidate=candidate,
                    cargo_quantity_mt=cargo_quantity_mt,
                )
            )

            candidate[
                "voyage_cost"
            ] = voyage_cost

        except Exception as exc:

            candidate[
                "voyage_cost_status"
            ] = "unavailable"

            candidate[
                "voyage_cost_error"
            ] = str(exc)

        candidates.append(
            candidate
        )

    # ========================================================
    # 3. Keep vessels with complete economics
    # ========================================================

    economic_candidates = [

        candidate

        for candidate in candidates

        if candidate.get(
            "feasible"
        ) is True

        and candidate.get(
            "voyage_cost"
        ) is not None

    ]

    # ========================================================
    # 4. No economically usable vessel
    # ========================================================

    if not economic_candidates:

        # Build a frontend-friendly response even when the scenario
        # cannot support a complete vessel voyage. This keeps the
        # diagnostic information visible instead of returning a
        # sparse error-shaped payload that the UI cannot render well.
        vessel_comparison = []

        for candidate in candidates:
            comparison = {
                "vessel_type": candidate.get("vessel_type"),
                "feasible": candidate.get("feasible", False),
            }

            if candidate.get("dwt") is not None:
                comparison["dwt"] = candidate["dwt"]

            if candidate.get("voyage_cost_error"):
                comparison["voyage_cost_error"] = candidate[
                    "voyage_cost_error"
                ]

            if candidate.get("reason"):
                comparison["reason"] = candidate["reason"]

            if candidate.get("reasons"):
                comparison["reasons"] = candidate["reasons"]

            if candidate.get("loading_berths") is not None:
                comparison["loading_berths"] = candidate.get(
                    "loading_berths", []
                )

            if candidate.get("discharge_berths") is not None:
                comparison["discharge_berths"] = candidate.get(
                    "discharge_berths", []
                )

            vessel_comparison.append(comparison)

        return {
            "status": "NO_ECONOMICALLY_FEASIBLE_VESSEL",
            "input": {
                "cargo_quantity_mt": cargo_quantity_mt,
                "origin_port": origin_port,
                "destination_port": destination_port,
                "contract_duration_months": contract_duration_months,
                "planned_voyages": planned_voyages,
            },
            "message": (
                "No vessel has a complete feasible voyage cost under "
                "the current assumptions. Review vessel capacity, "
                "berth constraints, or choose another destination."
            ),
            "candidates": candidates,
            "vessel_comparison": vessel_comparison,
            "congestion": congestion_summary,
            "diagnostic": {
                "type": "VESSEL_FEASIBILITY",
                "recommended_action": (
                    "CHANGE_DESTINATION_OR_CARGO_OR_REVIEW_VESSEL_CONSTRAINTS"
                ),
            },
            "data_note": (
                "No economically feasible vessel was found under the "
                "current prototype vessel, berth, cost, and queue-time "
                "assumptions. Market forecast and contract economics "
                "are not generated because no vessel class can be "
                "selected reliably for this scenario."
            ),
        }

    # ========================================================
    # 5. Select lowest-cost vessel
    # ========================================================

    best_candidate = min(
        economic_candidates,

        key=lambda x:
        x[
            "voyage_cost"
        ][
            "total_voyage_cost_usd"
        ],
    )

    recommended_vessel = (
        best_candidate[
            "vessel_type"
        ]
    )

    voyage_cost = (
        best_candidate[
            "voyage_cost"
        ]
    )

    # ========================================================
    # 6. Generate forecasts for selected vessel
    # ========================================================

    forecasts = get_forecasts(
        recommended_vessel
    )

    # ========================================================
    # 7. Primary 30-day signal
    # ========================================================

    forecast_30 = forecasts.get(
        "30",
        {},
    )

    current_index = (
        forecast_30.get(
            "current_index"
        )
    )

    predicted_index = (
        forecast_30.get(
            "predicted_index"
        )
    )

    change_percent = (
        forecast_30.get(
            "change_percent"
        )
    )

    forecast_confidence = (
        forecast_30.get(
            "confidence",
            "LOW",
        )
    )

    # ========================================================
    # 8. Current prototype freight rate
    # ========================================================

    current_rate = get_freight_rate(
        recommended_vessel
    )

    # ========================================================
    # 9. Forecasted freight-rate proxy
    # ========================================================

    if change_percent is not None:

        forecast_rate = (
            current_rate
            * (
                1
                + change_percent / 100
            )
        )

    else:

        forecast_rate = (
            current_rate
        )

    # ========================================================
    # 10. Calculate contract rate
    # ========================================================

    contract_rate = (
        calculate_contract_rate(
            spot_rate_usd_per_mt=(
                current_rate
            ),
            contract_months=(
                contract_duration_months
            ),
        )
    )

    # ========================================================
    # 11. Risk analysis
    # ========================================================

    risk_analysis = (
        evaluate_contract_risk(
            cargo_quantity_mt=(
                cargo_quantity_mt
            ),

            voyages=(
                planned_voyages
            ),

            current_rate_usd_per_mt=(
                current_rate
            ),

            forecast_change_percent=(
                change_percent
                or 0.0
            ),

            contract_rate_usd_per_mt=(
                contract_rate
            ),
        )
    )

    expected_savings = (
        risk_analysis[
            "expected_savings_from_contract_usd"
        ]
    )

    # ========================================================
    # 12. Confidence-aware final strategy
    # ========================================================

    final_strategy = (
        calculate_confidence_aware_strategy(
            change_percent=(
                change_percent
                or 0.0
            ),

            confidence=(
                forecast_confidence
            ),

            expected_savings_usd=(
                expected_savings
            ),
        )
    )

    # ========================================================
    # 13. Vessel economic comparison
    # ========================================================

    vessel_comparison = []

    for candidate in candidates:

        comparison = {
            "vessel_type": (
                candidate.get(
                    "vessel_type"
                )
            ),

            "feasible": (
                candidate.get(
                    "feasible"
                )
            ),
        }

        # ----------------------------------------------------
        # Economic data
        # ----------------------------------------------------

        if candidate.get(
            "voyage_cost"
        ):

            comparison[
                "total_voyage_cost_usd"
            ] = candidate[
                "voyage_cost"
            ][
                "total_voyage_cost_usd"
            ]

            comparison[
                "cost_per_mt_usd"
            ] = candidate[
                "voyage_cost"
            ][
                "total_cost_per_mt_usd"
            ]

            comparison[
                "freight_cost_usd"
            ] = candidate[
                "voyage_cost"
            ][
                "freight_cost_usd"
            ]

            comparison[
                "vessel_time_cost_usd"
            ] = candidate[
                "voyage_cost"
            ][
                "vessel_time_cost_usd"
            ]

            comparison[
                "bunker_cost_usd"
            ] = candidate[
                "voyage_cost"
            ][
                "bunker_cost_usd"
            ]

            comparison[
                "port_charges_usd"
            ] = candidate[
                "voyage_cost"
            ][
                "port_charges_usd"
            ]

            comparison[
                "total_vessel_time_days"
            ] = candidate.get(
                "total_vessel_time_days"
            )

            comparison[
                "total_port_time_days"
            ] = candidate.get(
                "total_port_time_days"
            )

        # ----------------------------------------------------
        # Infeasibility reason
        # ----------------------------------------------------

        if candidate.get(
            "reason"
        ):

            comparison[
                "reason"
            ] = candidate[
                "reason"
            ]

        if candidate.get(
            "reasons"
        ):

            comparison[
                "reasons"
            ] = candidate[
                "reasons"
            ]

        vessel_comparison.append(
            comparison
        )

    # ========================================================
    # 14. Return complete decision
    # ========================================================

    return {

        "status": "SUCCESS",

        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        "input": {

            "cargo_quantity_mt": (
                cargo_quantity_mt
            ),

            "origin_port": (
                origin_port
            ),

            "destination_port": (
                destination_port
            ),

            "contract_duration_months": (
                contract_duration_months
            ),

            "planned_voyages": (
                planned_voyages
            ),
        },

        # ----------------------------------------------------
        # VESSEL DECISION
        # ----------------------------------------------------

        "vessel_decision": {

            "recommended_vessel": (
                recommended_vessel
            ),

            "recommended_voyage_cost_usd": (
                voyage_cost[
                    "total_voyage_cost_usd"
                ]
            ),

            "cost_per_mt_usd": (
                voyage_cost[
                    "total_cost_per_mt_usd"
                ]
            ),

            "freight_cost_usd": (
                voyage_cost[
                    "freight_cost_usd"
                ]
            ),

            "vessel_time_cost_usd": (
                voyage_cost[
                    "vessel_time_cost_usd"
                ]
            ),

            "bunker_cost_usd": (
                voyage_cost[
                    "bunker_cost_usd"
                ]
            ),

            "port_charges_usd": (
                voyage_cost[
                    "port_charges_usd"
                ]
            ),

            "total_vessel_time_days": (
                best_candidate.get(
                    "total_vessel_time_days"
                )
            ),

            "total_port_time_days": (
                best_candidate.get(
                    "total_port_time_days"
                )
            ),

            "loading_berths": (
                best_candidate.get(
                    "loading_berths",
                    [],
                )
            ),

            "discharge_berths": (
                best_candidate.get(
                    "discharge_berths",
                    [],
                )
            ),
        },

        # ----------------------------------------------------
        # ALL VESSEL COMPARISON
        # ----------------------------------------------------
        "congestion": congestion_summary,

        "vessel_comparison": (
            vessel_comparison
        ),

        # ----------------------------------------------------
        # FORECAST
        # ----------------------------------------------------

        "forecast": {

            "vessel_class": (
                VESSEL_TO_MODEL_CLASS[
                    recommended_vessel
                ]
            ),

            "current_index": (
                current_index
            ),

            "predicted_30d_index": (
                predicted_index
            ),

            "change_percent_30d": (
                change_percent
            ),

            "confidence_30d": (
                forecast_confidence
            ),

            "all_horizons": (
                forecasts
            ),
        },

        # ----------------------------------------------------
        # CONTRACT
        # ----------------------------------------------------

        "contract_decision": {

            "current_rate_usd_per_mt": (
                current_rate
            ),

            "forecast_rate_usd_per_mt": (
                round(
                    forecast_rate,
                    2,
                )
            ),

            "contract_rate_usd_per_mt": (
                round(
                    contract_rate,
                    2,
                )
            ),

            "contract_duration_months": (
                contract_duration_months
            ),

            "planned_voyages": (
                planned_voyages
            ),

            "risk_analysis": (
                risk_analysis
            ),
        },

        # ----------------------------------------------------
        # FINAL RECOMMENDATION
        # ----------------------------------------------------

        "final_recommendation": {

            "action": (
                final_strategy[
                    "action"
                ]
            ),

            "recommended_vessel": (
                recommended_vessel
            ),

            "reason": (
                final_strategy[
                    "reason"
                ]
            ),

            "forecast_confidence": (
                forecast_confidence
            ),
        },

        # ----------------------------------------------------
        # DATA NOTE
        # ----------------------------------------------------

        "data_note": (

            "The ML component currently forecasts a Baltic "
            "vessel-class market index. USD/MT freight rate, "
            "bunker cost, port charges, sailing time, and "
            "queue time are prototype assumptions and are "
            "not route-specific market quotes."
        ),
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = build_decision(

        cargo_quantity_mt=60_000,

        origin_port="Paradip",

        destination_port="Visakhapatnam",

        contract_duration_months=6,

        planned_voyages=6,

        sailing_days=3.0,

        loading_queue_days=1.0,

        discharge_queue_days=1.5,

        verified_only=False,
    )

    print()

    print(
        "=" * 75
    )

    print(
        "FREIGHT PREDICTION - MASTER DECISION"
    )

    print(
        "=" * 75
    )

    print(
        f"\nStatus: "
        f"{result['status']}"
    )

    if result["status"] == "SUCCESS":

        # ==================================================
        # INPUT
        # ==================================================

        print(
            "\nINPUT"
        )

        print(
            "-" * 75
        )

        print(
            f"Cargo: "
            f"{result['input']['cargo_quantity_mt']:,} MT"
        )

        print(
            f"Route: "
            f"{result['input']['origin_port']} -> "
            f"{result['input']['destination_port']}"
        )

        print(
            f"Contract duration: "
            f"{result['input']['contract_duration_months']} months"
        )

        print(
            f"Planned voyages: "
            f"{result['input']['planned_voyages']}"
        )

        # ==================================================
        # VESSEL COMPARISON
        # ==================================================

        print(
            "\nVESSEL ECONOMIC COMPARISON"
        )

        print(
            "-" * 75
        )

        for vessel in result[
            "vessel_comparison"
        ]:

            print()

            print(
                f"{vessel['vessel_type']}"
            )

            print(
                f"Feasible: "
                f"{vessel['feasible']}"
            )

            if (
                "total_voyage_cost_usd"
                in vessel
            ):

                print(
                    f"Total voyage cost: "
                    f"${vessel['total_voyage_cost_usd']:,.2f}"
                )

                print(
                    f"Cost per MT: "
                    f"${vessel['cost_per_mt_usd']:.2f}"
                )

                print(
                    f"Freight cost: "
                    f"${vessel['freight_cost_usd']:,.2f}"
                )

                print(
                    f"Vessel time cost: "
                    f"${vessel['vessel_time_cost_usd']:,.2f}"
                )

                print(
                    f"Bunker cost: "
                    f"${vessel['bunker_cost_usd']:,.2f}"
                )

                print(
                    f"Port charges: "
                    f"${vessel['port_charges_usd']:,.2f}"
                )

                print(
                    f"Total vessel time: "
                    f"{vessel['total_vessel_time_days']:.2f} days"
                )

            if vessel.get(
                "reason"
            ):

                print(
                    f"Reason: "
                    f"{vessel['reason']}"
                )

            if vessel.get(
                "reasons"
            ):

                print(
                    f"Reasons: "
                    f"{vessel['reasons']}"
                )

        # ==================================================
        # SELECTED VESSEL
        # ==================================================

        print(
            "\nSELECTED VESSEL"
        )

        print(
            "-" * 75
        )

        vessel = result[
            "vessel_decision"
        ]

        print(
            f"Recommended vessel: "
            f"{vessel['recommended_vessel']}"
        )

        print(
            f"Total voyage cost: "
            f"${vessel['recommended_voyage_cost_usd']:,.2f}"
        )

        print(
            f"Cost per MT: "
            f"${vessel['cost_per_mt_usd']:.2f}"
        )

        print(
            f"Freight cost: "
            f"${vessel['freight_cost_usd']:,.2f}"
        )

        print(
            f"Vessel time cost: "
            f"${vessel['vessel_time_cost_usd']:,.2f}"
        )

        print(
            f"Bunker cost: "
            f"${vessel['bunker_cost_usd']:,.2f}"
        )

        print(
            f"Port charges: "
            f"${vessel['port_charges_usd']:,.2f}"
        )

        print(
            f"Total vessel time: "
            f"{vessel['total_vessel_time_days']:.2f} days"
        )

        print(
            f"Total port time: "
            f"{vessel['total_port_time_days']:.2f} days"
        )

        print(
            f"Loading berths: "
            f"{vessel['loading_berths']}"
        )

        print(
            f"Discharge berths: "
            f"{vessel['discharge_berths']}"
        )

        # ==================================================
        # FORECAST
        # ==================================================
        print(
            "\nCONGESTION"
        )

        print(
            "-" * 75
        )

        congestion = result[
            "congestion"
        ]

        print(
            f"Loading queue: "
            f"{congestion['loading']['queue_days']} days"
        )

        print(
            f"Discharge queue: "
            f"{congestion['discharge']['queue_days']} days"
        )

        print(
            f"Total queue: "
            f"{congestion['total_queue_days']} days"
        )

        print(
            f"Risk level: "
            f"{congestion['risk_level']}"
        )

        print(
            f"Real data used: "
            f"{congestion['real_data_used']}"
        )

        print(
            "\nFORECAST"
        )

        print(
            "-" * 75
        )

        forecast = result[
            "forecast"
        ]

        print(
            f"Vessel class: "
            f"{forecast['vessel_class']}"
        )

        print(
            f"Current index: "
            f"{forecast['current_index']}"
        )

        print(
            f"30-day predicted index: "
            f"{forecast['predicted_30d_index']}"
        )

        print(
            f"30-day change: "
            f"{forecast['change_percent_30d']}%"
        )

        print(
            f"30-day confidence: "
            f"{forecast['confidence_30d']}"
        )

        print(
            "\nAll Forecasts:"
        )

        for horizon, data in forecast[
            "all_horizons"
        ].items():

            print(
                f"\n{horizon}-day:"
            )

            print(
                f"  Model: "
                f"{data.get('model_used', 'N/A')}"
            )

            print(
                f"  Current index: "
                f"{data.get('current_index', 'N/A')}"
            )

            print(
                f"  Predicted index: "
                f"{data.get('predicted_index', 'N/A')}"
            )

            print(
                f"  Change: "
                f"{data.get('change_percent', 'N/A')}%"
            )

            print(
                f"  Confidence: "
                f"{data.get('confidence', 'N/A')}"
            )

            if (
                "validation_mape"
                in data
            ):

                print(
                    f"  Validation MAPE: "
                    f"{data['validation_mape']:.2f}%"
                )

            if (
                "validation_r2"
                in data
            ):

                print(
                    f"  Validation R²: "
                    f"{data['validation_r2']:.3f}"
                )

            if (
                "walk_forward_improvement_percent"
                in data
            ):

                print(
                    f"  Walk-forward improvement: "
                    f"{data['walk_forward_improvement_percent']:.2f}%"
                )

        # ==================================================
        # CONTRACT
        # ==================================================

        print(
            "\nCONTRACT"
        )

        print(
            "-" * 75
        )

        contract = result[
            "contract_decision"
        ]

        print(
            f"Current rate: "
            f"${contract['current_rate_usd_per_mt']:.2f}/MT"
        )

        print(
            f"Forecast rate: "
            f"${contract['forecast_rate_usd_per_mt']:.2f}/MT"
        )

        print(
            f"Contract rate: "
            f"${contract['contract_rate_usd_per_mt']:.2f}/MT"
        )

        risk = contract[
            "risk_analysis"
        ]

        print(
            f"Expected spot cost: "
            f"${risk['expected_spot_cost_usd']:,.2f}"
        )

        print(
            f"Contract cost: "
            f"${risk['contract_cost_usd']:,.2f}"
        )

        print(
            f"Expected contract savings: "
            f"${risk['expected_savings_from_contract_usd']:,.2f}"
        )

        print(
            f"Expected savings %: "
            f"{risk['expected_savings_percent']:.2f}%"
        )

        # ==================================================
        # FINAL RECOMMENDATION
        # ==================================================

        print(
            "\nFINAL RECOMMENDATION"
        )

        print(
            "-" * 75
        )

        recommendation = result[
            "final_recommendation"
        ]

        print(
            f"ACTION: "
            f"{recommendation['action']}"
        )

        print(
            f"VESSEL: "
            f"{recommendation['recommended_vessel']}"
        )

        print(
            f"CONFIDENCE: "
            f"{recommendation['forecast_confidence']}"
        )

        print(
            f"REASON: "
            f"{recommendation['reason']}"
        )

        # ==================================================
        # DATA NOTE
        # ==================================================

        print(
            "\nDATA NOTE"
        )

        print(
            "-" * 75
        )

        print(
            result["data_note"]
        )

    else:

        print(
            result["message"]
        )

    print(
        "\n" + "=" * 75
    )