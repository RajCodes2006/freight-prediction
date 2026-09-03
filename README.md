# Freight Prediction

AI-powered freight forecasting and chartering decision-support system for bulk cargo procurement to India's East Coast ports.

## Overview

Bulk cargo chartering is often handled through repeated spot-market decisions based on current freight rates. This reactive approach makes it difficult to identify favorable market-entry windows, select the most suitable vessel, manage port constraints, and decide when short-term or medium-term multiple-voyage contracts are economically preferable.

**Freight Prediction** aims to move this process from reactive decision-making toward a predictive, data-driven approach.

The system is being developed to forecast dry-bulk freight market conditions for different vessel classes and eventually combine those forecasts with vessel specifications, port constraints, congestion, market conditions, and contract economics.

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

## Project Structure

```text
freight-prediction/
│
├── backend/
│
├── dashboard/
│
├── data/
│   ├── bdi_clean.csv
│   ├── freight_rates.csv
│   ├── model_dataset.csv
│   ├── forecast_dataset.csv
│   └── multihorizon_model_dataset.csv
│
├── models/
│   ├── inspect_bdi.py
│   ├── clean_bdi.py
│   ├── analyze_bdi.py
│   ├── create_features.py
│   ├── create_forecast_targets.py
│   ├── create_multihorizon_features.py
│   ├── train_models.py
│   ├── train_multihorizon_models.py
│   ├── train_arima_models.py
│   └── evaluate_walk_forward.py
│
├── kaggle_datasets/
│
├── requirements.txt
└── README.md