"""Compare signed SKY130 MOS pulse injection into small and extracted gate banks."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_DIR = ROOT / "artifacts/analog_asic/layout/sky130_mos_gate_bank_100x10_nf10"
OUT = ROOT / "artifacts/analog_asic/results/sky130_mos_gate_bank_signed_event.json"
BENCH = ROOT / "artifacts/analog_asic/benches/sky130_mos_gate_bank_signed_event.cir"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
CELL = "mos_gate_bank_100x10_nf10"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    lines = [
        "* SKY130 MOS injector into a 10-unit extracted MOS gate bank, TT/27C",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2 gmin=1e-12",
        ".temp 27",
        f'.include "{MODEL}/models/parameters/invariant.spice"',
        f'.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"',
        f'.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        f'.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "/workspace/artifacts/analog_asic/layout/{LAYOUT_DIR.name}/{CELL}.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
        ".subckt diff_inject vp vn pp np pn nn vdd vss params: geom=1",
        "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
        "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
        "Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
        "Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
        ".ends diff_inject",
    ]
    cap_check = ROOT / "artifacts/analog_asic/benches/sky130_mos_gate_bank_scale_check.cir"
    cap_lines = ["* Check extracted MOS dimensions under the event deck global scale option",
        ".option scale=1u", ".temp 27",
        f'.include "{MODEL}/models/parameters/invariant.spice"',
        f'.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"',
        f'.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "/workspace/artifacts/analog_asic/layout/{LAYOUT_DIR.name}/{CELL}.spice"',
        "Vcm cm 0 0.9", "Vgate gate 0 dc 0.9 ac 1", f"Xcap gate 0 0 {CELL}",
        "Vgsmall gsmall 0 dc 0.9 ac 1"]
    cap_lines += [f"Xsm{i} 0 gsmall 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1" for i in range(10)]
    cap_lines += [".control", "set numdgt=15", "ac lin 1 1meg 1meg",
                  "let cgate=abs(imag(i(Vgate)))/(2*pi*frequency)",
                  "let csmall=abs(imag(i(Vgsmall)))/(2*pi*frequency)",
                  "print cgate", "print csmall", "quit", ".endc", ".end", ""]
    cap_check.write_text("\n".join(cap_lines), encoding="ascii")
    cap_proc = subprocess.run(["docker", "run", "--rm", "-v", f"{ROOT}:/workspace", "-w", "/workspace",
                               "--entrypoint", "ngspice", IMAGE, "-b",
                               f"/workspace/artifacts/analog_asic/benches/{cap_check.name}"],
                              capture_output=True, text=True, timeout=150, cwd=ROOT)
    cap_log = cap_proc.stdout + cap_proc.stderr
    cap_match = re.search(r"\bcgate\s*=\s*([-+0-9.eE]+)", cap_log, re.I)
    small_cap_match = re.search(r"\bcsmall\s*=\s*([-+0-9.eE]+)", cap_log, re.I)
    if cap_proc.returncode or not cap_match or not small_cap_match:
        raise RuntimeError(f"Scaled extracted-cap AC check failed:\n{cap_log[-3000:]}")
    extracted_cap_scaled_f = float(cap_match.group(1))
    small_cap_f = float(small_cap_match.group(1))
    cases = ("large_pos", "large_neg", "small_pos", "small_neg")
    pulse_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                           if arg.startswith("--pulse-ns=")), "42.2657"))
    rise_ns, fraction = 2.0, 0.9
    event_end_us = 3.0 + pulse_ns/1000 + 0.02
    p_on, n_on = 1.8 - fraction * 1.08, fraction * 0.6
    for tag in cases:
        vp, vn = f"vp_{tag}", f"vn_{tag}"
        if tag.startswith("large"):
            lines += [f"Xcap_{tag}_p {vp} 0 0 {CELL}",
                      f"Xcap_{tag}_n {vn} 0 0 {CELL}"]
        else:
            for index in range(10):
                lines += [f"Xcap_{tag}_p{index} 0 {vp} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1",
                          f"Xcap_{tag}_n{index} 0 {vn} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1"]
        lines += [f"Vinitp_{tag} initp_{tag} 0 PWL(0 0.9 3.1u 0.9)",
                  f"Vinitn_{tag} initn_{tag} 0 PWL(0 0.9 3.1u 0.9)",
                  f"Sinitp_{tag} initp_{tag} {vp} init_{tag} 0 sw_init",
                  f"Sinitn_{tag} initn_{tag} {vn} init_{tag} 0 sw_init",
                  f"Vinit_{tag} init_{tag} 0 PWL(0 1.8 2.999u 1.8 3u 0 3.1u 0)"]
        lines.append(f"Xinj_{tag} {vp} {vn} pp_{tag} np_{tag} pn_{tag} nn_{tag} vdd 0 diff_inject params: geom=1")
        positive = tag.endswith("pos")
        gates = {"pp": p_on if positive else 1.8,
                 "nn": n_on if positive else 0.0,
                 "pn": p_on if not positive else 1.8,
                 "np": n_on if not positive else 0.0}
        for pin, active in gates.items():
            off = 1.8 if pin in ("pp", "pn") else 0.0
            start = 3.0
            t1 = start + rise_ns / 1000
            t2 = start + pulse_ns / 1000
            t3 = t2 + rise_ns / 1000
            node = f"{pin}_{tag}"
            lines.append(f"V{node} {node} 0 PWL(0 {off} 2.999u {off} {t1:.9g}u {active:.12g} "
                         f"{t2:.9g}u {active:.12g} {t3:.9g}u {off} {event_end_us:g}u {off})")
    lines += [".model sw_init SW(Ron=10 Roff=1e15 Vt=0.9 Vh=0.1)", ".ic " + " ".join(
        f"v(vp_{tag})=0.9 v(vn_{tag})=0.9" for tag in cases),
        ".control", "set numdgt=15", f"tran 0.5n {event_end_us:g}u 0 0.5n uic"]
    for tag in cases:
        lines += [f"let diff_{tag}=v(vp_{tag})-v(vn_{tag})",
                  f"meas tran {tag} find diff_{tag} at={event_end_us:g}u",
                  f"meas tran vp_{tag}_end find v(vp_{tag}) at={event_end_us:g}u",
                  f"meas tran vn_{tag}_end find v(vn_{tag}) at={event_end_us:g}u",
                  f"meas tran vp_{tag}_before find v(vp_{tag}) at=2.9u",
                  f"meas tran vn_{tag}_before find v(vn_{tag}) at=2.9u"]
    lines += ["quit", ".endc", ".end", ""]
    BENCH.parent.mkdir(parents=True, exist_ok=True)
    BENCH.write_text("\n".join(lines), encoding="ascii")
    proc = subprocess.run(["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
                           "-v", f"{ROOT}:/workspace", "-w", "/workspace",
                           "--entrypoint", "ngspice", IMAGE, "-b",
                           f"/workspace/artifacts/analog_asic/benches/{BENCH.name}"],
                          capture_output=True, text=True, timeout=180, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (OUT.parent / "results").mkdir(parents=True, exist_ok=True)
    (OUT.with_suffix(".log")).write_text(log, encoding="utf-8")
    values = {name.lower(): float(value) for name, value in re.findall(
        r"(?im)^\s*(large_pos|large_neg|small_pos|small_neg)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(values) != set(cases):
        raise RuntimeError(f"Signed event comparison failed:\n{log[-5000:]}")
    rows = {tag: {"signed_state_step_v": values[tag], "measured_abs_step_v": abs(values[tag]),
                  "polarity_correct": (values[tag] > 0 if tag.endswith("pos") else values[tag] < 0)}
            for tag in cases}
    report = {"test": "sky130_extracted_mos_gate_bank_signed_event_transfer",
              "corner": "tt", "temperature_c": 27, "injector_geometry_factor": 1,
              "pulse_width_ns": pulse_ns, "gate_fraction": fraction,
              "measurement_time_us": event_end_us,
              "initial_differential_v": 0, "initial_common_mode_v": 0.9,
              "large_bank_extracted_capacitance_f": 74.8442682833e-12,
              "large_bank_capacitance_with_option_scale_f": extracted_cap_scaled_f,
              "small_reference_capacitance_with_option_scale_f": small_cap_f,
              "small_reference_cap_geometry_um2_per_rail": 100,
              "all_storage_capacitor_source_drain_bulk_nodes_v": 0.0,
              "rows": rows,
              "large_to_small_step_ratio": abs(values["large_pos"]/values["small_pos"]),
              "node_voltage_samples": {key.lower(): float(value) for key, value in re.findall(
                  r"(?im)^\s*(vp_(?:large|small)_(?:pos|neg)_(?:end|before)|vn_(?:large|small)_(?:pos|neg)_(?:end|before))\s*=\s*([-+0-9.eE]+)", log)},
              "simulation_completed": True,
              "limitations": ["ideal voltage initialization", "schematic MOS injector, no layout or extraction",
                              "no event sequences, 5ms retention, sampled noise, mismatch or PVT"]}
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
