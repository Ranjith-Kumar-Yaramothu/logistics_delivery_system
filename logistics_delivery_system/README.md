# Intelligent Logistics & Delivery Route Optimization System

## Project Overview

The **Intelligent Logistics & Delivery Route Optimization System** is a Python-based application designed to manage delivery operations, assign vehicles, plan delivery routes, simulate delivery activities, detect operational anomalies, and generate analytics reports.

The system provides a centralized dashboard for monitoring delivery performance and accessing logistics data.

## Key Features

- **Master Data Management:** Manage customer sites, vehicles, and delivery information.
- **Synthetic Data Generation:** Generate sample logistics datasets for testing and development.
- **Data Validation:** Validate generated datasets before loading them into the database.
- **Vehicle Assignment:** Assign eligible vehicles based on delivery capacity requirements.
- **Route Planning:** Generate delivery routes based on available vehicles, drivers, delivery schedules, and time windows.
- **Route Simulation:** Simulate route execution and update delivery outcomes.
- **Anomaly Detection:** Identify operational issues such as delivery delays, capacity violations, duplicate stops, and shift overruns.
- **Ground Truth Evaluation:** Test anomaly detection rules against nine predefined scenarios.
- **Analytics Dashboard:** Monitor delivery statuses, route performance, and operational statistics.
- **Data Export:** Download delivery, route, route-stop, anomaly, and analytics reports.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend | FastAPI |
| Frontend | Streamlit |
| Database | MySQL |
| ORM | SQLAlchemy |
| Data Processing | Pandas |
| Visualization | Plotly |
| API Testing | Swagger UI |
| Data Format | CSV, Excel |

## Project Structure

```text
logistics_delivery_system/
│
├── backend/
│   ├── routers/
│   ├── services/
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── main.py
│   └── init_db.py
│
├── frontend/
│   ├── pages/
│   │   ├── 1_Master_Data.py
│   │   ├── 2_Deliveries.py
│   │   ├── 3_Route_Planning.py
│   │   ├── 5_Analytics.py
│   │   └── 6_Exports.py
│   └── app.py
│
├── data/
│   ├── generated/
│   └── ground_truth/
│
├── scripts/
│   └── load_csv_to_mysql.py
│
├── docs/
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd logistics_delivery_system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure MySQL

Create the database in MySQL Workbench:

```sql
CREATE DATABASE logistics_db;
```

Configure the database connection using your local environment settings. Do not upload passwords or other credentials to GitHub.

### 5. Initialize Database Tables

```bash
python -m backend.init_db
```

### 6. Generate Synthetic Data

Generate the starter dataset:

```bash
python -m backend.services.data_generator --mode starter --seed 20261022
```

### 7. Validate Generated Data

```bash
python -m backend.services.validation
```

### 8. Load Data into MySQL

```bash
python -m scripts.load_csv_to_mysql
```

## Running the Application

### Start the FastAPI Backend

Open a terminal and run:

```bash
python -m uvicorn backend.main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

Swagger API documentation:

`http://127.0.0.1:8000/docs`

### Start the Streamlit Frontend

Open another terminal and run:

```bash
python -m streamlit run frontend/app.py
```

The dashboard will open in your browser.

## Route Planning Workflow

1. Select a delivery planning date.
2. Enter the maximum number of deliveries to plan.
3. Generate routes through the dashboard or API.
4. Review assigned and unserved deliveries.
5. View the generated routes and their stops.
6. Simulate a route to update delivery statuses and outcomes.
7. Review detected anomalies and analytics.

## Anomaly Detection

The system includes rule-based checks for the following scenarios:

1. Unexpected delivery delay.
2. Weight capacity exceeded.
3. Volume capacity exceeded.
4. Duplicate delivery.
5. Arrival before previous departure.
6. Driver shift exceeded.
7. Customer coordinates outside the configured region.
8. Planned arrival outside the customer time window.
9. Actual arrival outside the customer time window.

The ground truth evaluator runs controlled test scenarios to verify the detection rules.

Run the evaluator using:

```bash
python -m backend.services.ground_truth_evaluator
```

## Data Export

The application provides the following downloadable reports:

- Deliveries CSV
- Routes CSV
- Route Stops CSV
- Anomaly Report CSV
- Logistics Analytics Excel Workbook

These reports are available through the Data Export Center and the backend API.

## Reproducibility

The synthetic data generator uses a fixed random seed:

```text
20261022
```

Using the same seed and configuration helps reproduce the generated starter dataset.

## Current Implementation and Limitations

This project is a working prototype developed for logistics planning and operational monitoring.

- The current verified dataset is the starter dataset.
- Route planning currently uses a greedy assignment approach.
- Anomaly detection is rule-based.
- Route simulation uses deterministic logic.
- The ground truth evaluation verifies predefined test scenarios; it is not an independent machine-learning accuracy evaluation.
- Results depend on the generated data and configured database.

These limitations identify areas for future improvement, including advanced route optimization, larger datasets, realistic traffic simulation, and predictive analytics.

## Future Enhancements

- Implement OR-Tools for advanced vehicle routing optimization.
- Add realistic traffic and travel-time scenarios.
- Improve vehicle and driver constraint handling.
- Introduce machine-learning-based anomaly detection.
- Add real-time GPS tracking.
- Improve dashboard filtering and reporting.
- Support larger operational datasets.

## Project Objective

The main objective is to build an integrated logistics platform that improves delivery planning, supports operational monitoring, identifies delivery-related issues, and provides useful reports for decision-making.
