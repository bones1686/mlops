"""Train, evaluate, persist and optionally register the baseline classifier."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline

from .config import MLFLOW_TRACKING_URI, MODEL_NAME, MODEL_PATH
from .data import load_training_data, validate_dataframe


@dataclass
class TrainingResult:
    accuracy: float
    macro_f1: float
    best_c: float
    rows: int
    classes: int
    model_path: str
    run_id: str | None = None
    model_version: str | None = None


def build_pipeline(c: float = 1.0) -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=20_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(C=c, max_iter=1_000, class_weight="balanced"),
            ),
        ]
    )


def train_model(
    frame: pd.DataFrame,
    output_path: str = MODEL_PATH,
    c_values: Sequence[float] = (0.5, 1.0, 2.0),
    test_size: float = 0.25,
    random_state: int = 42,
    use_mlflow: bool = True,
) -> TrainingResult:
    quality = validate_dataframe(frame, min_rows_per_class=4)
    x_train, x_test, y_train, y_test = train_test_split(
        frame["query"],
        frame["intent"],
        test_size=test_size,
        random_state=random_state,
        stratify=frame["intent"],
    )

    search = GridSearchCV(
        build_pipeline(),
        {"classifier__C": list(c_values)},
        scoring="f1_macro",
        cv=3,
        n_jobs=-1,
    )
    search.fit(x_train, y_train)
    model = search.best_estimator_
    predictions = model.predict(x_test)
    accuracy = float(accuracy_score(y_test, predictions))
    macro_f1 = float(f1_score(y_test, predictions, average="macro"))
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    report_path = path.with_suffix(".metrics.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    result = TrainingResult(
        accuracy=accuracy,
        macro_f1=macro_f1,
        best_c=float(search.best_params_["classifier__C"]),
        rows=int(quality["rows"]),
        classes=int(quality["classes"]),
        model_path=str(path),
    )
    if use_mlflow:
        _log_and_register(model, x_test, result, report_path)
    return result


def _log_and_register(model, x_example, result: TrainingResult, report_path: Path) -> None:
    import mlflow
    import mlflow.sklearn
    from mlflow.models import infer_signature

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("support-ticket-classification")
    with mlflow.start_run(run_name="tfidf-logistic-regression") as run:
        result.run_id = run.info.run_id
        mlflow.log_params(
            {
                "algorithm": "tfidf_logistic_regression",
                "best_c": result.best_c,
                "training_rows": result.rows,
                "classes": result.classes,
            }
        )
        mlflow.log_metrics({"accuracy": result.accuracy, "macro_f1": result.macro_f1})
        mlflow.log_artifact(str(report_path), artifact_path="evaluation")
        example = x_example.iloc[:3].tolist()
        signature = infer_signature(example, model.predict(example))
        model_info = mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            signature=signature,
        )
        version = mlflow.register_model(model_info.model_uri, MODEL_NAME)
        result.model_version = str(version.version)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", help="local CSV; MinIO then seed data are fallback")
    parser.add_argument("--output", default=MODEL_PATH)
    parser.add_argument("--c-values", default="0.5,1.0,2.0")
    parser.add_argument("--no-mlflow", action="store_true")
    parser.add_argument("--version-output", help="write the registered model version to this file")
    args = parser.parse_args()
    values = tuple(float(value) for value in args.c_values.split(","))
    result = train_model(
        load_training_data(args.data),
        output_path=args.output,
        c_values=values,
        use_mlflow=not args.no_mlflow,
    )
    if args.version_output:
        if result.model_version is None:
            raise RuntimeError("No model version was created")
        version_path = Path(args.version_output)
        version_path.parent.mkdir(parents=True, exist_ok=True)
        version_path.write_text(result.model_version, encoding="utf-8")
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
