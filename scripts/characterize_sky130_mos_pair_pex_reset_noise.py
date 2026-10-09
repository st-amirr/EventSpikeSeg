"""Small-signal reset-path noise through extracted SKY130 MOS state pairs and TGs.

This is an always-on reset-switch .noise screen, not finite-aperture transient
noise or full neuron acceptance. The pair and access switch use their PEX views.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
MODEL = "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
PDK = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A"
LAYOUTS = ("sky130_mos_gate_state_pair_10x1_nf10",
           "sky130_mos_gate_state_pair_20x2_nf10",
           "sky130_mos_gate_state_pair_100x10_nf10")


def run(layout: str, corner: str = "tt", temp_c: int = 27) -> dict[str, object]:
    cell = layout.removeprefix("sky130_")
    tag = f"sky130_mos_pair_pex_reset_noise_{cell}_{corner}_temp{temp_c}"
    bench = OUT / "benches" / f"{tag}.cir"
    result = OUT / "results"
    bench.parent.mkdir(parents=True, exist_ok=True)
    result.mkdir(parents=True, exist_ok=True)
    deck = f'''* Extracted state pair and reset-TG small-signal noise
.option scale=1u
.temp {temp_c}
.include "{PDK}/libs.tech/ngspice/parameters/invariant.spice"
.include "{MODEL}/models/parameters/invariant.spice"
.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"
.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../layout/{layout}/{cell}.spice"
.include "../layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vdrivep drivep 0 dc 0.9 ac 1
Vdriven driven 0 dc 0.9 ac 0
Ven en 0 1.8
Venb enb 0 0
Xrstp drivep statep en enb vdd 0 sky130_transmission_gate_raw
Xrstn driven staten en enb vdd 0 sky130_transmission_gate_raw
Xstate statep staten vcm 0 {cell}
.control
set numdgt=15
noise v(statep,staten) Vdrivep dec 20 10 100meg
print onoise_total
print inoise_total
quit
.endc
.end
'''
    bench.write_text(deck, encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", bench.name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=135)
    log = proc.stdout + proc.stderr
    (result / f"{tag}.log").write_text(log, encoding="utf-8")
    vals = {k.lower(): float(v) for k, v in re.findall(
        r"(?im)^\s*(onoise_total|inoise_total)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(vals) != {"onoise_total", "inoise_total"}:
        raise RuntimeError(f"PEX MOS-pair reset-noise simulation failed for {layout}/{corner}:\n{log[-4000:]}")
    c_f = json.loads((OUT / "layout" / layout / "qualification.json").read_text())["zero_state_capacitance_f_per_rail"]
    k = 1.380649e-23
    return {"layout": layout, "corner": corner, "temperature_c": temp_c,
            "capacitance_per_rail_f": c_f,
            "analytic_independent_pair_ktc_uv_rms": (2 * k * (temp_c + 273.15) / c_f) ** 0.5 * 1e6,
            "integrated_pex_noise_uv_rms": vals["onoise_total"] * 1e6,
            "integration_band_hz": [10, 100_000_000], "simulation_completed": True,
            "access_switch": "extracted SKY130 transmission-gate PEX held continuously on",
            "scope": "PDK small-signal transistor noise through the extracted paired MOS-cap and TG views. No finite reset aperture, turn-off noise, post-reset noise, mismatch, or full PLIF behavior."}


def main() -> int:
    rows = [run(layout) for layout in LAYOUTS]
    report = {"test": "sky130_pex_mos_pair_reset_noise", "rows": rows}
    path = OUT / "results" / "sky130_mos_pair_pex_reset_noise_tt.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
