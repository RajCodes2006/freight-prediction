from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from models.inference.live_market import get_live_market_snapshot

BASE_DIR = Path(__file__).resolve().parents[2]
HISTORY_FILE = BASE_DIR / "data" / "bdi_clean.csv"


def _fit(y: pd.Series, x: pd.DataFrame):
    df = pd.concat([y.rename("y"), x], axis=1).dropna()
    if len(df) < 30:
        raise ValueError("Insufficient historical data for calibration")
    xv = df[x.columns].astype(float).to_numpy()
    yv = df["y"].astype(float).to_numpy()
    design = np.column_stack([np.ones(len(xv)), xv])
    coef, *_ = np.linalg.lstsq(design, yv, rcond=None)
    fitted = design @ coef
    ss_res = float(np.sum((yv - fitted) ** 2))
    ss_tot = float(np.sum((yv - np.mean(yv)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return coef, r2


def _predict(coef, values):
    return float(np.array([1.0, *values], dtype=float) @ coef)


def _load_history():
    if not HISTORY_FILE.exists():
        raise FileNotFoundError(f"Calibration dataset not found: {HISTORY_FILE}")
    df = pd.read_csv(HISTORY_FILE, parse_dates=["Date"])
    required = {"Date", "HSI", "SI", "PI", "CI"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Calibration dataset missing columns: {sorted(missing)}")
    df = df.sort_values("Date").reset_index(drop=True)
    df["BDI_derived"] = 0.40 * df["CI"] + 0.30 * df["PI"] + 0.30 * df["SI"]
    return df


def calibrate_live_vessel_indices(snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot = snapshot or get_live_market_snapshot()
    if not snapshot.get("available"):
        return {"available": False, "vessel_indices": {}, "method": "HISTORICAL_ONLY"}

    bdi = snapshot.get("benchmarks", {}).get("bdi", {}).get("value")
    bci = snapshot.get("benchmarks", {}).get("bci", {}).get("value")
    if bdi is None or bci is None:
        return {"available": False, "vessel_indices": {}, "method": "HISTORICAL_ONLY"}

    df = _load_history()
    si_coef, si_r2 = _fit(df["SI"], df[["BDI_derived", "CI"]])
    pi_coef, pi_r2 = _fit(df["PI"], df[["BDI_derived", "CI"]])
    hsi_coef, hsi_r2 = _fit(df["HSI"], df[["SI"]])

    si = max(0.0, _predict(si_coef, [float(bdi), float(bci)]))
    pi = max(0.0, _predict(pi_coef, [float(bdi), float(bci)]))
    hsi = max(0.0, _predict(hsi_coef, [si]))
    ci = max(0.0, float(bci))

    return {
        "available": True,
        "vessel_indices": {
            "HSI": round(hsi, 2),
            "SI": round(si, 2),
            "PI": round(pi, 2),
            "CI": round(ci, 2),
        },
        "calibration_r2": {
            "HSI": round(max(0.0, min(1.0, hsi_r2)), 4),
            "SI": round(max(0.0, min(1.0, si_r2)), 4),
            "PI": round(max(0.0, min(1.0, pi_r2)), 4),
            "CI": 1.0,
        },
        "inputs": {"bdi": float(bdi), "bci": float(bci)},
        "source": "OilPriceAPI BDI + BCI with historical calibration",
        "method": "LIVE_LEVEL_CALIBRATION",
        "note": "Benchmark level calibration, not a route-specific freight quote.",
    }
