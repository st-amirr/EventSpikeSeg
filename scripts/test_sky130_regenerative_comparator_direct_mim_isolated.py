"""Bound direct clocked comparison of two physical SKY130 MIM state capacitors."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

from characterize_sky130_sensor_vth_mismatch import PDK_MODEL, make_variant

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
DELTAS_UV = tuple(float(x) for x in next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--deltas-uv=")), "-6,-0.537257883,0,0.537257883,6").split(","))
STATE_SCALE = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--state-scale=")), "1000"))
VCM = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--vcm=")), "0.9"))
READ_FALL_NS = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--read-fall-ns=")), "20"))
READ_N_WIDTH = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--read-n-width=")), "1"))
PDK_MISMATCH = "--pdk-vth-1sigma" in sys.argv[1:]
SWAP_MISMATCH = "--swap-mismatch" in sys.argv[1:]
TRIM_UV = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--trim-uv=")), "0"))
PHYSICAL_TRIM_DAC = "--physical-trim-dac" in sys.argv[1:]
TRIM_CODE = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--trim-code=")), str((1 << 23) - 1)))
TRIM_BITS = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--trim-bits=")), "24"))
TRIM_R_OHMS = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--trim-r-ohms=")), "1000"))
TRIM_SWITCH_M = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--trim-switch-m=")), "100"))
PHYSICAL_CAP_TRIM_ARRAY = "--physical-cap-trim-array" in sys.argv[1:]
CAP_TRIM_CODE = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--cap-trim-code=")), "128"))
CAP_TRIM_FINE_CODE = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--cap-trim-fine-code=")), "128"))
CAP_COARSE_SWING_MV = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--cap-coarse-swing-mv=")), "90"))
CAP_FINE_SWING_MV = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--cap-fine-swing-mv=")), "0.4"))
BIN_END_US = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--bin-end-us=")), "2.73"))
MAX_STEP_NS = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--max-step-ns=")), "2"))
CORNER = next((a.split("=", 1)[1].lower() for a in sys.argv[1:] if a.startswith("--corner=")), "tt")
TEMP_C = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--temp-c=")), "27"))


def main() -> int:
    read_finish_us = 2.73 + READ_FALL_NS * 1e-3
    if CORNER not in ("tt", "ss", "ff"):
        raise ValueError("corner must be tt, ss or ff")
    if PDK_MISMATCH and CORNER != "tt":
        raise ValueError("deterministic published mismatch variants are currently TT-only")
    if BIN_END_US < read_finish_us or MAX_STEP_NS <= 0:
        raise ValueError("bin-end-us must cover the read window and max-step-ns must be positive")
    read_shift_us = BIN_END_US - read_finish_us
    if not 0 <= TRIM_CODE <= 0xFFFFFF:
        raise ValueError("physical trim code must be an unsigned 24-bit value")
    if TRIM_BITS not in (12, 24):
        raise ValueError("trim-bits must be 12 or 24")
    if TRIM_BITS == 12 and TRIM_CODE % 4096:
        raise ValueError("12-bit trim code must be aligned to the upper 12 bits")
    if TRIM_R_OHMS <= 0 or TRIM_SWITCH_M <= 0:
        raise ValueError("trim resistor and switch multiplicity must be positive")
    if PHYSICAL_TRIM_DAC and TRIM_UV:
        raise ValueError("choose either the physical trim DAC or the ideal trim diagnostic")
    if PHYSICAL_CAP_TRIM_ARRAY and (PHYSICAL_TRIM_DAC or TRIM_UV):
        raise ValueError("choose one comparator offset-trim method")
    if PHYSICAL_CAP_TRIM_ARRAY and not (0 <= CAP_TRIM_CODE <= 255 and 0 <= CAP_TRIM_FINE_CODE <= 255 and CAP_COARSE_SWING_MV > 0 and CAP_FINE_SWING_MV > 0):
        raise ValueError("capacitor-trim codes must be 8-bit and plate swings must be positive")
    suffix = ("_pdkvth1sigma_swap" if PDK_MISMATCH and SWAP_MISMATCH else
              "_pdkvth1sigma" if PDK_MISMATCH else "") + (f"_trim{TRIM_UV:g}uv" if TRIM_UV else "")
    if PHYSICAL_TRIM_DAC:
        suffix += f"_physicaltrim{TRIM_BITS}_code{TRIM_CODE}"
        if TRIM_BITS == 12:
            suffix += f"_r{TRIM_R_OHMS:g}_m{TRIM_SWITCH_M}"
    if PHYSICAL_CAP_TRIM_ARRAY:
        suffix += f"_physicalcaptrim_c{CAP_TRIM_CODE}_f{CAP_TRIM_FINE_CODE}"
    lines = [
        "SKY130 direct clocked comparator reading floating physical MIM state",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        f".temp {TEMP_C:g}",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{CORNER}.corner.spice"',
        f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{CORNER}.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
        '.include "../../../asic/analog/modules.spice"',
        '.include "../../../asic/analog/sky130_ms_plif.spice"',
        "Vdd vdd 0 1.8", f"Vcm vcm 0 {VCM:g}",
        "Vinit init 0 PWL(0 1.8 2.49u 1.8 2.51u 0 2.75u 0)",
        "Vinitb initb 0 PWL(0 0 2.49u 0 2.51u 1.8 2.75u 1.8)",
        f"Vpre pre 0 PWL(0 1.8 {read_shift_us+2.555:g}u 1.8 {read_shift_us+2.565:g}u 0 {BIN_END_US:g}u 0)",
        f"Vpreb preb 0 PWL(0 0 {read_shift_us+2.555:g}u 0 {read_shift_us+2.565:g}u 1.8 {BIN_END_US:g}u 1.8)",
        f"Vread read 0 PWL(0 0 {read_shift_us+2.57:g}u 0 {read_shift_us+2.58:g}u 1.8 {read_shift_us+2.66:g}u 1.8 {read_shift_us+2.66+READ_FALL_NS*1e-3:g}u 0 {BIN_END_US:g}u 0)",
        f"Vreadb readb 0 PWL(0 1.8 {read_shift_us+2.57:g}u 1.8 {read_shift_us+2.58:g}u 0 {read_shift_us+2.66:g}u 0 {read_shift_us+2.66+READ_FALL_NS*1e-3:g}u 1.8 {BIN_END_US:g}u 1.8)",
        f"Vclk clk 0 PWL(0 0 {read_shift_us+2.63:g}u 0 {read_shift_us+2.65:g}u 1.8 {BIN_END_US:g}u 1.8)",
        ".subckt range_read_tg a b en enb vdd vss",
        f"Xrn a en b vss sky130_fd_pr__nfet_01v8 w={READ_N_WIDTH:g} l=0.5",
        f"Xrp a enb b vdd sky130_fd_pr__pfet_01v8 w={2*READ_N_WIDTH:g} l=0.5",
        ".ends range_read_tg",
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
    if PHYSICAL_CAP_TRIM_ARRAY:
        lines.insert(10, '.include "../layout/sky130_cap_trim_weighted_array/sky130_cap_trim_weighted_array_pex.spice"')
    if PHYSICAL_TRIM_DAC:
        dac_max = (1 << TRIM_BITS) - 1
        code_p = TRIM_CODE if TRIM_BITS == 24 else TRIM_CODE >> 12
        code_n = dac_max - code_p
        lines += ["Vtrim_hi trim_hi 0 0.95", "Vtrim_lo trim_lo 0 0.85"]
        if TRIM_BITS == 12:
            r = f"{TRIM_R_OHMS:g}"
            r2 = f"{2*TRIM_R_OHMS:g}"
            dac_lines = [
                ".subckt r2r_trim_switch a b en enb vdd vss",
                f"Xn a en b 0 sky130_fd_pr__nfet_01v8 w=1 l=0.15 m={TRIM_SWITCH_M}",
                f"Xp a enb b vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15 m={TRIM_SWITCH_M}",
                ".ends r2r_trim_switch",
                ".subckt r2r_dac_u12 out b11 b10 b9 b8 b7 b6 b5 b4 b3 b2 b1 b0 vhi vlo vdd vss"]
            for bit in range(12):
                dac_lines.append(f"Xiv{bit} b{bit} bb{bit} vdd vss r2r_inv")
            dac_lines.append(f"Rterm n0 vlo {r2}")
            for bit in range(11, 0, -1):
                left = "out" if bit == 11 else f"n{bit}"
                dac_lines.append(f"Rq{bit} {left} n{bit-1} {r}")
            for bit in range(11, -1, -1):
                tap = "out" if bit == 11 else f"n{bit}"
                dac_lines += [f"R2b{bit} {tap} m{bit} {r2}",
                              f"Xth{bit} vhi m{bit} b{bit} bb{bit} vdd vss r2r_trim_switch",
                              f"Xtl{bit} vlo m{bit} bb{bit} b{bit} vdd vss r2r_trim_switch"]
            dac_lines.append(".ends r2r_dac_u12")
            lines += dac_lines
        for bit in range(TRIM_BITS):
            lines += [f"Vdacp{bit} dacp{bit} 0 {(code_p >> bit) & 1}",
                      f"Vdacn{bit} dacn{bit} 0 {(code_n >> bit) & 1}"]
        pins_p = " ".join(f"dacp{bit}" for bit in range(TRIM_BITS-1, -1, -1))
        pins_n = " ".join(f"dacn{bit}" for bit in range(TRIM_BITS-1, -1, -1))
        dac_subckt = f"r2r_dac_u{TRIM_BITS}"
        lines += [f"Xdacp trim_p {pins_p} trim_hi trim_lo vdd 0 {dac_subckt}",
                  f"Xdacn trim_n {pins_n} trim_hi trim_lo vdd 0 {dac_subckt}"]
    if PDK_MISMATCH:
        source = PDK_MODEL.read_text(encoding="ascii")
        plus = make_variant(source, "plus", 1)
        minus = make_variant(source, "minus", -1)
        model_dir = BENCH / "diff_sensor_probe"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "nfet_vthsigma_plus.spice").write_text(plus, encoding="ascii")
        (model_dir / "nfet_vthsigma_minus.spice").write_text(minus, encoding="ascii")
        lines += ['.include "diff_sensor_probe/nfet_vthsigma_plus.spice"',
                  '.include "diff_sensor_probe/nfet_vthsigma_minus.spice"']
    if PDK_MISMATCH:
        for i, line in enumerate(lines):
            if line.startswith("Xin_p "):
                lines[i] = line.replace("sky130_fd_pr__nfet_01v8", "nfet_vthsigma_minus" if SWAP_MISMATCH else "nfet_vthsigma_plus")
            elif line.startswith("Xin_n "):
                lines[i] = line.replace("sky130_fd_pr__nfet_01v8", "nfet_vthsigma_plus" if SWAP_MISMATCH else "nfet_vthsigma_minus")
    vectors = []
    for delta in DELTAS_UV:
        tag = f"d{delta:g}".replace("-", "m").replace(".", "p")
        signal = f"mem_{tag}"
        reference = f"ref_{tag}"
        inp = f"inp_{tag}"
        inn = f"inn_{tag}"
        regen_inp, regen_inn = inp, inn
        trim_vectors = []
        if TRIM_UV:
            regen_inp, regen_inn = f"{inp}_trim", f"{inn}_trim"
            lines += [f"Vtrim_p_{tag} {regen_inp} {inp} DC {TRIM_UV*0.5:g}u",
                      f"Vtrim_n_{tag} {regen_inn} {inn} DC {-TRIM_UV*0.5:g}u"]
            trim_vectors = [f"v({regen_inp})", f"v({regen_inn})"]
        lines += [
            f"Vtarget_{tag} target_{tag} 0 {VCM+delta*1e-6*STATE_SCALE:.12f}",
            f"Xcmem_{tag} {signal} vcm membrane_mim w_um=100 l_um=100",
            f"Xcref_{tag} {reference} vcm membrane_mim w_um=100 l_um=100",
            f"Xinit_mem_{tag} target_{tag} {signal} init initb vdd 0 transmission_gate",
            f"Xinit_ref_{tag} vcm {reference} init initb vdd 0 transmission_gate",
            f"Xpre_inp_{tag} {inp} vcm pre preb vdd 0 transmission_gate",
            f"Xpre_inn_{tag} {inn} vcm pre preb vdd 0 transmission_gate",
            f"Xread_mem_{tag} {signal} {'sig_sample_'+tag if PHYSICAL_TRIM_DAC else inp} read readb vdd 0 range_read_tg",
            f"Xread_ref_{tag} {reference} {'ref_sample_'+tag if PHYSICAL_TRIM_DAC else inn} read readb vdd 0 range_read_tg",
            f"Xregen_{tag} {regen_inp} {regen_inn} clk op_{tag} on_{tag} vdd 0 regen",
            f"Cloadp_{tag} op_{tag} 0 20f", f"Cloadn_{tag} on_{tag} 0 20f",
        ]
        if PHYSICAL_TRIM_DAC:
            lines += [f"Rstate_p_{tag} sig_sample_{tag} {inp} 1Meg",
                      f"Rtrim_p_{tag} trim_p {inp} 1Meg",
                      f"Rstate_n_{tag} ref_sample_{tag} {inn} 1Meg",
                      f"Rtrim_n_{tag} trim_n {inn} 1Meg"]
        if PHYSICAL_CAP_TRIM_ARRAY:
            # Connect the routed 1,020-cell differential coarse/fine MIM bank
            # directly to the comparator sampling nodes. This first integration
            # evaluates PEX charge-transfer capacity with ideal plate selections;
            # the physical selector/decoder remains a separate layout gate.
            trim_start = read_shift_us + 2.59
            trim_stop = read_shift_us + 2.64
            bank_pins: list[str] = []
            for bank, code, state_node, swing_mv in (
                ("COARSE_P", CAP_TRIM_CODE, inp, CAP_COARSE_SWING_MV),
                ("COARSE_N", 255-CAP_TRIM_CODE, inn, CAP_COARSE_SWING_MV),
                ("FINE_P", CAP_TRIM_FINE_CODE, inp, CAP_FINE_SWING_MV),
                ("FINE_N", 255-CAP_TRIM_FINE_CODE, inn, CAP_FINE_SWING_MV),
            ):
                swing = swing_mv * 1e-3
                for bit in range(8):
                    plate = f"captrim_{tag}_{bank.lower()}_{bit}"
                    bank_pins.extend([state_node, plate])
                    level = VCM + (swing/2 if (code >> bit) & 1 else -swing/2)
                    lines.append(f"V{plate} {plate} 0 PWL(0 {VCM:.9f} {trim_start-0.01:g}u {VCM:.9f} {trim_start:g}u {level:.9f} {trim_stop:g}u {level:.9f} {trim_stop+0.01:g}u {VCM:.9f} {BIN_END_US:g}u {VCM:.9f})")
            lines.append(f"Xcaptrim_{tag} " + " ".join(bank_pins) + " sky130_cap_trim_weighted_array")
        vectors += [f"v(op_{tag})", f"v(on_{tag})", f"v({signal})", f"v({reference})", f"v({inp})", f"v({inn})", *trim_vectors]
    delta_tag = "_".join(str(x).replace("-", "m").replace(".", "p") for x in DELTAS_UV)
    bin_tag = f"_bin{BIN_END_US:g}u_step{MAX_STEP_NS:g}n" if BIN_END_US != 2.73 or MAX_STEP_NS != 2 else ""
    corner_tag = f"_{CORNER}_t{TEMP_C:g}c" if CORNER != "tt" or TEMP_C != 27 else ""
    stem = f"sky130_regenerative_comparator_direct_mim_isolated_vcm{VCM:g}_scale{STATE_SCALE:g}_deltas{delta_tag}_readfall{READ_FALL_NS:g}ns_readn{READ_N_WIDTH:g}um" + suffix + corner_tag + bin_tag
    deck = BENCH / f"{stem}.cir"
    data = RES / f"{stem}.dat"
    stop_us = BIN_END_US
    lines += [".control", "set wr_singlescale", "set wr_vecnames", f"tran {MAX_STEP_NS:g}n {stop_us:g}u uic", f"wrdata ../results/{data.name} " + " ".join(vectors), "quit", ".endc", ".end"]
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=150)
    log = run.stdout + run.stderr
    (RES / f"{stem}.log").write_text(log, encoding="utf-8")
    raw = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                row = [float(value) for value in line.split()]
                if len(row) == 1 + (8 if TRIM_UV else 6) * len(DELTAS_UV):
                    raw.append(row)
            except ValueError:
                continue
    completed = (run.returncode == 0 and len(raw) > 100 and "ngspice-36 done" in log.lower()
                 and "tran simulation(s) aborted" not in log.lower())
    trim_diff_uv = ((2*TRIM_CODE-0xFFFFFF)/0x1000000)*100_000 if PHYSICAL_TRIM_DAC else None
    report = {"test": "sky130_clocked_comparator_direct_physical_mim_state", "simulation_completed": completed, "return_code": run.returncode, "corner": CORNER.upper(), "temperature_c": TEMP_C, "input_differentials_uv": list(DELTAS_UV), "physical_state_voltage_scale": STATE_SCALE, "common_mode_v": VCM, "membrane_and_reference_mim_um": 100, "bin_end_us": BIN_END_US, "read_window_shift_us": read_shift_us, "max_transient_step_ns": MAX_STEP_NS, "evaluation_ns": (read_shift_us+2.65)*1000, "read_switch_open_start_ns": (read_shift_us+2.66)*1000, "read_switch_fall_ns": READ_FALL_NS, "read_nfet_width_um": READ_N_WIDTH, "read_pfet_width_um": 2*READ_N_WIDTH, "pdk_input_vth_mismatch_1sigma": PDK_MISMATCH, "pdk_mismatch_swapped": SWAP_MISMATCH if PDK_MISMATCH else None, "ideal_differential_trim_uv": TRIM_UV, "physical_trim_dac_enabled": PHYSICAL_TRIM_DAC, "physical_trim_dac_bits": TRIM_BITS if PHYSICAL_TRIM_DAC else None, "physical_trim_dac_code24_aligned": TRIM_CODE if PHYSICAL_TRIM_DAC else None, "physical_trim_dac_code": (TRIM_CODE if TRIM_BITS == 12 else TRIM_CODE >> 12) if PHYSICAL_TRIM_DAC else None, "trim_r_ohms": TRIM_R_OHMS if PHYSICAL_TRIM_DAC and TRIM_BITS == 12 else None, "trim_switch_multiplicity": TRIM_SWITCH_M if PHYSICAL_TRIM_DAC and TRIM_BITS == 12 else None, "physical_trim_nominal_differential_uv": trim_diff_uv, "physical_cap_trim_array_enabled": PHYSICAL_CAP_TRIM_ARRAY, "cap_trim_code": CAP_TRIM_CODE if PHYSICAL_CAP_TRIM_ARRAY else None, "cap_trim_fine_code": CAP_TRIM_FINE_CODE if PHYSICAL_CAP_TRIM_ARRAY else None, "cap_trim_plate_swings_mv": [CAP_COARSE_SWING_MV, CAP_FINE_SWING_MV] if PHYSICAL_CAP_TRIM_ARRAY else None, "scope": (f"{CORNER.upper()}/{TEMP_C:g}C physical SKY130 MIM state and PDK read switches plus regenerative latch; integrated routed 1020-cell MIM trim-array PEX with ideal plate-selection waveforms, no selector/decoder layout, mismatch/noise Monte Carlo or network replay" if PHYSICAL_CAP_TRIM_ARRAY else f"{CORNER.upper()}/{TEMP_C:g}C physical SKY130 MIM state and PDK read switches plus regenerative latch; optional complementary {TRIM_BITS}-section PDK-switched R-2R ladders use {TRIM_R_OHMS:g}ohm R legs and {TRIM_SWITCH_M}x MOS switches over a200mV rail span and inject through matched1Meg resistors; deterministic paired ±1sigma input NFET Vth realization when requested (TT only); no DAC resistor mismatch/extraction/noise or network replay")}
    if completed:
        def at(ns):
            return min(raw, key=lambda row: abs(row[0] - ns * 1e-9))
        for index, delta in enumerate(DELTAS_UV):
            stride = 8 if TRIM_UV else 6
            base = 1 + stride * index
            points = {}
            before_ns = read_shift_us*1000 + 2568
            preeval_ns = read_shift_us*1000 + 2629.8
            decision_ns = read_shift_us*1000 + 2670
            after_ns = (read_shift_us + 2.66 + READ_FALL_NS*1e-3 + 0.01) * 1000
            for ns in (before_ns, read_shift_us*1000 + 2590, preeval_ns, read_shift_us*1000 + 2635, decision_ns, after_ns):
                row = at(ns)
                points[str(ns)] = {"state_diff_uv": (row[base+2] - row[base+3]) * 1e6, "signal_state_v": row[base+2], "reference_state_v": row[base+3], "latch_input_diff_uv": (row[base+6] - row[base+7]) * 1e6 if TRIM_UV else (row[base+4] - row[base+5]) * 1e6, "output_diff_v": row[base] - row[base+1]}
            before = points[str(before_ns)]["state_diff_uv"]
            preeval = points[str(preeval_ns)]["state_diff_uv"]
            after = points[str(after_ns)]["state_diff_uv"]
            decision = points[str(decision_ns)]["output_diff_v"]
            report.setdefault("measurements", []).append({"source_input_uv": delta, "state_diff_before_read_uv": before, "state_diff_preeval_uv": preeval, "state_diff_after_read_uv": after, "read_state_disturbance_uv": after-before, "decision_after_20ns_v": decision, "decision_matches_preeval_state": (decision > 0) == (preeval < 0) if delta else None, "points": points})
    (RES / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if completed else 1

if __name__ == "__main__":
    raise SystemExit(main())
