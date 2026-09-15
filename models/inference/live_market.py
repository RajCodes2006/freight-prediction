"""Live freight-market data adapter.

Uses OilPriceAPI as an optional server-side source for current Baltic dry-bulk
benchmarks. The API key is never exposed to the frontend.

Environment:
    OILPRICEAPI_KEY  Optional API token.

The adapter deliberately fails soft: if no key is configured or the provider
is unavailable, the forecasting engine can continue using the local model data.
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE_URL = "https://api.oilpriceapi.com/v1/prices/latest"
CACHE_TTL_SECONDS = 30 * 60
TIMEOUT_SECONDS = 8

_cache: dict[str, tuple[float, dict[str, Any]]] = {}


class LiveMarketDataError(RuntimeError):
    """Raised when live market data cannot be retrieved."""


def _fetch_index(code: str) -> dict[str, Any]:
    api_key = os.getenv("OILPRICEAPI_KEY")
    if not api_key:
        raise LiveMarketDataError("OILPRICEAPI_KEY is not configured")

    now = time.time()
    cached = _cache.get(code)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        response = requests.get(
            BASE_URL,
            params={"by_code": code},
            headers={"Authorization": f"Token {api_key}"},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        value = payload.get("price")
        if value is None:
            raise LiveMarketDataError(f"Provider returned no price for {code}")

        record = {
            "code": code,
            "value": float(value),
            "currency": payload.get("currency"),
            "unit": payload.get("unit"),
            "source": payload.get("source", "OilPriceAPI"),
            "as_of": payload.get("as_of") or payload.get("updated_at"),
            "updated_at": payload.get("updated_at"),
            "stale": bool(payload.get("stale", False)),
            "age_days": payload.get("age_days"),
        }
        _cache[code] = (now, record)
        return record
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise LiveMarketDataError(f"Live market request failed for {code}") from exc


def get_live_market_snapshot() -> dict[str, Any]:
    """Return current dry-bulk benchmark data when configured.

    The Baltic Dry Index (BDI) is a composite of Capesize, Panamax and
    Supramax. The Baltic Capesize Index (BCI) is a separate daily benchmark.
    """

    snapshot: dict[str, Any] = {
        "available": False,
        "provider": None,
        "benchmarks": {},
        "note": "Live market provider not configured; using local model data.",
    }

    try:
        bdi = _fetch_index("BALTIC_DRY_INDEX")
        snapshot["benchmarks"]["bdi"] = bdi
        snapshot["available"] = True
        snapshot["provider"] = "OilPriceAPI"
    except LiveMarketDataError:
        pass

    try:
        bci = _fetch_index("BALTIC_CAPESIZE_INDEX")
        snapshot["benchmarks"]["bci"] = bci
        snapshot["available"] = True
        snapshot["provider"] = "OilPriceAPI"
    except LiveMarketDataError:
        pass

    if snapshot["available"]:
        snapshot["note"] = (
            "Daily dry-bulk benchmark snapshot retrieved server-side. "
            "Values are benchmark indices, not route-specific charter rates."
        )

    return snapshot
