"""Train spike-native semantic models on DDD17 or raw-event DSEC."""

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
    DEFAULT_DDD17_ROOT,
    DEFAULT_DSEC_ROOT,
    DEFAULT_INTERNAL_UPDATES,
    DSEC_INPUT_MODE,
    IGNORE_INDEX,
    INPUT_MODES,
    DSECRawEventDataset,
    TemporalDataset,
    build_temporal_dataset,
    deterministic_dataset_subset,
    discover_ddd17_records,
    discover_dsec_records,
    dsec_temporal_collate,
    inspect_ddd17,
    inspect_dsec,
    make_dsec_protocol,
    make_temporal_protocol,
    resolve_ddd17_root,
    resolve_dsec_root,
    split_dsec_records_by_sequence,
    split_records_by_sequence,
    temporal_collate,
)
from .metrics import ConfusionMatrix
from .model import FINAL_MODELS
from .model import build_model as build_final_model
from .top_five_models import (
    TOP_FIVE_PRESETS,
    build_top_five_model,
)
from .top_ten_models import (
    TOP_TEN_PRESETS,
    build_top_ten_model,
)
from .top_three_models import (
    TOP_THREE_PRESETS,
    build_top_three_model,
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


def apply_resume_learning_rate(
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    *,
    learning_rate: float,
) -> list[float]:
    """Apply the CLI LR after restoring optimizer/scheduler state.

    Checkpoints retain Adam moments and the scheduler's elapsed epoch, but the
    optimizer state also contains its old parameter-group LRs. A supplied CLI
    value explicitly replaces those rates on resume.
    """
    group_rates = [learning_rate] * len(optimizer.param_groups)
    for group, rate in zip(optimizer.param_groups, group_rates):
        group["lr"] = rate
        group["initial_lr"] = rate
    scheduler.base_lrs = list(group_rates)
    scheduler._last_lr = list(group_rates)
    return group_rates


def build_experiment_model(
    architecture: str,
    *,
    class_count: int = DDD17_CLASS_COUNT,
    input_channels: int = 6,
    suite: str = "auto",
    internal_updates: int = DEFAULT_INTERNAL_UPDATES,
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
            internal_updates=internal_updates,
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


def soft_dice_loss(logits: Tensor, target: Tensor, class_count: int) -> Tensor:
    """Differentiable Dice loss for each semantic class in the current batch."""
    probabilities = logits.softmax(dim=1)
    valid = target != IGNORE_INDEX
    safe_target = target.masked_fill(~valid, 0)
    one_hot = F.one_hot(safe_target, class_count).permute(0, 3, 1, 2).float()
    valid_mask = valid.unsqueeze(1).float()
    probabilities = probabilities * valid_mask
    one_hot = one_hot * valid_mask
    numerator = 2.0 * (probabilities * one_hot).sum(dim=(0, 2, 3)) + 1.0
    denominator = probabilities.sum(dim=(0, 2, 3)) + one_hot.sum(dim=(0, 2, 3)) + 1.0
    return 1.0 - numerator / denominator


def estimate_class_weights(dataset: TemporalDataset, maximum: int | None = None) -> Tensor:
    """Use capped median-frequency balancing over the selected training subset."""
    class_count = int(getattr(dataset, "class_count", DDD17_CLASS_COUNT))
    counts = torch.zeros(class_count, dtype=torch.float64)
    limit = len(dataset) if maximum is None else min(len(dataset), maximum)
    for index in range(limit):
        mask = dataset.target_mask(index)
        valid = mask != IGNORE_INDEX
        counts += torch.bincount(mask[valid], minlength=class_count)
    frequencies = counts / counts.sum().clamp_min(1.0)
    median_frequency = frequencies[counts > 0].median().clamp_min(1e-6)
    weights = median_frequency / frequencies.clamp_min(1e-6)
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
    return (
        0.10 * dead_hidden
        + 0.01 * excessive_hidden
        + 0.50 * dead_output
        + 0.01 * excessive_output
    )


def split_temporal_chunks(sequence: Tensor, chunk_count: int) -> tuple[Tensor, ...]:
    """Split raw-event TNC inputs into equal chronological TBPTT chunks."""
    if chunk_count < 1:
        raise ValueError("sequential_chunks must be >= 1")
    if chunk_count == 1:
        return (sequence,)
    if sequence.ndim != 5:
        raise ValueError(
            "sequential_chunks > 1 requires a raw-event [T,N,C,H,W] input"
        )
    if sequence.shape[0] % chunk_count != 0:
        raise ValueError(
            f"time dimension {sequence.shape[0]} must divide evenly into "
            f"{chunk_count} sequential chunks"
        )
    return tuple(sequence.chunk(chunk_count, dim=0))


def _training_objective(
    outputs: dict[str, Tensor],
    target: Tensor,
    *,
    class_weights: Tensor,
    class_count: int,
    loss_profile: LossProfile,
    is_final_run: bool,
    training_phase: str,
) -> tuple[Tensor, Tensor, Tensor]:
    """Build one chunk's objective and detached reporting spike rate."""
    logits = outputs["segmentation_logits"]
    ce = F.cross_entropy(
        logits,
        target,
        weight=class_weights,
        ignore_index=IGNORE_INDEX,
    )
    focal = focal_cross_entropy(logits, target, class_weights)
    dice_losses = soft_dice_loss(logits, target, class_count)
    valid_target = target[target != IGNORE_INDEX]
    present_classes = (
        torch.bincount(valid_target, minlength=class_count) > 0
        if valid_target.numel() > 0
        else torch.zeros(class_count, dtype=torch.bool, device=target.device)
    )
    present_dice_loss = (
        dice_losses[present_classes].mean()
        if present_classes.any()
        else logits.sum() * 0.0
    )
    loss = (
        loss_profile.cross_entropy * ce
        + loss_profile.focal * focal
        + loss_profile.dice * present_dice_loss
        + _activity_regularizer(outputs)
    )
    if "auxiliary_logits" in outputs:
        auxiliary = F.interpolate(
            outputs["auxiliary_logits"], size=target.shape[-2:], mode="nearest"
        )
        auxiliary_ce = F.cross_entropy(
            auxiliary, target, weight=class_weights, ignore_index=IGNORE_INDEX
        )
        auxiliary_focal = focal_cross_entropy(auxiliary, target, class_weights)
        auxiliary_weight = (
            0.30
            if is_final_run and training_phase == "decoder_detail_refinement"
            else None
        )
        loss = loss + (
            (loss_profile.auxiliary_ce if auxiliary_weight is None else auxiliary_weight)
            * auxiliary_ce
            + (
                loss_profile.auxiliary_focal
                if auxiliary_weight is None
                else auxiliary_weight
            )
            * auxiliary_focal
        )
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
        deep_auxiliary_scale = (
            0.20 if training_phase == "decoder_detail_refinement" else 0.10
        )
        loss = loss + deep_auxiliary_scale * (
            deep_auxiliary_ce + deep_auxiliary_focal
        )
    output_spike_rate = outputs.get("segmentation_rate")
    if output_spike_rate is None:
        output_spike_rate = outputs["segmentation_spikes"].mean()
    return loss, dice_losses, output_spike_rate.detach()


def _dataset_subset_from_spec(
    dataset: TemporalDataset, *, amount: float, seed: int
) -> TemporalDataset:
    """Select temporal samples by fraction or absolute count."""
    if amount <= 0:
        maximum = 0
    elif amount <= 1:
        maximum = max(1, int(round(len(dataset) * amount)))
    else:
        if not float(amount).is_integer():
            raise ValueError(
                "sample values above 1 must be integer counts; " f"got {amount!r}"
            )
        maximum = int(amount)
    return deterministic_dataset_subset(dataset, maximum=maximum, seed=seed)


def _prepare_datasets(
    root: Path,
    *,
    seed: int,
    output_size: tuple[int, int] | None,
    validation_fraction: float,
    input_mode: str,
    manifest: Path | None,
    train_samples: float = 0.0,
    internal_updates: int = DEFAULT_INTERNAL_UPDATES,
    stateful_stream: bool = True,
    dataset_name: str = "ddd17",
) -> tuple[TemporalDataset, TemporalDataset, dict[str, object], str]:
    """Build sequence-disjoint train/validation datasets and freeze their protocol."""
    if dataset_name == "dsec":
        if input_mode != DSEC_INPUT_MODE:
            raise ValueError("DSEC requires --input-mode raw-events")
        if manifest is not None:
            raise ValueError("DSEC chronology comes from sequence timestamp files, not --manifest")
        all_train_records = discover_dsec_records(root, "train")
        training_records, validation_records = split_dsec_records_by_sequence(
            all_train_records,
            validation_fraction=validation_fraction,
            train_samples=train_samples,
        )
        train_pool = DSECRawEventDataset(
            root,
            split="train",
            output_size=output_size,
            internal_updates=internal_updates,
            records=training_records,
        )
        validation_dataset = DSECRawEventDataset(
            root,
            split="train",
            output_size=output_size,
            internal_updates=internal_updates,
            records=validation_records,
        )
        protocol = make_dsec_protocol(
            root,
            validation_fraction=validation_fraction,
            training_records=training_records,
            validation_records=validation_records,
            internal_updates=internal_updates,
            stateful_stream=stateful_stream,
        )
        return (
            train_pool,
            validation_dataset,
            protocol.to_dict(),
            protocol.fingerprint,
        )
    if dataset_name != "ddd17":
        raise ValueError(f"unknown dataset {dataset_name!r}")
    if input_mode not in INPUT_MODES:
        raise ValueError("DDD17 requires --input-mode timestamp-events")
    all_train_records = discover_ddd17_records(root, "train", manifest=manifest)
    training_records, validation_records = split_records_by_sequence(
        all_train_records,
        validation_fraction=validation_fraction,
        seed=seed,
    )
    train_pool = build_temporal_dataset(
        root,
        split="train",
        input_mode=input_mode,
        output_size=output_size,
        records=training_records,
        manifest=manifest,
    )
    validation_dataset = build_temporal_dataset(
        root,
        split="train",
        input_mode=input_mode,
        output_size=output_size,
        records=validation_records,
        manifest=manifest,
    )
    protocol = make_temporal_protocol(
        root,
        input_mode=input_mode,
        validation_fraction=validation_fraction,
        training_records=training_records,
        validation_records=validation_records,
        internal_updates=internal_updates,
        stateful_stream=stateful_stream,
        manifest=manifest,
    )
    return train_pool, validation_dataset, protocol.to_dict(), protocol.fingerprint


def _epoch_train_dataset(
    train_pool: TemporalDataset,
    *,
    train_samples: float,
    seed: int,
    epoch: int,
) -> TemporalDataset:
    """Select one deterministic contiguous stream segment for an epoch."""
    total = len(train_pool)
    if train_samples <= 0:
        return train_pool
    if isinstance(train_pool, DSECRawEventDataset) and train_samples < 1:
        grouped_indices: dict[str, list[int]] = {}
        for index, record in enumerate(train_pool.records):
            grouped_indices.setdefault(record.sequence_id, []).append(index)
        generator = torch.Generator().manual_seed(seed + epoch)
        selected_indices: list[int] = []
        for sequence_id in sorted(grouped_indices):
            indices = grouped_indices[sequence_id]
            count = max(1, int(round(len(indices) * train_samples)))
            maximum_start = len(indices) - count
            start = (
                int(torch.randint(0, maximum_start + 1, (1,), generator=generator).item())
                if maximum_start > 0
                else 0
            )
            selected_indices.extend(indices[start : start + count])
        return train_pool.subset(selected_indices)
    if train_samples <= 1:
        count = max(1, int(round(total * train_samples)))
    else:
        if not float(train_samples).is_integer():
            raise ValueError(
                "sample values above 1 must be integer counts; " f"got {train_samples!r}"
            )
        count = min(total, int(train_samples))
    if count >= total:
        return train_pool
    generator = torch.Generator().manual_seed(seed + epoch)
    start = int(torch.randint(0, total - count + 1, (1,), generator=generator).item())
    indices = list(range(start, start + count))
    return train_pool.subset(indices)

def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    *,
    device: torch.device,
    stateful_stream: bool = True,
) -> tuple[dict[str, object], float, dict[str, float]]:
    model.eval()
    class_count = int(loader.dataset.class_count)
    confusion = ConfusionMatrix(class_count, IGNORE_INDEX)
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
        for batch_index, (sequence, target) in enumerate(loader):
            sequence = sequence.to(device)
            target = target.to(device)
            dataset = loader.dataset
            is_stream_start = getattr(dataset, "is_stream_start", None)
            if not stateful_stream or batch_index == 0 or (
                callable(is_stream_start) and is_stream_start(batch_index)
            ):
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
    input_mode: str,
    manifest: Path | None,
    train_samples: float,
    validation_fraction: float,
    learning_rate: float,
    output_dir: Path,
    output_size: tuple[int, int] | None,
    device: str,
    checkpoint_every: int = 5,
    amp: bool = False,
    accumulate_steps: int = 1,
    internal_updates: int = DEFAULT_INTERNAL_UPDATES,
    sequential_chunks: int = 1,
    continuous_state: bool = True,
    dataset_name: str = "ddd17",
    load: Path | None = None,
) -> TrainResult:
    if batch_size != 1:
        raise ValueError("timestamp-stream training requires batch_size=1")
    if sequential_chunks < 1:
        raise ValueError("sequential_chunks must be >= 1")
    if sequential_chunks > 1 and dataset_name != "dsec":
        raise ValueError(
            "sequential_chunks > 1 is supported only for DSEC raw-event inputs"
        )
    if internal_updates % sequential_chunks != 0:
        raise ValueError(
            "internal_updates must divide evenly by sequential_chunks"
        )
    seed_everything(seed)
    resolved_suite = infer_model_suite(architecture) if suite == "auto" else suite
    loss_profile = loss_profile_for_suite(resolved_suite)
    train_pool, validation_dataset, temporal_protocol, protocol_fingerprint = _prepare_datasets(
        root,
        seed=seed,
        output_size=output_size,
        validation_fraction=validation_fraction,
        input_mode=input_mode,
        manifest=manifest,
        train_samples=train_samples,
        internal_updates=internal_updates,
        stateful_stream=continuous_state,
        dataset_name=dataset_name,
    )
    collate = dsec_temporal_collate if dataset_name == "dsec" else temporal_collate
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
    class_count = int(train_pool.class_count)
    class_names = tuple(str(name) for name in train_pool.class_names)
    protocol_version = str(train_pool.protocol_version)
    model = build_experiment_model(
        architecture,
        class_count=class_count,
        input_channels=train_pool.input_channels,
        suite=resolved_suite,
        internal_updates=internal_updates,
    ).to(resolved_device)
    amp_enabled = bool(amp and resolved_device.type == "cuda")
    scaler = torch.cuda.amp.GradScaler(enabled=amp_enabled)
    output_dir.mkdir(parents=True, exist_ok=True)
    is_final_run = resolved_suite == "final"
    if checkpoint_every < 1:
        raise ValueError("checkpoint_every must be >= 1")
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
            {"params": base_neuron_parameters, "lr": learning_rate, "weight_decay": 0.0}
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
    last_validation_metrics: dict[str, object] | None = None
    last_validation_spike_rate = 0.0
    last_validation_layer_rates: dict[str, float] = {}
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
                "class_names": class_names,
                "dataset": dataset_name,
                "seed": seed,
                "epoch": epoch_number,
                "epochs": epochs,
                "held_out_split": "sequence_train_holdout",
                "input_channels": train_pool.input_channels,
                "input_representation": input_mode,
                "temporal_protocol_version": protocol_version,
                "temporal_protocol": temporal_protocol,
                "protocol_fingerprint": protocol_fingerprint,
                "output_size": list(output_size) if output_size is not None else None,
                "training_phase": training_phase_name,
                "amp": amp_enabled,
                "sequential_chunks": sequential_chunks,
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
        if checkpoint.get("temporal_protocol_version") != protocol_version:
            raise ValueError(
                "checkpoint uses the obsolete repeated-static/legacy data protocol; "
                "start a new timestamp-stream run instead of resuming it"
            )
        checkpoint_protocol = checkpoint.get("temporal_protocol")
        normalized_checkpoint_protocol = (
            dict(checkpoint_protocol) if isinstance(checkpoint_protocol, dict) else None
        )
        if (
            normalized_checkpoint_protocol is not None
            and "internal_updates" not in normalized_checkpoint_protocol
        ):
            integration_us = int(
                normalized_checkpoint_protocol.get("integration_window_us", 0)
            )
            event_clock_us = int(normalized_checkpoint_protocol.get("event_clock_us", 0))
            if event_clock_us > 0 and integration_us % event_clock_us == 0:
                normalized_checkpoint_protocol["internal_updates"] = (
                    integration_us // event_clock_us
                )
        protocol_matches = (
            checkpoint.get("protocol_fingerprint") == protocol_fingerprint
            or normalized_checkpoint_protocol == temporal_protocol
        )
        if not protocol_matches:
            raise ValueError(
                "checkpoint temporal/data protocol does not match this run; "
                "sequence split, manifest, input mode, or event-clock contract changed"
            )
        if int(checkpoint.get("input_channels", -1)) != train_pool.input_channels:
            raise ValueError(
                "checkpoint input channel count does not match temporal representation"
            )
        model.load_state_dict(checkpoint["model_state_dict"])

        optimizer_state = checkpoint.get("optimizer_state_dict")
        scheduler_state = checkpoint.get("scheduler_state_dict")
        scaler_state = checkpoint.get("scaler_state_dict")
        if optimizer_state is not None:
            optimizer.load_state_dict(optimizer_state)
        if scheduler_state is not None:
            scheduler.load_state_dict(scheduler_state)
        resumed_group_rates = apply_resume_learning_rate(
            optimizer,
            scheduler,
            learning_rate=learning_rate,
        )
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
        fallback_best_epoch = loaded_epoch if checkpoint_miou > float("-inf") else 0
        best_epoch = int(checkpoint.get("best_epoch", fallback_best_epoch))
        best_metrics = checkpoint.get("best_validation_metrics")
        if best_metrics is None and checkpoint.get("is_best"):
            best_metrics = checkpoint_metrics
        best_mean_spike_rate = float(
            checkpoint.get(
                "best_validation_mean_spike_rate",
                checkpoint.get("validation_mean_spike_rate", 0.0)
                if checkpoint.get("is_best")
                else 0.0,
            )
            or 0.0
        )
        best_layer_spike_rates = dict(
            checkpoint.get(
                "best_validation_layer_spike_rates",
                checkpoint.get("validation_layer_spike_rates", {})
                if checkpoint.get("is_best")
                else {},
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
            f"completed_epoch={loaded_epoch} next_epoch={start_epoch} target_epoch={epochs} | "
            f"CLI LR applied: {', '.join(f'{rate:.2e}' for rate in resumed_group_rates)}",
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
        f"Training {architecture} | dataset={dataset_name} | {resolved_device} | {precision} | "
        f"epochs={epochs} batch={batch_size} accumulate={accumulate_steps} "
        f"effective_batch={batch_size * accumulate_steps} "
        f"mode={input_mode} internal_updates={internal_updates} "
        f"sequential_chunks={sequential_chunks} "
        f"chunk_updates={internal_updates // sequential_chunks} "
        f"{'continuous_state' if continuous_state else 'stateless_records'} size={size_label} | "
        f"train_pool={len(train_pool)} epoch_train={len(example_epoch_train)} "
        f"val={len(validation_dataset)} | "
        f"params={model.parameter_count():,}",
        flush=True,
    )
    if dataset_name == "dsec":
        validation_sequences = ",".join(
            sorted({record.sequence_id for record in validation_dataset.records})
        )
        actual_validation_fraction = len(validation_dataset) / (
            len(train_pool) + len(validation_dataset)
        )
        print(
            f"DSEC fixed validation | sequences={validation_sequences} | "
            f"records={len(validation_dataset)} "
            f"({actual_validation_fraction:.1%} of complete training data)",
            flush=True,
        )
    print(
        "Median-frequency class weights | "
        + ", ".join(
            f"{class_name}={weight:.3f}"
            for class_name, weight in zip(class_names, class_weights.tolist())
        ),
        flush=True,
    )
    print(
        "Batch Dice-loss order | " + ", ".join(class_names),
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
            shuffle=False,
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
            # Keep the initial PLIF representation unconstrained for the first
            # 12.5% of a run, then ramp homeostasis to full strength by 50%.
            # Fractions preserve the same schedule when --epochs changes.
            homeostasis_start_fraction = 0.2
            homeostasis_full_fraction = 0.6
            epoch_fraction = epoch / float(epochs)

            if epoch_fraction <= homeostasis_start_fraction:
                homeostasis_scale = 0.0
            else:
                homeostasis_scale = min(
                    1.0,
                    (epoch_fraction - homeostasis_start_fraction)
                    / (homeostasis_full_fraction - homeostasis_start_fraction),
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
        running_dice_losses = torch.zeros(class_count, dtype=torch.float64)
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
            if not continuous_state or epoch_train_dataset.is_stream_start(batch_index - 1):
                model.reset()
            chunks = split_temporal_chunks(sequence, sequential_chunks)
            batch_loss = 0.0
            detached_dice_losses = torch.zeros(class_count, dtype=torch.float64)
            output_spike_rate = 0.0
            for chunk in chunks:
                with torch.cuda.amp.autocast(enabled=amp_enabled, dtype=torch.float16):
                    outputs = model(chunk)
                    chunk_loss, chunk_dice_losses, chunk_spike_rate = _training_objective(
                        outputs,
                        target,
                        class_weights=class_weights,
                        class_count=class_count,
                        loss_profile=loss_profile,
                        is_final_run=is_final_run,
                        training_phase=training_phase,
                    )
                if not torch.isfinite(chunk_loss):
                    raise RuntimeError(
                        f"non-finite loss for {architecture} at epoch {epoch}"
                    )
                # Average over temporal chunks and accumulated records. Backward
                # immediately so this chunk's large activation graph can be freed
                # before the next chronological chunk is evaluated.
                scaled_loss = chunk_loss / float(
                    accumulate_steps * sequential_chunks
                )
                scaler.scale(scaled_loss).backward()
                batch_loss += float(chunk_loss.detach()) / sequential_chunks
                detached_dice_losses += (
                    chunk_dice_losses.detach().cpu().double() / sequential_chunks
                )
                output_spike_rate += float(chunk_spike_rate) / sequential_chunks

                # Preserve numeric membrane/homeostasis values but truncate their
                # autograd history at every chunk boundary (sequential TBPTT).
                detach_state = getattr(model, "detach_state", None)
                if callable(detach_state):
                    detach_state()
                del outputs, chunk_loss, chunk_dice_losses, chunk_spike_rate, scaled_loss
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
            running_loss += batch_loss
            running_dice_losses += detached_dice_losses.double()
            progress.set_postfix(
                loss=f"{batch_loss:.4f}",
                avg=f"{running_loss / batch_index:.4f}",
                lr=f"{optimizer.param_groups[0]['lr']:.2e}",
                spike=f"{output_spike_rate:.4f}",
                dice_loss="/".join(
                    f"{value:.2f}" for value in detached_dice_losses.tolist()
                ),
                phase=training_phase,
                refresh=False,
            )


            del chunks, gradient_norm, sequence, target
        scheduler.step()
        mean_epoch_loss = running_loss / max(1, len(train_loader))
        mean_epoch_dice_losses = running_dice_losses / max(1, len(train_loader))
        print(
            f"Epoch {epoch:02d}/{epochs:02d} complete | "
            f"loss={mean_epoch_loss:.4f} | phase={training_phase} | "
            f"homeostasis={homeostasis_scale:.2f} | "
            "dice_loss="
            + ", ".join(
                f"{class_name}={value:.3f}"
                for class_name, value in zip(
                    class_names, mean_epoch_dice_losses.tolist()
                )
            ),
            flush=True,
        )


        if is_final_run:
            validation_metrics, validation_spike_rate, validation_layer_rates = evaluate_model(
                model,
                validation_loader,
                device=resolved_device,
                stateful_stream=continuous_state,
            )
            last_validation_metrics = validation_metrics
            last_validation_spike_rate = validation_spike_rate
            last_validation_layer_rates = validation_layer_rates
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
        # The final epoch was evaluated immediately after its optimizer step.
        # Reuse that result instead of running an identical full validation pass.
        if last_validation_metrics is None:
            raise RuntimeError("final epoch validation metrics were not recorded")
        save_training_checkpoint(
            last_checkpoint_path,
            epoch_number=epochs,
            validation_metrics=last_validation_metrics,
            validation_spike_rate=last_validation_spike_rate,
            validation_layer_rates=last_validation_layer_rates,
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
            model,
            validation_loader,
            device=resolved_device,
            stateful_stream=continuous_state,
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
                "class_names": class_names,
                "dataset": dataset_name,
                "seed": seed,
                "held_out_split": "sequence_train_holdout",
                "input_channels": train_pool.input_channels,
                "input_representation": input_mode,
                "temporal_protocol_version": protocol_version,
                "temporal_protocol": temporal_protocol,
                "protocol_fingerprint": protocol_fingerprint,
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
    root = (
        resolve_dsec_root(args.root)
        if args.dataset == "dsec"
        else resolve_ddd17_root(args.root)
    )
    presets = architecture_presets(args.suite)
    results = [
        train_architecture(
            root,
            architecture=name,
            suite=args.suite,
            seed=args.seed,
            epochs=args.epochs,
            batch_size=args.batch_size,
            input_mode=args.input_mode,
            manifest=args.manifest,
            train_samples=args.train_samples,
            validation_fraction=args.validation_fraction,
            learning_rate=args.learning_rate,
            output_dir=args.output_dir / "checkpoints",
            output_size=_resolve_output_size(args.height, args.width),
            device=args.device,
            checkpoint_every=args.checkpoint_every,
            amp=args.amp,
            accumulate_steps=args.accumulate_steps,
            internal_updates=args.internal_updates,
            sequential_chunks=args.sequential_chunks,
            continuous_state=args.continuous_state,
            dataset_name=args.dataset,
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
            "input_mode": args.input_mode,
            "dataset": args.dataset,
            "internal_updates": args.internal_updates,
            "manifest": str(args.manifest) if args.manifest is not None else None,
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
        "--dataset",
        choices=("ddd17", "dsec"),
        default="ddd17",
        help="dataset contract to use (DSEC consumes raw HDF5 events)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help=(
            f"dataset root (defaults: DDD17={DEFAULT_DDD17_ROOT}; "
            f"DSEC={DEFAULT_DSEC_ROOT})"
        ),
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument(
        "--input-mode",
        choices=(*INPUT_MODES, DSEC_INPUT_MODE),
        default="timestamp-events",
        help="DDD17 timestamp statistics or rectified raw DSEC polarity events",
    )
    parser.add_argument(
        "--internal-updates",
        type=int,
        default=DEFAULT_INTERNAL_UPDATES,
        help=(
            "PLIF clock updates inside each 50 ms record (default: 10); "
            "must divide 50,000 microseconds exactly"
        ),
    )
    parser.add_argument(
        "--no-continuous-state",
        action="store_false",
        dest="continuous_state",
        help=(
            "reset all PLIF state before every 50 ms record; useful only for "
            "the independent-record ablation"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="DDD17 temporal manifest; DSEC instead uses per-sequence timestamp files",
    )
    parser.add_argument(
        "--train-samples", type=float, default=2048.0,
        help=(
            "per-epoch contiguous stream: "
            "0=all, 0<x<=1=fraction, x>1=absolute count"
        ),
    )
    parser.add_argument(
        "--validation-fraction",
        type=float,
        default=0.10,
        help="fraction of training sequences reserved for validation in the final suite",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-3,
        help="base LR; overrides checkpoint parameter-group LRs when resuming",
    )
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
    parser.add_argument(
        "--sequential-chunks",
        type=int,
        default=1,
        help=(
            "number of equal chronological DSEC chunks used for truncated BPTT; "
            "1 preserves the original full-record forward/backward"
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument(
        "--dataset", choices=("ddd17", "dsec"), default="ddd17"
    )
    inspect_parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="dataset root; defaults according to --dataset",
    )
    inspect_parser.add_argument("--manifest", type=Path, default=None)

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
        default="EventSpikeSeg140k",
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
    root = None
    if args.command != "promote":
        root = (
            resolve_dsec_root(args.root)
            if args.dataset == "dsec"
            else resolve_ddd17_root(args.root)
        )
    if args.command == "inspect":
        inspection = (
            inspect_dsec(root)
            if args.dataset == "dsec"
            else inspect_ddd17(root, manifest=args.manifest)
        )
        print(json.dumps(inspection.to_dict(), indent=2))
    elif args.command == "single":
        train_architecture(
            root,
            architecture=args.architecture,
            suite=args.suite,
            seed=args.seed,
            epochs=args.epochs,
            batch_size=args.batch_size,
            input_mode=args.input_mode,
            manifest=args.manifest,
            train_samples=args.train_samples,
            validation_fraction=args.validation_fraction,
            learning_rate=args.learning_rate,
            output_dir=args.checkpoint_dir,
            output_size=_resolve_output_size(args.height, args.width),
            device=args.device,
            checkpoint_every=args.checkpoint_every,
            amp=args.amp,
            accumulate_steps=args.accumulate_steps,
            internal_updates=args.internal_updates,
            sequential_chunks=args.sequential_chunks,
            continuous_state=args.continuous_state,
            dataset_name=args.dataset,
            load=args.load,
        )
    elif args.command == "benchmark":
        print(json.dumps(benchmark_architectures(args), indent=2))
    else:
        print(json.dumps(promote_winner(args.summary, args.destination), indent=2))


if __name__ == "__main__":
    main()
