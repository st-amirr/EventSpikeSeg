"""Evaluate a DDD17 semantic-segmentation checkpoint and save visual summaries."""

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
    DDD17Dataset,
    deterministic_record_subset,
    discover_ddd17_records,
    resolve_ddd17_root,
)
from .metrics import ConfusionMatrix
from .model import build_model
from .train import temporal_collate

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
    sample = sequence[0, 0].detach().cpu()
    histogram_0 = sample[0].numpy()
    histogram_1 = sample[1].numpy()
    maximum = max(float(histogram_0.max()), float(histogram_1.max()), 1.0)
    image = np.zeros((*histogram_0.shape, 3), dtype=np.uint8)
    image[..., 0] = np.clip(histogram_1 / maximum * 255.0, 0, 255).astype(np.uint8)
    image[..., 2] = np.clip(histogram_0 / maximum * 255.0, 0, 255).astype(np.uint8)
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
    canvas = np.concatenate((event, target_rgb, prediction_rgb, confidence_rgb), axis=1)
    Image.fromarray(canvas).save(destination / f"sample_{index:02d}.png")


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
) -> dict[str, object]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    architecture = checkpoint["architecture"]
    time_steps = int(checkpoint.get("time_steps", 20))
    records = deterministic_record_subset(
        discover_ddd17_records(root, split),
        maximum=maximum_samples,
        seed=int(checkpoint["seed"]) + 2,
    )
    output_size = tuple(int(value) for value in checkpoint.get("output_size", [64, 64]))
    dataset = DDD17Dataset(root, split=split, records=records, output_size=output_size)
    collate = lambda batch: temporal_collate(batch, time_steps=time_steps)  # noqa: E731
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, collate_fn=collate)
    if device == "auto":
        resolved_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        resolved_device = torch.device(device)
    model = build_model(architecture, class_count=DDD17_CLASS_COUNT).to(resolved_device)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    confusion = ConfusionMatrix(DDD17_CLASS_COUNT)
    spike_sum = 0.0
    spike_elements = 0
    saved = 0
    with torch.no_grad():
        for sequence, target in loader:
            sequence = sequence.to(resolved_device)
            target = target.to(resolved_device)
            model.reset()
            outputs = model(sequence)
            prediction = outputs["segmentation_logits"].argmax(dim=1)
            confusion.update(prediction, target)
            spikes = outputs["segmentation_spikes"]
            spike_sum += float(spikes.sum())
            spike_elements += spikes.numel()
            if saved < visualizations:
                _save_visual(
                    visualization_dir,
                    saved,
                    sequence,
                    target[0],
                    prediction[0],
                    spikes,
                )
                saved += 1
    metrics = confusion.compute().to_dict()
    metrics.update(
        {
            "architecture": architecture,
            "checkpoint": str(checkpoint_path),
            "class_names": list(DDD17_CLASS_NAMES),
            "samples": len(dataset),
            "mean_spike_rate": spike_sum / max(1, spike_elements),
            "visualization_dir": str(visualization_dir),
        }
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_DDD17_ROOT,
        help=f"DDD17 root (default: embedded {DEFAULT_DDD17_ROOT})",
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split", choices=("train", "test"), default="test")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--visualizations", type=int, default=8)
    parser.add_argument("--visualization-dir", type=Path, default=Path("artifacts/Validation"))
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    result = evaluate(
        resolve_ddd17_root(args.root),
        args.checkpoint,
        split=args.split,
        batch_size=args.batch_size,
        maximum_samples=args.max_samples,
        visualizations=args.visualizations,
        visualization_dir=args.visualization_dir,
        device=args.device,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
