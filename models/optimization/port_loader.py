import pandas as pd
from pathlib import Path

# ============================================================
# FREIGHT PREDICTION
# Port Data Loader
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PORT_FILE = BASE_DIR / "data" / "ports.csv"

REQUIRED_COLUMNS = [
    "port",
    "berth",
    "commodity",
    "max_loa_m",
    "max_beam_m",
    "max_draft_m",
    "max_dwt_mt",
    "handling_rate_mt_day",
    "operational_notes",
    "data_status",
    "source",
]


def load_ports() -> pd.DataFrame:
    """
    Load and validate the port/berth database.
    """

    if not PORT_FILE.exists():
        raise FileNotFoundError(
            f"Port database not found:\n{PORT_FILE}"
        )

    df = pd.read_csv(PORT_FILE)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # --------------------------------------------------------
    # Clean text columns
    # --------------------------------------------------------

    text_columns = [
        "port",
        "berth",
        "commodity",
        "operational_notes",
        "data_status",
        "source",
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # --------------------------------------------------------
    # Convert numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "max_loa_m",
        "max_beam_m",
        "max_draft_m",
        "max_dwt_mt",
        "handling_rate_mt_day",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Validate status
    # --------------------------------------------------------

    valid_statuses = {
        "VERIFIED",
        "PARTIAL"
    }

    invalid_statuses = set(
        df["data_status"].unique()
    ) - valid_statuses

    if invalid_statuses:
        raise ValueError(
            f"Invalid data_status values: "
            f"{invalid_statuses}"
        )

    return df


def get_port_berths(
    port_name: str,
    verified_only: bool = False
) -> pd.DataFrame:
    """
    Return all known berth records for a port.

    Parameters
    ----------
    port_name:
        Port name.

    verified_only:
        If True, return only VERIFIED rows.
    """

    df = load_ports()

    result = df[
        df["port"].str.casefold()
        == port_name.strip().casefold()
    ].copy()

    if verified_only:

        result = result[
            result["data_status"] == "VERIFIED"
        ]

    return result.reset_index(drop=True)


def get_port_list(
    verified_only: bool = False
) -> list[str]:
    """
    Return unique port names.
    """

    df = load_ports()

    if verified_only:

        df = df[
            df["data_status"] == "VERIFIED"
        ]

    return sorted(
        df["port"].dropna().unique().tolist()
    )


def print_port_summary():
    """
    Display a simple summary of the port database.
    """

    df = load_ports()

    print("=" * 70)
    print("PORT DATABASE SUMMARY")
    print("=" * 70)

    print(
        f"\nTotal berth records: {len(df)}"
    )

    print(
        f"Unique ports: "
        f"{df['port'].nunique()}"
    )

    print("\nStatus:")
    print(
        df["data_status"]
        .value_counts()
        .to_string()
    )

    print("\nPorts:")

    for port in get_port_list():
        count = len(
            df[df["port"] == port]
        )

        print(
            f"  {port}: {count} berth record(s)"
        )


if __name__ == "__main__":
    print_port_summary()

    print("\nExample: Paradip")
    print(
        get_port_berths(
            "Paradip"
        ).to_string(index=False)
    )