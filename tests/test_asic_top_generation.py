from __future__ import annotations

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
    graph = topology.eventspikeseg140k_graph_contract()
    layers = []
    for index, name in enumerate(graph["actor_topological_order"]):
        safe = name.replace(".", "_")
        weight = tmp_path / f"{index:02d}_{safe}.mem"
        beta = tmp_path / f"{index:02d}_{safe}_beta.mem"
        threshold = tmp_path / f"{index:02d}_{safe}_threshold.mem"
        parameters = tmp_path / f"{index:02d}_{safe}.json"
        weight.write_text("01\n", encoding="ascii")
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
                "input_hw": [1, 1],
                "output_hw": [1, 1],
                "in_channels": 1,
                "out_channels": 1,
                "kernel": [1, 1],
                "stride": [1, 1],
                "padding": [0, 0],
                "dilation": [1, 1],
                "groups": 1,
                "weight_count": 1,
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
            "input_hw": [1, 1],
            "output_hw": [1, 1],
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
    generator.generate_top(model_spec, generated, module_name="generated_mini_dag")
    text = generated.read_text(encoding="utf-8")
    assert text.count("streaming_channelized_plif_actor #(") == 25
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
