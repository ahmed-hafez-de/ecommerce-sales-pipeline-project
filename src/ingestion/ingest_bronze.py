import logging
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Setup structured logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Find the exact folder where this  code file lives
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def run_bronze_ingestion():
    sql_script_path = BASE_DIR / "sql" / "01_create_bronze_tables.sql"
    csv_file_path = BASE_DIR / "data" / "Online_Retail.csv"
    start_time = time.time()

    logger.info("Starting Bronze ingestion pipeline...")
    conn = None

    try:
        # Connect to Postgres using psycopg2
        logger.info("Connecting to PostgreSQL database...")
        conn = psycopg2.connect()

        # Execute sql/01_create_bronze_tables.sql to ensure table exists
        with conn.cursor() as cursor:
            logger.info(f"Executing schema definition from {sql_script_path}...")
            with open(sql_script_path, "r") as ddl_file:
                schema_sql = ddl_file.read()
                cursor.execute(schema_sql)
            conn.commit()

        # Open a transaction context
        with conn.cursor() as cursor:
            logger.info("Beginning data ingestion transaction...")

            # TRUNCATE bronze_sales;
            cursor.execute("TRUNCATE bronze_sales;")
            logger.info("Target table 'bronze_sales' truncated.")

            # copy_expert() from data/Online_Retail.csv
            logger.info(f"Streaming data from {csv_file_path}...")
            with open(csv_file_path, "r", encoding="latin-1") as csv_file:
                copy_query = """
                    COPY bronze_sales (InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country)
                    FROM STDIN
                    WITH (FORMAT CSV, HEADER true, DELIMITER ',');
                """
                cursor.copy_expert(sql=copy_query, file=csv_file)

            # Commit transaction
            conn.commit()
            logger.info("Transaction committed.")

            # Log execution time and total rows loaded
            cursor.execute("SELECT COUNT(*) FROM bronze_sales;")
            total_rows = cursor.fetchone()

            elapsed_time = time.time() - start_time
            logger.info(
                f"Bronze load complete! Rows Loaded: {total_rows[0]} | Duration: {elapsed_time:.2f} seconds"
            )

    except FileNotFoundError as fnf_error:
        logger.error(f"Pipeline failed: File not found -> {fnf_error}")

    except psycopg2.Error as db_error:
        logger.error(f"Pipeline failed: Database error occurred -> {db_error}")
        # Explicitly clear out the broken transaction state
        if conn:
            logger.info("Rolling back database transaction...")
            conn.rollback()

    except Exception as general_error:  # noqa: BLE001
        logger.error(f"Pipeline failed: Unexpected error -> {general_error}")
        if conn:
            logger.info("Rolling back database transaction due to unexpected error...")
            conn.rollback()

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    run_bronze_ingestion()
