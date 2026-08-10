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
from tqdm.auto import tqdm

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
from .model import (
    FINAL_MODELS,
    build_model as build_final_model,
)
from .top_five_models import (
    TOP_FIVE_PRESETS,
    build_top_five_model,
)
from .top_three_models import (
    TOP_THREE_PRESETS,
    build_top_three_model,
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
    if suite == "top-three":
        return TOP_THREE_PRESETS
    if suite == "final":
        return FINAL_MODELS
    raise ValueError(f"unknown model suite {suite!r}")


def infer_model_suite(architecture: str) -> str:
    if architecture in TOP_TEN_PRESETS:
        return "top-ten"
    if architecture in TOP_FIVE_PRESETS:
        return "top-five"
    if architecture in TOP_THREE_PRESETS:
        return "top-three"
    if architecture in FINAL_MODELS:
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
    if resolved_suite == "top-three":
        return build_top_three_model(
            architecture, class_count=class_count, input_channels=input_channels
        )
    if resolved_suite == "final":
        if architecture not in FINAL_MODELS:
            raise KeyError(
                f"final suite requires one of {tuple(FINAL_MODELS)!r}, got {architecture!r}"
            )
        return build_final_model(
            class_count=class_count,
            input_channels=input_channels,
            architecture=architecture,
        )
    raise ValueError(f"unknown model suite {resolved_suite!r}")


@dataclass(frozen=True)
class TrainResult:
    architecture: str
    seed: int
    epochs: int
    train_samples: float
    validation_samples: float
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


@dataclass(frozen=True)
class LossProfile:
    """Frozen objective weights for reproducible suites."""

    cross_entropy: float
    focal: float = 0.5
    dice: float = 0.75
    auxiliary_ce: float = 0.15
    auxiliary_focal: float = 0.15


HISTORICAL_LOSS_PROFILE = LossProfile(cross_entropy=0.5)
FINAL_LOSS_PROFILE = LossProfile(cross_entropy=1.0)


def loss_profile_for_suite(suite: str) -> LossProfile:
    if suite in {"top-ten", "top-five", "top-three"}:
        return HISTORICAL_LOSS_PROFILE
    if suite == "final":
        return FINAL_LOSS_PROFILE
    raise ValueError(f"unknown model suite {suite!r}")


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
    # Ev-SegNet DDD17 supplies one six-channel statistical event image per
    # record. Direct encoding reuses that same current over all SNN timesteps.
    # Keep this as an expanded *view* instead of cloning T physical copies.
    if all(events.shape[0] == 1 for events, _ in batch):
        static_batch = torch.stack([events[0] for events, _ in batch], dim=0)
        sequence = static_batch.unsqueeze(0).expand(
            time_steps, -1, -1, -1, -1
        )
        masks = torch.stack([mask for _, mask in batch])
        return sequence, masks

    sequences: list[Tensor] = []
    masks: list[Tensor] = []
    for events, mask in batch:
        if events.shape[0] >= time_steps:
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
    scalar_hidden_keys = tuple(
        key
        for key in ("enc1_rate", "enc2_rate", "enc3_rate", "enc4_rate", "decoder_rate")
        if key in outputs
    )
    if scalar_hidden_keys:
        hidden_rates = torch.stack([outputs[key] for key in scalar_hidden_keys])
    else:
        # Frozen historical registries preserve their full-spike output contract.
        hidden_keys = tuple(
            key
            for key in (
                "enc1_spikes", "enc2_spikes", "enc3_spikes", "enc4_spikes", "decoder_spikes"
            )
            if key in outputs
        )
        hidden_rates = torch.stack([outputs[key].mean() for key in hidden_keys])
    output_rate = outputs.get("segmentation_rate")
    if output_rate is None:
        output_rate = outputs["segmentation_spikes"].mean()
    dead_hidden = torch.relu(0.005 - hidden_rates).mean()
    excessive_hidden = torch.relu(hidden_rates - 0.25).mean()
    dead_output = torch.relu(0.01 - output_rate)
    excessive_output = torch.relu(output_rate - 0.25)
    return 0.10 * dead_hidden + 0.01 * excessive_hidden + 0.50 * dead_output + 0.01 * excessive_output


def _record_subset_from_spec(
    records: list, *, amount: float, seed: int
) -> list:
    """Select records by fraction or absolute count.

    amount <= 0: all records
    0 < amount <= 1: fraction of available records
    amount > 1: absolute record count (must be integer-valued)
    """
    if amount <= 0:
        maximum = 0
    elif amount <= 1:
        maximum = max(1, int(round(len(records) * amount)))
    else:
        if not float(amount).is_integer():
            raise ValueError(
                "sample values above 1 must be integer counts; "
                f"got {amount!r}"
            )
        maximum = int(amount)
    return deterministic_record_subset(records, maximum=maximum, seed=seed)


def _prepare_datasets(
    root: Path,
    *,
    seed: int,
    output_size: tuple[int, int] | None,
    final_validation_fraction: float | None = None,
) -> tuple[DDD17Dataset, DDD17Dataset]:
    """Build the fixed train pool and held-out set.

    ``--train-samples`` is applied later per epoch so each epoch can draw a
    fresh random subset from this pool. Validation/test stay fixed.
    """
    all_train_records = discover_ddd17_records(root, "train")
    if final_validation_fraction is not None:
        if not (0.0 < final_validation_fraction < 0.5):
            raise ValueError("validation_fraction must satisfy 0 < value < 0.5")
        if len(all_train_records) < 2:
            raise ValueError("at least two DDD17 training records are required")
        generator = torch.Generator().manual_seed(seed + 1)
        order = torch.randperm(len(all_train_records), generator=generator).tolist()
        validation_count = max(
            1, int(round(len(all_train_records) * final_validation_fraction))
        )
        validation_count = min(validation_count, len(all_train_records) - 1)
        validation_records = [all_train_records[index] for index in order[:validation_count]]
        training_records = [all_train_records[index] for index in order[validation_count:]]
        return (
            DDD17Dataset(
                root, split="train", records=training_records, output_size=output_size
            ),
            DDD17Dataset(
                root, split="train", records=validation_records, output_size=output_size
            ),
        )

    # Historical architecture-search behavior: benchmark against the official
    # Ev-SegNet test split exactly as the completed rounds did. Do not use this
    # branch for checkpoint selection in the canonical final-model run.
    test_records = discover_ddd17_records(root, "test")
    return (
        DDD17Dataset(
            root, split="train", records=all_train_records, output_size=output_size
        ),
        DDD17Dataset(root, split="test", records=test_records, output_size=output_size),
    )


def _epoch_train_dataset(
    train_pool: DDD17Dataset,
    *,
    train_samples: float,
    seed: int,
    epoch: int,
) -> DDD17Dataset:
    """Draw a fresh ``train_samples`` subset from the fixed train pool."""
    epoch_records = _record_subset_from_spec(
        train_pool.records,
        amount=train_samples,
        seed=seed + epoch * 1009,
    )
    return DDD17Dataset(
        train_pool.root,
        split="train",
        records=epoch_records,
        output_size=train_pool.output_size,
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
    tracked_rate_keys = (
        "enc1_rate", "enc2_rate", "enc3_rate", "enc4_rate",
        "decoder_rate", "segmentation_rate",
    )
    layer_sums: dict[str, float] = {}
    layer_elements: dict[str, int] = {}
    scalar_rate_sums: dict[str, float] = {}
    scalar_rate_batches: dict[str, int] = {}
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
            for key in tracked_rate_keys:
                if key not in outputs:
                    continue
                scalar_rate_sums[key] = scalar_rate_sums.get(key, 0.0) + float(outputs[key])
                scalar_rate_batches[key] = scalar_rate_batches.get(key, 0) + 1
            # no_grad avoids an autograd graph, but the full temporal output
            # tensors are still large. Drop the batch references before the
            # loader produces the next native-resolution batch.
            del outputs, prediction, sequence, target
    metrics = confusion.compute().to_dict()
    rates = {
        key: layer_sums[key] / max(1, layer_elements[key]) for key in layer_sums
    }
    for key, total in scalar_rate_sums.items():
        rates[key] = total / max(1, scalar_rate_batches[key])
    output_rate = rates.get(
        "segmentation_rate", rates.get("segmentation_spikes", float("nan"))
    )
    return metrics, output_rate, rates


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
    train_samples: float,
    validation_fraction: float,
    learning_rate: float,
    output_dir: Path,
    output_size: tuple[int, int] | None,
    device: str,
    checkpoint_every: int = 5,
    amp: bool = False,
    accumulate_steps: int = 1,
    load: Path | None = None,
) -> TrainResult:
    seed_everything(seed)
    resolved_suite = infer_model_suite(architecture) if suite == "auto" else suite
    loss_profile = loss_profile_for_suite(resolved_suite)
    train_pool, validation_dataset = _prepare_datasets(
        root,
        seed=seed,
        output_size=output_size,
        final_validation_fraction=(
            validation_fraction if resolved_suite == "final" else None
        ),
    )
    collate = lambda batch: temporal_collate(batch, time_steps=time_steps)  # noqa: E731
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
    model = build_experiment_model(
        architecture, class_count=DDD17_CLASS_COUNT, suite=resolved_suite
    ).to(resolved_device)
    amp_enabled = bool(amp and resolved_device.type == "cuda")
    scaler = torch.cuda.amp.GradScaler(enabled=amp_enabled)
    output_dir.mkdir(parents=True, exist_ok=True)
    is_final_run = resolved_suite == "final"
    if checkpoint_every < 1:
        raise ValueError("checkpoint_every must be >= 1")
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
    class_weights = estimate_class_weights(train_pool).to(resolved_device)

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

    best_mean_iou = float("-inf")
    best_epoch = 0
    best_metrics: dict[str, object] | None = None
    best_mean_spike_rate = 0.0
    best_layer_spike_rates: dict[str, float] = {}
    best_neuron_diagnostics: dict[str, float] = {}
    best_checkpoint_path = output_dir / f"{architecture}_seed{seed}_best.pt"
    last_checkpoint_path = output_dir / f"{architecture}_seed{seed}_last.pt"
    canonical_checkpoint_path = output_dir / f"{architecture}_seed{seed}.pt"

    def save_training_checkpoint(
        path: Path,
        *,
        epoch_number: int,
        validation_metrics: dict[str, object] | None,
        validation_spike_rate: float | None,
        validation_layer_rates: dict[str, float] | None,
        training_phase_name: str,
        best: bool = False,
    ) -> None:
        diagnostics_fn = getattr(model, "neuron_diagnostics", None)
        diagnostics = diagnostics_fn() if callable(diagnostics_fn) else {}
        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "scaler_state_dict": scaler.state_dict(),
                "best_mean_iou": best_mean_iou,
                "best_epoch": best_epoch,
                "best_validation_metrics": best_metrics,
                "best_validation_mean_spike_rate": best_mean_spike_rate,
                "best_validation_layer_spike_rates": best_layer_spike_rates,
                "best_neuron_diagnostics": best_neuron_diagnostics,
                "architecture": architecture,
                "model_suite": resolved_suite,
                "architecture_config": model.architecture.to_dict(),
                "class_names": DDD17_CLASS_NAMES,
                "seed": seed,
                "epoch": epoch_number,
                "epochs": epochs,
                "time_steps": time_steps,
                "held_out_split": "train_holdout" if is_final_run else "test",
                "input_channels": 6,
                "input_representation": "evsegnet_hist_mean_std_direct_encoding",
                "output_size": list(output_size) if output_size is not None else None,
                "training_phase": training_phase_name,
                "amp": amp_enabled,
                "validation_metrics": validation_metrics,
                "validation_mean_spike_rate": validation_spike_rate,
                "validation_layer_spike_rates": validation_layer_rates or {},
                "neuron_diagnostics": diagnostics,
                "is_best": best,
            },
            path,
        )

    start_epoch = 1
    if load is not None:
        load_path = Path(load)
        if not load_path.is_file():
            raise FileNotFoundError(f"resume checkpoint not found: {load_path}")
        checkpoint = torch.load(load_path, map_location=resolved_device)
        checkpoint_architecture = checkpoint.get("architecture")
        if checkpoint_architecture not in (None, architecture):
            raise ValueError(
                f"checkpoint architecture {checkpoint_architecture!r} does not match "
                f"requested architecture {architecture!r}"
            )
        if "model_state_dict" not in checkpoint:
            raise KeyError(f"checkpoint has no model_state_dict: {load_path}")
        model.load_state_dict(checkpoint["model_state_dict"])

        optimizer_state = checkpoint.get("optimizer_state_dict")
        scheduler_state = checkpoint.get("scheduler_state_dict")
        scaler_state = checkpoint.get("scaler_state_dict")
        if optimizer_state is not None:
            optimizer.load_state_dict(optimizer_state)
        if scheduler_state is not None:
            scheduler.load_state_dict(scheduler_state)
        if scaler_state is not None and amp_enabled:
            scaler.load_state_dict(scaler_state)

        loaded_epoch = int(checkpoint.get("epoch", 0))
        start_epoch = loaded_epoch + 1
        if start_epoch > epochs:
            raise ValueError(
                f"checkpoint is already at epoch {loaded_epoch}, but --epochs={epochs}; "
                "set --epochs to a larger total target"
            )

        checkpoint_metrics = checkpoint.get("validation_metrics")
        checkpoint_miou = (
            float(checkpoint_metrics["mean_iou"])
            if isinstance(checkpoint_metrics, dict) and "mean_iou" in checkpoint_metrics
            else float("-inf")
        )
        best_mean_iou = float(checkpoint.get("best_mean_iou", checkpoint_miou))
        best_epoch = int(checkpoint.get("best_epoch", loaded_epoch if checkpoint_miou > float("-inf") else 0))
        best_metrics = checkpoint.get("best_validation_metrics")
        if best_metrics is None and checkpoint.get("is_best"):
            best_metrics = checkpoint_metrics
        best_mean_spike_rate = float(
            checkpoint.get(
                "best_validation_mean_spike_rate",
                checkpoint.get("validation_mean_spike_rate", 0.0) if checkpoint.get("is_best") else 0.0,
            )
            or 0.0
        )
        best_layer_spike_rates = dict(
            checkpoint.get(
                "best_validation_layer_spike_rates",
                checkpoint.get("validation_layer_spike_rates", {}) if checkpoint.get("is_best") else {},
            )
            or {}
        )
        best_neuron_diagnostics = dict(
            checkpoint.get(
                "best_neuron_diagnostics",
                checkpoint.get("neuron_diagnostics", {}) if checkpoint.get("is_best") else {},
            )
            or {}
        )
        previous_training_phase = checkpoint.get("training_phase")
        print(
            f"Resuming {architecture} from {load_path} | "
            f"completed_epoch={loaded_epoch} next_epoch={start_epoch} target_epoch={epochs}",
            flush=True,
        )

    precision = "AMP FP16" if amp_enabled else "FP32"
    size_label = (
        f"{output_size[0]}x{output_size[1]}" if output_size is not None else "native"
    )
    example_epoch_train = _epoch_train_dataset(
        train_pool, train_samples=train_samples, seed=seed, epoch=1
    )
    print(
        f"Training {architecture} | {resolved_device} | {precision} | "
        f"epochs={epochs} batch={batch_size} accumulate={accumulate_steps} "
        f"effective_batch={batch_size * accumulate_steps} "
        f"T={time_steps} size={size_label} | "
        f"train_pool={len(train_pool)} epoch_train={len(example_epoch_train)} "
        f"val={len(validation_dataset)} | "
        f"params={model.parameter_count():,}",
        flush=True,
    )


    for epoch in range(start_epoch, epochs + 1):
        model.train()
        epoch_train_dataset = _epoch_train_dataset(
            train_pool, train_samples=train_samples, seed=seed, epoch=epoch
        )
        train_loader = DataLoader(
            epoch_train_dataset,
            batch_size=batch_size,
            shuffle=True,
            generator=torch.Generator().manual_seed(seed + epoch),
            num_workers=0,
            collate_fn=collate,
        )
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
        total_batches = len(train_loader)
        progress = tqdm(
            train_loader,
            total=total_batches,
            desc=f"Epoch {epoch:02d}/{epochs:02d}",
            unit="batch",
            dynamic_ncols=True,
            leave=True,
        )
        optimizer.zero_grad(set_to_none=True)
        for batch_index, (sequence, target) in enumerate(progress, start=1):
            sequence = sequence.to(resolved_device)
            target = target.to(resolved_device)
            model.reset()
            with torch.cuda.amp.autocast(enabled=amp_enabled, dtype=torch.float16):
                outputs = model(sequence)
                logits = outputs["segmentation_logits"]
                ce = F.cross_entropy(logits, target, weight=class_weights, ignore_index=IGNORE_INDEX)
                focal = focal_cross_entropy(logits, target, class_weights)
                dice = soft_dice_loss(logits, target, DDD17_CLASS_COUNT)
                activity = _activity_regularizer(outputs)
                loss = (
                    loss_profile.cross_entropy * ce
                    + loss_profile.focal * focal
                    + loss_profile.dice * dice
                    + activity
                )
                auxiliary = auxiliary_ce = auxiliary_focal = None
                deep_auxiliary = deep_auxiliary_ce = deep_auxiliary_focal = None
                auxiliary_term = logits.new_zeros(())
                deep_auxiliary_term = logits.new_zeros(())
                if "auxiliary_logits" in outputs:
                    auxiliary = F.interpolate(
                        outputs["auxiliary_logits"], size=target.shape[-2:], mode="nearest"
                    )
                    auxiliary_ce = F.cross_entropy(
                        auxiliary, target, weight=class_weights, ignore_index=IGNORE_INDEX
                    )
                    auxiliary_focal = focal_cross_entropy(auxiliary, target, class_weights)
                    auxiliary_ce_weight = (
                        0.30
                        if is_final_run and training_phase == "decoder_detail_refinement"
                        else loss_profile.auxiliary_ce
                    )
                    auxiliary_focal_weight = (
                        0.30
                        if is_final_run and training_phase == "decoder_detail_refinement"
                        else loss_profile.auxiliary_focal
                    )
                    auxiliary_term = (
                        auxiliary_ce_weight * auxiliary_ce
                        + auxiliary_focal_weight * auxiliary_focal
                    )
                    loss = loss + auxiliary_term
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
                    deep_auxiliary_term = deep_auxiliary_scale * (
                        deep_auxiliary_ce + deep_auxiliary_focal
                    )
                    loss = loss + deep_auxiliary_term
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss for {architecture} at epoch {epoch}")
            # Average gradients across micro-batches so accumulate_steps mimics
            # a larger batch without holding those samples in memory together.
            scaled_loss = loss / float(accumulate_steps)
            scaler.scale(scaled_loss).backward()
            should_step = (
                batch_index % accumulate_steps == 0 or batch_index == total_batches
            )
            gradient_norm = None
            if should_step:
                scaler.unscale_(optimizer)
                gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
            batch_loss = float(loss.detach())
            running_loss += batch_loss
            output_spike_rate = float(
                outputs["segmentation_rate"].detach()
                if "segmentation_rate" in outputs
                else outputs["segmentation_spikes"].detach().mean()
            )
            progress.set_postfix(
                loss=f"{batch_loss:.4f}",
                avg=f"{running_loss / batch_index:.4f}",
                lr=f"{optimizer.param_groups[0]['lr']:.2e}",
                spike=f"{output_spike_rate:.4f}",
                phase=training_phase,
                refresh=False,
            )


            # Do not carry a completed batch's autograd graph into the next
            # forward pass. Python locals otherwise keep the large output/aux
            # tensors alive until they are overwritten during the next batch,
            # which can nearly double peak host RAM at native resolution.
            del outputs, logits, loss, scaled_loss, ce, focal, dice, activity
            del auxiliary, auxiliary_ce, auxiliary_focal
            del deep_auxiliary, deep_auxiliary_ce, deep_auxiliary_focal
            del auxiliary_term, deep_auxiliary_term, gradient_norm
            del sequence, target
        scheduler.step()
        mean_epoch_loss = running_loss / max(1, len(train_loader))
        print(
            f"Epoch {epoch:02d}/{epochs:02d} complete | "
            f"loss={mean_epoch_loss:.4f} | phase={training_phase} | "
            f"homeostasis={homeostasis_scale:.2f}",
            flush=True,
        )


        if is_final_run:
            validation_metrics, validation_spike_rate, validation_layer_rates = evaluate_model(
                model, validation_loader, device=resolved_device
            )
            validation_miou = float(validation_metrics["mean_iou"])
            improved = validation_miou > best_mean_iou
            if improved:
                best_mean_iou = validation_miou
                best_epoch = epoch
                best_metrics = validation_metrics
                best_mean_spike_rate = validation_spike_rate
                best_layer_spike_rates = validation_layer_rates
                diagnostics_fn = getattr(model, "neuron_diagnostics", None)
                best_neuron_diagnostics = (
                    diagnostics_fn() if callable(diagnostics_fn) else {}
                )
                save_training_checkpoint(
                    best_checkpoint_path,
                    epoch_number=epoch,
                    validation_metrics=validation_metrics,
                    validation_spike_rate=validation_spike_rate,
                    validation_layer_rates=validation_layer_rates,
                    training_phase_name=training_phase,
                    best=True,
                )
            if epoch % checkpoint_every == 0:
                periodic_path = output_dir / (
                    f"{architecture}_seed{seed}_epoch{epoch:03d}.pt"
                )
                save_training_checkpoint(
                    periodic_path,
                    epoch_number=epoch,
                    validation_metrics=validation_metrics,
                    validation_spike_rate=validation_spike_rate,
                    validation_layer_rates=validation_layer_rates,
                    training_phase_name=training_phase,
                )
            best_marker = " | new best" if improved else ""
            checkpoint_marker = " | checkpoint saved" if epoch % checkpoint_every == 0 else ""
            print(
                f"Validation {epoch:02d}/{epochs:02d} | "
                f"mIoU={validation_miou:.4f} | "
                f"pixel_acc={float(validation_metrics['pixel_accuracy']):.4f} | "
                f"spike={validation_spike_rate:.4f} | "
                f"best={best_mean_iou:.4f} (epoch {best_epoch})"
                f"{best_marker}{checkpoint_marker}",
                flush=True,
            )

            model.train()

    if callable(set_backbone_trainable):
        set_backbone_trainable(True)

    set_homeostasis = getattr(model, "set_homeostasis_scale", None)
    if callable(set_homeostasis):
        set_homeostasis(1.0)
    set_competition = getattr(model, "set_competition_enabled", None)
    if callable(set_competition):
        set_competition(True)
    if is_final_run:
        # Preserve the last state for recovery, then expose the best-validation
        # checkpoint at the historical canonical filename for compatibility.
        final_metrics, final_spike_rate, final_layer_rates = evaluate_model(
            model, validation_loader, device=resolved_device
        )
        save_training_checkpoint(
            last_checkpoint_path,
            epoch_number=epochs,
            validation_metrics=final_metrics,
            validation_spike_rate=final_spike_rate,
            validation_layer_rates=final_layer_rates,
            training_phase_name=previous_training_phase or "joint",
        )
        if not best_checkpoint_path.is_file():
            raise RuntimeError("best checkpoint was not created during final-model training")
        shutil.copy2(best_checkpoint_path, canonical_checkpoint_path)
        if best_metrics is None:
            raise RuntimeError("best validation metrics were not recorded")
        metrics = best_metrics
        mean_spike_rate = best_mean_spike_rate
        layer_spike_rates = best_layer_spike_rates
        neuron_diagnostics = best_neuron_diagnostics
        checkpoint_path = canonical_checkpoint_path
    else:
        metrics, mean_spike_rate, layer_spike_rates = evaluate_model(
            model, validation_loader, device=resolved_device
        )
        diagnostics_fn = getattr(model, "neuron_diagnostics", None)
        neuron_diagnostics = diagnostics_fn() if callable(diagnostics_fn) else {}
        checkpoint_path = output_dir / f"{architecture}_seed{seed}.pt"

    result = TrainResult(
        architecture=architecture,
        seed=seed,
        epochs=epochs,
        train_samples=len(example_epoch_train),
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
    if not is_final_run:
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
                "output_size": list(output_size) if output_size is not None else None,
                "result": result.to_dict(),
            },
            checkpoint_path,
        )
    print(
        f"Training complete | mIoU={result.mean_iou:.4f} | "
        f"pixel_acc={result.pixel_accuracy:.4f} | checkpoint={result.checkpoint}",
        flush=True,
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
            validation_fraction=args.validation_fraction,
            learning_rate=args.learning_rate,
            output_dir=args.output_dir / "checkpoints",
            output_size=_resolve_output_size(args.height, args.width),
            device=args.device,
            checkpoint_every=args.checkpoint_every,
            amp=args.amp,
            accumulate_steps=args.accumulate_steps,
            load=None,
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
        "protocol": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "time_steps": args.time_steps,
            "train_samples": args.train_samples,
            "height": args.height,
            "width": args.width,
            "learning_rate": args.learning_rate,
            "loss_profile": asdict(loss_profile_for_suite(args.suite)),
        },
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


def _resolve_output_size(height: int | None, width: int | None) -> tuple[int, int] | None:
    if height is None and width is None:
        return None
    if height is None or width is None:
        raise ValueError("--height and --width must be provided together, or both omitted")
    if height <= 0 or width <= 0:
        raise ValueError("--height and --width must be positive")
    return (height, width)


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
    parser.add_argument(
        "--train-samples", type=float, default=2048.0,
        help=(
            "per-epoch random draw from the train pool: "
            "0=all, 0<x<=1=fraction, x>1=absolute count (reshuffled each epoch)"
        ),
    )
    parser.add_argument(
        "--validation-fraction",
        type=float,
        default=0.10,
        help="fraction of the DDD17 training split reserved for validation in the final suite",
    )
    parser.add_argument("--learning-rate", type=float, default=2e-3)
    parser.add_argument(
        "--height", type=int, default=None,
        help="optional resize height; omit together with --width to preserve native dataset size",
    )
    parser.add_argument(
        "--width", type=int, default=None,
        help="optional resize width; omit together with --height to preserve native dataset size",
    )
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=5,
        help="save a recoverable periodic checkpoint every N epochs (final suite)",
    )
    parser.add_argument(
        "--amp",
        action="store_true",
        help="enable CUDA automatic mixed precision (FP16 autocast + GradScaler)",
    )
    parser.add_argument(
        "--accumulate-steps",
        type=int,
        default=1,
        help=(
            "accumulate gradients over this many micro-batches before an optimizer "
            "step (effective batch = batch-size * accumulate-steps; memory stays ~batch-size)"
        ),
    )


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
            + tuple(TOP_THREE_PRESETS)
            + tuple(FINAL_MODELS)
        ),
        default="EventSpikeSeg",
    )
    single.add_argument(
        "--suite", choices=("auto", "top-ten", "top-five", "top-three", "final"), default="auto"
    )
    single.add_argument("--checkpoint-dir", type=Path, default=Path("artifacts/checkpoints"))
    single.add_argument(
        "--load",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "resume from this checkpoint file (full path + filename); "
            "omit to start training from scratch"
        ),
    )

    benchmark = subparsers.add_parser("benchmark")
    _common_training_arguments(benchmark)
    benchmark.add_argument(
        "--suite", choices=("top-ten", "top-five", "top-three"), default="top-five"
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
            validation_fraction=args.validation_fraction,
            learning_rate=args.learning_rate,
            output_dir=args.checkpoint_dir,
            output_size=_resolve_output_size(args.height, args.width),
            device=args.device,
            checkpoint_every=args.checkpoint_every,
            amp=args.amp,
            accumulate_steps=args.accumulate_steps,
            load=args.load,
        )
    elif args.command == "benchmark":
        print(json.dumps(benchmark_architectures(args), indent=2))
    else:
        print(json.dumps(promote_winner(args.summary, args.destination), indent=2))


if __name__ == "__main__":
    main()
