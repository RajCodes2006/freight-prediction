import pandas as pd
from pathlib import Path

from models.model_registry import get_best_model
from models.inference.load_models import load_model
from models.inference.live_market import get_live_market_snapshot
from models.inference.live_calibration import calibrate_live_vessel_indices

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

    The trained model still operates on its historical feature space. When
    current BDI/BCI data is available, a historical calibration layer updates
    the current level and applies the model's predicted percentage movement
    to that live level. This avoids treating BDI/BCI as route-specific rates.
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

    historical_current_index = float(
        latest_row[vessel_type]
    )

    model_name = get_best_model(
        vessel_type,
        horizon_days
    )

    # --------------------------------------------------------
    # Historical-space prediction
    # --------------------------------------------------------

    if model_name == "Naive":

        historical_prediction = historical_current_index

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

            historical_prediction = float(
                model.predict(X)[0]
            )

        except FileNotFoundError:

            model_name = f"{model_name} (fallback)"

            historical_prediction = historical_current_index

    # --------------------------------------------------------
    # Live calibration
    # --------------------------------------------------------

    market_snapshot = get_live_market_snapshot()
    calibration = calibrate_live_vessel_indices(market_snapshot)

    live_current_index = calibration.get(
        "vessel_indices", {}
    ).get(vessel_type)

    if (
        calibration.get("available")
        and live_current_index is not None
        and historical_current_index != 0
    ):
        # Preserve the trained model's relative movement while replacing the
        # stale historical level with the current calibrated market level.
        relative_multiplier = (
            historical_prediction / historical_current_index
        )
        prediction = float(live_current_index) * relative_multiplier
        current_index = float(live_current_index)
        current_level_source = "LIVE_CALIBRATED"
    else:
        prediction = historical_prediction
        current_index = historical_current_index
        current_level_source = "HISTORICAL_MODEL_DATA"

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
        "trend": trend,
        "historical_model_index": round(
            historical_current_index,
            2
        ),
        "historical_model_prediction": round(
            historical_prediction,
            2
        ),
        "current_level_source": current_level_source,
        "live_market_calibration": calibration,
    }
