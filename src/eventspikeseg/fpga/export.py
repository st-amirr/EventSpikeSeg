"""Deterministic EventSpikeSeg140k checkpoint-to-RTL artifact exporter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn

from ..data import DSEC_CLASS_NAMES
from ..model import EventSpikeSeg140k
from ..model_components import ChannelAffine, ParametricLIF, SpikingStage
from .fixed_point import FPGA_FORMATS
from .target import NEXYS_VIDEO_XC7A200T, memory_budget

EVENTSPIKESEG140K_INFERENCE_STAGES = (
    "stem",
    "enc1.depthwise",
    "enc1.pointwise",
    "enc1_extra.depthwise",
    "enc1_extra.pointwise",
    "detail1.depthwise",
    "detail1.pointwise",
    "detail2.depthwise",
    "detail2.pointwise",
    "detail3.depthwise",
    "detail3.pointwise",
    "down2.depthwise",
    "down2.pointwise",
    "enc2.depthwise",
    "enc2.pointwise",
    "enc2_extra.depthwise",
    "enc2_extra.pointwise",
    "down3.depthwise",
    "down3.pointwise",
    "enc3.depthwise",
    "enc3.pointwise",
    "enc3_extra.depthwise",
    "enc3_extra.pointwise",
    "context1.depthwise",
    "context1.pointwise",
    "context2.depthwise",
    "context2.pointwise",
    "project3",
    "decoder2_extra.depthwise",
    "decoder2_extra.pointwise",
    "project2",
    "final_selector.selector",
    "final_fuse.depthwise",
    "final_fuse.pointwise",
    "decoder1_extra.depthwise",
    "decoder1_extra.pointwise",
    "head.stage",
)

_SPATIAL_TIERS = {
    **{name: "full" for name in EVENTSPIKESEG140K_INFERENCE_STAGES},
    **{
        name: "half"
        for name in (
            "down2.depthwise",
            "down2.pointwise",
            "enc2.depthwise",
            "enc2.pointwise",
            "enc2_extra.depthwise",
            "enc2_extra.pointwise",
            "decoder2_extra.depthwise",
            "decoder2_extra.pointwise",
            "project2",
        )
    },
    **{
        name: "quarter"
        for name in (
            "down3.depthwise",
            "down3.pointwise",
            "enc3.depthwise",
            "enc3.pointwise",
            "enc3_extra.depthwise",
            "enc3_extra.pointwise",
            "context1.depthwise",
            "context1.pointwise",
            "context2.depthwise",
            "context2.pointwise",
            "project3",
        )
    },
}

_INPUT_SPATIAL_TIER = {
    "down2.depthwise": "full",
    "down3.depthwise": "half",
}

_BASE_SKELETON_STAGES = {
    "stem",
    "enc1.depthwise",
    "enc1.pointwise",
    "down2.depthwise",
    "down2.pointwise",
    "enc2.depthwise",
    "enc2.pointwise",
    "down3.depthwise",
    "down3.pointwise",
    "enc3.depthwise",
    "enc3.pointwise",
    "project3",
    "project2",
    "head.stage",
}


def _json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _folded_weights(stage: SpikingStage) -> Tensor:
    weights = stage.conv.weight.detach().cpu().float().clone()
    transform = stage.transform.op
    if isinstance(transform, ChannelAffine):
        weights *= transform.gain.detach().cpu().float().view(-1, 1, 1, 1)
    elif not isinstance(transform, nn.Identity):
        raise ValueError("FPGA export supports only identity or foldable ChannelAffine")
    return weights


def _stage_parameters(stage: SpikingStage) -> dict[str, object]:
    neuron = stage.neuron
    if not isinstance(neuron, ParametricLIF):
        raise ValueError("EventSpikeSeg140k FPGA export requires PLIF at every stage")
    beta_q = FPGA_FORMATS["beta"].quantize(neuron.beta.detach().cpu())
    threshold = neuron.learned_threshold
    if threshold is None:
        threshold = torch.full((stage.conv.out_channels,), neuron.config.threshold)
    threshold_q = FPGA_FORMATS["threshold"].quantize(threshold.detach().cpu())
    inhibition_strength = neuron.inhibition_strength
    adaptation_strength = neuron.threshold_adaptation_strength
    adaptation_duration = neuron.adaptation_duration
    return {
        "beta_q": beta_q.tolist(),
        "threshold_q": threshold_q.tolist(),
        "inhibition_enabled": neuron.config.inhibition_enabled,
        "inhibition_kind": neuron.config.inhibition_kind,
        "inhibition_strength_q": (
            None
            if inhibition_strength is None
            else FPGA_FORMATS["adaptation"].quantize(inhibition_strength.detach().cpu()).tolist()
        ),
        "threshold_adaptation_enabled": neuron.config.threshold_adaptation_enabled,
        "adaptation_kind": neuron.config.adaptation_kind,
        "threshold_adaptation_strength_q": (
            None
            if adaptation_strength is None
            else FPGA_FORMATS["adaptation"].quantize(
                adaptation_strength.detach().cpu()
            ).tolist()
        ),
        "adaptation_duration_q": (
            None
            if adaptation_duration is None
            else FPGA_FORMATS["adaptation"].quantize(
                adaptation_duration.detach().cpu()
            ).tolist()
        ),
    }


def _spatial_shapes(height: int, width: int) -> dict[str, list[int]]:
    return {
        "full": [height, width],
        "half": [(height + 1) // 2, (width + 1) // 2],
        "quarter": [(height + 3) // 4, (width + 3) // 4],
    }


def _validate_model(model: nn.Module) -> EventSpikeSeg140k:
    if type(model) is not EventSpikeSeg140k:
        raise TypeError("FPGA export is frozen to EventSpikeSeg140k; XL is not accepted")
    if model.class_count != 11 or model.source_input_channels != 2:
        raise ValueError("FPGA target requires DSEC EventSpikeSeg140k with 2 inputs and 11 classes")
    named = dict(model.named_modules())
    missing = [name for name in EVENTSPIKESEG140K_INFERENCE_STAGES if name not in named]
    if missing:
        raise ValueError(f"140k inference graph drifted; missing stages: {missing}")
    if not all(
        isinstance(named[name], SpikingStage)
        for name in EVENTSPIKESEG140K_INFERENCE_STAGES
    ):
        raise TypeError("all frozen inference entries must be SpikingStage modules")
    return model


def export_model(
    model: nn.Module,
    output_dir: str | Path,
    *,
    height: int = 241,
    width: int = 351,
    checkpoint_metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    """Export the frozen 140k inference graph and return its manifest."""

    model = _validate_model(model)
    if height < 1 or width < 1:
        raise ValueError("spatial dimensions must be positive")
    destination = Path(output_dir)
    weights_dir = destination / "weights"
    parameters_dir = destination / "parameters"
    weights_dir.mkdir(parents=True, exist_ok=True)
    parameters_dir.mkdir(parents=True, exist_ok=True)

    named = dict(model.named_modules())
    shapes = _spatial_shapes(height, width)
    arrays: dict[str, np.ndarray] = {}
    layers: list[dict[str, object]] = []
    executed_parameters = 0
    convolution_weights = 0
    for layer_id, name in enumerate(EVENTSPIKESEG140K_INFERENCE_STAGES):
        stage = named[name]
        assert isinstance(stage, SpikingStage)
        folded = _folded_weights(stage)
        weight_q = FPGA_FORMATS["weight"].quantize(folded).to(torch.int8).numpy()
        safe_name = name.replace(".", "_")
        rom_name = f"{layer_id:02d}_{safe_name}.mem"
        rom_path = weights_dir / rom_name
        rom_path.write_text(
            "".join(f"{int(value) & 0xFF:02x}\n" for value in weight_q.reshape(-1)),
            encoding="ascii",
        )
        arrays[name] = weight_q
        parameters = _stage_parameters(stage)
        _json_write(parameters_dir / f"{layer_id:02d}_{safe_name}.json", parameters)
        tier = _SPATIAL_TIERS[name]
        input_tier = _INPUT_SPATIAL_TIER.get(name, tier)
        conv = stage.conv
        logical_state_count = conv.out_channels * shapes[tier][0] * shapes[tier][1]
        layer_parameter_count = sum(parameter.numel() for parameter in stage.parameters())
        executed_parameters += layer_parameter_count
        convolution_weights += conv.weight.numel()
        layers.append(
            {
                "id": layer_id,
                "name": name,
                "actor": f"actor_{layer_id:02d}_{safe_name}",
                "spatial_tier": tier,
                "input_hw": shapes[input_tier],
                "output_hw": shapes[tier],
                "in_channels": conv.in_channels,
                "out_channels": conv.out_channels,
                "logical_membrane_states": logical_state_count,
                "origin": (
                    "base_encoder_decoder_skeleton"
                    if name in _BASE_SKELETON_STAGES
                    else "canonical_140k_architecture_addition"
                ),
                "kernel": list(conv.kernel_size),
                "stride": list(conv.stride),
                "padding": list(conv.padding),
                "dilation": list(conv.dilation),
                "groups": conv.groups,
                "weight_count": conv.weight.numel(),
                "parameter_count": layer_parameter_count,
                "weight_rom": f"weights/{rom_name}",
                "parameter_file": f"parameters/{layer_id:02d}_{safe_name}.json",
                "normalization": "channel_affine_folded_into_weight",
            }
        )

    registered_parameters = sum(parameter.numel() for parameter in model.parameters())
    if len(layers) != 37 or convolution_weights != 127_456:
        raise ValueError(
            "140k inference graph contract changed: expected 37 stages and 127456 conv weights"
        )
    if registered_parameters != 140_589 or executed_parameters != 134_807:
        raise ValueError(
            "140k parameter contract changed: expected registered/executed 140589/134807, "
            f"got {registered_parameters}/{executed_parameters}"
        )
    total_membrane_states = sum(
        int(layer["logical_membrane_states"]) for layer in layers
    )
    if total_membrane_states != 72_843_333:
        raise ValueError(
            "140k DSEC state contract changed: expected 72843333 membrane states, "
            f"got {total_membrane_states}"
        )
    base_membrane_states = sum(
        int(layer["logical_membrane_states"])
        for layer in layers
        if layer["origin"] == "base_encoder_decoder_skeleton"
    )

    np.savez_compressed(destination / "quantized_weights.npz", **arrays)
    class_mapping = {str(index): name for index, name in enumerate(DSEC_CLASS_NAMES)}
    _json_write(destination / "class_mapping.json", class_mapping)
    graph_operations = [
        {"after": "project3", "operation": "nearest_event_fanout", "target": "half"},
        {"before": "decoder2_extra.depthwise", "operation": "binary_OR", "with": "enc2"},
        {"after": "project2", "operation": "nearest_event_fanout", "target": "full"},
        {
            "before": "final_selector.selector",
            "operation": "channel_concat_remap",
            "sources": ["project2_upsampled", "enc1", "detail3"],
        },
        {
            "after": "final_selector.selector",
            "operation": "retinotopic_binary_gate",
            "source": "concat",
        },
        {"after": "head.stage", "operation": "class_spike_counter_and_argmax"},
    ]
    manifest: dict[str, Any] = {
        "schema_version": "1.0.0",
        "model": "EventSpikeSeg140k",
        "dataset": "DSEC-Semantic",
        "class_count": 11,
        "input_channels": 2,
        "input_event": ["timestamp_us", "polarity", "y", "x"],
        "input_size": [height, width],
        "timing_model": "asynchronous_timestamp_ordered_no_input_bins",
        "spatial_shapes": shapes,
        "registered_parameters": registered_parameters,
        "executed_inference_parameters": executed_parameters,
        "executed_convolution_weights": convolution_weights,
        "inference_PLIF_populations": len(layers),
        "logical_membrane_states": total_membrane_states,
        "base_skeleton_membrane_states": base_membrane_states,
        "canonical_addition_membrane_states": total_membrane_states - base_membrane_states,
        "deployment_excludes": ["refine2", "aux_head", "surrogate_gradient", "XL_modules"],
        "hardware_topology": {
            "layer_actors": "one_dedicated_actor_per_executed_population",
            "cross_layer_compute_sharing": False,
            "partial_reconfiguration": False,
            "event_flow": "timestamp_ordered_ready_valid",
            "state_memory": "on_chip_sparse_BRAM_LUTRAM_pending_measured_fit",
            "weight_memory": "actor_local_BRAM_LUTROM",
            "external_or_onboard_DDR_allowed": False,
        },
        "target": NEXYS_VIDEO_XC7A200T.to_dict(),
        "dense_state_memory_budget": memory_budget(NEXYS_VIDEO_XC7A200T.bram_kibits),
        "quantization": {name: fmt.to_dict() for name, fmt in FPGA_FORMATS.items()},
        "layer_order": list(EVENTSPIKESEG140K_INFERENCE_STAGES),
        "layers": layers,
        "graph_operations": graph_operations,
        "class_mapping_file": "class_mapping.json",
        "checkpoint": checkpoint_metadata or {},
    }
    # JSON is valid YAML 1.2; emitting this canonical subset avoids a runtime YAML
    # dependency while preserving the requested model_spec.yaml artifact.
    _json_write(destination / "model_spec.yaml", manifest)
    _json_write(
        destination / "layer_graph.json",
        {"layers": layers, "operations": graph_operations},
    )
    return manifest


def export_checkpoint(
    checkpoint_path: str | Path,
    output_dir: str | Path,
    *,
    height: int = 241,
    width: int = 351,
) -> dict[str, object]:
    checkpoint = torch.load(Path(checkpoint_path), map_location="cpu")
    if checkpoint.get("architecture") != "EventSpikeSeg140k":
        raise ValueError("checkpoint architecture must be EventSpikeSeg140k")
    class_names = checkpoint.get("class_names", DSEC_CLASS_NAMES)
    if tuple(class_names) != tuple(DSEC_CLASS_NAMES):
        raise ValueError("checkpoint must contain the canonical 11-class DSEC mapping")
    input_channels = int(checkpoint.get("input_channels", 2))
    model = EventSpikeSeg140k(class_count=11, input_channels=input_channels)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    metadata = {
        key: checkpoint.get(key)
        for key in (
            "architecture",
            "dataset",
            "epoch",
            "seed",
            "temporal_protocol_version",
            "training_strategy_version",
        )
    }
    return export_model(
        model,
        output_dir,
        height=height,
        width=width,
        checkpoint_metadata=metadata,
    )
