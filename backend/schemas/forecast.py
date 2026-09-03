from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    commodity: str = Field(..., min_length=1)

    quantity_mt: float = Field(
        ...,
        gt=0,
        description="Cargo quantity in metric tonnes",
    )

    origin_country: str = Field(
        ...,
        min_length=1,
        description="International cargo origin country",
    )

    origin_port: str = Field(
        ...,
        min_length=1,
        description="International cargo origin port",
    )

    destination_port: str = Field(
        ...,
        min_length=1,
        description="Indian East Coast destination port",
    )

    contract_duration_months: int = Field(
        ...,
        ge=1,
        le=12,
        description="Contract duration in months",
    )

    planned_voyages: int = Field(
        ...,
        ge=1,
        le=24,
        description="Number of planned voyages",
    )