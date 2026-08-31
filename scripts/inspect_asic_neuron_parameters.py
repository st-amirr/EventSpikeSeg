"""Print learned PLIF parameter ranges from a 140k checkpoint without inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.model_components import ParametricLIF, SpikingStage


def statistics(values: torch.Tensor) -> dict[str, float]:
    values = values.detach().float().cpu().flatten()
    return {
        "minimum": float(values.min()),
        "median": float(values.median()),
        "maximum": float(values.max()),
        "mean": float(values.mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    if checkpoint.get("architecture") != "EventSpikeSeg140k":
        raise ValueError("only EventSpikeSeg140k checkpoints are supported")
    model = EventSpikeSeg140k(
        class_count=11,
        input_channels=int(checkpoint.get("input_channels", 2)),
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    named = dict(model.named_modules())
    layers = []
    all_beta = []
    all_threshold = []
    for name in EVENTSPIKESEG140K_INFERENCE_STAGES:
        stage = named[name]
        assert isinstance(stage, SpikingStage)
        neuron = stage.neuron
        assert isinstance(neuron, ParametricLIF)
        threshold = neuron.learned_threshold
        assert threshold is not None
        all_beta.append(neuron.beta.detach())
        all_threshold.append(threshold.detach())
        layers.append(
            {
                "layer": name,
                "beta": statistics(neuron.beta),
                "threshold": statistics(threshold),
            }
        )
    runtime_keys = [
        key
        for key in checkpoint["model_state_dict"]
        if any(
            token in key
            for token in ("membrane", "last_update_us", "threshold_adaptation_age")
        )
    ]
    print(
        json.dumps(
            {
                "checkpoint": str(args.checkpoint),
                "epoch": checkpoint.get("epoch"),
                "runtime_state_keys": runtime_keys,
                "global_beta": statistics(torch.cat(all_beta)),
                "global_threshold": statistics(torch.cat(all_threshold)),
                "layers": layers,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
