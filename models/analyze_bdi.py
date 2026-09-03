import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# FREIGHT PREDICTION
# Step 3: Exploratory Time-Series Analysis
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FILE = BASE_DIR / "data" / "bdi_clean.csv"

# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------

df = pd.read_csv(FILE, parse_dates=["Date"])

df = df.sort_values("Date").reset_index(drop=True)

print("=" * 70)
print("FREIGHT PREDICTION - TIME SERIES ANALYSIS")
print("=" * 70)

print(f"\nRows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print(f"\nDate range:")
print(f"Start: {df['Date'].min().date()}")
print(f"End  : {df['Date'].max().date()}")

# ------------------------------------------------------------
# 2. Check date gaps
# ------------------------------------------------------------

date_diff = df["Date"].diff().dt.days.dropna()

print("\nDate gap analysis:")
print(date_diff.value_counts().sort_index())

print("\nMaximum gap between observations:",
      date_diff.max(), "days")

# ------------------------------------------------------------
# 3. Basic statistics
# ------------------------------------------------------------

vessel_columns = ["HSI", "SI", "PI", "CI"]

print("\nBasic statistics:")
print(df[vessel_columns].describe())

# ------------------------------------------------------------
# 4. Correlation
# ------------------------------------------------------------

print("\nCorrelation matrix:")
print(df[vessel_columns].corr())

# ------------------------------------------------------------
# 5. Volatility
# ------------------------------------------------------------

print("\nDaily percentage volatility:")

returns = df[vessel_columns].pct_change() * 100

print(returns.std())

# ------------------------------------------------------------
# 6. Highest and lowest values
# ------------------------------------------------------------

for column in vessel_columns:

    max_index = df[column].idxmax()
    min_index = df[column].idxmin()

    print(f"\n{column}")

    print(
        f"  Maximum: {df.loc[max_index, column]} "
        f"on {df.loc[max_index, 'Date'].date()}"
    )

    print(
        f"  Minimum: {df.loc[min_index, column]} "
        f"on {df.loc[min_index, 'Date'].date()}"
    )

# ------------------------------------------------------------
# 7. Monthly averages
# ------------------------------------------------------------

monthly = (
    df.set_index("Date")[vessel_columns]
      .resample("ME")
      .mean()
)

print("\nMonthly average sample:")
print(monthly.head(12))

# ------------------------------------------------------------
# 8. Yearly averages
# ------------------------------------------------------------

yearly = (
    df.set_index("Date")[vessel_columns]
      .resample("YE")
      .mean()
)

print("\nYearly averages:")
print(yearly)

# ------------------------------------------------------------
# 9. Plot all vessel indices
# ------------------------------------------------------------

plt.figure(figsize=(14, 7))

for column in vessel_columns:
    plt.plot(
        df["Date"],
        df[column],
        label=column
    )

plt.title("Baltic Vessel Indices Over Time")
plt.xlabel("Date")
plt.ylabel("Index Value")
plt.legend()
plt.grid(True)

plt.tight_layout()

output = BASE_DIR / "data" / "bdi_all_indices.png"

plt.savefig(output, dpi=150)
plt.show()

print(f"\nChart saved to:")
print(output)

# ------------------------------------------------------------
# 10. Individual plots
# ------------------------------------------------------------

for column in vessel_columns:

    plt.figure(figsize=(14, 6))

    plt.plot(
        df["Date"],
        df[column]
    )

    plt.title(f"{column} Historical Time Series")
    plt.xlabel("Date")
    plt.ylabel("Index Value")
    plt.grid(True)

    plt.tight_layout()

    output = BASE_DIR / "data" / f"{column}_history.png"

    plt.savefig(output, dpi=150)

    plt.close()

    print(f"Saved: {output}")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)