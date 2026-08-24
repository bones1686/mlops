# Adaptive Customer Support Classification

An end-to-end MLOps service that classifies customer-support requests by intent
and routes them to the appropriate support queue. It includes automated data
ingestion, validation, model training, MLflow tracking and registration,
champion-challenger promotion, and FastAPI serving.

## Repository map

```text
src/support_classifier/   application, training, ingestion and promotion code
dags/                     Airflow data-ingestion DAG
kubeflow/                 Kubeflow Pipelines v2 definition
data/                     small offline seed dataset
tests/                    fast local checks
docker/                   container images and reverse-proxy configuration
```

## Fast local demo

The offline path needs only Python, pandas and scikit-learn:

```bash
PYTHONPATH=src python -m support_classifier.train --data data/seed_support_queries.csv \
  --output artifacts/model.joblib --no-mlflow
PYTHONPATH=src MODEL_PATH=artifacts/model.joblib uvicorn support_classifier.api:app --port 8000
curl -s http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"query":"I do not recognize this cash withdrawal"}'
```

## Complete stack

Start the data pipeline, MLflow, MinIO, Airflow, prediction API and Nginx gateway:

```bash
docker compose up --build
```

Local endpoints:

- prediction API and Swagger UI: `http://localhost:8000/docs`;
- MLflow: `http://localhost:5000`;
- MinIO console: `http://localhost:9001`;
- Airflow: `http://localhost:8080` (`admin` / `admin`).

The Kubeflow pipeline definition is in `kubeflow/pipeline.py`; the compiled
pipeline specification is `support_pipeline.yaml`.
