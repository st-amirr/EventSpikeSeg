"""PVT screen of the extracted SKY130 TG using its Magic parasitic-cap netlist."""
from __future__ import annotations
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAY=ROOT/"artifacts/analog_asic/layout/sky130_transmission_gate"
OUT=ROOT/"artifacts/analog_asic/results/sky130_transmission_gate_pvt"
SIM="eventspikeseg:analog-ngspice36"
CASES=[("tt",27),("ss",0),("ff",85)]
VIN=[round(0.1+i*0.2,1) for i in range(9)]
def main():
 OUT.mkdir(parents=True,exist_ok=True); summary=[]
 for corner,temp in CASES:
  lines=["* Extracted physical SKY130 transmission gate Ron over signal common mode",
   ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
   '.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"',
   f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
   f'.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
   f'.include "/workspace/{(LAY/"sky130_transmission_gate_pex.spice").relative_to(ROOT).as_posix()}"',
   ".subckt tg a b en enb vdd vss","Xg a b en enb vdd vss sky130_transmission_gate_raw",".ends tg",
   "Vdd vdd 0 1.8","Vss vss 0 0",".temp "+str(temp)]
  for i,vin in enumerate(VIN):
   lines += [f"Vsrc{i} src{i} 0 {vin}",f"Rsrc{i} src{i} a{i} 1k",
    f"Rload{i} b{i} 0 1Meg",f"Ven{i} en{i} 0 1.8",f"Venb{i} enb{i} 0 0",
    f"Xtg{i} a{i} b{i} en{i} enb{i} vdd vss tg"]
  lines += [".control","op"]
  for i in range(len(VIN)):
   lines += [f"let ron{i}=(v(a{i})-v(b{i}))/abs(i(Vsrc{i}))",f"print ron{i}"]
  lines += ["quit",".endc",".end",""]
  deck=OUT/f"tg_ron_{corner}_{temp}c.cir"; deck.write_text("\n".join(lines),encoding="ascii")
  p=subprocess.run(["docker","run","--rm","-v",f"{ROOT}:/workspace","-w","/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models","--entrypoint","ngspice",SIM,"-b",f"/workspace/{deck.relative_to(ROOT).as_posix()}"],capture_output=True,text=True,timeout=120,cwd=ROOT)
  log=p.stdout+p.stderr; (OUT/f"tg_ron_{corner}_{temp}c.log").write_text(log,encoding="utf-8")
  vals={int(i):float(x) for i,x in re.findall(r"(?im)^ron(\d+)\s*=\s*([-+0-9.eE]+)",log)}
  if p.returncode or len(vals)!=len(VIN) or "ngspice-36 done" not in log: raise RuntimeError(log[-4000:])
  rs=[vals[i] for i in range(len(VIN))]
  summary.append({"corner":corner.upper(),"temperature_c":temp,"signal_v":VIN,"on_resistance_ohm":rs,"min_ohm":min(rs),"max_ohm":max(rs),"span_fraction_of_mean":(max(rs)-min(rs))/(sum(rs)/len(rs))})
 report={"test":"sky130_extracted_tg_pvt_on_resistance","completed":True,"switch_control":"EN=1.8V ENB=0V","source_resistance_ohm":1000,"load_ohm":1000000,"cases":summary,"parasitic_netlist":"Magic capacitance extraction included; explicit interconnect resistance not included","scope":"TT/27C, SS/0C, FF/85C; no mismatch Monte Carlo, transient charge injection, or full PLIF replay."}
 (OUT/"qualification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
