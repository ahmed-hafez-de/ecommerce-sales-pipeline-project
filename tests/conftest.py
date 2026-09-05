import psycopg2
import pytest
from dotenv import load_dotenv

load_dotenv(".env.test", override=True)


@pytest.fixture(scope="function")
def db_conn():
    """
    Automated fixture providing an isolated database connection.
    Cleans up the testing sandbox before and after every test function
    execution.
    """
    # Connect to 'ecommerce_platform_test'
    conn = psycopg2.connect()

    # SETUP: clean before test
    with conn.cursor() as cursor:
        cursor.execute(
            """
                DROP TABLE IF EXISTS fact_sales CASCADE;
                DROP TABLE IF EXISTS dim_product CASCADE;
                DROP TABLE IF EXISTS dim_customer CASCADE;
                DROP TABLE IF EXISTS dim_date CASCADE;
                DROP TABLE IF EXISTS silver_sales CASCADE;
                DROP TABLE IF EXISTS bronze_sales CASCADE;
            """
        )
        conn.commit()

    try:
        yield conn  # Hand control over to the executing test function
    # TEARDOWN: Clear tables and kill database after test completion
    finally:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                    DROP TABLE IF EXISTS fact_sales CASCADE;
                    DROP TABLE IF EXISTS dim_product CASCADE;
                    DROP TABLE IF EXISTS dim_customer CASCADE;
                    DROP TABLE IF EXISTS dim_date CASCADE;
                    DROP TABLE IF EXISTS silver_sales CASCADE;
                    DROP TABLE IF EXISTS bronze_sales CASCADE;
                """
            )
            conn.commit()
        conn.close()
