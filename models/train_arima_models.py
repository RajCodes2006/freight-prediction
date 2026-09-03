import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ============================================================
# FREIGHT PREDICTION
# Step 7A: ARIMA Multi-Horizon Benchmark
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "bdi_clean.csv"
MODEL_DIR = BASE_DIR / "models" / "saved_arima"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

VESSELS = ["HSI", "SI", "PI", "CI"]
HORIZONS = [7, 30, 60, 90]

print("=" * 80)
print("FREIGHT PREDICTION - ARIMA MULTI-HORIZON BENCHMARK")
print("=" * 80)

# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)

# ------------------------------------------------------------
# Chronological train/test split
# ------------------------------------------------------------

split_index = int(len(df) * 0.80)

train_df = df.iloc[:split_index].copy()
test_df = df.iloc[split_index:].copy()

print(
    f"\nTrain: {train_df['Date'].min().date()} → "
    f"{train_df['Date'].max().date()}"
)

print(
    f"Test : {test_df['Date'].min().date()} → "
    f"{test_df['Date'].max().date()}"
)

results = []

# ------------------------------------------------------------
# Train/test each vessel
# ------------------------------------------------------------

for vessel in VESSELS:

    print("\n" + "=" * 80)
    print(f"VESSEL: {vessel}")
    print("=" * 80)

    train_series = train_df[vessel].astype(float)

    test_series = test_df[vessel].astype(float)

    for horizon in HORIZONS:

        print(f"\n--- {vessel} | {horizon}-DAY FORECAST ---")

        # ----------------------------------------------------
        # Create evaluation target
        # ----------------------------------------------------
        #
        # For each test date, compare the forecast horizon ahead.
        # We use the first available observation at/after the
        # requested calendar horizon.

        actual_dates = []
        actual_values = []

        test_dates = test_df["Date"].tolist()

        all_dates = df["Date"]

        for current_date in test_dates:

            target_date = current_date + pd.Timedelta(days=horizon)

            future = df.loc[
                df["Date"] >= target_date,
                ["Date", vessel]
            ]

            if future.empty:
                continue

            actual_dates.append(current_date)
            actual_values.append(
                future.iloc[0][vessel]
            )

        actual = np.array(actual_values, dtype=float)

        if len(actual) == 0:
            print("No evaluation data available.")
            continue

        # ----------------------------------------------------
        # ARIMA forecast
        # ----------------------------------------------------
        #
        # A simple ARIMA(5,1,0) benchmark.
        # We deliberately start simple instead of blindly
        # searching dozens of models.

        try:

            model = ARIMA(
                train_series,
                order=(5, 1, 0)
            )

            fitted = model.fit()

            # Forecast enough steps to cover the horizon.
            forecast = fitted.forecast(
                steps=horizon
            )

            # Use the final forecast value as the horizon estimate.
            predicted_value = float(forecast.iloc[-1])

            predictions = np.repeat(
                predicted_value,
                len(actual)
            )

            mae = mean_absolute_error(
                actual,
                predictions
            )

            rmse = np.sqrt(
                mean_squared_error(
                    actual,
                    predictions
                )
            )

            r2 = r2_score(
                actual,
                predictions
            )

            print(f"ARIMA MAE  : {mae:.2f}")
            print(f"ARIMA RMSE : {rmse:.2f}")
            print(f"ARIMA R²   : {r2:.4f}")

            results.append({
                "vessel_type": vessel,
                "horizon_days": horizon,
                "arima_mae": mae,
                "arima_rmse": rmse,
                "arima_r2": r2
            })

            # Save fitted model
            model_file = (
                MODEL_DIR /
                f"{vessel.lower()}_{horizon}d_arima.joblib"
            )

            joblib.dump(
                fitted,
                model_file
            )

            print(f"Saved: {model_file}")

        except Exception as e:

            print(f"ARIMA failed: {e}")

# ------------------------------------------------------------
# Save results
# ------------------------------------------------------------

results_df = pd.DataFrame(results)

RESULT_FILE = (
    BASE_DIR /
    "data" /
    "arima_model_results.csv"
)

results_df.to_csv(
    RESULT_FILE,
    index=False
)

print("\n" + "=" * 80)
print("ARIMA RESULTS")
print("=" * 80)

print(results_df.to_string(index=False))

print(f"\nResults saved:")
print(RESULT_FILE)

print("\n" + "=" * 80)
print("ARIMA BENCHMARK COMPLETE")
print("=" * 80)