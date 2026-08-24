"""Dataset acquisition, cleaning, validation and object-storage helpers."""

from __future__ import annotations

import io
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from .config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    DATA_BUCKET,
    DATA_KEY,
    PROJECT_ROOT,
    S3_ENDPOINT_URL,
    SUPPORTED_INTENTS,
)

REQUIRED_COLUMNS = {"query", "intent"}


def clean_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a normalized, de-duplicated training frame."""
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    clean = frame[["query", "intent"]].copy()
    clean["query"] = clean["query"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    clean["intent"] = clean["intent"].astype(str).str.strip()
    clean = clean[(clean["query"].str.len() >= 3) & (clean["intent"].str.len() > 0)]
    return clean.drop_duplicates(subset=["query", "intent"]).reset_index(drop=True)


def validate_dataframe(frame: pd.DataFrame, min_rows_per_class: int = 2) -> dict[str, object]:
    """Fail fast on schema/class issues and return a compact quality report."""
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Training data is empty")
    nulls = frame[list(REQUIRED_COLUMNS)].isna().sum().sum()
    if nulls:
        raise ValueError(f"Training data contains {int(nulls)} null values")
    counts = frame["intent"].value_counts()
    too_small = counts[counts < min_rows_per_class]
    if not too_small.empty:
        raise ValueError(f"Classes below {min_rows_per_class} rows: {too_small.to_dict()}")
    return {
        "rows": len(frame),
        "classes": int(frame["intent"].nunique()),
        "duplicates": int(frame.duplicated(subset=["query", "intent"]).sum()),
        "class_counts": {str(k): int(v) for k, v in counts.to_dict().items()},
    }


def load_banking77(intents: Iterable[str] = SUPPORTED_INTENTS) -> pd.DataFrame:
    """Load the selected BANKING77 intents from Hugging Face."""
    from datasets import concatenate_datasets, load_dataset

    revision = "796a4623935746f71378f0ebd435635a8ce08e50"
    base = f"https://huggingface.co/datasets/PolyAI/banking77/resolve/{revision}/data"
    dataset = load_dataset(
        "parquet",
        data_files={
            "train": f"{base}/train-00000-of-00001.parquet",
            "test": f"{base}/test-00000-of-00001.parquet",
        },
    )
    parts = [dataset[split] for split in ("train", "test")]
    joined = concatenate_datasets(parts)
    selected_label_ids = {
        "activate_my_card": 0,
        "beneficiary_not_allowed": 7,
        "card_arrival": 11,
        "cash_withdrawal_not_recognised": 20,
        "change_pin": 21,
        "declined_cash_withdrawal": 26,
        "pending_transfer": 48,
        "wrong_exchange_rate_for_cash_withdrawal": 76,
    }
    allowed = {selected_label_ids[name]: name for name in intents}
    rows = [
        {"query": row["text"], "intent": allowed[row["label"]]}
        for row in joined
        if row["label"] in allowed
    ]
    return clean_dataframe(pd.DataFrame(rows))


def load_seed_data() -> pd.DataFrame:
    return clean_dataframe(pd.read_csv(PROJECT_ROOT / "data" / "seed_support_queries.csv"))


def s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def upload_csv(frame: pd.DataFrame, bucket: str = DATA_BUCKET, key: str = DATA_KEY) -> str:
    client = s3_client()
    try:
        client.head_bucket(Bucket=bucket)
    except Exception:  # noqa: BLE001 - any unavailable bucket is followed by idempotent creation
        client.create_bucket(Bucket=bucket)
    payload = frame.to_csv(index=False).encode("utf-8")
    client.put_object(Bucket=bucket, Key=key, Body=payload, ContentType="text/csv")
    return f"s3://{bucket}/{key}"


def download_csv(bucket: str = DATA_BUCKET, key: str = DATA_KEY) -> pd.DataFrame:
    response = s3_client().get_object(Bucket=bucket, Key=key)
    return clean_dataframe(pd.read_csv(io.BytesIO(response["Body"].read())))


def load_training_data(local_path: str | Path | None = None) -> pd.DataFrame:
    if local_path:
        return clean_dataframe(pd.read_csv(local_path))
    try:
        return download_csv()
    except Exception:  # noqa: BLE001 - offline seed is the documented availability fallback
        return load_seed_data()
