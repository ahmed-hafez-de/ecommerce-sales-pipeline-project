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

### 🔄 Automated Orchestration with Apache Airflow

The entire Medallion data engineering lifecycle is managed using containerized **Apache Airflow**. Airflow handles scheduling, automated retries, failure tracking, and visual task orchestration without running heavy transformations inside its own memory space.

Airflow maps the pipeline tasks sequentially as a Directed Acyclic Graph (DAG):

```text
 ┌──────────────────────┐       ┌───────────────────────────┐       ┌─────────────────────────┐
 │ run_bronze_ingestion │ ────▶ │ run_silver_transformation │ ────▶ │ run_gold_transformation │
 └──────────────────────┘       └───────────────────────────┘       └─────────────────────────┘
      (Ingest CSV)                   (Clean & Deduplicate)             (Load Rerun-Safe Schema)
```

The DAG runs **idempotently**. If any layer fails due to a network or database interruption, Airflow isolates the crash point. You can fix the issue and retry only the broken layer from the dashboard UI without corrupting rows or losing downstream transaction metrics.

The containerized infrastructure explicitly decouples the coordination engine from the analytical storage layer:

```text
                               ┌───────────────────────────────────┐
                               │       Docker Compose Environment  │
                               └─────────────────┬─────────────────┘
                                                 │
                       ┌─────────────────────────┴─────────────────────────┐
                       ▼                                                   ▼
     ┌──────────────────────────────────┐                ┌────────────────────────────────────┐
     │       airflow_metadata_db        │                │      ecommerce_warehouse_db        │
     │──────────────────────────────────│                │────────────────────────────────────│
     │  • DATABASE=airflow              │                │  • DATABASE=ecommerce_platform     │
     │  • Tracks Task States / DAG Runs │                │  • DATABASE=ecommerce_platform_test│
     │  • Hidden from Business Users    │                │  • Port: 54876                     │
     └──────────────────────────────────┘                └────────────────────────────────────┘
```

---

## 🧪 Automated Testing & QA

This project uses an automated testing suite with **Pytest** to keep the pipeline reliable without risking real data. Instead of using fake data mocks, the tests run against a real, isolated PostgreSQL sandbox database (`ecommerce_platform_test`). This test database automatically spins up, verifies the pipeline's logic, and cleans up after itself so development data stays completely safe.

👉 **[Read the Data Pipeline Integration Testing Guide](docs/testing.md)**

---

## 🏗️ Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                  Apache Airflow Core  ·  Orchestration Scheduler  ·  Shared Volume Log Streams                   │
│                    ↳ Isolated Backend Engine Context: [airflow_metadata_db Instance]                             │
│                                                                                                                  │
│  ┌─────────────┐      ┌───────────────────────────────────────────────────────────────────────┐    ┌───────────┐ │
│  │  Sources    │      │         ecommerce_warehouse_db Container  ·  PostgreSQL 15  (:54876)  │    │  Consume  │ │
│  │             │      │                                                                       │    │           │ │
│  │  UCI Online │      │  ┌───────────────┐   ┌────────────────┐   ┌────────────────────────┐  │    │ BI        │ │
│  │  Retail CSV │─────▶│  │ Bronze layer  │──▶│ Silver layer   │──▶│ Gold layer             │  │───▶│ Dashboards│ │
│  │             │      │  │ Raw landing   │   │ Cleaned Data   │   │ Star Schema            │  │    │ (Metabase)│ │
│  │  Metadata:  │      │  │               │   │                │   │                        │  │    │           │ │
│  │  - CSV text │      │  │ Load:         │   │ Load:          │   │  fact_sales            │  │    │ Streamlit │ │
│  │  - 541,909  │      │  │ - STDIN stream│   │ - SQL DML      │   │   ├─ dim_date          │  │    │ Web Apps  │ │
│  │    rows     │      │  │ - Truncate    │   │ - Idempotent   │   │   ├─ dim_product       │  │    │           │ │
│  │             │      │  │               │   │                │   │   └─ dim_customer      │  │    │ Ad-Hoc    │ │
│  │  Anomalies: │      │  │ Format:       │   │ Logic Rules:   │   │                        │  │    │ SQL       │ │
│  │  - null IDs │      │  │ - Generic     │   │ - type cast    │   │ Dynamic Audit Status:  │  │    │ Analytical│ │
│  │  - returns  │      │  │   TEXT fields │   │ - window dedupe│   │ • 536,639 Fact Rows    │  │    │ Queries   │ │
│  │  - formats  │      │  │               │   │ - cancellation │   │ • Exact Parity Check   │  │    │           │ │
│  │             │      │  │               │   │                │   │                        │  │    │           │ │
│  └─────────────┘      │  └───────────────┘   └────────────────┘   └────────────────────────┘  │    └───────────┘ │
│                       │                                                                       │                  │
│                       │   Development Tooling Network: Python 3.12  ·  uv  ·  Pytest  ·  Ruff │                  │
│                       └───────────────────────────────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

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

7. **Why isolate the Metadata Database from the Business Data Warehouse?**

    - **Decision:** Separate Postgres instances handle Airflow internal processing and e-commerce transactions.
    - **Trade-off:** This prevents data load drops from breaking core scheduler loops and maintains separate schemas for straightforward interview delivery.

---

## 📊 Core Environment Mappings

| **Service Component**            | **Internal Hostname**   | **Shared Local Port**   | **Default Credentials** |
|---                               | ---                     | ---                     | ---                     |
| **Data Warehouse DB**            | `warehouse-db`          | `54876`                 | `postgres` / `postgres` |
| **Airflow Webserver Dashboard**  | `airflow-webserver`     | `8080`                  | `admin` / `admin`       |
| **Airflow Metadata DB**          | airflow-db              | *Isolated internal*     | `airflow` / `airflow`   |

---

## 📂 Project Structure

```text
.
├── dags/
│   └── ecommerce_pipeline_dag.py     # Airflow DAG
├── data/
│   └── Online_Retail.csv             # Source dataset asset
├── docs/
│   ├── silver_layer_transformations.md
│   └── testing.md
├── sql/
│   ├── 01_create_bronze_tables.sql
│   ├── 02_create_silver_tables.sql
│   ├── 03_transform_silver.sql
│   ├── 04_create_gold_tables.sql
│   └── 05_transform_gold.sql         # Clean star schema transformation logic
├── src/
│   ├── ingestion/
│   │   └── ingest_bronze.py          # Bronze ingestion engine
│   └── transformation/
│       ├── transform_gold.py         # Gold deployment runner
│       └── transform_silver.py       # Silver normalization rules
├── tests/
│   ├── conftest.py                   # Automated sandbox setup/teardown fixture
│   ├── test_bronze.py                # Bronze layer assertions
│   ├── test_silver.py                # Silver layer assertions
│   └── test_gold.py                  # Gold star schema structural tests
├── docker-compose.yml                # Unified multi-service deployment layout
├── pyproject.toml                    # UV environment tool configuration
└── uv.lock                           # Locked dependency tree manifest
```

---

## 🚀 Getting Started

### Prerequisites

- **Docker** installed and running.
- **Python 3.12+** with `uv` installed.
- **Git** (to clone the repo).

### Step 1 — Configure Credentials

Before starting the containers, create your local configuration files by copying the environment templates:

```bash
cp .env.example .env
```

### Step 2 — Spin Up Your Infrastructure Cluster (Docker)

Launch the isolated data warehouse engine database and the Airflow orchestration nodes together using Docker Compose:

```bash
docker compose up -d
```

Verify that all backend containers are active and healthy:

```bash
docker compose ps
```

### Step 3 — Install Local Dependencies (For IDE & Local Tools)

Sync your local virtual environment libraries to ensure you have `ruff`, `pytest`, and database driver auto-complete tools available on your host system:

```bash
uv sync
```

### Step 4 — Run and Monitor the Pipeline via Airflow Web UI

1. Open your browser and navigate to the Airflow Dashboard at `http://localhost:8080`.
2. Log in using the administrator credentials:

   - **Username:** `admin`
   - **Password:** `admin`
3. Activate the `ecommerce_sales_pipeline` DAG using the blue toggle switch on the left.
4. Click the **Play** icon (Trigger DAG) on the right to execute the pipeline across your data layers.

### Step 5 — Verify Data Integrity and Row Counts

To ensure that the pipeline ran successfully query the target tables directly inside the data warehouse container:

```bash
# Execute the data validation counter check inside the warehouse database container
docker compose exec warehouse-db psql -U postgres -d ecommerce_platform -c "
SELECT
    (SELECT COUNT(*) FROM bronze_sales) AS bronze_rows,
    (SELECT COUNT(*) FROM silver_sales) AS silver_rows,
    (SELECT COUNT(*) FROM fact_sales) AS fact_rows;
"
```

**Expected Target Output:**

```text
 bronze_rows | silver_rows | fact_rows
-------------+-------------+-----------
      541909 |      536639 |    536639
```

### Step 6 — Run Automated Integration Tests

To run your end-to-end quality assurance suite against your isolated testing database sandbox, execute:

```bash
uv run python -m pytest -v
```

---

## 📜 Dataset Reference & Licensing

The pipeline targets the **Online Retail Dataset** provided by the UCI Machine Learning Repository.

- **Data Characteristics:** Cross-border transactions occurring between 01/12/2010 and 09/12/2011 for a UK-based non-store retail company.
- **Licensing and Attribution:** Publicly accessible dataset for academic and data engineering development purposes. Distributed under the standard UCI repository guidelines.
