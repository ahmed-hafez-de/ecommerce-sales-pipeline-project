import shutil
from pathlib import Path

import src.transformation.transform_silver
from src.transformation.transform_silver import run_silver_transformation


def test_silver_transformation_cleans_data(db_conn, tmp_path):
    """
    Integration Test: Injects dirty seed rows into bronze_sales, copies real
    SQL transform declarations, and asserts that type-casting and deduplication evaluate properly.
    """
    mock_sql_dir = tmp_path / "sql"
    mock_sql_dir.mkdir()

    # Stage the final transformation scripts into test runtime workspace
    project_root_sql = Path(__file__).resolve().parent.parent / "sql"
    shutil.copy(
        project_root_sql / "02_create_silver_tables.sql",
        mock_sql_dir / "02_create_silver_tables.sql",
    )
    shutil.copy(
        project_root_sql / "03_transform_silver.sql",
        mock_sql_dir / "03_transform_silver.sql",
    )

    # Re-route the real scripts into our temporary workspace directory
    src.transformation.transform_silver.BASE_DIR = tmp_path

    # Simulate dirty upstream text data in the bronze schema
    with db_conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bronze_sales (
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
        """)

        # Inject identical duplicate rows to validate that ROW_NUMBER() window partitions drop duplicates
        cursor.execute("""
            INSERT INTO bronze_sales (InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country)
            VALUES
            ('536365', '85123A', ' heart ', '6', '12/01/2010 08:26:00', '2.55', '17850', 'united kingdom'),
            ('536365', '85123A', ' heart ', '6', '12/01/2010 08:26:00', '2.55', '17850', 'united kingdom');
        """)
        db_conn.commit()

    # Execute Transformation pipeline
    run_silver_transformation()

    # Query cleaned and typed rows from target table
    with db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT count(*), description, quantity, unit_price, country
            FROM silver_sales
            GROUP BY description, quantity, unit_price, country;
        """)
        result = cursor.fetchone()

    assert result is not None, (
        "Pipeline failure: 'silver_sales' target dataset is completely empty."
    )

    # Check that deduplication (rn = 1) worked
    assert result[0] == 1, (
        f"Deduplication validation failed! Found duplicate leakage: {result[0]} rows."
    )

    # Check text cleaning (UPPER and TRIM)
    assert result[1] == "HEART", (
        f"String manipulation failure: expected 'HEART', got '{result[1]}'."
    )

    # Assert proper target integer casting
    assert result[2] == 6, (
        f"Type cast failure: expected Integer 6, got {type(result[2])} value {result[2]}."
    )

    # Assert proper target numeric scale casting
    assert float(result[3]) == 2.55, (
        f"Type cast scale failure: expected 2.55, got {result[3]}."
    )

    # Check region formatting (INITCAP and TRIM)
    assert result[4] == "United Kingdom", (
        f"Region normalization failure: expected 'United Kingdom', got '{result[4]}'."
    )
