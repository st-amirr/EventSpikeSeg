"""Bridge measured GF180 analog-neuron SPIKE outputs into the routed 128-page RTL."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DAT = ROOT / "artifacts/analog_asic/results/gf180_five_module_parent_nominal_srcf6f1e759f510.dat"
DECK = ROOT / "artifacts/analog_asic/benches/gf180_five_module_parent_nominal_srcf6f1e759f510.spice"
PAGE_RTL = ROOT / "asic/analog/gf180_analog_spike_event_page128_v1.sv"
BANK_RTL = ROOT / "asic/analog/gf180_analog_spike_event_serializer32_v1.sv"
MERGE_RTL = ROOT / "asic/analog/gf180_analog_binary_event_merge_sorted2.sv"
OUT_TB = ROOT / "artifacts/analog_asic/benches/gf180_neuron_spike_to_page128_v1_tb.sv"
OUT_LOG = ROOT / "artifacts/analog_asic/benches/gf180_neuron_spike_to_page128_v1.log"
OUT_JSON = ROOT / "artifacts/analog_asic/results/gf180_neuron_spike_to_page128_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measured_spikes(sample_time_s: float = 1043.5e-6) -> dict[str, float]:
    with DAT.open(encoding="ascii") as f:
        header = f.readline().split()
        indices = {name: header.index(f"v(spike_{name})") for name in ("near", "high", "low")}
        best_dt = float("inf")
        best: dict[str, float] = {}
        for line in f:
            parts = line.split()
            if not parts:
                continue
            t = float(parts[0])
            dt = abs(t - sample_time_s)
            if dt < best_dt:
                best_dt = dt
                best = {name: float(parts[index]) for name, index in indices.items()}
    if not best or best_dt > 1e-7:
        raise RuntimeError(f"No analog sample near requested time; nearest delta={best_dt:g}s")
    return best


def make_tb(bitmap: int) -> str:
    return f'''`timescale 1ns/1ps
module gf180_neuron_spike_to_page128_v1_tb;
  logic clk=0, reset=1;
  logic page_valid_i=0, page_ready_o;
  logic [25:0] page_base_i=26'd4000;
  logic [127:0] spike_bitmap_i=128'h{bitmap:032x};
  logic [7:0] lane_count_i=8'd128;
  logic page_last_i=1;
  logic [23:0] page_bin_tag_i=24'd91;
  logic event_valid_o, event_ready_i=1;
  logic [25:0] event_address_o;
  logic event_completion_o;
  logic [23:0] event_bin_tag_o;
  logic page_format_error_o, address_order_error_o, tag_mismatch_o;
  integer observed=0;
  integer completed=0;
  always #10 clk=~clk;
  gf180_analog_spike_event_page128_v1 dut (.*);
  always @(posedge clk) begin
    if (reset) begin observed=0; completed=0; end
    else if (event_valid_o && event_ready_i) begin
      if (event_bin_tag_o!==page_bin_tag_i) $fatal(1,"analog event bin tag changed");
      if (event_completion_o) completed=completed+1;
      else begin
        if (observed!=0 || event_address_o!==26'd4001)
          $fatal(1,"analog spike event address/order mismatch: %0d",event_address_o);
        observed=observed+1;
      end
    end
  end
  initial begin
    repeat(2) @(negedge clk); reset=0;
    while (!page_ready_o) @(negedge clk);
    page_valid_i=1;
    @(posedge clk); @(negedge clk); page_valid_i=0;
    repeat(100) begin
      if (completed==1) begin
        if (observed!=1 || page_format_error_o || address_order_error_o || tag_mismatch_o)
          $fatal(1,"analog-to-page completion had malformed results");
        $display("gf180_neuron_spike_to_page128_v1_tb PASS");
        $finish;
      end
      @(negedge clk);
    end
    $fatal(1,"analog-to-page event completion timeout");
  end
endmodule
'''


def main() -> None:
    if OUT_JSON.exists():
        raise FileExistsError(OUT_JSON)
    analog = measured_spikes()
    cmos_vih = 2.31  # 0.7 * 3.3 V; conservative GF180 CMOS high-level boundary.
    bitmap = sum((1 << lane) for lane, name in enumerate(("near", "high", "low"))
                 if analog[name] >= cmos_vih)
    expected_bitmap = 1 << 1
    if bitmap != expected_bitmap:
        raise RuntimeError(f"Unexpected measured analog decision bitmap {bitmap:#x}")
    OUT_TB.write_text(make_tb(bitmap), encoding="ascii")
    docker_root = str(ROOT)
    cmd = [
        "docker", "run", "--rm", "--network", "bridge", "--memory", "2g", "--cpus", "2",
        "--volume", f"{docker_root}:/workspace", "--workdir", "/workspace",
        "--entrypoint", "bash", "eventspikeseg:analog-ngspice47", "-lc",
        "apt-get update -qq && apt-get install -y -qq iverilog >/dev/null && "
        "iverilog -g2012 -s gf180_neuron_spike_to_page128_v1_tb "
        "-o /workspace/artifacts/analog_asic/benches/gf180_neuron_spike_to_page128_v1_tb.vvp "
        "/workspace/asic/analog/gf180_analog_spike_event_serializer32_v1.sv "
        "/workspace/asic/analog/gf180_analog_binary_event_merge_sorted2.sv "
        "/workspace/asic/analog/gf180_analog_spike_event_page128_v1.sv "
        "/workspace/artifacts/analog_asic/benches/gf180_neuron_spike_to_page128_v1_tb.sv && "
        "vvp /workspace/artifacts/analog_asic/benches/gf180_neuron_spike_to_page128_v1_tb.vvp",
    ]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    log = run.stdout + run.stderr
    OUT_LOG.write_text(log, encoding="utf-8")
    passed = run.returncode == 0 and "gf180_neuron_spike_to_page128_v1_tb PASS" in log
    report = {
        "design": "gf180_neuron_spike_to_page128_v1",
        "status": "PASS" if passed else "FAIL",
        "scope": "Bounded analog-to-categorical co-simulation: three output voltages from the existing physically routed five-module GF180 neuron parent are classified at 0.7*VDD, then injected as a comparator bitmap into the routed 128-neuron page RTL.",
        "analog_source": "artifacts/analog_asic/results/gf180_five_module_parent_nominal_srcf6f1e759f510.json",
        "sample_time_us": 1043.5,
        "supply_v": 3.3,
        "logic_high_boundary_v": cmos_vih,
        "measured_spike_output_v": analog,
        "classified_bitmap_hex": f"0x{bitmap:032x}",
        "expected_event_address": 4001,
        "simulator": "Icarus Verilog (installed in ephemeral eventspikeseg:analog-ngspice47 container)",
        "simulation_pass": passed,
        "limitations": [
            "The analog voltage samples come from three independent characterization arms, not a 128-channel loaded analog actor.",
            "The 0.7*VDD threshold models the CMOS input-high boundary; mixed-signal parasitics at the actual analog-to-digital pin are not extracted.",
            "This proves interface semantics only; it does not make the analog comparator bank physically connected to the routed page or close the full graph, accuracy, or 5 ms service gates."
        ],
        "evidence": {
            "analog_deck_sha256": sha(DECK),
            "analog_waveform_sha256": sha(DAT),
            "neuron_page_rtl_sha256": sha(PAGE_RTL),
            "serializer_rtl_sha256": sha(BANK_RTL),
            "merge_rtl_sha256": sha(MERGE_RTL),
            "testbench_sha256": sha(OUT_TB),
        },
    }
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "evidence"}, indent=2))
    if not passed:
        raise SystemExit(run.returncode or 1)


if __name__ == "__main__":
    main()
