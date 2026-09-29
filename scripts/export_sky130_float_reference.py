"""Export executed EventSpikeSeg140k float parameters for analog studies.

This intentionally bypasses the Q7.16 ASIC exporter. Arrays are float32 values
loaded from the saved checkpoint, with channel-affine gains folded only into the
effective convolution tensor used by the inference stage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES, _validate_model
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.model_components import ChannelAffine, SpikingStage


def as_numpy(tensor: torch.Tensor) -> np.ndarray:
    return tensor.detach().cpu().float().contiguous().numpy().copy()


def stats(array: np.ndarray) -> dict[str, object]:
    x = array.astype(np.float64, copy=False)
    result: dict[str, object] = {
        "count": int(x.size),
        "min": float(x.min()) if x.size else 0.0,
        "max": float(x.max()) if x.size else 0.0,
        "mean": float(x.mean()) if x.size else 0.0,
        "std": float(x.std()) if x.size else 0.0,
        "absmax": float(np.abs(x).max()) if x.size else 0.0,
        "zero_fraction": float(np.count_nonzero(x == 0) / x.size) if x.size else 0.0,
        "abs_le_1e-4_fraction": float(np.count_nonzero(np.abs(x) <= 1e-4) / x.size) if x.size else 0.0,
        "abs_le_1e-3_fraction": float(np.count_nonzero(np.abs(x) <= 1e-3) / x.size) if x.size else 0.0,
    }
    if x.size:
        result["abs_percentiles"] = {
            str(q): float(np.percentile(np.abs(x), q))
            for q in (0.1, 1, 10, 25, 50, 75, 90, 99, 99.9)
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checkpoint_path = args.checkpoint.resolve()
    output_dir = args.output.resolve()
    raw = checkpoint_path.read_bytes()
    checkpoint_sha256 = hashlib.sha256(raw).hexdigest()
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint.get("architecture") != "EventSpikeSeg140k":
        raise ValueError("float analog reference exporter requires EventSpikeSeg140k")
    if int(checkpoint.get("input_channels", -1)) != 2:
        raise ValueError("checkpoint must use the two-channel raw-event ingress")
    protocol = checkpoint.get("temporal_protocol")
    if not isinstance(protocol, dict):
        raise ValueError("checkpoint is missing its temporal protocol")
    updates = int(protocol.get("internal_updates", -1))
    if updates < 1:
        raise ValueError("checkpoint has invalid internal_updates")

    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=updates)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.set_mechanism_scale(float(checkpoint.get("mechanism_scale", 1.0)))
    for module in model.modules():
        toggle = getattr(module, "set_asic_qat_enabled", None)
        if callable(toggle):
            toggle(False)
    model.eval()
    model, profile = _validate_model(model)
    named = dict(model.named_modules())

    arrays: dict[str, np.ndarray] = {}
    layer_reports: list[dict[str, object]] = []
    for layer_name in EVENTSPIKESEG140K_INFERENCE_STAGES:
        stage = named[layer_name]
        if not isinstance(stage, SpikingStage):
            raise TypeError(f"{layer_name} is not a SpikingStage")
        conv = stage.conv
        transform = stage.transform.op
        weight = as_numpy(conv.weight)
        if isinstance(transform, ChannelAffine):
            gain = as_numpy(transform.gain)
        elif isinstance(transform, nn.Identity):
            gain = np.ones((conv.out_channels,), dtype=np.float32)
        else:
            raise TypeError(f"unsupported current transform for {layer_name}: {type(transform).__name__}")
        folded = weight * gain.reshape(-1, 1, 1, 1)
        safe = layer_name.replace(".", "__")
        arrays[f"weight__{safe}"] = folded.astype(np.float32, copy=False)
        arrays[f"affine_gain__{safe}"] = gain.astype(np.float32, copy=False)
        arrays[f"beta__{safe}"] = as_numpy(stage.neuron.beta)
        threshold = stage.neuron.learned_threshold
        if threshold is None:
            threshold = torch.full((conv.out_channels,), stage.neuron.config.threshold)
        arrays[f"threshold__{safe}"] = as_numpy(threshold)
        inhibition = stage.neuron.inhibition_strength
        if inhibition is not None:
            arrays[f"inhibition_strength__{safe}"] = as_numpy(inhibition * stage.neuron.inhibition_scale)
        adaptation = stage.neuron.threshold_adaptation_strength
        if adaptation is not None:
            arrays[f"threshold_adaptation_strength__{safe}"] = as_numpy(
                adaptation * stage.neuron.threshold_adaptation_scale
            )
        duration = stage.neuron.adaptation_duration
        if duration is not None:
            arrays[f"adaptation_duration__{safe}"] = as_numpy(duration)
        layer_reports.append({
            "name": layer_name,
            "weight": stats(folded),
            "raw_conv_weight": stats(weight),
            "affine_gain": stats(gain),
            "affine_offset": None,
            "beta": stats(arrays[f"beta__{safe}"]),
            "threshold": stats(arrays[f"threshold__{safe}"]),
            "weight_shape_oihw": list(folded.shape),
            "conv_groups": int(conv.groups),
            "conv_stride": list(conv.stride),
            "conv_padding": list(conv.padding),
            "conv_dilation": list(conv.dilation),
            "per_output_channel_weight": [stats(row) for row in folded.reshape(conv.out_channels, -1)],
            "normalization": "ChannelAffine gain folded into synaptic weight; no additive offset",
            "inhibition_kind": stage.neuron.config.inhibition_kind,
            "inhibition_enabled": bool(stage.neuron.config.inhibition_enabled),
            "threshold_adaptation_kind": stage.neuron.config.adaptation_kind,
            "threshold_adaptation_enabled": bool(stage.neuron.config.threshold_adaptation_enabled),
        })

    readout = named[str(profile["readout"])]
    if not isinstance(readout, nn.Conv2d):
        raise TypeError("inference readout is not Conv2d")
    arrays["weight__head_synapse"] = as_numpy(readout.weight)
    if readout.bias is not None:
        arrays["bias__head_synapse"] = as_numpy(readout.bias)

    output_dir.mkdir(parents=True, exist_ok=True)
    npz_path = output_dir / "eventspikeseg140k_float_parameters.npz"
    np.savez_compressed(npz_path, **arrays)
    metadata = {
        "format": "float32 inference parameter arrays; no Q7.16 conversion or fake quantization",
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": checkpoint_sha256,
        "checkpoint_bytes": len(raw),
        "architecture": checkpoint["architecture"],
        "dataset": checkpoint.get("dataset"),
        "seed": checkpoint.get("seed"),
        "epoch": checkpoint.get("epoch"),
        "epochs": checkpoint.get("epochs"),
        "best_epoch": checkpoint.get("best_epoch"),
        "is_best": checkpoint.get("is_best"),
        "best_mean_iou": checkpoint.get("best_mean_iou"),
        "model_suite": checkpoint.get("model_suite"),
        "training_phase": checkpoint.get("training_phase"),
        "training_strategy_version": checkpoint.get("training_strategy_version"),
        "asic_qat_enabled_metadata": checkpoint.get("asic_qat_enabled", "absent"),
        "asic_qat_epochs_metadata": checkpoint.get("asic_qat_epochs", "absent"),
        "qat_provenance": "not required or used by analog export; checkpoint QAT metadata fields are absent, and the exported inference forward is explicitly set to float path",
        "mechanism_scale": float(checkpoint.get("mechanism_scale", 1.0)),
        "input_channels": checkpoint.get("input_channels"),
        "input_representation": checkpoint.get("input_representation"),
        "temporal_protocol": {
            key: protocol.get(key)
            for key in ("version", "input_mode", "input_channels", "integration_window_us", "internal_updates", "event_clock_us", "stateful_stream")
        },
        "inference_actor_count": len(profile["actors"]),
        "inference_actors": list(profile["actors"]),
        "inference_synaptic_weight_count": int(profile["weights"]),
        "effective_folded_weight_and_neuron_parameters": layer_reports,
        "readout_weight": stats(arrays["weight__head_synapse"]),
        "readout_weight_shape_oihw": list(arrays["weight__head_synapse"].shape),
        "parameter_archive": npz_path.name,
        "parameter_array_names": sorted(arrays),
        "purpose": "analog pulse-duration transfer and software-error reference; not a claimed analog accuracy or precision contract",
    }
    metadata_path = output_dir / "eventspikeseg140k_float_reference.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"metadata": str(metadata_path), "archive": str(npz_path),
                      "checkpoint_sha256": checkpoint_sha256,
                      "inference_actor_count": len(profile["actors"]),
                      "inference_synaptic_weight_count": int(profile["weights"]),
                      "qat_provenance": metadata["qat_provenance"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
