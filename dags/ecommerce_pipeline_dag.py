from datetime import UTC, datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

CONTAINER_ROOT = "/opt/airflow"

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ecommerce_sales_pipeline",
    default_args=default_args,
    description="Dockerized ETL pipeline orchestrating Bronze, Silver, and Gold Layers",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    tags=["ecommerce", "medallion"],
) as dag:
    # This markdown block displays directly inside your Airflow Web dashboard!
    dag.doc_md = """
    ### E-commerce Star Schema ETL Pipeline
    This automated workflow runs sequentially across 3 distinct data layers:
    1. **Bronze Ingestion**: Loads raw unstructured CSV values into staging.
    2. **Silver Transformation**: Sanitizes types and drops identical duplicate rows.
    3. **Gold Star Schema**: Wipes data, inserts a stable `-1` key placeholder, and builds clean analytical tables.
    """

    run_bronze_ingestion = BashOperator(
        task_id="run_bronze_ingestion",
        bash_command=f"cd {CONTAINER_ROOT} && python src/ingestion/ingest_bronze.py",
    )

    run_silver_transformation = BashOperator(
        task_id="run_silver_transformation",
        bash_command=f"cd {CONTAINER_ROOT} && python src/transformation/transform_silver.py",
    )

    run_gold_transformation = BashOperator(
        task_id="run_gold_transformation",
        bash_command=f"cd {CONTAINER_ROOT} && python src/transformation/transform_gold.py",
    )

    run_bronze_ingestion >> run_silver_transformation >> run_gold_transformation
