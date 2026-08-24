"""Kubeflow Pipelines v2 definition for the complete MLOps workflow.

Compile with:
    python kubeflow/pipeline.py
"""

from kfp import compiler, dsl

DEFAULT_IMAGE = "support-classifier:0.1.0"

DOCKER_DESKTOP_ENV = {
    "PROJECT_ROOT": "/app",
    "MLFLOW_TRACKING_URI": "http://host.docker.internal:5000",
    "MLFLOW_S3_ENDPOINT_URL": "http://host.docker.internal:9000",
    "S3_ENDPOINT_URL": "http://host.docker.internal:9000",
    "AWS_ACCESS_KEY_ID": "minioadmin",
    "AWS_SECRET_ACCESS_KEY": "minioadmin",
    "DATA_BUCKET": "support-data",
    "DATA_KEY": "training/latest.csv",
    "MODEL_NAME": "support-ticket-classifier",
}


def with_docker_desktop_env(task: dsl.PipelineTask) -> dsl.PipelineTask:
    """Connect a local Kubeflow component to the Compose demo services."""
    for name, value in DOCKER_DESKTOP_ENV.items():
        task.set_env_variable(name=name, value=value)
    return task


@dsl.container_component
def gather_data() -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image=DEFAULT_IMAGE,
        command=["python", "-m", "support_classifier.ingest"],
    )


@dsl.container_component
def validate_data() -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image=DEFAULT_IMAGE,
        command=["python", "-m", "support_classifier.validate"],
    )


@dsl.container_component
def tune_train_and_register(
    candidate_version: dsl.OutputPath(str),
    c_values: str = "0.5,1.0,2.0",
) -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image=DEFAULT_IMAGE,
        command=["python", "-m", "support_classifier.train"],
        args=["--c-values", c_values, "--version-output", candidate_version],
    )


@dsl.container_component
def evaluate_and_promote(
    candidate_version: str,
    min_improvement: float = 0.0,
) -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image=DEFAULT_IMAGE,
        command=["python", "-m", "support_classifier.promote"],
        args=[
            "--version",
            candidate_version,
            "--min-improvement",
            min_improvement,
        ],
    )


@dsl.container_component
def reload_serving(service_url: str) -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image="curlimages/curl:8.10.1",
        command=["sh", "-c"],
        args=["curl -fsS -X POST \"$1/reload\"", "--", service_url],
    )


@dsl.pipeline(
    name="adaptive-support-classification",
    description="Gather, validate, tune, train, register, compare and serve the best classifier.",
)
def support_classification_pipeline(
    c_values: str = "0.5,1.0,2.0",
    min_improvement: float = 0.0,
    serving_url: str = "http://support-api.default.svc.cluster.local:8000",
):
    ingestion = with_docker_desktop_env(gather_data()).set_caching_options(False)
    validation = with_docker_desktop_env(validate_data()).after(ingestion)
    training = with_docker_desktop_env(
        tune_train_and_register(c_values=c_values)
    ).after(validation)
    promotion = with_docker_desktop_env(
        evaluate_and_promote(
            candidate_version=training.outputs["candidate_version"],
            min_improvement=min_improvement,
        )
    )
    reload_serving(service_url=serving_url).after(promotion)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=support_classification_pipeline,
        package_path="support_pipeline.yaml",
    )
