CREATE TABLE IF NOT EXISTS silver_sales(
	invoice_no     TEXT,
	stock_code     TEXT,
	description    TEXT,
	quantity       INT,
	invoice_date   TIMESTAMP,
	unit_price     NUMERIC(10,2),
	customer_id    INT,
	country        TEXT,
	is_cancelled   BOOLEAN,
	total_amount   NUMERIC(10,2),
    loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
