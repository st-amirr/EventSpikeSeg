"""Measure quantized live-neuron occupancy on chronological DSEC records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from eventspikeseg.data import DSECRawEventDataset
from eventspikeseg.fpga.export import EVENTSPIKESEG140K_INFERENCE_STAGES
from eventspikeseg.fpga.profile import LiveStateProfile
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.model_components import ParametricLIF, SpikingStage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--records", type=int, default=4)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.records < 1:
        raise ValueError("--records must be positive")

    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    if checkpoint.get("architecture") != "EventSpikeSeg140k":
        raise ValueError("only EventSpikeSeg140k checkpoints can be profiled")
    protocol = checkpoint.get("temporal_protocol") or {}
    internal_updates = int(protocol.get("internal_updates", 10))
    device_name = args.device
    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_name)
    model = EventSpikeSeg140k(
        class_count=11,
        input_channels=int(checkpoint.get("input_channels", 2)),
        internal_updates=internal_updates,
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.to(device).eval()
    model.set_asynchronous_event_mode(True)

    dataset = DSECRawEventDataset(
        args.root,
        split="train",
        output_size=(241, 351),
        internal_updates=internal_updates,
    )
    profile = LiveStateProfile()
    named = dict(model.named_modules())
    handles = []
    for stage_name in EVENTSPIKESEG140K_INFERENCE_STAGES:
        stage = named[stage_name]
        assert isinstance(stage, SpikingStage)
        neuron = stage.neuron
        assert isinstance(neuron, ParametricLIF)

        def observe(_module, _inputs, _output, *, name=stage_name, source=neuron):
            profile.observe(name, source)

        handles.append(neuron.register_forward_hook(observe))

    model.reset()
    try:
        with torch.no_grad():
            for index in range(min(args.records, len(dataset))):
                if dataset.is_stream_start(index):
                    model.reset()
                sequence, _target, deltas_us = dataset[index]
                model.set_step_deltas_us(deltas_us.to(device))
                outputs = model(sequence.unsqueeze(1).to(device))
                del outputs
                profile.samples += 1
                print(
                    json.dumps(
                        {
                            "record": index,
                            "samples": profile.samples,
                            "high_watermark_entries_sum": sum(
                                profile.high_watermark_by_layer.values()
                            ),
                        }
                    ),
                    flush=True,
                )
    finally:
        for handle in handles:
            handle.remove()
        dataset.close()

    summary = profile.summary()
    encoded = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
