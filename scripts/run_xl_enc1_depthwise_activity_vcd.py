#!/usr/bin/env python3
"""Generate and verify an RTL VCD for an exact XL enc1.depthwise trace."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from run_xl_actor_activity_vcd import assert_cocotb_results_passed

from eventspikeseg.asic.activity_trace import sha256_file, validate_trace_payload

ROOT = Path(__file__).resolve().parents[1]
ACTOR = "enc1.depthwise"


def validate_trace(trace_path: Path, model_spec: Path, checkpoint: Path, event_file: Path) -> dict:
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    validate_trace_payload(trace)
    expected = {
        "actor": ACTOR,
        "model_spec_sha256": sha256_file(model_spec),
        "checkpoint_sha256": sha256_file(checkpoint),
        "event_file_sha256": sha256_file(event_file),
        "bins": 10,
        "input_channels": 32,
        "input_width": 3,
        "input_height": 3,
        "input_vector_bits": 288,
        "output_channels": 32,
    }
    observed = {key: trace.get(key) for key in expected}
    if observed != expected:
        raise ValueError(f"enc1.depthwise trace mismatch: expected={expected}, observed={observed}")
    if trace.get("scope") != "single_coordinate_checkpoint_exact_integer_actor_trace":
        raise ValueError("actor trace does not have the required exact scope")
    return trace


def main() -> None:
    from cocotb.runner import get_runner

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--export", type=Path, default=Path("artifacts/ASIC_XL"))
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--event-file", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/ASIC_XL/activity/enc1_depthwise_1x1"),
    )
    args = parser.parse_args()
    model_spec = args.export / "model_spec.yaml"
    trace = validate_trace(args.trace, model_spec, args.checkpoint, args.event_file)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_top = output_dir / "enc1_depthwise_1x1_activity_top.sv"
    from generate_resident_tile_pnr_top import generate_tile_top

    generate_tile_top(model_spec, generated_top, actor_name=ACTOR, tile_width=1, tile_height=1)
    wrapper = output_dir / "enc1_depthwise_1x1_activity_tb.sv"
    wrapper.write_text(
        "`timescale 1ns/1ps\n"
        "module xl_enc1_depthwise_activity_tb (\n"
        "  input logic clk, input logic reset,\n"
        "  input logic presynaptic_valid_i, output logic presynaptic_ready_o,\n"
        "  input logic [287:0] presynaptic_spike_vector_i,\n"
        "  input logic completion_valid_i, output logic completion_ready_o,\n"
        "  input logic [23:0] completion_tag_i,\n"
        "  output logic result_valid_o, input logic result_ready_i,\n"
        "  output logic [31:0] spike_vector_o,\n"
        "  output logic [23:0] completion_tag_o, output logic error_o);\n"
        "  resident_actor_tile_pnr_top dut (.*);\n"
        "  initial begin\n"
        "    $dumpfile(\"enc1_depthwise_1x1_activity.vcd\");\n"
        "    $dumpvars(1, dut);\n"
        "    $dumpvars(1, dut.actor.ordinary.population);\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )
    sources = [
        ROOT / "asic/rtl/resident_convolution_synapses.sv",
        ROOT / "asic/rtl/resident_plif_population.sv",
        ROOT / "asic/rtl/retinotopic_mechanism_update.sv",
        ROOT / "asic/rtl/resident_retinotopic_plif_population.sv",
        ROOT / "asic/rtl/resident_channelized_plif_actor.sv",
        generated_top,
        wrapper,
    ]
    runner = get_runner("icarus")
    runner.build(
        verilog_sources=sources,
        hdl_toplevel="xl_enc1_depthwise_activity_tb",
        build_dir=output_dir / "sim_build",
        always=True,
        build_args=["-g2012"],
    )
    copied_test = output_dir / "test_xl_actor_trace_vcd.py"
    # The project source is mounted read-only in guarded replay containers.
    # copy2 preserves that source mode, so remove an earlier copied test before
    # refreshing it instead of attempting to overwrite a read-only inode.
    copied_test.unlink(missing_ok=True)
    shutil.copy2(
        ROOT / "verification/cocotb/test_xl_actor_trace_vcd.py",
        copied_test,
    )
    environment = dict(os.environ)
    environment["EVENTSPIKESEG_ACTOR_TRACE"] = str(args.trace.resolve())
    environment["EVENTSPIKESEG_ACTOR"] = ACTOR
    results = output_dir / "results.xml"
    results.unlink(missing_ok=True)
    runner.test(
        hdl_toplevel="xl_enc1_depthwise_activity_tb",
        test_module="test_xl_actor_trace_vcd",
        test_dir=output_dir,
        extra_env=environment,
    )
    assert_cocotb_results_passed(results)
    vcd = output_dir / "enc1_depthwise_1x1_activity.vcd"
    if not vcd.is_file() or vcd.stat().st_size == 0:
        raise RuntimeError(f"simulation passed without producing {vcd}")
    print(
        f"verified {trace['bins']}-bin exact enc1.depthwise VCD: {vcd} "
        f"({vcd.stat().st_size} bytes)"
    )


if __name__ == "__main__":
    main()
