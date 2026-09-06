# 🧪 Data Pipeline Integration Testing Documentation

This document outlines the testing architecture for the automated E-commerce Sales Data Pipeline. The pipeline employs an automated integration testing strategy utilizing **Pytest**, containerized **PostgreSQL (Docker Compose)**, and isolated environments to validate data processing logic across the Bronze, Silver, and Gold layers without putting production or development data at risk.

---

## 1. Database Architecture & Environment Isolation

To ensure running test suites never corrupt, lock, or truncate active development tables, the architecture uses a **Multi-Database Strategy** isolated across separate storage volumes inside the database layer.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                     ecommerce_warehouse_db CONTAINER                   │
│                                                                        │
│  ┌────────────────────────────────┐  ┌───────────────────────────────┐ │
│  │       ecommerce_platform       │  │  ecommerce_platform_test      │ │
│  │    (Active Business Warehouse) │  │  (Isolated Test Sandbox)      │ │
│  │                                │  │                               │ │
│  │    • Untouched by test runs    │  │    • Wiped pre/post test      │ │
│  │    • Configured via .env       │  │    • Configured via .env.test │ │
│  └────────────────────────────────┘  └───────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### Step 1: Automated Sandbox

We have a multi-container environment spins up via `docker compose up -d`, the database initialization sequence automatically handles provisioning:

* Builds the core operational transactional engine (`ecommerce_platform`)
* Sets up the parallel data validation engine (`ecommerce_platform_test`)
* Restores host connectivity on port **`54876`**

### Step 2: Configure Environment Boundary Files

The platform manages target database routing using standard PostgreSQL environment flags (`PG*`). This allows `psycopg2.connect()` to read variables implicitly based on which `.env` context file is active.

Before executing tests, copy the environment template and verify your credentials:

```bash
cp .env.test.example .env.test
```

---

## 2. Test Infrastructure & Automation (`conftest.py`)

The global `tests/conftest.py` workspace orchestrates the testing framework lifecycle:

* **Environment Interception:** It triggers `load_dotenv(".env.test", override=True)` immediately at boot time. This overrides standard local environment configurations and safely redirects all pipeline code connections to the isolated test database.
* **Cascade Database Lifecycle Control:** It manages a Pytest database fixture hook (`db_conn`) passed down to all functional test blocks.
* **Stateless Test Execution:** The fixture runs a `DROP TABLE IF EXISTS ... CASCADE` loop before a test case starts (**Setup**) and immediately after it completes (**Teardown**). This ensures a clean slate, prevents cross-test database pollution, and guarantees test repeatability.

---

## 3. Integration Testing Strategy

The test scripts live under the `tests/` folder and execute real pipeline operations against runtime-generated data files, rather than relying on fragile code mocks.

### A. Bronze Layer Ingestion (`test_bronze_pipeline.py`)

Validates the high-performance raw CSV streaming logic.

* **The Strategy:** The test utilizes Pytest's built-in `tmp_path` fixture to dynamically generate an ephemeral, single-row mock CSV file (`Online_Retail.csv`) inside a temp data directory during test runtime.
* **Assertions:** It overrides the module's `BASE_DIR`, triggers `run_bronze_ingestion()`, and asserts that the `copy_expert()` transaction successfully streams raw data into the target `bronze_sales` landing table with accurate text schemas.

### B. Silver Layer Transformation (`test_silver_pipeline.py`)

Validates structural type casting and analytical cleaning rules.

* **The Strategy:** Stages dirty text strings directly inside the test database's `bronze_sales` table. It dynamically copies the production SQL DDL and transformation code files (`02_create_silver_tables.sql` and `03_transform_silver.sql`) into the temporary test runtime folder.
* **Assertions:** It triggers `run_silver_transformation()`, asserting that string cleaning rules (`UPPER`, `TRIM`, `INITCAP`) process perfectly, data values are cast accurately (`INT`, `NUMERIC`), duplicate entries drop completely via `ROW_NUMBER()` window filtering, and anonymous IDs map smoothly.

### C. Gold Layer Transformation (`test_gold.py`)

Validates Star Schema data modeling and structural row-count parity.

* **The Strategy:** Pre-populates clean data vectors inside a temporary `silver_sales` layout. It stages `04_create_gold_tables.sql` and `05_transform_gold.sql` into the runtime test space.
* **Assertions:** It triggers `run_gold_transformation()` and asserts that:
  1. The `dim_date` dimension table generates the correct sequence of calendar dates.
  2. The manual `-1` surrogate key placeholder is successfully seeded as a static row in `dim_customer`.
  3. The `UNIQUE` constraints function properly on natural business dimensions.
  4. The global row-count match works seamlessly, proving that no data explosion (fan-out bug) occurs when joining the `fact_sales` table.

---

## 4. Execution Instructions

To execute the verification suites, always use Python module execution flags (`python -m pytest`). This explicitly injects the project's source root (`src/`) paths straight into your active Python path to prevent package import failures.

Run the commands from the root directory of your repository:

### Verify the Complete Pipeline Suite

```bash
uv run python -m pytest -v
```

### Target a Specific Pipeline Layer

```bash
# Test Bronze Ingestion only
uv run python -m pytest -v tests/test_bronze.py

# Test Silver Transformation only
uv run python -m pytest -v tests/test_silver.py

# Test Gold Transformation only
uv run python -m pytest -v tests/test_gold.py
```
