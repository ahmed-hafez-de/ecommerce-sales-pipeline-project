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


def run_gold_transformation():
    create_table_sql_path = BASE_DIR / "sql" / "04_create_gold_tables.sql"
    transform_sql_path = BASE_DIR / "sql" / "05_transform_gold.sql"

    start_time = time.time()

    logger.info("Starting Gold layer transformation pipeline...")
    conn = None

    try:
        logger.info("Connecting to PostgreSQL database...")
        conn = psycopg2.connect()

        with conn.cursor() as cursor:
            # Create Gold tables
            logger.info(
                f"Executing Gold table definitions from {create_table_sql_path}..."
            )

            with open(create_table_sql_path) as ddl_file:
                create_table_sql = ddl_file.read()

            cursor.execute(create_table_sql)

            # Execute Gold transformation execution sequence
            logger.info(
                f"Executing Gold transformation sequence from {transform_sql_path}..."
            )

            with open(transform_sql_path) as sql_file:
                transformation_sql = sql_file.read()

            cursor.execute(transformation_sql)

            # Validation metrics tailored for the Gold layer star schema
            cursor.execute("SELECT COUNT(*) FROM fact_sales;")
            total_sales = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM dim_customer;")
            total_customers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM dim_product;")
            total_products = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM fact_sales
                WHERE customer_key = -1;
                """
            )
            anonymous_sales = cursor.fetchone()[0]

            # Commit transaction
            conn.commit()

            elapsed_time = time.time() - start_time

            logger.info(
                f"Gold transformation complete successfully! "
                f"Fact Rows: {total_sales} | "
                f"Customers Monitored: {total_customers} | "
                f"Products Tracked: {total_products} | "
                f"Sales mapped to Unknown Customer (-1): {anonymous_sales} | "
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
    run_gold_transformation()
