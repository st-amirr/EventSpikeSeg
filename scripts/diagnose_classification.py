"""Compare class-current, membrane, threshold, and spike traces across checkpoints."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import torch

from eventspikeseg.config import BackboneConfig, EventBinningConfig, LIFConfig
from eventspikeseg.datasets import load_mevdt_window
from eventspikeseg.evaluate_mevdt import select_mevdt_evaluation_records
from eventspikeseg.system import EventSpikeSegSystem
from eventspikeseg.train_mevdt import event_supported_attention_target


def _trace_summary(trace: dict[str, torch.Tensor], threshold: float) -> dict[str, list[float]]:
    currents = trace["currents"]
    candidates = trace["candidate_membranes"]
    spikes = trace["spikes"]
    return {
        "current_mean": currents.mean(dim=(0, 1)).tolist(),
        "current_max": currents.amax(dim=(0, 1)).tolist(),
        "candidate_max": candidates.amax(dim=(0, 1)).tolist(),
        "threshold_crossings": (candidates >= threshold).sum(dim=(0, 1)).float().tolist(),
        "spike_counts": spikes.sum(dim=(0, 1)).tolist(),
    }


def _average_summaries(summaries: list[dict[str, list[float]]]) -> dict[str, list[float]]:
    return {
        key: torch.tensor([summary[key] for summary in summaries]).mean(dim=0).tolist()
        for key in summaries[0]
    }


def diagnose_checkpoint(
    root: Path,
    checkpoint_path: Path,
    *,
    samples_per_class: int,
) -> dict[str, object]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    lif = LIFConfig(
        threshold=float(checkpoint["lif_threshold"]),
        f_inst_enabled=bool(checkpoint["f_inst_enabled"]),
        f_long_enabled=bool(checkpoint["f_long_enabled"]),
        adaptation_increment=float(checkpoint["adaptation_increment"]),
        adaptation_decay=float(checkpoint["adaptation_decay"]),
    )
    system = EventSpikeSegSystem(
        class_count=2,
        backbone_config=BackboneConfig(lif=lif),
        classification_current_scale_shift=int(
            checkpoint.get("classification_current_scale_shift", 0)
        ),
    )
    system.load_state_dict(checkpoint["model_state_dict"])
    system.eval()
    records = select_mevdt_evaluation_records(root, checkpoint, split="validation")
    config = EventBinningConfig(bin_duration_us=int(checkpoint["bin_duration_us"]))
    collected: dict[tuple[str, int], list[dict[str, list[float]]]] = defaultdict(list)

    with torch.no_grad():
        for record in records:
            sample = load_mevdt_window(
                record,
                config=config,
                window_steps=int(checkpoint["window_steps"]),
            )
            target_class = int(bool(sample.boxes))
            if len(collected[("predicted_attention", target_class)]) >= samples_per_class:
                if all(
                    len(collected[(mode, class_id)]) >= samples_per_class
                    for mode in ("predicted_attention", "oracle_attention")
                    for class_id in (0, 1)
                ):
                    break
                continue
            system.reset()
            activations = system.backbone(sample.events.float(), return_all=True)
            predicted_attention = system.attention(activations[0])
            attention_height, attention_width = predicted_attention.shape[-2:]
            oracle = event_supported_attention_target(
                sample.events.float(), sample.boxes, attention_height, attention_width
            )
            oracle_attention = oracle.unsqueeze(0).expand(
                activations[2].shape[0], -1, -1, -1, -1
            )
            for mode, attention in (
                ("predicted_attention", predicted_attention),
                ("oracle_attention", oracle_attention),
            ):
                system.classification.reset()
                trace = system.classification.forward_attention_trace(activations[2], attention)
                collected[(mode, target_class)].append(
                    _trace_summary(trace, system.classification.neuron.config.threshold)
                )

    return {
        "checkpoint": checkpoint_path.name,
        "seed": int(checkpoint["seed"]),
        "class_threshold": system.classification.neuron.config.threshold,
        "samples_per_class": samples_per_class,
        "traces": {
            mode: {
                str(class_id): _average_summaries(collected[(mode, class_id)])
                for class_id in (0, 1)
            }
            for mode in ("predicted_attention", "oracle_attention")
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, action="append", required=True)
    parser.add_argument("--samples-per-class", type=int, default=8)
    args = parser.parse_args()
    if args.samples_per_class <= 0:
        parser.error("--samples-per-class must be positive")
    report = [
        diagnose_checkpoint(
            args.root,
            checkpoint,
            samples_per_class=args.samples_per_class,
        )
        for checkpoint in args.checkpoint
    ]
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
