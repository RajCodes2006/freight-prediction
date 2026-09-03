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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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