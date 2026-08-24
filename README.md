# Adaptive Customer Support Classification

An end-to-end MLOps course project that classifies customer-support requests by
intent and routes them to a support queue. The repository grows through four
assignments: design, baseline serving, experiment tracking and champion–challenger
deployment, and a Kubeflow-compatible production pipeline.

## Repository map

```text
src/support_classifier/   application, training, ingestion and promotion code
dags/                     Airflow data-ingestion DAG
kubeflow/                 Kubeflow Pipelines v2 definition
data/                     small offline seed dataset
reports/                  one report per assignment and demo instructions
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

For the complete stack and assignment-by-assignment demo, see
[`reports/demo.md`](reports/demo.md).

## Reports

- [`Assignment 1 — design`](reports/assignment1_design.md)
- [`Assignment 2 — baseline and data ingestion`](reports/assignment2_report.md)
- [`Assignment 3 — MLflow and champion–challenger`](reports/assignment3_report.md)
- [`Assignment 4 — full Kubeflow pipeline`](reports/assignment4_report.md)
