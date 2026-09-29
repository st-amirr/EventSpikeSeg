"""Bounded SKY130 24-bit signed-Q7.16 membrane restore and mux smoke.

Digital state words are signed two's-complement Q7.16. Before the DAC, the
controller clips to a declared signed state range and maps to offset-binary
u24 over a rail-safe voltage window. The resistor ladder is an ideal-R
schematic model and this smoke does not establish physical 24-bit ENOB.
"""
from __future__ import annotations
import json, math, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VDD, VCM, SCALE, STATE_ABSMAX = 1.8, 0.9, 0.2, 1.0
TT_DAC_RAIL_SHIFT_V = 0.002553424  # measured q=0 residual correction at TT
VLO = VCM - SCALE * STATE_ABSMAX + TT_DAC_RAIL_SHIFT_V
VHI = VCM + SCALE * STATE_ABSMAX + TT_DAC_RAIL_SHIFT_V
RESTORE_ERROR_LIMIT_V = 0.003
TT_COMMON_MODE_OFFSET_U24 = 12544  # provisional TT offset, applied uniformly to both signs
N = 1 << 24

COMMON = """.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
"""


def signed24(raw: int) -> int:
    raw &= N - 1
    return raw - N if raw & (1 << 23) else raw


def q716_to_u24(q: int) -> tuple[int, int, float]:
    """Clip signed Q7.16 into ±STATE_ABSMAX, then map to offset-binary u24."""
    value_q = signed24(q)
    q_limit = round(STATE_ABSMAX * 65536)
    clipped_q = max(-q_limit, min(q_limit - 1, value_q))
    clipped = clipped_q / 65536.0
    # Round the nonnegative affine code deterministically, half upward.
    code = math.floor(((clipped + STATE_ABSMAX) / (2 * STATE_ABSMAX)) * N + 0.5)
    code += TT_COMMON_MODE_OFFSET_U24
    code = max(0, min(N - 1, code))
    return code, clipped_q, VCM + SCALE * clipped


def deck(q_words: list[int]) -> tuple[str, list[dict]]:
    mapped = []
    for q in q_words:
        code, clipped_q, target = q716_to_u24(q)
        mapped.append({"q716_signed": signed24(q), "q716_clipped": clipped_q,
                       "u24_offset_code": code, "expected_v": target})
    slot_us = 30
    end_us = slot_us * len(mapped)
    lines = [f"SKY130 Q7.16 membrane restore/multiplex smoke ({len(mapped)} codes)", COMMON,
             f"Vdd vdd 0 {VDD}", f"Vcm vcm 0 {VCM}", f"Vmemhi mem_hi 0 {VHI}", f"Vmemlo mem_lo 0 {VLO}",
             "Vwhi weight_hi 0 1.8", "Vwlo weight_lo 0 0", "Vbias vbias 0 0.65", "Voff ibias_n_off 0 0",
             "Vreset reset 0 PWL(0 1.8 0.1u 1.8 0.101u 0 240u 0)",
             "Vresetb reset_b 0 PWL(0 0 0.1u 0 0.101u 1.8 240u 1.8)",
             "Vcap capture 0 0", "Vcapb capture_b 0 1.8", "Vleak leak_en 0 0", "Vleakb leak_enb 0 1.8",
             "Vpp pulse_pos 0 1.8", "Vpn pulse_neg 0 0", "Vsign sign_n 0 0", ""]
    for bit in range(24):
        values = [((item["u24_offset_code"] >> bit) & 1) * VDD for item in mapped]
        points = [f"0 {values[0]}"]
        for j in range(1, len(values)):
            t = j * slot_us
            points += [f"{t}u {values[j-1]}", f"{t}.001u {values[j]}"]
        points += [f"{end_us}u {values[-1]}"]
        lines.append(f"Vmb{bit} mb{bit} 0 PWL(" + " ".join(points) + ")")
    for name, start, stop in (("restore", 2, 20),):
        points = ["0 0"]
        for j in range(len(mapped)):
            a, b = j * slot_us + start, j * slot_us + stop
            points += [f"{a}u 0", f"{a}.001u {VDD}", f"{b}u {VDD}", f"{b}.001u 0"]
        points += [f"{end_us}u 0"]
        lines.append(f"V{name} {name} 0 PWL(" + " ".join(points) + ")")
        inv_points = [f"{t.split()[0]} {VDD-float(t.split()[1])}" for t in points]
        lines.append(f"V{name}b restore_b 0 PWL(" + " ".join(inv_points) + ")")
    w_pins = " ".join(f"w{i}" for i in range(22,-1,-1))
    m_pins = " ".join(f"mb{i}" for i in range(23,-1,-1))
    lines += [f"Xplif state snapshot spike capture capture_b reset reset_b leak_en leak_enb restore restore_b pulse_pos pulse_neg sign_n {w_pins} {m_pins} vbias mem_hi mem_lo weight_hi weight_lo ibias_n_off vdd 0 vcm analog_plif_mux_channel theta=0.4 scale={SCALE} w_um=100 l_um=100",
              ".control", "set wr_singlescale", "set wr_vecnames", f"tran 20n {end_us}u",
              f"wrdata ../results/sky130_ms_restore_mux_24bit.dat v(state)", "quit", ".endc", ".end"]
    return "\n".join(lines) + "\n", mapped


def run() -> tuple[int, str]:
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", "sky130_ms_restore_mux_24bit.cir"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
    text = r.stdout + r.stderr
    (RES / "sky130_ms_restore_mux_24bit.log").write_text(text)
    return r.returncode, text


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True); RES.mkdir(parents=True, exist_ok=True)
    # Includes rail endpoints, zero, signed negative/positive states, and saturation.
    q_words = [-65536, -1, 0, 32768, -32768, 32768, 65535, 131072]
    cir, mapped = deck(q_words)
    (BENCH / "sky130_ms_restore_mux_24bit.cir").write_text(cir)
    dat = RES / "sky130_ms_restore_mux_24bit.dat"
    dat.unlink(missing_ok=True)
    rc, log = run()
    rows = []
    if dat.is_file():
        for line in dat.read_text().splitlines()[1:]:
            try:
                row = [float(x) for x in line.split()]
                if len(row) >= 2 and all(math.isfinite(x) for x in row): rows.append(row[:2])
            except ValueError: pass
    completed = rc == 0 and bool(rows) and rows[-1][0] >= len(mapped)*12e-6*0.999 and "aborted" not in log.lower()
    slot_results = []
    if completed:
        for j, item in enumerate(mapped):
            t = (j*30 + 25.0)*1e-6
            row = min(rows, key=lambda r: abs(r[0]-t))
            slot_results.append({**item, "sample_time_s": row[0], "measured_v": row[1],
                                 "abs_error_v": abs(row[1]-item["expected_v"])})
    # Verify A→B→A on one physical capacitor (slots 3, 4, 5).
    mux = {"slot_a_first_v": slot_results[3]["measured_v"] if completed else None,
           "slot_b_v": slot_results[4]["measured_v"] if completed else None,
           "slot_a_return_v": slot_results[5]["measured_v"] if completed else None}
    if completed:
        mux["a_roundtrip_error_v"] = abs(mux["slot_a_return_v"]-mux["slot_a_first_v"])
        mux["ab_separation_v"] = abs(mux["slot_a_first_v"]-mux["slot_b_v"])
    range_smoke = completed and all(x["abs_error_v"] <= RESTORE_ERROR_LIMIT_V for x in slot_results)
    mux_pass = completed and mux.get("a_roundtrip_error_v", float("inf")) <= RESTORE_ERROR_LIMIT_V and mux.get("ab_separation_v", 0) >= 0.1
    ordered = sorted(slot_results, key=lambda x: x["q716_clipped"])
    unique_codes = []
    for item in ordered:
        if not unique_codes or item["q716_clipped"] != unique_codes[-1]["q716_clipped"]:
            unique_codes.append(item)
    measured_monotonic = all(b["measured_v"] >= a["measured_v"] for a,b in zip(unique_codes,unique_codes[1:])) if completed else False
    q_lsb_v = SCALE / 65536.0
    max_err = max((x["abs_error_v"] for x in slot_results), default=float("inf"))
    q_precision = completed and max_err <= q_lsb_v / 2
    report = {"architecture": "sky130_mixed_signal_digital_q716_restore_mux", "logic_word_format": "signed_int24_Q7.16",
              "dac_input_format": "offset_binary_u24_after_range_mapping", "state_absmax": STATE_ABSMAX,
              "tt_common_mode_offset_u24": TT_COMMON_MODE_OFFSET_U24,
              "offset_caveat": "provisional common-mode +12544 code offset applied uniformly to both signs; TT schematic only",
              "volts_per_state_unit": SCALE, "vcm_v": VCM, "dac_window_v": [VLO,VHI],
              "tt_dac_rail_shift_v": TT_DAC_RAIL_SHIFT_V,
              "ideal_r_ladder_not_physical_24bit_enob": True, "simulation_completed": completed,
              "exit_code": rc, "dac_restore_error_limit_v": RESTORE_ERROR_LIMIT_V,
              "q716_voltage_lsb_v": q_lsb_v, "max_abs_restore_error_v": max_err,
              "max_abs_error_in_q716_lsb": max_err/q_lsb_v if math.isfinite(max_err) else None,
              "rail_range_restore_smoke_pass": bool(range_smoke), "tested_code_monotonic_pass": bool(measured_monotonic),
              "q716_half_lsb_accuracy_pass": bool(q_precision), "mux_roundtrip_pass": bool(mux_pass),
              "slots": slot_results, "mux_roundtrip": mux,
              "glue_smoke_pass": bool(range_smoke and measured_monotonic and mux_pass)}
    (RES / "sky130_ms_restore_mux_24bit.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2)); print("glue_smoke_pass", report["glue_smoke_pass"])
    return 0 if report["glue_smoke_pass"] else 2

if __name__ == "__main__": raise SystemExit(main())



