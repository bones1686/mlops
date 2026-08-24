"""Stateless FastAPI model-serving application."""

from __future__ import annotations

import threading
import time
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import MLFLOW_TRACKING_URI, MODEL_PATH, MODEL_URI, ROUTING_GROUPS

_state: dict[str, object] = {
    "model": None,
    "source": None,
    "loaded_at": None,
    "requests": 0,
    "low_confidence": 0,
}
_lock = threading.Lock()


class PredictionRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2_000)


class PredictionResponse(BaseModel):
    intent: str
    routing_group: str
    confidence: float
    low_confidence: bool
    model_source: str


def load_model() -> str:
    """Prefer the MLflow champion alias and fall back to a local artifact."""
    model = None
    source = MODEL_URI
    try:
        import mlflow
        import mlflow.sklearn

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        model = mlflow.sklearn.load_model(MODEL_URI)
    except Exception:  # noqa: BLE001 - registry outage intentionally uses the offline artifact
        source = MODEL_PATH
        model = joblib.load(MODEL_PATH)
    with _lock:
        _state.update({"model": model, "source": source, "loaded_at": time.time()})
    return source


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_model()
    yield


app = FastAPI(
    title="Customer Support Classification API",
    version="0.1.0",
    description="Classifies a support query and routes it to a support group.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok" if _state["model"] is not None else "not_ready",
        "model_source": _state["source"],
        "loaded_at": _state["loaded_at"],
    }


@app.get("/metrics")
def metrics() -> dict[str, int]:
    return {
        "classification_requests_total": int(_state["requests"]),
        "low_confidence_predictions_total": int(_state["low_confidence"]),
    }


@app.post("/reload")
def reload_model() -> dict[str, str]:
    try:
        return {"status": "reloaded", "model_source": load_model()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Model reload failed: {exc}") from exc


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    model = _state["model"]
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    probabilities = model.predict_proba([request.query])[0]
    index = int(probabilities.argmax())
    intent = str(model.classes_[index])
    confidence = float(probabilities[index])
    is_low = confidence < 0.60
    with _lock:
        _state["requests"] = int(_state["requests"]) + 1
        if is_low:
            _state["low_confidence"] = int(_state["low_confidence"]) + 1
    return PredictionResponse(
        intent=intent,
        routing_group=ROUTING_GROUPS.get(intent, "manual_review"),
        confidence=round(confidence, 6),
        low_confidence=is_low,
        model_source=str(_state["source"]),
    )
