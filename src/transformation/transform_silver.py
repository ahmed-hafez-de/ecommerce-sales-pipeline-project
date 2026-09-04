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

# Find the exact folder where this code file lives
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def run_silver_transformation():
    create_table_sql_path = BASE_DIR / "sql" / "02_create_silver_tables.sql"
    transform_sql_path = BASE_DIR / "sql" / "03_transform_silver.sql"

    start_time = time.time()

    logger.info("Starting Silver transformation pipeline...")
    conn = None

    try:
        logger.info("Connecting to PostgreSQL database...")
        conn = psycopg2.connect()

        with conn.cursor() as cursor:
            # 1. Create Silver table
            logger.info(
                f"Executing Silver table definition from {create_table_sql_path}..."
            )

            with open(create_table_sql_path) as ddl_file:
                create_table_sql = ddl_file.read()

            cursor.execute(create_table_sql)

            # 2. Execute Silver transformation
            logger.info(f"Executing Silver transformation from {transform_sql_path}...")

            with open(transform_sql_path) as sql_file:
                transformation_sql = sql_file.read()

            cursor.execute(transformation_sql)

            # 3. Validation / metrics
            cursor.execute("SELECT COUNT(*) FROM silver_sales;")
            total_rows = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM silver_sales
                WHERE is_cancelled = TRUE;
                """
            )
            cancelled_rows = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM silver_sales
                WHERE customer_id = -1;
                """
            )
            unknown_customer_rows = cursor.fetchone()[0]

            # 4. Commit
            conn.commit()

            elapsed_time = time.time() - start_time

            logger.info(
                f"Silver transformation complete! "
                f"Rows: {total_rows} | "
                f"Cancelled: {cancelled_rows} | "
                f"Unknown Customers: {unknown_customer_rows} | "
                f"Duration: {elapsed_time:.2f} seconds"
            )

    except FileNotFoundError as fnf_error:
        logger.error(f"Pipeline failed: File not found -> {fnf_error}")

    except psycopg2.Error as db_error:
        logger.error(f"Pipeline failed: Database error occurred -> {db_error}")

        if conn:
            logger.info("Rolling back database transaction...")
            conn.rollback()

    except Exception as general_error:  # noqa: BLE001
        logger.error(f"Pipeline failed: Unexpected error -> {general_error}")

        if conn:
            logger.info("Rolling back database transaction...")
            conn.rollback()

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    run_silver_transformation()
