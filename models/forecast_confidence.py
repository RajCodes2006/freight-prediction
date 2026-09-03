from pathlib import Path
from typing import Dict

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "model_competition_results.csv"
)

WALK_FORWARD_FILE = (
    BASE_DIR
    / "data"
    / "walk_forward_results.csv"
)


def load_model_results() -> pd.DataFrame:
    """Load model competition results."""

    if not MODEL_RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Model results file not found:\n"
            f"{MODEL_RESULTS_FILE}"
        )

    return pd.read_csv(MODEL_RESULTS_FILE)


def load_walk_forward_results() -> pd.DataFrame:
    """Load walk-forward results."""

    if not WALK_FORWARD_FILE.exists():
        raise FileNotFoundError(
            f"Walk-forward file not found:\n"
            f"{WALK_FORWARD_FILE}"
        )

    return pd.read_csv(WALK_FORWARD_FILE)


def get_model_performance(
    vessel_type: str,
    horizon_days: int,
    model_name: str,
) -> Dict:
    """Return validation metrics for a model."""

    df = load_model_results()

    result = df[
        (df["vessel_type"] == vessel_type)
        & (df["horizon_days"] == horizon_days)
        & (df["model"] == model_name)
    ]

    if result.empty:
        raise ValueError(
            f"No performance data found for "
            f"{vessel_type}/{horizon_days}/{model_name}"
        )

    row = result.iloc[0]

    return {
        "vessel_type": vessel_type,
        "horizon_days": horizon_days,
        "model": model_name,
        "evaluation_points": int(
            row["evaluation_points"]
        ),
        "mae": float(row["mae"]),
        "rmse": float(row["rmse"]),
        "r2": float(row["r2"]),
        "mape": float(row["mape"]),
    }


def get_walk_forward_improvement(
    vessel_type: str,
    horizon_days: int,
) -> float:
    """Get walk-forward improvement versus naive."""

    df = load_walk_forward_results()

    result = df[
        (df["vessel_type"] == vessel_type)
        & (df["horizon_days"] == horizon_days)
    ]

    if result.empty:
        return 0.0

    return float(
        result.iloc[0]["improvement_percent"]
    )


def calculate_confidence(
    r2: float,
    mape: float,
    improvement_percent: float,
) -> str:
    """
    Conservative confidence classification.

    HIGH:
        R² >= 0.50
        MAPE <= 15%
        improvement > 10%

    MEDIUM:
        R² >= 0.00
        MAPE <= 30%
        improvement > 0%

    LOW:
        Everything else.
    """

    # Strong validation performance
    if (
        r2 >= 0.50
        and mape <= 15
        and improvement_percent > 10
    ):
        return "HIGH"

    # Usable but uncertain
    if (
        r2 >= 0.00
        and mape <= 30
        and improvement_percent > 0
    ):
        return "MEDIUM"

    return "LOW"


def get_forecast_confidence(
    vessel_type: str,
    horizon_days: int,
    model_name: str,
) -> Dict:
    """Combine model performance and walk-forward validation."""

    performance = get_model_performance(
        vessel_type=vessel_type,
        horizon_days=horizon_days,
        model_name=model_name,
    )

    improvement_percent = get_walk_forward_improvement(
        vessel_type=vessel_type,
        horizon_days=horizon_days,
    )

    confidence = calculate_confidence(
        r2=performance["r2"],
        mape=performance["mape"],
        improvement_percent=improvement_percent,
    )

    return {
        **performance,
        "walk_forward_improvement_percent": round(
            improvement_percent,
            2,
        ),
        "confidence": confidence,
    }


def explain_confidence(
    confidence: str,
    r2: float,
    mape: float,
    improvement_percent: float,
) -> str:
    """Generate a human-readable explanation."""

    if confidence == "HIGH":
        return (
            f"High confidence because validation shows "
            f"strong explanatory power (R²={r2:.2f}), "
            f"low forecast error (MAPE={mape:.2f}%), "
            f"and {improvement_percent:.2f}% improvement "
            f"over the naive baseline."
        )

    if confidence == "MEDIUM":
        return (
            f"Medium confidence because the model provides "
            f"some predictive value, but uncertainty remains. "
            f"R²={r2:.2f}, MAPE={mape:.2f}%, "
            f"improvement={improvement_percent:.2f}%."
        )

    return (
        f"Low confidence because validation does not show "
        f"strong predictive reliability. "
        f"R²={r2:.2f}, MAPE={mape:.2f}%, "
        f"improvement={improvement_percent:.2f}%."
    )


if __name__ == "__main__":

    tests = [
        ("PI", 7, "XGBoost"),
        ("PI", 30, "LightGBM"),
        ("PI", 60, "RandomForest"),
        ("PI", 90, "XGBoost"),
        ("SI", 7, "XGBoost"),
        ("SI", 30, "Naive"),
        ("SI", 60, "Naive"),
        ("SI", 90, "Naive"),
    ]

    print("\nFORECAST MODEL CONFIDENCE")
    print("=" * 70)

    for vessel, horizon, model in tests:

        try:

            result = get_forecast_confidence(
                vessel_type=vessel,
                horizon_days=horizon,
                model_name=model,
            )

            explanation = explain_confidence(
                confidence=result["confidence"],
                r2=result["r2"],
                mape=result["mape"],
                improvement_percent=(
                    result[
                        "walk_forward_improvement_percent"
                    ]
                ),
            )

            print("\n" + "-" * 70)

            print(
                f"Vessel class: {vessel}"
            )

            print(
                f"Horizon: {horizon} days"
            )

            print(
                f"Model: {model}"
            )

            print(
                f"MAE: {result['mae']:.2f}"
            )

            print(
                f"RMSE: {result['rmse']:.2f}"
            )

            print(
                f"R²: {result['r2']:.3f}"
            )

            print(
                f"MAPE: {result['mape']:.2f}%"
            )

            print(
                f"Walk-forward improvement: "
                f"{result['walk_forward_improvement_percent']:.2f}%"
            )

            print(
                f"CONFIDENCE: "
                f"{result['confidence']}"
            )

            print(
                f"Explanation: "
                f"{explanation}"
            )

        except Exception as exc:

            print(
                f"\nERROR for "
                f"{vessel}/{horizon}/{model}: "
                f"{exc}"
            )