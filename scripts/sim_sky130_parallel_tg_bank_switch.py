#!/usr/bin/env python3
"""Isolate the extracted parallel TG bank's on/off DC transfer."""
from __future__ import annotations
import json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAY=ROOT/"artifacts/analog_asic/layout/sky130_parallel_tg_bank_4"
OUT=ROOT/"artifacts/analog_asic/results/sky130_parallel_tg_bank_switch"
IMAGE="eventspikeseg:analog-ngspice36"

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bank=LAY/"sky130_parallel_tg_bank_4_pex.spice"; n=4
    pdk="/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"; report={}
    for corner,temp in (("tt",27),("ss",0),("ff",85)):
        lines=["* Isolated extracted TG4 switch check", ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",f".temp {temp}",
          f'.include "{pdk}/models/parameters/invariant.spice"',
          f'.include "{pdk}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
          f'.include "{pdk}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
          f'.include "/workspace/{bank.relative_to(ROOT).as_posix()}"',"Vdd vdd 0 1.8","Vss vss 0 0",
          "Vrail rail 0 0.95","Vcm cm 0 0.9"]
        result={}
        for mode,on in (("off",False),("on",True)):
            nodes=[]
            for i in range(n):
                en=f"en_{i}_{mode}"; enb=f"enb_{i}_{mode}"; value=1.8 if on else 0
                lines += [f"V{en} {en} 0 {value}",f"V{enb} {enb} 0 {1.8-value}"]; nodes += [en,enb]
            args=["rail",f"out_{mode}",*nodes,"vdd","vss"]
            lines += ["Xsw_"+mode+" "+" ".join(args)+" sky130_parallel_tg_bank_4_raw",f"Rload_{mode} out_{mode} cm 100k"]
        lines += [".control","set numdgt=15","op","print v(out_off)","print v(out_on)","quit",".endc",".end",""]
        deck=OUT/f"tg4_switch_{corner}_{temp}c.cir"; deck.write_text("\n".join(lines),encoding="ascii")
        cmd=["docker","run","--rm","--memory","4g","--cpus","2","-v",f"{ROOT}:/workspace","-w","/workspace/artifacts/analog_asic/layout","--entrypoint","ngspice",IMAGE,"-b",f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
        p=subprocess.run(cmd,text=True,capture_output=True,timeout=90,cwd=ROOT); log=p.stdout+p.stderr
        (OUT/f"tg4_switch_{corner}_{temp}c.log").write_text(log,encoding="utf-8")
        vals={name:float(v) for name,v in re.findall(r"(?im)^\s*v\((out_(?:off|on))\)\s*=\s*([-+0-9.eE]+)",log)}
        if p.returncode or "ngspice-36 done" not in log or len(vals)!=2: raise RuntimeError(f"TG bank switch test failed: {log[-2000:]}")
        result={"off_v":vals["out_off"],"on_v":vals["out_on"]}; report[f"{corner.upper()}_{temp}C"]=result
    out={"test":"sky130_extracted_tg4_on_off_transfer","simulation_completed":True,"bank_count":4,
      "dc_transfer":report,"scope":"one physical 4-cell bank PEX with ideal gate drives, 100k output load, no R extraction, timing, mismatch or noise."}
    (OUT/"tg4_switch.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8"); print(json.dumps(out,indent=2))
if __name__=="__main__": main()
