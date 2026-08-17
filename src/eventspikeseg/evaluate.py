"""Evaluate a DDD17 timestamp-stream semantic-segmentation checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader

from .data import (
    DDD17_CLASS_COUNT,
    DDD17_CLASS_NAMES,
    DEFAULT_DDD17_ROOT,
    TEMPORAL_PROTOCOL_VERSION,
    build_temporal_dataset,
    deterministic_dataset_subset,
    discover_ddd17_records,
    resolve_ddd17_root,
    temporal_collate,
)
from .metrics import ConfusionMatrix
from .train import build_experiment_model

_PALETTE = np.array(
    [
        [128, 64, 128],
        [0, 0, 0],
        [220, 220, 0],
        [107, 142, 35],
        [220, 20, 60],
        [0, 0, 142],
    ],
    dtype=np.uint8,
)


def _event_image(sequence: torch.Tensor) -> np.ndarray:
    if sequence.ndim == 4:
        sample = sequence[0, :2].detach().cpu()
    else:
        sample = sequence[:, 0].sum(dim=0).detach().cpu()
    channel_0 = sample[0].numpy()
    channel_1 = sample[1].numpy()
    maximum = max(float(channel_0.max()), float(channel_1.max()), 1.0)
    image = np.zeros((*channel_0.shape, 3), dtype=np.uint8)
    image[..., 0] = np.clip(channel_1 / maximum * 255.0, 0, 255).astype(np.uint8)
    image[..., 2] = np.clip(channel_0 / maximum * 255.0, 0, 255).astype(np.uint8)
    return image


def _colour_mask(mask: np.ndarray) -> np.ndarray:
    output = np.zeros((*mask.shape, 3), dtype=np.uint8)
    valid = (mask >= 0) & (mask < len(_PALETTE))
    output[valid] = _PALETTE[mask[valid]]
    return output


def _save_visual(
    destination: Path,
    index: int,
    sequence: torch.Tensor,
    target: torch.Tensor,
    prediction: torch.Tensor,
    spikes: torch.Tensor,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    event = _event_image(sequence)
    target_rgb = _colour_mask(target.detach().cpu().numpy())
    prediction_rgb = _colour_mask(prediction.detach().cpu().numpy())
    confidence = spikes[:, 0].sum(dim=0).amax(dim=0).detach().cpu().numpy()
    confidence = confidence / max(float(confidence.max()), 1.0)
    confidence_rgb = np.repeat((confidence[..., None] * 255).astype(np.uint8), 3, axis=2)
    comparison = np.concatenate(
        (event, target_rgb, prediction_rgb, confidence_rgb), axis=1
    )
    Image.fromarray(comparison).save(destination / f"sample_{index:02d}.png")


def _records_for_checkpoint(
    root: Path,
    checkpoint: dict[str, object],
    *,
    split: str,
    manifest: Path | None,
):
    protocol = checkpoint["temporal_protocol"]
    if not isinstance(protocol, dict):
        raise ValueError("checkpoint temporal_protocol is malformed")
    if split in {"train", "validation"}:
        field = "training_record_ids" if split == "train" else "validation_record_ids"
        raw_ids = protocol.get(field)
        if not isinstance(raw_ids, list):
            raise ValueError(
                f"checkpoint temporal protocol is missing exact {split} record membership"
            )
        record_ids = {(str(value[0]), int(value[1])) for value in raw_ids}
        records = [
            record
            for record in discover_ddd17_records(root, "train", manifest=manifest)
            if (record.sequence_id, record.frame_index) in record_ids
        ]
        if len(records) != len(record_ids):
            raise ValueError(
                f"current manifest does not contain every checkpoint {split} record"
            )
        return records, "train"
    return discover_ddd17_records(root, "test", manifest=manifest), "test"


def evaluate(
    root: Path,
    checkpoint_path: Path,
    *,
    split: str,
    batch_size: int,
    maximum_samples: int,
    visualizations: int,
    visualization_dir: Path,
    device: str,
    manifest: Path | None = None,
) -> dict[str, object]:
    if batch_size != 1:
        raise ValueError("timestamp-stream evaluation requires batch_size=1")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if checkpoint.get("temporal_protocol_version") != TEMPORAL_PROTOCOL_VERSION:
        raise ValueError(
            "legacy checkpoints are obsolete and cannot be evaluated by timestamp-stream v3"
        )
    architecture = str(checkpoint["architecture"])
    protocol = checkpoint.get("temporal_protocol")
    if not isinstance(protocol, dict):
        raise ValueError("checkpoint is missing temporal_protocol")
    input_mode = str(protocol["input_mode"])
    internal_updates = int(
        protocol.get(
            "internal_updates",
            int(protocol["integration_window_us"]) // int(protocol["event_clock_us"]),
        )
    )
    stateful_stream = bool(protocol.get("stateful_stream", True))
    records, dataset_split = _records_for_checkpoint(
        root, checkpoint, split=split, manifest=manifest
    )
    raw_output_size = checkpoint.get("output_size")
    output_size = tuple(int(v) for v in raw_output_size) if raw_output_size is not None else None
    dataset = build_temporal_dataset(
        root,
        split=dataset_split,
        input_mode=input_mode,
        output_size=output_size,
        records=records,
        manifest=manifest,
    )
    dataset = deterministic_dataset_subset(
        dataset, maximum=maximum_samples, seed=int(checkpoint["seed"]) + 1
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, collate_fn=temporal_collate)
    if device == "auto":
        resolved_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        resolved_device = torch.device(device)
    suite = str(checkpoint.get("model_suite", "auto"))
    model = build_experiment_model(
        architecture,
        class_count=DDD17_CLASS_COUNT,
        input_channels=int(checkpoint["input_channels"]),
        suite=suite,
        internal_updates=internal_updates,
    ).to(resolved_device)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    confusion = ConfusionMatrix(DDD17_CLASS_COUNT)
    spike_sum = 0.0
    spike_elements = 0
    saved = 0
    with torch.no_grad():
        for batch_index, (sequence, target) in enumerate(loader):
            sequence = sequence.to(resolved_device)
            target = target.to(resolved_device)
            is_stream_start = getattr(dataset, "is_stream_start", None)
            if not stateful_stream or batch_index == 0 or (
                callable(is_stream_start) and is_stream_start(batch_index)
            ):
                model.reset()
            outputs = model(sequence)
            prediction = outputs["segmentation_logits"].argmax(dim=1)
            confusion.update(prediction, target)
            spikes = outputs["segmentation_spikes"]
            spike_sum += float(spikes.sum())
            spike_elements += spikes.numel()
            if saved < visualizations:
                _save_visual(
                    visualization_dir, saved, sequence, target[0], prediction[0], spikes
                )
                saved += 1
    metrics = confusion.compute().to_dict()
    metrics.update(
        {
            "architecture": architecture,
            "checkpoint": str(checkpoint_path),
            "class_names": list(DDD17_CLASS_NAMES),
            "samples": len(dataset),
            "split": split,
            "input_mode": input_mode,
            "integration_window_us": protocol["integration_window_us"],
            "internal_updates": internal_updates,
            "event_clock_us": protocol["event_clock_us"],
            "mean_spike_rate": spike_sum / max(1, spike_elements),
            "visualization_dir": str(visualization_dir),
        }
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_DDD17_ROOT)
    parser.add_argument("--checkpoint", type=Path, action="append", required=True)
    parser.add_argument("--split", choices=("train", "validation", "test"), default="test")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--visualizations", type=int, default=8)
    parser.add_argument("--visualization-dir", type=Path, default=Path("artifacts/Validation"))
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    root = resolve_ddd17_root(args.root)
    results = []
    for checkpoint_path in args.checkpoint:
        destination = (
            args.visualization_dir / checkpoint_path.stem
            if len(args.checkpoint) > 1
            else args.visualization_dir
        )
        results.append(
            evaluate(
                root,
                checkpoint_path,
                split=args.split,
                batch_size=args.batch_size,
                maximum_samples=args.max_samples,
                visualizations=args.visualizations,
                visualization_dir=destination,
                device=args.device,
                manifest=args.manifest,
            )
        )
    print(json.dumps(results[0] if len(results) == 1 else {"results": results}, indent=2))


if __name__ == "__main__":
    main()
