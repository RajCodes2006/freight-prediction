from fastapi import APIRouter, HTTPException

from backend.schemas.forecast import ForecastRequest
from models.decision_engine import build_decision

router = APIRouter(prefix="/api", tags=["Forecast"])


@router.post("/forecast")
def forecast(request: ForecastRequest):
    try:
        result = build_decision(
            cargo_quantity_mt=request.quantity_mt,
            origin_port=request.destination_port,
            destination_port=request.destination_port,
            contract_duration_months=request.contract_duration_months,
            planned_voyages=request.planned_voyages,
            sailing_days=3.0,
            verified_only=False,
        )

        # Make sure the response always has the expected input structure.
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

        result["trade_context"] = {
            "origin_country": request.origin_country,
            "origin_port": request.origin_port,
            "destination_port": request.destination_port,
            "optimization_mode": "INDIAN_DESTINATION_PROTOTYPE",
        }

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:
        print(f"FORECAST ERROR: {type(exc).__name__}: {exc}")

        raise HTTPException(
            status_code=500,
            detail=f"Internal prediction error: {exc}"
        )