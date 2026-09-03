import pandas as pd
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Excel file
file_path = BASE_DIR / "data" / "edited BDI data1.xls"

print("=" * 60)
print("FREIGHT PREDICTION - BDI DATA INSPECTION")
print("=" * 60)

# Check file exists
if not file_path.exists():
    print(f"\nERROR: File not found:\n{file_path}")
    raise SystemExit(1)

print(f"\nFile found: {file_path}")

# Read workbook
try:
    excel_file = pd.ExcelFile(file_path, engine="xlrd")

    print("\nSheets found:")
    for sheet in excel_file.sheet_names:
        print(f"  - {sheet}")

    # Read first sheet
    df = pd.read_excel(
        file_path,
        sheet_name=excel_file.sheet_names[0],
        engine="xlrd"
    )

    print("\nDataset shape:")
    print(f"Rows    : {df.shape[0]}")
    print(f"Columns : {df.shape[1]}")

    print("\nColumn names:")
    for column in df.columns:
        print(f"  - {column}")

    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nBasic statistics:")
    print(df.describe(include="all").to_string())

except Exception as e:
    print(f"\nERROR while reading Excel file:")
    print(e)
    raise