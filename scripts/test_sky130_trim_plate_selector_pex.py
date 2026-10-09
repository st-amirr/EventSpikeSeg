"""Transient-test the extracted one-bit precharge/HI/LO selector."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
LAYOUT = OUT / "layout/sky130_trim_plate_selector"
IMAGE = "eventspikeseg:analog-ngspice36"


def main() -> int:
    args = sys.argv[1:]
    corner = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--corner=")), "tt")
    temp = float(next((a.split("=", 1)[1] for a in args if a.startswith("--temp-c=")), {"tt": 27, "ss": 0, "ff": 85}.get(corner, 27)))
    if corner not in {"tt", "ss", "ff"}:
        raise ValueError("corner must be tt, ss, or ff")
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    deck = BENCH / "sky130_trim_plate_selector_pex.cir"
    dat = RES / f"sky130_trim_plate_selector_pex_{corner}.dat"
    logpath = RES / f"sky130_trim_plate_selector_pex_{corner}.log"
    source = r"""* Extracted SKY130 MIM plate-selector transient
.option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__CORNER__.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__CORNER__.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../layout/sky130_trim_plate_selector/sky130_trim_plate_selector_pex.spice"
VDD vdd 0 1.8
VCM vcm 0 0.9
VPRE pre 0 0.9
VHI hi 0 0.98
VLO lo 0 0.82
Vpre_en en_pre 0 PWL(0 0 0.1u 0 0.11u 1.8 1.0u 1.8 1.01u 0 5.1m 0)
Vpre_enb enb_pre 0 PWL(0 1.8 0.1u 1.8 0.11u 0 1.0u 0 1.01u 1.8 5.1m 1.8)
Vhi_en en_hi 0 PWL(0 0 1.09u 0 1.1u 1.8 5.0m 1.8 5.001m 0 5.1m 0)
Vhi_enb enb_hi 0 PWL(0 1.8 1.09u 1.8 1.1u 0 5.0m 0 5.001m 1.8 5.1m 1.8)
Vlo_en en_lo 0 PWL(0 0 5.009m 0 5.01m 1.8 5.09m 1.8 5.091m 0 5.1m 0)
Vlo_enb enb_lo 0 PWL(0 1.8 5.009m 1.8 5.01m 0 5.09m 0 5.091m 1.8 5.1m 1.8)
Rplate plate vcm 1e12
Cload plate 0 10f
Xsel pre en_pre enb_pre hi en_hi enb_hi lo en_lo enb_lo 0 plate vdd vdd vdd sky130_trim_plate_selector
.control
set wr_singlescale
set wr_vecnames
tran 10u 5.1m 0 10u uic
wrdata ../results/sky130_trim_plate_selector_pex.dat v(plate) v(pre) v(hi) v(lo)
quit
.endc
.end
"""
    source = source.replace("__CORNER__", f"__{corner}")
    # Set the device temperature explicitly; ngspice still uses the model's
    # nominal TNOM of 27C.
    source = source.replace(".param sky130_fd_pr__res_high_po__slope_spectre", f".temp {temp:g}\n.param sky130_fd_pr__res_high_po__slope_spectre")
    source = source.replace("sky130_trim_plate_selector_pex.dat", f"sky130_trim_plate_selector_pex_{corner}.dat")
    deck.write_text(source, encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2", "-v", f"{ROOT}:/workspace:ro",
        "-v", f"{OUT}:/workspace/artifacts/analog_asic",
        "-w", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", IMAGE,
        "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=75, cwd=ROOT)
    log = run.stdout + run.stderr
    logpath.write_text(log, encoding="utf-8")
    rows = []
    if dat.exists():
        for line in dat.read_text(encoding="utf-8").splitlines()[1:]:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                pass
    complete = run.returncode == 0 and len(rows) > 20 and "ngspice-36 done" in log.lower() and "tran simulation(s) aborted" not in log.lower()
    if not complete:
        raise RuntimeError(f"Extracted selector transient failed: rc={run.returncode}, points={len(rows)}\n{log[-3000:]}")
    def near(t: float) -> list[float]:
        return min(rows, key=lambda r: abs(r[0] - t*1e-6))
    measured = {"precharge_v": near(0.9)[1], "hi_5ms_v": near(4.9e3)[1],
                "lo_selected_v": near(5.05e3)[1]}
    report = {"test": "sky130_extracted_trim_plate_selector_transient", "process_corner": corner, "temperature_c": temp, "completed": complete,
        "measurement_v": measured, "targets_v": {"precharge_v": 0.9, "hi_5ms_v": 0.98, "lo_selected_v": 0.82},
        "scope": f"{corner.upper()} schematic controls driving routed/extracted three-TG selector with 10fF load; HI remains actively selected for nearly 5ms and LO for 40us. No decoder, mismatch/noise, or integrated array yet."}
    (RES / f"sky130_trim_plate_selector_pex_{corner}.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
