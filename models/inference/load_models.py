import joblib
from pathlib import Path

# ============================================================
# FREIGHT PREDICTION
# Model Loader
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

XGBOOST_DIR = BASE_DIR / "models" / "saved_multihorizon"

MODEL_DIRECTORIES = {
    "xgboost": XGBOOST_DIR,
    "lightgbm": XGBOOST_DIR,
    "randomforest": XGBOOST_DIR,
}


def load_model(
    vessel_type: str,
    horizon_days: int,
    model_name: str
):
    """
    Load a trained forecasting model.

    Naive forecasts do not require a saved model.
    """

    vessel_type = vessel_type.lower()
    model_name = model_name.lower()

    if model_name == "naive":
        return None

    if model_name not in MODEL_DIRECTORIES:
        raise ValueError(
            f"Unsupported model: {model_name}"
        )

    filename = (
        f"{vessel_type}_{horizon_days}d_{model_name}.joblib"
    )

    model_path = MODEL_DIRECTORIES[model_name] / filename

    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained model not found:\n{model_path}\n\n"
            f"Expected file:\n{filename}"
        )

    return joblib.load(model_path)