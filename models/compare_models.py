import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# ============================================================
# FREIGHT PREDICTION
# Step 8B: Model Competition
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "multihorizon_model_dataset.csv"
OUTPUT_FILE = BASE_DIR / "data" / "model_competition_results.csv"

VESSELS = ["HSI", "SI", "PI", "CI"]
HORIZONS = [7, 30, 60, 90]

# Number of historical decision points to evaluate
EVALUATION_POINTS = 30

print("=" * 85)
print("FREIGHT PREDICTION - MODEL COMPETITION")
print("=" * 85)

# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)

print(f"\nDataset shape: {df.shape}")
print(
    f"Date range: "
    f"{df['Date'].min().date()} → "
    f"{df['Date'].max().date()}"
)

# ------------------------------------------------------------
# 2. Identify targets and features
# ------------------------------------------------------------

target_columns = [
    f"{vessel}_target_{horizon}d"
    for vessel in VESSELS
    for horizon in HORIZONS
]

feature_columns = [
    column
    for column in df.columns
    if column not in target_columns
    and column != "Date"
]

print(f"Number of features: {len(feature_columns)}")

# ------------------------------------------------------------
# 3. Create future target dates
# ------------------------------------------------------------

date_array = df["Date"].values


def future_observation_date(current_date, horizon):
    target_date = (
        current_date
        + pd.Timedelta(days=horizon)
    )

    idx = np.searchsorted(
        date_array,
        np.datetime64(target_date),
        side="left"
    )

    if idx >= len(df):
        return pd.NaT

    return pd.Timestamp(date_array[idx])


for horizon in HORIZONS:
    df[f"target_date_{horizon}d"] = [
        future_observation_date(date, horizon)
        for date in df["Date"]
    ]

# ------------------------------------------------------------
# 4. Select evaluation dates
# ------------------------------------------------------------

candidate_dates = df.loc[
    (df["Date"] >= pd.Timestamp("2018-03-15"))
    & (df["Date"] <= pd.Timestamp("2019-04-01")),
    "Date"
].unique()

if len(candidate_dates) > EVALUATION_POINTS:

    indices = np.linspace(
        0,
        len(candidate_dates) - 1,
        EVALUATION_POINTS
    ).astype(int)

    evaluation_dates = [
        pd.Timestamp(candidate_dates[i])
        for i in indices
    ]

else:

    evaluation_dates = [
        pd.Timestamp(date)
        for date in candidate_dates
    ]

print(
    f"\nEvaluation points: {len(evaluation_dates)}"
)

# ------------------------------------------------------------
# 5. Model factory
# ------------------------------------------------------------

def create_models():

    return {
        "XGBoost": XGBRegressor(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1
        ),

        "RandomForest": RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ),

        "LightGBM": LGBMRegressor(
            n_estimators=250,
            max_depth=5,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=-1,
            n_jobs=-1
        )
    }


results = []

# ------------------------------------------------------------
# 6. Walk-forward model comparison
# ------------------------------------------------------------

for vessel in VESSELS:

    print("\n" + "=" * 85)
    print(f"VESSEL: {vessel}")
    print("=" * 85)

    for horizon in HORIZONS:

        target = f"{vessel}_target_{horizon}d"
        target_date_column = f"target_date_{horizon}d"

        print(
            f"\n--- {vessel} | {horizon}-DAY ---"
        )

        predictions = {
            "Naive": [],
            "XGBoost": [],
            "RandomForest": [],
            "LightGBM": []
        }

        actual_values = []

        for evaluation_date in evaluation_dates:

            decision_rows = df[
                df["Date"] == evaluation_date
            ]

            if decision_rows.empty:
                continue

            decision_row = decision_rows.iloc[0]

            if pd.isna(decision_row[target]):
                continue

            # ------------------------------------------------
            # Leakage-safe training data
            # ------------------------------------------------

            train_mask = (
                (df["Date"] < evaluation_date)
                &
                (df[target_date_column] <= evaluation_date)
            )

            train_data = df.loc[
                train_mask
            ].copy()

            if len(train_data) < 300:
                continue

            X_train = train_data[feature_columns]
            y_train = train_data[target]

            X_test = pd.DataFrame(
                [decision_row[feature_columns].values],
                columns=feature_columns
            )

            actual = float(
                decision_row[target]
            )

            actual_values.append(actual)

            # ------------------------------------------------
            # Naive prediction
            # ------------------------------------------------

            predictions["Naive"].append(
                float(decision_row[vessel])
            )

            # ------------------------------------------------
            # Train ML models
            # ------------------------------------------------

            models = create_models()

            for model_name, model in models.items():

                model.fit(
                    X_train,
                    y_train
                )

                prediction = float(
                    model.predict(X_test)[0]
                )

                predictions[model_name].append(
                    prediction
                )

        # ----------------------------------------------------
        # Calculate metrics
        # ----------------------------------------------------

        if len(actual_values) < 10:

            print("Not enough evaluation points.")
            continue

        actual = np.array(actual_values)

        for model_name, model_predictions in predictions.items():

            predicted = np.array(
                model_predictions
            )

            mae = mean_absolute_error(
                actual,
                predicted
            )

            rmse = np.sqrt(
                mean_squared_error(
                    actual,
                    predicted
                )
            )

            r2 = r2_score(
                actual,
                predicted
            )

            non_zero = actual != 0

            mape = (
                np.mean(
                    np.abs(
                        (
                            actual[non_zero]
                            - predicted[non_zero]
                        )
                        / actual[non_zero]
                    )
                ) * 100
            )

            results.append({
                "vessel_type": vessel,
                "horizon_days": horizon,
                "model": model_name,
                "evaluation_points": len(actual),
                "mae": mae,
                "rmse": rmse,
                "r2": r2,
                "mape": mape
            })

            print(
                f"{model_name:12} "
                f"MAE={mae:8.2f} "
                f"RMSE={rmse:8.2f} "
                f"R²={r2:7.4f} "
                f"MAPE={mape:7.2f}%"
            )

# ------------------------------------------------------------
# 7. Save results
# ------------------------------------------------------------

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ------------------------------------------------------------
# 8. Best model for every vessel/horizon
# ------------------------------------------------------------

print("\n" + "=" * 85)
print("BEST MODEL BY VESSEL / HORIZON")
print("=" * 85)

for vessel in VESSELS:

    for horizon in HORIZONS:

        subset = results_df[
            (results_df["vessel_type"] == vessel)
            &
            (results_df["horizon_days"] == horizon)
        ]

        if subset.empty:
            continue

        best = subset.loc[
            subset["mae"].idxmin()
        ]

        print(
            f"{vessel:10} "
            f"{horizon:3}d → "
            f"{best['model']:12} "
            f"MAE={best['mae']:.2f}"
        )

print("\nResults saved:")
print(OUTPUT_FILE)

print("\n" + "=" * 85)
print("MODEL COMPETITION COMPLETE")
print("=" * 85)