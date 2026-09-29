"""Bound direct clocked comparison of two physical SKY130 MIM state capacitors."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
DELTAS_UV = (-6.0, -3.0, 0.0, 3.0, 6.0)


def main() -> int:
    lines = [
        "SKY130 direct clocked comparator reading floating physical MIM state",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
        '.include "../../../asic/analog/modules.spice"',
        '.include "../../../asic/analog/sky130_ms_plif.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
        "Vinit init 0 PWL(0 1.8 2.4999u 1.8 2.5u 0 2.7u 0)",
        "Vinitb initb 0 PWL(0 0 2.4999u 0 2.5u 1.8 2.7u 1.8)",
        "Vpre pre 0 PWL(0 1.8 2.5549u 1.8 2.555u 0 2.7u 0)",
        "Vpreb preb 0 PWL(0 0 2.5549u 0 2.555u 1.8 2.7u 1.8)",
        "Vread read 0 PWL(0 0 2.5599u 0 2.56u 1.8 2.6019u 1.8 2.602u 0 2.7u 0)",
        "Vreadb readb 0 PWL(0 1.8 2.5599u 1.8 2.56u 0 2.6019u 0 2.602u 1.8 2.7u 1.8)",
        "Vclk clk 0 PWL(0 0 2.5999u 0 2.6u 1.8 2.7u 1.8)",
        ".subckt regen inp inn clk outp outn vdd vss",
        "Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xln outp outn ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
        "Xrn outn outp ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xlatch_tail ltail clk vss vss sky130_fd_pr__nfet_01v8 w=8 l=0.5",
        "Xin_p outp inp tail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xin_n outn inn tail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
        "Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w=4 l=1",
        ".ends regen",
    ]
    vectors = []
    for delta in DELTAS_UV:
        tag = f"d{delta:g}".replace("-", "m").replace(".", "p")
        signal = f"mem_{tag}"
        reference = f"ref_{tag}"
        inp = f"inp_{tag}"
        inn = f"inn_{tag}"
        lines += [
            f"Vtarget_{tag} target_{tag} 0 {0.9+delta*1e-6:.12f}",
            f"Xcmem_{tag} {signal} vcm membrane_mim w_um=100 l_um=100",
            f"Xcref_{tag} {reference} vcm membrane_mim w_um=100 l_um=100",
            f"Xinit_mem_{tag} target_{tag} {signal} init initb vdd 0 transmission_gate",
            f"Xinit_ref_{tag} vcm {reference} init initb vdd 0 transmission_gate",
            f"Xpre_inp_{tag} {inp} vcm pre preb vdd 0 transmission_gate",
            f"Xpre_inn_{tag} {inn} vcm pre preb vdd 0 transmission_gate",
            f"Xread_mem_{tag} {signal} {inp} read readb vdd 0 transmission_gate",
            f"Xread_ref_{tag} {reference} {inn} read readb vdd 0 transmission_gate",
            f"Xregen_{tag} {inp} {inn} clk op_{tag} on_{tag} vdd 0 regen",
            f"Cloadp_{tag} op_{tag} 0 20f", f"Cloadn_{tag} on_{tag} 0 20f",
        ]
        if delta:
            from_node, to_node = (inp, inn) if delta > 0 else (inn, inp)
            lines.append(f"Iopp_{tag} {from_node} {to_node} PWL(0 0 2.60205u 0 2.60206u 80n 2.60216u 80n 2.60217u 0 2.7u 0)")
        vectors += [f"v(op_{tag})", f"v(on_{tag})", f"v({signal})", f"v({reference})", f"v({inp})", f"v({inn})"]
    stem = "sky130_regenerative_comparator_cut2ns_perturb80"
    deck = BENCH / f"{stem}.cir"
    data = RES / f"{stem}.dat"
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 2n 2.7u uic", f"wrdata ../results/{data.name} " + " ".join(vectors), "quit", ".endc", ".end"]
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    raw = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                row = [float(value) for value in line.split()]
                if len(row) == 1 + 6 * len(DELTAS_UV):
                    raw.append(row)
            except ValueError:
                continue
    completed = run.returncode == 0 and len(raw) > 100 and "tran simulation(s) aborted" not in log.lower()
    report = {"test": "sky130_clocked_comparator_direct_physical_mim_state", "simulation_completed": completed, "return_code": run.returncode, "input_differentials_uv": list(DELTAS_UV), "membrane_and_reference_mim_um": 100, "evaluation_ns": 2600, "read_switch_open_ns": 2602.0, "opposing_current_pulse_na": 80, "opposing_pulse_duration_ns": 0.1, "scope": "TT physical MIM states and PDK switches; deterministic opposing input-gate current pulse after read isolation, ideal initialization/clock/source; no sampled or device noise, mismatch, PVT, extraction, or network replay"}
    if completed:
        def at(ns):
            return min(raw, key=lambda row: abs(row[0] - ns * 1e-9))
        for index, delta in enumerate(DELTAS_UV):
            base = 1 + 6 * index
            points = {}
            for ns in (2558, 2590, 2599.8, 2601, 2602.3, 2605, 2640):
                row = at(ns)
                points[str(ns)] = {"state_diff_uv": (row[base+2] - row[base+3]) * 1e6, "signal_state_v": row[base+2], "reference_state_v": row[base+3], "latch_input_diff_uv": (row[base+4] - row[base+5]) * 1e6, "output_diff_v": row[base] - row[base+1]}
            before = points["2558"]["state_diff_uv"]
            preeval = points["2599.8"]["state_diff_uv"]
            after = points["2640"]["state_diff_uv"]
            decision = points["2605"]["output_diff_v"]
            report.setdefault("measurements", []).append({"source_input_uv": delta, "state_diff_before_read_uv": before, "state_diff_preeval_uv": preeval, "state_diff_after_read_uv": after, "read_state_disturbance_uv": after-before, "decision_five_ns_v": decision, "decision_matches_preeval_state": (decision > 0) == (preeval < 0) if delta else None, "points": points})
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if completed else 1

if __name__ == "__main__":
    raise SystemExit(main())
