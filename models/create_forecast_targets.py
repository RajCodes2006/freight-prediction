import pandas as pd
from pathlib import Path

# ============================================================
# FREIGHT PREDICTION
# Step 6A: Create Multi-Horizon Forecast Dataset
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "bdi_clean.csv"
OUTPUT_FILE = BASE_DIR / "data" / "forecast_dataset.csv"

VESSELS = ["HSI", "SI", "PI", "CI"]

# Forecast horizons in calendar days
HORIZONS = [7, 30, 60, 90]

print("=" * 70)
print("FREIGHT PREDICTION - MULTI-HORIZON TARGET CREATION")
print("=" * 70)

# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["Date"]
)

df = df.sort_values("Date").reset_index(drop=True)

# We don't need CTI for this stage
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
# 2. Create future targets
# ------------------------------------------------------------
# IMPORTANT:
# The source data contains business/assessment days, not every
# calendar day. Therefore we use the next observation on/after
# the requested calendar horizon rather than pretending every
# calendar date has an index value.

for vessel in VESSELS:

    for horizon in HORIZONS:

        target_name = f"{vessel}_target_{horizon}d"

        target_values = []

        dates = df["Date"]

        for current_date in dates:

            future_date = current_date + pd.Timedelta(days=horizon)

            future_rows = df.loc[
                df["Date"] >= future_date,
                vessel
            ]

            if future_rows.empty:
                target_values.append(None)
            else:
                target_values.append(future_rows.iloc[0])

        df[target_name] = target_values

# ------------------------------------------------------------
# 3. Remove rows without all requested targets
# ------------------------------------------------------------

target_columns = [
    f"{vessel}_target_{horizon}d"
    for vessel in VESSELS
    for horizon in HORIZONS
]

before = len(df)

df = df.dropna(
    subset=target_columns
).reset_index(drop=True)

after = len(df)

print(
    f"\nRows removed because future target was unavailable: "
    f"{before - after}"
)

print(f"Final rows: {after}")

# ------------------------------------------------------------
# 4. Save
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(f"\nSaved:")
print(OUTPUT_FILE)

# ------------------------------------------------------------
# 5. Display target columns
# ------------------------------------------------------------

print("\nForecast targets:")

for column in target_columns:
    print(f"  {column}")

# ------------------------------------------------------------
# 6. Sample
# ------------------------------------------------------------

print("\nSample target values:")

display_columns = [
    "Date",
    "HSI",
    "SI",
    "PI",
    "CI",
    "HSI_target_7d",
    "HSI_target_30d",
    "HSI_target_60d",
    "HSI_target_90d"
]

print(
    df[display_columns]
    .head(10)
    .to_string(index=False)
)

print("\n" + "=" * 70)
print("MULTI-HORIZON TARGET CREATION COMPLETE")
print("=" * 70)