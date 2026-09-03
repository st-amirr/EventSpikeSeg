from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_dag_generator_emits_compilable_25_actor_top(tmp_path: Path) -> None:
    topology = _load_module(
        ROOT / "src/eventspikeseg/asic/topology.py", "eventspikeseg_topology_contract"
    )
    generator = _load_module(
        ROOT / "scripts/generate_asic_top.py", "eventspikeseg_asic_top_generator"
    )
    graph = copy.deepcopy(topology.eventspikeseg140k_graph_contract())
    # Preserve native/half/quarter/eighth geometry and concat widths in the
    # reduced resident fixture. The old all-1x1 scalar fixture could ignore
    # these relationships; bitmap routing cannot and should not.
    for edge in graph["edges"]:
        if edge.get("transform") == "channel_concat":
            edge["channel_offset"] = 0 if edge["channel_offset"] == 0 else 1
    native = {"detail_stem", "detail1.standard", "final_fuse.standard"}
    half = {
        "stem",
        "enc1.standard",
        "enc1_extra.depthwise",
        "enc1_extra.pointwise",
    }
    quarter = {
        "down2.standard",
        "enc2.depthwise",
        "enc2.pointwise",
        "enc2_extra.depthwise",
        "enc2_extra.pointwise",
        "decoder2_fuse",
        "project2",
    }

    def output_hw(name: str) -> list[int]:
        if name in native:
            return [8, 8]
        if name in half:
            return [4, 4]
        if name in quarter:
            return [2, 2]
        return [1, 1]

    def input_hw(name: str) -> list[int]:
        if name in {"detail_stem", "stem", "detail1.standard", "final_fuse.standard"}:
            return [8, 8]
        if name in {
            "enc1.standard",
            "enc1_extra.depthwise",
            "enc1_extra.pointwise",
            "down2.standard",
        }:
            return [4, 4]
        if name in {
            "enc2.depthwise",
            "enc2.pointwise",
            "enc2_extra.depthwise",
            "enc2_extra.pointwise",
            "down3.depthwise",
            "decoder2_fuse",
            "project2",
        }:
            return [2, 2]
        return [1, 1]
    layers = []
    for index, name in enumerate(graph["actor_topological_order"]):
        safe = name.replace(".", "_")
        weight = tmp_path / f"{index:02d}_{safe}.mem"
        beta = tmp_path / f"{index:02d}_{safe}_beta.mem"
        threshold = tmp_path / f"{index:02d}_{safe}_threshold.mem"
        parameters = tmp_path / f"{index:02d}_{safe}.json"
        input_channels = 2 if name in {"decoder2_fuse", "final_fuse.standard"} else 1
        weight_count = input_channels
        weight.write_text("01\n" * weight_count, encoding="ascii")
        beta.write_text("7fff\n", encoding="ascii")
        threshold.write_text("0001\n", encoding="ascii")
        parameters.write_text(
            json.dumps(
                {
                    "inhibition_enabled": False,
                    "threshold_adaptation_enabled": False,
                    "inhibition_strength_q": None,
                    "threshold_adaptation_strength_q": None,
                    "adaptation_duration_q": None,
                }
            ),
            encoding="utf-8",
        )
        layers.append(
            {
                "name": name,
                "input_hw": input_hw(name),
                "output_hw": output_hw(name),
                "in_channels": input_channels,
                "out_channels": 1,
                "kernel": [1, 1],
                "stride": [1, 1],
                "padding": [0, 0],
                "dilation": [1, 1],
                "groups": 1,
                "weight_count": weight_count,
                "weight_rom": weight.name,
                "beta_rom": beta.name,
                "threshold_rom": threshold.name,
                "parameter_file": parameters.name,
            }
        )
    readout_weight = tmp_path / "readout.mem"
    readout_weight.write_text("01\nff\n", encoding="ascii")
    layers.append(
        {
            "name": graph["current_readout"],
            "input_hw": [8, 8],
            "output_hw": [8, 8],
            "in_channels": 1,
            "out_channels": 2,
            "kernel": [1, 1],
            "stride": [1, 1],
            "padding": [0, 0],
            "dilation": [1, 1],
            "groups": 1,
            "weight_count": 2,
            "weight_rom": readout_weight.name,
        }
    )
    model_spec = tmp_path / "model_spec.yaml"
    model_spec.write_text(
        json.dumps(
            {
                "graph": graph,
                "layers": layers,
                "timing_contract": {"prediction_bins_default": 2},
            }
        ),
        encoding="utf-8",
    )
    generated = tmp_path / "generated_dag.sv"
    generator.generate_top(
        model_spec,
        generated,
        module_name="generated_mini_dag",
        architecture="legacy_sram",
    )
    text = generated.read_text(encoding="utf-8")
    assert text.count("streaming_channelized_plif_actor #(") == 25
    buffered_edge_count = sum(
        edge["destination"] != "prediction" for edge in graph["edges"]
    )
    assert text.count("event_stream_fifo #(") == buffered_edge_count
    assert text.count("_high_watermark;") == buffered_edge_count
    assert "parameter integer EDGE_FIFO_DEPTH = 2" in text
    assert text.count(".USE_PARALLEL_BANKED_STATE(0)") == 25
    assert text.count(".STATE_CHANNEL_LANE_COUNT(1)") == 25
    assert text.count(".STATE_SPATIAL_LANE_COUNT(1)") == 25
    assert text.count("binary_event_union2 #(") == 9
    assert text.count("event_upsample2x ") == 3
    assert "temporal_class_readout #(\n" in text
    assert "parameter integer USE_STATE_MACRO = 0" in text
    assert text.count(".USE_STATE_MACRO(USE_STATE_MACRO)") == 35
    assert text.count(".initialization_done_o(initialized_actor_") == 25
    assert ".initialization_done_o(initialized_readout)" in text
    assert "assign ingress_valid = input_valid && all_memories_initialized;" in text
    assert "assign input_ready = ingress_ready && all_memories_initialized;" in text
    initialization_assignment = next(
        line for line in text.splitlines() if "assign all_memories_initialized" in line
    )
    assert initialization_assignment.count("initialized_actor_") == 25
    assert initialization_assignment.count("initialized_readout") == 1

    lane_config = tmp_path / "lane_config.json"
    first_actor = graph["actor_topological_order"][0]
    lane_config.write_text(
        json.dumps(
            {
                "actors": {
                    first_actor: {
                        "use_parallel_banked_state": True,
                        "channel_lanes": 1,
                        "spatial_lanes": 1,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    configured = tmp_path / "generated_configured_dag.sv"
    generator.generate_top(
        model_spec,
        configured,
        module_name="generated_configured_dag",
        lane_config_path=lane_config,
        architecture="legacy_sram",
    )
    configured_text = configured.read_text(encoding="utf-8")
    assert configured_text.count(".USE_PARALLEL_BANKED_STATE(1)") == 1
    assert configured_text.count(".USE_PARALLEL_BANKED_STATE(0)") == 24

    testbench = tmp_path / "generated_mini_dag_tb.sv"
    testbench.write_text(
        """`timescale 1ns/1ps
module generated_mini_dag_tb;
  logic clk = 0; always #5 clk = ~clk;
  logic reset = 1, input_valid = 0, input_completion = 0;
  logic [31:0] input_payload = 0;
  logic [23:0] input_bin_tag = 0;
  logic input_ready, prediction_valid, frame_done_valid, fault_o;
  logic [9:0] prediction_x_o;
  logic [8:0] prediction_y_o;
  logic [3:0] prediction_class_o;
  logic [23:0] frame_bin_tag_o;
  integer cycles = 0;
  generated_mini_dag dut(
    .clk, .reset, .input_valid, .input_ready, .input_payload, .input_completion,
    .input_bin_tag, .prediction_valid, .prediction_ready(1'b1), .prediction_x_o,
    .prediction_y_o, .prediction_class_o, .frame_done_valid,
    .frame_done_ready(1'b1), .frame_bin_tag_o, .fault_o
  );
  task send_completion(input [23:0] tag);
    begin
      while (!input_ready) @(posedge clk);
      @(negedge clk); input_completion = 1; input_bin_tag = tag; input_valid = 1;
      @(posedge clk); @(negedge clk); input_valid = 0; input_completion = 0;
    end
  endtask
  initial begin
    repeat (3) @(posedge clk); reset = 0;
    send_completion(24'd1);
    send_completion(24'd2);
    while (!frame_done_valid && cycles < 5000) begin
      @(posedge clk); cycles = cycles + 1;
    end
    if (!frame_done_valid || frame_bin_tag_o != 2 || fault_o) $fatal(1);
    $display("FULL_DAG_COMPLETION_PASS");
    $finish;
  end
endmodule
""",
        encoding="utf-8",
    )
    sources = sorted((ROOT / "asic/rtl").glob("*.sv"))
    executable = tmp_path / "generated_mini_dag.vvp"
    subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "generated_mini_dag_tb",
            "-o",
            str(executable),
            *(str(path) for path in sources),
            str(generated),
            str(testbench),
        ],
        check=True,
        cwd=ROOT,
    )
    version = subprocess.run(
        ["iverilog", "-V"], capture_output=True, text=True, check=True
    )
    # Icarus 11 enters a known zero-time event-loop assertion/oscillation on
    # this large generated ready/valid graph. Compilation still validates the
    # complete structure there; Icarus 12+ runs the bounded token simulation.
    if "Icarus Verilog version 11." in version.stdout + version.stderr:
        return
    result = subprocess.run(
        ["vvp", str(executable)], check=True, capture_output=True, text=True, cwd=ROOT
    )
    assert "FULL_DAG_COMPLETION_PASS" in result.stdout

    resident = tmp_path / "generated_resident_dag.sv"
    generator.generate_top(
        model_spec, resident, module_name="generated_resident_dag"
    )
    resident_text = resident.read_text(encoding="utf-8")
    assert resident_text.count("streaming_resident_channelized_plif_actor #(") == 25
    assert resident_text.count(".SPATIAL_TILE_WIDTH(") == 25
    assert resident_text.count(".SPATIAL_TILE_HEIGHT(") == 25
    assert resident_text.count("resident_spike_vector_union2 #(") == 9
    assert resident_text.count("resident_spike_vector_upsample2x #(") == 3
    assert "resident_temporal_class_readout #(\n" in resident_text
    assert "actor_local_state_sram" not in resident_text
    assert "USE_STATE_MACRO" not in resident_text

    resident_testbench = tmp_path / "generated_resident_dag_tb.sv"
    resident_testbench.write_text(
        testbench.read_text(encoding="utf-8").replace(
            "generated_mini_dag", "generated_resident_dag"
        ),
        encoding="utf-8",
    )
    resident_executable = tmp_path / "generated_resident_dag.vvp"
    resident_sources = [
        ROOT / "asic/rtl/event_fork2.sv",
        ROOT / "asic/rtl/event_join2.sv",
        ROOT / "asic/rtl/resident_channelized_plif_actor.sv",
        ROOT / "asic/rtl/resident_convolution_synapses.sv",
        ROOT / "asic/rtl/resident_event_ingress_adapter.sv",
        ROOT / "asic/rtl/resident_plif_population.sv",
        ROOT / "asic/rtl/resident_retinotopic_plif_population.sv",
        ROOT / "asic/rtl/resident_spike_vector_channel_offset.sv",
        ROOT / "asic/rtl/resident_spike_vector_edge.sv",
        ROOT / "asic/rtl/resident_spike_vector_fork2.sv",
        ROOT / "asic/rtl/resident_spike_vector_union2.sv",
        ROOT / "asic/rtl/resident_spike_vector_upsample2x.sv",
        ROOT / "asic/rtl/resident_temporal_class_readout.sv",
        ROOT / "asic/rtl/tiled_resident_channelized_plif_actor.sv",
        ROOT / "asic/rtl/retinotopic_mechanism_update.sv",
        ROOT / "asic/rtl/streaming_resident_channelized_plif_actor.sv",
    ]
    subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "generated_resident_dag_tb",
            "-o",
            str(resident_executable),
            *(str(path) for path in resident_sources),
            str(resident),
            str(resident_testbench),
        ],
        check=True,
        cwd=ROOT,
        timeout=60,
    )
    # Icarus compiles the complete reduced resident DAG, but event simulation
    # of its deliberately fully parallel bitmap combinational network takes
    # more than 60 seconds even at 8x8. Bounded cocotb tests cover each resident
    # actor/route primitive; full-DAG resident equivalence needs a compiled
    # simulator and is not claimed by this elaboration gate.
    assert resident_executable.exists()


def test_packed_literal_chunks_large_rom_without_changing_word_order(tmp_path: Path) -> None:
    generator = _load_module(
        ROOT / "scripts/generate_asic_top.py", "eventspikeseg_asic_top_chunk_test"
    )
    rom = tmp_path / "large.mem"
    words = [index & 0xFF for index in range(600)]
    rom.write_text("".join(f"{word:02x}\n" for word in words), encoding="ascii")

    literal = generator._packed_literal(rom, word_bits=8, expected_words=len(words))

    assert literal.startswith("{\n")
    assert max(len(line) for line in literal.splitlines()) < 1100
    chunks = [line.strip().rstrip(",") for line in literal.splitlines()[1:-1]]
    recovered_hex = "".join(chunk.split("'h", 1)[1] for chunk in chunks)
    recovered = [
        int(recovered_hex[index : index + 2], 16)
        for index in range(0, len(recovered_hex), 2)
    ]
    assert recovered == list(reversed(words))
