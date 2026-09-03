import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ============================================================
# FREIGHT PREDICTION
# Step 6C: Multi-Horizon Model Training
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "multihorizon_model_dataset.csv"
MODEL_DIR = BASE_DIR / "models" / "saved_multihorizon"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

VESSELS = ["HSI", "SI", "PI", "CI"]
HORIZONS = [7, 30, 60, 90]

print("=" * 80)
print("FREIGHT PREDICTION - MULTI-HORIZON MODEL TRAINING")
print("=" * 80)

# ------------------------------------------------------------
# 1. Load dataset
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)

print(f"\nDataset shape: {df.shape}")
print(
    f"Date range: "
    f"{df['Date'].min().date()} → {df['Date'].max().date()}"
)

# ------------------------------------------------------------
# 2. Identify targets
# ------------------------------------------------------------

target_columns = [
    f"{vessel}_target_{horizon}d"
    for vessel in VESSELS
    for horizon in HORIZONS
]

# Never use future target columns as features
feature_columns = [
    column
    for column in df.columns
    if column not in target_columns
    and column != "Date"
]

print(f"\nNumber of features: {len(feature_columns)}")

# ------------------------------------------------------------
# 3. Chronological split
# ------------------------------------------------------------

split_index = int(len(df) * 0.80)

train_df = df.iloc[:split_index].copy()
test_df = df.iloc[split_index:].copy()

print("\nTrain/Test split:")

print(
    f"Train: "
    f"{train_df['Date'].min().date()} → "
    f"{train_df['Date'].max().date()}"
)

print(
    f"Test : "
    f"{test_df['Date'].min().date()} → "
    f"{test_df['Date'].max().date()}"
)

# ------------------------------------------------------------
# 4. Model parameters
# ------------------------------------------------------------

model_params = {
    "n_estimators": 400,
    "max_depth": 4,
    "learning_rate": 0.03,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "random_state": 42,
    "n_jobs": -1
}

results = []

# ------------------------------------------------------------
# 5. Train 16 models
# ------------------------------------------------------------

for vessel in VESSELS:

    print("\n" + "=" * 80)
    print(f"VESSEL TYPE: {vessel}")
    print("=" * 80)

    for horizon in HORIZONS:

        target = f"{vessel}_target_{horizon}d"

        print(
            f"\n--- {vessel} | {horizon}-DAY FORECAST ---"
        )

        X_train = train_df[feature_columns]
        X_test = test_df[feature_columns]

        y_train = train_df[target]
        y_test = test_df[target]

        # ----------------------------------------------------
        # Naive baseline
        # ----------------------------------------------------
        # Use today's value as the future prediction.

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

        # ----------------------------------------------------
        # XGBoost
        # ----------------------------------------------------

        model = XGBRegressor(**model_params)

        model.fit(
            X_train,
            y_train,
            verbose=False
        )

        predictions = model.predict(X_test)

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

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

        # Safe MAPE
        y_test_array = np.asarray(y_test)

        non_zero = y_test_array != 0

        mape = (
            np.mean(
                np.abs(
                    (
                        y_test_array[non_zero]
                        - predictions[non_zero]
                    )
                    / y_test_array[non_zero]
                )
            )
            * 100
        )

        # Improvement in MAE
        improvement = (
            (baseline_mae - mae)
            / baseline_mae
        ) * 100

        print("\nBaseline:")
        print(f"  MAE  : {baseline_mae:.2f}")
        print(f"  RMSE : {baseline_rmse:.2f}")
        print(f"  R²   : {baseline_r2:.4f}")

        print("\nXGBoost:")
        print(f"  MAE  : {mae:.2f}")
        print(f"  RMSE : {rmse:.2f}")
        print(f"  R²   : {r2:.4f}")
        print(f"  MAPE : {mape:.2f}%")

        print(
            f"\nImprovement over baseline: "
            f"{improvement:.2f}%"
        )

        # ----------------------------------------------------
        # Save model
        # ----------------------------------------------------

        model_file = (
            MODEL_DIR
            / f"{vessel.lower()}_{horizon}d_xgboost.joblib"
        )

        joblib.dump(
            model,
            model_file
        )

        print(f"Model saved: {model_file}")

        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        results.append({
            "vessel_type": vessel,
            "horizon_days": horizon,
            "baseline_mae": baseline_mae,
            "baseline_rmse": baseline_rmse,
            "baseline_r2": baseline_r2,
            "xgb_mae": mae,
            "xgb_rmse": rmse,
            "xgb_r2": r2,
            "xgb_mape": mape,
            "improvement_percent": improvement
        })

# ------------------------------------------------------------
# 6. Results dataframe
# ------------------------------------------------------------

results_df = pd.DataFrame(results)

RESULT_FILE = BASE_DIR / "data" / "multihorizon_model_results.csv"

results_df.to_csv(
    RESULT_FILE,
    index=False
)

# ------------------------------------------------------------
# 7. Print summary
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("MULTI-HORIZON MODEL COMPARISON")
print("=" * 80)

print(
    results_df.to_string(index=False)
)

# ------------------------------------------------------------
# 8. Best models
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("BEST MODEL BY HORIZON")
print("=" * 80)

for horizon in HORIZONS:

    horizon_df = results_df[
        results_df["horizon_days"] == horizon
    ]

    best = horizon_df.loc[
        horizon_df["improvement_percent"].idxmax()
    ]

    print(
        f"{horizon:>3} days → "
        f"{best['vessel_type']} | "
        f"Improvement: "
        f"{best['improvement_percent']:.2f}%"
    )

print("\nResults saved:")
print(RESULT_FILE)

print("\n" + "=" * 80)
print("MULTI-HORIZON MODEL TRAINING COMPLETE")
print("=" * 80)