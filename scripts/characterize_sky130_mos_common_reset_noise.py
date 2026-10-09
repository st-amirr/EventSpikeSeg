"""Compare PEX differential reset noise for independent clamps and a bridged clamp.

Both are always-on small-signal .noise states. This captures PDK transistor
channel noise with extracted cell capacitance, not turn-off transients/noise.
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
PAIR_LAYOUT = "sky130_mos_gate_state_pair_100x10_nf10"
PAIR = PAIR_LAYOUT.removeprefix("sky130_")
TG = "sky130_transmission_gate_raw"


def run(topology: str, corner: str, temp: int) -> dict[str, object]:
    tag = f"sky130_mos_common_reset_noise_{topology}_{corner}_temp{temp}"
    deck_path = OUT / "benches" / f"{tag}.cir"
    deck_path.parent.mkdir(parents=True, exist_ok=True)
    if topology == "independent":
        body = f'''Xclp drivep p en enb vdd 0 {TG}
Xcln driven n en enb vdd 0 {TG}
Xstate p n vcm 0 {PAIR}
'''
    elif topology == "shared_bridge":
        body = f'''Xclamp drivep p en enb vdd 0 {TG}
Xbridge p n en enb vdd 0 {TG}
Xstate p n vcm 0 {PAIR}
'''
    else:
        raise ValueError(topology)
    deck = f'''* SKY130 PEX reset network small-signal differential noise
.option scale=1u
.temp {temp}
.include "{MODEL}/models/parameters/invariant.spice"
.include "{MODEL}/models/r+c/res_typical__cap_typical__lin.spice"
.include "{MODEL}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "{MODEL}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../layout/{PAIR_LAYOUT}/{PAIR}.spice"
.include "../layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vdrivep drivep 0 dc 0.9 ac 1
Vdriven driven 0 dc 0.9 ac 0
Ven en 0 1.8
Venb enb 0 0
{body}.control
set numdgt=15
noise v(p,n) Vdrivep dec 20 10 100meg
print onoise_total
print inoise_total
quit
.endc
.end
'''
    deck_path.write_text(deck, encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "3g", "--cpus", "2", "--volume",
           f"{ROOT}:/workspace", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck_path.name]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=135)
    log = proc.stdout + proc.stderr
    resdir = OUT / "results"
    resdir.mkdir(parents=True, exist_ok=True)
    (resdir / f"{tag}.log").write_text(log, encoding="utf-8")
    vals = {k.lower(): float(v) for k, v in re.findall(
        r"(?im)^\s*(onoise_total|inoise_total)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(vals) != {"onoise_total", "inoise_total"}:
        raise RuntimeError(f"reset noise failed for {tag}:\n{log[-4000:]}")
    return {"topology": topology, "corner": corner, "temperature_c": temp,
            "integrated_differential_noise_uv_rms": vals["onoise_total"] * 1e6,
            "integration_band_hz": [10, 100_000_000], "simulation_completed": True,
            "scope": "PDK channel noise through extracted MOS pair and extracted reset TGs held on continuously. No finite aperture, clock turn-off noise, mismatch or post-reset event accumulation."}


def main() -> int:
    rows = [run(topology, corner, temp)
            for corner, temp in (("tt", 27), ("ss", 0), ("ff", 85))
            for topology in ("independent", "shared_bridge")]
    report = {"test": "sky130_common_bridge_reset_noise_pex", "state_pair": PAIR_LAYOUT, "rows": rows}
    (OUT / "results" / "sky130_mos_common_reset_noise_pex.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
