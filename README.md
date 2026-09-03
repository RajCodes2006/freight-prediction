# Freight Prediction

AI-powered freight forecasting and chartering decision-support system for bulk cargo procurement to India's East Coast ports.

## Overview

Bulk cargo chartering is often handled through repeated spot-market decisions based on current freight rates. This reactive approach makes it difficult to identify favorable market-entry windows, select the most suitable vessel, manage port constraints, and decide when short-term or medium-term multiple-voyage contracts are economically preferable.

**Freight Prediction** aims to move this process from reactive decision-making toward a predictive, data-driven approach.

The system combines freight-market forecasting with vessel specifications, port constraints, congestion, voyage economics, and contract-risk analysis to support more informed chartering decisions.

## Objectives

- Forecast future freight-market conditions for different vessel classes.
- Estimate 7, 30, 60, and 90-day market movements.
- Identify favorable charter-entry windows.
- Support vessel-type selection.
- Account for Indian East Coast port constraints.
- Estimate idle-time and operational risks.
- Compare spot chartering with short-term and medium-term multiple-voyage strategies.
- Provide actionable recommendations through a dashboard.

## Vessel Classes

The initial forecasting layer covers:

- Handysize
- Supramax
- Panamax
- Capesize

## Target Trade Network

The intended system will eventually cover bulk-cargo movements from major origins such as:

- Australia
- Indonesia
- United States
- Mozambique
- Russia

to East Coast Indian ports including:

- Paradip
- Visakhapatnam
- Gangavaram
- Gopalpur
- Dhamra
- Sagar/Sandheads
- Haldia

## Current Data

The current prototype uses historical Baltic dry-bulk index data containing:

- HSI — Handysize
- SI — Supramax
- PI — Panamax
- CI — Capesize
- DTI
- CTI

The current historical dataset covers:

**1 August 2012 → 31 July 2019**

The current dataset is used for model development and experimentation. It is an index dataset and should not be interpreted as route-specific USD/MT freight quotations.

Additional data sources will be integrated later for:

- Route-level freight rates
- Port activity
- Port congestion
- Vessel specifications
- Bunker/fuel prices
- Commodity prices
- Economic indicators
- Port infrastructure constraints

## Current System

The current prototype includes:

- Multi-horizon freight forecasting
- Model comparison and walk-forward evaluation
- Forecast confidence scoring
- Vessel feasibility analysis
- Port and berth constraints
- Congestion analysis
- Voyage cost estimation
- Contract optimization
- Risk analysis
- Master decision engine
- FastAPI backend
- React frontend

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