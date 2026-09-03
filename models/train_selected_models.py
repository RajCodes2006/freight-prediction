import pandas as pd
import joblib

from pathlib import Path
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor

from models.model_registry import MODEL_REGISTRY

# ============================================================
# FREIGHT PREDICTION
# Step 13: Train Selected Models
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "multihorizon_model_dataset.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "models"
    / "saved_multihorizon"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

VESSELS = ["HSI", "SI", "PI", "CI"]
HORIZONS = [7, 30, 60, 90]

print("=" * 80)
print("FREIGHT PREDICTION - TRAIN SELECTED MODELS")
print("=" * 80)

# ------------------------------------------------------------
# 1. Load dataset
# ------------------------------------------------------------

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)

print(
    f"\nDataset shape: {df.shape}"
)

print(
    f"Date range: "
    f"{df['Date'].min().date()} → "
    f"{df['Date'].max().date()}"
)

# ------------------------------------------------------------
# 2. Identify targets
# ------------------------------------------------------------

target_columns = [
    f"{vessel}_target_{horizon}d"
    for vessel in VESSELS
    for horizon in HORIZONS
]

feature_columns = [
    column
    for column in df.columns
    if column != "Date"
    and column not in target_columns
]

print(
    f"Feature columns: {len(feature_columns)}"
)

# ------------------------------------------------------------
# 3. Model factory
# ------------------------------------------------------------

def create_model(model_name):

    if model_name == "XGBoost":

        return XGBRegressor(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1
        )

    if model_name == "LightGBM":

        return LGBMRegressor(
            n_estimators=250,
            max_depth=5,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=-1,
            n_jobs=-1
        )

    if model_name == "RandomForest":

        return RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

    raise ValueError(
        f"Unsupported model: {model_name}"
    )


# ------------------------------------------------------------
# 4. Train selected models
# ------------------------------------------------------------

trained = 0
skipped = 0

for vessel in VESSELS:

    for horizon in HORIZONS:

        model_name = MODEL_REGISTRY[
            vessel
        ][horizon]

        target = (
            f"{vessel}_target_{horizon}d"
        )

        print("\n" + "-" * 80)

        print(
            f"{vessel} | "
            f"{horizon} days | "
            f"{model_name}"
        )

        # ----------------------------------------------------
        # Naive requires no model
        # ----------------------------------------------------

        if model_name == "Naive":

            print(
                "Naive model → no file required."
            )

            skipped += 1
            continue

        # ----------------------------------------------------
        # Prepare training data
        # ----------------------------------------------------

        training_data = df.dropna(
            subset=[target]
        ).copy()

        X_train = training_data[
            feature_columns
        ]

        y_train = training_data[
            target
        ]

        print(
            f"Training rows: {len(training_data)}"
        )

        # ----------------------------------------------------
        # Train
        # ----------------------------------------------------

        model = create_model(
            model_name
        )

        model.fit(
            X_train,
            y_train
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        filename = (
            f"{vessel.lower()}_"
            f"{horizon}d_"
            f"{model_name.lower()}.joblib"
        )

        model_path = MODEL_DIR / filename

        joblib.dump(
            model,
            model_path
        )

        print(
            f"Saved: {model_path}"
        )

        trained += 1


# ------------------------------------------------------------
# 5. Verify expected files
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("MODEL FILE VERIFICATION")
print("=" * 80)

for vessel in VESSELS:

    for horizon in HORIZONS:

        model_name = MODEL_REGISTRY[
            vessel
        ][horizon]

        if model_name == "Naive":
            continue

        filename = (
            f"{vessel.lower()}_"
            f"{horizon}d_"
            f"{model_name.lower()}.joblib"
        )

        model_path = MODEL_DIR / filename

        if model_path.exists():

            print(
                f"✓ {filename}"
            )

        else:

            print(
                f"✗ MISSING: {filename}"
            )

print("\n" + "=" * 80)
print("TRAINING COMPLETE")
print("=" * 80)

print(
    f"\nModels trained: {trained}"
)

print(
    f"Naive configurations skipped: {skipped}"
)

print(
    f"\nModel directory:"
    f"\n{MODEL_DIR}"
)