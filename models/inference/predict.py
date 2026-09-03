import pandas as pd
from pathlib import Path

from models.model_registry import get_best_model
from models.inference.load_models import load_model

# ============================================================
# FREIGHT PREDICTION
# Prediction Engine
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "multihorizon_model_dataset.csv"
)

VESSELS = ["HSI", "SI", "PI", "CI"]

HORIZONS = [7, 30, 60, 90]

TARGET_COLUMNS = [
    f"{vessel}_target_{horizon}d"
    for vessel in VESSELS
    for horizon in HORIZONS
]


def load_latest_data():
    """Load the latest available feature dataset."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{DATA_FILE}"
        )

    df = pd.read_csv(
        DATA_FILE,
        parse_dates=["Date"]
    )

    if df.empty:
        raise ValueError(
            "Forecast dataset is empty."
        )

    return df.sort_values("Date").reset_index(drop=True)


def get_latest_row():
    """Return the latest available observation."""

    df = load_latest_data()

    return df.iloc[-1]


def predict(
    vessel_type: str,
    horizon_days: int
):
    """
    Generate a forecast for one vessel type and horizon.
    """

    vessel_type = vessel_type.upper()

    if vessel_type not in VESSELS:
        raise ValueError(
            f"Unsupported vessel type: {vessel_type}"
        )

    if horizon_days not in HORIZONS:
        raise ValueError(
            "Horizon must be 7, 30, 60, or 90 days."
        )

    latest_row = get_latest_row()

    current_index = float(
        latest_row[vessel_type]
    )

    model_name = get_best_model(
        vessel_type,
        horizon_days
    )

    # --------------------------------------------------------
    # Naive forecast
    # --------------------------------------------------------

    if model_name == "Naive":

        prediction = current_index

    # --------------------------------------------------------
    # ML forecast
    # --------------------------------------------------------

    else:

        try:

            model = load_model(
                vessel_type,
                horizon_days,
                model_name
            )

            feature_columns = [
                column
                for column in latest_row.index
                if column != "Date"
                and column not in TARGET_COLUMNS
            ]

            X = pd.DataFrame(
                [
                    latest_row[feature_columns].values
                ],
                columns=feature_columns
            )

            prediction = float(
                model.predict(X)[0]
            )

        except FileNotFoundError:

            # Temporary development fallback.
            # We will remove this once all selected models
            # have been trained and saved.

            model_name = f"{model_name} (fallback)"

            prediction = current_index

    # --------------------------------------------------------
    # Change
    # --------------------------------------------------------

    change = prediction - current_index

    if current_index != 0:

        change_percent = (
            change / current_index
        ) * 100

    else:

        change_percent = 0.0

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    if change_percent > 1:

        trend = "UP"

    elif change_percent < -1:

        trend = "DOWN"

    else:

        trend = "STABLE"

    return {
        "vessel_type": vessel_type,
        "horizon_days": horizon_days,
        "model_used": model_name,
        "current_index": round(
            current_index,
            2
        ),
        "predicted_index": round(
            prediction,
            2
        ),
        "change": round(
            change,
            2
        ),
        "change_percent": round(
            change_percent,
            2
        ),
        "trend": trend
    }