# Intelligent Logistics & Delivery Route Optimization System

## Features
- Reproducible synthetic master and transaction data.
- MySQL persistence using SQLAlchemy models.
- FastAPI endpoints for sites, deliveries, vehicles, routes and analytics.
- Capacity-aware greedy route assignment starter.
- Route simulation and rule-based exception detection.
- Streamlit control-tower dashboard.
- Separate ground-truth anomaly catalogue and generated-data checksums.

## Setup (Windows)
1. Install Python 3.11+, MySQL 8+, and VS Code.
2. Create a MySQL database: `CREATE DATABASE logistics_db;`
3. Copy `.env.example` to `.env` and set your MySQL password.
4. Create and activate a venv:
   `python -m venv venv`
   `venv\Scripts\activate`
5. Install: `pip install -r requirements.txt`
6. Generate starter data: `python -m backend.services.data_generator --mode starter --seed 20261022`
7. Validate CSVs: `python -m backend.services.validation`
8. Create tables: `python -m backend.init_db`
9. Import CSV data into MySQL: use the supplied `scripts/load_csv_to_mysql.py`.
10. Start API: `uvicorn backend.main:app --reload`
11. Start dashboard in another terminal: `streamlit run frontend/app.py`

## Full dataset
`python -m backend.services.data_generator --mode full --seed 20261022`

Full mode creates 500 sites, 2,000 deliveries, 100 vehicles, 100 drivers, 30 days of shifts, and a daily directed travel matrix. The full travel matrix can be large; allow sufficient disk space and runtime.

## Reproducibility
Run the same generator twice with the same mode and seed. `data/generated/checksums.json` records SHA-256 hashes for generated CSV files. Compare checksum files between runs.

## Important scope notes
This is a functional starter implementation, not a production-grade VRP solver. The route planner currently uses a deterministic greedy capacity-aware assignment and a fixed synthetic travel leg for its initial demonstration. It does not yet enforce every time-window, vehicle restriction, driver qualification, multi-trip, or traffic-matrix constraint during optimization. The anomaly catalogue includes all requested ground-truth scenarios; the operational anomaly detector checks route capacity, duplicate stops, sequence times, shift end and coordinate bounds. Stop omission is detected by comparing assigned deliveries to route stops in a future validation enhancement. Replace the greedy planner with a fully constrained OR-Tools model before production use.
