# 🧪 Data Pipeline Integration Testing Documentation

This document outlines the testing architecture for the automated E-commerce Sales Data Pipeline. The pipeline employs an automated integration testing strategy utilizing **Pytest**, containerized **PostgreSQL (Docker)**, and isolated environments to validate raw data ingestion (Bronze layer) and business logic transformations (Silver layer) without putting production or development data at risk.

---

## 1. Database Architecture & Environment Isolation

To ensure running tests never corrupt or delete active development data, the pipeline uses a **Multi-Database Strategy** hosted within the same Docker container.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DOCKER CONTAINER                       │
│                                                                        │
│  ┌────────────────────────────────┐  ┌────────────────────────────┐    │
│  │       ecommerce_platform       │  │  ecommerce_platform_test   │    │
│  │       (Dev / Prod Data)        │  │  (Isolated Test Sandbox)   │    │
│  │                                │  │                            │    │
│  │    • Untouched by test runs    │  │    • Wiped pre/post test   │    │
│  │    • Loaded via .env           │  │    • Loaded via .env.test  │    │
│  └────────────────────────────────┘  └────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

### Step 1: Initialize the Isolated Test Database

Run this command in your terminal to create a dedicated, blank testing database next to your primary database inside the running Postgres container:

```bash
docker exec -it local-postgres createdb -U postgres ecommerce_platform_test
```

### Step 2: Configure Environment Boundary Files

The application manages database connections dynamically using standard PostgreSQL system environment prefixes (`PG*`). This allows `psycopg2.connect()` to read variables implicitly based on which `.env` context is active, keeping credentials secure and completely out of the code.

Copy the example env file and fill in your local values:

```bash
cp .env.test.example .env.test
```

---

## 2. Test Infrastructure & Automation (`conftest.py`)

The global `tests/conftest.py` file acts as the orchestration manager for the testing framework. Its primary responsibilities include:

* **Environment Interception:** It calls `load_dotenv(".env.test", override=True)` immediately at startup. This safely forces the pipeline scripts to connect to the test database instead of dev data.
* **Automatic Database Lifecycle Control:** It manages a Pytest database fixture (`db_conn`) that hooks into test functions automatically.
* **Stateless Test Execution:** The fixture drops and truncates database tables before a test runs (Setup) and after it completes (Teardown). This provides a clean, stateless slate for every single test case and avoids cross-test data pollution.

---

## 3. Integration Testing Strategy

The test files live under the `tests/` folder and isolate target validation steps across both data architecture layers. Instead of utilizing fragile mocks, tests run real pipeline operations against runtime-generated fixtures.

### A. Bronze Layer Ingestion (`test_bronze_pipeline.py`)

This suite validates the raw CSV streaming ingestion pipeline.

* **The Strategy:** The test utilizes Pytest's built-in `tmp_path` fixture to dynamically generate an ephemeral, single-row mock CSV file (`Online_Retail.csv`) during runtime.
* **Assertions:** It overrides the module's `BASE_DIR`, triggers `run_bronze_ingestion()`, and asserts that the `copy_expert()` transaction successfully streams raw text data directly into the database with accurate row and column structure.

### B. Silver Layer Transformation (`test_silver_pipeline.py`)

This suite validates the analytical transformation scripts and data cleaning logic.

* **The Strategy:** The test manually prepares raw text entries inside a temporary `bronze_sales` table. It copies the actual production SQL DDL and transformation files (`02_create_silver_tables.sql` and `03_transform_silver.sql`) into a temp workspace folder.
* **Assertions:** It triggers `run_silver_transformation()` and asserts that the SQL script parses cleanly. It verifies that window functions properly deduplicate records (`ROW_NUMBER()`), strings are cleanly normalized (`UPPER`, `TRIM`, `INITCAP`), valid numbers are type-cast accurately (`INT`, `NUMERIC`), and cancellation rules match expected conditional logic.

---

## 4. Execution Instructions

To execute the verification suites, always use Python module execution flags. This explicitly injects the project's source root (`src/`) paths straight into your active Python path to prevent package import failures.

Run the commands from the root directory of your repository:

### Verify the Complete Pipeline Suite

```bash
python -m pytest -v
```

### Target a Specific Pipeline Layer

```bash
# Test Bronze Ingestion only
python -m pytest -v tests/test_bronze.py

# Test Silver Transformation only
python -m pytest -v tests/test_silver.py

# Test Gold Transformation only
python -m pytest -v tests/test_gold.py
```
