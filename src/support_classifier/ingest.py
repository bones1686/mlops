"""Command-line and Airflow entry point for dataset ingestion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import load_banking77, load_seed_data, upload_csv, validate_dataframe


def ingest(use_seed: bool = False, local_copy: str | None = None) -> dict[str, object]:
    source = "seed"
    if use_seed:
        frame = load_seed_data()
    else:
        try:
            frame = load_banking77()
            source = "PolyAI/banking77"
        except Exception as exc:  # noqa: BLE001 - remote failure intentionally activates seed data
            print(f"BANKING77 download failed; using offline seed data: {exc}")
            frame = load_seed_data()
    report = validate_dataframe(frame)
    uri = upload_csv(frame)
    if local_copy:
        path = Path(local_copy)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    return {"source": source, "uri": uri, **report}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use-seed", action="store_true", help="skip remote download")
    parser.add_argument("--local-copy", help="also write the normalized CSV locally")
    args = parser.parse_args()
    print(json.dumps(ingest(args.use_seed, args.local_copy), indent=2))


if __name__ == "__main__":
    main()
