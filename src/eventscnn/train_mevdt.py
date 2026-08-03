"""Bounded, reproducible MEVDT training entry point for the EventSCNN system."""

import argparse
import json
from dataclasses import asdict, dataclass
from math import ceil, floor
from pathlib import Path

import torch
from torch import Tensor

from .config import BackboneConfig, EventBinningConfig, LIFConfig
from .datasets import MEVDTBox, discover_mevdt_frames, load_mevdt_window
from .system import EventSCNNSystem


@dataclass(frozen=True)
class MEVDTTrainingResult:
    samples: int
    positive_samples: int
    negative_samples: int
    optimizer_steps: int
    mean_loss: float
    final_loss: float
    max_conv1_weight_change: float
    total_input_events: int
    checkpoint: str


def box_to_feature_roi(
    box: MEVDTBox,
    *,
    feature_width: int = 30,
    feature_height: int = 23,
) -> Tensor:
    """Project a native 240x180 XYXY box to a clipped Conv3 XYWH ROI."""

    x0 = max(0, floor(box.x_min * feature_width / 240))
    y0 = max(0, floor(box.y_min * feature_height / 180))
    x1 = min(feature_width, ceil(box.x_max * feature_width / 240))
    y1 = min(feature_height, ceil(box.y_max * feature_height / 180))
    return torch.tensor([[x0, y0, max(1, x1 - x0), max(1, y1 - y0)]])


def objectness_target(boxes: tuple[MEVDTBox, ...], height: int, width: int) -> Tensor:
    """Rasterize native boxes onto the Conv1 objectness feature map."""

    target = torch.zeros((1, 1, height, width), dtype=torch.float32)
    for box in boxes:
        x0 = max(0, floor(box.x_min * width / 240))
        y0 = max(0, floor(box.y_min * height / 180))
        x1 = min(width, ceil(box.x_max * width / 240))
        y1 = min(height, ceil(box.y_max * height / 180))
        target[:, :, y0:y1, x0:x1] = 1.0
    return target


def run_mevdt_training(
    root: Path,
    *,
    max_samples: int = 1,
    window_steps: int = 20,
    learning_rate: float = 1e-3,
    checkpoint_path: Path = Path("artifacts/checkpoints/mevdt_smoke.pt"),
) -> MEVDTTrainingResult:
    """Train on a bounded set of positive MEVDT frames and save a restartable checkpoint."""

    if max_samples <= 0:
        raise ValueError("max_samples must be positive")
    root = root.expanduser().resolve()
    torch.manual_seed(17)
    indexed_records = discover_mevdt_frames(root, split="train")
    positive_records = [record for record in indexed_records if record.label_path.stat().st_size]
    negative_records = [
        record for record in indexed_records if not record.label_path.stat().st_size
    ]
    records = []
    for index in range(max(len(positive_records), len(negative_records))):
        if index < len(positive_records):
            records.append(positive_records[index])
        if index < len(negative_records):
            records.append(negative_records[index])
        if len(records) >= max_samples:
            records = records[:max_samples]
            break
    if not records:
        raise ValueError("MEVDT training split contains no indexed samples")

    config = EventBinningConfig(bin_duration_us=1_000)
    baseline_lif = LIFConfig(f_inst_enabled=False, f_long_enabled=False)
    system = EventSCNNSystem(
        class_count=2,
        backbone_config=BackboneConfig(lif=baseline_lif),
    )
    optimizer = torch.optim.AdamW(system.parameters(), lr=learning_rate, weight_decay=1e-4)
    initial_conv1 = system.backbone.blocks[0].conv.weight.detach().clone()
    losses: list[float] = []
    total_input_events = 0
    positive_samples = 0
    negative_samples = 0

    system.train()
    for record in records:
        sample = load_mevdt_window(record, config=config, window_steps=window_steps)
        if sample.boxes:
            target_box = max(sample.boxes, key=lambda box: box.area)
            if target_box.class_id != 1:
                raise ValueError(f"unsupported MEVDT class id: {target_box.class_id}")
            roi = box_to_feature_roi(target_box)
            class_target = torch.tensor([1], dtype=torch.long)
            positive_samples += 1
        else:
            roi = torch.tensor([[0, 0, 30, 23]])
            class_target = torch.tensor([0], dtype=torch.long)
            negative_samples += 1
        sequence = sample.events.float()
        total_input_events += int(sequence.sum())
        system.reset()
        outputs = system.trainable_outputs(sequence, roi)
        activity = outputs["objectness_spikes"].mean(dim=0)
        target = objectness_target(sample.boxes, activity.shape[-2], activity.shape[-1])
        # Foreground boxes occupy a small fraction of the 90x120 map. A bounded
        # positive weight prevents the all-background solution without destabilizing
        # sparse samples whose boxes cover only a handful of feature locations.
        proposal_weights = 1.0 + 9.0 * target
        proposal_loss = ((activity - target).square() * proposal_weights).mean()
        classification_loss = torch.nn.functional.cross_entropy(
            outputs["classification_logits"], class_target
        )
        spike_regularization = sum(
            outputs[name].mean()
            for name in ("conv1_spikes", "conv2_spikes", "conv3_spikes")
        )
        loss = proposal_loss + classification_loss + 0.001 * spike_regularization
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite MEVDT training loss at {record.label_path}")
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))

    if not losses:
        raise RuntimeError("MEVDT training produced no optimizer steps")
    weight_change = float(
        (system.backbone.blocks[0].conv.weight.detach() - initial_conv1).abs().max()
    )
    if weight_change <= 0:
        raise RuntimeError("MEVDT training did not update Conv1 weights")

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    result = MEVDTTrainingResult(
        samples=len(losses),
        positive_samples=positive_samples,
        negative_samples=negative_samples,
        optimizer_steps=len(losses),
        mean_loss=sum(losses) / len(losses),
        final_loss=losses[-1],
        max_conv1_weight_change=weight_change,
        total_input_events=total_input_events,
        checkpoint=str(checkpoint_path),
    )
    torch.save(
        {
            "model_state_dict": system.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "training_result": asdict(result),
            "bin_duration_us": config.bin_duration_us,
            "window_steps": window_steps,
            "seed": 17,
            "f_inst_enabled": False,
            "f_long_enabled": False,
            "training_records": [str(record.label_path.relative_to(root)) for record in records],
        },
        checkpoint_path,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--max-samples", type=int, default=1)
    parser.add_argument("--window-steps", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument(
        "--checkpoint", type=Path, default=Path("artifacts/checkpoints/mevdt_smoke.pt")
    )
    args = parser.parse_args()
    result = run_mevdt_training(
        args.root,
        max_samples=args.max_samples,
        window_steps=args.window_steps,
        learning_rate=args.learning_rate,
        checkpoint_path=args.checkpoint,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
