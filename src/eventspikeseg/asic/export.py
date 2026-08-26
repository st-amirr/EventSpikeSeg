"""Deterministic EventSpikeSeg140k checkpoint-to-ASIC artifact exporter."""

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
from .contracts import (
    BIN_TAG_WIDTH,
    BIN_US,
    DEFAULT_PREDICTION_BINS,
    MANUFACTURABLE_TARGET_GATE,
    OPEN_PPA_TARGET,
    state_capacity_contract,
)
from .fixed_point import ASIC_FORMATS
from .topology import (
    EVENTSPIKESEG140K_ACTORS,
    EVENTSPIKESEG140K_CURRENT_READOUT,
    eventspikeseg140k_graph_contract,
    validate_eventspikeseg140k_topology,
)

# Compatibility name retained for existing exporters/tests.  This tuple is a
# deterministic topological/export order only; it is NOT a runtime linear pipeline.
EVENTSPIKESEG140K_INFERENCE_STAGES = EVENTSPIKESEG140K_ACTORS


_SPATIAL_TIERS = {
    **{name: "native" for name in EVENTSPIKESEG140K_INFERENCE_STAGES},
    **{
        name: "half"
        for name in (
            "stem",
            "enc1.standard",
            "enc1_extra.depthwise",
            "enc1_extra.pointwise",
        )
    },
    **{
        name: "quarter"
        for name in (
            "down2.standard",
            "enc2.depthwise",
            "enc2.pointwise",
            "enc2_extra.depthwise",
            "enc2_extra.pointwise",
            "decoder2_fuse",
            "project2",
        )
    },
    **{
        name: "eighth"
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
    "stem": "native",
    "down2.standard": "half",
    "down3.depthwise": "quarter",
}

_BASE_SKELETON_STAGES = {
    "stem",
    "enc1.standard",
    "down2.standard",
    "enc2.depthwise",
    "enc2.pointwise",
    "down3.depthwise",
    "down3.pointwise",
    "enc3.depthwise",
    "enc3.pointwise",
    "project3",
    "project2",
}


def _json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _folded_weights(stage: SpikingStage) -> Tensor:
    weights = stage.conv.weight.detach().cpu().float().clone()
    transform = stage.transform.op
    if isinstance(transform, ChannelAffine):
        weights *= transform.gain.detach().cpu().float().view(-1, 1, 1, 1)
    elif not isinstance(transform, nn.Identity):
        raise ValueError("ASIC export supports only identity or foldable ChannelAffine")
    return weights


def _stage_parameters(stage: SpikingStage) -> dict[str, object]:
    neuron = stage.neuron
    if not isinstance(neuron, ParametricLIF):
        raise ValueError("EventSpikeSeg140k ASIC export requires PLIF at every stage")
    beta_q = ASIC_FORMATS["beta"].quantize(neuron.beta.detach().cpu())
    threshold = neuron.learned_threshold
    if threshold is None:
        threshold = torch.full((stage.conv.out_channels,), neuron.config.threshold)
    threshold_q = ASIC_FORMATS["threshold"].quantize(threshold.detach().cpu())
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
            else ASIC_FORMATS["adaptation"].quantize(inhibition_strength.detach().cpu()).tolist()
        ),
        "threshold_adaptation_enabled": neuron.config.threshold_adaptation_enabled,
        "adaptation_kind": neuron.config.adaptation_kind,
        "threshold_adaptation_strength_q": (
            None
            if adaptation_strength is None
            else ASIC_FORMATS["adaptation"].quantize(
                adaptation_strength.detach().cpu()
            ).tolist()
        ),
        "adaptation_duration_q": (
            None
            if adaptation_duration is None
            else ASIC_FORMATS["adaptation"].quantize(
                adaptation_duration.detach().cpu()
            ).tolist()
        ),
    }


def _spatial_shapes(height: int, width: int) -> dict[str, list[int]]:
    return {
        "native": [height, width],
        "half": [(height + 1) // 2, (width + 1) // 2],
        "quarter": [(height + 3) // 4, (width + 3) // 4],
        "eighth": [(height + 7) // 8, (width + 7) // 8],
    }


def _validate_model(model: nn.Module) -> EventSpikeSeg140k:
    if type(model) is not EventSpikeSeg140k:
        raise TypeError("ASIC export is frozen to EventSpikeSeg140k; XL is not accepted")
    if model.class_count != 11 or model.source_input_channels != 2:
        raise ValueError("ASIC target requires DSEC EventSpikeSeg140k with 2 inputs and 11 classes")
    named = dict(model.named_modules())
    missing = [name for name in EVENTSPIKESEG140K_INFERENCE_STAGES if name not in named]
    if missing:
        raise ValueError(f"140k inference graph drifted; missing stages: {missing}")
    if not all(
        isinstance(named[name], SpikingStage)
        for name in EVENTSPIKESEG140K_INFERENCE_STAGES
    ):
        raise TypeError("all frozen inference entries must be SpikingStage modules")
    if not isinstance(named.get(EVENTSPIKESEG140K_CURRENT_READOUT), nn.Conv2d):
        raise TypeError("the final inference readout must be a 1x1 Conv2d synapse")
    return model


def export_model(
    model: nn.Module,
    output_dir: str | Path,
    *,
    height: int = 440,
    width: int = 640,
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
        weight_q = ASIC_FORMATS["weight"].quantize(folded).to(torch.int8).numpy()
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

    readout = named[EVENTSPIKESEG140K_CURRENT_READOUT]
    assert isinstance(readout, nn.Conv2d)
    readout_q = ASIC_FORMATS["weight"].quantize(
        readout.weight.detach().cpu().float()
    ).to(torch.int8).numpy()
    readout_id = len(layers)
    readout_rom_name = f"{readout_id:02d}_head_synapse.mem"
    (weights_dir / readout_rom_name).write_text(
        "".join(f"{int(value) & 0xFF:02x}\n" for value in readout_q.reshape(-1)),
        encoding="ascii",
    )
    arrays[EVENTSPIKESEG140K_CURRENT_READOUT] = readout_q
    readout_parameters = sum(parameter.numel() for parameter in readout.parameters())
    executed_parameters += readout_parameters
    convolution_weights += readout.weight.numel()
    layers.append(
        {
            "id": readout_id,
            "name": EVENTSPIKESEG140K_CURRENT_READOUT,
            "actor": "temporal_class_current_readout",
            "kind": "stateless_temporal_current_accumulator",
            "spatial_tier": "native",
            "input_hw": shapes["native"],
            "output_hw": shapes["native"],
            "in_channels": readout.in_channels,
            "out_channels": readout.out_channels,
            "logical_membrane_states": 0,
            "kernel": list(readout.kernel_size),
            "stride": list(readout.stride),
            "padding": list(readout.padding),
            "dilation": list(readout.dilation),
            "groups": readout.groups,
            "weight_count": readout.weight.numel(),
            "parameter_count": readout_parameters,
            "weight_rom": f"weights/{readout_rom_name}",
            "normalization": "none",
        }
    )

    registered_parameters = sum(parameter.numel() for parameter in model.parameters())
    if len(layers) != 26 or convolution_weights != 143_904:
        raise ValueError(
            "140k inference graph contract changed: expected 25 PLIF stages plus readout "
            "and 143904 synaptic weights"
        )
    if registered_parameters != 150_245 or executed_parameters != 149_503:
        raise ValueError(
            "140k parameter contract changed: expected registered/executed 150245/149503, "
            f"got {registered_parameters}/{executed_parameters}"
        )
    total_membrane_states = sum(
        int(layer["logical_membrane_states"]) for layer in layers
    )
    if total_membrane_states != 30_976_000:
        raise ValueError(
            "native-resolution state contract changed: expected 30976000 membrane states, "
            f"got {total_membrane_states}"
        )
    base_membrane_states = sum(
        int(layer["logical_membrane_states"])
        for layer in layers
        if layer.get("origin") == "base_encoder_decoder_skeleton"
    )

    np.savez_compressed(destination / "quantized_weights.npz", **arrays)
    class_mapping = {str(index): name for index, name in enumerate(DSEC_CLASS_NAMES)}
    _json_write(destination / "class_mapping.json", class_mapping)
    graph_operations = [
        {"after": "stem", "operation": "learned_stride2_downsample", "target": "half"},
        {"after": "project3", "operation": "nearest_event_fanout", "target": "quarter"},
        {
            "before": "decoder2_fuse",
            "operation": "channel_concat_remap",
            "sources": ["project3_upsampled", "enc2"],
        },
        {"after": "project2", "operation": "nearest_event_fanout", "target": "half"},
        {
            "after": "project2_upsampled",
            "operation": "event_multiplicity_sum",
            "with": "enc1",
            "output_values": [0, 1, 2],
        },
        {"after": "semantic_half", "operation": "nearest_event_fanout", "target": "native"},
        {
            "before": "final_fuse.standard",
            "operation": "channel_concat_remap",
            "sources": ["semantic_half_upsampled", "detail1"],
        },
        {"after": "head.synapse", "operation": "temporal_current_accumulate_and_argmax"},
    ]
    validate_eventspikeseg140k_topology()
    graph_contract = eventspikeseg140k_graph_contract()

    manifest: dict[str, Any] = {
        "schema_version": "2.1.0",
        "model": "EventSpikeSeg140k",
        "dataset": "DSEC-Semantic",
        "class_count": 11,
        "input_channels": 2,
        "input_event": ["timestamp_us", "polarity", "y", "x"],
        "input_size": [height, width],
        "timing_model": "autonomous_actor_events_with_ordered_5ms_completion_tokens",
        "timing_contract": {
            "bin_us": BIN_US,
            "prediction_bins_default": DEFAULT_PREDICTION_BINS,
            "prediction_period_us_default": BIN_US * DEFAULT_PREDICTION_BINS,
            "schedule": "autonomous_static_actor_graph",
            "epoch_boundary": "ordered_completion_token",
            "global_actor_scheduler": False,
            "commit_rule": "one_PLIF_update_per_touched_destination_after_completion",
            "per_neuron_timestamp_required": False,
            "per_neuron_last_bin_tag_required": True,
            "last_bin_tag_width_bits": BIN_TAG_WIDTH,
        },
        "spatial_shapes": shapes,
        "registered_parameters": registered_parameters,
        "executed_inference_parameters": executed_parameters,
        "executed_convolution_weights": convolution_weights,
        "inference_PLIF_populations": len(EVENTSPIKESEG140K_INFERENCE_STAGES),
        "logical_membrane_states": total_membrane_states,
        "base_skeleton_membrane_states": base_membrane_states,
        "canonical_addition_membrane_states": total_membrane_states - base_membrane_states,
        "deployment_excludes": [
            "refine2", "aux_head", "boundary_head", "surrogate_gradient", "XL_modules"
        ],
        "hardware_topology": {
            "layer_actors": "25_dedicated_PLIF_actors_plus_final_current_readout",
            "graph_kind": "static_directed_acyclic_actor_graph",
            "linear_pipeline": False,
            "interconnect": "compile_time_dedicated_fanout_skip_merge_paths",
            "completion_join_rule": "wait_for_all_required_upstream_tokens_of_same_5ms_bin",
            "cross_layer_compute_sharing": False,
            "partial_reconfiguration": False,
            "event_flow": "ready_valid_spikes_plus_ordered_completion_tokens",
            "kernel_mapping": "parallel_presynaptic_taps_to_one_canonical_destination_state",
            "state_ownership": "actor_local_direct_indexed_SRAM",
            "state_record_timestamp_field": False,
            "state_record_last_bin_tag_bits": BIN_TAG_WIDTH,
            "state_memory": "characterized_actor_local_SRAM_macro_required",
            "weight_memory": "actor_local_mask_ROM_or_compiled_ROM",
            "runtime_layer_reconfiguration": False,
        },
        "open_PPA_target": OPEN_PPA_TARGET,
        "manufacturable_target_gate": MANUFACTURABLE_TARGET_GATE,
        "state_capacity": state_capacity_contract(),
        "quantization": {name: fmt.to_dict() for name, fmt in ASIC_FORMATS.items()},
        # Compatibility/export ordering only. Runtime connectivity is the DAG below.
        "layer_order": [
            *EVENTSPIKESEG140K_INFERENCE_STAGES,
            EVENTSPIKESEG140K_CURRENT_READOUT,
        ],
        "layer_order_semantics": "deterministic_topological_export_order_not_runtime_chain",
        "layers": layers,
        "graph_operations": graph_operations,
        "graph": graph_contract,
        "graph_edges": graph_contract["edges"],
        "class_mapping_file": "class_mapping.json",
        "checkpoint": checkpoint_metadata or {},
    }
    # JSON is valid YAML 1.2; emitting this canonical subset avoids a runtime YAML
    # dependency while preserving the requested model_spec.yaml artifact.
    _json_write(destination / "model_spec.yaml", manifest)
    _json_write(
        destination / "layer_graph.json",
        {
            "graph_kind": graph_contract["graph_kind"],
            "linear_pipeline": False,
            "actors": list(EVENTSPIKESEG140K_INFERENCE_STAGES),
            "nodes": graph_contract["nodes"],
            "edges": graph_contract["edges"],
            "join_nodes": graph_contract["join_nodes"],
            "operations": graph_operations,
            "layers": layers,
        },
    )
    return manifest


def export_checkpoint(
    checkpoint_path: str | Path,
    output_dir: str | Path,
    *,
    height: int = 440,
    width: int = 640,
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
