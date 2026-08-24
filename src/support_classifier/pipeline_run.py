"""Run validation, training, registry and promotion as one local workflow."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .data import load_training_data, validate_dataframe
from .promote import promote_candidate
from .train import train_model


def run_pipeline(data: str | None = None, min_improvement: float = 0.0) -> dict[str, object]:
    frame = load_training_data(data)
    quality = validate_dataframe(frame, min_rows_per_class=4)
    training = train_model(frame, use_mlflow=True)
    if training.model_version is None:
        raise RuntimeError("Training completed without a registered model version")
    promotion = promote_candidate(training.model_version, min_improvement)
    return {"quality": quality, "training": asdict(training), "promotion": promotion}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data")
    parser.add_argument("--min-improvement", type=float, default=0.0)
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.data, args.min_improvement), indent=2))


if __name__ == "__main__":
    main()

