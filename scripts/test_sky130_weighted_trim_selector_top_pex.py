"""Simulate the integrated extracted MIM trim array and 32 plate selectors."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
LAYOUT = OUT / "layout/sky130_weighted_trim_selector_top"
CELL = "sky130_weighted_trim_selector_top"
CORNER = next((a.split("=", 1)[1].lower() for a in sys.argv[1:] if a.startswith("--corner=")), "tt")
TEMP_C = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--temp-c=")), {"tt":27,"ss":0,"ff":85}.get(CORNER,27)))
if CORNER not in {"tt","ss","ff"}:
    raise ValueError("corner must be tt, ss, or ff")
NEW_SIM = "--ngspice47" in sys.argv[1:]
IMAGE = "eventspikeseg:analog-ngspice47" if NEW_SIM else "eventspikeseg:analog-ngspice36"
SIM_SUFFIX = "_ngspice47" if NEW_SIM else ""
REDUCED_MIM_SERIES = "--reduce-mim-series" in sys.argv[1:]
if REDUCED_MIM_SERIES:
    SIM_SUFFIX += "_reducedmim"
if CORNER != "tt" or TEMP_C != 27:
    SIM_SUFFIX += f"_{CORNER}_{TEMP_C:g}c"
CODES = {"COARSE_P": 126, "COARSE_N": 129, "FINE_P": 54, "FINE_N": 201}


def main() -> int:
    zero_swing = "--zero-swing" in sys.argv[1:]
    no_leak_return = "--no-leak-return" in sys.argv[1:]
    bypass_mim_via_resistance = "--bypass-mim-via-resistance" in sys.argv[1:]
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    spice = (LAYOUT / f"{CELL}_pex.spice").read_text(encoding="ascii")
    m = re.search(rf"(?im)^\.subckt\s+{CELL}([^\n]*(?:\n\+[^\n]*)*)", spice)
    if not m:
        raise RuntimeError("Missing integrated trim top PEX")
    pins = m.group(1).replace("+", " ").split()
    nodes = []
    for pin in pins:
        m = re.fullmatch(r"STATE_(COARSE_P|COARSE_N|FINE_P|FINE_N)_B\d+", pin)
        if m:
            nodes.append("sa" if m.group(1) in {"COARSE_P","FINE_P"} else "sb")
            continue
        m = re.fullmatch(r"PLATE_(COARSE_P|COARSE_N|FINE_P|FINE_N)_B(\d+)", pin)
        if m:
            nodes.append(f"plate_{m.group(1).lower()}_{m.group(2)}")
            continue
        m = re.fullmatch(r"(PRE|HI|LO)_B(\d+)", pin)
        if m:
            rail, bit = m.group(1), int(m.group(2))
            # Selector index 0..7 coarse P, 8..15 coarse N, 16..23 fine P,
            # 24..31 fine N (matches the weighted-array physical row order).
            bank = ("COARSE_P","COARSE_N","FINE_P","FINE_N")[bit//8]
            if rail == "PRE": node = "vcm"
            elif rail == "HI": node = "hi_coarse" if bank.startswith("COARSE") else "hi_fine"
            else: node = "lo_coarse" if bank.startswith("COARSE") else "lo_fine"
            nodes.append(node)
            continue
        m = re.fullmatch(r"EN(B?)_(PRE|HI|LO)_B(\d+)", pin)
        if m:
            inv, rail, bit_s = m.groups(); bit = int(bit_s)
            bank = ("COARSE_P","COARSE_N","FINE_P","FINE_N")[bit//8]
            if rail == "PRE": node = f"en{'b' if inv else ''}_pre"
            else:
                on = bool(CODES[bank] & (1 << (bit % 8)))
                selected = on if rail == "HI" else not on
                node = f"en{'b' if inv else ''}_{rail.lower()}_{'on' if selected else 'off'}"
            nodes.append(node)
            continue
        if pin.startswith("BULKP_"):
            nodes.append("vdd"); continue
        if pin.startswith("BULKN_"):
            nodes.append("0"); continue
        raise RuntimeError(f"Cannot map integrated pin {pin}")

    lines = ["* Integrated weighted SKY130 MIM trim array + routed 32-selector bank",
        ".option scale=1u reltol=1e-6 abstol=1e-16 vntol=1e-10 method=gear maxord=2",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        '.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
        ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
        ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{CORNER}.corner.spice"',
        f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{CORNER}.corner.spice"',
        f".temp {TEMP_C:g}",
        ('.include "trim_mim_model_no_rs2.spice"' if bypass_mim_via_resistance else ('.include "trim_mim_model_reduced.spice"' if REDUCED_MIM_SERIES else '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"')),
        f'.include "../layout/{CELL}/{CELL}_pex.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
        f"Vhicoarse hi_coarse 0 {0.9 if zero_swing else 0.91}",
        f"Vlo_coarse lo_coarse 0 {0.9 if zero_swing else 0.89}",
        f"Vhi_fine hi_fine 0 {0.9 if zero_swing else 0.90005}",
        f"Vlo_fine lo_fine 0 {0.9 if zero_swing else 0.89995}",
        "Csa sa vcm 21.84p", "Csb sb vcm 21.84p",
        ".model init_sw sw ron=1 roff=1e30 vt=0.9 vh=0.1", "Vinita inita 0 0.9", "Vinitb initb 0 0.9",
        "Vinit_mem init_mem 0 PWL(0 1.8 0.09u 1.8 0.1u 0 5.1m 0)",
        "Sinit_a sa inita init_mem 0 init_sw", "Sinit_b sb initb init_mem 0 init_sw",
        "Vpre en_pre 0 PWL(0 0 0.1u 0 0.11u 1.8 1.0u 1.8 1.01u 0 5.1m 0)",
        "Vpreb enb_pre 0 PWL(0 1.8 0.1u 1.8 0.11u 0 1.0u 0 1.01u 1.8 5.1m 1.8)",
        "Vhi_on en_hi_on 0 PWL(0 0 1.09u 0 1.1u 1.8 5.1m 1.8)",
        "Vhi_onb enb_hi_on 0 PWL(0 1.8 1.09u 1.8 1.1u 0 5.1m 0)",
        "Vhi_off en_hi_off 0 0", "Vhi_offb enb_hi_off 0 1.8",
        "Vlo_on en_lo_on 0 PWL(0 0 1.09u 0 1.1u 1.8 5.1m 1.8)",
        "Vlo_onb enb_lo_on 0 PWL(0 1.8 1.09u 1.8 1.1u 0 5.1m 0)",
        "Vlo_off en_lo_off 0 0", "Vlo_offb enb_lo_off 0 1.8"]
    if not no_leak_return:
        lines[lines.index("Csb sb vcm 21.84p") + 1:lines.index("Csb sb vcm 21.84p") + 1] = ["Rsa sa vcm 1e12", "Rsb sb vcm 1e12"]
    # All membrane-equivalent state pins are joined to sa/sb above; PEX MIMs
    # already supply the physical weighted capacitor array.
    lines += [f"Xtrim {' '.join(nodes)} {CELL}", ".control", "set wr_singlescale", "set wr_vecnames",
        "tran 1u 5.1m 0 1u uic",
        f"wrdata ../results/{CELL}_pex{SIM_SUFFIX}.dat v(sa) v(sb) v(plate_coarse_p_0) v(plate_coarse_n_0) v(plate_fine_p_0) v(plate_fine_n_0)",
        "quit", ".endc", ".end"]
    deck = BENCH / f"{CELL}_pex{SIM_SUFFIX}.cir"
    if bypass_mim_via_resistance:
        model=(OUT/"pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice").read_text(encoding="ascii")
        model=model.replace("rs2 b1        c1 'r2' tc1 = {tc1rvia4} tc2 = {tc2rvia4}", "rs2 b1        c1 0")
        (BENCH/"trim_mim_model_no_rs2.spice").write_text(model,encoding="ascii")
    if REDUCED_MIM_SERIES:
        model=(OUT/"pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice").read_text(encoding="ascii")
        model=model.replace("c1 c0       a 'czero' tc1 = 0 tc2 = 0.0\nrs1 a        b1 'r1' tc1 = {tc1rm4} tc2 = {tc2rm4}\nrs2 b1        c1 'r2' tc1 = {tc1rvia4} tc2 = {tc2rvia4}", "c1 c0       c1 'czero' tc1 = 0 tc2 = 0.0")
        (BENCH/"trim_mim_model_reduced.spice").write_text(model,encoding="ascii")
    deck.write_text("\n".join(lines)+"\n", encoding="ascii")
    dat = RES / f"{CELL}_pex{SIM_SUFFIX}.dat"
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v", f"{ROOT}:/workspace:ro",
        "-v", f"{OUT}:/workspace/artifacts/analog_asic", "-w", "/workspace/artifacts/analog_asic/benches",
        "--entrypoint", "timeout", IMAGE, "180", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=195, cwd=ROOT)
    log = run.stdout + run.stderr
    (RES / f"{CELL}_pex{SIM_SUFFIX}.log").write_text(log, encoding="utf-8")
    rows=[]
    if dat.exists():
        for line in dat.read_text(encoding="utf-8").splitlines()[1:]:
            try: rows.append([float(x) for x in line.split()])
            except ValueError: pass
    complete = run.returncode == 0 and len(rows)>100 and "ngspice-36 done" in log.lower() and "tran simulation(s) aborted" not in log.lower()
    if not complete: raise RuntimeError(f"Integrated trim PEX sim failed, rc={run.returncode}, points={len(rows)}\n{log[-3500:]}")
    def near(t_us): return min(rows,key=lambda r:abs(r[0]-t_us*1e-6))
    at_pre, at_start, at_5ms = near(0.9), near(2.0), near(4900.0)
    vdiff_uv=(at_5ms[1]-at_5ms[2])*1e6
    report={"test":"sky130_integrated_weighted_trim_array_selector_pex","completed":complete,
        "process_corner":CORNER,"temperature_c":TEMP_C,"simulated_mim_units":1020,"selector_devices":192,
        "codes":CODES,"rail_swing_bypassed":zero_swing,"weak_return_resistors_removed":no_leak_return,"diagnostic_mim_via_resistance_bypassed":bypass_mim_via_resistance,"diagnostic_mim_series_reduced_to_nominal_capacitance":REDUCED_MIM_SERIES,"sample_cap_pf_each":21.84,
        "state_v_at_precharge_sample":[at_pre[1],at_pre[2]],"state_v_after_trim_update":[at_start[1],at_start[2]],
        "state_v_at_4p9ms":[at_5ms[1],at_5ms[2]],"trim_differential_at_4p9ms_uv":vdiff_uv,
        "scope":"Combined 1020-MIM/96-TG routed PEX, ideal per-bit decoded controls, 20mV coarse and0.1mV fine rails; no comparator, chopper, mismatch/noise, decoder layout, or model replay."}
    report["simulator"] = "ngspice-47" if NEW_SIM else "ngspice-36"
    (RES/f"{CELL}_pex{SIM_SUFFIX}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
