#!/usr/bin/env python3
"""Generate the fixed EventSpikeSeg140k SystemVerilog DAG from an ASIC export."""

from __future__ import annotations

import argparse
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
    packed = "".join(f"{value:0{digits}x}" for value in reversed(values))
    return f"{expected_words * word_bits}'h{packed}"


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


def generate_top(
    model_spec_path: Path,
    output_path: Path,
    *,
    module_name: str = "eventspikeseg140k_dag_top",
) -> None:
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    export_dir = model_spec_path.parent
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
        f"module {module_name} #(",
        "  parameter integer PAYLOAD_WIDTH = 32,",
        "  parameter integer TAG_WIDTH = 24,",
        "  parameter integer RESIDUAL_MAX_EVENTS = 64",
        ") (",
        "  input logic clk, input logic reset,",
        "  input logic input_valid, output logic input_ready,",
        "  input logic [PAYLOAD_WIDTH-1:0] input_payload,",
        "  input logic input_completion,",
        "  input logic [TAG_WIDTH-1:0] input_bin_tag,",
        "  output logic prediction_valid, input logic prediction_ready,",
        "  output logic [9:0] prediction_x_o, output logic [8:0] prediction_y_o,",
        "  output logic [3:0] prediction_class_o,",
        "  output logic frame_done_valid, input logic frame_done_ready,",
        "  output logic [TAG_WIDTH-1:0] frame_bin_tag_o,",
        "  output logic fault_o",
        ");",
    ]

    stream_nodes = {
        name
        for name in node_kinds
        if name not in {"input", readout_name, "prediction"}
    }
    for name in sorted(stream_nodes):
        _declare_stream(lines, f"n_{_identifier(name)}")
    for index, _edge in enumerate(edges):
        _declare_stream(lines, f"e_{index}")

    fault_signals: list[str] = []
    source_base = lambda name: "input" if name == "input" else f"n_{_identifier(name)}"
    for source, source_edges in outgoing.items():
        base = source_base(source)
        if len(source_edges) == 1:
            _connect_stream(lines, base, f"e_{source_edges[0][0]}")
        elif len(source_edges) == 2:
            first, second = source_edges
            ports = [".clk", ".reset", *_ports(base, "in")]
            ports.extend(_ports(f"e_{first[0]}", "out0"))
            ports.extend(_ports(f"e_{second[0]}", "out1"))
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
        lines.append(f"  logic {error};")
        fault_signals.append(error)
        params = [
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
                "binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) "
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
    lines.append(f"  logic {readout_error};")
    fault_signals.append(readout_error)
    readout_params = [
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
         f".address_error_o({readout_error})"],
    )
    lines.append("  assign fault_o = " + (" | ".join(fault_signals) or "1'b0") + ";")
    lines.append("endmodule")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--module-name", default="eventspikeseg140k_dag_top")
    args = parser.parse_args()
    generate_top(args.model_spec, args.output, module_name=args.module_name)


if __name__ == "__main__":
    main()
