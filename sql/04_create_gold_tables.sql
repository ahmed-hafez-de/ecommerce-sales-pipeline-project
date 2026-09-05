-- ============================================================================
-- Description: DDL script to define the Star Schema layout for the Gold Layer.
--              Contains optimized dimension tables linked via surrogate keys
--              to a central fact table for high-performance reporting.
-- ============================================================================

-- Date Dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_key     INT PRIMARY KEY,
    full_date    DATE,
    year         INT,
    quarter      INT,
    month        INT,
    day_of_month INT,
    day_name     TEXT,
    is_weekend   BOOLEAN
);

-- Customer Dimension
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id  INT UNIQUE
);

-- Create Product Dimension
CREATE TABLE IF NOT EXISTS dim_product (
    product_key SERIAL PRIMARY KEY,
    stock_code  TEXT UNIQUE,
    description TEXT
);

-- Create Fact Sales Table
CREATE TABLE IF NOT EXISTS fact_sales (
    sales_id     SERIAL PRIMARY KEY,
    invoice_no   TEXT,
    date_key     INT REFERENCES dim_date(date_key),
    product_key  INT REFERENCES dim_product(product_key),
    customer_key INT REFERENCES dim_customer(customer_key),
    quantity     INT,
    unit_price   NUMERIC(10,2),
    total_amount NUMERIC(10,2),
    country      TEXT,
    is_cancelled BOOLEAN
);
