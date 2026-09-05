import shutil
from pathlib import Path

import src.transformation.transform_gold
from src.transformation.transform_gold import run_gold_transformation


def test_gold_transformation_populates_star_schema(db_conn, tmp_path):
    """
    Integration Test: Injects mocked pre-deduplicated datasets into silver_sales,
    stubs the SQL DDL and execution assets, and validates structural constraints,
    the manual -1 customer placeholder, and that country-tracking remains safe in the fact table.
    """
    # Create isolated runtime file workspace
    mock_sql_dir = tmp_path / "sql"
    mock_sql_dir.mkdir()

    # Stage structural definitions into the test sandbox
    project_root_sql = Path(__file__).resolve().parent.parent / "sql"
    shutil.copy(
        project_root_sql / "04_create_gold_tables.sql",
        mock_sql_dir / "04_create_gold_tables.sql",
    )
    shutil.copy(
        project_root_sql / "05_transform_gold.sql",
        mock_sql_dir / "05_transform_gold.sql",
    )

    # Re-route real modules to consume files inside the temporary directory workspace
    src.transformation.transform_gold.BASE_DIR = tmp_path

    # Simulate our structured, clean Silver schema dataset
    with db_conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE silver_sales (
                invoice_no   TEXT,
                stock_code   TEXT,
                description  TEXT,
                quantity     INT,
                invoice_date TIMESTAMP,
                unit_price   NUMERIC(10,2),
                customer_id  INT,
                country      TEXT,
                is_cancelled BOOLEAN
            );
        """)

        # Inject unique test cases:
        # Row 1: Real Customer (9942) purchasing from the USA
        # Row 2: Anonymous Customer (-1) purchasing from the United Kingdom
        # Row 3: Anonymous Customer (-1) purchasing from France (Validates country mapping is safe)
        cursor.execute("""
            INSERT INTO silver_sales (invoice_no, stock_code, description, quantity, invoice_date, unit_price, customer_id, country, is_cancelled)
            VALUES
            ('536365', '85123A', 'WHITE HEART', 6, '2010-12-01 08:26:00'::TIMESTAMP, 2.55, 9942, 'USA', FALSE),
            ('536366', '22423', 'REGENCY CAKESTAND', 2, '2010-12-02 10:00:00'::TIMESTAMP, 12.75, -1, 'United Kingdom', FALSE),
            ('536367', '22423', 'REGENCY CAKESTAND', 1, '2010-12-02 11:30:00'::TIMESTAMP, 12.75, -1, 'France', FALSE);
        """)
        db_conn.commit()

    # Trigger transformation sequence pipeline
    run_gold_transformation()

    with db_conn.cursor() as cursor:
        # Assert 1: Validate Date dimension generation limits
        cursor.execute("SELECT COUNT(*) FROM dim_date;")
        date_count = cursor.fetchone()[0]
        assert date_count > 0, "dim_date calendar table failed to populate completely."

        # Assert 2: Validate dim_customer holds exactly two entries (-1 placeholder and real 9942 customer)
        cursor.execute(
            "SELECT customer_key, customer_id FROM dim_customer ORDER BY customer_key;"
        )
        customers = cursor.fetchall()
        assert len(customers) == 2, (
            f"Expected 2 rows in dim_customer, got {len(customers)}."
        )

        # Verify the manual placeholder assigned key = -1
        assert customers[0] == (-1, -1), (
            f"Placeholder registration corrupt: {customers[0]}"
        )
        # Verify the real customer got standard sequential SERIAL key = 1
        assert customers[1][0] == 1, (
            f"Real customer surrogate serial key starting mismatch: {customers[1][0]}"
        )

        # Assert 3: Validate fact_sales joined correctly and didn't drop rows
        cursor.execute("SELECT COUNT(*) FROM fact_sales;")
        fact_count = cursor.fetchone()[0]
        assert fact_count == 3, (
            f"Data leakage in fact mapping! Expected 3 records, got {fact_count}."
        )

        # Assert 4: Validate country tracking logic behavior inside fact_sales for anonymous accounts
        cursor.execute("""
            SELECT country, customer_key
            FROM fact_sales
            WHERE invoice_no IN ('536366', '536367')
            ORDER BY country;
        """)
        anonymous_sales_records = cursor.fetchall()

        # Row 1 check (France)
        assert anonymous_sales_records[0] == ("France", -1), (
            f"Country data lost for France! Got: {anonymous_sales_records[0]}"
        )
        # Row 2 check (United Kingdom)
        assert anonymous_sales_records[1] == ("United Kingdom", -1), (
            f"Country data lost for United Kingdom! Got: {anonymous_sales_records[1]}"
        )
