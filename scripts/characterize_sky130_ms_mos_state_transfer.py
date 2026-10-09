"""Measure signed MOS-injector transfer into a MOS-gate membrane store."""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
GEOMETRIES = (0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0)
FRACTIONS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)
PULSE_NS = 42.2657
RISE_NS = 2.0
EVENT_US = 3.0
MEASURE_US = EVENT_US + PULSE_NS / 1000 + 0.02
STOP_US = 3.1
EXPECTED_SHA = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"
CHECKPOINT = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"

HEADER = """SKY130 SS/0C MOS gate-state transfer calibration
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


def deck(selected: list[dict]) -> str:
    lines = [HEADER, ".subckt diff_inject vp vn pp np pn nn vdd vss params: geom=1",
             "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
             "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
             "Xp_neg vn pn vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
             "Xn_pos vp np vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
             ".ends diff_inject"]

    def cap_bank(prefix: str, vp: str, vn: str) -> list[str]:
        rows = []
        for finger in range(10):
            rows += [f"Xcap_{prefix}_p{finger} 0 {vp} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1",
                     f"Xcap_{prefix}_n{finger} 0 {vn} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1"]
        return rows

    lines += cap_bank("ref", "vp_ref", "vn_ref")
    lines += ["Vcl_ref cl_ref 0 PWL(0 1.8 2.99u 1.8 2.991u 0 3.1u 0)",
              "Vclb_ref clb_ref 0 PWL(0 0 2.99u 0 2.991u 1.8 3.1u 1.8)",
              "Xcl_p_ref vcm vp_ref cl_ref clb_ref vdd 0 transmission_gate",
              "Xcl_n_ref vcm vn_ref cl_ref clb_ref vdd 0 transmission_gate"]
    for case in selected:
        geometry, fraction, polarity = case["geometry"], case["gate_fraction"], case["polarity"]
        tag = case["tag"]
        vp, vn = f"vp_{tag}", f"vn_{tag}"
        lines += cap_bank(tag, vp, vn)
        lines += [f"Vcl_{tag} cl_{tag} 0 PWL(0 1.8 2.99u 1.8 2.991u 0 {STOP_US}u 0)",
                  f"Vclb_{tag} clb_{tag} 0 PWL(0 0 2.99u 0 2.991u 1.8 {STOP_US}u 1.8)",
                  f"Xcl_p_{tag} vcm {vp} cl_{tag} clb_{tag} vdd 0 transmission_gate",
                  f"Xcl_n_{tag} vcm {vn} cl_{tag} clb_{tag} vdd 0 transmission_gate"]
        pg_off, ng_off = 1.8, 0.0
        pg_on, ng_on = 1.8 - fraction * 1.08, fraction * 0.6
        t0 = EVENT_US
        t1 = t0 + RISE_NS / 1000
        t2 = t0 + PULSE_NS / 1000
        t3 = t2 + RISE_NS / 1000
        gates = {"pp": pg_on if polarity == "p" else pg_off,
                 "np": ng_on if polarity == "n" else ng_off,
                 "pn": pg_on if polarity == "n" else pg_off,
                 "nn": ng_on if polarity == "p" else ng_off}
        for pin, active in gates.items():
            off = pg_off if pin in ("pp", "pn") else ng_off
            node = f"{pin}_{tag}"
            lines.append(f"V{node} {node} 0 PWL(0 {off} {t0-0.001:.9g}u {off} {t1:.9g}u {active:.12g} "
                         f"{t2:.9g}u {active:.12g} {t3:.9g}u {off} {STOP_US}u {off})")
        lines.append(f"Xinj_{tag} {vp} {vn} pp_{tag} np_{tag} pn_{tag} nn_{tag} vdd 0 diff_inject params: geom={geometry}")
    lines += [".control", "set numdgt=15", "tran 0.5n 3.1u 0 0.5n uic",
              "let diff_ref=v(vp_ref)-v(vn_ref)"]
    for row in selected:
        lines.append(f"let diff_{row['tag']}=v(vp_{row['tag']})-v(vn_{row['tag']})")
        lines.append(f"let delta_{row['tag']}=diff_{row['tag']}-diff_ref")
        lines.append(f"meas tran {row['tag']} find delta_{row['tag']} at={MEASURE_US:.9g}u")
    lines += ["quit", ".endc", ".end"]
    return "\n".join(lines) + "\n"


def main() -> int:
    if hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest() != EXPECTED_SHA:
        raise RuntimeError("the original full-float checkpoint hash differs")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    tag = "sky130_ms_mos_state_transfer_ss0"
    rows = [{"tag": f"g{str(geometry).replace('.', 'p')}_f{str(fraction).replace('.', 'p')}_p",
             "geometry": geometry, "gate_fraction": fraction, "polarity": polarity}
            for geometry in GEOMETRIES for fraction in FRACTIONS for polarity in ("p",)]
    completed_decks = []
    for batch_index, start in enumerate(range(0, len(rows), 8)):
        batch = rows[start:start + 8]
        batch_tag = f"{tag}_g{str(batch[0]['geometry']).replace('.', 'p')}"
        deck_path = BENCH / f"{batch_tag}.cir"
        deck_path.write_text(deck(batch), encoding="utf-8")
        command = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
                   "--volume", f"{ROOT}:/workspace:ro",
                   "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
                   "--workdir", "/workspace/artifacts/analog_asic/benches",
                   "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
                   "120", "ngspice", "-b", deck_path.name]
        simulation = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=150)
        log = simulation.stdout + simulation.stderr
        log_path = RES / f"{batch_tag}.log"
        log_path.write_text(log, encoding="utf-8")
        measured = {name.lower(): float(value) for name, value in re.findall(
            r"^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)", log, re.I | re.M)}
        for row in batch:
            row["event_delta_v"] = measured.get(row["tag"])
            row["measured"] = row["event_delta_v"] is not None
        batch_complete = (simulation.returncode == 0 and "ngspice-36 done" in log
                          and "Timestep too small" not in log and all(row["measured"] for row in batch))
        completed_decks.append({"deck": deck_path.name, "log": log_path.name,
                                "return_code": simulation.returncode, "case_count": len(batch),
                                "completed": batch_complete,
                                "failure": ("transient nonconvergence" if "Timestep too small" in log else
                                            "missing measurements or nonzero simulator exit" if not batch_complete else None)})
        print(json.dumps({"batch": batch_index + 1, "batch_count": (len(rows) + 7) // 8,
                          "geometry": batch[0]["geometry"], "completed": batch_complete,
                          "measured": sum(row["measured"] for row in batch)}), flush=True)
    completed = all(batch["completed"] for batch in completed_decks)
    failure = None if completed else "one or more bounded geometry batches failed"
    transfer_p = [[next(row["event_delta_v"] for row in rows
                        if row["geometry"] == geometry and row["gate_fraction"] == fraction)
                   for fraction in FRACTIONS] for geometry in GEOMETRIES]
    transfer = {"p": transfer_p, "n": [[-value for value in row] for row in transfer_p]}
    report = {
        "test": "sky130_MOS_gate_state_signed_injector_transfer_calibration",
        "checkpoint_sha256": EXPECTED_SHA,
        "qat_or_quantized_reference_used": False,
        "mos_corner": "ss", "temperature_c": 0,
        "state_cap_drawn_area_um2_per_node": 100,
        "physical_event_width_ns": PULSE_NS, "event_rise_ns": RISE_NS,
        "geometry_factors": list(GEOMETRIES), "gate_fractions": list(FRACTIONS),
        "simulation_completed": completed, "simulator_exit_code": simulation.returncode,
        "failure": failure, "batches": completed_decks, "rows": rows,
        "negative_transfer_mirrored_from_positive_nominal_symmetry": True,
        "transfer_delta_v_by_polarity_geometry_fraction": transfer,
        "deck": deck_path.name, "log": log_path.name,
        "scope": "104 positive one-event cases in13 bounded geometry batches. Each stores on two banks of ten SKY130 NFET gates (100um2 drawn area per node), sampled through physical TGs at VCM=0.9V. A physical P/N MOS injector sweeps13 device geometry factors and eight ideal shared gate fractions at SS/0C. Negative transfer is mirrored by nominal circuit symmetry, not separately measured in the full sweep; a two-polarity spot check at geometry0.5/fraction0.4 matched to simulation precision. Transfer is event-minus-matched-no-event differential at the end of a42.2657ns pulse. The 208-case and16-case batch attempts were OOM-killed; bounded eight-case batches are used. No state-dependent operating point, full fan-in, physical bias DAC, noise/mismatch, PVT, retention, beta/reset/threshold, extraction or layout."
    }
    (RES / f"{tag}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    pos_values = [row["event_delta_v"] for row in rows if row["event_delta_v"] is not None]
    neg_values = [-value for value in pos_values]
    print(json.dumps({"simulation_completed": completed, "measured_case_count": sum(row["measured"] for row in rows),
                      "case_count": len(rows), "failure": failure,
                      "positive_minmax_uv": [min(pos_values) * 1e6, max(pos_values) * 1e6] if pos_values else None,
                      "negative_minmax_uv": [min(neg_values) * 1e6, max(neg_values) * 1e6] if neg_values else None}, indent=2))
    return 0 if completed else 2


if __name__ == "__main__":
    raise SystemExit(main())
