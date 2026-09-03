from typing import Literal

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    commodity: str
    quantity_mt: float = Field(..., gt=0)
    origin: str
    destination: str
    contract_duration_months: int = Field(
        ...,
        ge=1,
        le=12,
    )
    vessel_type: Literal[
        "HSI",
        "SI",
        "PI",
        "CI",
    ]