#!/usr/bin/env python3
# ruff: noqa: E501
"""Generate the exact native XL top with actor/readout leaves replaced by hard macros."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def _matching_paren(text: str, opening: int) -> int:
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unterminated parameter block in generated native top")


def _replace_parameterized_instances(
    source: str, module: str, replacements: list[tuple[str, str]]
) -> tuple[str, list[str], str]:
    pattern = re.compile(rf"\b{re.escape(module)}\s*#\s*\(")
    matches = list(pattern.finditer(source))
    if len(matches) != len(replacements):
        raise ValueError(
            f"expected {len(replacements)} {module} instances, found {len(matches)}"
        )
    result: list[str] = []
    retained: list[str] = []
    observed_instances: list[str] = []
    cursor = 0
    for match, (expected_instance, replacement_module) in zip(matches, replacements):
        opening = source.find("(", match.start(), match.end())
        closing = _matching_paren(source, opening)
        suffix = source[closing + 1 :]
        instance_match = re.match(r"\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", suffix)
        if not instance_match:
            raise ValueError(f"cannot identify instance following {module}")
        observed = instance_match.group(1)
        if observed != expected_instance:
            raise ValueError(f"expected instance {expected_instance}, found {observed}")
        unchanged = source[cursor : match.start()]
        retained.append(unchanged)
        result.extend((unchanged, replacement_module))
        observed_instances.append(observed)
        cursor = closing + 1
    retained.append(source[cursor:])
    result.append(source[cursor:])
    return "".join(result), observed_instances, _text_sha256("".join(retained))


def _actor_wrapper(
    actor: str,
    layer: dict[str, Any],
    rows: list[dict[str, str]],
    masters: dict[str, dict[str, Any]],
    logical_tile_h: int,
    logical_tile_w: int,
    physical_tile_h: int,
    physical_tile_w: int,
) -> str:
    wrapper = "xl_macro_actor__" + _identifier(actor)
    input_channels = int(layer["in_channels"])
    output_channels = int(layer["out_channels"])
    input_h, input_w = (int(value) for value in layer["input_hw"])
    output_h, output_w = (int(value) for value in layer["output_hw"])
    kernel_h, kernel_w = (int(value) for value in layer["kernel"])
    stride_y, stride_x = (int(value) for value in layer["stride"])
    pad_y, pad_x = (int(value) for value in layer["padding"])
    dilation_y, dilation_x = (int(value) for value in layer["dilation"])
    tile_rows = (output_h + physical_tile_h - 1) // physical_tile_h
    tile_columns = (output_w + physical_tile_w - 1) // physical_tile_w
    tile_count = tile_rows * tile_columns
    by_master: dict[str, dict[str, str]] = {}
    for row in rows:
        by_master.setdefault(row["master"], row)

    lines = [
        f"module {wrapper} (",
        "  input logic clk, input logic reset,",
        "  input logic in_valid_i, output logic in_ready_o,",
        f"  input logic [{input_channels * input_h * input_w - 1}:0] in_spike_vector_i,",
        "  input logic in_completion_i, input logic [23:0] in_tag_i,",
        "  output logic out_valid_o, input logic out_ready_i,",
        f"  output logic [{output_channels * output_h * output_w - 1}:0] out_spike_vector_o,",
        "  output logic out_completion_o, output logic [23:0] out_tag_o,",
        "  output logic error_o",
        ");",
        f"  localparam integer LOGICAL_TILE_HEIGHT = {logical_tile_h};",
        f"  localparam integer LOGICAL_TILE_WIDTH = {logical_tile_w};",
        f"  localparam integer PHYSICAL_TILE_HEIGHT = {physical_tile_h};",
        f"  localparam integer PHYSICAL_TILE_WIDTH = {physical_tile_w};",
        f"  localparam integer TILE_COUNT = {tile_count};",
        f"  logic [{output_channels * output_h * output_w - 1}:0] result_vector;",
        f"  logic [{tile_count - 1}:0] tile_presynaptic_ready, tile_completion_ready;",
        f"  logic [{tile_count - 1}:0] tile_result_valid, tile_error;",
        f"  logic [{tile_count - 1}:0][23:0] tile_tag;",
        "  logic presynaptic_ready, completion_ready, result_valid, result_ready, tag_error;",
        "  assign presynaptic_ready = (&tile_presynaptic_ready) && !in_completion_i;",
        "  assign completion_ready = (&tile_completion_ready) && in_completion_i;",
        "  assign in_ready_o = in_completion_i ? completion_ready : presynaptic_ready;",
        "  assign result_valid = &tile_result_valid;",
        "  assign error_o = (|tile_error) || tag_error;",
        "  always_comb begin",
        "    tag_error = 1'b0;",
        "    if (result_valid)",
        "      for (integer i = 1; i < TILE_COUNT; i = i+1)",
        "        if (tile_tag[i] != tile_tag[0]) tag_error = 1'b1;",
        "  end",
        f"  for (genvar tile_y = 0; tile_y < {tile_rows}; tile_y = tile_y+1) begin : row",
        f"    for (genvar tile_x = 0; tile_x < {tile_columns}; tile_x = tile_x+1) begin : column",
        f"      localparam integer INDEX = tile_y*{tile_columns}+tile_x;",
        f"      localparam integer LOCAL_WIDTH = (((tile_x+1)*{physical_tile_w}) <= {output_w}) ? {physical_tile_w} : {output_w}-tile_x*{physical_tile_w};",
        f"      localparam integer LOCAL_HEIGHT = (((tile_y+1)*{physical_tile_h}) <= {output_h}) ? {physical_tile_h} : {output_h}-tile_y*{physical_tile_h};",
        f"      localparam integer RAW_MIN_X = tile_x*{physical_tile_w}*{stride_x}-{pad_x};",
        f"      localparam integer RAW_MIN_Y = tile_y*{physical_tile_h}*{stride_y}-{pad_y};",
        "      localparam integer INPUT_ORIGIN_X = (RAW_MIN_X < 0) ? 0 : RAW_MIN_X;",
        "      localparam integer INPUT_ORIGIN_Y = (RAW_MIN_Y < 0) ? 0 : RAW_MIN_Y;",
        f"      localparam integer RAW_MAX_X = (tile_x*{physical_tile_w}+LOCAL_WIDTH-1)*{stride_x}-{pad_x}+{kernel_w - 1}*{dilation_x};",
        f"      localparam integer RAW_MAX_Y = (tile_y*{physical_tile_h}+LOCAL_HEIGHT-1)*{stride_y}-{pad_y}+{kernel_h - 1}*{dilation_y};",
        f"      localparam integer INPUT_END_X = (RAW_MAX_X >= {input_w}) ? {input_w - 1} : RAW_MAX_X;",
        f"      localparam integer INPUT_END_Y = (RAW_MAX_Y >= {input_h}) ? {input_h - 1} : RAW_MAX_Y;",
        "      localparam integer LOCAL_INPUT_WIDTH = INPUT_END_X-INPUT_ORIGIN_X+1;",
        "      localparam integer LOCAL_INPUT_HEIGHT = INPUT_END_Y-INPUT_ORIGIN_Y+1;",
        "      localparam integer OFFSET_X = RAW_MIN_X-INPUT_ORIGIN_X;",
        "      localparam integer OFFSET_Y = RAW_MIN_Y-INPUT_ORIGIN_Y;",
    ]
    for branch_index, (master_name, row) in enumerate(sorted(by_master.items())):
        condition = (
            f"LOCAL_WIDTH == {row['output_width']} && LOCAL_HEIGHT == {row['output_height']} && "
            f"LOCAL_INPUT_WIDTH == {row['input_width']} && LOCAL_INPUT_HEIGHT == {row['input_height']} && "
            f"OFFSET_X == {int(row['output_x']) * stride_x - pad_x - int(row['input_x'])} && "
            f"OFFSET_Y == {int(row['output_y']) * stride_y - pad_y - int(row['input_y'])}"
        )
        keyword = "if" if branch_index == 0 else "else if"
        local_spatial = int(row["output_width"]) * int(row["output_height"])
        local_input_spatial = int(row["input_width"]) * int(row["input_height"])
        master = masters[master_name]
        lines.extend(
            [
                f"      {keyword} ({condition}) begin : variant_{branch_index}",
                f"        logic [{int(master['input_bits']) - 1}:0] local_input_spikes;",
                f"        logic [{int(master['output_bits']) - 1}:0] local_spikes;",
                f"        for (genvar c = 0; c < {input_channels}; c = c+1)",
                f"          for (genvar y = 0; y < {row['input_height']}; y = y+1)",
                f"            for (genvar x = 0; x < {row['input_width']}; x = x+1)",
                f"              assign local_input_spikes[c*{local_input_spatial}+y*{row['input_width']}+x] =",
                f"                in_spike_vector_i[c*{input_w * input_h}+(INPUT_ORIGIN_Y+y)*{input_w}+INPUT_ORIGIN_X+x];",
                f"        {master_name} tile (",
                "          .clk, .reset,",
                "          .presynaptic_valid_i(in_valid_i && !in_completion_i && presynaptic_ready),",
                "          .presynaptic_ready_o(tile_presynaptic_ready[INDEX]),",
                "          .presynaptic_spike_vector_i(local_input_spikes),",
                "          .completion_valid_i(in_valid_i && in_completion_i && completion_ready),",
                "          .completion_ready_o(tile_completion_ready[INDEX]), .completion_tag_i(in_tag_i),",
                "          .result_valid_o(tile_result_valid[INDEX]), .result_ready_i(result_ready),",
                "          .spike_vector_o(local_spikes), .completion_tag_o(tile_tag[INDEX]),",
                "          .error_o(tile_error[INDEX])",
                "        );",
                f"        for (genvar c = 0; c < {output_channels}; c = c+1)",
                f"          for (genvar y = 0; y < {row['output_height']}; y = y+1)",
                f"            for (genvar x = 0; x < {row['output_width']}; x = x+1)",
                f"              assign result_vector[c*{output_w * output_h}+(tile_y*{physical_tile_h}+y)*{output_w}+tile_x*{physical_tile_w}+x] =",
                f"                local_spikes[c*{local_spatial}+y*{row['output_width']}+x];",
                "      end",
            ]
        )
    lines.extend(
        [
            "      else begin : invalid_variant",
            "        initial $error(\"hard-macro catalog has no matching actor tile variant\");",
            "      end",
            "    end",
            "  end",
            f"  resident_spike_vector_edge #(.VECTOR_WIDTH({output_channels * output_h * output_w}), .TAG_WIDTH(24)) output_edge (",
            "    .clk, .reset, .result_valid_i(result_valid), .result_ready_o(result_ready),",
            "    .spike_vector_i(result_vector), .completion_tag_i(tile_tag[0]),",
            "    .out_valid_o, .out_ready_i, .out_vector_o(out_spike_vector_o),",
            "    .out_completion_o, .out_tag_o",
            "  );",
            "endmodule",
        ]
    )
    return "\n".join(lines)


def _readout_wrapper(master: dict[str, Any], layer: dict[str, Any]) -> str:
    input_channels = int(layer["in_channels"])
    output_h, output_w = (int(value) for value in layer["output_hw"])
    tile_h, tile_w = int(master["output_height"]), int(master["output_width"])
    rows, columns = output_h // tile_h, output_w // tile_w
    count, spatial = rows * columns, output_h * output_w
    tile_index_width = max(1, (count - 1).bit_length())
    local_x_width = max(1, (tile_w - 1).bit_length())
    local_y_width = max(1, (tile_h - 1).bit_length())
    return f"""module xl_macro_temporal_readout (
  input logic clk, input logic reset,
  input logic in_valid_i, output logic in_ready_o,
  input logic [{input_channels * spatial - 1}:0] in_spike_vector_i,
  input logic in_completion_i, input logic [23:0] in_tag_i,
  output logic prediction_valid_o, input logic prediction_ready_i,
  output logic [9:0] prediction_x_o, output logic [8:0] prediction_y_o,
  output logic [3:0] prediction_class_o,
  output logic frame_done_valid_o, input logic frame_done_ready_i,
  output logic [23:0] frame_tag_o, output logic error_o
);
  localparam integer TILE_COUNT = {count};
  logic [TILE_COUNT-1:0] tile_in_ready, tile_prediction_valid;
  logic [TILE_COUNT-1:0] tile_prediction_ready, tile_frame_done_valid;
  logic [TILE_COUNT-1:0][3:0] tile_prediction_class;
  logic [TILE_COUNT-1:0][23:0] tile_frame_tag;
  logic [18:0] emit_spatial_reg;
  logic [{tile_index_width - 1}:0] selected_tile_index;
  logic tag_error;
  assign in_ready_o = &tile_in_ready;
  assign prediction_x_o = $unsigned(emit_spatial_reg) % {output_w};
  assign prediction_y_o = $unsigned(emit_spatial_reg) / {output_w};
  assign selected_tile_index = (($unsigned(prediction_y_o)/{tile_h})*{columns})+($unsigned(prediction_x_o)/{tile_w});
  assign prediction_valid_o = tile_prediction_valid[selected_tile_index];
  assign prediction_class_o = tile_prediction_class[selected_tile_index];
  assign frame_done_valid_o = &tile_frame_done_valid;
  assign frame_tag_o = tile_frame_tag[0];
  assign error_o = tag_error;
  always_comb begin
    tag_error = 1'b0;
    if (frame_done_valid_o)
      for (integer i = 1; i < TILE_COUNT; i = i+1)
        if (tile_frame_tag[i] != tile_frame_tag[0]) tag_error = 1'b1;
  end
  always_ff @(posedge clk) begin
    if (reset) emit_spatial_reg <= '0;
    else if (prediction_valid_o && prediction_ready_i)
      emit_spatial_reg <= (emit_spatial_reg+1 >= {spatial}) ? '0 : emit_spatial_reg+1'b1;
  end
  for (genvar tile_y = 0; tile_y < {rows}; tile_y = tile_y+1) begin : row
    for (genvar tile_x = 0; tile_x < {columns}; tile_x = tile_x+1) begin : column
      localparam integer INDEX = tile_y*{columns}+tile_x;
      logic [{int(master['input_bits']) - 1}:0] local_input_spikes;
      logic [{local_x_width - 1}:0] unused_prediction_x;
      logic [{local_y_width - 1}:0] unused_prediction_y;
      assign tile_prediction_ready[INDEX] = prediction_ready_i && prediction_valid_o && (selected_tile_index == INDEX);
      for (genvar c = 0; c < {input_channels}; c = c+1)
        for (genvar y = 0; y < {tile_h}; y = y+1)
          for (genvar x = 0; x < {tile_w}; x = x+1)
            assign local_input_spikes[c*{tile_h * tile_w}+y*{tile_w}+x] =
              in_spike_vector_i[c*{spatial}+(tile_y*{tile_h}+y)*{output_w}+tile_x*{tile_w}+x];
      {master['module']} tile (
        .clk, .reset, .in_valid_i(in_valid_i && in_ready_o),
        .in_ready_o(tile_in_ready[INDEX]), .in_spike_vector_i(local_input_spikes),
        .in_completion_i, .in_tag_i,
        .prediction_valid_o(tile_prediction_valid[INDEX]),
        .prediction_ready_i(tile_prediction_ready[INDEX]),
        .prediction_x_o(unused_prediction_x), .prediction_y_o(unused_prediction_y),
        .prediction_class_o(tile_prediction_class[INDEX]),
        .frame_done_valid_o(tile_frame_done_valid[INDEX]),
        .frame_done_ready_i(frame_done_ready_i && frame_done_valid_o),
        .frame_tag_o(tile_frame_tag[INDEX])
      );
    end
  end
endmodule"""


def generate(
    model_spec: Path,
    tile_plan: Path,
    catalog_path: Path,
    instances_path: Path,
    source_top: Path,
    output_top: Path,
    output_wrappers: Path,
    output_preflight: Path,
) -> dict[str, Any]:
    spec = json.loads(model_spec.read_text(encoding="utf-8"))
    plan = json.loads(tile_plan.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(instances_path.open(encoding="utf-8"), delimiter="\t"))
    actors = [str(name) for name in spec["graph"]["actor_topological_order"]]
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    masters = {str(item["module"]): item for item in catalog["masters"]}
    actor_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    readout_rows = []
    for row in rows:
        if row["kind"] == "actor_tile":
            actor_rows[row["actor"]].append(row)
        elif row["kind"] == "readout_tile":
            readout_rows.append(row)
        else:
            raise ValueError(f"unknown hard-macro instance kind {row['kind']}")
    if set(actor_rows) != set(actors):
        raise ValueError("instance map actor set differs from graph actor set")
    if Counter(row["master"] for row in rows) != Counter(
        {name: int(master["instances"]) for name, master in masters.items()}
    ):
        raise ValueError("instance map master counts differ from catalog")

    # Prove that the compile-time geometry predicate in each generated actor
    # wrapper selects exactly the master named by every instance-map row.
    for actor in actors:
        layer = layers[actor]
        output_h, output_w = (int(value) for value in layer["output_hw"])
        stride_y, stride_x = (int(value) for value in layer["stride"])
        pad_y, pad_x = (int(value) for value in layer["padding"])
        partition = catalog["actor_physical_partition_policy"]["actors"][actor]
        physical_h = int(partition["physical_tile_height"])
        physical_w = int(partition["physical_tile_width"])
        covered: set[tuple[int, int]] = set()
        master_signatures: dict[str, tuple[int, ...]] = {}
        signature_masters: dict[tuple[int, ...], str] = {}
        for row in actor_rows[actor]:
            output_y, output_x = int(row["output_y"]), int(row["output_x"])
            local_h, local_w = int(row["output_height"]), int(row["output_width"])
            if (
                int(row["tile_row"]) != output_y // int(plan["tile_nominal_hw"][0])
                or int(row["tile_column"]) != output_x // int(plan["tile_nominal_hw"][1])
                or int(row["physical_subtile_row"])
                != (output_y % int(plan["tile_nominal_hw"][0])) // physical_h
                or int(row["physical_subtile_column"])
                != (output_x % int(plan["tile_nominal_hw"][1])) // physical_w
            ):
                raise ValueError(f"{actor}: physical leaf is not grouped by its logical 8x8 tile")
            for y in range(output_y, output_y + local_h):
                for x in range(output_x, output_x + local_w):
                    if (y, x) in covered:
                        raise ValueError(f"{actor}: physical actor leaves overlap at {(y, x)}")
                    covered.add((y, x))
            signature = (
                int(row["output_width"]),
                int(row["output_height"]),
                int(row["input_width"]),
                int(row["input_height"]),
                int(row["output_x"]) * stride_x - pad_x - int(row["input_x"]),
                int(row["output_y"]) * stride_y - pad_y - int(row["input_y"]),
            )
            previous_signature = master_signatures.setdefault(row["master"], signature)
            if previous_signature != signature:
                raise ValueError(f"{actor}: one master has multiple geometry signatures")
            previous_master = signature_masters.setdefault(signature, row["master"])
            if previous_master != row["master"]:
                raise ValueError(f"{actor}: geometry signature maps to multiple masters")
        if covered != {(y, x) for y in range(output_h) for x in range(output_w)}:
            raise ValueError(f"{actor}: physical actor leaves do not cover the output exactly")

    tile_h, tile_w = (int(value) for value in plan["tile_nominal_hw"])
    actor_partitions = catalog["actor_physical_partition_policy"]["actors"]
    wrappers = ["`timescale 1ns/1ps", "// Generated fixed hard-macro assembly wrappers."]
    for actor in actors:
        partition = actor_partitions[actor]
        wrappers.append(
            _actor_wrapper(
                actor, layers[actor], actor_rows[actor], masters,
                tile_h, tile_w,
                int(partition["physical_tile_height"]),
                int(partition["physical_tile_width"]),
            )
        )
    readout_master = next(master for master in masters.values() if master["kind"] == "readout_tile")
    readout_name = str(spec["graph"]["current_readout"])
    wrappers.append(_readout_wrapper(readout_master, layers[readout_name]))
    output_wrappers.parent.mkdir(parents=True, exist_ok=True)
    wrappers_text = "\n\n".join(wrappers) + "\n"
    referenced_masters = {
        name for name in masters if re.search(rf"\b{re.escape(name)}\s+tile\s*\(", wrappers_text)
    }
    if referenced_masters != set(masters):
        raise ValueError("generated wrappers do not reference every catalogued hard master")
    if wrappers_text.count("resident_spike_vector_edge #(") != len(actors):
        raise ValueError("generated actor wrapper output-edge count is incomplete")
    output_wrappers.write_text(wrappers_text, encoding="utf-8")

    source = source_top.read_text(encoding="utf-8")
    actor_replacements = [
        ("actor_" + _identifier(actor), "xl_macro_actor__" + _identifier(actor))
        for actor in actors
    ]
    transformed, observed_actors, retained_actor_sha = _replace_parameterized_instances(
        source, "streaming_resident_channelized_plif_actor", actor_replacements
    )
    transformed, observed_readout, retained_readout_sha = _replace_parameterized_instances(
        transformed,
        "tiled_resident_temporal_class_readout",
        [("temporal_readout", "xl_macro_temporal_readout")],
    )
    output_top.write_text(transformed, encoding="utf-8")

    soft_modules = (
        "resident_event_ingress_adapter",
        "resident_spike_mask_attention",
        "resident_spike_vector_edge",
        "resident_spike_vector_fork2",
        "resident_spike_vector_channel_offset",
        "resident_spike_vector_upsample2x",
        "resident_spike_vector_union2",
        "event_join2",
    )
    soft_counts = {
        module: {
            "source": len(re.findall(rf"\b{module}\b", source)),
            "macroized": len(re.findall(rf"\b{module}\b", transformed)),
        }
        for module in soft_modules
    }
    if any(item["source"] != item["macroized"] for item in soft_counts.values()):
        raise ValueError("soft routing/attention instance inventory changed")
    interface_end = source.index(");", source.index("module eventspikesegxl_dag_top")) + 2
    transformed_interface_end = transformed.index(
        ");", transformed.index("module eventspikesegxl_dag_top")
    ) + 2
    interface_sha = _text_sha256(source[:interface_end])
    if interface_sha != _text_sha256(transformed[:transformed_interface_end]):
        raise ValueError("native top interface changed")

    readiness_path = catalog_path.parent / "hard_macro_view_readiness.json"
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    per_actor = {
        actor: {
            "physical_instances": len(actor_rows[actor]),
            "unique_masters": len({row["master"] for row in actor_rows[actor]}),
        }
        for actor in actors
    }
    preflight = {
        "schema_version": "1.0.0",
        "scope": "exact_native_xl_macroized_assembly",
        "structural_generation_complete": True,
        "physical_implementation_ready": bool(readiness["ready"]),
        "model_spec_sha256": _sha256(model_spec),
        "tile_plan_sha256": _sha256(tile_plan),
        "catalog_sha256": _sha256(catalog_path),
        "instance_map_sha256": _sha256(instances_path),
        "source_top_sha256": _sha256(source_top),
        "macroized_top_sha256": _sha256(output_top),
        "macro_wrappers_sha256": _sha256(output_wrappers),
        "native_top_interface_sha256": interface_sha,
        "retained_text_sha256_after_actor_replacement": retained_actor_sha,
        "retained_text_sha256_after_readout_replacement": retained_readout_sha,
        "native_dimensions_hw": [440, 640],
        "actor_count": len(actors),
        "logical_actor_tiles_8x8": int(catalog["logical_actor_tiles_8x8"]),
        "actor_physical_macro_instances": sum(len(value) for value in actor_rows.values()),
        "actor_physical_macro_instances_by_hw": catalog[
            "actor_physical_macro_instances_by_hw"
        ],
        "actor_count_by_resource_class": catalog["actor_count_by_resource_class"],
        "actor_logical_plifs": sum(
            int(master["output_bits"]) * int(master["instances"])
            for master in masters.values()
            if master["kind"] == "actor_tile"
        ),
        "actor_physical_receptive_halo_input_bits": sum(
            int(master["input_bits"]) * int(master["instances"])
            for master in masters.values()
            if master["kind"] == "actor_tile"
        ),
        "actor_logical_8x8_receptive_halo_input_bits": int(
            plan["totals"]["receptive_halo_input_bits"]
        ),
        "logical_readout_tiles_8x8": int(catalog["logical_readout_tiles_8x8"]),
        "readout_physical_macro_instances_2x2": len(readout_rows),
        "nominal_tile_instances": int(catalog["nominal_tile_instances"]),
        "total_hard_macro_instances": len(rows),
        "native_readout_pixels": sum(
            int(row["output_height"]) * int(row["output_width"]) for row in readout_rows
        ),
        "unique_hard_macro_masters": len(masters),
        "actor_replacements": observed_actors,
        "readout_replacements": observed_readout,
        "actor_wrapper_output_edges": wrappers_text.count("resident_spike_vector_edge #("),
        "referenced_hard_macro_masters": len(referenced_masters),
        "per_actor": per_actor,
        "soft_instance_inventory": soft_counts,
        "required_physical_views": int(readiness["required_view_file_count"]),
        "present_physical_views": int(readiness["present_view_file_count"]),
        "gate": (
            "Macroized assembly is generated, but native ORFS assembly must wait until "
            "hard_macro_view_readiness.json reports every LEF/GDS/Liberty view present."
        ),
    }
    expected = {
        "actor_count": 44,
        "logical_actor_tiles_8x8": int(plan["totals"]["tile_count"]),
        "actor_physical_macro_instances": int(
            catalog["actor_physical_macro_instances"]
        ),
        "actor_logical_plifs": int(plan["totals"]["logical_plifs"]),
        "actor_logical_8x8_receptive_halo_input_bits": int(
            plan["totals"]["receptive_halo_input_bits"]
        ),
        "logical_readout_tiles_8x8": 4400,
        "readout_physical_macro_instances_2x2": 70400,
        "nominal_tile_instances": 54010,
        "total_hard_macro_instances": int(catalog["total_hard_macro_instances"]),
        "native_readout_pixels": 281600,
        "unique_hard_macro_masters": int(catalog["unique_hard_macro_masters"]),
    }
    for key, value in expected.items():
        if preflight[key] != value:
            raise ValueError(f"conservation failure for {key}: {preflight[key]} != {value}")
    output_preflight.write_text(json.dumps(preflight, indent=2) + "\n", encoding="utf-8")
    return preflight


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-spec", type=Path, required=True)
    parser.add_argument("--tile-plan", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--source-top", type=Path, required=True)
    parser.add_argument("--output-top", type=Path, required=True)
    parser.add_argument("--output-wrappers", type=Path, required=True)
    parser.add_argument("--output-preflight", type=Path, required=True)
    args = parser.parse_args()
    preflight = generate(
        args.model_spec, args.tile_plan, args.catalog, args.instances,
        args.source_top, args.output_top, args.output_wrappers, args.output_preflight,
    )
    print(json.dumps({key: preflight[key] for key in (
        "actor_count", "logical_actor_tiles_8x8", "actor_physical_macro_instances",
        "logical_readout_tiles_8x8",
        "readout_physical_macro_instances_2x2", "nominal_tile_instances",
        "total_hard_macro_instances", "native_readout_pixels",
        "unique_hard_macro_masters", "physical_implementation_ready",
    )}, indent=2))


if __name__ == "__main__":
    main()
