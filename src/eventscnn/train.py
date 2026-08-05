"""Train one DDD17 segmentation model or benchmark the ten architecture presets."""

from __future__ import annotations

import argparse
import json
import random
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
from torch import Tensor
from torch.nn import functional as F
from torch.utils.data import DataLoader

from .data import (
    DDD17_CLASS_COUNT,
    DDD17_CLASS_NAMES,
    DEFAULT_DDD17_ROOT,
    IGNORE_INDEX,
    DDD17Dataset,
    deterministic_record_subset,
    discover_ddd17_records,
    inspect_ddd17,
    resolve_ddd17_root,
)
from .metrics import ConfusionMatrix
from .model import ARCHITECTURE_PRESETS, DEFAULT_ARCHITECTURE, EventSpikeSeg, build_model


@dataclass(frozen=True)
class TrainResult:
    architecture: str
    seed: int
    epochs: int
    train_samples: int
    validation_samples: int
    parameter_count: int
    mean_iou: float
    pixel_accuracy: float
    mean_spike_rate: float
    checkpoint: str
    per_class_iou: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["per_class_iou"] = list(self.per_class_iou)
        return data


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def temporal_collate(
    batch: list[tuple[Tensor, Tensor]], *, time_steps: int
) -> tuple[Tensor, Tensor]:
    sequences: list[Tensor] = []
    masks: list[Tensor] = []
    for events, mask in batch:
        if events.shape[0] == 1:
            # Ev-SegNet supplies one six-channel statistical event image.  Direct
            # encoding applies the same current over the SNN's internal timesteps.
            events = events.expand(time_steps, -1, -1, -1).clone()
        elif events.shape[0] >= time_steps:
            events = events[:time_steps]
        else:
            padding = torch.zeros(
                (time_steps - events.shape[0], *events.shape[1:]), dtype=events.dtype
            )
            events = torch.cat((events, padding), dim=0)
        sequences.append(events)
        masks.append(mask)
    # DataLoader convention is N first; model convention is T first.
    return torch.stack(sequences).permute(1, 0, 2, 3, 4), torch.stack(masks)


def soft_dice_loss(logits: Tensor, target: Tensor, class_count: int) -> Tensor:
    probabilities = logits.softmax(dim=1)
    valid = target != IGNORE_INDEX
    safe_target = target.masked_fill(~valid, 0)
    one_hot = F.one_hot(safe_target, class_count).permute(0, 3, 1, 2).float()
    valid_mask = valid.unsqueeze(1).float()
    probabilities = probabilities * valid_mask
    one_hot = one_hot * valid_mask
    numerator = 2.0 * (probabilities * one_hot).sum(dim=(0, 2, 3)) + 1.0
    denominator = probabilities.sum(dim=(0, 2, 3)) + one_hot.sum(dim=(0, 2, 3)) + 1.0
    return 1.0 - (numerator / denominator).mean()


def estimate_class_weights(dataset: DDD17Dataset, maximum: int = 256) -> Tensor:
    counts = torch.zeros(DDD17_CLASS_COUNT, dtype=torch.float64)
    for index in range(min(len(dataset), maximum)):
        _, mask = dataset[index]
        valid = mask != IGNORE_INDEX
        counts += torch.bincount(mask[valid], minlength=DDD17_CLASS_COUNT)
    frequencies = counts / counts.sum().clamp_min(1.0)
    weights = 1.0 / torch.sqrt(frequencies.clamp_min(1e-5))
    weights /= weights.mean()
    return weights.float().clamp(max=6.0)


def _prepare_datasets(
    root: Path,
    *,
    seed: int,
    train_samples: int,
    validation_samples: int,
    output_size: tuple[int, int],
) -> tuple[DDD17Dataset, DDD17Dataset]:
    train_records = deterministic_record_subset(
        discover_ddd17_records(root, "train"),
        maximum=train_samples,
        seed=seed,
    )
    test_records = deterministic_record_subset(
        discover_ddd17_records(root, "test"),
        maximum=validation_samples,
        seed=seed + 1,
    )
    return (
        DDD17Dataset(root, split="train", records=train_records, output_size=output_size),
        DDD17Dataset(root, split="test", records=test_records, output_size=output_size),
    )


def evaluate_model(
    model: EventSpikeSeg,
    loader: DataLoader,
    *,
    device: torch.device,
) -> tuple[dict[str, object], float]:
    model.eval()
    confusion = ConfusionMatrix(DDD17_CLASS_COUNT, IGNORE_INDEX)
    spike_sum = 0.0
    spike_elements = 0
    with torch.no_grad():
        for sequence, target in loader:
            sequence = sequence.to(device)
            target = target.to(device)
            model.reset()
            outputs = model(sequence)
            prediction = outputs["segmentation_logits"].argmax(dim=1)
            confusion.update(prediction, target)
            spikes = outputs["segmentation_spikes"]
            spike_sum += float(spikes.sum())
            spike_elements += spikes.numel()
    metrics = confusion.compute().to_dict()
    return metrics, spike_sum / max(1, spike_elements)


def train_architecture(
    root: Path,
    *,
    architecture: str,
    seed: int,
    epochs: int,
    batch_size: int,
    time_steps: int,
    train_samples: int,
    validation_samples: int,
    learning_rate: float,
    output_dir: Path,
    output_size: tuple[int, int],
    device: str,
) -> TrainResult:
    seed_everything(seed)
    train_dataset, validation_dataset = _prepare_datasets(
        root,
        seed=seed,
        train_samples=train_samples,
        validation_samples=validation_samples,
        output_size=output_size,
    )
    collate = lambda batch: temporal_collate(batch, time_steps=time_steps)  # noqa: E731
    generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
        num_workers=0,
        collate_fn=collate,
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        collate_fn=collate,
    )
    if device == "auto":
        resolved_device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
    else:
        resolved_device = torch.device(device)
    model = build_model(architecture, class_count=DDD17_CLASS_COUNT).to(resolved_device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))
    class_weights = estimate_class_weights(train_dataset).to(resolved_device)

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for sequence, target in train_loader:
            sequence = sequence.to(resolved_device)
            target = target.to(resolved_device)
            model.reset()
            outputs = model(sequence)
            logits = outputs["segmentation_logits"]
            ce = F.cross_entropy(logits, target, weight=class_weights, ignore_index=IGNORE_INDEX)
            dice = soft_dice_loss(logits, target, DDD17_CLASS_COUNT)
            spike_rate = outputs["segmentation_spikes"].mean()
            loss = ce + 0.5 * dice + 0.001 * torch.relu(spike_rate - 0.10)
            if "auxiliary_logits" in outputs:
                auxiliary = F.interpolate(
                    outputs["auxiliary_logits"], size=target.shape[-2:], mode="nearest"
                )
                loss = loss + 0.3 * F.cross_entropy(
                    auxiliary, target, weight=class_weights, ignore_index=IGNORE_INDEX
                )
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss for {architecture} at epoch {epoch}")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            running_loss += float(loss.detach())
        scheduler.step()
        print(
            json.dumps(
                {
                    "architecture": architecture,
                    "epoch": epoch,
                    "epochs": epochs,
                    "mean_loss": running_loss / max(1, len(train_loader)),
                },
                sort_keys=True,
            ),
            flush=True,
        )

    metrics, mean_spike_rate = evaluate_model(
        model, validation_loader, device=resolved_device
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / f"{architecture}_seed{seed}.pt"
    result = TrainResult(
        architecture=architecture,
        seed=seed,
        epochs=epochs,
        train_samples=len(train_dataset),
        validation_samples=len(validation_dataset),
        parameter_count=model.parameter_count(),
        mean_iou=float(metrics["mean_iou"]),
        pixel_accuracy=float(metrics["pixel_accuracy"]),
        mean_spike_rate=mean_spike_rate,
        checkpoint=str(checkpoint_path),
        per_class_iou=tuple(float(value) for value in metrics["per_class_iou"]),
    )
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "architecture": architecture,
            "architecture_config": model.architecture.to_dict(),
            "class_names": DDD17_CLASS_NAMES,
            "seed": seed,
            "time_steps": time_steps,
            "held_out_split": "test",
            "input_channels": 6,
            "input_representation": "evsegnet_hist_mean_std_direct_encoding",
            "output_size": list(output_size),
            "result": result.to_dict(),
        },
        checkpoint_path,
    )
    return result


def select_winner(results: list[TrainResult]) -> TrainResult:
    if not results:
        raise ValueError("no architecture results")
    best_miou = max(result.mean_iou for result in results)
    close = [result for result in results if best_miou - result.mean_iou <= 0.005]
    return min(close, key=lambda result: (result.parameter_count, result.mean_spike_rate))


def benchmark_architectures(args: argparse.Namespace) -> dict[str, object]:
    root = resolve_ddd17_root(args.root)
    results = [
        train_architecture(
            root,
            architecture=name,
            seed=args.seed,
            epochs=args.epochs,
            batch_size=args.batch_size,
            time_steps=args.time_steps,
            train_samples=args.train_samples,
            validation_samples=args.validation_samples,
            learning_rate=args.learning_rate,
            output_dir=args.output_dir / "checkpoints",
            output_size=(args.height, args.width),
            device=args.device,
        )
        for name in ARCHITECTURE_PRESETS
    ]
    winner = select_winner(results)
    summary = {
        "selection_rule": (
            "highest test mIoU; within 0.5 percentage points choose "
            "fewer parameters then lower spike rate"
        ),
        "seed": args.seed,
        "results": [result.to_dict() for result in results],
        "winner": winner.to_dict(),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def promote_winner(summary_path: Path, destination: Path) -> dict[str, object]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    winner = summary["winner"]
    source = Path(winner["checkpoint"])
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    marker = destination.with_suffix(".json")
    marker.write_text(json.dumps(winner, indent=2), encoding="utf-8")
    return {"winner": winner["architecture"], "checkpoint": str(destination)}


def _common_training_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_DDD17_ROOT,
        help=f"DDD17 root (default: embedded {DEFAULT_DDD17_ROOT})",
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--time-steps", type=int, default=20)
    parser.add_argument("--train-samples", type=int, default=2048)
    parser.add_argument("--validation-samples", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=2e-3)
    parser.add_argument("--height", type=int, default=64)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--device", default="auto")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_DDD17_ROOT,
        help=f"DDD17 root (default: embedded {DEFAULT_DDD17_ROOT})",
    )

    single = subparsers.add_parser("single")
    _common_training_arguments(single)
    single.add_argument(
        "--architecture",
        choices=ARCHITECTURE_PRESETS,
        default=DEFAULT_ARCHITECTURE,
    )
    single.add_argument("--checkpoint-dir", type=Path, default=Path("artifacts/checkpoints"))

    benchmark = subparsers.add_parser("benchmark")
    _common_training_arguments(benchmark)
    benchmark.add_argument("--output-dir", type=Path, default=Path("artifacts/ablation"))

    promote = subparsers.add_parser("promote")
    promote.add_argument(
        "--summary",
        type=Path,
        default=Path("artifacts/ablation/summary.json"),
    )
    promote.add_argument(
        "--destination",
        type=Path,
        default=Path("artifacts/checkpoints/ddd17_best.pt"),
    )

    args = parser.parse_args()
    root = resolve_ddd17_root(args.root) if args.command != "promote" else None
    if args.command == "inspect":
        print(json.dumps(inspect_ddd17(root).to_dict(), indent=2))
    elif args.command == "single":
        result = train_architecture(
            root,
            architecture=args.architecture,
            seed=args.seed,
            epochs=args.epochs,
            batch_size=args.batch_size,
            time_steps=args.time_steps,
            train_samples=args.train_samples,
            validation_samples=args.validation_samples,
            learning_rate=args.learning_rate,
            output_dir=args.checkpoint_dir,
            output_size=(args.height, args.width),
            device=args.device,
        )
        print(json.dumps(result.to_dict(), indent=2))
    elif args.command == "benchmark":
        print(json.dumps(benchmark_architectures(args), indent=2))
    else:
        print(json.dumps(promote_winner(args.summary, args.destination), indent=2))


if __name__ == "__main__":
    main()
