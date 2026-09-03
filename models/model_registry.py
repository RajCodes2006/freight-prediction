# ============================================================
# FREIGHT PREDICTION
# Model Registry
# ============================================================

MODEL_REGISTRY = {
    "HSI": {
        7: "XGBoost",
        30: "Naive",
        60: "XGBoost",
        90: "XGBoost",
    },

    "SI": {
        7: "XGBoost",
        30: "Naive",
        60: "Naive",
        90: "Naive",
    },

    "PI": {
        7: "XGBoost",
        30: "LightGBM",
        60: "RandomForest",
        90: "XGBoost",
    },

    "CI": {
        7: "Naive",
        30: "Naive",
        60: "Naive",
        90: "XGBoost",
    },
}


def get_best_model(vessel_type: str, horizon_days: int) -> str:
    """
    Return the validated best model for a
    vessel type and forecast horizon.
    """

    vessel_type = vessel_type.upper()

    if vessel_type not in MODEL_REGISTRY:
        raise ValueError(
            f"Unsupported vessel type: {vessel_type}"
        )

    if horizon_days not in MODEL_REGISTRY[vessel_type]:
        raise ValueError(
            f"Unsupported forecast horizon: {horizon_days}"
        )

    return MODEL_REGISTRY[vessel_type][horizon_days]