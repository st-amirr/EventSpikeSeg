#!/usr/bin/env python3
"""Prepare and validate the checkpoint-exact enc1.depthwise gate-power flow."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from eventspikeseg.asic.activity_trace import sha256_file, validate_trace_payload


def validate_trace(
    trace_path: Path, model_spec: Path, checkpoint: Path, event_file: Path
) -> dict:
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    validate_trace_payload(trace)
    expected = {
        "actor": "enc1.depthwise",
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
        raise ValueError(f"enc1.depthwise trace mismatch: {observed}")
    if trace.get("scope") != "single_coordinate_checkpoint_exact_integer_actor_trace":
        raise ValueError("actor trace does not have the required exact scope")
    return trace


def require_nonempty(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"required non-empty artifact is missing: {path}")


def require_passing_rtl_results(path: Path) -> None:
    require_nonempty(path)
    root = ET.parse(path).getroot()
    testcases = root.findall(".//testcase")
    failures = root.findall(".//failure")
    errors = root.findall(".//error")
    if not testcases or failures or errors:
        raise ValueError(
            "RTL replay must pass before gate replay: "
            f"testcases={len(testcases)}, failures={len(failures)}, errors={len(errors)}"
        )


def make_testbench(trace: dict, sdf_name: str) -> str:
    inputs = trace["input_vectors_hex"]
    outputs = trace["expected_output_vectors_hex"]
    if len(inputs) != 10 or len(outputs) != 10:
        raise ValueError("gate replay requires exactly ten paired vectors")
    body: list[str] = []
    for index, (input_hex, output_hex) in enumerate(zip(inputs, outputs), start=1):
        body.append(
            f"    replay_bin(24'd{index}, 288'h{input_hex}, 32'h{output_hex});"
        )
    return f"""`timescale 1ns/1ps
module xl_enc1_depthwise_gate_tb;
  reg clk = 0;
  reg reset = 1;
  reg presynaptic_valid_i = 0;
  reg [287:0] presynaptic_spike_vector_i = 0;
  reg completion_valid_i = 0;
  reg [23:0] completion_tag_i = 0;
  reg result_ready_i = 0;
  wire presynaptic_ready_o, completion_ready_o, result_valid_o, error_o;
  wire [31:0] spike_vector_o;
  wire [23:0] completion_tag_o;
  integer cycles = 0;

  resident_actor_tile_pnr_top dut (.*);
  always #2.5 clk = ~clk;

  task tick;
    begin
      @(posedge clk); #1; cycles = cycles + 1;
      if (cycles > 200000) $fatal(1, "gate replay timeout");
      if (!reset &&
          ((presynaptic_ready_o !== 1'b0 && presynaptic_ready_o !== 1'b1) ||
           (completion_ready_o !== 1'b0 && completion_ready_o !== 1'b1) ||
           (result_valid_o !== 1'b0 && result_valid_o !== 1'b1) ||
           (error_o !== 1'b0 && error_o !== 1'b1)))
        $fatal(1, "X/Z on gate control outputs at cycle %0d", cycles);
    end
  endtask

  task replay_bin;
    input [23:0] tag;
    input [287:0] stimulus;
    input [31:0] expected;
    begin
      if (stimulus != 0) begin
        while (presynaptic_ready_o !== 1'b1) tick();
        @(negedge clk);
        presynaptic_spike_vector_i = stimulus;
        presynaptic_valid_i = 1;
        tick();
        @(negedge clk);
        presynaptic_valid_i = 0;
        presynaptic_spike_vector_i = 0;
      end
      while (completion_ready_o !== 1'b1) tick();
      @(negedge clk);
      completion_tag_i = tag;
      completion_valid_i = 1;
      tick();
      @(negedge clk);
      completion_valid_i = 0;
      while (result_valid_o !== 1'b1) tick();
      if ((^completion_tag_o === 1'bx) || (^spike_vector_o === 1'bx) ||
          (error_o !== 1'b0 && error_o !== 1'b1))
        $fatal(1, "X/Z in bin %0d result", tag);
      if (completion_tag_o !== tag)
        $fatal(1, "tag mismatch bin %0d: got %0d", tag, completion_tag_o);
      if (spike_vector_o !== expected)
        $fatal(1, "output mismatch bin %0d: got %h expected %h",
               tag, spike_vector_o, expected);
      if (error_o !== 1'b0) $fatal(1, "error_o asserted in bin %0d", tag);
      result_ready_i = 1;
      tick();
      @(negedge clk); result_ready_i = 0;
    end
  endtask

  initial begin
    $dumpfile("enc1_depthwise_beta48_gate.vcd");
    $dumpvars(0, dut);
`ifdef ENABLE_SDF
    $sdf_annotate("{sdf_name}", dut);
`endif
    repeat (3) tick();
    @(negedge clk); reset = 0;
{chr(10).join(body)}
    $display("GATE_REPLAY_PASS vectors=10 cycles=%0d", cycles);
    $finish;
  end
endmodule
"""


def validate_simulation(log_path: Path, vcd_path: Path) -> dict:
    require_nonempty(log_path)
    require_nonempty(vcd_path)
    log = log_path.read_text(encoding="utf-8", errors="replace")
    if "GATE_REPLAY_PASS vectors=10" not in log:
        raise ValueError("gate simulator did not report ten-vector equivalence")
    forbidden = [r"\bFATAL\b", r"output mismatch", r"tag mismatch", r"X/Z"]
    hits = [pattern for pattern in forbidden if re.search(pattern, log, re.I)]
    if hits:
        raise ValueError(f"gate replay log contains failure indicators: {hits}")
    warnings = len(re.findall(r"SDF.*warning|warning.*SDF", log, re.I))
    errors = len(re.findall(r"SDF.*error|error.*SDF", log, re.I))
    if errors:
        raise ValueError(f"SDF annotation reported {errors} errors")
    return {"vectors": 10, "vcd_bytes": vcd_path.stat().st_size,
            "sdf_warnings": warnings, "sdf_errors": errors}


def validate_sdf(log_path: Path, sdf_path: Path) -> dict:
    require_nonempty(log_path)
    require_nonempty(sdf_path)
    log = log_path.read_text(encoding="utf-8", errors="replace")
    if "SDF_GENERATION_PASS" not in log:
        raise ValueError("OpenROAD SDF generation did not reach its success marker")
    if re.search(r"\[ERROR\b|\bError:", log):
        raise ValueError("OpenROAD reported an error while generating SDF")
    sdf = sdf_path.read_text(encoding="utf-8", errors="replace")
    if '(DESIGN "resident_actor_tile_pnr_top")' not in sdf:
        raise ValueError("SDF design does not match the beta48 routed top")
    if "(TIMESCALE 1ps)" not in sdf:
        raise ValueError("SDF does not declare the expected 1 ps time scale")
    cells = len(re.findall(r"(?m)^\s*\(CELL\s*$", sdf))
    if cells < 2:
        raise ValueError(f"SDF contains too few CELL records: {cells}")
    return {"sdf_bytes": sdf_path.stat().st_size, "cell_records": cells,
            "design": "resident_actor_tile_pnr_top", "timescale": "1ps"}


def annotation_percentages(report: str) -> list[float]:
    values: list[float] = []
    for line in report.splitlines():
        if "annotat" not in line.lower():
            continue
        values.extend(float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", line))
    return values


def validate_power(log_path: Path, report_path: Path, annotation_path: Path) -> dict:
    require_nonempty(log_path)
    require_nonempty(report_path)
    require_nonempty(annotation_path)
    log = log_path.read_text(encoding="utf-8", errors="replace")
    report = report_path.read_text(encoding="utf-8", errors="replace")
    if "ACTIVITY_POWER_PASS" not in log:
        raise ValueError("OpenROAD activity-power run did not reach its success marker")
    if not re.search(r"Total", report, re.I):
        raise ValueError("power report has no total row")
    if re.search(r"read_vcd.*(error|failed)|error.*read_vcd", log, re.I):
        raise ValueError("OpenROAD failed to read the gate VCD")
    annotation = annotation_path.read_text(encoding="utf-8", errors="replace")
    percentages = annotation_percentages(annotation)
    if percentages:
        minimum_coverage = min(percentages)
    else:
        mapped_match = re.search(r"(?m)^vcd\s+(\d+)\s*$", annotation)
        missing_match = re.search(r"(?m)^unannotated\s+(\d+)\s*$", annotation)
        if mapped_match is None or missing_match is None:
            raise ValueError("activity annotation report has no mapped coverage data")
        mapped = int(mapped_match.group(1))
        missing = int(missing_match.group(1))
        if mapped + missing == 0:
            raise ValueError("activity annotation report contains no pins")
        minimum_coverage = 100.0 * mapped / (mapped + missing)
    if minimum_coverage < 90.0:
        raise ValueError(f"gate VCD annotation coverage is too low: {minimum_coverage}%")
    return {"scope": "checkpoint_exact_single_coordinate_enc1_depthwise_partition",
            "power_report_bytes": report_path.stat().st_size,
            "minimum_annotation_percent": minimum_coverage}


def prepare(args: argparse.Namespace) -> None:
    for path in (args.odb, args.spef, args.sdc, args.netlist):
        require_nonempty(path)
    require_passing_rtl_results(args.rtl_results)
    trace = validate_trace(args.trace, args.model_spec, args.checkpoint, args.event_file)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "xl_enc1_depthwise_gate_tb.sv").write_text(
        make_testbench(trace, "sim_models/enc1_depthwise_beta48_iverilog.sdf"),
        encoding="utf-8",
    )
    manifest = {
        "scope": "checkpoint_exact_single_coordinate_enc1_depthwise_partition",
        "actor": "enc1.depthwise", "vectors": 10, "clock_period_ns": 5.0,
        "trace": str(args.trace.resolve()), "odb": str(args.odb.resolve()),
        "spef": str(args.spef.resolve()), "sdc": str(args.sdc.resolve()),
        "netlist": str(args.netlist.resolve()),
        "trace_payload_sha256": trace["trace_payload_sha256"],
        "odb_sha256": sha256_file(args.odb),
        "spef_sha256": sha256_file(args.spef),
        "sdc_sha256": sha256_file(args.sdc),
        "netlist_sha256": sha256_file(args.netlist),
        "gate_replay_timing_mode": "post_route_functional_zero_delay",
        "timing_authority": "extracted OpenSTA setup/hold with routed SPEF",
        "claim_limit": "one routed 1x1 enc1.depthwise partition at one exact coordinate",
    }
    (args.output_dir / "flow_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    for name in ("trace", "model-spec", "checkpoint", "event-file", "odb", "spef",
                 "sdc", "netlist", "rtl-results", "output-dir"):
        prep.add_argument(f"--{name}", type=Path, required=True)
    sim = sub.add_parser("validate-sim")
    sim.add_argument("--log", type=Path, required=True)
    sim.add_argument("--vcd", type=Path, required=True)
    sdf = sub.add_parser("validate-sdf")
    sdf.add_argument("--log", type=Path, required=True)
    sdf.add_argument("--sdf", type=Path, required=True)
    power = sub.add_parser("validate-power")
    power.add_argument("--log", type=Path, required=True)
    power.add_argument("--report", type=Path, required=True)
    power.add_argument("--annotation-report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    elif args.command == "validate-sim":
        print(json.dumps(validate_simulation(args.log, args.vcd), indent=2))
    elif args.command == "validate-sdf":
        print(json.dumps(validate_sdf(args.log, args.sdf), indent=2))
    else:
        print(json.dumps(validate_power(
            args.log, args.report, args.annotation_report
        ), indent=2))


if __name__ == "__main__":
    main()
