# End-to-end demo script

## Prerequisites

- Docker with Compose;
- ports 5000, 8000, 8080, 9000 and 9001 available;
- approximately 6 GB free memory for the full stack.

## 1. Local code smoke test

```bash
PYTHONPATH=src python -m support_classifier.train \
  --data data/seed_support_queries.csv \
  --output artifacts/model.joblib \
  --no-mlflow
```

Expected: JSON containing eight classes, 64 rows, metrics and the artifact path.

## 2. Start the complete environment

```bash
docker compose up --build -d
docker compose ps
```

The startup order is deterministic: MinIO/PostgreSQL -> buckets -> ingestion -> MLflow -> training
and promotion -> API/gateway. Airflow is initialized independently in the same Compose project.

## 3. Inspect services

| Component | URL | Demo login |
|---|---|---|
| Prediction API docs | http://localhost:8000/docs | none |
| MLflow | http://localhost:5000 | none |
| Airflow | http://localhost:8080 | `admin/admin` |
| MinIO | http://localhost:9001 | `minioadmin/minioadmin` |

## 4. Call the API

```bash
curl -s http://localhost:8000/health

curl -s http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"query":"I do not recognize this cash withdrawal"}'

curl -s http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"query":"Why is my bank transfer still pending?"}'

curl -s http://localhost:8000/metrics
```

Discuss the predicted intent, routing group, confidence, and why low-confidence tickets go to manual
review.

## 5. Show MLOps evidence

1. In MinIO, open `support-data/training/latest.csv` and the `mlflow` bucket.
2. In MLflow, open the experiment and show parameters, metrics and the evaluation artifact.
3. Open the registered model and show `challenger` and `champion` aliases.
4. In Airflow, trigger `support_data_ingestion` and show its validation log.

## 6. Demonstrate scaling

```bash
docker compose up -d --no-deps --scale api=3 api gateway
docker compose ps api
```

Repeated requests continue through port 8000 while gateway distributes them among stateless API
containers.

## 7. Compile the Kubeflow pipeline

```bash
python -m venv .venv
. .venv/bin/activate
pip install '.[kubeflow]'
python kubeflow/pipeline.py
test -s support_pipeline.yaml
```

Open the YAML or upload it to Kubeflow and point out the five graph nodes: gather, validate,
tune/train/register, evaluate/promote, and reload serving.

## 8. Stop the demo

```bash
docker compose down
```

Volumes are retained for the next demonstration. To remove them, use `docker compose down -v` only
when the stored demo runs and artifacts are no longer needed.
