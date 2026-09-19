"""Marine and atmospheric weather integration for Freight Prediction.

Uses Open-Meteo's public marine and weather endpoints. No API key is required
for the public non-commercial tier.

The service samples the same prototype route chain used by route_sailing.py,
fetches 7 days of hourly conditions, summarizes route-wide conditions, and
turns them into a bounded prototype weather-impact adjustment for sailing time
and bunker cost.

This is operational decision support, not a nautical navigation or safety
system. Open-Meteo documents that marine current/tide fields are modelled at
coarser resolution and should not replace nautical navigation data.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import requests

from models.optimization.route_sailing import (
    ORIGIN_ROUTE_OVERRIDES,
    PORT_COORDINATES,
    WAYPOINTS,
    get_route_coordinates,
    get_route_distance_nm,
    get_route_routing_source,
)

MARINE_API_BASE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_API_BASE_URL = "https://api.open-meteo.com/v1/forecast"

FORECAST_DAYS = 7
REQUEST_TIMEOUT_SECONDS = 12
CACHE_TTL_SECONDS = 30 * 60

MARINE_HOURLY_VARIABLES = (
    "wave_height",
    "wave_direction",
    "wave_period",
    "wind_wave_height",
    "wind_wave_direction",
    "wind_wave_period",
    "swell_wave_height",
    "swell_wave_direction",
    "swell_wave_period",
    "ocean_current_velocity",
    "ocean_current_direction",
    "sea_level_height_msl",
)

ATMOSPHERIC_HOURLY_VARIABLES = (
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation",
    "visibility",
    "weather_code",
)

_CACHE: dict[str, tuple[float, Any]] = {}


def _coords(point_name: str) -> tuple[float, float]:
    if point_name in PORT_COORDINATES:
        return PORT_COORDINATES[point_name]
    if point_name in WAYPOINTS:
        return WAYPOINTS[point_name]
    raise ValueError(f"Unknown route point: {point_name}")


def get_route_points(origin_port: str, destination_port: str) -> list[str]:
    """Return the prototype maritime route chain used for weather sampling."""
    if origin_port not in PORT_COORDINATES:
        raise ValueError(f"Unknown origin port: {origin_port}")
    if destination_port not in PORT_COORDINATES:
        raise ValueError(f"Unknown destination port: {destination_port}")

    return [
        origin_port,
        *ORIGIN_ROUTE_OVERRIDES.get(origin_port, []),
        destination_port,
    ]


def _build_url(
    coordinates: list[tuple[float, float]],
    base_url: str,
    hourly_variables: tuple[str, ...],
    *,
    forecast_days: int = FORECAST_DAYS,
    extra_params: dict[str, str] | None = None,
    use_sea_cell_selection: bool = False,
) -> str:
    if not coordinates:
        raise ValueError("At least one route coordinate is required")

    params = [
        ("latitude", ",".join(f"{lat:.5f}" for lat, _ in coordinates)),
        ("longitude", ",".join(f"{lon:.5f}" for _, lon in coordinates)),
        ("hourly", ",".join(hourly_variables)),
        ("forecast_days", str(forecast_days)),
        ("timezone", "GMT"),
    ]

    if use_sea_cell_selection:
        params.append(("cell_selection", "sea"))

    if extra_params:
        params.extend(extra_params.items())

    return f"{base_url}?{urlencode(params)}"


def build_marine_weather_url(
    origin_port: str,
    destination_port: str,
    forecast_days: int = FORECAST_DAYS,
) -> str:
    """Build the Open-Meteo Marine API URL for the route."""
    if not 1 <= forecast_days <= 8:
        raise ValueError("forecast_days must be between 1 and 8")

    return _build_url(
        get_route_coordinates(origin_port, destination_port),
        MARINE_API_BASE_URL,
        MARINE_HOURLY_VARIABLES,
        forecast_days=forecast_days,
        use_sea_cell_selection=True,
    )


def build_atmospheric_weather_url(
    origin_port: str,
    destination_port: str,
    forecast_days: int = FORECAST_DAYS,
) -> str:
    """Build the Open-Meteo standard weather URL for the route."""
    if not 1 <= forecast_days <= 16:
        raise ValueError("forecast_days must be between 1 and 16")

    return _build_url(
        get_route_coordinates(origin_port, destination_port),
        WEATHER_API_BASE_URL,
        ATMOSPHERIC_HOURLY_VARIABLES,
        forecast_days=forecast_days,
        extra_params={"wind_speed_unit": "kn"},
    )


def _get_json(url: str) -> Any:
    now = time.time()
    cached = _CACHE.get(url)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "Freight-Prediction/1.0"},
    )
    response.raise_for_status()
    payload = response.json()

    _CACHE[url] = (now, payload)
    return payload


def _as_location_list(payload: Any) -> list[dict[str, Any]]:
    """Normalize Open-Meteo single- or multi-location responses."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        return [payload]

    return []


def _flatten_numeric(payload: Any, key: str) -> list[float]:
    values: list[float] = []

    for location in _as_location_list(payload):
        hourly = location.get("hourly")
        if not isinstance(hourly, dict):
            continue

        raw_values = hourly.get(key, [])
        if not isinstance(raw_values, list):
            continue

        for value in raw_values:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue

            if number == number:
                values.append(number)

    return values


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None

    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower

    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _severity(value: float | None, low: float, high: float) -> float:
    if value is None:
        return 0.0
    return _clamp((value - low) / (high - low) * 100.0)


def _detect_severe_weather_codes(payload: Any) -> bool:
    severe_codes = {65, 67, 75, 82, 95, 96, 99}

    for location in _as_location_list(payload):
        hourly = location.get("hourly")
        if not isinstance(hourly, dict):
            continue

        for code in hourly.get("weather_code", []) or []:
            try:
                if int(code) in severe_codes:
                    return True
            except (TypeError, ValueError):
                continue

    return False


def _calculate_weather_metrics(
    marine_payload: Any,
    atmospheric_payload: Any,
    route_points: list[str],
    base_sailing_days: float,
    forecast_days: int,
) -> dict[str, Any]:
    if not _as_location_list(marine_payload) or not _as_location_list(atmospheric_payload):
        raise ValueError("Weather provider returned no location data")

    marine_samples = _flatten_numeric(marine_payload, "wave_height")
    atmospheric_samples = _flatten_numeric(
        atmospheric_payload,
        "wind_speed_10m",
    )

    if not marine_samples and not atmospheric_samples:
        raise ValueError("Weather provider returned no usable weather samples")

    wave_p90 = _percentile(marine_samples, 0.90)
    swell_p90 = _percentile(
        _flatten_numeric(marine_payload, "swell_wave_height"),
        0.90,
    )
    wind_p90 = _percentile(
        _flatten_numeric(atmospheric_payload, "wind_speed_10m"),
        0.90,
    )
    gust_p90 = _percentile(
        _flatten_numeric(atmospheric_payload, "wind_gusts_10m"),
        0.90,
    )
    current_p90 = _percentile(
        _flatten_numeric(marine_payload, "ocean_current_velocity"),
        0.90,
    )
    visibility_p10 = _percentile(
        _flatten_numeric(atmospheric_payload, "visibility"),
        0.10,
    )
    precipitation_p90 = _percentile(
        _flatten_numeric(atmospheric_payload, "precipitation"),
        0.90,
    )

    wave_score = _severity(wave_p90, 1.5, 4.5)
    swell_score = _severity(swell_p90, 1.0, 3.0)
    wind_score = _severity(wind_p90, 25.0, 45.0)
    gust_score = _severity(gust_p90, 35.0, 60.0)
    current_score = _severity(current_p90, 0.75, 2.0)
    visibility_score = (
        0.0
        if visibility_p10 is None
        else _clamp((5000.0 - visibility_p10) / 5000.0 * 100.0)
    )

    severe_weather_detected = _detect_severe_weather_codes(
        atmospheric_payload
    )

    score = (
        0.40 * wave_score
        + 0.20 * swell_score
        + 0.20 * wind_score
        + 0.10 * gust_score
        + 0.05 * current_score
        + 0.05 * visibility_score
    )

    if severe_weather_detected:
        score += 10.0

    score = round(_clamp(score), 1)

    if score < 25:
        risk_level = "LOW"
    elif score < 50:
        risk_level = "MODERATE"
    elif score < 75:
        risk_level = "HIGH"
    else:
        risk_level = "SEVERE"

    # Prototype weather penalty: cap the speed reduction at 20%.
    speed_reduction = min(0.20, score / 500.0)

    if base_sailing_days <= 0:
        adjusted_sailing_days = 0.0
        weather_delay_days = 0.0
        bunker_multiplier = 1.0
        coverage_fraction = 0.0
    else:
        theoretical_adjusted_days = base_sailing_days / max(
            1.0 - speed_reduction,
            0.80,
        )
        theoretical_delay_days = (
            theoretical_adjusted_days - base_sailing_days
        )

        # Only the first 7 forecast days are adjusted. For longer voyages,
        # do not pretend today's 7-day forecast describes the entire voyage.
        coverage_fraction = min(
            1.0,
            forecast_days / base_sailing_days,
        )
        weather_delay_days = theoretical_delay_days * coverage_fraction
        adjusted_sailing_days = base_sailing_days + weather_delay_days

        bunker_multiplier = min(
            1.25,
            1.0 + weather_delay_days / base_sailing_days,
        )

    return {
        "status": "AVAILABLE",
        "provider": "Open-Meteo",
        "data_fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "forecast_days": forecast_days,
        "route_points": route_points,
        "weather_risk_score": score,
        "risk_level": risk_level,
        "p90_wave_height_m": (
            round(wave_p90, 2) if wave_p90 is not None else None
        ),
        "p90_swell_height_m": (
            round(swell_p90, 2) if swell_p90 is not None else None
        ),
        "p90_wind_speed_knots": (
            round(wind_p90, 1) if wind_p90 is not None else None
        ),
        "p90_wind_gust_knots": (
            round(gust_p90, 1) if gust_p90 is not None else None
        ),
        "p90_ocean_current_ms": (
            round(current_p90, 2) if current_p90 is not None else None
        ),
        "p10_visibility_m": (
            round(visibility_p10) if visibility_p10 is not None else None
        ),
        "p90_precipitation_mm": (
            round(precipitation_p90, 2)
            if precipitation_p90 is not None
            else None
        ),
        "severe_weather_detected": severe_weather_detected,
        "base_sailing_days": round(base_sailing_days, 2),
        "adjusted_sailing_days": round(adjusted_sailing_days, 2),
        "weather_delay_days": round(weather_delay_days, 2),
        "speed_reduction_percent": round(speed_reduction * 100.0, 1),
        "bunker_cost_multiplier": round(bunker_multiplier, 4),
        "forecast_coverage_fraction": round(coverage_fraction, 3),
        "note": (
            "Prototype weather-impact model using route-sampled Open-Meteo "
            "marine and atmospheric forecasts. The configured forecast window "
            "is used to adjust sailing time and bunker cost; longer-voyage "
            "conditions beyond that window are not forecast here."
        ),
        "marine_api_url": build_marine_weather_url(
            route_points[0],
            route_points[-1],
            forecast_days=forecast_days,
        ),
        "weather_api_url": build_atmospheric_weather_url(
            route_points[0],
            route_points[-1],
            forecast_days=forecast_days,
        ),
    }


def get_route_weather(
    origin_port: str,
    destination_port: str,
    base_sailing_days: float,
    forecast_days: int = FORECAST_DAYS,
) -> dict[str, Any]:
    """Fetch route weather and return a bounded economic impact summary.

    Fail-soft behavior is intentional: if the provider is unreachable,
    the voyage keeps its original sailing time and bunker multiplier.
    """
    if base_sailing_days < 0:
        raise ValueError("base_sailing_days cannot be negative")

    if not 1 <= forecast_days <= 8:
        raise ValueError("forecast_days must be between 1 and 8")

    route_points = get_route_points(origin_port, destination_port)
    route_coordinates = get_route_coordinates(
        origin_port,
        destination_port,
        max_points=24,
    )
    route_distance_nm = get_route_distance_nm(
        origin_port,
        destination_port,
    )
    routing_source = get_route_routing_source(
        origin_port,
        destination_port,
    )

    # Keep the public helpers aligned when callers request a non-default
    # forecast horizon.
    marine_url = build_marine_weather_url(
        origin_port,
        destination_port,
        forecast_days=forecast_days,
    )
    weather_url = build_atmospheric_weather_url(
        origin_port,
        destination_port,
        forecast_days=forecast_days,
    )

    unavailable = {
        "status": "UNAVAILABLE",
        "provider": "Open-Meteo",
        "forecast_days": forecast_days,
        "route_points": route_points,
        "route_distance_nm": round(route_distance_nm, 2),
        "route_sampling_points": len(route_coordinates),
        "routing_source": routing_source,
        "weather_risk_score": None,
        "risk_level": "UNKNOWN",
        "base_sailing_days": round(base_sailing_days, 2),
        "adjusted_sailing_days": round(base_sailing_days, 2),
        "weather_delay_days": 0.0,
        "speed_reduction_percent": 0.0,
        "bunker_cost_multiplier": 1.0,
        "forecast_coverage_fraction": 0.0,
        "available_sources": [],
        "source_status": {
            "marine": "UNAVAILABLE",
            "atmospheric": "UNAVAILABLE",
        },
        "marine_api_url": marine_url,
        "weather_api_url": weather_url,
        "note": (
            "Open-Meteo weather data was unavailable. No weather adjustment "
            "was applied; the route-time model fell back to its base estimate."
        ),
    }

    try:
        marine_payload = None
        atmospheric_payload = None
        marine_error = None
        atmospheric_error = None

        try:
            marine_payload = _get_json(marine_url)
        except (requests.RequestException, ValueError, TypeError) as exc:
            marine_error = f"{type(exc).__name__}: {exc}"

        try:
            atmospheric_payload = _get_json(weather_url)
        except (requests.RequestException, ValueError, TypeError) as exc:
            atmospheric_error = f"{type(exc).__name__}: {exc}"

        if marine_payload is None and atmospheric_payload is None:
            raise ValueError("Both weather providers failed")

        result = _calculate_weather_metrics(
            marine_payload or {},
            atmospheric_payload or {},
            route_points,
            base_sailing_days,
            forecast_days,
        )
        result["route_distance_nm"] = round(route_distance_nm, 2)
        result["route_sampling_points"] = len(route_coordinates)
        result["routing_source"] = routing_source

        available_sources = []
        if marine_payload is not None:
            available_sources.append("marine")
        if atmospheric_payload is not None:
            available_sources.append("atmospheric")

        result["status"] = (
            "AVAILABLE" if len(available_sources) == 2 else "PARTIAL"
        )
        result["available_sources"] = available_sources
        result["source_status"] = {
            "marine": "AVAILABLE" if marine_payload is not None else "UNAVAILABLE",
            "atmospheric": (
                "AVAILABLE"
                if atmospheric_payload is not None
                else "UNAVAILABLE"
            ),
        }
        result["provider_errors"] = {
            key: value
            for key, value in {
                "marine": marine_error,
                "atmospheric": atmospheric_error,
            }.items()
            if value
        }
        result["marine_api_url"] = marine_url
        result["weather_api_url"] = weather_url
        result["forecast_days"] = forecast_days

        if len(available_sources) == 1:
            result["note"] = (
                "Partial Open-Meteo coverage was available for this route. "
                "Only the returned marine/atmospheric variables were used; "
                "missing weather sources did not trigger a zero-data assumption."
            )

        return result
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        unavailable["provider_error"] = f"{type(exc).__name__}: {exc}"
        return unavailable
