"""Bounded, reproducible MEVDT training entry point for the EventSCNN system."""

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass
from math import ceil, floor
from pathlib import Path

import torch
from torch import Tensor

from .config import BackboneConfig, EventBinningConfig, LIFConfig
from .datasets import (
    MEVDT_VALIDATION_PARTITION_SEED,
    MEVDTBox,
    discover_mevdt_frames,
    load_mevdt_window,
    split_mevdt_train_sequences,
)
from .model import EventSCNNSystem


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


def balanced_training_records(records, max_samples: int, *, seed: int = 17):
    """Select a seeded, class-balanced subset without dataset-order bias."""

    positive = [record for record in records if record.label_path.stat().st_size]
    negative = [record for record in records if not record.label_path.stat().st_size]
    generator = random.Random(seed)
    generator.shuffle(positive)
    generator.shuffle(negative)
    selected = []
    for index in range(max(len(positive), len(negative))):
        if index < len(positive):
            selected.append(positive[index])
        if index < len(negative):
            selected.append(negative[index])
        if len(selected) >= max_samples:
            return selected[:max_samples]
    return selected


def box_to_feature_roi(
    box: MEVDTBox,
    *,
    feature_width: int = 60,
    feature_height: int = 45,
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


def event_supported_attention_target(
    events: Tensor,
    boxes: tuple[MEVDTBox, ...],
    height: int,
    width: int,
    *,
    dilation: int = 1,
) -> Tensor:
    """Create weak pixel attention from event support inside annotated boxes."""

    if events.ndim != 5 or events.shape[2:] != (2, 180, 240):
        raise ValueError("events must have shape [T,N,2,180,240]")
    if dilation < 0:
        raise ValueError("dilation cannot be negative")
    event_activity = events.sum(dim=(0, 2), keepdim=False) > 0
    box_mask = torch.zeros_like(event_activity)
    for box in boxes:
        x0, y0 = floor(box.x_min), floor(box.y_min)
        x1, y1 = ceil(box.x_max), ceil(box.y_max)
        box_mask[:, y0:y1, x0:x1] = True
    supported = (event_activity & box_mask).float().unsqueeze(1)
    target = torch.nn.functional.adaptive_max_pool2d(supported, (height, width))
    if dilation:
        kernel = 2 * dilation + 1
        target = torch.nn.functional.max_pool2d(
            target, kernel_size=kernel, stride=1, padding=dilation
        )
    return target


def window_spike_presence(spikes: Tensor) -> Tensor:
    """Reduce TNCHW spikes to differentiable window-level NCHW presence."""

    if spikes.ndim != 5:
        raise ValueError("spikes must have shape [T,N,C,H,W]")
    return spikes.sum(dim=0).clamp(max=1.0)


def event_activity_target(events: Tensor, height: int, width: int) -> Tensor:
    """Reduce all event support to a locally dilated N1HW feature-support target."""

    if events.ndim != 5 or events.shape[2:] != (2, 180, 240):
        raise ValueError("events must have shape [T,N,2,180,240]")
    support = (events.sum(dim=(0, 2)) > 0).float().unsqueeze(1)
    support = torch.nn.functional.adaptive_max_pool2d(support, (height, width))
    return torch.nn.functional.max_pool2d(support, kernel_size=3, stride=1, padding=1)


def dice_loss(prediction: Tensor, target: Tensor) -> Tensor:
    """Compute a stable soft Dice loss, with empty/empty treated as a match."""

    intersection = (prediction * target).sum()
    return 1.0 - (2.0 * intersection + 1e-6) / (
        prediction.sum() + target.sum() + 1e-6
    )


def attention_centroid_loss(activity: Tensor, boxes: tuple[MEVDTBox, ...]) -> Tensor:
    """Supervise attention centroid without making a box part of inference."""

    if activity.shape[0:2] != (1, 1) or not boxes:
        return activity.sum() * 0.0
    box = max(boxes, key=lambda candidate: candidate.area)
    height, width = activity.shape[-2:]
    xs = torch.arange(width, device=activity.device, dtype=activity.dtype) + 0.5
    ys = torch.arange(height, device=activity.device, dtype=activity.dtype) + 0.5
    total = activity.sum() + 1e-6
    predicted_x = (activity[0, 0] * xs.view(1, -1)).sum() / total
    predicted_y = (activity[0, 0] * ys.view(-1, 1)).sum() / total
    target_x = ((box.x_min + box.x_max) * 0.5) * width / 240.0
    target_y = ((box.y_min + box.y_max) * 0.5) * height / 180.0
    return ((predicted_x - target_x) / width).square() + (
        (predicted_y - target_y) / height
    ).square()


def run_mevdt_training(
    root: Path,
    *,
    max_samples: int = 1,
    window_steps: int = 50,
    learning_rate: float = 1e-3,
    f_inst_enabled: bool = False,
    f_long_enabled: bool = False,
    seed: int = 17,
    validation_fraction: float = 0.2,
    partition_seed: int = MEVDT_VALIDATION_PARTITION_SEED,
    progress_every: int = 0,
    checkpoint_path: Path = Path("artifacts/checkpoints/mevdt_smoke.pt"),
) -> MEVDTTrainingResult:
    """Train on a bounded set of positive MEVDT frames and save a restartable checkpoint."""

    if max_samples <= 0:
        raise ValueError("max_samples must be positive")
    if progress_every < 0:
        raise ValueError("progress_every cannot be negative")
    root = root.expanduser().resolve()
    torch.manual_seed(seed)
    indexed_records = discover_mevdt_frames(root, split="train")
    training_records, validation_records = split_mevdt_train_sequences(
        indexed_records,
        validation_fraction=validation_fraction,
        seed=partition_seed,
    )
    records = balanced_training_records(training_records, max_samples, seed=seed)
    if not records:
        raise ValueError("MEVDT training split contains no indexed samples")

    config = EventBinningConfig(bin_duration_us=1_000)
    training_threshold = 0.25
    baseline_lif = LIFConfig(
        threshold=training_threshold,
        f_inst_enabled=f_inst_enabled,
        f_long_enabled=f_long_enabled,
        adaptation_increment=training_threshold / 16.0,
        adaptation_decay=training_threshold / 32.0,
    )
    system = EventSCNNSystem(
        class_count=2,
        backbone_config=BackboneConfig(lif=baseline_lif),
        classification_current_scale_shift=5,
    )
    with torch.no_grad():
        for block in system.backbone.blocks:
            torch.nn.init.kaiming_normal_(
                block.conv.weight, mode="fan_in", nonlinearity="relu"
            )
        torch.nn.init.kaiming_normal_(
            system.attention.conv.weight, mode="fan_in", nonlinearity="relu"
        )
        torch.nn.init.kaiming_normal_(
            system.classification.synapse.weight,
            mode="fan_in",
            nonlinearity="relu",
        )
    optimizer = torch.optim.AdamW(system.parameters(), lr=learning_rate, weight_decay=1e-4)
    initial_conv1 = system.backbone.blocks[0].conv.weight.detach().clone()
    losses: list[float] = []
    total_input_events = 0
    positive_samples = 0
    negative_samples = 0

    system.train()
    for step, record in enumerate(records, start=1):
        sample = load_mevdt_window(record, config=config, window_steps=window_steps)
        if sample.boxes:
            if any(box.class_id != 1 for box in sample.boxes):
                raise ValueError("MEVDT attention baseline supports vehicle class id 1")
            class_target = torch.tensor([1], dtype=torch.long)
            positive_samples += 1
        else:
            class_target = torch.tensor([0], dtype=torch.long)
            negative_samples += 1
        sequence = sample.events.float()
        total_input_events += int(sequence.sum())
        system.reset()
        outputs = system.trainable_outputs(sequence)
        activity = window_spike_presence(outputs["attention_spikes"])
        target = event_supported_attention_target(
            sequence, sample.boxes, activity.shape[-2], activity.shape[-1]
        )
        attention_weights = 1.0 + 31.0 * target
        weighted_mse = ((activity - target).square() * attention_weights).mean()
        attention_dice_loss = dice_loss(activity, target)
        positive_recall_loss = ((1.0 - activity) * target).sum() / target.sum().clamp_min(1.0)
        centroid_loss = attention_centroid_loss(activity, sample.boxes)
        conv1_presence = window_spike_presence(outputs["conv1_spikes"]).amax(
            dim=1, keepdim=True
        )
        conv1_target = event_activity_target(
            sequence, conv1_presence.shape[-2], conv1_presence.shape[-1]
        )
        feature_support_loss = dice_loss(conv1_presence, conv1_target)
        proposal_loss = (
            weighted_mse
            + attention_dice_loss
            + 0.25 * positive_recall_loss
            + 0.25 * centroid_loss
            + 0.1 * feature_support_loss
        )
        classification_rate_logits = (
            4.0 * outputs["classification_scores"] / float(window_steps)
        )
        classification_loss = torch.nn.functional.cross_entropy(
            classification_rate_logits, class_target
        )
        spike_regularization = sum(
            torch.relu(outputs[name].mean() - 0.05)
            for name in ("conv1_spikes", "conv2_spikes", "conv3_spikes")
        )
        loss = proposal_loss + classification_loss + 0.001 * spike_regularization
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite MEVDT training loss at {record.label_path}")
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
        if progress_every and (step % progress_every == 0 or step == len(records)):
            print(
                json.dumps(
                    {
                        "progress_step": step,
                        "progress_total": len(records),
                        "running_mean_loss": sum(losses) / len(losses),
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
                flush=True,
            )

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
            "seed": seed,
            "architecture": "fully_spiking_attention_v1",
            "backbone_strides": [[2, 2], [2, 2], [1, 1]],
            "attention_kernel": [3, 3],
            "lif_threshold": baseline_lif.threshold,
            "adaptation_increment": baseline_lif.adaptation_increment,
            "adaptation_decay": baseline_lif.adaptation_decay,
            "attention_activity": "window_spike_presence",
            "classification_readout": "bias_free_synapse_lif_spike_count",
            "classification_f_inst_enabled": False,
            "classification_f_long_enabled": False,
            "classification_training_rate_scale": 4.0,
            "classification_current_scale_shift": 5,
            "classification_attention_gradient": "detached",
            "f_inst_enabled": f_inst_enabled,
            "f_long_enabled": f_long_enabled,
            "training_records": [str(record.label_path.relative_to(root)) for record in records],
            "training_sequences": sorted(
                {f"{record.scene}/{record.sequence}" for record in training_records}
            ),
            "validation_sequences": sorted(
                {f"{record.scene}/{record.sequence}" for record in validation_records}
            ),
            "validation_fraction": validation_fraction,
            "partition_seed": partition_seed,
            "sampling": "seeded_balanced_shuffle",
        },
        checkpoint_path,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--max-samples", type=int, default=1)
    parser.add_argument("--window-steps", type=int, default=50)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--f-inst", action="store_true")
    parser.add_argument("--f-long", action="store_true")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--progress-every", type=int, default=0)
    parser.add_argument(
        "--checkpoint", type=Path, default=Path("artifacts/checkpoints/mevdt_attention.pt")
    )
    args = parser.parse_args()
    result = run_mevdt_training(
        args.root,
        max_samples=args.max_samples,
        window_steps=args.window_steps,
        learning_rate=args.learning_rate,
        f_inst_enabled=args.f_inst,
        f_long_enabled=args.f_long,
        seed=args.seed,
        validation_fraction=args.validation_fraction,
        progress_every=args.progress_every,
        checkpoint_path=args.checkpoint,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
