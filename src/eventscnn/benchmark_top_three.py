"""Standalone accuracy benchmark for the active top-three DDD17 SNN contenders.

This module deliberately owns the active three-model ranking experiment.  The generic
``eventscnn.train`` module does not import or register these contenders, which keeps the
canonical/single-model training path independent from the experimental search registry.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader

from .data import (
    DDD17_CLASS_COUNT,
    DDD17_CLASS_NAMES,
    DEFAULT_DDD17_ROOT,
    IGNORE_INDEX,
    resolve_ddd17_root,
)
from .top_three_models import TOP_THREE_PRESETS, build_top_three_model
from .train import (
    TrainResult,
    _activity_regularizer,
    _prepare_datasets,
    estimate_class_weights,
    evaluate_model,
    focal_cross_entropy,
    seed_everything,
    select_winner,
    soft_dice_loss,
    temporal_collate,
)


def train_contender(
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
    """Train one top-three contender under the frozen common benchmark protocol."""
    seed_everything(seed)
    train_dataset, validation_dataset = _prepare_datasets(
        root,
        seed=seed,
        train_samples=train_samples,
        validation_samples=validation_samples,
        output_size=output_size,
    )

    def collate(batch):
        return temporal_collate(batch, time_steps=time_steps)

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

    resolved_device = torch.device(
        "cuda" if device == "auto" and torch.cuda.is_available()
        else "cpu" if device == "auto"
        else device
    )
    model = build_top_three_model(
        architecture,
        class_count=DDD17_CLASS_COUNT,
        input_channels=6,
    ).to(resolved_device)

    base_neuron_tokens = ("beta_logit", "threshold_logit")
    mechanism_tokens = (
        "adaptation_tau_logit",
        "adaptation_strength_logit",
        "target_rate_logit",
        "inhibition_strength_logit",
        "threshold_adaptation_strength_logit",
        "adaptation_duration_logit",
    )
    base_neuron_parameters = []
    mechanism_parameters = []
    weight_parameters = []
    for name, parameter in model.named_parameters():
        if any(token in name for token in mechanism_tokens):
            mechanism_parameters.append(parameter)
        elif any(token in name for token in base_neuron_tokens):
            base_neuron_parameters.append(parameter)
        else:
            weight_parameters.append(parameter)

    parameter_groups = [
        {"params": weight_parameters, "lr": learning_rate, "weight_decay": 1e-4}
    ]
    if base_neuron_parameters:
        parameter_groups.append(
            {
                "params": base_neuron_parameters,
                "lr": learning_rate * 2.0,
                "weight_decay": 0.0,
            }
        )
    if mechanism_parameters:
        parameter_groups.append(
            {
                "params": mechanism_parameters,
                "lr": learning_rate,
                "weight_decay": 0.0,
            }
        )

    optimizer = torch.optim.AdamW(parameter_groups)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=max(1, epochs)
    )
    class_weights = estimate_class_weights(train_dataset).to(resolved_device)

    # All three contenders use the selected mechanism-round dynamics: PLIF,
    # stem-only peer-membrane inhibition and encoder triangular threshold adaptation.
    warmup_epochs = max(2, int(round(epochs * 0.50)))
    for epoch in range(1, epochs + 1):
        model.train()
        homeostasis_scale = (
            0.0
            if epoch == 1
            else min(1.0, (epoch - 1) / float(max(1, warmup_epochs - 1)))
        )
        competition_enabled = True
        hidden_inhibition_enabled = True

        setter = getattr(model, "set_homeostasis_scale", None)
        if callable(setter):
            setter(homeostasis_scale)
        setter = getattr(model, "set_competition_enabled", None)
        if callable(setter):
            setter(competition_enabled)
        setter = getattr(model, "set_hidden_inhibition_enabled", None)
        if callable(setter):
            setter(hidden_inhibition_enabled)

        running_loss = 0.0
        for sequence, target in train_loader:
            sequence = sequence.to(resolved_device)
            target = target.to(resolved_device)
            model.reset()
            outputs = model(sequence)
            logits = outputs["segmentation_logits"]
            ce = F.cross_entropy(
                logits,
                target,
                weight=class_weights,
                ignore_index=IGNORE_INDEX,
            )
            focal = focal_cross_entropy(logits, target, class_weights)
            dice = soft_dice_loss(logits, target, DDD17_CLASS_COUNT)
            loss = (
                0.5 * ce
                + 0.5 * focal
                + 0.75 * dice
                + _activity_regularizer(outputs)
            )
            if "auxiliary_logits" in outputs:
                auxiliary = F.interpolate(
                    outputs["auxiliary_logits"],
                    size=target.shape[-2:],
                    mode="nearest",
                )
                auxiliary_ce = F.cross_entropy(
                    auxiliary,
                    target,
                    weight=class_weights,
                    ignore_index=IGNORE_INDEX,
                )
                auxiliary_focal = focal_cross_entropy(
                    auxiliary, target, class_weights
                )
                loss = loss + 0.15 * auxiliary_ce + 0.15 * auxiliary_focal

            if not torch.isfinite(loss):
                raise RuntimeError(
                    f"non-finite loss for {architecture} at epoch {epoch}"
                )
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
                    "homeostasis_scale": homeostasis_scale,
                    "competition_enabled": competition_enabled,
                    "hidden_inhibition_enabled": hidden_inhibition_enabled,
                },
                sort_keys=True,
            ),
            flush=True,
        )

    setter = getattr(model, "set_homeostasis_scale", None)
    if callable(setter):
        setter(1.0)
    setter = getattr(model, "set_competition_enabled", None)
    if callable(setter):
        setter(True)
    setter = getattr(model, "set_hidden_inhibition_enabled", None)
    if callable(setter):
        setter(True)

    metrics, mean_spike_rate, layer_spike_rates = evaluate_model(
        model, validation_loader, device=resolved_device
    )
    diagnostics_fn = getattr(model, "neuron_diagnostics", None)
    neuron_diagnostics = diagnostics_fn() if callable(diagnostics_fn) else {}

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
        ground_truth_pixels=tuple(
            int(value) for value in metrics["ground_truth_pixels"]
        ),
        predicted_pixels=tuple(
            int(value) for value in metrics["predicted_pixels"]
        ),
        layer_spike_rates=layer_spike_rates,
        neuron_diagnostics=neuron_diagnostics,
    )
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "architecture": architecture,
            "model_suite": "top-three",
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


def run_benchmark(args: argparse.Namespace) -> dict[str, object]:
    """Train all three contenders fairly and persist one ranking summary."""
    root = resolve_ddd17_root(args.root)
    results = [
        train_contender(
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
        for name in TOP_THREE_PRESETS
    ]
    winner = select_winner(results)
    summary = {
        "selection_rule": (
            "highest test mIoU; within 0.5 percentage points choose "
            "fewer parameters then lower spike rate"
        ),
        "suite": "top-three",
        "seed": args.seed,
        "protocol": {
            "epochs": args.epochs,
            "time_steps": args.time_steps,
            "train_samples": args.train_samples,
            "validation_samples": args.validation_samples,
            "height": args.height,
            "width": args.width,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
        },
        "results": [result.to_dict() for result in results],
        "winner": winner.to_dict(),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_DDD17_ROOT)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=14)
    parser.add_argument("--time-steps", type=int, default=15)
    parser.add_argument("--train-samples", type=int, default=2048)
    parser.add_argument("--validation-samples", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=2e-3)
    parser.add_argument("--height", type=int, default=64)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ablation/top_three"),
    )
    args = parser.parse_args()
    print(json.dumps(run_benchmark(args), indent=2))


if __name__ == "__main__":
    main()
