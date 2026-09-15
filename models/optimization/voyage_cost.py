from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from models.inference.live_calibration import calibrate_live_vessel_indices
from models.inference.live_market import get_live_market_snapshot


# Baseline freight-rate assumptions in USD/MT.
# These remain the fallback/reference values when live market data is unavailable.
PROTOTYPE_FREIGHT_RATE_USD_PER_MT = {
    "Handysize": 22.0,
    "Supramax": 20.0,
    "Panamax": 18.0,
    "Capesize": 16.0,
}


# Prototype additional voyage costs in USD.
# These are still assumptions for development/testing.
PROTOTYPE_BUNKER_COST_USD = {
    "Handysize": 30_000,
    "Supramax": 40_000,
    "Panamax": 50_000,
    "Capesize": 65_000,
}


PROTOTYPE_PORT_CHARGES_USD = {
    "Handysize": 10_000,
    "Supramax": 15_000,
    "Panamax": 20_000,
    "Capesize": 30_000,
}


BASE_DIR = Path(__file__).resolve().parents[2]
REFERENCE_INDEX_FILE = BASE_DIR / "data" / "bdi_clean.csv"

VESSEL_TO_INDEX = {
    "Handysize": "HSI",
    "Supramax": "SI",
    "Panamax": "PI",
    "Capesize": "CI",
}

# Keep the live benchmark adjustment deliberately bounded. This prevents a
# prototype benchmark calibration from producing absurd freight quotes.
MIN_MARKET_MULTIPLIER = 0.70
MAX_MARKET_MULTIPLIER = 1.50


def _get_reference_index(vessel_type: str) -> Optional[float]:
    """Return the latest historical vessel-class index used as the baseline."""

    index_column = VESSEL_TO_INDEX.get(vessel_type)
    if index_column is None or not REFERENCE_INDEX_FILE.exists():
        return None

    try:
        df = pd.read_csv(REFERENCE_INDEX_FILE, usecols=["Date", index_column])
        df = df.sort_values("Date")
        values = pd.to_numeric(df[index_column], errors="coerce").dropna()
        if values.empty:
            return None
        return float(values.iloc[-1])
    except (OSError, ValueError, TypeError):
        return None


def _get_live_market_rate(vessel_type: str) -> Optional[Dict]:
    """Calculate a bounded live-market freight-rate estimate for a vessel class."""

    try:
        snapshot = get_live_market_snapshot()
        calibration = calibrate_live_vessel_indices(snapshot)
        if not calibration.get("available"):
            return None

        live_index = calibration.get("vessel_indices", {}).get(
            VESSEL_TO_INDEX.get(vessel_type, "")
        )
        reference_index = _get_reference_index(vessel_type)

        if live_index is None or reference_index is None or reference_index <= 0:
            return None

        multiplier = float(live_index) / float(reference_index)
        multiplier = max(
            MIN_MARKET_MULTIPLIER,
            min(MAX_MARKET_MULTIPLIER, multiplier),
        )

        base_rate = PROTOTYPE_FREIGHT_RATE_USD_PER_MT[vessel_type]
        estimated_rate = base_rate * multiplier

        return {
            "rate_usd_per_mt": round(estimated_rate, 2),
            "base_rate_usd_per_mt": base_rate,
            "market_multiplier": round(multiplier, 4),
            "live_index": round(float(live_index), 2),
            "reference_index": round(float(reference_index), 2),
            "source": "LIVE_CALIBRATED_INDEX",
            "source_note": (
                "Prototype freight-rate estimate scaled from the baseline rate "
                "using the live-calibrated vessel-class index. It is not a route-specific charter quote."
            ),
        }
    except Exception:
        return None


def get_freight_rate(vessel_type: str) -> float:
    """Return a live-market-aware freight-rate estimate, with prototype fallback."""

    if vessel_type not in PROTOTYPE_FREIGHT_RATE_USD_PER_MT:
        raise ValueError(f"Unknown vessel type: {vessel_type}")

    live_rate = _get_live_market_rate(vessel_type)
    if live_rate is not None:
        return live_rate["rate_usd_per_mt"]

    return PROTOTYPE_FREIGHT_RATE_USD_PER_MT[vessel_type]


def get_freight_rate_details(vessel_type: str) -> Dict:
    """Return the freight-rate estimate together with transparent provenance."""

    if vessel_type not in PROTOTYPE_FREIGHT_RATE_USD_PER_MT:
        raise ValueError(f"Unknown vessel type: {vessel_type}")

    live_rate = _get_live_market_rate(vessel_type)
    if live_rate is not None:
        return live_rate

    base_rate = PROTOTYPE_FREIGHT_RATE_USD_PER_MT[vessel_type]
    return {
        "rate_usd_per_mt": base_rate,
        "base_rate_usd_per_mt": base_rate,
        "market_multiplier": 1.0,
        "live_index": None,
        "reference_index": _get_reference_index(vessel_type),
        "source": "PROTOTYPE_ASSUMPTION",
        "source_note": "Fallback prototype freight rate; no live market calibration available.",
    }


def get_bunker_cost(vessel_type: str) -> float:
    """Return prototype bunker/fuel cost."""

    if vessel_type not in PROTOTYPE_BUNKER_COST_USD:
        raise ValueError(f"Unknown vessel type: {vessel_type}")

    return PROTOTYPE_BUNKER_COST_USD[vessel_type]


def get_port_charges(vessel_type: str) -> float:
    """Return prototype port charges."""

    if vessel_type not in PROTOTYPE_PORT_CHARGES_USD:
        raise ValueError(f"Unknown vessel type: {vessel_type}")

    return PROTOTYPE_PORT_CHARGES_USD[vessel_type]


def calculate_freight_cost(
    cargo_quantity_mt: float,
    vessel_type: str,
) -> float:
    """Freight cost = cargo quantity × estimated freight rate."""

    if cargo_quantity_mt <= 0:
        raise ValueError("cargo_quantity_mt must be greater than 0")

    rate = get_freight_rate(vessel_type)
    return cargo_quantity_mt * rate


def calculate_total_voyage_cost(
    cargo_quantity_mt: float,
    vessel_type: str,
    vessel_time_cost_usd: float,
) -> Dict:
    """Calculate total estimated voyage cost."""

    if cargo_quantity_mt <= 0:
        raise ValueError("cargo_quantity_mt must be greater than 0")

    if vessel_time_cost_usd < 0:
        raise ValueError("vessel_time_cost_usd cannot be negative")

    freight_details = get_freight_rate_details(vessel_type)
    freight_rate = freight_details["rate_usd_per_mt"]
    bunker_cost = get_bunker_cost(vessel_type)
    port_charges = get_port_charges(vessel_type)

    freight_cost = cargo_quantity_mt * freight_rate

    total_cost = (
        freight_cost
        + vessel_time_cost_usd
        + bunker_cost
        + port_charges
    )

    cost_per_mt = total_cost / cargo_quantity_mt

    return {
        "vessel_type": vessel_type,
        "cargo_quantity_mt": cargo_quantity_mt,
        "freight_rate_usd_per_mt": round(freight_rate, 2),
        "freight_rate_source": freight_details["source"],
        "freight_rate_details": freight_details,
        "freight_cost_usd": round(freight_cost, 2),
        "vessel_time_cost_usd": round(vessel_time_cost_usd, 2),
        "bunker_cost_usd": round(bunker_cost, 2),
        "port_charges_usd": round(port_charges, 2),
        "total_voyage_cost_usd": round(total_cost, 2),
        "total_cost_per_mt_usd": round(cost_per_mt, 2),
    }


if __name__ == "__main__":
    result = calculate_total_voyage_cost(
        cargo_quantity_mt=60_000,
        vessel_type="Supramax",
        vessel_time_cost_usd=127_200,
    )

    print("\nVoyage Cost Calculation:")
    print("=" * 65)

    for key, value in result.items():
        print(f"{key}: {value}")
