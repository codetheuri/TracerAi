# TracerAI

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-orange.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

This repository contains the "AI brain" for the **TracerAI** platform. It is a data-processing backend built in Python using **FastAPI** and **Scikit-learn**, designed to work with the **[go-Tracer](https://github.com/codetheuri/go-Tracer)** sensor.

Its job is to ingest, enrich, analyze, and store the `FlowEvent` summaries sent by one or more `go-Tracer` agents.

## Features

* **High-Speed Ingestion:** Built with **FastAPI** to asynchronously handle thousands of incoming flow events.
* **Real-time Enrichment:** Automatically enriches incoming flows with **GeoIP** data (e.g., "Local" -> "USA").
* **Advanced Feature Engineering:** Includes an offline script (`feature_engineer.py`) to aggregate raw flows into behavioral "fingerprints" for each host (e.g., `port_entropy`, `unique_dest_ips`).
* **AI Anomaly Detection:** Uses an **IsolationForest** model (from `scikit-learn`) trained on these advanced fingerprints to detect anomalous host behavior.
* **Simple Dashboard:** Includes a basic HTML dashboard (served by Jinja2) to view the latest raw flow data.

## Architecture & Workflow

The backend uses a multi-stage pipeline, separating "fast" collection from "slow" analysis.

1.  **Stage 1: Collect (Real-time)**
    * The `go-Tracer` agent sends a `FlowEvent` to the **`POST /ingest`** endpoint.
    * FastAPI enriches the event with GeoIP data and saves it to the `flow_events` table.

2.  **Stage 2: Engineer Features (Offline)**
    * The **`python feature_engineer.py`** script is run (e.g., every 10 minutes via cron).
    * It queries the `flow_events` table, aggregates data by host, and saves the "fingerprints" to the `host_behavior_summary` table.

3.  **Stage 3: Train AI (Offline)**
    * The **`python train.py`** script is run.
    * It loads all "fingerprints" from the `host_behavior_summary` table and trains the `IsolationForest` AI model, saving it to a `.pkl` file.

4.  **Stage 4: Detect (On-Demand)**
    * A request to **`POST /run-analysis`** triggers a background task.
    * This task runs the feature engineering (Stage 2) and then runs the AI (Stage 3) on the new data, printing any `🚨 [AI ALERT] 🚨` messages.

## How to Run (Setup & Workflow)

### 1. Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/codetheuri/TracerAI.git](https://github.com/codetheuri/TracerAI.git)
    cd TracerAI-Backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download GeoIP Database:**
    * Sign up for a free MaxMind account at [maxmind.com](https://www.maxmind.com/en/geolite2/signup).
    * Download the `GeoLite2-Country.mmdb` file and place it in the root of this project folder.

### 2. The 4-Step Workflow

You must run these steps in order.

**Step 1: Collect Data (Let it run for 10-15 minutes)**
* Start the FastAPI server (this creates the database):
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
* Start your **[go-Tracer](https://github.com/codetheuri/go-Tracer)** agent (in its own terminal), making sure its `AGENT_ENDPOINT_URL` is pointed to `http://127.0.0.1:8000/ingest`.
* Let this run and collect raw flow data.
* Once done, **stop the `uvicorn` server (Ctrl+C)** to unlock the database.

**Step 2: Engineer Features**
* Run the feature engineering script to process the raw data:
    ```bash
    python feature_engineer.py
    ```

**Step 3: Train the AI**
* Run the training script to build your AI model:
    ```bash
    python train.py
    ```

**Step 4: Go "Live"**
* Restart the FastAPI server. It will now load the new AI models.
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
* You can view the live data stream on the dashboard at `http://127.0.0.1:8000/`.
* To trigger an analysis of the latest data, send a POST request:
    ```bash
    curl -X POST [http://127.0.0.1:8000/run-analysis](http://127.0.0.1:8000/run-analysis)
    ```