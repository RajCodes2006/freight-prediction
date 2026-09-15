from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.forecast import router as forecast_router


app = FastAPI(
    title="Freight Prediction API",
    description=(
        "AI-powered freight forecasting and "
        "chartering decision-support API."
    ),
    version="1.0.0",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------
#
# allow_origins=["*"] combined with allow_credentials=True is invalid
# per the Fetch/CORS spec (browsers reject credentialed requests to a
# wildcard origin). The frontend doesn't send credentials, so pin
# allow_credentials to False and keep the wildcard for now; if
# cookie/auth-based requests are added later, replace the wildcard
# with an explicit list of allowed frontend origins instead.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Routes
# --------------------------------------------------

app.include_router(forecast_router)


@app.get("/")
def root():
    return {
        "message": "Freight Prediction API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }