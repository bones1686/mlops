"""Validate the current object-storage or local training dataset."""

from __future__ import annotations

import argparse
import json

from .data import load_training_data, validate_dataframe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data")
    args = parser.parse_args()
    print(json.dumps(validate_dataframe(load_training_data(args.data), 4), indent=2))


if __name__ == "__main__":
    main()

