"""Exercise all 32 routed trim selectors through a 5ms extracted transient."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
LAYOUT = OUT / "layout/sky130_trim_plate_selector_bank32"
CELL = "sky130_trim_plate_selector_bank32"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    spice = (LAYOUT / f"{CELL}_pex.spice").read_text(encoding="ascii")
    m = re.search(rf"(?im)^\.subckt\s+{CELL}([^\n]*(?:\n\+[^\n]*)*)", spice)
    if not m:
        raise RuntimeError("Missing extracted 32-bit selector subcircuit")
    pins = m.group(1).replace("+", " ").split()
    pin_nodes: list[str] = []
    for pin in pins:
        mat = re.fullmatch(r"(PRE|HI|LO)_B(\d+)", pin)
        if mat:
            pin_nodes.append({"PRE": "vcm", "HI": "vhi", "LO": "vlo"}[mat.group(1)])
            continue
        mat = re.fullmatch(r"EN(B?)_(PRE|HI|LO)_B(\d+)", pin)
        if mat:
            pin_nodes.append(f"en{'b' if mat.group(1) else ''}_{mat.group(2).lower()}_{mat.group(3)}")
            continue
        mat = re.fullmatch(r"PLATE_B(\d+)", pin)
        if mat:
            pin_nodes.append(f"plate_{mat.group(1)}")
            continue
        if pin.startswith("BULKP_"):
            pin_nodes.append("vdd")
            continue
        if pin.startswith("BULKN_"):
            pin_nodes.append("0")
            continue
        raise RuntimeError(f"Unmapped extracted bank port: {pin}")

    lines = ["* Full 32-bit extracted selector bank, alternating code and 5ms rail update",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        '.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
        ".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
        ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",
        '.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
        f'.include "../layout/{CELL}/{CELL}_pex.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vhi vhi 0 0.98", "Vlo vlo 0 0.82"]
    for bit in range(32):
        # Precharge all plates together, then hold a real driven code. Even
        # bits select HI and odd bits LO for 5ms, then the selections swap.
        lines += [f"Vpre{bit} en_pre_{bit} 0 PWL(0 0 0.1u 0 0.11u 1.8 1.0u 1.8 1.01u 0 5.1m 0)",
                  f"Vpreb{bit} enb_pre_{bit} 0 PWL(0 1.8 0.1u 1.8 0.11u 0 1.0u 0 1.01u 1.8 5.1m 1.8)"]
        high_first = bit % 2 == 0
        for rail, first in (("hi", high_first), ("lo", not high_first)):
            on0, off0 = (1.1e-6, 5.0e-3) if first else (5.01e-3, 5.09e-3)
            off_edge, on_edge = off0 + 1e-6, on0 - 1e-8
            if first:
                control = f"PWL(0 0 {on_edge:g} 0 {on0:g} 1.8 {off0:g} 1.8 {off_edge:g} 0 5.1m 0)"
            else:
                control = f"PWL(0 0 {on_edge:g} 0 {on0:g} 1.8 {off0:g} 1.8 {off_edge:g} 0 5.1m 0)"
            # Build complement explicitly to avoid changing the time tokens.
            p = re.findall(r"([-+\d.eE]+)\s+([-+\d.eE]+)", control[5:-1])
            pairs = [(t, "0" if v == "1.8" else "1.8") for t, v in p]
            inv = "PWL(" + " ".join(f"{t} {v}" for t,v in pairs) + ")"
            lines += [f"V{rail}{bit} en_{rail}_{bit} 0 {control}",
                      f"V{rail}b{bit} enb_{rail}_{bit} 0 {inv}"]
        lines += [f"Cload{bit} plate_{bit} 0 10f", f"Rleak{bit} plate_{bit} vcm 1e12"]
    lines += [f"Xbank {' '.join(pin_nodes)} {CELL}", ".control", "set wr_singlescale", "set wr_vecnames",
        "tran 10u 5.1m 0 10u uic",
        "wrdata ../results/sky130_trim_plate_selector_bank32_pex.dat v(plate_0) v(plate_1) v(plate_30) v(plate_31)",
        "quit", ".endc", ".end"]
    deck = BENCH / f"{CELL}_pex.cir"
    deck.write_text("\n".join(lines)+"\n", encoding="ascii")
    dat = RES / f"{CELL}_pex.dat"
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "-v", f"{ROOT}:/workspace:ro",
        "-v", f"{OUT}:/workspace/artifacts/analog_asic", "-w", "/workspace/artifacts/analog_asic/benches",
        "--entrypoint", "timeout", IMAGE, "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=135, cwd=ROOT)
    log = run.stdout + run.stderr
    (RES / f"{CELL}_pex.log").write_text(log, encoding="utf-8")
    rows = []
    if dat.exists():
        for line in dat.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                pass
    complete = run.returncode == 0 and len(rows) > 100 and "ngspice-36 done" in log.lower() and "tran simulation(s) aborted" not in log.lower()
    if not complete:
        raise RuntimeError(f"Full bank extracted transient failed, rc={run.returncode}, points={len(rows)}\n{log[-3000:]}")
    def near(t: float) -> list[float]:
        return min(rows, key=lambda r: abs(r[0] - t*1e-6))
    vals = {"bit0_hi_at_4p9ms_v": near(4.9e3)[1], "bit1_lo_at_4p9ms_v": near(4.9e3)[2],
            "bit0_lo_after_update_v": near(5.05e3)[1], "bit1_hi_after_update_v": near(5.05e3)[2],
            "bit30_lo_after_update_v": near(5.05e3)[3], "bit31_hi_after_update_v": near(5.05e3)[4]}
    report = {"test": "sky130_32bit_trim_selector_bank_extracted_transient", "completed": complete,
        "process_corner": "tt", "temperature_c": 27, "selector_bits": 32, "simulated_devices": 192,
        "measurement_v": vals, "targets_v": {"hi": 0.98, "lo": 0.82},
        "scope": "Full routed/extracted 32-bit bank, all plates loaded by10fF and all precharged then rail driven; external independent ideal controls, no decoder or MIM-array connection."}
    (RES / f"{CELL}_pex.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
