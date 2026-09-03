# ============================================================
# FREIGHT PREDICTION
# Recommendation Engine
# ============================================================


def generate_recommendation(
    current_index: float,
    predicted_index: float,
    horizon_days: int
):
    """
    Generate an initial market-entry recommendation.

    IMPORTANT:
    This is a prototype rule-based recommendation.
    Later we will incorporate:
    - forecast confidence
    - route-specific freight rates
    - port congestion
    - vessel economics
    - bunker costs
    - contract duration
    - spot vs multiple-voyage economics
    """

    if current_index <= 0:
        return {
            "action": "NO_DECISION",
            "change_percent": 0.0,
            "reason": "Current freight index is invalid."
        }

    # --------------------------------------------------------
    # Calculate expected movement
    # --------------------------------------------------------

    change_percent = (
        (predicted_index - current_index)
        / current_index
    ) * 100

    # --------------------------------------------------------
    # Decision thresholds
    # --------------------------------------------------------

    if change_percent >= 5:

        action = "FIX_NOW"

        reason = (
            f"Freight conditions are forecast to increase "
            f"by {change_percent:.2f}% over {horizon_days} days. "
            f"Early chartering may reduce exposure to higher rates."
        )

    elif change_percent <= -5:

        action = "WAIT"

        reason = (
            f"Freight conditions are forecast to decrease "
            f"by {abs(change_percent):.2f}% over {horizon_days} days. "
            f"Waiting may provide a better market-entry opportunity."
        )

    else:

        action = "MONITOR"

        reason = (
            f"Expected freight movement is only "
            f"{change_percent:.2f}%. "
            f"No strong market-entry signal is detected."
        )

    return {
        "action": action,
        "change_percent": round(change_percent, 2),
        "reason": reason
    }