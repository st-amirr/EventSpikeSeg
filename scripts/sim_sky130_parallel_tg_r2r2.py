#!/usr/bin/env python3
"""Simulate the extracted four-device TG bank with the physical 2-bit ladder."""
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAY=ROOT/"artifacts/analog_asic/layout"
OUT=ROOT/"artifacts/analog_asic/results/sky130_parallel_tg_r2r2"
IMAGE="eventspikeseg:analog-ngspice36"
LTOP="sky130_physical_r2r2_slice_raw"

def spice_instance(tokens, limit=180):
    rows=[]; row=tokens[0]
    for token in tokens[1:]:
        if len(row)+1+len(token)>limit:
            rows.append(row); row="+ "+token
        else:
            row += " "+token
    rows.append(row)
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--count",type=int,default=4); ap.add_argument("--omit-capacitance",action="store_true"); ap.add_argument("--omit-off-branch",action="store_true"); ap.add_argument("--tie-control-pins",action="store_true"); args=ap.parse_args(); n=args.count
    OUT.mkdir(parents=True,exist_ok=True)
    ladder=LAY/"sky130_physical_r2r2_slice/sky130_physical_r2r2_slice.spice"
    suffix="" if args.omit_capacitance else "_pex"
    bank=LAY/f"sky130_parallel_tg_bank_{n}/sky130_parallel_tg_bank_{n}{suffix}.spice"
    BTOP=f"sky130_parallel_tg_bank_{n}_raw"
    src=ladder.read_text(encoding="ascii")
    bodyset=set(re.findall(r"^X\S+\s+\S+\s+\S+\s+(\S+)\s+sky130_fd_pr__res_xhigh_po_1p41",src,re.M))
    if len(bodyset)!=1 or not bank.exists(): raise RuntimeError("missing extracted ladder/body or PEX TG bank")
    body=next(iter(bodyset)); pdk="/workspace/artifacts/analog_asic/pdk/sky130_fd_pr"
    ports=["A","B"]+[p+str(i) for i in range(n) for p in ("EN","ENB")]+["BULKP","BULKN"]
    reports={}
    for corner,temp in (("tt",27),("ss",0),("ff",85)):
        base=[f"* Extracted {n}-TG bank and extracted R-2R slice", ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",f".temp {temp}",
          f'.include "{pdk}/models/parameters/invariant.spice"',f'.include "{pdk}/models/r+c/res_typical__cap_typical__lin.spice"',
          f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"',f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po.model.spice"',
          f'.include "{pdk}/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"',f'.include "{pdk}/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"',
          f'.include "{pdk}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',f'.include "{pdk}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
          f'.include "/workspace/{ladder.relative_to(ROOT).as_posix()}"',f'.include "/workspace/{bank.relative_to(ROOT).as_posix()}"',
          f".global {body}",".param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0",
          ".param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11",f"Vbody {body} 0 0","Vdd vdd 0 1.8","Vss vss 0 0",
          "Vhi rail_hi 0 0.95","Vlo_switch rail_lo 0 0.85","Vlo_ref vlo 0 0.85","Vcm cm 0 0.9"]
        out=[]
        for code in range(4):
            lines=base.copy()
            tag=f"c{code}"; b1,b0=code>>1,code&1
            lines += [f"Xdac_{tag} out_{tag} vlo b1_{tag} b0_{tag} {LTOP}"]
            for bit,val in (("b1",b1),("b0",b0)):
                for rail,sel in (("hi",val),("lo",1-val)):
                    if args.omit_off_branch and not sel: continue
                    ien=[1.8 if sel else 0 for _ in range(n)]
                    en_nodes=[]
                    if args.tie_control_pins:
                        en=f"en_{bit}_{rail}_{tag}"; enb=f"enb_{bit}_{rail}_{tag}"; v=1.8 if sel else 0
                        lines += [f"V{en} {en} 0 {v}",f"V{enb} {enb} 0 {1.8-v}"]
                        en_nodes=[node for _ in range(n) for node in (en,enb)]
                    else:
                        for i,v in enumerate(ien):
                            en=f"en_{bit}_{rail}_{i}_{tag}"; enb=f"enb_{bit}_{rail}_{i}_{tag}"
                            lines += [f"V{en} {en} 0 {v}",f"V{enb} {enb} 0 {1.8-v}"]
                            en_nodes += [en,enb]
                    a="rail_hi" if rail=="hi" else "rail_lo"; b=f"{bit}_{tag}"
                    inst_args=[a,b,*en_nodes,"vdd","vss"]
                    lines.extend(spice_instance([f"X{bit}{rail}_{tag}",*inst_args,BTOP]))
            lines += [f"Rload_{tag} out_{tag} cm 100Meg",".control","set numdgt=15","op",f"print v(out_{tag})","quit",".endc",".end",""]
            deck=OUT/f"parallel_tg_r2r2_n{n}_{corner}_{temp}c_code{code}.cir"; deck.write_text("\n".join(lines),encoding="ascii")
            cmd=["docker","run","--rm","--memory","4g","--cpus","2","-v",f"{ROOT}:/workspace","-w",f"/workspace/{LAY.relative_to(ROOT).as_posix()}","--entrypoint","ngspice",IMAGE,"-b",f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
            p=subprocess.run(cmd,text=True,capture_output=True,timeout=90,cwd=ROOT); log=p.stdout+p.stderr
            (OUT/f"parallel_tg_r2r2_n{n}_{corner}_{temp}c_code{code}.log").write_text(log,encoding="utf-8")
            vals=[float(v) for v in re.findall(r"(?im)^\s*v\(out_"+tag+r"\)\s*=\s*([-+0-9.eE]+)",log)]
            if p.returncode or "ngspice-36 done" not in log or not vals: raise RuntimeError(f"SPICE failed with status {p.returncode}: {log[-2500:]}")
            out.append(vals[-1])
        steps=[out[i+1]-out[i] for i in range(3)]
        reports[f"{corner.upper()}_{temp}C"]={"output_v":out,"steps_v":steps,"strictly_monotonic":all(s>0 for s in steps),
          "max_step_deviation_from_mean_pct":max(abs(s/(sum(steps)/3)-1) for s in steps)*100}
    report={"test":f"sky130_extracted_parallel_tg{n}_and_r2r2_dc","simulation_completed":True,"tg_count_per_switch":n,
      "switch_layout":f"{n} physical TG devices per bit-rail switch, A/B buses physically routed, unique LVS, Magic DRC0",
      "switch_controls":"ideal separate pin drives; shared gate routing not extracted","resistor_layout":"7-resistor extracted PCell slice",
      "temperature_and_corner":reports,"scope":("Extracted MOS device netlist without layout capacitances, extracted resistor ladder, DC transfer only; no resistance PEX, dynamic settling, mismatch/noise, full-resolution DAC, or full-float SNN replay." if args.omit_capacitance else "PEX capacitor deck with extracted R ladder, DC transfer only; no resistance PEX, dynamic settling, mismatch/noise, full-resolution DAC, or full-float SNN replay."),
      "off_switch_model":"ideal open for each unselected rail" if args.omit_off_branch else "physical off TG banks retained",
      "gate_connections":"ideal common drive nodes shared across gate pins" if args.tie_control_pins else "separate ideal gate sources per physical cell; no shared physical gate routing"}
    suffix=("_device_only" if args.omit_capacitance else "")+("_selected_only" if args.omit_off_branch else "")+("_tied_controls" if args.tie_control_pins else "")
    report_path=OUT/f"parallel_tg_r2r2_n{n}{suffix}.json"
    report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
