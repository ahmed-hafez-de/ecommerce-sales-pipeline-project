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

## 🏅 Medallion Pipeline Stages

| Layer | What Happens |
| :--- | :--- |
| 🟫 **Bronze** | Raw CSV → PostgreSQL via atomic truncate-and-load. All columns stored as TEXT. |
| ⬜ **Silver** | Bronze → cleaned, typed, standardized transaction data with deduplication and business rules. |
| 🟨 **Gold** | Star schema (Fact & Dimension tables) ready for BI dashboards. |

### 🔍 Silver Layer Business Logic

To keep this README clear and concise, the complete data cleaning rules—including deduplication, type casting, and transaction filtering are documented separately. Read the full breakdown in the Silver Layer Transformations Guide.

👉 **[Read the Silver Layer Transformations Guide](docs/silver_layer_transformations.md)**

### ⭐ Gold Layer Data Modeling (Star Schema)

The Gold layer transforms conformed Silver data into a **Star Schema** tailored for fast OLAP queries, BI reporting, and executive dashboards.

```text
                    ┌─────────────────┐
                    │   dim_product   │
                    │─────────────────│
                    │ product_key PK  │
                    │ stock_code  U   │
                    │ description     │
                    └────────▲────────┘
                             │
┌──────────────┐    ┌────────┴────────┐    ┌──────────────┐
│   dim_date   │    │   fact_sales    │    │ dim_customer │
│──────────────│    │─────────────────│    │──────────────│
│ date_key PK  │───▶│ sales_id PK     │◀───│ customer_key │
│ full_date    │    │ invoice_no      │    │ customer_id U│
│ year         │    │ date_key FK     │    └──────────────┘
│ quarter      │    │ product_key FK  │
│ month        │    │ customer_key FK │
│ day_of_month │    │ quantity        │
│ day_name     │    │ unit_price      │
│ is_weekend   │    │ total_amount    │
└──────────────┘    │ country         │
                    │ is_cancelled    │
                    └─────────────────┘
```

---

## 🧪 Automated Testing & QA

This project uses an automated testing suite with **Pytest** to keep the pipeline reliable without risking real data. Instead of using fake data mocks, the tests run against a real, isolated PostgreSQL sandbox database (`ecommerce_platform_test`). This test database automatically spins up, verifies the pipeline's logic, and cleans up after itself so development data stays completely safe.

👉 **[Read the Data Pipeline Integration Testing Guide](docs/testing.md)**

---

## 🏗️ Architecture Overview

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Database** | PostgreSQL 14+ | Warehouse engine, containerized via Docker |
| **Language** | Python 3.12+ | Ingestion pipelines and orchestration logic |
| **Package Manager** | uv | Fast, modern Python dependency management |
| **DB Driver** | psycopg2 | High-performance PostgreSQL adapter with `copy_expert()` |
| **Config** | python-dotenv | Secure credential management via `.env` files |
| **Code Quality** | Ruff | Blazing-fast linting and formatting |
| **Infrastructure** | Docker | Isolated, reproducible database environment |
| **Orchestration** | Apache Airflow | Scheduled DAGs for recurring ETL runs |

---

## ⚖️ Design Decisions & Trade-Offs

1. **Why `TEXT` columns in Bronze instead of strict types?**
    - **Decision:** The raw landing table uses generic `TEXT` fields for every column.
    - **Trade-off:** Raw loading guarantees ingestion never crashes from messy source formats (like mixed dates, blank IDs, or string-encoded numbers). Cleaning and validation are handled later in the Silver layer.

2. **Why stream via `STDIN` instead of `COPY FROM` file paths?**
    - **Decision:** The pipeline uses `psycopg2.copy_expert()` with a Python file stream piped to `STDIN`.
    - **Trade-off:** Since PostgreSQL is isolated in Docker without host file access, streaming over `STDIN` bypasses container boundaries completely. This eliminates shared mounts and path mapping headaches while boosting speed by avoiding an extra disk I/O hop.

3. **Why `PG` environment variables?**
    - **Decision:** Connection config uses `PGHOST`, `PGPORT`, `PGUSER`, etc. instead of custom names like DB_HOST.
    - **Trade-off:** Because `psycopg2` natively reads `PG` environment variables, the driver auto-configures itself without manual connection string parsing. This reduces lines of code and eliminates places where credentials could accidentally leak into logs.

4. **Why Truncate-and-Reload for Bronze?**
    - **Decision:** Every Bronze run wipes the table and reloads from scratch.
    - **Trade-off:** For this dataset size (~500K rows), a full reload takes seconds and eliminates complex incremental merge logic. As data volumes scale, incremental loading will be introduced in the Silver and Gold layers where performance impact matters most.

5. **Why use Python for orchestration instead of putting everything in SQL?**
    - **Decision:** SQL handles the data transformation while Python handles execution, transaction management, error handling, logging, and validation.
    - **Trade-off:** This provides a clean separation of responsibilities and makes the pipeline easier to integrate later with an orchestrator such as Airflow.

6. **Why use a transaction to wrap data insertion processes?**
    - **Decision:** Table preparation, truncation, and data loading operations are executed within a single database transaction.
    - **Trade-off:** If any part of the insertion process fails, the entire transaction rolls back. This prevents tables from being left empty, duplicated, or partially loaded after a failed run.

---

## 📂 Project Structure

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

### Step 4 — Run the Pipeline

```bash
# Step 1: Load Raw CSV to Bronze
uv run python src/ingestion/ingest_bronze.py

# Step 2: Clean types, format fields, and remove duplicate rows into the Silver layer
uv run python src/transformation/transform_silver.py

# Step 3: Build and load the Gold layer Star Schema (Fact and Dimensions)
uv run python src/transformation/transform_gold.py
```

### Step 5 — Run Automated Tests

```bash
uv run python -m pytest -v
```
