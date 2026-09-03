#!/usr/bin/env python3
"""Generate the fixed EventSpikeSeg140k SystemVerilog DAG from an ASIC export."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

STREAM_FIELDS = ("valid", "ready", "payload", "completion", "bin_tag")


def _identifier(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return value if not value[:1].isdigit() else f"n_{value}"


def _packed_literal(path: Path, *, word_bits: int, expected_words: int) -> str:
    words = [line.strip() for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
    if len(words) != expected_words:
        raise ValueError(f"{path} contains {len(words)} words; expected {expected_words}")
    mask = (1 << word_bits) - 1
    values = [int(word, 16) & mask for word in words]
    digits = (word_bits + 3) // 4
    reversed_values = list(reversed(values))
    maximum_hex_digits = 1024
    words_per_chunk = max(1, maximum_hex_digits // digits)
    if len(reversed_values) <= words_per_chunk:
        packed = "".join(f"{value:0{digits}x}" for value in reversed_values)
        return f"{expected_words * word_bits}'h{packed}"
    chunks = []
    for start in range(0, len(reversed_values), words_per_chunk):
        words = reversed_values[start : start + words_per_chunk]
        packed = "".join(f"{value:0{digits}x}" for value in words)
        chunks.append(f"{len(words) * word_bits}'h{packed}")
    return "{\n      " + ",\n      ".join(chunks) + "\n    }"


def _parameter_literal(
    export_dir: Path,
    layer: dict[str, Any],
    *,
    key: str,
    rom_key: str,
    word_bits: int,
) -> str:
    count = int(layer["out_channels"])
    rom_path = layer.get(rom_key)
    if rom_path is not None:
        return _packed_literal(
            export_dir / str(rom_path), word_bits=word_bits, expected_words=count
        )
    parameters = json.loads(
        (export_dir / str(layer["parameter_file"])).read_text(encoding="utf-8")
    )
    values = parameters[key]
    if len(values) != count:
        raise ValueError(f"{layer['name']} {key} count does not match out_channels")
    mask = (1 << word_bits) - 1
    digits = (word_bits + 3) // 4
    packed = "".join(
        f"{int(value) & mask:0{digits}x}" for value in reversed(values)
    )
    return f"{count * word_bits}'h{packed}"


def _mechanism_parameters(export_dir: Path, layer: dict[str, Any]) -> dict[str, int]:
    parameter_file = layer.get("parameter_file")
    if parameter_file is None:
        return {
            "inhibition_enabled": 0,
            "adaptation_enabled": 0,
            "inhibition_strength": 0,
            "adaptation_strength": 0,
            "adaptation_duration": 0,
        }
    values = json.loads((export_dir / str(parameter_file)).read_text(encoding="utf-8"))

    def scalar(key: str) -> int:
        value = values.get(key)
        if value is None:
            return 0
        if isinstance(value, list):
            return int(value[0]) if value else 0
        return int(value)

    return {
        "inhibition_enabled": int(bool(values.get("inhibition_enabled", False))),
        "adaptation_enabled": int(
            bool(values.get("threshold_adaptation_enabled", False))
        ),
        "inhibition_strength": scalar("inhibition_strength_q"),
        "adaptation_strength": scalar("threshold_adaptation_strength_q"),
        "adaptation_duration": scalar("adaptation_duration_q"),
    }


def _declare_stream(lines: list[str], base: str) -> None:
    lines.extend(
        [
            f"  logic {base}_valid;",
            f"  logic {base}_ready;",
            f"  logic [PAYLOAD_WIDTH-1:0] {base}_payload;",
            f"  logic {base}_completion;",
            f"  logic [TAG_WIDTH-1:0] {base}_bin_tag;",
        ]
    )


def _connect_stream(lines: list[str], source: str, destination: str) -> None:
    lines.extend(
        [
            f"  assign {destination}_valid = {source}_valid;",
            f"  assign {source}_ready = {destination}_ready;",
            f"  assign {destination}_payload = {source}_payload;",
            f"  assign {destination}_completion = {source}_completion;",
            f"  assign {destination}_bin_tag = {source}_bin_tag;",
        ]
    )


def _ports(base: str, prefix: str) -> list[str]:
    return [
        f".{prefix}_valid({base}_valid)",
        f".{prefix}_ready({base}_ready)",
        f".{prefix}_payload({base}_payload)",
        f".{prefix}_completion({base}_completion)",
        f".{prefix}_bin_tag({base}_bin_tag)",
    ]


def _instance(lines: list[str], header: str, ports: list[str]) -> None:
    lines.append(f"  {header} (")
    lines.append("    " + ",\n    ".join(ports))
    lines.append("  );")


def _generate_legacy_top(
    model_spec_path: Path,
    output_path: Path,
    *,
    module_name: str = "eventspikeseg140k_dag_top",
    lane_config_path: Path | None = None,
) -> None:
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    export_dir = (model_spec_path.parent / str(spec.get("artifact_root", "."))).resolve()
    graph = spec["graph"]
    actors = list(graph["actor_topological_order"])
    if len(actors) != 25 or graph.get("linear_pipeline") is not False:
        raise ValueError("ASIC top generation requires the exact non-linear 25-actor graph")
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    if set(actors) - layers.keys():
        raise ValueError("model specification is missing one or more PLIF actor layers")
    readout_name = str(graph["current_readout"])
    if readout_name not in layers:
        raise ValueError("model specification is missing the temporal current readout")
    readout_class_count = int(layers[readout_name]["out_channels"])
    readout_class_width = max(1, (readout_class_count - 1).bit_length())
    lane_config: dict[str, Any] = {}
    lane_config_sha256: str | None = None
    if lane_config_path is not None:
        lane_bytes = lane_config_path.read_bytes()
        lane_config_sha256 = hashlib.sha256(lane_bytes).hexdigest()
        lane_document = json.loads(lane_bytes.decode("utf-8"))
        lane_config = dict(lane_document.get("actors", {}))
        unknown_actors = set(lane_config) - set(actors)
        if unknown_actors:
            raise ValueError(
                "lane configuration contains unknown actors: "
                + ", ".join(sorted(unknown_actors))
            )

    all_edges = [dict(edge) for edge in graph["edges"]]
    edges = [edge for edge in all_edges if str(edge["destination"]) != "prediction"]
    incoming: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    outgoing: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, edge in enumerate(edges):
        incoming[str(edge["destination"])].append((index, edge))
        outgoing[str(edge["source"])].append((index, edge))
    if any(len(items) > 2 for items in outgoing.values()):
        raise ValueError("generated RTL currently requires fanout degree <= 2")
    if any(len(items) > 2 for items in incoming.values()):
        raise ValueError("generated RTL currently requires join degree <= 2")

    node_kinds = {str(node["name"]): str(node["kind"]) for node in graph["nodes"]}
    join_contracts = graph["join_nodes"]
    lines = [
        "`timescale 1ns/1ps",
        "// Generated file: do not hand edit. Source is model_spec.yaml graph + ROM images.",
        "// Lane configuration SHA256: "
        + (lane_config_sha256 or "none_single_lane_reference"),
        f"module {module_name} #(",
        "  parameter integer PAYLOAD_WIDTH = 32,",
        "  parameter integer TAG_WIDTH = 24,",
        "  parameter integer RESIDUAL_MAX_EVENTS = 64,",
        "  parameter integer EDGE_FIFO_DEPTH = 2,",
        "  parameter integer USE_STATE_MACRO = 0",
        ") (",
        "  input logic clk, input logic reset,",
        "  input logic input_valid, output logic input_ready,",
        "  input logic [PAYLOAD_WIDTH-1:0] input_payload,",
        "  input logic input_completion,",
        "  input logic [TAG_WIDTH-1:0] input_bin_tag,",
        "  output logic prediction_valid, input logic prediction_ready,",
        "  output logic [9:0] prediction_x_o, output logic [8:0] prediction_y_o,",
        f"  output logic [{readout_class_width - 1}:0] prediction_class_o,",
        "  output logic frame_done_valid, input logic frame_done_ready,",
        "  output logic [TAG_WIDTH-1:0] frame_bin_tag_o,",
        "  output logic fault_o",
        ");",
        "  localparam integer EDGE_FIFO_COUNT_WIDTH = $clog2(EDGE_FIFO_DEPTH+1);",
    ]

    stream_nodes = {
        name
        for name in node_kinds
        if name not in {"input", readout_name, "prediction"}
    }
    _declare_stream(lines, "ingress")
    lines.extend(
        [
            "  logic all_memories_initialized;",
            "  assign ingress_valid = input_valid && all_memories_initialized;",
            "  assign input_ready = ingress_ready && all_memories_initialized;",
            "  assign ingress_payload = input_payload;",
            "  assign ingress_completion = input_completion;",
            "  assign ingress_bin_tag = input_bin_tag;",
        ]
    )
    for name in sorted(stream_nodes):
        _declare_stream(lines, f"n_{_identifier(name)}")
    for index, _edge in enumerate(edges):
        _declare_stream(lines, f"r_{index}")
        _declare_stream(lines, f"e_{index}")
        lines.append(
            f"  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_{index}_occupancy;"
        )
        lines.append(
            f"  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_{index}_high_watermark;"
        )

    for index, _edge in enumerate(edges):
        _instance(
            lines,
            "event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), "
            ".TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) "
            f"edge_fifo_{index}",
            [
                ".clk",
                ".reset",
                *_ports(f"r_{index}", "in"),
                *_ports(f"e_{index}", "out"),
                f".occupancy_o(edge_{index}_occupancy)",
            ],
        )
        lines.extend(
            [
                "  always_ff @(posedge clk) begin",
                f"    if (reset) edge_{index}_high_watermark <= '0;",
                f"    else if (edge_{index}_occupancy > edge_{index}_high_watermark)",
                f"      edge_{index}_high_watermark <= edge_{index}_occupancy;",
                "  end",
            ]
        )

    fault_signals: list[str] = []
    initialization_signals: list[str] = []

    def source_base(name: str) -> str:
        return "ingress" if name == "input" else f"n_{_identifier(name)}"

    for source, source_edges in outgoing.items():
        base = source_base(source)
        if len(source_edges) == 1:
            _connect_stream(lines, base, f"r_{source_edges[0][0]}")
        elif len(source_edges) == 2:
            first, second = source_edges
            ports = [".clk", ".reset", *_ports(base, "in")]
            ports.extend(_ports(f"r_{first[0]}", "out0"))
            ports.extend(_ports(f"r_{second[0]}", "out1"))
            _instance(lines, f"event_fork2 fork_{_identifier(source)}", ports)

    for actor_name in actors:
        actor_inputs = incoming[actor_name]
        if len(actor_inputs) != 1:
            raise ValueError(f"actor {actor_name} must have exactly one input")
        edge_base = f"e_{actor_inputs[0][0]}"
        output_base = f"n_{_identifier(actor_name)}"
        layer = layers[actor_name]
        weight_count = int(layer["weight_count"])
        weights = _packed_literal(
            export_dir / str(layer["weight_rom"]),
            word_bits=8,
            expected_words=weight_count,
        )
        betas = _parameter_literal(
            export_dir, layer, key="beta_q", rom_key="beta_rom", word_bits=16
        )
        thresholds = _parameter_literal(
            export_dir,
            layer,
            key="threshold_q",
            rom_key="threshold_rom",
            word_bits=16,
        )
        mechanisms = _mechanism_parameters(export_dir, layer)
        kernel_h, kernel_w = (int(value) for value in layer["kernel"])
        stride_y, stride_x = (int(value) for value in layer["stride"])
        pad_y, pad_x = (int(value) for value in layer["padding"])
        dilation_y, dilation_x = (int(value) for value in layer["dilation"])
        output_h, output_w = (int(value) for value in layer["output_hw"])
        error = f"error_actor_{_identifier(actor_name)}"
        initialized = f"initialized_actor_{_identifier(actor_name)}"
        lines.append(f"  logic {error};")
        lines.append(f"  logic {initialized};")
        fault_signals.append(error)
        initialization_signals.append(initialized)
        actor_lanes = dict(lane_config.get(actor_name, {}))
        use_parallel_banks = int(
            bool(actor_lanes.get("use_parallel_banked_state", False))
        )
        channel_lanes = int(actor_lanes.get("channel_lanes", 1))
        spatial_lanes = int(actor_lanes.get("spatial_lanes", 1))
        output_channels = int(layer["out_channels"])
        spatial_destinations = output_h * output_w
        mechanism_enabled = bool(
            mechanisms["inhibition_enabled"] or mechanisms["adaptation_enabled"]
        )
        if channel_lanes <= 0 or channel_lanes > output_channels:
            raise ValueError(f"{actor_name} has an invalid channel lane count")
        if spatial_lanes <= 0 or spatial_lanes > spatial_destinations:
            raise ValueError(f"{actor_name} has an invalid spatial lane count")
        if use_parallel_banks and mechanism_enabled and channel_lanes != 1:
            raise ValueError(
                f"{actor_name} mechanisms require all peer channels in one spatial bank"
            )
        params = [
            ".USE_STATE_MACRO(USE_STATE_MACRO)",
            f".USE_PARALLEL_BANKED_STATE({use_parallel_banks})",
            f".STATE_LANE_COUNT({channel_lanes * spatial_lanes})",
            f".STATE_CHANNEL_LANE_COUNT({channel_lanes})",
            f".STATE_SPATIAL_LANE_COUNT({spatial_lanes})",
            f".INPUT_CHANNELS({int(layer['in_channels'])})",
            f".OUTPUT_CHANNELS({int(layer['out_channels'])})",
            f".GROUPS({int(layer['groups'])})",
            f".KERNEL_WIDTH({kernel_w})", f".KERNEL_HEIGHT({kernel_h})",
            f".STRIDE_X({stride_x})", f".STRIDE_Y({stride_y})",
            f".DILATION_X({dilation_x})", f".DILATION_Y({dilation_y})",
            f".PAD_X({pad_x})", f".PAD_Y({pad_y})",
            f".OUTPUT_WIDTH({output_w})", f".OUTPUT_HEIGHT({output_h})",
            f".KERNEL_WEIGHTS({weights})", f".CHANNEL_BETAS({betas})",
            f".CHANNEL_THRESHOLDS({thresholds})",
            f".ENABLE_INHIBITION({mechanisms['inhibition_enabled']})",
            f".ENABLE_ADAPTATION({mechanisms['adaptation_enabled']})",
            f".INHIBITION_STRENGTH(16'h{mechanisms['inhibition_strength'] & 0xFFFF:04x})",
            f".ADAPTATION_STRENGTH(16'h{mechanisms['adaptation_strength'] & 0xFFFF:04x})",
            f".ADAPTATION_DURATION(16'h{mechanisms['adaptation_duration'] & 0xFFFF:04x})",
        ]
        ports = [".clk", ".reset", *_ports(edge_base, "in"), *_ports(output_base, "out")]
        ports.append(f".actor_error_o({error})")
        ports.append(f".initialization_done_o({initialized})")
        _instance(
            lines,
            "streaming_channelized_plif_actor #(\n    " + ",\n    ".join(params) +
            f"\n  ) actor_{_identifier(actor_name)}",
            ports,
        )

    for node_name, kind in node_kinds.items():
        if node_name in actors or node_name in {"input", readout_name, "prediction"}:
            continue
        node_inputs = incoming[node_name]
        output_base = f"n_{_identifier(node_name)}"
        if kind == "nearest_event_fanout_2x":
            if len(node_inputs) != 1:
                raise ValueError(f"upsample node {node_name} requires one input")
            _instance(
                lines,
                f"event_upsample2x upsample_{_identifier(node_name)}",
                [".clk", ".reset", *_ports(f"e_{node_inputs[0][0]}", "in"),
                 *_ports(output_base, "out"), ".coordinate_overflow_o()"],
            )
            continue
        if node_name not in join_contracts or len(node_inputs) != 2:
            raise ValueError(f"unsupported generated route node {node_name} ({kind})")
        prepared: list[str] = []
        contract = join_contracts[node_name]
        for input_number, (edge_index, edge) in enumerate(node_inputs):
            edge_base = f"e_{edge_index}"
            if str(contract["kind"]) == "channel_concat":
                mapped = f"m_{_identifier(node_name)}_{input_number}"
                _declare_stream(lines, mapped)
                overflow = f"error_offset_{_identifier(node_name)}_{input_number}"
                lines.append(f"  logic {overflow};")
                fault_signals.append(overflow)
                offset = int(edge.get("channel_offset", 0))
                _instance(
                    lines,
                    f"event_channel_offset #(.CHANNEL_OFFSET({offset})) "
                    f"offset_{_identifier(node_name)}_{input_number}",
                    [*_ports(edge_base, "in"), *_ports(mapped, "out"),
                     f".channel_overflow_o({overflow})"],
                )
                prepared.append(mapped)
            else:
                prepared.append(edge_base)
        mismatch = f"error_tag_{_identifier(node_name)}"
        lines.append(f"  logic {mismatch};")
        fault_signals.append(mismatch)
        common_ports = [".clk", ".reset", *_ports(prepared[0], "in0"),
                        *_ports(prepared[1], "in1"), *_ports(output_base, "out")]
        if str(contract["kind"]) == "binary_residual_or":
            overflow = f"error_union_{_identifier(node_name)}"
            lines.append(f"  logic {overflow};")
            fault_signals.append(overflow)
            common_ports.extend([f".overflow_o({overflow})", f".tag_mismatch_o({mismatch})"])
            _instance(
                lines,
                "binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), "
                ".USE_STATE_MACRO(USE_STATE_MACRO)) "
                f"union_{_identifier(node_name)}",
                common_ports,
            )
        else:
            common_ports.append(f".tag_mismatch_o({mismatch})")
            _instance(lines, f"event_join2 join_{_identifier(node_name)}", common_ports)

    readout_inputs = incoming[readout_name]
    if len(readout_inputs) != 1:
        raise ValueError("temporal current readout must have exactly one input")
    readout = layers[readout_name]
    readout_weights = _packed_literal(
        export_dir / str(readout["weight_rom"]),
        word_bits=8,
        expected_words=int(readout["weight_count"]),
    )
    readout_h, readout_w = (int(value) for value in readout["output_hw"])
    readout_error = "error_readout"
    readout_initialized = "initialized_readout"
    lines.append(f"  logic {readout_error};")
    lines.append(f"  logic {readout_initialized};")
    fault_signals.append(readout_error)
    initialization_signals.append(readout_initialized)
    readout_params = [
        ".USE_STATE_MACRO(USE_STATE_MACRO)",
        f".INPUT_CHANNELS({int(readout['in_channels'])})",
        f".CLASS_COUNT({int(readout['out_channels'])})",
        f".OUTPUT_WIDTH({readout_w})", f".OUTPUT_HEIGHT({readout_h})",
        f".PREDICTION_BINS({int(spec['timing_contract']['prediction_bins_default'])})",
        f".READOUT_WEIGHTS({readout_weights})",
    ]
    _instance(
        lines,
        "temporal_class_readout #(\n    " + ",\n    ".join(readout_params) +
        "\n  ) temporal_readout",
        [".clk", ".reset", *_ports(f"e_{readout_inputs[0][0]}", "in"),
         ".prediction_valid", ".prediction_ready", ".prediction_x_o",
         ".prediction_y_o", ".prediction_class_o", ".frame_done_valid",
         ".frame_done_ready", ".frame_bin_tag_o",
         f".address_error_o({readout_error})",
         f".initialization_done_o({readout_initialized})"],
    )
    lines.append(
        "  assign all_memories_initialized = "
        + (" & ".join(initialization_signals) or "1'b1")
        + ";"
    )
    lines.append("  assign fault_o = " + (" | ".join(fault_signals) or "1'b0") + ";")
    lines.append("endmodule")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _declare_sized_stream(lines: list[str], base: str, width: int | str) -> None:
    lines.extend(
        [
            f"  logic {base}_valid;",
            f"  logic {base}_ready;",
            f"  logic [{width}-1:0] {base}_payload;",
            f"  logic {base}_completion;",
            f"  logic [TAG_WIDTH-1:0] {base}_bin_tag;",
        ]
    )


def _resident_shapes(
    graph: dict[str, Any], layers: dict[str, dict[str, Any]]
) -> dict[str, tuple[int, int, int]]:
    """Infer channel/height/width for every resident spike-vector node."""
    shapes: dict[str, tuple[int, int, int]] = {}
    actors = set(graph["actor_topological_order"])
    for name in actors:
        layer = layers[name]
        height, width = (int(value) for value in layer["output_hw"])
        shapes[name] = (int(layer["out_channels"]), height, width)
    first = layers[str(graph["actor_topological_order"][0])]
    input_height, input_width = (int(value) for value in first["input_hw"])
    shapes["input"] = (int(first["in_channels"]), input_height, input_width)
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph["edges"]:
        incoming[str(edge["destination"])].append(edge)
    kinds = {str(node["name"]): str(node["kind"]) for node in graph["nodes"]}
    unresolved = {
        name
        for name in kinds
        if name not in shapes and name not in {str(graph["current_readout"]), "prediction"}
    }
    while unresolved:
        progressed = False
        for name in list(unresolved):
            sources = [str(edge["source"]) for edge in incoming[name]]
            if not sources or any(source not in shapes for source in sources):
                continue
            source_shapes = [shapes[source] for source in sources]
            kind = kinds[name]
            if kind == "nearest_event_fanout_2x":
                channels, height, width = source_shapes[0]
                shape = (channels, 2 * height, 2 * width)
            elif kind == "channel_concat":
                heights = {shape[1] for shape in source_shapes}
                widths = {shape[2] for shape in source_shapes}
                if len(heights) != 1 or len(widths) != 1:
                    raise ValueError(f"concat node {name} has incompatible spatial shapes")
                shape = (
                    sum(item[0] for item in source_shapes),
                    source_shapes[0][1],
                    source_shapes[0][2],
                )
            elif kind in {"binary_residual_or", "multiplicity_preserving_sum"}:
                if any(item != source_shapes[0] for item in source_shapes[1:]):
                    raise ValueError(f"merge node {name} has incompatible vector shapes")
                shape = source_shapes[0]
            else:
                raise ValueError(f"unsupported resident route node {name} ({kind})")
            shapes[name] = shape
            unresolved.remove(name)
            progressed = True
        if not progressed:
            raise ValueError("could not infer all resident graph vector shapes")
    return shapes


def _generate_resident_top(
    model_spec_path: Path,
    output_path: Path,
    *,
    module_name: str,
    tile_width: int,
    tile_height: int,
) -> None:
    if tile_width < 1 or tile_height < 1:
        raise ValueError("resident tile dimensions must be positive")
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    export_dir = (model_spec_path.parent / str(spec.get("artifact_root", "."))).resolve()
    graph = spec["graph"]
    actors = list(graph["actor_topological_order"])
    if len(actors) != 25 or graph.get("linear_pipeline") is not False:
        raise ValueError("resident generation requires the exact non-linear 25-actor graph")
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    readout_name = str(graph["current_readout"])
    shapes = _resident_shapes(graph, layers)
    edges = [
        dict(edge)
        for edge in graph["edges"]
        if str(edge["destination"]) != "prediction"
    ]
    incoming: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    outgoing: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, edge in enumerate(edges):
        incoming[str(edge["destination"])].append((index, edge))
        outgoing[str(edge["source"])].append((index, edge))
    if any(len(items) > 2 for items in incoming.values()) or any(
        len(items) > 2 for items in outgoing.values()
    ):
        raise ValueError("resident generator supports graph degree <= 2")
    node_kinds = {str(node["name"]): str(node["kind"]) for node in graph["nodes"]}
    readout = layers[readout_name]
    class_count = int(readout["out_channels"])
    class_width = max(1, (class_count - 1).bit_length())
    lines = [
        "`timescale 1ns/1ps",
        "// Generated resident-state ASIC top; do not hand edit.",
        f"module {module_name} #(",
        "  parameter integer PAYLOAD_WIDTH = 32,",
        "  parameter integer TAG_WIDTH = 24",
        ") (",
        "  input logic clk, input logic reset,",
        "  input logic input_valid, output logic input_ready,",
        "  input logic [PAYLOAD_WIDTH-1:0] input_payload,",
        "  input logic input_completion,",
        "  input logic [TAG_WIDTH-1:0] input_bin_tag,",
        "  output logic prediction_valid, input logic prediction_ready,",
        "  output logic [9:0] prediction_x_o, output logic [8:0] prediction_y_o,",
        f"  output logic [{class_width-1}:0] prediction_class_o,",
        "  output logic frame_done_valid, input logic frame_done_ready,",
        "  output logic [TAG_WIDTH-1:0] frame_bin_tag_o,",
        "  output logic fault_o",
        ");",
    ]
    _declare_sized_stream(lines, "ingress", "PAYLOAD_WIDTH")
    lines.extend(
        [
            "  assign ingress_valid = input_valid;",
            "  assign input_ready = ingress_ready;",
            "  assign ingress_payload = input_payload;",
            "  assign ingress_completion = input_completion;",
            "  assign ingress_bin_tag = input_bin_tag;",
        ]
    )
    stream_nodes = {
        name
        for name in node_kinds
        if name not in {"input", readout_name, "prediction"}
    }
    for name in sorted(stream_nodes):
        width = shapes[name][0] * shapes[name][1] * shapes[name][2]
        _declare_sized_stream(lines, f"n_{_identifier(name)}", width)
    for index, edge in enumerate(edges):
        source = str(edge["source"])
        width: int | str = "PAYLOAD_WIDTH" if source == "input" else (
            shapes[source][0] * shapes[source][1] * shapes[source][2]
        )
        _declare_sized_stream(lines, f"r_{index}", width)

    def source_base(name: str) -> str:
        return "ingress" if name == "input" else f"n_{_identifier(name)}"

    for source, source_edges in outgoing.items():
        base = source_base(source)
        if len(source_edges) == 1:
            _connect_stream(lines, base, f"r_{source_edges[0][0]}")
        elif source == "input":
            first, second = source_edges
            _instance(
                lines,
                "event_fork2 #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH)) ingress_fork",
                [".clk", ".reset", *_ports(base, "in"),
                 *_ports(f"r_{first[0]}", "out0"),
                 *_ports(f"r_{second[0]}", "out1")],
            )
        else:
            first, second = source_edges
            width = shapes[source][0] * shapes[source][1] * shapes[source][2]
            _instance(
                lines,
                f"resident_spike_vector_fork2 #(.VECTOR_WIDTH({width}), .TAG_WIDTH(TAG_WIDTH)) fork_{_identifier(source)}",
                [".clk", ".reset", f".in_valid_i({base}_valid)",
                 f".in_ready_o({base}_ready)", f".in_vector_i({base}_payload)",
                 f".in_completion_i({base}_completion)", f".in_tag_i({base}_bin_tag)",
                 f".out0_valid_o(r_{first[0]}_valid)", f".out0_ready_i(r_{first[0]}_ready)",
                 f".out0_vector_o(r_{first[0]}_payload)", f".out0_completion_o(r_{first[0]}_completion)",
                 f".out0_tag_o(r_{first[0]}_bin_tag)",
                 f".out1_valid_o(r_{second[0]}_valid)", f".out1_ready_i(r_{second[0]}_ready)",
                 f".out1_vector_o(r_{second[0]}_payload)", f".out1_completion_o(r_{second[0]}_completion)",
                 f".out1_tag_o(r_{second[0]}_bin_tag)"],
            )

    faults: list[str] = []
    for actor_name in actors:
        actor_inputs = incoming[actor_name]
        if len(actor_inputs) != 1:
            raise ValueError(f"actor {actor_name} must have exactly one input")
        edge_index, edge = actor_inputs[0]
        layer = layers[actor_name]
        input_h, input_w = (int(value) for value in layer["input_hw"])
        output_h, output_w = (int(value) for value in layer["output_hw"])
        input_channels = int(layer["in_channels"])
        output_channels = int(layer["out_channels"])
        actor_input = f"r_{edge_index}"
        if str(edge["source"]) == "input":
            adapted = f"a_{_identifier(actor_name)}"
            _declare_sized_stream(lines, adapted, input_channels * input_h * input_w)
            ingress_error = f"error_ingress_{_identifier(actor_name)}"
            lines.append(f"  logic {ingress_error};")
            faults.append(ingress_error)
            _instance(
                lines,
                f"resident_event_ingress_adapter #(.INPUT_CHANNELS({input_channels}), .INPUT_WIDTH({input_w}), .INPUT_HEIGHT({input_h}), .TAG_WIDTH(TAG_WIDTH)) ingress_{_identifier(actor_name)}",
                [f".in_valid_i({actor_input}_valid)", f".in_ready_o({actor_input}_ready)",
                 f".in_payload_i({actor_input}_payload)", f".in_completion_i({actor_input}_completion)",
                 f".in_tag_i({actor_input}_bin_tag)", f".out_valid_o({adapted}_valid)",
                 f".out_ready_i({adapted}_ready)", f".out_spike_vector_o({adapted}_payload)",
                 f".out_completion_o({adapted}_completion)", f".out_tag_o({adapted}_bin_tag)",
                 f".coordinate_error_o({ingress_error})"],
            )
            actor_input = adapted
        kernel_h, kernel_w = (int(value) for value in layer["kernel"])
        stride_y, stride_x = (int(value) for value in layer["stride"])
        pad_y, pad_x = (int(value) for value in layer["padding"])
        dilation_y, dilation_x = (int(value) for value in layer["dilation"])
        weights = _packed_literal(
            export_dir / str(layer["weight_rom"]),
            word_bits=8,
            expected_words=int(layer["weight_count"]),
        )
        betas = _parameter_literal(
            export_dir, layer, key="beta_q", rom_key="beta_rom", word_bits=16
        )
        thresholds = _parameter_literal(
            export_dir, layer, key="threshold_q", rom_key="threshold_rom", word_bits=16
        )
        mechanism = _mechanism_parameters(export_dir, layer)
        error = f"error_actor_{_identifier(actor_name)}"
        lines.append(f"  logic {error};")
        faults.append(error)
        params = [
            f".INPUT_CHANNELS({input_channels})", f".INPUT_WIDTH({input_w})",
            f".INPUT_HEIGHT({input_h})", f".OUTPUT_CHANNELS({output_channels})",
            f".OUTPUT_WIDTH({output_w})", f".OUTPUT_HEIGHT({output_h})",
            f".SPATIAL_TILE_WIDTH({min(tile_width, output_w)})",
            f".SPATIAL_TILE_HEIGHT({min(tile_height, output_h)})",
            f".GROUPS({int(layer['groups'])})", f".KERNEL_WIDTH({kernel_w})",
            f".KERNEL_HEIGHT({kernel_h})", f".STRIDE_X({stride_x})",
            f".STRIDE_Y({stride_y})", f".DILATION_X({dilation_x})",
            f".DILATION_Y({dilation_y})", f".PAD_X({pad_x})", f".PAD_Y({pad_y})",
            f".TAG_WIDTH(TAG_WIDTH)", f".KERNEL_WEIGHTS({weights})",
            f".CHANNEL_BETAS({betas})", f".CHANNEL_THRESHOLDS({thresholds})",
            f".ENABLE_INHIBITION({mechanism['inhibition_enabled']})",
            f".ENABLE_ADAPTATION({mechanism['adaptation_enabled']})",
            f".INHIBITION_STRENGTH(16'h{mechanism['inhibition_strength'] & 0xFFFF:04x})",
            f".ADAPTATION_STRENGTH(16'h{mechanism['adaptation_strength'] & 0xFFFF:04x})",
            f".ADAPTATION_DURATION(16'h{mechanism['adaptation_duration'] & 0xFFFF:04x})",
        ]
        output = f"n_{_identifier(actor_name)}"
        _instance(
            lines,
            "streaming_resident_channelized_plif_actor #(\n    " +
            ",\n    ".join(params) + f"\n  ) actor_{_identifier(actor_name)}",
            [".clk", ".reset", f".in_valid_i({actor_input}_valid)",
             f".in_ready_o({actor_input}_ready)", f".in_spike_vector_i({actor_input}_payload)",
             f".in_completion_i({actor_input}_completion)", f".in_tag_i({actor_input}_bin_tag)",
             f".out_valid_o({output}_valid)", f".out_ready_i({output}_ready)",
             f".out_spike_vector_o({output}_payload)", f".out_completion_o({output}_completion)",
             f".out_tag_o({output}_bin_tag)", f".error_o({error})"],
        )

    for node_name, kind in node_kinds.items():
        if node_name in actors or node_name in {"input", readout_name, "prediction"}:
            continue
        node_inputs = incoming[node_name]
        output = f"n_{_identifier(node_name)}"
        out_channels, out_h, out_w = shapes[node_name]
        out_count = out_channels * out_h * out_w
        if kind == "nearest_event_fanout_2x":
            edge_index, edge = node_inputs[0]
            in_channels, in_h, in_w = shapes[str(edge["source"])]
            base = f"r_{edge_index}"
            _instance(
                lines,
                f"resident_spike_vector_upsample2x #(.CHANNELS({in_channels}), .INPUT_WIDTH({in_w}), .INPUT_HEIGHT({in_h}), .TAG_WIDTH(TAG_WIDTH)) upsample_{_identifier(node_name)}",
                [f".in_valid_i({base}_valid)", f".in_ready_o({base}_ready)",
                 f".in_vector_i({base}_payload)", f".in_completion_i({base}_completion)",
                 f".in_tag_i({base}_bin_tag)", f".out_valid_o({output}_valid)",
                 f".out_ready_i({output}_ready)", f".out_vector_o({output}_payload)",
                 f".out_completion_o({output}_completion)", f".out_tag_o({output}_bin_tag)"],
            )
            continue
        if len(node_inputs) != 2:
            raise ValueError(f"resident join {node_name} requires two inputs")
        prepared: list[str] = []
        for input_number, (edge_index, edge) in enumerate(node_inputs):
            base = f"r_{edge_index}"
            if kind == "channel_concat":
                source_shape = shapes[str(edge["source"])]
                mapped = f"m_{_identifier(node_name)}_{input_number}"
                _declare_sized_stream(lines, mapped, out_count)
                map_error = f"error_map_{_identifier(node_name)}_{input_number}"
                lines.append(f"  logic {map_error};")
                faults.append(map_error)
                _instance(
                    lines,
                    f"resident_spike_vector_channel_offset #(.INPUT_CHANNELS({source_shape[0]}), .OUTPUT_CHANNELS({out_channels}), .SPATIAL_COUNT({out_h*out_w}), .CHANNEL_OFFSET({int(edge.get('channel_offset', 0))}), .TAG_WIDTH(TAG_WIDTH)) map_{_identifier(node_name)}_{input_number}",
                    [f".in_valid_i({base}_valid)", f".in_ready_o({base}_ready)",
                     f".in_vector_i({base}_payload)", f".in_completion_i({base}_completion)",
                     f".in_tag_i({base}_bin_tag)", f".out_valid_o({mapped}_valid)",
                     f".out_ready_i({mapped}_ready)", f".out_vector_o({mapped}_payload)",
                     f".out_completion_o({mapped}_completion)", f".out_tag_o({mapped}_bin_tag)",
                     f".configuration_error_o({map_error})"],
                )
                prepared.append(mapped)
            else:
                prepared.append(base)
        mismatch = f"error_tag_{_identifier(node_name)}"
        lines.append(f"  logic {mismatch};")
        faults.append(mismatch)
        if kind == "binary_residual_or":
            _instance(
                lines,
                f"resident_spike_vector_union2 #(.VECTOR_WIDTH({out_count}), .TAG_WIDTH(TAG_WIDTH)) union_{_identifier(node_name)}",
                [".clk", ".reset", f".in0_valid_i({prepared[0]}_valid)",
                 f".in0_ready_o({prepared[0]}_ready)", f".in0_vector_i({prepared[0]}_payload)",
                 f".in0_completion_i({prepared[0]}_completion)", f".in0_tag_i({prepared[0]}_bin_tag)",
                 f".in1_valid_i({prepared[1]}_valid)", f".in1_ready_o({prepared[1]}_ready)",
                 f".in1_vector_i({prepared[1]}_payload)", f".in1_completion_i({prepared[1]}_completion)",
                 f".in1_tag_i({prepared[1]}_bin_tag)", f".out_valid_o({output}_valid)",
                 f".out_ready_i({output}_ready)", f".out_vector_o({output}_payload)",
                 f".out_completion_o({output}_completion)", f".out_tag_o({output}_bin_tag)",
                 f".tag_mismatch_o({mismatch})"],
            )
        else:
            _instance(
                lines,
                f"event_join2 #(.PAYLOAD_WIDTH({out_count}), .TAG_WIDTH(TAG_WIDTH)) join_{_identifier(node_name)}",
                [".clk", ".reset", *_ports(prepared[0], "in0"),
                 *_ports(prepared[1], "in1"), *_ports(output, "out"),
                 f".tag_mismatch_o({mismatch})"],
            )

    readout_input = incoming[readout_name]
    if len(readout_input) != 1:
        raise ValueError("resident temporal readout requires one input")
    readout_base = f"r_{readout_input[0][0]}"
    readout_h, readout_w = (int(value) for value in readout["output_hw"])
    readout_weights = _packed_literal(
        export_dir / str(readout["weight_rom"]),
        word_bits=8,
        expected_words=int(readout["weight_count"]),
    )
    _instance(
        lines,
        "resident_temporal_class_readout #(\n    " + ",\n    ".join(
            [f".INPUT_CHANNELS({int(readout['in_channels'])})",
             f".CLASS_COUNT({class_count})", f".OUTPUT_WIDTH({readout_w})",
             f".OUTPUT_HEIGHT({readout_h})",
             f".PREDICTION_BINS({int(spec['timing_contract']['prediction_bins_default'])})",
             f".TAG_WIDTH(TAG_WIDTH)", f".READOUT_WEIGHTS({readout_weights})"]
        ) + "\n  ) temporal_readout",
        [".clk", ".reset", f".in_valid_i({readout_base}_valid)",
         f".in_ready_o({readout_base}_ready)",
         f".in_spike_vector_i({readout_base}_payload)",
         f".in_completion_i({readout_base}_completion)", f".in_tag_i({readout_base}_bin_tag)",
         ".prediction_valid_o(prediction_valid)", ".prediction_ready_i(prediction_ready)",
         ".prediction_x_o(prediction_x_o)", ".prediction_y_o(prediction_y_o)",
         ".prediction_class_o(prediction_class_o)",
         ".frame_done_valid_o(frame_done_valid)", ".frame_done_ready_i(frame_done_ready)",
         ".frame_tag_o(frame_bin_tag_o)"],
    )
    lines.append("  assign fault_o = " + (" | ".join(faults) or "1'b0") + ";")
    lines.append("endmodule")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_top(
    model_spec_path: Path,
    output_path: Path,
    *,
    module_name: str = "eventspikeseg140k_dag_top",
    lane_config_path: Path | None = None,
    architecture: str = "resident",
    resident_tile_width: int = 8,
    resident_tile_height: int = 8,
) -> None:
    if architecture == "resident":
        if lane_config_path is not None:
            raise ValueError("resident architecture has no addressed-state lane configuration")
        _generate_resident_top(
            model_spec_path,
            output_path,
            module_name=module_name,
            tile_width=resident_tile_width,
            tile_height=resident_tile_height,
        )
    elif architecture == "legacy_sram":
        _generate_legacy_top(
            model_spec_path,
            output_path,
            module_name=module_name,
            lane_config_path=lane_config_path,
        )
    else:
        raise ValueError(f"unknown ASIC architecture {architecture!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--module-name", default="eventspikeseg140k_dag_top")
    parser.add_argument("--lane-config", type=Path)
    parser.add_argument(
        "--architecture", choices=("resident", "legacy_sram"), default="resident"
    )
    parser.add_argument("--resident-tile-width", type=int, default=8)
    parser.add_argument("--resident-tile-height", type=int, default=8)
    args = parser.parse_args()
    generate_top(
        args.model_spec,
        args.output,
        module_name=args.module_name,
        lane_config_path=args.lane_config,
        architecture=args.architecture,
        resident_tile_width=args.resident_tile_width,
        resident_tile_height=args.resident_tile_height,
    )


if __name__ == "__main__":
    main()
