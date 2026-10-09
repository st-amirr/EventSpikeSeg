#!/usr/bin/env python3
"""Transient PEX settling of a four-cell parallel TG bank into a 100k load."""
from __future__ import annotations
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAY=ROOT/"artifacts/analog_asic/layout/sky130_parallel_tg_bank_4"
OUT=ROOT/"artifacts/analog_asic/results/sky130_parallel_tg_bank_switch"
IMAGE="eventspikeseg:analog-ngspice36"

def main():
    OUT.mkdir(parents=True,exist_ok=True); bank=LAY/"sky130_parallel_tg_bank_4_pex.spice"; reports={}
    pdk="/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
    for corner,temp in (("tt",27),("ss",0),("ff",85)):
        lines=["* Extracted TG4 turn-on settling", ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",f".temp {temp}",
          f'.include "{pdk}/models/parameters/invariant.spice"',
          f'.include "{pdk}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
          f'.include "{pdk}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
          f'.include "/workspace/{bank.relative_to(ROOT).as_posix()}"',"Vdd vdd 0 1.8","Vss vss 0 0","Vrail rail 0 0.95","Vcm cm 0 0.9",
          "Ven en 0 PULSE(0 1.8 1n 20p 20p 10n 20n)","Venb enb 0 PULSE(1.8 0 1n 20p 20p 10n 20n)"]
        nodes=[node for _ in range(4) for node in ("en","enb")]
        lines += ["Xsw rail out "+" ".join(nodes)+" vdd vss sky130_parallel_tg_bank_4_raw","Rload out cm 100k",
          ".control","set numdgt=15","tran 10p 5n","meas tran v_pre find v(out) at=0.9n","meas tran v_early find v(out) at=1.1n",
          "meas tran v_500ps find v(out) at=1.5n","meas tran v_2ns find v(out) at=3n","meas tran v_4ns find v(out) at=5n","quit",".endc",".end",""]
        deck=OUT/f"tg4_settling_{corner}_{temp}c.cir"; deck.write_text("\n".join(lines),encoding="ascii")
        cmd=["docker","run","--rm","--memory","4g","--cpus","2","-v",f"{ROOT}:/workspace","-w","/workspace/artifacts/analog_asic/layout","--entrypoint","ngspice",IMAGE,"-b",f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
        p=subprocess.run(cmd,text=True,capture_output=True,timeout=120,cwd=ROOT); log=p.stdout+p.stderr
        (OUT/f"tg4_settling_{corner}_{temp}c.log").write_text(log,encoding="utf-8")
        got={k:float(v) for k,v in re.findall(r"(?im)^\s*(v_pre|v_early|v_500ps|v_2ns|v_4ns)\s*=\s*([-+0-9.eE]+)",log)}
        if p.returncode or "ngspice-36 done" not in log or len(got)!=5: raise RuntimeError(f"settling simulation failed at {corner}/{temp}: {log[-2000:]}")
        reports[f"{corner.upper()}_{temp}C"]=got
    result={"test":"sky130_extracted_tg4_load_settling","simulation_completed":True,"bank_count":4,"load":"100k to 0.9V",
      "edge":"ideal complementary gate drive at 1ns","settling":reports,"scope":"PEX capacitance and extracted MOS devices, but no wire resistance, gate-driver resistance, interconnect delay, mismatch, or noise."}
    (OUT/"tg4_settling.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,indent=2))
if __name__=="__main__":main()
