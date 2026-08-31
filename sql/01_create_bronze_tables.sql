CREATE TABLE IF NOT EXISTS bronze_sales(
    InvoiceNo    TEXT,
    StockCode    TEXT,
    Description  TEXT,
    Quantity     TEXT,
    InvoiceDate  TEXT,
    UnitPrice    TEXT,
    CustomerID   TEXT,
    Country      TEXT,
    loaded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
