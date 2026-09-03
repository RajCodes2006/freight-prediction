import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from xgboost import XGBRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# ============================================================
# FREIGHT PREDICTION
# Step 5: Train Forecasting Models
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "model_dataset.csv"
MODEL_DIR = BASE_DIR / "models" / "saved"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

VESSELS = ["HSI", "SI", "PI", "CI"]

print("=" * 75)
print("FREIGHT PREDICTION - MODEL TRAINING")
print("=" * 75)

# ------------------------------------------------------------
# 1. Load dataset
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)

print(f"\nDataset shape: {df.shape}")
print(f"Date range: {df['Date'].min().date()} → {df['Date'].max().date()}")

# ------------------------------------------------------------
# 2. Remove future target columns from FEATURES
# ------------------------------------------------------------
# IMPORTANT:
# Every *_target column represents the future.
# Keeping them would cause data leakage.

target_columns = [
    "HSI_target",
    "SI_target",
    "PI_target",
    "CI_target"
]

feature_columns = [
    col
    for col in df.columns
    if col not in target_columns
    and col != "Date"
]

print(f"\nNumber of features: {len(feature_columns)}")

# ------------------------------------------------------------
# 3. Chronological train/test split
# ------------------------------------------------------------

split_index = int(len(df) * 0.80)

train_df = df.iloc[:split_index].copy()
test_df = df.iloc[split_index:].copy()

print("\nTrain/Test split:")
print(
    f"Train: {train_df['Date'].min().date()} "
    f"→ {train_df['Date'].max().date()}"
)

print(
    f"Test : {test_df['Date'].min().date()} "
    f"→ {test_df['Date'].max().date()}"
)

# ------------------------------------------------------------
# 4. XGBoost settings
# ------------------------------------------------------------

model_params = {
    "n_estimators": 500,
    "max_depth": 6,
    "learning_rate": 0.03,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "random_state": 42,
    "n_jobs": -1
}

results = []

# ------------------------------------------------------------
# 5. Train one model for each vessel class
# ------------------------------------------------------------

for vessel in VESSELS:

    print("\n" + "-" * 75)
    print(f"TRAINING MODEL: {vessel}")
    print("-" * 75)

    target = f"{vessel}_target"

    # Features
    X_train = train_df[feature_columns]
    X_test = test_df[feature_columns]

    # Target
    y_train = train_df[target]
    y_test = test_df[target]

    # --------------------------------------------------------
    # Baseline
    # --------------------------------------------------------
    # Today's value predicts the next available value.

    baseline_predictions = test_df[vessel].values

    baseline_mae = mean_absolute_error(
        y_test,
        baseline_predictions
    )

    baseline_rmse = np.sqrt(
        mean_squared_error(
            y_test,
            baseline_predictions
        )
    )

    baseline_r2 = r2_score(
        y_test,
        baseline_predictions
    )

    # --------------------------------------------------------
    # XGBoost
    # --------------------------------------------------------

    model = XGBRegressor(**model_params)

    model.fit(
        X_train,
        y_train,
        verbose=False
    )

    predictions = model.predict(X_test)

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    # MAPE
    non_zero = y_test != 0

    mape = np.mean(
        np.abs(
            (y_test[non_zero] - predictions[non_zero])
            / y_test[non_zero]
        )
    ) * 100

    # Improvement over baseline
    improvement = (
        (baseline_mae - mae)
        / baseline_mae
    ) * 100

    print(f"\nBaseline:")
    print(f"  MAE  : {baseline_mae:.2f}")
    print(f"  RMSE : {baseline_rmse:.2f}")
    print(f"  R²   : {baseline_r2:.4f}")

    print(f"\nXGBoost:")
    print(f"  MAE  : {mae:.2f}")
    print(f"  RMSE : {rmse:.2f}")
    print(f"  R²   : {r2:.4f}")
    print(f"  MAPE : {mape:.2f}%")

    print(
        f"\nImprovement over baseline: "
        f"{improvement:.2f}%"
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    model_file = MODEL_DIR / f"{vessel.lower()}_xgboost.joblib"

    joblib.dump(
        model,
        model_file
    )

    print(f"\nModel saved:")
    print(model_file)

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    results.append({
        "vessel_type": vessel,
        "baseline_mae": baseline_mae,
        "baseline_rmse": baseline_rmse,
        "xgb_mae": mae,
        "xgb_rmse": rmse,
        "xgb_r2": r2,
        "xgb_mape": mape,
        "improvement_percent": improvement
    })

# ------------------------------------------------------------
# 6. Results table
# ------------------------------------------------------------

results_df = pd.DataFrame(results)

results_file = BASE_DIR / "data" / "model_results.csv"

results_df.to_csv(
    results_file,
    index=False
)

print("\n" + "=" * 75)
print("MODEL COMPARISON")
print("=" * 75)

print(
    results_df.to_string(index=False)
)

print(f"\nResults saved to:")
print(results_file)

print("\n" + "=" * 75)
print("MODEL TRAINING COMPLETE")
print("=" * 75)