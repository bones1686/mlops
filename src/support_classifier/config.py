"""Environment-backed configuration shared by services."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[2]))

MODEL_NAME = os.getenv("MODEL_NAME", "support-ticket-classifier")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_URI = os.getenv("MODEL_URI", f"models:/{MODEL_NAME}@champion")
MODEL_PATH = os.getenv("MODEL_PATH", str(PROJECT_ROOT / "artifacts" / "model.joblib"))

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
DATA_BUCKET = os.getenv("DATA_BUCKET", "support-data")
DATA_KEY = os.getenv("DATA_KEY", "training/latest.csv")

SUPPORTED_INTENTS = (
    "activate_my_card",
    "beneficiary_not_allowed",
    "card_arrival",
    "cash_withdrawal_not_recognised",
    "change_pin",
    "declined_cash_withdrawal",
    "pending_transfer",
    "wrong_exchange_rate_for_cash_withdrawal",
)

ROUTING_GROUPS = {
    "activate_my_card": "card_support",
    "beneficiary_not_allowed": "transfers",
    "card_arrival": "card_delivery",
    "cash_withdrawal_not_recognised": "fraud",
    "change_pin": "card_support",
    "declined_cash_withdrawal": "cash_operations",
    "pending_transfer": "transfers",
    "wrong_exchange_rate_for_cash_withdrawal": "cash_operations",
}
