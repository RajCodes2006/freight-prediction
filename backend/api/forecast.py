from fastapi import APIRouter, HTTPException

from backend.schemas.forecast import ForecastRequest
from models.decision_engine import build_decision
from models.optimization.route_sailing import (
    estimate_sailing_days,
    get_route_distance_nm,
    get_route_routing_source,
)
from models.inference.live_market import get_live_market_snapshot
from models.inference.live_calibration import calibrate_live_vessel_indices
from models.optimization.voyage_cost import get_freight_rate_details
from models.data_provenance import build_data_provenance
from models.inference.marine_weather import get_route_weather

router = APIRouter(prefix="/api", tags=["Forecast"])


@router.post("/forecast")
def forecast(request: ForecastRequest):
    try:
        route_distance_nm = get_route_distance_nm(
            request.origin_port,
            request.destination_port,
        )
        route_routing_source = get_route_routing_source(
            request.origin_port,
            request.destination_port,
        )

        sailing_days = estimate_sailing_days(
            origin_port=request.origin_port,
            destination_port=request.destination_port,
        )

        weather_impact = get_route_weather(
            origin_port=request.origin_port,
            destination_port=request.destination_port,
            base_sailing_days=sailing_days,
            forecast_days=7,
        )

        result = build_decision(
            cargo_quantity_mt=request.quantity_mt,
            origin_port=request.origin_port,
            destination_port=request.destination_port,
            contract_duration_months=request.contract_duration_months,
            planned_voyages=request.planned_voyages,
            sailing_days=weather_impact["adjusted_sailing_days"],
            verified_only=False,
            weather_impact=weather_impact,
        )

        if not isinstance(result, dict):
            raise ValueError("Decision engine returned an invalid response.")

        result.setdefault("input", {})

        result["input"]["cargo_quantity_mt"] = request.quantity_mt
        result["input"]["commodity"] = request.commodity
        result["input"]["origin_country"] = request.origin_country
        result["input"]["origin_port"] = request.origin_port
        result["input"]["destination_port"] = request.destination_port
        result["input"]["contract_duration_months"] = request.contract_duration_months
        result["input"]["planned_voyages"] = request.planned_voyages

        # Expose current market benchmarks as context. The forecasting
        # engine separately applies the live calibration when available.
        result["market_context"] = get_live_market_snapshot()

        # Surface the exact freight-rate method used for this response.
        recommended_vessel = (result.get("vessel_decision") or {}).get(
            "recommended_vessel"
        )
        if recommended_vessel:
            freight_details = get_freight_rate_details(recommended_vessel)
            result["vessel_decision"]["freight_rate_source"] = freight_details["source"]
            result["vessel_decision"]["freight_rate_details"] = freight_details

        result["trade_context"] = {
            "origin_country": request.origin_country,
            "origin_port": request.origin_port,
            "destination_port": request.destination_port,
            "optimization_mode": "INDIAN_DESTINATION_PROTOTYPE",
            "route_distance_nm": round(route_distance_nm, 2),
            "route_routing_source": route_routing_source,
            "estimated_sailing_days": sailing_days,
            "weather_adjusted_sailing_days": weather_impact.get(
                "adjusted_sailing_days"
            ),
            "weather_delay_days": weather_impact.get(
                "weather_delay_days"
            ),
            "sailing_time_source": (
                "MARITIME_ROUTING_PLUS_WEATHER"
                if weather_impact.get("status") == "AVAILABLE"
                else "MARITIME_ROUTING"
            ),
            "sailing_time_note": (
                "Maritime sea-route distance from the configured routing network "
                "and planning speed, optionally adjusted using the first 7 days of "
                "weather sampled along that route; not a live vessel schedule."
            ),
        }

        # Keep the headline data note aligned with the actual current engine.
        if (
            result.get("vessel_decision", {}).get("freight_rate_source")
            == "LIVE_CALIBRATED_INDEX"
        ):
            result["data_note"] = (
                "The ML component forecasts a Baltic vessel-class market index. "
                "The current freight-rate estimate is scaled from the live-calibrated "
                "vessel-class index and a prototype baseline; it is not a route-specific "
                "charter quote. Weather-adjusted sailing time and bunker impact are "
                "prototype calculations based on route-sampled Open-Meteo data. "
                "Port charges and some queue inputs remain prototype assumptions."
            )
        else:
            result["data_note"] = (
                "The ML component forecasts a Baltic vessel-class market index. "
                "Freight rate uses a prototype fallback when live calibration is unavailable. "
                "Weather-adjusted sailing time and bunker impact use route-sampled "
                "Open-Meteo data when available; otherwise the base route estimate is used. "
                "Port charges and some queue inputs remain prototype assumptions."
            )

        # Attach an explicit provenance map after all response sections are
        # assembled so each important value is classified by data origin.
        result["data_provenance"] = build_data_provenance(result)

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:
        # Full detail stays server-side; the client only gets a
        # generic message so internal paths/exception text are never
        # exposed in the API response.
        print(f"FORECAST ERROR: {type(exc).__name__}: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Internal prediction error. Please try again."
        )
