import shutil
from pathlib import Path

import src.ingestion.ingest_bronze
from src.ingestion.ingest_bronze import run_bronze_ingestion


def test_bronze_ingestion_loads_csv_correctly(db_conn, tmp_path):
    """
    Integration Test: Generates an isolated test workspace, simulates a raw file landing,
    and runs the COPY ingestion pipeline against the text-based schema.
    """
    # and runs the COPY ingestion pipeline against the text-based schema.
    mock_data_dir = tmp_path / "data"
    mock_sql_dir = tmp_path / "sql"
    mock_data_dir.mkdir()
    mock_sql_dir.mkdir()

    # Generate a single-row mock CSV file
    mock_csv_path = mock_data_dir / "Online_Retail.csv"
    mock_csv_path.write_text(
        "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"
        "536365,85123A,WHITE HEART,6,12/01/2010 08:26:00,2.55,17850,United Kingdom\n",
        encoding="latin-1",
    )

    # Re-route real DDL schema script into the temporary workspace directory
    real_sql_script = (
        Path(__file__).resolve().parent.parent / "sql" / "01_create_bronze_tables.sql"
    )
    shutil.copy(real_sql_script, mock_sql_dir / "01_create_bronze_tables.sql")

    # Patch the package path pointer to simulate project root
    src.ingestion.ingest_bronze.BASE_DIR = tmp_path

    # Execute ingestion pipeline
    run_bronze_ingestion()

    # Verify database state
    with db_conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*), InvoiceNo, description
            FROM bronze_sales GROUP BY InvoiceNo, description;
        """
        )
        result = cursor.fetchone()

    assert result is not None, "Pipeline failure: 'bronze_sales' table is empty."
    assert result[0] == 1, f"Expected 1 loaded row, but found {result[0]} rows."
    assert result[1] == "536365", f"Expected InvoiceNo '536365', got '{result[1]}'."
    assert result[2] == "WHITE HEART", (
        f"Expected raw description text 'WHITE HEART', got '{result[2]}'."
    )
