"""Measure MOS-state transfer with the full shared 13-geometry injector bank loaded."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
CHECKPOINT = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
EXPECTED_SHA = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
LAYOUT_BANK = "--extracted-layout-bank" in sys.argv[1:]
LAYOUT_CELL = "sky130_mos_gate_bank_100x10_nf10"
LAYOUT_SUBCKT = "mos_gate_bank_100x10_nf10"
ALL_GEOMETRIES = (0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0)
ALL_FRACTIONS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)
GEOMETRIES = tuple(float(x) for x in next((a.split("=", 1)[1] for a in sys.argv[1:]
                       if a.startswith("--geometry-selection=")), ",".join(map(str, ALL_GEOMETRIES))).split(","))
FRACTIONS = tuple(float(x) for x in next((a.split("=", 1)[1] for a in sys.argv[1:]
                       if a.startswith("--fractions=")), ",".join(map(str, ALL_FRACTIONS))).split(","))
POLARITIES = tuple(next((a.split("=", 1)[1] for a in sys.argv[1:]
                         if a.startswith("--polarities=")), "p"))
if any(g not in ALL_GEOMETRIES for g in GEOMETRIES) or any(f not in ALL_FRACTIONS for f in FRACTIONS):
    raise ValueError("geometry/fraction selections must use the characterized grid")
if not POLARITIES or any(p not in "pn" for p in POLARITIES):
    raise ValueError("polarities must be p and/or n")
PULSE_NS = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                       if arg.startswith("--pulse-width-ns=")),
                      "4400" if LAYOUT_BANK else "42.2657"))
if not 2.5 <= PULSE_NS <= 4400.0:
    raise ValueError("pulse width must be within 2.5..4400ns")
RISE_NS = 2.0
MEASURE_US = 3.0 + PULSE_NS / 1000 + 0.02
STOP_US = MEASURE_US + 0.05 if LAYOUT_BANK else 3.1

HEADER = """SKY130 SS/0C MOS state transfer with shared injector bank
.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2 gmin=1e-12
.temp 0
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__ss.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__ss.corner.spice"
.include "../../../asic/analog/modules.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""
if LAYOUT_BANK:
    HEADER += f'\n.include "../layout/{LAYOUT_CELL}/{LAYOUT_SUBCKT}.spice"\n'


def add_cap(lines: list[str], tag: str, vp: str, vn: str) -> None:
    if LAYOUT_BANK:
        lines.extend((f"Xcap_{tag}_p {vp} vcm 0 {LAYOUT_SUBCKT}",
                      f"Xcap_{tag}_n {vn} vcm 0 {LAYOUT_SUBCKT}"))
    else:
        lines.extend(f"Xcap_{tag}_{side}{finger} 0 {node} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1"
                     for side, node in (("p", vp), ("n", vn)) for finger in range(10))


def add_sample(lines: list[str], tag: str, vp: str, vn: str, state_diff_mv: float) -> None:
    vpos, vneg = 0.9 + state_diff_mv * 0.0005, 0.9 - state_diff_mv * 0.0005
    lines += [f"Vinitp_{tag} initp_{tag} 0 {vpos:.12g}",
              f"Vinitn_{tag} initn_{tag} 0 {vneg:.12g}",
              f"Vcl_{tag} cl_{tag} 0 PWL(0 1.8 2.99u 1.8 2.991u 0 {STOP_US}u 0)",
              f"Vclb_{tag} clb_{tag} 0 PWL(0 0 2.99u 0 2.991u 1.8 {STOP_US}u 1.8)",
              f"Xcl_p_{tag} initp_{tag} {vp} cl_{tag} clb_{tag} vdd 0 transmission_gate",
              f"Xcl_n_{tag} initn_{tag} {vn} cl_{tag} clb_{tag} vdd 0 transmission_gate"]


def deck(cases: list[dict], state_diff_mv: float) -> str:
    lines = [HEADER]
    bank_pins = [f"{pin}{index}" for index in range(len(ALL_GEOMETRIES))
                 for pin in ("pp", "np", "pn", "nn")]
    lines.append(".subckt diff_inject vp vn " + " ".join(bank_pins) + " vdd vss")
    for index, geometry in enumerate(ALL_GEOMETRIES):
        lines += [f"Xp_pos{index} vp pp{index} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geometry:g} l=10",
                  f"Xn_neg{index} vn nn{index} vss vss sky130_fd_pr__nfet_01v8 w={geometry:g} l=10",
                  f"Xp_neg{index} vn pn{index} vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geometry:g} l=10",
                  f"Xn_pos{index} vp np{index} vss vss sky130_fd_pr__nfet_01v8 w={geometry:g} l=10"]
    lines.append(".ends diff_inject")
    add_cap(lines, "ref", "vp_ref", "vn_ref")
    add_sample(lines, "ref", "vp_ref", "vn_ref", state_diff_mv)
    for case in cases:
        tag, geometry, fraction = case["tag"], case["geometry"], case["gate_fraction"]
        vp, vn = f"vp_{tag}", f"vn_{tag}"
        add_cap(lines, tag, vp, vn)
        add_sample(lines, tag, vp, vn, state_diff_mv)
        active_index = ALL_GEOMETRIES.index(geometry)
        p_on, n_on = 1.8 - fraction * 1.08, fraction * 0.6
        t0, t1 = 3.0, 3.0 + RISE_NS / 1000
        t2, t3 = 3.0 + PULSE_NS / 1000, 3.0 + (PULSE_NS + RISE_NS) / 1000
        gate_nodes = []
        active_pins = {"pp", "nn"} if case["polarity"] == "p" else {"pn", "np"}
        for index in range(len(ALL_GEOMETRIES)):
            for pin, mos in (("pp", "p"), ("np", "n"), ("pn", "p"), ("nn", "n")):
                active = ((p_on if mos == "p" else n_on)
                          if index == active_index and pin in active_pins else
                          (1.8 if mos == "p" else 0.0))
                off = 1.8 if mos == "p" else 0.0
                node = f"{pin}{index}_{tag}"
                lines.append(f"V{node} {node} 0 PWL(0 {off} 2.999u {off} {t1:.9g}u {active:.12g} "
                             f"{t2:.9g}u {active:.12g} {t3:.9g}u {off} {STOP_US}u {off})")
                gate_nodes.append(node)
        lines.append(f"Xinj_{tag} {vp} {vn} " + " ".join(gate_nodes) + " vdd 0 diff_inject")
    lines += [".control", "set numdgt=15", f"tran 0.5n {STOP_US}u 0 0.5n uic",
              "let diff_ref=v(vp_ref)-v(vn_ref)"]
    for case in cases:
        tag = case["tag"]
        lines += [f"let diff_{tag}=v(vp_{tag})-v(vn_{tag})",
                  f"let delta_{tag}=diff_{tag}-diff_ref",
                  f"meas tran {tag} find delta_{tag} at={MEASURE_US:.9g}u"]
    lines += ["quit", ".endc", ".end"]
    return "\n".join(lines) + "\n"


def main() -> int:
    if hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest() != EXPECTED_SHA:
        raise RuntimeError("the original full-float checkpoint hash differs")
    if LAYOUT_BANK and not (OUT / "layout" / LAYOUT_CELL / f"{LAYOUT_SUBCKT}.spice").exists():
        raise RuntimeError("the extracted MOS bank must be built before its transfer map")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    state_diff_mv = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                if arg.startswith("--state-diff-mv=")), "0"))
    tag_base = "sky130_ms_mos_state_banked_transfer_ss0_layoutbank" if LAYOUT_BANK else \
               "sky130_ms_mos_state_banked_transfer_ss0"
    default_pulse_ns = 4400.0 if LAYOUT_BANK else 42.2657
    if abs(PULSE_NS - default_pulse_ns) > 0.001:
        tag_base += f"_w{PULSE_NS:g}n".replace(".", "p")
    if (GEOMETRIES != ALL_GEOMETRIES or FRACTIONS != ALL_FRACTIONS or POLARITIES != ("p",)):
        tag_base += "_subsetg" + "-".join(f"{g:g}".replace(".", "p") for g in GEOMETRIES)
        tag_base += "_f" + "-".join(f"{f:g}".replace(".", "p") for f in FRACTIONS)
        tag_base += "_pol" + "".join(POLARITIES)
    if state_diff_mv:
        tag_base += f"_d{state_diff_mv:g}mV".replace("-", "m").replace(".", "p")
    rows = [{"tag": f"g{str(g).replace('.', 'p')}_f{str(f).replace('.', 'p')}_{polarity}",
             "geometry": g, "gate_fraction": f, "polarity": polarity}
            for g in GEOMETRIES for f in FRACTIONS for polarity in POLARITIES]
    batches = []
    # Each branch contains all13 geometries. Four branches per deck bound ngspice memory.
    for batch_index, start in enumerate(range(0, len(rows), 4)):
        batch = rows[start:start + 4]
        deck_name = f"{tag_base}_b{batch_index:02d}.cir"
        (BENCH / deck_name).write_text(deck(batch, state_diff_mv), encoding="utf-8")
        command = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2",
                   "--volume", f"{ROOT}:/workspace:ro",
                   "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
                   "--workdir", "/workspace/artifacts/analog_asic/benches",
                   "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
                   "120", "ngspice", "-b", deck_name]
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=150)
        log = proc.stdout + proc.stderr
        log_name = f"{tag_base}_b{batch_index:02d}.log"
        (RES / log_name).write_text(log, encoding="utf-8")
        measured = {name.lower(): float(value) for name, value in re.findall(
            r"^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)", log, re.I | re.M)}
        for case in batch:
            case["event_delta_v"] = measured.get(case["tag"])
            case["measured"] = case["event_delta_v"] is not None
        done = proc.returncode == 0 and "ngspice-36 done" in log and "Timestep too small" not in log and all(
            case["measured"] for case in batch)
        batches.append({"deck": deck_name, "log": log_name, "return_code": proc.returncode,
                        "case_count": len(batch), "completed": done})
        print(json.dumps({"batch": batch_index + 1, "batch_count": (len(rows) + 3) // 4,
                          "completed": done, "measured": sum(case["measured"] for case in batch)}), flush=True)
    complete = all(batch["completed"] for batch in batches)
    values = {polarity: [[next((case["event_delta_v"] for case in rows
                                if case["geometry"] == geometry and case["gate_fraction"] == fraction
                                and case["polarity"] == polarity), None)
                           for fraction in FRACTIONS] for geometry in GEOMETRIES]
              for polarity in POLARITIES}
    for polarity in ("p", "n"):
        values.setdefault(polarity, [[None for _ in FRACTIONS] for _ in GEOMETRIES])
    if POLARITIES == ("p",):
        values["n"] = [[-value if value is not None else None for value in row] for row in values["p"]]
    report = {"test": "sky130_MOS_state_transfer_with_full_13_geometry_injector_bank",
              "checkpoint_sha256": EXPECTED_SHA, "qat_or_quantized_reference_used": False,
              "mos_corner": "ss", "temperature_c": 0, "state_common_mode_v": 0.9,
              "state_differential_v": state_diff_mv * 1e-3, "geometry_factors": list(GEOMETRIES),
              "gate_fractions": list(FRACTIONS), "pulse_width_ns": PULSE_NS,
              "simulation_completed": complete, "batches": batches, "rows": rows,
              "transfer_delta_v_by_polarity_geometry_fraction": values,
              "negative_transfer_mirrored_by_nominal_symmetry": POLARITIES == ("p",),
              "storage_cell": LAYOUT_CELL if LAYOUT_BANK else "two schematic 100um2 MOS gate banks",
              "storage_cell_layout_extracted": LAYOUT_BANK,
              "storage_cell_gds_bbox_um": [119.85, 101.99] if LAYOUT_BANK else None,
              "scope": (f"{len(rows)} selected signed one-event transfers; every case keeps the complete 13-geometry P/N injector bank connected to two extracted ten-device MOS gate banks. Selected geometry/fraction grid: {list(GEOMETRIES)} x {list(FRACTIONS)}; physically driven polarities: {list(POLARITIES)}; pulse {PULSE_NS:g}ns. Any unmeasured polarity in this sparse report is explicitly absent (not mirrored). No physical bias DAC, mismatch, state dependence across nonzero state, repeated-event train, 5ms retention or PLIF dynamics." if LAYOUT_BANK else f"{len(rows)} selected signed one-event transfers through a schematic MOS state bank at {PULSE_NS:g}ns. Selected geometry/fraction grid: {list(GEOMETRIES)} x {list(FRACTIONS)}; physically driven polarities: {list(POLARITIES)}. No extracted state-cell layout, physical bias DAC, mismatch, nonzero-state transfer, repeated-event train, retention or PLIF dynamics.")}
    (RES / f"{tag_base}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"simulation_completed": complete,
                      "measured_case_count": sum(case["measured"] for case in rows),
                      "selected_transfer_uv": values}, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
