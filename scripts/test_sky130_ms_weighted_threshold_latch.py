"""Connect one measured full-float fan-in to a physical clocked MIM latch."""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
SOURCE = ("sky130_ms_first_touch_float_fanin_ss0_near_threshold_scale_"
          "stage_continuous_geometry_mapw42p2657n_bankedmap_durationfloor_"
          "slot50p253n_shuffleonly")


def main() -> int:
    shift_uv = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                           if arg.startswith("--threshold-shift-uv=")), "0"))
    if abs(shift_uv) > 20:
        raise ValueError("threshold-shift diagnostic is bounded to +/-20uV")
    source_meta = json.loads((RES / f"{SOURCE}_deck.json").read_text(encoding="utf-8"))
    margins = json.loads((RES / "sky130_ms_fanin_threshold_margin_screen.json").read_text(encoding="utf-8"))
    site = margins["cases"]["near_threshold_scale"]
    if (source_meta["checkpoint_sha256"] != margins["checkpoint_sha256"] or
            source_meta["qat_or_quantized_reference_used"] or
            source_meta["site_selection"] != "near_threshold_scale" or
            source_meta["event_orders"] != ["shuffle"] or
            source_meta["selected_flat_batch"] != 1 or
            site["trace_index"] != [0, 1, 7, 42, 1] or
            abs(site["float_candidate"] - site["float_current"]) > 1e-5):
        raise RuntimeError("the source deck and full-float site do not match")
    volts_per_unit = float(margins["volts_per_model_unit"])
    threshold_v = float(site["float_threshold"]) * volts_per_unit + shift_uv * 1e-6
    ideal_margin_v = (float(site["float_candidate"]) - float(site["float_threshold"])) * volts_per_unit - shift_uv * 1e-6
    init_diff_v = -threshold_v
    source_deck = BENCH / f"{SOURCE}.cir"
    deck_lines = source_deck.read_text(encoding="utf-8").splitlines()
    replacements = {
        "Xcl_p_shuffle vcm vp_shuffle": "Xcl_p_shuffle initp_shuffle vp_shuffle",
        "Xcl_n_shuffle vcm vn_shuffle": "Xcl_n_shuffle initn_shuffle vn_shuffle",
    }
    for old, new in replacements.items():
        hits = [i for i, line in enumerate(deck_lines) if line.startswith(old)]
        if len(hits) != 1:
            raise RuntimeError(f"expected one source clamp line: {old}")
        deck_lines[hits[0]] = deck_lines[hits[0]].replace(old, new, 1)
    control_i = deck_lines.index(".control")
    latch = [
        f"Vinitp_shuffle initp_shuffle 0 {0.9 + init_diff_v / 2:.12f}",
        f"Vinitn_shuffle initn_shuffle 0 {0.9 - init_diff_v / 2:.12f}",
        "Vpre_latch pre_latch 0 PWL(0 1.8 20.0449u 1.8 20.045u 0 20.2u 0)",
        "Vpreb_latch preb_latch 0 PWL(0 0 20.0449u 0 20.045u 1.8 20.2u 1.8)",
        "Vread_latch read_latch 0 PWL(0 0 20.0499u 0 20.05u 1.8 20.1019u 1.8 20.102u 0 20.2u 0)",
        "Vreadb_latch readb_latch 0 PWL(0 1.8 20.0499u 1.8 20.05u 0 20.1019u 0 20.102u 1.8 20.2u 1.8)",
        "Vclk_latch clk_latch 0 PWL(0 0 20.0999u 0 20.1u 1.8 20.2u 1.8)",
        ".subckt weighted_regen inp inn clk outp outn vdd vss",
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
        ".ends weighted_regen",
        "Xpre_inp_latch inp_latch vcm pre_latch preb_latch vdd 0 transmission_gate",
        "Xpre_inn_latch inn_latch vcm pre_latch preb_latch vdd 0 transmission_gate",
        "Xread_p_latch vp_shuffle inp_latch read_latch readb_latch vdd 0 transmission_gate",
        "Xread_n_latch vn_shuffle inn_latch read_latch readb_latch vdd 0 transmission_gate",
        "Xregen_latch inp_latch inn_latch clk_latch op_latch on_latch vdd 0 weighted_regen",
        "Cloadp_latch op_latch 0 20f",
        "Cloadn_latch on_latch 0 20f",
    ]
    deck_lines[control_i:control_i] = latch
    tran_i = next(i for i, line in enumerate(deck_lines) if line.startswith("tran "))
    deck_lines[tran_i] = "tran 0.5n 20.2u uic"
    quit_i = deck_lines.index("quit")
    deck_lines[quit_i:quit_i] = [
        "let weighted_state=v(vp_shuffle)-v(vn_shuffle)",
        "let weighted_input=v(inp_latch)-v(inn_latch)",
        "let weighted_output=v(op_latch)-v(on_latch)",
        "meas tran before_state find weighted_state at=20.049u",
        "meas tran before_ref find diff_ref at=20.049u",
        "meas tran preeval_state find weighted_state at=20.0998u",
        "meas tran preeval_ref find diff_ref at=20.0998u",
        "meas tran preeval_input find weighted_input at=20.0998u",
        "meas tran early_output find weighted_output at=20.105u",
        "meas tran late_output find weighted_output at=20.15u",
        "meas tran after_state find weighted_state at=20.15u",
        "meas tran after_ref find diff_ref at=20.15u",
    ]
    shift_tag = f"{shift_uv:g}".replace("-", "m").replace(".", "p")
    stem = f"sky130_ms_weighted_threshold_latch_nearthr_shift{shift_tag}uv"
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join(deck_lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
           "180", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=195)
    log = proc.stdout + proc.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    names = ("before_state", "before_ref", "preeval_state", "preeval_ref", "preeval_input",
             "early_output", "late_output", "after_state", "after_ref")
    measured = {}
    for name in names:
        match = re.search(rf"(?im)^\s*{name}\s*=\s*([-+0-9.eE]+)", log)
        if match:
            measured[name] = float(match.group(1))
    complete = (proc.returncode == 0 and len(measured) == len(names) and
                "ngspice-36 done" in log and "timestep too small" not in log.lower())
    thermal_pair_uv = math.sqrt(2 * 1.380649e-23 * 273.15 / 203.8e-15) * 1e6
    report = {"test": "sky130_full_float_weighted_fanin_then_clocked_mim_latch",
              "simulation_completed": complete, "return_code": proc.returncode,
              "source_deck": source_deck.name,
              "checkpoint_sha256": source_meta["checkpoint_sha256"],
              "qat_or_quantized_reference_used": False,
              "event_count": source_meta["event_count"],
              "float_candidate": site["float_candidate"],
              "float_threshold": site["float_threshold"],
              "volts_per_model_unit": volts_per_unit,
              "ideal_float_candidate_minus_threshold_uv": ideal_margin_v * 1e6,
              "threshold_shift_uv": shift_uv,
              "ideal_initial_differential_uv": init_diff_v * 1e6,
              "read_mim_side_um": 10, "read_tg_open_ns_after_eval": 2.0,
              "independent_pair_kt_over_c_proxy_uv_rms_at_0c": thermal_pair_uv,
              "state_capacitance_each_f_from_prior_sky130_screen": 203.8e-15,
              "measurements_v": measured,
              "scope": "One SS/0C 329-event original-float final-fusion fan-in with physical PDK MOS/TG/MIM and clocked transistor latch. The learned threshold is imposed by ideal differential clamp levels before the event train; the full fan-in R-2R correction remains ideal effective gate PWL. No physical threshold DAC, beta/prior state, noise, mismatch, PVT sweep, extraction, full-frame closed-loop spike replay or layout."}
    if complete:
        before = measured["before_state"] - measured["before_ref"]
        preeval = measured["preeval_state"] - measured["preeval_ref"]
        after = measured["after_state"] - measured["after_ref"]
        expected = ideal_margin_v > 0
        observed = measured["early_output"] < 0  # This latch inverts input polarity.
        physical_expected = preeval > 0
        report.update({"pre_read_state_minus_reference_uv": before * 1e6,
                       "preeval_state_minus_reference_uv": preeval * 1e6,
                       "preeval_physical_minus_float_margin_uv": (preeval - ideal_margin_v) * 1e6,
                       "post_read_state_minus_reference_uv": after * 1e6,
                       "read_state_disturbance_uv": (after - before) * 1e6,
                       "latch_input_preeval_uv": measured["preeval_input"] * 1e6,
                       "expected_float_spike_at_shifted_threshold": expected,
                       "expected_spike_from_physical_preeval_state": physical_expected,
                       "observed_latch_spike": observed,
                       "decision_matches_float": bool(observed == expected),
                       "decision_matches_physical_preeval_state": bool(observed == physical_expected)})
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
