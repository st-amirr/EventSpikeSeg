"""Export a trained EventSpikeSeg140k checkpoint for static ASIC actors."""

from __future__ import annotations

import argparse
import json

from eventspikeseg.asic import export_checkpoint


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--height", type=int, default=440)
    parser.add_argument("--width", type=int, default=640)
    args = parser.parse_args()
    manifest = export_checkpoint(
        args.checkpoint, args.output, height=args.height, width=args.width
    )
    summary = {
        key: manifest[key]
        for key in (
            "model",
            "registered_parameters",
            "executed_inference_parameters",
            "executed_convolution_weights",
            "inference_PLIF_populations",
        )
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
