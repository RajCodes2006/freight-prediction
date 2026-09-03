from pathlib import Path
from typing import Dict, Optional

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

CONGESTION_FILE = (
    BASE_DIR
    / "data"
    / "port_congestion.csv"
)


# ------------------------------------------------------------
# Prototype fallback values
# ------------------------------------------------------------
# These are NOT observed congestion measurements.
# They are only used until a real port activity/congestion
# dataset is available.

DEFAULT_QUEUE_DAYS = {
    "loading": 1.0,
    "discharge": 1.5,
}


def load_congestion_data() -> Optional[pd.DataFrame]:
    """
    Load port congestion data when available.

    Expected columns:

        port
        congestion_index
        average_waiting_days
        observation_date
        data_status

    Returns None when the file does not yet exist.
    """

    if not CONGESTION_FILE.exists():
        return None

    df = pd.read_csv(
        CONGESTION_FILE,
        parse_dates=["observation_date"],
    )

    required_columns = {
        "port",
        "congestion_index",
        "average_waiting_days",
        "observation_date",
        "data_status",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            "Missing congestion columns: "
            + ", ".join(sorted(missing))
        )

    df["port"] = (
        df["port"]
        .astype(str)
        .str.strip()
    )

    df["data_status"] = (
        df["data_status"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["congestion_index"] = pd.to_numeric(
        df["congestion_index"],
        errors="coerce",
    )

    df["average_waiting_days"] = pd.to_numeric(
        df["average_waiting_days"],
        errors="coerce",
    )

    return df


def get_latest_port_congestion(
    port_name: str,
) -> Optional[Dict]:
    """
    Return the latest congestion observation for a port.

    Returns None when no real congestion dataset exists.
    """

    df = load_congestion_data()

    if df is None:
        return None

    result = df[
        df["port"].str.lower()
        == port_name.strip().lower()
    ].copy()

    if result.empty:
        return None

    result = result.sort_values(
        "observation_date"
    )

    row = result.iloc[-1]

    return {
        "port": row["port"],
        "congestion_index": (
            float(row["congestion_index"])
            if pd.notna(
                row["congestion_index"]
            )
            else None
        ),
        "average_waiting_days": (
            float(row["average_waiting_days"])
            if pd.notna(
                row["average_waiting_days"]
            )
            else None
        ),
        "observation_date": (
            row["observation_date"]
            .strftime("%Y-%m-%d")
            if pd.notna(
                row["observation_date"]
            )
            else None
        ),
        "data_status": row["data_status"],
        "source": "port_congestion.csv",
    }


def estimate_port_queue_time(
    port_name: str,
    operation: str,
) -> Dict:
    """
    Get queue time for a port.

    Uses real congestion data when available.

    Otherwise returns the current prototype fallback.
    """

    operation = operation.lower().strip()

    if operation not in {
        "loading",
        "discharge",
    }:
        raise ValueError(
            "operation must be 'loading' or 'discharge'"
        )

    congestion = get_latest_port_congestion(
        port_name
    )

    # --------------------------------------------------------
    # Real data available
    # --------------------------------------------------------

    if congestion is not None:

        waiting_days = (
            congestion[
                "average_waiting_days"
            ]
        )

        if waiting_days is not None:

            return {
                "port": port_name,
                "operation": operation,
                "queue_days": round(
                    waiting_days,
                    2,
                ),
                "source": "DATA",
                "data_status": congestion[
                    "data_status"
                ],
                "observation_date": congestion[
                    "observation_date"
                ],
                "congestion_index": congestion[
                    "congestion_index"
                ],
            }

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return {
        "port": port_name,
        "operation": operation,
        "queue_days": DEFAULT_QUEUE_DAYS[
            operation
        ],
        "source": "PROTOTYPE_FALLBACK",
        "data_status": "ASSUMED",
        "observation_date": None,
        "congestion_index": None,
    }


def calculate_route_congestion(
    origin_port: str,
    destination_port: str,
) -> Dict:
    """
    Calculate loading and discharge queue time for a route.
    """

    loading = estimate_port_queue_time(
        port_name=origin_port,
        operation="loading",
    )

    discharge = estimate_port_queue_time(
        port_name=destination_port,
        operation="discharge",
    )

    total_queue_days = (
        loading["queue_days"]
        + discharge["queue_days"]
    )

    real_data_used = (
        loading["source"] == "DATA"
        and discharge["source"] == "DATA"
    )

    return {
        "origin_port": origin_port,
        "destination_port": destination_port,
        "loading": loading,
        "discharge": discharge,
        "total_queue_days": round(
            total_queue_days,
            2,
        ),
        "real_data_used": real_data_used,
    }


def congestion_risk_level(
    total_queue_days: float,
) -> str:
    """
    Convert expected waiting time into a simple risk level.

    Prototype thresholds:
        <= 1 day     LOW
        <= 3 days    MEDIUM
        > 3 days     HIGH
    """

    if total_queue_days <= 1:
        return "LOW"

    if total_queue_days <= 3:
        return "MEDIUM"

    return "HIGH"


def build_congestion_summary(
    origin_port: str,
    destination_port: str,
) -> Dict:
    """
    Build a route congestion summary.
    """

    route = calculate_route_congestion(
        origin_port=origin_port,
        destination_port=destination_port,
    )

    risk = congestion_risk_level(
        route["total_queue_days"]
    )

    return {
        **route,
        "risk_level": risk,
    }


# ------------------------------------------------------------
# Test
# ------------------------------------------------------------

if __name__ == "__main__":

    result = build_congestion_summary(
        origin_port="Paradip",
        destination_port="Visakhapatnam",
    )

    print("\nPORT CONGESTION ANALYSIS")
    print("=" * 70)

    print(
        f"Origin: "
        f"{result['origin_port']}"
    )

    print(
        f"Destination: "
        f"{result['destination_port']}"
    )

    print("\nLoading:")
    print(
        f"  Queue days: "
        f"{result['loading']['queue_days']}"
    )

    print(
        f"  Source: "
        f"{result['loading']['source']}"
    )

    print("\nDischarge:")
    print(
        f"  Queue days: "
        f"{result['discharge']['queue_days']}"
    )

    print(
        f"  Source: "
        f"{result['discharge']['source']}"
    )

    print(
        f"\nTotal queue time: "
        f"{result['total_queue_days']} days"
    )

    print(
        f"Congestion risk: "
        f"{result['risk_level']}"
    )

    print(
        f"Real congestion data used: "
        f"{result['real_data_used']}"
    )