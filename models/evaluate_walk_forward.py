import pandas as pd
import numpy as np

from pathlib import Path
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ============================================================
# FREIGHT PREDICTION
# Step 7A: Proper Walk-Forward Evaluation
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FEATURE_FILE = BASE_DIR / "data" / "multihorizon_model_dataset.csv"
RAW_FILE = BASE_DIR / "data" / "bdi_clean.csv"

OUTPUT_FILE = BASE_DIR / "data" / "walk_forward_results.csv"

VESSELS = ["HSI", "SI", "PI", "CI"]
HORIZONS = [7, 30, 60, 90]

# Number of evaluation dates.
# Using periodic evaluation keeps runtime reasonable.
EVALUATION_POINTS = 40

print("=" * 85)
print("FREIGHT PREDICTION - WALK-FORWARD EVALUATION")
print("=" * 85)

# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------

df = pd.read_csv(
    FEATURE_FILE,
    parse_dates=["Date"]
)

raw = pd.read_csv(
    RAW_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)
raw = raw.sort_values("Date").reset_index(drop=True)

print(f"\nFeature dataset: {df.shape}")
print(f"Raw dataset    : {raw.shape}")

# ------------------------------------------------------------
# 2. Target columns
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
# 3. Create mapping from source date to future target date
# ------------------------------------------------------------

raw_dates = raw["Date"].values

def get_future_date(current_date, horizon):
    """
    Returns the first available observation on/after
    current_date + horizon calendar days.
    """

    target_date = current_date + pd.Timedelta(days=horizon)

    position = np.searchsorted(
        raw_dates,
        np.datetime64(target_date),
        side="left"
    )

    if position >= len(raw):
        return pd.NaT

    return pd.Timestamp(raw_dates[position])


# Add target dates for every horizon
for horizon in HORIZONS:

    df[f"target_date_{horizon}d"] = df["Date"].apply(
        lambda x: get_future_date(x, horizon)
    )

# ------------------------------------------------------------
# 4. Select evaluation dates
# ------------------------------------------------------------
#
# Use dates late enough to have:
#   - sufficient training history
#   - complete future targets
#
# We evaluate periodically rather than every single day.

test_start = pd.Timestamp("2018-03-15")
test_end = pd.Timestamp("2019-04-01")

candidate_dates = df.loc[
    (df["Date"] >= test_start)
    & (df["Date"] <= test_end),
    "Date"
].unique()

if len(candidate_dates) > EVALUATION_POINTS:

    selected_indices = np.linspace(
        0,
        len(candidate_dates) - 1,
        EVALUATION_POINTS
    ).astype(int)

    evaluation_dates = [
        pd.Timestamp(candidate_dates[i])
        for i in selected_indices
    ]

else:

    evaluation_dates = [
        pd.Timestamp(x)
        for x in candidate_dates
    ]

print(
    f"\nEvaluation dates: {len(evaluation_dates)}"
)

print(
    f"Evaluation period: "
    f"{min(evaluation_dates).date()} → "
    f"{max(evaluation_dates).date()}"
)

# ------------------------------------------------------------
# 5. XGBoost settings
# ------------------------------------------------------------

model_params = {
    "n_estimators": 250,
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
# 6. Walk-forward loop
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

        actual_values = []
        naive_values = []
        xgb_values = []
        forecast_dates = []

        # ----------------------------------------------------
        # Evaluate each historical decision point
        # ----------------------------------------------------

        for evaluation_date in evaluation_dates:

            # Row corresponding to decision date
            decision_rows = df[
                df["Date"] == evaluation_date
            ]

            if decision_rows.empty:
                continue

            decision_row = decision_rows.iloc[0]

            # Future target must exist
            actual_value = decision_row[target]

            if pd.isna(actual_value):
                continue

            # ------------------------------------------------
            # Prevent target leakage
            #
            # A training row may only be used if its target
            # occurs ON or BEFORE the current evaluation date.
            # ------------------------------------------------

            train_mask = (
                (df["Date"] < evaluation_date)
                &
                (df[target_date_column] <= evaluation_date)
            )

            train_data = df.loc[
                train_mask
            ].copy()

            # Need enough observations
            if len(train_data) < 300:
                continue

            X_train = train_data[feature_columns]
            y_train = train_data[target]

            X_predict = pd.DataFrame(
                [decision_row[feature_columns].values],
                columns=feature_columns
            )

            # ------------------------------------------------
            # Naive baseline
            # ------------------------------------------------

            naive_prediction = float(
                decision_row[vessel]
            )

            # ------------------------------------------------
            # XGBoost
            # ------------------------------------------------

            model = XGBRegressor(
                **model_params
            )

            model.fit(
                X_train,
                y_train,
                verbose=False
            )

            prediction = float(
                model.predict(X_predict)[0]
            )

            actual_values.append(
                float(actual_value)
            )

            naive_values.append(
                naive_prediction
            )

            xgb_values.append(
                prediction
            )

            forecast_dates.append(
                evaluation_date
            )

        if len(actual_values) < 10:

            print(
                "Not enough valid evaluation points."
            )

            continue

        actual = np.array(actual_values)
        naive = np.array(naive_values)
        xgb = np.array(xgb_values)

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        naive_mae = mean_absolute_error(
            actual,
            naive
        )

        naive_rmse = np.sqrt(
            mean_squared_error(
                actual,
                naive
            )
        )

        naive_r2 = r2_score(
            actual,
            naive
        )

        xgb_mae = mean_absolute_error(
            actual,
            xgb
        )

        xgb_rmse = np.sqrt(
            mean_squared_error(
                actual,
                xgb
            )
        )

        xgb_r2 = r2_score(
            actual,
            xgb
        )

        # Safe MAPE
        non_zero = actual != 0

        xgb_mape = (
            np.mean(
                np.abs(
                    (actual[non_zero] - xgb[non_zero])
                    / actual[non_zero]
                )
            ) * 100
        )

        improvement = (
            (naive_mae - xgb_mae)
            / naive_mae
        ) * 100

        print(
            f"Evaluation points: {len(actual)}"
        )

        print(
            f"Naive MAE : {naive_mae:.2f}"
        )

        print(
            f"XGB MAE   : {xgb_mae:.2f}"
        )

        print(
            f"XGB RMSE  : {xgb_rmse:.2f}"
        )

        print(
            f"XGB R²    : {xgb_r2:.4f}"
        )

        print(
            f"XGB MAPE  : {xgb_mape:.2f}%"
        )

        print(
            f"Improvement: {improvement:.2f}%"
        )

        results.append({
            "vessel_type": vessel,
            "horizon_days": horizon,
            "evaluation_points": len(actual),
            "naive_mae": naive_mae,
            "naive_rmse": naive_rmse,
            "naive_r2": naive_r2,
            "xgb_mae": xgb_mae,
            "xgb_rmse": xgb_rmse,
            "xgb_r2": xgb_r2,
            "xgb_mape": xgb_mape,
            "improvement_percent": improvement
        })

# ------------------------------------------------------------
# 7. Save results
# ------------------------------------------------------------

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 85)
print("WALK-FORWARD RESULTS")
print("=" * 85)

print(
    results_df.to_string(index=False)
)

print("\nResults saved:")
print(OUTPUT_FILE)

print("\n" + "=" * 85)
print("WALK-FORWARD EVALUATION COMPLETE")
print("=" * 85)