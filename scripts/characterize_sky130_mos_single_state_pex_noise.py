"""Measure reset-TG noise for one extracted SKY130 MOS gate-state rail."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
PDK = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A"
LAYOUTS = ("sky130_mos_gate_bank_10x1_nf10", "sky130_mos_gate_bank_20x2_nf10",
           "sky130_mos_gate_bank_100x10_nf10")


def run(layout: str, corner: str, temp: int) -> dict[str, object]:
    cell = layout.removeprefix("sky130_")
    tag = f"sky130_mos_single_state_pex_noise_{cell}_{corner}_temp{temp}"
    bench = OUT / "benches" / f"{tag}.cir"
    bench.parent.mkdir(parents=True, exist_ok=True)
    deck = f'''* Extracted single-rail MOS gate-cap and reset-TG noise
.option scale=1u
.temp {temp}
.include "{MODEL}/models/parameters/invariant.spice"
.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"
.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../layout/{layout}/{cell}.spice"
.include "../layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vdrive drive 0 dc 0.9 ac 1
Ven en 0 1.8
Venb enb 0 0
Xreset drive state en enb vdd 0 sky130_transmission_gate_raw
Xstate state vcm 0 {cell}
.control
set numdgt=15
noise v(state,vcm) Vdrive dec 20 10 100meg
print onoise_total
print inoise_total
quit
.endc
.end
'''
    bench.write_text(deck, encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", bench.name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=135)
    log = proc.stdout + proc.stderr
    results = OUT / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{tag}.log").write_text(log, encoding="utf-8")
    vals = {k.lower(): float(v) for k, v in re.findall(
        r"(?im)^\s*(onoise_total|inoise_total)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(vals) != {"onoise_total", "inoise_total"}:
        raise RuntimeError(f"single-state PEX noise failed for {tag}:\n{log[-4000:]}")
    qual = json.loads((OUT / "layout" / layout / "qualification.json").read_text())
    c_f = qual.get("extracted_cgate_f", qual.get("zero_state_capacitance_f_per_rail"))
    ktc = (1.380649e-23 * (temp + 273.15) / c_f) ** 0.5
    return {"layout": layout, "corner": corner, "temperature_c": temp,
            "capacitance_f": c_f, "analytic_single_rail_ktc_uv_rms": ktc * 1e6,
            "integrated_pex_noise_uv_rms": vals["onoise_total"] * 1e6,
            "integration_band_hz": [10, 100_000_000], "simulation_completed": True,
            "scope": "One extracted gate-cap rail to an ideal shared VCM, with extracted reset-TG PEX held on continuously. No finite aperture, switch turn-off, reference noise, mismatch or event updates."}


def main() -> int:
    rows = [run(layout, corner, temp)
            for layout in LAYOUTS
            for corner, temp in (("tt", 27), ("ss", 0), ("ff", 85))]
    report = {"test": "sky130_mos_single_state_pex_reset_noise", "rows": rows}
    (OUT / "results" / "sky130_mos_single_state_pex_noise.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
