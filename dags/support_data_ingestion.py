"""Daily BANKING77 ingestion into MinIO."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task


@dag(
    dag_id="support_data_ingestion",
    description="Refresh and validate the support-intent training dataset in MinIO",
    schedule="@daily",
    start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    default_args={"owner": "mlops", "retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["customer-support", "ingestion"],
)
def support_data_ingestion():
    @task
    def ingest_and_validate() -> dict[str, object]:
        from support_classifier.ingest import ingest

        return ingest(use_seed=False)

    ingest_and_validate()


support_data_ingestion()
