TRUNCATE TABLE silver_sales;

INSERT INTO silver_sales (
    invoice_no,
    stock_code,
    description,
    quantity,
    invoice_date,
    unit_price,
    customer_id,
    country,
    is_cancelled,
    total_amount
)
SELECT
    invoiceno,
    stockcode,
    UPPER(TRIM(description)) AS description,
    quantity::INT AS quantity,
    TO_TIMESTAMP(invoicedate, 'MM/DD/YYYY HH24:MI:SS') AS invoice_date,
    unitprice::DECIMAL(10,2) AS unit_price,
    COALESCE(customerid::INT, -1) AS customer_id,
    INITCAP(TRIM(country)) AS country,

    CASE
        WHEN invoiceno LIKE 'C%'
             OR quantity::INT < 0
        THEN TRUE
        ELSE FALSE
    END AS is_cancelled,

    quantity::INT * unitprice::DECIMAL(10,2) AS total_amount

FROM (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY
                InvoiceNo,
                StockCode,
                Description,
                Quantity,
                InvoiceDate,
                UnitPrice,
                CustomerID,
                Country
            ORDER BY InvoiceNo
        ) AS rn
    FROM bronze_sales
) AS deduplicated

WHERE rn = 1
  AND unitprice::DECIMAL(10,2) >= 0
  AND quantity::INT <> 0
  AND invoicedate IS NOT NULL;
