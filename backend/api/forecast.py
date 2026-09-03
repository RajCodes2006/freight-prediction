from fastapi import APIRouter, HTTPException

from backend.schemas.forecast import ForecastRequest
from models.decision_engine import build_decision


router = APIRouter(
    prefix="/api",
    tags=["Forecast"]
)


@router.post("/forecast")
def forecast(request: ForecastRequest):
    """
    Run the complete freight prediction and chartering
    decision pipeline.
    """

    try:

        result = build_decision(
            cargo_quantity_mt=request.quantity_mt,
            origin_port=request.origin,
            destination_port=request.destination,
            contract_duration_months=(
                request.contract_duration_months
            ),
            planned_voyages=6,
            sailing_days=3.0,
            loading_queue_days=1.0,
            discharge_queue_days=1.5,
            verified_only=False,
        )

        # --------------------------------------------------
        # Add user-provided inputs that are not currently
        # used by the ML model.
        # --------------------------------------------------

        result["input"]["commodity"] = request.commodity
        result["input"]["requested_vessel_type"] = (
            request.vessel_type
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )