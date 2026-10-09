"""Integrate SKY130 transmission-gate reset noise into candidate state capacitors.

This is a small-signal device-noise screen with the reset gates continuously on.
It measures the PDK MOS channel noise filtered by physical-model MIM capacitors;
it is not a switched transient, mismatch, or full state-cell qualification.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
RESULTS = OUT / "results"
BENCH = OUT / "benches"
CAP_WIDTHS_UM = (10, 30, 100)
TOPOLOGIES = ("independent_pair", "single_differential", "mos_gate_pair",
              "single_ended_mim", "single_ended_mos")
FSTART_HZ = 10
FSTOP_HZ = 100_000_000


def run_one(width: int, topology: str) -> dict[str, object]:
    tag = f"sky130_mim_reset_noise_tt_{topology}_w{width}um_f{FSTART_HZ:g}-{FSTOP_HZ:g}"
    deck = BENCH / f"{tag}.cir"
    single_ended = topology.startswith("single_ended_")
    if topology in ("independent_pair", "single_ended_mim"):
        caps = (f"Xcap_p state_p 0 sky130_fd_pr__cap_mim_m3_2 w={width} l={width}\n"
                + (f"Xcap_n state_n 0 sky130_fd_pr__cap_mim_m3_2 w={width} l={width}"
                   if topology == "independent_pair" else ""))
    elif topology == "single_differential":
        caps = f"Xcap_diff state_p state_n sky130_fd_pr__cap_mim_m3_2 w={width} l={width}"
    else:
        finger_l = width / 10
        mos_caps = [f"Xcap_p_{i} 0 state_p 0 0 sky130_fd_pr__nfet_01v8 w={width} l={finger_l:g}"
                    for i in range(10)]
        if topology == "mos_gate_pair":
            mos_caps += [f"Xcap_n_{i} 0 state_n 0 0 sky130_fd_pr__nfet_01v8 w={width} l={finger_l:g}"
                         for i in range(10)]
        caps = "\n".join(mos_caps)
    reset_branches = ("Xreset_p drive state_p en enb vdd 0 tg" if single_ended else
                      "Xreset_p drive state_p en enb vdd 0 tg\n"
                      "Xreset_n reference state_n en enb vdd 0 tg")
    observed = "v(state_p)" if single_ended else "v(state_p,state_n)"
    deck.write_text(f'''* SKY130 TT/27C differential MIM reset-switch device-noise screen
.option scale=1u
.temp 27
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
Vdd vdd 0 1.8
Vdrive drive 0 0.9 AC 1
Vreference reference 0 0.9
Ven en 0 1.8
Venb enb 0 0
.subckt tg a b en enb vdd vss
Xn a en b vss sky130_fd_pr__nfet_01v8 w=1 l=0.15
Xp a enb b vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15
.ends tg
{reset_branches}
{caps}
.control
set numdgt=15
noise {observed} Vdrive dec 20 {FSTART_HZ} {FSTOP_HZ}
print onoise_total
print inoise_total
quit
.endc
.end
''', encoding="ascii")
    command = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace:ro", "--workdir",
               "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
               "eventspikeseg:analog-ngspice36", "90", "ngspice", "-b", deck.name]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=105, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{tag}.log").write_text(log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(onoise_total|inoise_total)\s*=\s*([-+0-9.eE]+)", log)}
    if proc.returncode or "ngspice-36 done" not in log or set(values) != {"onoise_total", "inoise_total"}:
        raise RuntimeError(f"PDK reset-noise analysis failed for {width}um MIM:\n{log[-5000:]}")
    mos_storage = topology in ("mos_gate_pair", "single_ended_mos")
    expected_c_ff = ((650.4488 if mos_storage else 207.6) *
                     (width / 10) ** 2)
    cap_count = 2 if topology in ("independent_pair", "mos_gate_pair") else 1
    expected_noise_factor = 2 if topology in ("independent_pair", "mos_gate_pair") else 1
    expected_pair_uv = (expected_noise_factor * 1.380649e-23 * 300.15 /
                        (expected_c_ff * 1e-15)) ** 0.5 * 1e6
    return {"capacitor_geometry_scale_width_um": width,
            "topology": topology,
            "storage_element_count": cap_count,
            "expected_capacitance_per_leg_f": expected_c_ff * 1e-15,
            "analytic_kTC_uv_rms_300k": expected_pair_uv,
            "integrated_state_output_noise_v_rms": values["onoise_total"],
            "integrated_state_output_noise_uv_rms": values["onoise_total"] * 1e6,
            "input_referred_noise_v_rms": values["inoise_total"],
            "corner": "tt", "temperature_c": 27,
            "integration_band_hz": [FSTART_HZ, FSTOP_HZ],
            "simulation_completed": True}


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    BENCH.mkdir(parents=True, exist_ok=True)
    rows = [run_one(width, topology) for topology in TOPOLOGIES
            for width in CAP_WIDTHS_UM]
    report = {"test": "sky130_differential_mim_reset_switch_device_noise",
              "rows": rows,
              "reset_tg_geometry_um": {"nfet_w": 1, "nfet_l": 0.15,
                                       "pfet_w": 2, "pfet_l": 0.15},
              "scope": "Small-signal .noise analysis of always-on SKY130 TT transmission gates charging independent MIM pairs, one differential MIM capacitor, two NFET gate capacitors, or a single-ended MIM/MOS gate capacitor to a shared ground reference. MOS gate capacitance uses the effective capacitance measured by the earlier equal-area MOS-cap screen. Includes PDK MOS device noise; omits finite reset aperture, switch turn-off transient, post-reset hold noise, mismatch, common-mode stability of floating differential state, routing parasitics, and PLIF feedback."}
    (RESULTS / "sky130_mim_reset_noise_tt.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
