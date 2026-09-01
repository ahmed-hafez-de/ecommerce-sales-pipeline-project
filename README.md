# 🏷️ E-Commerce Data Warehouse

> A production-grade SQL data warehouse built on the Medallion Architecture pattern — transforming messy retail CSV into clean, analytics-ready tables inside PostgreSQL, orchestrated with Python and containerized infrastructure.

---

## 🚨 The Problem

E-commerce teams are drowning in dirty data. Raw transaction logs from online retail systems are riddled with missing customer IDs, negative quantities (returns), inconsistent date formats, and corrupted string values. Running analytics directly on these files means:
    - **Marketing** can't reliably identify top customers or revenue trends.
    - **Finance** gets wrong numbers because `Quantity` contains returns mixed with sales.
    - **Analysts** waste hours debugging type errors instead of delivering insights.

## 💡 The Solution

This project builds a single source of truth by ingesting raw e-commerce data into a structured PostgreSQL warehouse using the Medallion Architecture (Bronze → Silver → Gold). Each layer progressively cleans, conforms, and models the data so downstream teams can query with confidence.

Key business questions this warehouse answers:

    - Who are our top 10 customers by lifetime revenue?
    - What are the monthly sales trends broken down by country?
    - Which products drive the most revenue vs. volume?
    - How is transaction volume distributed geographically?

---

## 🏗️ Architecture Overview

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Database** | PostgreSQL 14+ | Warehouse engine, containerized via Docker |
| **Language** | Python 3.12+ | Ingestion pipelines and orchestration logic |
| **Package Manager** | uv | Fast, modern Python dependency management |
| **DB Driver** | psycopg2 | High-performance PostgreSQL adapter with copy_expert() |
| **Config** | python-dotenv | Secure credential management via .env files |
| **Code Quality** | Ruff | Blazing-fast linting and formatting |
| **Infrastructure** | Docker | Isolated, reproducible database environment |
| **Orchestration** | Apache Airflow | Scheduled DAGs for recurring ETL runs |

---

## 📂 Project Structure

---

## ⚖️ Design Decisions & Trade-Offs

1. **Why `TEXT` columns in Bronze instead of strict types?**
    - **Decision:** The raw landing table uses generic TEXT fields for every column.
    - **Trade-off:** Raw loading guarantees ingestion never crashes from messy source formats (like mixed dates, blank IDs, or string-encoded numbers). Cleaning and validation are handled later in the Silver layer.

2. **Why stream via `STDIN` instead of `COPY FROM` file paths?**
    - **Decision:** The pipeline uses psycopg2.copy_expert() with a Python file stream piped to STDIN.
    - **Trade-off:** Since PostgreSQL is isolated in Docker without host file access, streaming over STDIN bypasses container boundaries completely. This eliminates shared mounts and path mapping headaches while boosting speed by avoiding an extra disk I/O hop.

3. **Why PG* environment variables?**
    - Decision: Connection config uses PGHOST, PGPORT, PGUSER, etc. instead of custom names like DB_HOST.
    - **Trade-off:** Because psycopg2 natively reads PG* environment variables, the driver auto-configures itself without manual connection string parsing. This reduces lines of code and eliminates places where credentials could accidentally leak into logs.

4. **Why Truncate-and-Reload for Bronze?**
    - **Decision:** Every Bronze run wipes the table and reloads from scratch.
    - **Trade-off:** For this dataset size (~500K rows), a full reload takes seconds and eliminates complex incremental merge logic. As data volumes scale, incremental loading will be introduced in the Silver and Gold layers where performance impact matters most.

---

## 🚀 Getting Started

### Prerequisites

    - **Docker** installed and running.
    - **Python 3.12+** with `uv` installed.
    - **Git** (to clone the repo).

### Step 1 — Spin Up PostgreSQL

    ```bash
    docker run --name local-postgres \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -p 54876:5432 \
    -d postgres:latest
    ```

### Step 2 — Configure Credentials

Copy the example env file and fill in your local values:

    ```bash
    cp .env.example .env
    ```

### Step 3 — Install Dependencies

    ```bash
    uv sync
    ```

### Step 4 — Run the Bronze Pipeline

    ```bash
    uv run python src/ingestion/ingest_bronze.py
    ```
---

## 🏅 Medallion Pipeline Stages

| Layer | What Happens |
| :--- | :--- |
| 🟫 **Bronze** | Raw CSV → PostgreSQL via atomic truncate-and-load. All columns stored as TEXT. |
