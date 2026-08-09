"""Report complete MEVDT validation metrics separately for each frozen sequence."""

import argparse
import json
from pathlib import Path

import torch

from eventspikeseg.evaluate_mevdt import evaluate_mevdt_checkpoint


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()

    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    sequence_keys = sorted(checkpoint.get("validation_sequences", []))
    if not sequence_keys:
        parser.error("checkpoint does not freeze validation sequences")

    results = {}
    for sequence_key in sequence_keys:
        result = evaluate_mevdt_checkpoint(
            args.root,
            args.checkpoint,
            split="validation",
            sequence_key=sequence_key,
        )
        results[sequence_key] = {
            "samples": result.samples,
            "classification_f1": result.classification_f1,
            "attention_iou": result.attention_iou,
            "hota": result.hota,
            "hota_detection_accuracy": result.hota_detection_accuracy,
            "hota_association_accuracy": result.hota_association_accuracy,
            "mota": result.mota,
            "idf1": result.idf1,
            "tracking_success_auc": result.tracking_success_auc,
            "tracked_center_precision_at_20": result.tracked_center_precision_at_20,
            "true_positives_at_0_5": result.tracking_true_positives_at_0_5,
            "false_positives_at_0_5": result.tracking_false_positives_at_0_5,
            "false_negatives_at_0_5": result.tracking_false_negatives_at_0_5,
            "identity_switches_at_0_5": result.tracking_identity_switches_at_0_5,
        }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
