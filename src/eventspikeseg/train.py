"""Train the final DDD17 model or benchmark isolated architecture suites."""

from __future__ import annotations

import argparse
import json
import random
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
from torch import Tensor, nn
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
from .model import FINAL_ARCHITECTURE_NAME, build_model as build_final_model
from .top_five_models import (
    TOP_FIVE_PRESETS,
    build_top_five_model,
)
from .top_ten_models import (
    TOP_TEN_PRESETS,
    build_top_ten_model,
)

torch.set_num_threads(10)
torch.set_num_interop_threads(1)


def architecture_presets(suite: str) -> dict[str, object]:
    if suite == "top-ten":
        return TOP_TEN_PRESETS
    if suite == "top-five":
        return TOP_FIVE_PRESETS
    if suite == "final":
        return {FINAL_ARCHITECTURE_NAME: object()}
    raise ValueError(f"unknown model suite {suite!r}")


def infer_model_suite(architecture: str) -> str:
    if architecture in TOP_TEN_PRESETS:
        return "top-ten"
    if architecture in TOP_FIVE_PRESETS:
        return "top-five"
    if architecture == FINAL_ARCHITECTURE_NAME:
        return "final"
    raise KeyError(f"unknown architecture {architecture!r}")


def build_experiment_model(
    architecture: str,
    *,
    class_count: int = DDD17_CLASS_COUNT,
    input_channels: int = 6,
    suite: str = "auto",
) -> nn.Module:
    resolved_suite = infer_model_suite(architecture) if suite == "auto" else suite
    if resolved_suite == "top-ten":
        return build_top_ten_model(
            architecture, class_count=class_count, input_channels=input_channels
        )
    if resolved_suite == "top-five":
        return build_top_five_model(
            architecture, class_count=class_count, input_channels=input_channels
        )
    if resolved_suite == "final":
        if architecture != FINAL_ARCHITECTURE_NAME:
            raise KeyError(f"final architecture is {FINAL_ARCHITECTURE_NAME!r}")
        return build_final_model(
            class_count=class_count, input_channels=input_channels
        )
    raise ValueError(f"unknown model suite {resolved_suite!r}")


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
    ground_truth_pixels: tuple[int, ...]
    predicted_pixels: tuple[int, ...]
    layer_spike_rates: dict[str, float]
    neuron_diagnostics: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["per_class_iou"] = list(self.per_class_iou)
        data["ground_truth_pixels"] = list(self.ground_truth_pixels)
        data["predicted_pixels"] = list(self.predicted_pixels)
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


def estimate_class_weights(dataset: DDD17Dataset, maximum: int | None = None) -> Tensor:
    """Estimate weights from the complete selected training subset by default."""
    counts = torch.zeros(DDD17_CLASS_COUNT, dtype=torch.float64)
    limit = len(dataset) if maximum is None else min(len(dataset), maximum)
    for index in range(limit):
        _, mask = dataset[index]
        valid = mask != IGNORE_INDEX
        counts += torch.bincount(mask[valid], minlength=DDD17_CLASS_COUNT)
    frequencies = counts / counts.sum().clamp_min(1.0)
    weights = 1.0 / torch.sqrt(frequencies.clamp_min(1e-6))
    weights /= weights.mean().clamp_min(1e-8)
    return weights.float().clamp(max=8.0)


def focal_cross_entropy(
    logits: Tensor,
    target: Tensor,
    class_weights: Tensor,
    *,
    gamma: float = 1.5,
) -> Tensor:
    valid = target != IGNORE_INDEX
    safe_target = target.masked_fill(~valid, 0)
    log_probability = F.log_softmax(logits, dim=1)
    selected = log_probability.gather(1, safe_target.unsqueeze(1)).squeeze(1)
    probability = selected.exp()
    focal = -(1.0 - probability).pow(gamma) * selected
    focal = focal * class_weights[safe_target]
    return focal[valid].mean() if valid.any() else logits.sum() * 0.0


def _activity_regularizer(outputs: dict[str, Tensor]) -> Tensor:
    hidden_keys = tuple(
        key
        for key in (
            "enc1_spikes", "enc2_spikes", "enc3_spikes", "enc4_spikes", "decoder_spikes"
        )
        if key in outputs
    )
    hidden_rates = torch.stack([outputs[key].mean() for key in hidden_keys])
    output_rate = outputs["segmentation_spikes"].mean()
    dead_hidden = torch.relu(0.005 - hidden_rates).mean()
    excessive_hidden = torch.relu(hidden_rates - 0.25).mean()
    dead_output = torch.relu(0.01 - output_rate)
    excessive_output = torch.relu(output_rate - 0.25)
    return 0.10 * dead_hidden + 0.01 * excessive_hidden + 0.50 * dead_output + 0.01 * excessive_output


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
    model: nn.Module,
    loader: DataLoader,
    *,
    device: torch.device,
) -> tuple[dict[str, object], float, dict[str, float]]:
    model.eval()
    confusion = ConfusionMatrix(DDD17_CLASS_COUNT, IGNORE_INDEX)
    tracked_spike_keys = (
        "enc1_spikes", "enc2_spikes", "enc3_spikes", "enc4_spikes",
        "decoder_spikes", "segmentation_spikes",
    )
    layer_sums: dict[str, float] = {}
    layer_elements: dict[str, int] = {}
    with torch.no_grad():
        for sequence, target in loader:
            sequence = sequence.to(device)
            target = target.to(device)
            model.reset()
            outputs = model(sequence)
            prediction = outputs["segmentation_logits"].argmax(dim=1)
            confusion.update(prediction, target)
            for key in tracked_spike_keys:
                if key not in outputs:
                    continue
                spikes = outputs[key]
                layer_sums[key] = layer_sums.get(key, 0.0) + float(spikes.sum())
                layer_elements[key] = layer_elements.get(key, 0) + spikes.numel()
    metrics = confusion.compute().to_dict()
    rates = {
        key: layer_sums[key] / max(1, layer_elements[key]) for key in layer_sums
    }
    return metrics, rates["segmentation_spikes"], rates


def refinement_phase_for_epoch(
    epoch: int,
    epochs: int,
    schedule: tuple[float, float] | None,
) -> tuple[str, bool]:
    """Return final-model training phase and semantic-backbone trainability.

    Historical benchmark models pass ``schedule=None`` and remain unchanged.
    The canonical model trains jointly, freezes the semantic backbone for late
    detail/decoder refinement, then performs a final all-layer low-LR tune.
    """
    if schedule is None:
        return "joint", True
    freeze_start, unfreeze_start = schedule
    if not (0.0 < freeze_start < unfreeze_start < 1.0):
        raise ValueError("refinement schedule must satisfy 0 < freeze < unfreeze < 1")
    progress = (epoch - 1) / float(max(1, epochs))
    if progress >= unfreeze_start:
        return "final_joint_low_lr", True
    if progress >= freeze_start:
        return "decoder_detail_refinement", False
    return "joint", True


def train_architecture(
    root: Path,
    *,
    architecture: str,
    suite: str = "auto",
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
    resolved_suite = infer_model_suite(architecture) if suite == "auto" else suite
    model = build_experiment_model(
        architecture, class_count=DDD17_CLASS_COUNT, suite=resolved_suite
    ).to(resolved_device)
    base_neuron_tokens = ("beta_logit", "threshold_logit")
    mechanism_tokens = (
        "adaptation_tau_logit", "adaptation_strength_logit", "target_rate_logit",
        "inhibition_strength_logit", "threshold_adaptation_strength_logit", "adaptation_duration_logit",
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
            {"params": base_neuron_parameters, "lr": learning_rate * 2.0, "weight_decay": 0.0}
        )
    if mechanism_parameters:
        # fInst/fLong/TThresh-like parameters alter recurrent dynamics directly;
        # use the base LR so they do not outrun feature learning early on.
        parameter_groups.append(
            {"params": mechanism_parameters, "lr": learning_rate, "weight_decay": 0.0}
        )
    optimizer = torch.optim.AdamW(parameter_groups)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))
    class_weights = estimate_class_weights(train_dataset).to(resolved_device)

    raw_refinement_schedule = getattr(model, "refinement_schedule", None)
    refinement_schedule = (
        tuple(float(value) for value in raw_refinement_schedule)
        if raw_refinement_schedule is not None
        else None
    )
    set_backbone_trainable = getattr(model, "set_semantic_backbone_trainable", None)
    previous_training_phase: str | None = None

    architecture_config = getattr(model, "architecture", None)
    mechanism_round = bool(
        architecture_config is not None
        and (
            getattr(architecture_config, "homeostasis_kind", "legacy") == "triangular_threshold"
            or getattr(architecture_config, "inhibition_kind", "gate") == "peer_membrane"
            or str(getattr(architecture_config, "name", "")).startswith("f01p_")
        )
    )
    warmup_epochs = max(2, int(round(epochs * (0.50 if mechanism_round else 0.30))))
    for epoch in range(1, epochs + 1):
        model.train()
        training_phase, semantic_backbone_trainable = refinement_phase_for_epoch(
            epoch, epochs, refinement_schedule
        )
        if callable(set_backbone_trainable):
            set_backbone_trainable(semantic_backbone_trainable)
        # The final unfreeze is deliberately lower-LR than the decoder/detail
        # refinement phase. CosineAnnealing has already lowered LR late in the
        # run; this one-time multiplier makes the phase boundary explicit.
        if (
            training_phase == "final_joint_low_lr"
            and previous_training_phase != "final_joint_low_lr"
        ):
            for group in optimizer.param_groups:
                group["lr"] *= 0.25
        previous_training_phase = training_phase

        if mechanism_round:
            # Start exactly as the stable PLIF/threshold model, then introduce
            # triangular threshold adaptation smoothly over half the run.
            if epoch == 1:
                homeostasis_scale = 0.0
            else:
                homeostasis_scale = min(
                    1.0, (epoch - 1) / float(max(1, warmup_epochs - 1))
                )
            # Keep mutually-exclusive semantic class WTA active from the start.
            # ``peer_membrane`` is safe to enable immediately because its membrane
            # decrement is multiplied by homeostasis_scale.  ``winner_peer``
            # has a discrete winner gate, so delay only that hidden mechanism
            # until the PLIF/threshold representation has stabilized.
            competition_enabled = True
            winner_peer_inhibition = bool(
                architecture_config is not None
                and getattr(architecture_config, "inhibition_kind", "gate")
                == "winner_peer"
            )
            hidden_inhibition_enabled = (not winner_peer_inhibition) or epoch > warmup_epochs
        else:
            homeostasis_scale = min(1.0, epoch / float(warmup_epochs))
            competition_enabled = epoch > warmup_epochs
            hidden_inhibition_enabled = competition_enabled
        set_homeostasis = getattr(model, "set_homeostasis_scale", None)
        if callable(set_homeostasis):
            set_homeostasis(homeostasis_scale)
        set_competition = getattr(model, "set_competition_enabled", None)
        if callable(set_competition):
            set_competition(competition_enabled)
        set_hidden_inhibition = getattr(model, "set_hidden_inhibition_enabled", None)
        if callable(set_hidden_inhibition):
            set_hidden_inhibition(hidden_inhibition_enabled)
        running_loss = 0.0
        for sequence, target in train_loader:
            sequence = sequence.to(resolved_device)
            target = target.to(resolved_device)
            model.reset()
            outputs = model(sequence)
            logits = outputs["segmentation_logits"]
            ce = F.cross_entropy(logits, target, weight=class_weights, ignore_index=IGNORE_INDEX)
            focal = focal_cross_entropy(logits, target, class_weights)
            dice = soft_dice_loss(logits, target, DDD17_CLASS_COUNT)
            loss = 1.0 * ce + 0.5 * focal + 0.75 * dice + _activity_regularizer(outputs)
            if "auxiliary_logits" in outputs:
                auxiliary = F.interpolate(
                    outputs["auxiliary_logits"], size=target.shape[-2:], mode="nearest"
                )
                auxiliary_ce = F.cross_entropy(
                    auxiliary, target, weight=class_weights, ignore_index=IGNORE_INDEX
                )
                auxiliary_focal = focal_cross_entropy(auxiliary, target, class_weights)
                auxiliary_scale = (
                    0.30 if training_phase == "decoder_detail_refinement" else 0.15
                )
                loss = loss + auxiliary_scale * auxiliary_ce + auxiliary_scale * auxiliary_focal
            if "deep_auxiliary_logits" in outputs:
                deep_auxiliary = F.interpolate(
                    outputs["deep_auxiliary_logits"], size=target.shape[-2:], mode="nearest"
                )
                deep_auxiliary_ce = F.cross_entropy(
                    deep_auxiliary, target, weight=class_weights, ignore_index=IGNORE_INDEX
                )
                deep_auxiliary_focal = focal_cross_entropy(
                    deep_auxiliary, target, class_weights
                )
                # The deepest head is optimization-only and deliberately weaker
                # than the mid-decoder head so it improves gradient flow without
                # overpowering the final dense segmentation objective.
                deep_auxiliary_scale = (
                    0.20 if training_phase == "decoder_detail_refinement" else 0.10
                )
                loss = (
                    loss
                    + deep_auxiliary_scale * deep_auxiliary_ce
                    + deep_auxiliary_scale * deep_auxiliary_focal
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
                    "homeostasis_scale": homeostasis_scale,
                    "competition_enabled": competition_enabled,
                    "hidden_inhibition_enabled": hidden_inhibition_enabled,
                    "training_phase": training_phase,
                    "semantic_backbone_trainable": semantic_backbone_trainable,
                    "learning_rates": [group["lr"] for group in optimizer.param_groups],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    if callable(set_backbone_trainable):
        set_backbone_trainable(True)

    set_homeostasis = getattr(model, "set_homeostasis_scale", None)
    if callable(set_homeostasis):
        set_homeostasis(1.0)
    set_competition = getattr(model, "set_competition_enabled", None)
    if callable(set_competition):
        set_competition(True)
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
        ground_truth_pixels=tuple(int(value) for value in metrics["ground_truth_pixels"]),
        predicted_pixels=tuple(int(value) for value in metrics["predicted_pixels"]),
        layer_spike_rates=layer_spike_rates,
        neuron_diagnostics=neuron_diagnostics,
    )
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "architecture": architecture,
            "model_suite": resolved_suite,
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
    presets = architecture_presets(args.suite)
    results = [
        train_architecture(
            root,
            architecture=name,
            suite=args.suite,
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
        for name in presets
    ]
    winner = select_winner(results)
    summary = {
        "selection_rule": (
            "highest test mIoU; within 0.5 percentage points choose "
            "fewer parameters then lower spike rate"
        ),
        "suite": args.suite,
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
        choices=(
            tuple(TOP_TEN_PRESETS)
            + tuple(TOP_FIVE_PRESETS)
            + (FINAL_ARCHITECTURE_NAME,)
        ),
        default=FINAL_ARCHITECTURE_NAME,
    )
    single.add_argument(
        "--suite", choices=("auto", "top-ten", "top-five", "final"), default="auto"
    )
    single.add_argument("--checkpoint-dir", type=Path, default=Path("artifacts/checkpoints"))

    benchmark = subparsers.add_parser("benchmark")
    _common_training_arguments(benchmark)
    benchmark.add_argument(
        "--suite", choices=("top-ten", "top-five"), default="top-five"
    )
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
            suite=args.suite,
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
