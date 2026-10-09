"""Extracted SKY130 differential MIM trim unit with PEX transmission gates."""
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


def main() -> int:
    args = sys.argv[1:]
    corner = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--corner=")), "tt")
    temp = float(next((a.split("=", 1)[1] for a in args if a.startswith("--temp-c=")), "27"))
    step_mv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--plate-step-mv=")), "50"))
    routed_pair = "--routed-composite-pair" in args
    if corner not in {"tt", "ss", "ff"} or step_mv <= 0:
        raise ValueError("corner must be tt/ss/ff and plate step must be positive")
    vcm, dv = 0.9, step_mv * 1e-3
    vref_p, vref_n = vcm + dv, vcm - dv
    tag = f"{corner}_t{temp:g}c_step{step_mv:g}mv".replace(".", "p")
    if routed_pair: tag += "_routedpair"
    pair_include = (".include \"../layout/sky130_differential_trim_cap_pair/"
                    "sky130_differential_trim_cap_pair_pex.spice\"" if routed_pair else "")
    pair_instance = ("Xpair platep samplep platen samplen sky130_differential_trim_cap_pair"
                     if routed_pair else
                     "Xtrimp samplep platep packet_cap_mim_2x2um\n"
                     "Xtrimn samplen platen packet_cap_mim_2x2um")
    deck = BENCH / f"sky130_cap_offset_trim_unit_{tag}.cir"
    data = RES / f"sky130_cap_offset_trim_unit_{tag}.dat"
    deck.write_text(f"""* Matched differential extracted MIM trim pair and PEX TGs
.option scale=1u reltol=1e-6 abstol=1e-15 vntol=1e-9
.temp {temp:g}
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../layout/sky130_mim_packet_2x2/packet_cap_mim_2x2um.spice"
.include "../layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"
.include "../layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
{pair_include}
.subckt sky130_pex_tg a b en enb vdd vss
Xpex a b en enb vdd vss sky130_transmission_gate_raw
.ends sky130_pex_tg
Vdd vdd 0 1.8
Vcm vcm 0 {vcm:g}
Vrefp vrefp 0 {vref_p:.9f}
Vrefn vrefn 0 {vref_n:.9f}
Xsamplep samplep vcm mim_state_square_3x4_w30_l30
Xsamplen samplen vcm mim_state_square_3x4_w30_l30
Rreturnp samplep vcm 1e15
Rreturnn samplen vcm 1e15
Xsample_initp vcm samplep init init_b vdd 0 sky130_pex_tg
Xsample_initn vcm samplen init init_b vdd 0 sky130_pex_tg
{pair_instance}
Xplate_prep platep vcm pre pre_b vdd 0 sky130_pex_tg
Xplate_pren platen vcm pre pre_b vdd 0 sky130_pex_tg
Xplate_stepp platep vrefp step step_b vdd 0 sky130_pex_tg
Xplate_stepn platen vrefn step step_b vdd 0 sky130_pex_tg
Vinit init 0 PWL(0 1.8 0.5u 1.8 0.5001u 0 10u 0)
Vinit_b init_b 0 PWL(0 0 0.5u 0 0.5001u 1.8 10u 1.8)
Vpre pre 0 PWL(0 1.8 0.5u 1.8 0.5001u 0 10u 0)
Vpre_b pre_b 0 PWL(0 0 0.5u 0 0.5001u 1.8 10u 1.8)
Vstep step 0 PWL(0 0 1.9u 0 2u 1.8 3u 1.8 3.1u 0 10u 0)
Vstep_b step_b 0 PWL(0 1.8 1.9u 1.8 2u 0 3u 0 3.1u 1.8 10u 1.8)
.control
set wr_singlescale
set wr_vecnames
tran 1n 10u uic
wrdata ../results/{data.name} v(samplep) v(samplen) v(platep) v(platen) v(step)
let diff=v(samplep)-v(samplen)
meas tran before find diff at=1.8u
meas tran after find diff at=5u
meas tran cm_before find v(samplep) at=1.8u
meas tran cm_after find v(samplep) at=5u
quit
.endc
.end
""", encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "2g", "--cpus", "2",
           "-v", f"{ROOT}:/workspace:ro", "-v", f"{OUT}:/workspace/artifacts/analog_asic",
           "-w", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    log = run.stdout + run.stderr
    (RES / f"sky130_cap_offset_trim_unit_{tag}.log").write_text(log, encoding="utf-8")
    before = re.search(r"(?im)^before\s*=\s*([-+0-9.eE]+)", log)
    after = re.search(r"(?im)^after\s*=\s*([-+0-9.eE]+)", log)
    complete = run.returncode == 0 and "ngspice-36 done" in log.lower() and before and after and "tran simulation(s) aborted" not in log.lower()
    report = {"test": "sky130_extracted_differential_mim_offset_trim_unit", "corner": corner,
              "temperature_c": temp, "plate_step_mv_each_side": step_mv,
              "plate_references_v": [vref_p, vref_n], "simulation_completed": bool(complete),
              "return_code": run.returncode,
              "before_sample_differential_v": float(before.group(1)) if before else None,
              "after_sample_differential_v": float(after.group(1)) if after else None,
              "measured_differential_step_uv": (float(after.group(1))-float(before.group(1)))*1e6 if complete else None,
              "ideal_differential_step_uv": 2*9.52e-15/(21.84e-12+9.52e-15)*step_mv*1e3 if complete else None,
              "scope": ("Routed composite differential MIM pair with its Magic-extracted coupling caps, two extracted 30um-square sample MIM banks and two extracted PDK TGs; no weighted array, decoder, mismatch/noise Monte Carlo or latch integration." if routed_pair else "Matched extracted 2x2um MIM trim pair, two extracted 30um-square sample MIM banks and two extracted PDK TGs. No weighted array, switch decoder, mismatch/noise Monte Carlo, or latch integration.")}
    (RES / f"sky130_cap_offset_trim_unit_{tag}.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
