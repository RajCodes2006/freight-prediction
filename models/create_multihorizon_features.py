import pandas as pd
from pathlib import Path

# ============================================================
# FREIGHT PREDICTION
# Step 6B: Multi-Horizon Feature Engineering
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "forecast_dataset.csv"
OUTPUT_FILE = BASE_DIR / "data" / "multihorizon_model_dataset.csv"

VESSELS = ["HSI", "SI", "PI", "CI"]
HORIZONS = [7, 30, 60, 90]

print("=" * 75)
print("FREIGHT PREDICTION - MULTI-HORIZON FEATURE ENGINEERING")
print("=" * 75)

# ------------------------------------------------------------
# 1. Load target dataset
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)

print(f"\nOriginal rows: {len(df)}")

# ------------------------------------------------------------
# 2. Keep trusted current market variables
# ------------------------------------------------------------

df = df[
    [
        "Date",
        "HSI",
        "SI",
        "PI",
        "CI",
        "DTI"
    ]
    + [
        f"{vessel}_target_{horizon}d"
        for vessel in VESSELS
        for horizon in HORIZONS
    ]
].copy()

# ------------------------------------------------------------
# 3. Calendar features
# ------------------------------------------------------------

df["day_of_week"] = df["Date"].dt.dayofweek
df["month"] = df["Date"].dt.month
df["quarter"] = df["Date"].dt.quarter
df["year"] = df["Date"].dt.year

# Cyclical calendar encoding
df["month_sin"] = (
    __import__("numpy").sin(
        2 * __import__("numpy").pi * df["month"] / 12
    )
)

df["month_cos"] = (
    __import__("numpy").cos(
        2 * __import__("numpy").pi * df["month"] / 12
    )
)

# ------------------------------------------------------------
# 4. Lag features
# ------------------------------------------------------------

for vessel in VESSELS:

    for lag in [1, 2, 3, 7, 14, 30, 60, 90]:

        df[f"{vessel}_lag_{lag}"] = (
            df[vessel].shift(lag)
        )

# ------------------------------------------------------------
# 5. Rolling statistics
# ------------------------------------------------------------

for vessel in VESSELS:

    for window in [7, 14, 30, 60, 90]:

        df[f"{vessel}_rolling_mean_{window}"] = (
            df[vessel]
            .rolling(window)
            .mean()
        )

        df[f"{vessel}_rolling_std_{window}"] = (
            df[vessel]
            .rolling(window)
            .std()
        )

        df[f"{vessel}_rolling_min_{window}"] = (
            df[vessel]
            .rolling(window)
            .min()
        )

        df[f"{vessel}_rolling_max_{window}"] = (
            df[vessel]
            .rolling(window)
            .max()
        )

# ------------------------------------------------------------
# 6. Momentum features
# ------------------------------------------------------------

for vessel in VESSELS:

    df[f"{vessel}_change_1"] = (
        df[vessel] - df[vessel].shift(1)
    )

    df[f"{vessel}_change_7"] = (
        df[vessel] - df[vessel].shift(7)
    )

    df[f"{vessel}_change_30"] = (
        df[vessel] - df[vessel].shift(30)
    )

    df[f"{vessel}_pct_change_1"] = (
        df[vessel].pct_change(1)
    )

    df[f"{vessel}_pct_change_7"] = (
        df[vessel].pct_change(7)
    )

    df[f"{vessel}_pct_change_30"] = (
        df[vessel].pct_change(30)
    )

# ------------------------------------------------------------
# 7. Cross-vessel relationships
# ------------------------------------------------------------

df["HSI_SI_ratio"] = df["HSI"] / df["SI"]
df["SI_PI_ratio"] = df["SI"] / df["PI"]
df["PI_CI_ratio"] = df["PI"] / df["CI"]

df["HSI_SI_spread"] = df["HSI"] - df["SI"]
df["SI_PI_spread"] = df["SI"] - df["PI"]
df["PI_CI_spread"] = df["PI"] - df["CI"]

# ------------------------------------------------------------
# 8. Remove incomplete feature rows
# ------------------------------------------------------------

before = len(df)

# Only feature columns, not targets, determine whether a row
# has enough historical information.

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

df = df.dropna(
    subset=feature_columns + target_columns
).reset_index(drop=True)

after = len(df)

print(
    f"\nRows removed because of insufficient historical/future data: "
    f"{before - after}"
)

print(f"Final rows: {after}")

# ------------------------------------------------------------
# 9. Verify missing values
# ------------------------------------------------------------

missing_total = df.isna().sum().sum()

print(f"\nTotal missing values: {missing_total}")

if missing_total != 0:
    raise ValueError(
        "Dataset still contains missing values."
    )

# ------------------------------------------------------------
# 10. Save
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(f"\nSaved:")
print(OUTPUT_FILE)

print(f"\nFinal columns: {len(df.columns)}")

# ------------------------------------------------------------
# 11. Print target columns
# ------------------------------------------------------------

print("\nTarget columns:")

for column in target_columns:
    print(f"  {column}")

# ------------------------------------------------------------
# 12. Preview
# ------------------------------------------------------------

preview_columns = [
    "Date",
    "HSI",
    "SI",
    "PI",
    "CI",
    "HSI_target_7d",
    "HSI_target_30d",
    "HSI_target_60d",
    "HSI_target_90d",
    "PI_target_7d",
    "PI_target_30d",
    "PI_target_60d",
    "PI_target_90d"
]

print("\nDataset preview:")
print(
    df[preview_columns]
    .head(10)
    .to_string(index=False)
)

print("\n" + "=" * 75)
print("MULTI-HORIZON FEATURE ENGINEERING COMPLETE")
print("=" * 75)