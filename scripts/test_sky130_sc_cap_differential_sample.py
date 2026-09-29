"""Test capacitor-only late sampling of the SC-cell differential state."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

ROOT = Path(__file__).resolve().parents[1]
SEQUENCES = ("pp", "nn", "pn", "np")


def main() -> int:
    no_events = "--no-events" in sys.argv
    seq = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--sequence=")), "pp")
    if not no_events and seq not in SEQUENCES:
        raise ValueError(f"sequence must be one of {SEQUENCES}")
    if no_events:
        seq = "zero"
    width = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--sample-cap-um=")), "10"))
    bottomplate = "--bottomplate" in sys.argv
    suffix = f"{seq}_{str(width).replace('.', 'p')}um" + ("_bp" if bottomplate else "")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = [f"SKY130 TT differential MIM sample capacitor {width:g}um", COMMON,
             "Vdd vdd 0 1.8", "Vcm vcm 0 0.9"]
    for name, packet_seq in (("sig", None if no_events else seq), ("ref", None)):
        lines += cell(name, 0.90, packet_seq, long_bin=True)
    if bottomplate:
        lines += [
            "Vsample_hi sample_hi 0 PWL(0 0 4.8999m 0 4.900m 1.8 4.9494m 1.8 4.9495m 0 5.005m 0)",
            "Vsample_hib sample_hi_b 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 4.9494m 0 4.9495m 1.8 5.005m 1.8)",
            "Vsample_lo sample_lo 0 PWL(0 0 4.8999m 0 4.900m 1.8 4.9489m 1.8 4.949m 0 5.005m 0)",
            "Vsample_lob sample_lo_b 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 4.9489m 0 4.949m 1.8 5.005m 1.8)",
            "Vreset sample_reset 0 PWL(0 1.8 4.899m 1.8 4.8991m 0 5.005m 0)",
            "Vresetb sample_reset_b 0 PWL(0 0 4.899m 0 4.8991m 1.8 5.005m 1.8)",
            f"Xsampler out_ref out_sig diff_out diff_return sample_hi sample_hi_b sample_lo sample_lo_b sample_reset sample_reset_b vdd 0 vcm sky130_sc_diff_cap_sampler_bp sample_um={width:g}",
            f"Xdummy vcm vcm dummy_out dummy_return sample_hi sample_hi_b sample_lo sample_lo_b sample_reset sample_reset_b vdd 0 vcm sky130_sc_diff_cap_sampler_bp sample_um={width:g}",
        ]
    else:
        lines += [
        "Vsample sample 0 PWL(0 0 4.8999m 0 4.900m 1.8 4.9499m 1.8 4.950m 0 5.005m 0)",
        "Vsampleb sample_b 0 PWL(0 1.8 4.8999m 1.8 4.900m 0 4.9499m 0 4.950m 1.8 5.005m 1.8)",
        "Vreset sample_reset 0 PWL(0 1.8 4.899m 1.8 4.8991m 0 5.005m 0)",
        "Vresetb sample_reset_b 0 PWL(0 0 4.899m 0 4.8991m 1.8 5.005m 1.8)",
        f"Xsampler out_ref out_sig diff_out diff_return sample sample_b sample_reset sample_reset_b vdd 0 vcm sky130_sc_diff_cap_sampler sample_um={width:g}",
        f"Xdummy vcm vcm dummy_out dummy_return sample sample_b sample_reset sample_reset_b vdd 0 vcm sky130_sc_diff_cap_sampler sample_um={width:g}",
        ]
    data = RES / f"sky130_sc_cap_differential_sample_{suffix}.dat"
    vectors = "v(out_sig) v(out_ref) v(diff_out) v(diff_return) v(dummy_out) v(dummy_return)"
    lines += [".control", "set wr_singlescale", "set wr_vecnames", "tran 100n 5.005m uic",
              f"wrdata ../results/{data.name} {vectors}", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_cap_differential_sample_{suffix}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"sky130_sc_cap_differential_sample_{suffix}.log").write_text(log, encoding="utf-8")
    rows: list[list[float]] = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                continue
    report: dict[str, object] = {
        "test": "sky130_tt_capacitor_only_differential_membrane_sample",
        "simulation_completed": run.returncode == 0 and len(rows) > 2,
        "return_code": run.returncode, "sequence": seq,
        "sample_cap_width_um": width,
        "nominal_sample_cap_ff_estimate": 2.0 * width * width + 0.38 * width,
        "nominal_membrane_cap_ff_estimate": 2.0 * 100.0 * 100.0 + 0.38 * 200.0,
        "sample_kT_C_noise_mv_at_300K": (1.380649e-23 * 300.0 / ((2.0 * width * width + 0.38 * width) * 1e-15)) ** 0.5 * 1e3,
        "scope": "nominal TT schematic; MIM sample capacitor and transmission gates only; input cells isolated after 50us sample; no output buffer, mismatch, PVT, physical resistor geometry, or extraction",
    }
    if report["simulation_completed"]:
        times = [r[0] for r in rows]
        i_pre = min(range(len(times)), key=lambda i: abs(times[i] - 0.490e-3))
        i_sample_pre = min(range(len(times)), key=lambda i: abs(times[i] - 4.890e-3))
        i_final = min(range(len(times)), key=lambda i: abs(times[i] - 5.000e-3))
        sig_pre, ref_pre, out_pre, dummy_pre = rows[i_pre][1], rows[i_pre][2], rows[i_pre][3], rows[i_pre][5]
        sig_sample_pre, ref_sample_pre = rows[i_sample_pre][1], rows[i_sample_pre][2]
        sig_final, ref_final, out_final, dummy_final = rows[i_final][1], rows[i_final][2], rows[i_final][3], rows[i_final][5]
        d_pre, d_final = sig_pre - ref_pre, sig_final - ref_final
        report.update({
            "signal_common_shift_mv": (sig_final - sig_pre) * 1e3,
            "reference_common_shift_mv": (ref_final - ref_pre) * 1e3,
            "differential_state_change_uv": (d_final - d_pre) * 1e6,
            "differential_state_at_sampler_open_uv": (sig_sample_pre - ref_sample_pre) * 1e6,
            "differential_state_disturbance_during_sample_uv": ((sig_final - ref_final) - (sig_sample_pre - ref_sample_pre)) * 1e6,
            "sample_output_pre_v": out_pre, "sample_output_final_v": out_final,
            "sample_output_change_uv": (out_final - out_pre) * 1e6,
            "sample_output_relative_vcm_final_uv": (out_final - 0.9) * 1e6,
            "dummy_output_final_v": dummy_final,
            "dummy_offset_final_uv": (dummy_final - 0.9) * 1e6,
            "offset_cancelled_difference_v": out_final - dummy_final,
            "offset_cancelled_difference_uv": (out_final - dummy_final) * 1e6,
            "offset_cancelled_difference_relative_to_pre_uv": ((out_final - dummy_final) - (out_pre - dummy_pre)) * 1e6,
            "sample_output_raw_relation_error_uv": ((out_final - 0.9) - d_final) * 1e6,
            "same_run_real_minus_dummy_uv": (out_final - dummy_final) * 1e6,
            "sampled_difference_after_vcm_clamp_uv": (out_final - 0.9) * 1e6,
        })
    (RES / f"sky130_sc_cap_differential_sample_{suffix}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
