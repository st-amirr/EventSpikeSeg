#!/usr/bin/env python3
"""Isolate the four rail-switch banks around one R-2R code (code 1)."""
from __future__ import annotations
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAY=ROOT/"artifacts/analog_asic/layout"; OUT=ROOT/"artifacts/analog_asic/results/sky130_parallel_tg_r2r2"
IMAGE="eventspikeseg:analog-ngspice36"; N=4

def main():
    ladder=LAY/"sky130_physical_r2r2_slice/sky130_physical_r2r2_slice.spice"
    bank=LAY/f"sky130_parallel_tg_bank_{N}/sky130_parallel_tg_bank_{N}_pex.spice"
    body=next(iter(set(re.findall(r"^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41",ladder.read_text(),re.M))))
    pdk="/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"; report={}
    for mode, use_b1, use_b0 in (("ideal",False,False),("b1_only",True,False),("b0_only",False,True),("both",True,True)):
        lines=["* R2R code1 switch composition debug", ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",".temp 27",
          f'.include "{pdk}/models/parameters/invariant.spice"',f'.include "{pdk}/models/r+c/res_typical__cap_typical__lin.spice"',
          f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"',
          f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',f'.include "{pdk}/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
          f'.include "{pdk}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"',f'.include "{pdk}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"',
          f'.include "/workspace/{ladder.relative_to(ROOT).as_posix()}"',f'.include "/workspace/{bank.relative_to(ROOT).as_posix()}"',
          f".global {body}",".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
          ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",f"Vbody {body} 0 0","Vdd vdd 0 1.8","Vss vss 0 0",
          "Vhi rail_hi 0 0.95","Vlo_switch rail_lo 0 0.85","Vlo_ref vlo 0 0.85","Vcm cm 0 0.9","Xdac out vlo b1 b0 sky130_physical_r2r2_slice_raw","Rload out cm 100Meg"]
        for bit,use,val,ideal in (("b1",use_b1,0,.85),("b0",use_b0,1,.95)):
            if not use:
                lines.append(f"V{bit} {bit} 0 {ideal}"); continue
            for rail,sel in (("hi",val),("lo",1-val)):
                ctrls=[]
                for i in range(N):
                    en=f"en_{bit}_{rail}_{i}"; enb=f"enb_{bit}_{rail}_{i}"; v=1.8 if sel else 0
                    lines += [f"V{en} {en} 0 {v}",f"V{enb} {enb} 0 {1.8-v}"]; ctrls += [en,enb]
                a="rail_hi" if rail=="hi" else "rail_lo"
                lines.append(f"X{bit}{rail} {a} {bit} "+" ".join(ctrls)+f" vdd vss sky130_parallel_tg_bank_{N}_raw")
        lines += [".control","set numdgt=15","op","print v(b1)","print v(b0)","print v(out)","quit",".endc",".end",""]
        deck=OUT/f"r2r2_comp_{mode}.cir"; deck.write_text("\n".join(lines),encoding="ascii")
        cmd=["docker","run","--rm","--memory","4g","--cpus","2","-v",f"{ROOT}:/workspace","-w","/workspace/artifacts/analog_asic/layout","--entrypoint","ngspice",IMAGE,"-b",f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
        p=subprocess.run(cmd,text=True,capture_output=True,timeout=90,cwd=ROOT); log=p.stdout+p.stderr
        (OUT/f"r2r2_comp_{mode}.log").write_text(log,encoding="utf-8")
        vals={node:float(v) for node,v in re.findall(r"(?im)^\s*v\((b1|b0|out)\)\s*=\s*([-+0-9.eE]+)",log)}
        if p.returncode or "ngspice-36 done" not in log or len(vals)!=3: raise RuntimeError(f"composition bench {mode} failed: {log[-2000:]}")
        report[mode]=vals
    result={"test":"r2r2_code1_bitwise_physical_tg_isolation","simulation_completed":True,"corner":"TT/27C","measured_v":report,
      "ideal_code1_expected_output_v":.8750010605,"diagnostic":"one switch bank or both banks replace ideal bit voltage sources; physical TG PEX and resistor PCell extraction retained."}
    (OUT/"r2r2_bit_composition_debug.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2))
if __name__=="__main__":main()
