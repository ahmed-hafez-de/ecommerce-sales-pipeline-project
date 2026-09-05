-- ============================================================================
-- Description: ETL Script to clean slate and populate the Gold layer
-- Database: PostgreSQL
-- ============================================================================

-- Clean Slate: Wipe data and reset auto-increment counters
TRUNCATE TABLE fact_sales, dim_product, dim_customer, dim_date
RESTART IDENTITY CASCADE;

-- Populate dim_date
INSERT INTO dim_date (
    date_key, full_date, year, quarter, month, day_of_month, day_name, is_weekend
)
SELECT
    TO_CHAR(datum, 'YYYYMMDD')::INT AS date_key,
    datum::DATE AS full_date,
    EXTRACT(ISOYEAR FROM datum) AS year,
    EXTRACT(QUARTER FROM datum) AS quarter,
    EXTRACT(MONTH FROM datum) AS month,
    EXTRACT(DAY FROM datum) AS day_of_month,
    TRIM(TO_CHAR(datum, 'Day')) AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM datum) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series(
    '2010-01-01'::DATE,
    '2012-01-01'::DATE,
    '1 day'::INTERVAL
) AS datum;

-- Seed Unknown Customer (-1 Placeholder)
INSERT INTO dim_customer (customer_key, customer_id)
VALUES (-1, -1);

-- Populate dim_customer
INSERT INTO dim_customer (customer_id)
SELECT customer_id
FROM (
    SELECT
        customer_id,
        ROW_NUMBER() OVER (PARTITION BY customer_id) as rn
    FROM silver_sales
    WHERE customer_id <> -1 AND customer_id IS NOT NULL
) sub WHERE rn = 1;


-- Populate dim_product
INSERT INTO dim_product (stock_code, description)
SELECT stock_code, description
FROM (
    SELECT
        stock_code, description,
        ROW_NUMBER() OVER (
            PARTITION BY stock_code
            ORDER BY LENGTH(description) DESC, description ASC
        ) AS rn
    FROM silver_sales
    WHERE stock_code IS NOT NULL
) sub WHERE rn = 1;


-- Populate fact_sales
INSERT INTO fact_sales (
    invoice_no, date_key, product_key, customer_key, quantity, unit_price, total_amount, country, is_cancelled
)
SELECT
    s.invoice_no,
    d.date_key,
    p.product_key,
    COALESCE(c.customer_key, -1) AS customer_key, -- Safely falls back to our seeded -1 row
    s.quantity,
    s.unit_price,
    (s.quantity * s.unit_price) AS total_amount,
    s.country,
    s.is_cancelled
FROM silver_sales s
JOIN dim_date d
  ON d.full_date = s.invoice_date::DATE
JOIN dim_product p
  ON p.stock_code = s.stock_code
LEFT JOIN dim_customer c
  ON c.customer_id = s.customer_id;
