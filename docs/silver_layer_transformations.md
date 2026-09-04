# ⬜ Silver Layer Transformation

The Silver layer converts the raw Bronze data into clean, typed, standardized, and analytics-ready transaction data.

---

## 🧹 Column Transformations

| Bronze Column | Silver Column | Transformation |
| :--- | :--- | :--- |
| **InvoiceNo** | invoice_no | Rename to warehouse naming convention |
| **StockCode** | stock_code | Rename to warehouse naming convention |
| **Description** | description | `TRIM()` + `UPPER()` |
| **Quantity** | quantity | Cast to `INT` |
| **InvoiceDate** | invoice_date | Parse using `TO_TIMESTAMP()` |
| **UnitPrice** | unit_price | Cast to `NUMERIC(10,2)` |
| **CustomerID** | customer_id | Cast to `INT` + replace `NULL` with `-1` |
| **Country** | country | `TRIM()` + `INITCAP()` |
| **InvoiceNo + Quantity** | is_cancelled | Identify cancellation transactions |
| **Quantity × UnitPrice** | total_amount | Calculate transaction amount |

---

### 🔄 Cancellation Handling

- The source data identifies cancellations using invoice numbers beginning with C.
- Negative quantities are also treated as cancellation transactions.

```sql
CASE
    WHEN invoiceno LIKE 'C%'
        OR quantity::INT < 0
        THEN TRUE
        ELSE FALSE
END AS is_cancelled
```

- So, Cancellation transactions are **kept**, rather than deleted.
- This preserves transaction history and allows downstream analytics to account for cancellations and reversals.

---

### 🔗 Deduplication

- Duplicate records are identified using the complete set of attributes that describe a sales line:

```sql
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
```

- Only the first occurrence is retained: `WHERE rn = 1`.

---

## ⚖️ Data Quality Rules

| Rule | Action | Reason |
| :--- | :--- | :--- |
| **unit_price = 0** | Keep | Zero price is not automatically invalid |
| **unit_price < 0** | Drop | Invalid unit price |
| **quantity = 0** | Drop | No items were transacted |
| **quantity < 0** | Keep | Represents a reversal/cancellation |
| **InvoiceNo LIKE 'C%'** | Keep | Cancellation information is valuable |
| **Missing CustomerID** | Keep as -1 | Preserve transaction while identifying unknown customer |
| **Missing InvoiceDate** | Drop | Required for time-based analysis |
| **Duplicate sales-line record** | Keep one | Eliminate data redundancy |
