import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# FREIGHT PREDICTION
# Step 8A: Optimized Multi-Horizon Feature Engineering
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "forecast_dataset.csv"
OUTPUT_FILE = BASE_DIR / "data" / "multihorizon_model_dataset.csv"

VESSELS = ["HSI", "SI", "PI", "CI"]
HORIZONS = [7, 30, 60, 90]

print("=" * 75)
print("FREIGHT PREDICTION - OPTIMIZED MULTI-HORIZON FEATURES")
print("=" * 75)

# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)

print(f"\nOriginal rows: {len(df)}")

# ------------------------------------------------------------
# 2. Keep trusted columns
# ------------------------------------------------------------

target_columns = [
    f"{vessel}_target_{horizon}d"
    for vessel in VESSELS
    for horizon in HORIZONS
]

base_columns = [
    "Date",
    "HSI",
    "SI",
    "PI",
    "CI",
    "DTI"
]

df = df[base_columns + target_columns].copy()

# ------------------------------------------------------------
# 3. Calendar features
# ------------------------------------------------------------

calendar_features = pd.DataFrame(index=df.index)

calendar_features["day_of_week"] = df["Date"].dt.dayofweek
calendar_features["month"] = df["Date"].dt.month
calendar_features["quarter"] = df["Date"].dt.quarter
calendar_features["year"] = df["Date"].dt.year

# Cyclical month encoding
calendar_features["month_sin"] = np.sin(
    2 * np.pi * calendar_features["month"] / 12
)

calendar_features["month_cos"] = np.cos(
    2 * np.pi * calendar_features["month"] / 12
)

# ------------------------------------------------------------
# 4. Lag features
# ------------------------------------------------------------

lag_features = pd.DataFrame(index=df.index)

for vessel in VESSELS:

    for lag in [1, 2, 3, 7, 14, 30, 60, 90]:

        lag_features[f"{vessel}_lag_{lag}"] = (
            df[vessel].shift(lag)
        )

# ------------------------------------------------------------
# 5. Rolling statistics
# ------------------------------------------------------------

rolling_features = pd.DataFrame(index=df.index)

for vessel in VESSELS:

    for window in [7, 14, 30, 60, 90]:

        series = df[vessel]

        rolling_features[
            f"{vessel}_rolling_mean_{window}"
        ] = series.rolling(window).mean()

        rolling_features[
            f"{vessel}_rolling_std_{window}"
        ] = series.rolling(window).std()

        rolling_features[
            f"{vessel}_rolling_min_{window}"
        ] = series.rolling(window).min()

        rolling_features[
            f"{vessel}_rolling_max_{window}"
        ] = series.rolling(window).max()

# ------------------------------------------------------------
# 6. Momentum features
# ------------------------------------------------------------

momentum_features = pd.DataFrame(index=df.index)

for vessel in VESSELS:

    series = df[vessel]

    momentum_features[f"{vessel}_change_1"] = (
        series - series.shift(1)
    )

    momentum_features[f"{vessel}_change_7"] = (
        series - series.shift(7)
    )

    momentum_features[f"{vessel}_change_30"] = (
        series - series.shift(30)
    )

    momentum_features[f"{vessel}_pct_change_1"] = (
        series.pct_change(1)
    )

    momentum_features[f"{vessel}_pct_change_7"] = (
        series.pct_change(7)
    )

    momentum_features[f"{vessel}_pct_change_30"] = (
        series.pct_change(30)
    )

# ------------------------------------------------------------
# 7. Cross-vessel features
# ------------------------------------------------------------

cross_features = pd.DataFrame(index=df.index)

cross_features["HSI_SI_ratio"] = df["HSI"] / df["SI"]
cross_features["SI_PI_ratio"] = df["SI"] / df["PI"]
cross_features["PI_CI_ratio"] = df["PI"] / df["CI"]

cross_features["HSI_SI_spread"] = df["HSI"] - df["SI"]
cross_features["SI_PI_spread"] = df["SI"] - df["PI"]
cross_features["PI_CI_spread"] = df["PI"] - df["CI"]

# ------------------------------------------------------------
# 8. Combine all features at once
# ------------------------------------------------------------

df = pd.concat(
    [
        df,
        calendar_features,
        lag_features,
        rolling_features,
        momentum_features,
        cross_features
    ],
    axis=1
)

# ------------------------------------------------------------
# 9. Remove incomplete rows
# ------------------------------------------------------------

before = len(df)

feature_columns = [
    column
    for column in df.columns
    if column not in target_columns
    and column != "Date"
]

df = df.dropna(
    subset=feature_columns + target_columns
).reset_index(drop=True)

after = len(df)

print(
    f"\nRows removed: {before - after}"
)

print(f"Final rows: {after}")

# ------------------------------------------------------------
# 10. Validate
# ------------------------------------------------------------

missing_total = int(df.isna().sum().sum())

print(
    f"Total missing values: {missing_total}"
)

if missing_total != 0:
    raise ValueError(
        "Dataset still contains missing values."
    )

# Check duplicate dates
duplicates = df["Date"].duplicated().sum()

print(
    f"Duplicate dates: {duplicates}"
)

if duplicates != 0:
    raise ValueError(
        "Duplicate dates detected."
    )

# ------------------------------------------------------------
# 11. Save
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(f"\nSaved:")
print(OUTPUT_FILE)

print(
    f"\nFinal columns: {len(df.columns)}"
)

print(
    f"Feature columns: {len(feature_columns)}"
)

print("\nDate range:")
print(
    f"{df['Date'].min().date()} → "
    f"{df['Date'].max().date()}"
)

print("\n" + "=" * 75)
print("OPTIMIZED FEATURE ENGINEERING COMPLETE")
print("=" * 75)