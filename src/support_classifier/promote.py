"""Champion–challenger comparison using MLflow model aliases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import MLFLOW_TRACKING_URI, MODEL_NAME


def _metric(client, version, name: str) -> float:
    run = client.get_run(version.run_id)
    return float(run.data.metrics.get(name, 0.0))


def promote_candidate(
    candidate_version: str,
    min_improvement: float = 0.0,
    model_name: str = MODEL_NAME,
) -> dict[str, object]:
    from mlflow import MlflowClient, set_tracking_uri
    from mlflow.exceptions import MlflowException

    set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()
    candidate = client.get_model_version(model_name, candidate_version)
    candidate_f1 = _metric(client, candidate, "macro_f1")
    client.set_registered_model_alias(model_name, "challenger", candidate_version)
    client.set_model_version_tag(model_name, candidate_version, "validation_status", "evaluated")

    champion = None
    try:
        champion = client.get_model_version_by_alias(model_name, "champion")
    except MlflowException:
        champion = None

    champion_f1 = _metric(client, champion, "macro_f1") if champion else None
    should_promote = champion is None or candidate_f1 >= float(champion_f1) + min_improvement
    if should_promote:
        client.set_registered_model_alias(model_name, "champion", candidate_version)
        client.set_model_version_tag(model_name, candidate_version, "deployment_status", "champion")
        if champion and champion.version != candidate_version:
            client.set_model_version_tag(model_name, champion.version, "deployment_status", "archived")

    return {
        "candidate_version": candidate_version,
        "candidate_macro_f1": candidate_f1,
        "previous_champion_version": champion.version if champion else None,
        "previous_champion_macro_f1": champion_f1,
        "promoted": should_promote,
        "required_improvement": min_improvement,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    version_group = parser.add_mutually_exclusive_group(required=True)
    version_group.add_argument("--version")
    version_group.add_argument("--version-file")
    parser.add_argument("--min-improvement", type=float, default=0.0)
    parser.add_argument("--result-output")
    args = parser.parse_args()
    version = args.version or Path(args.version_file).read_text(encoding="utf-8").strip()
    result = promote_candidate(version, args.min_improvement)
    if args.result_output:
        result_path = Path(args.result_output)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
