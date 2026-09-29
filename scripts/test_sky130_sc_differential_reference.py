"""Bounded TT test of a matched no-packet reference integrator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

ROOT = Path(__file__).resolve().parents[1]
SEQUENCES = ("pp", "nn", "pn", "np")


def main() -> int:
    selected = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--sequence=")), "pp")
    sequences = (selected,) if selected in SEQUENCES else SEQUENCES
    sampled = "--sampled" in sys.argv
    gain = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--readout-gain=")), "1")
    corner = next((arg.split("=", 1)[1] for arg in sys.argv[1:] if arg.startswith("--corner=")), "tt")
    if corner not in ("tt", "ss", "ff"):
        raise ValueError("supported schematic corners: tt, ss, ff")
    common = COMMON.replace("__tt.corner.spice", f"__{corner}.corner.spice")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = [f"SKY130 {corner.upper()} matched differential reference, two 5ms-bin packets", common,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    names: list[str] = []
    for seq in sequences:
        for suffix, packet_seq in (("sig", seq), ("ref", None)):
            name = f"{seq}_{suffix}"
            names.append(name)
            lines += cell(name, 0.90, packet_seq, long_bin=True)
        lines += [f"Vread_vbn_{seq} read_vbn_{seq} 0 0.65", f"Vread_vbp_{seq} read_vbp_{seq} 0 0.75"]
        if sampled:
            lines += [f"Vread_en_{seq} read_en_{seq} 0 PWL(0 0 4.5024m 0 4.5025m 1.8 5.005m 1.8)",
                      f"Vread_enb_{seq} read_enb_{seq} 0 PWL(0 1.8 4.5024m 1.8 4.5025m 0 5.005m 0)",
                      f"Xread_{seq} out_{seq}_sig out_{seq}_ref diff_out_{seq} read_en_{seq} read_enb_{seq} read_vbn_{seq} read_vbp_{seq} vdd 0 vcm sky130_sc_diff_readout_sampled gain={gain}"]
        else:
            lines += [f"Xread_{seq} out_{seq}_sig out_{seq}_ref diff_out_{seq} read_vbn_{seq} read_vbp_{seq} vdd 0 vcm sky130_sc_diff_readout gain={gain}"]
    vectors = " ".join(f"v(out_{n}) v(sum_{n})" for n in names)
    vectors += " " + " ".join(f"v(diff_out_{seq})" for seq in sequences)
    gain_suffix = f"_g{gain.replace('.', 'p')}" if gain != "1" else ""
    suffix = ("sampled_" if sampled else "") + (f"{corner}_" if corner != "tt" else "") + ("all" if len(sequences) > 1 else sequences[0]) + gain_suffix
    data = RES / f"sky130_sc_differential_reference_{suffix}.dat"
    lines += [".control", "set wr_singlescale", "set wr_vecnames",
              "tran 100n 5.005m uic", f"wrdata ../results/{data.name} {vectors}", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_differential_reference_{suffix}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    command = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT_DIR()}:/workspace/artifacts/analog_asic",
               "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
               "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(command, text=True, capture_output=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"sky130_sc_differential_reference_{suffix}.log").write_text(log, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                continue
    completed = run.returncode == 0 and len(rows) > 2
    report: dict[str, object] = {
        "test": f"sky130_{corner}_matched_differential_reference_two_packets_over_5ms_bin",
        "simulation_completed": completed, "return_code": run.returncode,
        "scope": f"schematic {corner.upper()}; readout input switches close at 4.5025ms; resistor gain ratio={gain}; transistor mismatch/layout/extraction not modeled" if sampled else f"schematic {corner.upper()}; readout connected throughout; resistor gain ratio={gain}; transistor mismatch/layout/extraction not modeled",
        "initial_state_v": 0.90, "packet_cap_um": 1, "membrane_cap_um": 100,
        "cases": [], "sequences_tested": list(sequences),
    }
    if completed:
        times = [row[0] for row in rows]
        i_pre = min(range(len(times)), key=lambda i: abs(times[i] - 0.490e-3))
        i_final = min(range(len(times)), key=lambda i: abs(times[i] - 5.000e-3))
        for j, seq in enumerate(sequences):
            sig_col, ref_col = 1 + (j * 2) * 2, 1 + (j * 2 + 1) * 2
            sig_pre, ref_pre = rows[i_pre][sig_col], rows[i_pre][ref_col]
            sig_final, ref_final = rows[i_final][sig_col], rows[i_final][ref_col]
            readout_col = 1 + len(names) * 2 + j
            readout_pre, readout_final = rows[i_pre][readout_col], rows[i_final][readout_col]
            d_pre, d_final = sig_pre - ref_pre, sig_final - ref_final
            report["cases"].append({
                "sequence": seq, "signal_pre_v": sig_pre, "reference_pre_v": ref_pre,
                "signal_final_v": sig_final, "reference_final_v": ref_final,
                "signal_common_shift_mv": (sig_final - sig_pre) * 1e3,
                "reference_common_shift_mv": (ref_final - ref_pre) * 1e3,
                "differential_pre_mv": d_pre * 1e3, "differential_final_mv": d_final * 1e3,
                "differential_change_uv": (d_final - d_pre) * 1e6,
                "readout_pre_v": readout_pre, "readout_final_v": readout_final,
                "readout_change_uv": (readout_final - readout_pre) * 1e6,
                "readout_relation_error_uv": ((readout_final - readout_pre) + (d_final - d_pre)) * 1e6,
            })
        report["max_reference_common_shift_mv"] = max(abs(c["reference_common_shift_mv"]) for c in report["cases"])
        report["max_differential_change_abs_uv"] = max(abs(c["differential_change_uv"]) for c in report["cases"])
    (RES / f"sky130_sc_differential_reference_{suffix}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    available = []
    for seq in SEQUENCES:
        path = RES / f"sky130_sc_differential_reference_{seq}.json"
        if path.exists():
            part = json.loads(path.read_text(encoding="utf-8"))
            if part.get("simulation_completed"):
                available.extend(part.get("cases", []))
    if len(available) == len(SEQUENCES) and not sampled:
        aggregate = {
            "test": "sky130_tt_matched_differential_reference_two_packets_over_5ms_bin",
            "simulation_completed": True,
            "scope": report["scope"], "initial_state_v": 0.90,
            "packet_cap_um": 1, "membrane_cap_um": 100,
            "sequences_tested": list(SEQUENCES), "cases": available,
            "max_reference_common_shift_mv": max(abs(c["reference_common_shift_mv"]) for c in available),
            "max_differential_change_abs_uv": max(abs(c["differential_change_uv"]) for c in available),
            "max_mixed_sign_residual_abs_uv": max(abs(c["differential_change_uv"]) for c in available if c["sequence"] in ("pn", "np")),
            "max_readout_relation_error_abs_uv": max(abs(c.get("readout_relation_error_uv", c["readout_change_uv"] + c["differential_change_uv"])) for c in available),
        }
        (RES / "sky130_sc_differential_reference.json").write_text(json.dumps(aggregate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if completed else 1


def OUT_DIR() -> Path:
    return ROOT / "artifacts/analog_asic"


if __name__ == "__main__":
    raise SystemExit(main())
