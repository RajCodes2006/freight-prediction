import pandas as pd
from pathlib import Path

# ============================================================
# FREIGHT PREDICTION
# Step 2A: Clean BDI Dataset
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "edited BDI data1.xls"

OUTPUT_WIDE = BASE_DIR / "data" / "bdi_clean.csv"
OUTPUT_LONG = BASE_DIR / "data" / "freight_rates.csv"

print("=" * 60)
print("FREIGHT PREDICTION - BDI DATA CLEANING")
print("=" * 60)

# ------------------------------------------------------------
# 1. Check input file
# ------------------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

# ------------------------------------------------------------
# 2. Read main BDI sheet
# ------------------------------------------------------------

df = pd.read_excel(
    INPUT_FILE,
    sheet_name="MASTER EXCEL SHEET BDI ",
    engine="xlrd"
)

print(f"\nOriginal shape: {df.shape}")

# ------------------------------------------------------------
# 3. Keep relevant columns
# ------------------------------------------------------------

required_columns = [
    "Date",
    "HSI",
    "SI",
    "PI",
    "CI",
    "DTI",
    "CTI"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

df = df[required_columns].copy()

# ------------------------------------------------------------
# 4. Convert Date from text to datetime
# ------------------------------------------------------------

df["Date"] = pd.to_datetime(
    df["Date"],
    format="%b %d, %Y",
    errors="coerce"
)

# Check invalid dates
invalid_dates = df["Date"].isna().sum()

print(f"Invalid dates: {invalid_dates}")

if invalid_dates > 0:
    print("Removing rows with invalid dates...")
    df = df.dropna(subset=["Date"])

# ------------------------------------------------------------
# 5. Convert numeric columns
# ------------------------------------------------------------

numeric_columns = [
    "HSI",
    "SI",
    "PI",
    "CI",
    "DTI",
    "CTI"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

# ------------------------------------------------------------
# 6. Sort chronologically
# ------------------------------------------------------------

df = df.sort_values("Date").reset_index(drop=True)

# ------------------------------------------------------------
# 7. Remove duplicate dates
# ------------------------------------------------------------

duplicates = df["Date"].duplicated().sum()

print(f"Duplicate dates: {duplicates}")

if duplicates > 0:
    df = df.drop_duplicates(
        subset=["Date"],
        keep="last"
    ).reset_index(drop=True)

# ------------------------------------------------------------
# 8. Show missing values
# ------------------------------------------------------------

print("\nMissing values:")
print(df.isna().sum())

# ------------------------------------------------------------
# 9. Save cleaned wide-format dataset
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_WIDE,
    index=False
)

print(f"\nSaved wide dataset:")
print(OUTPUT_WIDE)

# ------------------------------------------------------------
# 10. Create long-format freight dataset
# ------------------------------------------------------------

vessel_columns = {
    "HSI": "Handysize",
    "SI": "Supramax",
    "PI": "Panamax",
    "CI": "Capesize"
}

records = []

for index_column, vessel_type in vessel_columns.items():

    temp = df[["Date", index_column]].copy()

    temp = temp.rename(
        columns={
            "Date": "date",
            index_column: "freight_index"
        }
    )

    temp["vessel_type"] = vessel_type

    # Remove missing index values
    temp = temp.dropna(subset=["freight_index"])

    records.append(temp)

freight_rates = pd.concat(
    records,
    ignore_index=True
)

# Arrange columns
freight_rates = freight_rates[
    [
        "date",
        "vessel_type",
        "freight_index"
    ]
]

# Sort
freight_rates = freight_rates.sort_values(
    ["date", "vessel_type"]
).reset_index(drop=True)

# ------------------------------------------------------------
# 11. Save long-format dataset
# ------------------------------------------------------------

freight_rates.to_csv(
    OUTPUT_LONG,
    index=False
)

print(f"\nSaved ML dataset:")
print(OUTPUT_LONG)

# ------------------------------------------------------------
# 12. Final summary
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CLEANING COMPLETE")
print("=" * 60)

print(f"Date range:")
print(f"  Start: {df['Date'].min().date()}")
print(f"  End  : {df['Date'].max().date()}")

print(f"\nCleaned rows: {len(df)}")

print("\nFreight dataset rows:")
print(len(freight_rates))

print("\nVessel types:")
print(freight_rates["vessel_type"].value_counts())

print("\nFirst 10 freight records:")
print(freight_rates.head(10).to_string(index=False))