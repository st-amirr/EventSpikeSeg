#!/usr/bin/env python3
"""Profile complete native DSEC activity with the exported integer ASIC DAG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from eventspikeseg.asic.activity_profile import profile_native_dsec


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, default=Path("artifacts/ASIC"))
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path(
            "artifacts/checkpointsV4/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
        ),
    )
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/RTL/profile/native_activity_profile.json"),
    )
    parser.add_argument("--maximum-records", type=int, default=0)
    args = parser.parse_args()
    if args.maximum_records < 0:
        parser.error("--maximum-records must be non-negative")
    profile = profile_native_dsec(
        model_spec=args.export / "model_spec.yaml",
        checkpoint_path=args.checkpoint,
        dataset_root=args.dataset_root,
        maximum_records=args.maximum_records,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
