import pandas as pd
from pathlib import Path

# ============================================================
# FREIGHT PREDICTION
# Step 5A: Corrected Feature Engineering
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "bdi_clean.csv"
OUTPUT_FILE = BASE_DIR / "data" / "model_dataset.csv"

VESSELS = ["HSI", "SI", "PI", "CI"]

print("=" * 70)
print("FREIGHT PREDICTION - CORRECTED FEATURE ENGINEERING")
print("=" * 70)

# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE, parse_dates=["Date"])

df = df.sort_values("Date").reset_index(drop=True)

# ------------------------------------------------------------
# 2. Keep ONLY variables we currently trust
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
].copy()

print(f"\nOriginal rows: {len(df)}")

# ------------------------------------------------------------
# 3. Calendar features
# ------------------------------------------------------------

df["day_of_week"] = df["Date"].dt.dayofweek
df["month"] = df["Date"].dt.month
df["quarter"] = df["Date"].dt.quarter
df["year"] = df["Date"].dt.year

# ------------------------------------------------------------
# 4. Lag features
# ------------------------------------------------------------

for vessel in VESSELS:

    for lag in [1, 2, 3, 7, 14, 30]:

        df[f"{vessel}_lag_{lag}"] = df[vessel].shift(lag)

# ------------------------------------------------------------
# 5. Rolling statistics
# ------------------------------------------------------------

for vessel in VESSELS:

    for window in [7, 14, 30]:

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

# ------------------------------------------------------------
# 6. Percentage changes
# ------------------------------------------------------------

for vessel in VESSELS:

    df[f"{vessel}_pct_change_1"] = (
        df[vessel].pct_change(1)
    )

    df[f"{vessel}_pct_change_7"] = (
        df[vessel].pct_change(7)
    )

# ------------------------------------------------------------
# 7. Future target
# ------------------------------------------------------------

# Predict the NEXT AVAILABLE observation.
for vessel in VESSELS:

    df[f"{vessel}_target"] = df[vessel].shift(-1)

# ------------------------------------------------------------
# 8. Remove rows made incomplete by feature engineering
# ------------------------------------------------------------

before = len(df)

df = df.dropna().reset_index(drop=True)

after = len(df)

print(f"\nRows removed because of lag/rolling/target:")
print(before - after)

print(f"Final rows: {after}")

# ------------------------------------------------------------
# 9. Save
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(f"\nSaved:")
print(OUTPUT_FILE)

print(f"\nFinal columns: {len(df.columns)}")

print("\nMissing values:")
print(df.isna().sum().sum())

print("\nDate range:")
print(f"Start: {df['Date'].min().date()}")
print(f"End  : {df['Date'].max().date()}")

print("\n" + "=" * 70)
print("CORRECTED FEATURE ENGINEERING COMPLETE")
print("=" * 70)