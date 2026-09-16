# Freight Prediction

AI-powered freight forecasting and chartering decision-support system for bulk cargo procurement to India's East Coast ports.

## 🚀 Live Deployments

| Service                  | Link                                                                           |
| ------------------------ | ------------------------------------------------------------------------------ |
| 🌐 **Frontend / Vercel** | https://freight-prediction.vercel.app/                                         |
| 💻 **GitHub Repository** | https://github.com/RajCodes2006/freight-prediction                             |
| ⚙️ **Backend / Render**  | The backend service is deployed through Render                                 |

## Overview

Bulk cargo chartering is often handled through repeated spot-market decisions based on current freight rates. This reactive approach makes it difficult to identify favorable market-entry windows, select the most suitable vessel, manage port constraints, and decide when short-term or medium-term multiple-voyage contracts are economically preferable.

**Freight Prediction** aims to move this process from reactive decision-making toward a predictive, data-driven approach.

The system combines freight-market forecasting with vessel specifications, port constraints, congestion, voyage economics, and contract-risk analysis to support more informed chartering decisions.

## Objectives

* Forecast future freight-market conditions for different vessel classes.
* Estimate 7, 30, 60, and 90-day market movements.
* Identify favorable charter-entry windows.
* Support vessel-type selection.
* Account for Indian East Coast port constraints.
* Estimate idle-time and operational risks.
* Compare spot chartering with short-term and medium-term multiple-voyage strategies.
* Provide actionable recommendations through a dashboard.

## Vessel Classes

The initial forecasting layer covers:

* **Handysize**
* **Supramax**
* **Panamax**
* **Capesize**

## Target Trade Network

The intended system will eventually cover bulk-cargo movements from major origins such as:

* Australia
* Indonesia
* United States
* Mozambique
* Russia

to East Coast Indian ports including:

* Paradip
* Visakhapatnam
* Gangavaram
* Gopalpur
* Dhamra
* Sagar / Sandheads
* Haldia

## Current Data

The current prototype uses historical Baltic dry-bulk index data containing:

* **HSI** — Handysize
* **SI** — Supramax
* **PI** — Panamax
* **CI** — Capesize

### Historical Dataset

**1 August 2012 → 31 July 2019**

The current historical dataset is used for model development and experimentation. It is an index dataset and should **not** be interpreted as route-specific USD/MT freight quotations.

Additional data sources will be integrated later for:

* Route-level freight rates
* Port activity
* Port congestion
* Vessel specifications
* Bunker / fuel prices
* Commodity prices
* Economic indicators
* Port infrastructure constraints

## Current System

The current prototype includes:

### 📈 Forecasting

* Multi-horizon freight forecasting
* Model comparison
* Walk-forward evaluation
* Forecast confidence scoring

### 🚢 Vessel & Port Analysis

* Vessel feasibility analysis
* Port and berth constraints
* Congestion analysis
* Vessel suitability evaluation

### 💰 Voyage Economics

* Voyage cost estimation
* Chartering strategy analysis
* Contract optimization
* Spot vs. multiple-voyage strategy comparison

### ⚠️ Risk & Decision Support

* Operational risk analysis
* Idle-time estimation
* Risk optimization
* Master decision engine
* Dashboard-based recommendations

### 🧩 Architecture

* **Frontend:** React + Vite
* **Backend:** FastAPI
* **Forecasting / ML:** Python
* **Deployment:** Vercel + Render
* **Version Control:** GitHub

## System Architecture

```text
                    ┌─────────────────────┐
                    │   Historical Data   │
                    │  BDI / Port / etc.  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Feature Pipeline  │
                    │  Cleaning + Features│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   ML Forecasting    │
                    │  7 / 30 / 60 / 90d  │
                    └──────────┬──────────┘
                               │
                               ▼
             ┌─────────────────────────────────┐
             │       Decision Engine            │
             │                                 │
             │ Vessel │ Port │ Cost │ Risk     │
             │        │      │      │           │
             └────────────────┬────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   React Dashboard   │
                    │ Recommendations &   │
                    │ Decision Support    │
                    └─────────────────────┘
```

## Project Structure

```text
freight-prediction/
│
├── backend/
│   ├── api/
│   ├── schemas/
│   └── main.py
│
├── dashboard/
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── bdi_clean.csv
│   ├── freight_rates.csv
│   ├── model_dataset.csv
│   ├── forecast_dataset.csv
│   ├── multihorizon_model_dataset.csv
│   ├── model_competition_results.csv
│   ├── walk_forward_results.csv
│   └── ports.csv
│
├── models/
│   ├── inference/
│   │   ├── load_models.py
│   │   └── predict.py
│   │
│   ├── optimization/
│   │   ├── chartering_strategy.py
│   │   ├── contract_optimizer.py
│   │   ├── port_congestion.py
│   │   ├── port_constraint.py
│   │   ├── port_loader.py
│   │   ├── port_time.py
│   │   ├── risk_optimizer.py
│   │   ├── vessel_cost.py
│   │   ├── vessel_optimizer.py
│   │   └── voyage_cost.py
│   │
│   ├── inspect_bdi.py
│   ├── clean_bdi.py
│   ├── analyze_bdi.py
│   ├── create_features.py
│   ├── create_forecast_targets.py
│   ├── create_multihorizon_features.py
│   ├── train_models.py
│   ├── train_multihorizon_models.py
│   ├── train_arima_models.py
│   ├── evaluate_walk_forward.py
│   ├── forecast_confidence.py
│   ├── model_registry.py
│   └── decision_engine.py
│
├── kaggle_datasets/
│
├── requirements.txt
└── README.md
```

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/RajCodes2006/freight-prediction.git
cd freight-prediction
```

### 2. Backend Setup

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI backend:

```bash
uvicorn backend.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

### 3. Frontend Setup

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The Vite development server will provide the local dashboard URL in the terminal.

## Deployment

The project uses a split deployment architecture:

```text
                ┌──────────────────────┐
                │     User Browser     │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │       Vercel         │
                │   React + Vite UI    │
                └──────────┬───────────┘
                           │ API Requests
                           ▼
                ┌──────────────────────┐
                │       Render         │
                │     FastAPI API      │
                └──────────────────────┘
```

### Production Links

**Frontend**

https://freight-prediction.vercel.app/

**GitHub**

https://github.com/RajCodes2006/freight-prediction

**Render**

The backend service is deployed through Render.

## Future Development

Planned improvements include:

* Integration of live freight-rate data.
* Route-specific freight prediction.
* Real-time port congestion data.
* AIS-based vessel tracking.
* Live bunker-price integration.
* Expanded vessel specifications.
* More detailed berth and draft constraints.
* Commodity-price integration.
* Macroeconomic indicators.
* Improved probabilistic forecasting.
* Automated chartering alerts.
* Historical backtesting of chartering strategies.
* Production-grade authentication and user management.

## Disclaimer

This project is a **decision-support prototype** intended for research, experimentation, and demonstration.

Forecasts and recommendations are model outputs and should not be treated as guaranteed future freight prices, commercial quotations, or financial advice.

---

## 👨‍💻 Project

**Freight Prediction**

AI-driven freight forecasting and chartering decision-support platform for bulk cargo procurement and maritime logistics.
