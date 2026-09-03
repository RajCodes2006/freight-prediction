from fastapi import FastAPI

from backend.api.forecast import router as forecast_router


# ============================================================
# FREIGHT PREDICTION API
# ============================================================

app = FastAPI(
    title="Freight Prediction API",
    description=(
        "AI-powered freight forecasting and "
        "chartering decision-support API."
    ),
    version="1.0.0"
)


# ------------------------------------------------------------
# Routers
# ------------------------------------------------------------

app.include_router(
    forecast_router
)


# ------------------------------------------------------------
# Root endpoint
# ------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Freight Prediction API is running",
        "status": "ok"
    }


# ------------------------------------------------------------
# Health endpoint
# ------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }