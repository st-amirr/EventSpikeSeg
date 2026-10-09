"""Repeat extracted-MIM 5 ms retention with the physically extracted TG PCell."""
from __future__ import annotations
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"artifacts/analog_asic/layout/sky130_mim_state_bank_square/square_bank_hold_5ms.cir"
TG=ROOT/"artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
OUT=ROOT/"artifacts/analog_asic/results/sky130_mim_bank_physical_tg_hold"
CASES=[("tt",27),("ss",0),("ff",85)]
def main():
 OUT.mkdir(parents=True,exist_ok=True); results=[]
 original=BASE.read_text(encoding="ascii")
 for corner,temp in CASES:
  deck=original.replace('sky130.lib.spice" tt',f'sky130.lib.spice" {corner}')
  deck=deck.replace('.include "/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"',f'.include "/workspace/artifacts/analog_asic/layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"\n.include "/workspace/{TG.relative_to(ROOT).as_posix()}"\n.subckt transmission_gate a b en enb vdd vss\nXphysical a b en enb vdd vss sky130_transmission_gate_raw\n.ends transmission_gate')
  for state,src in (("06","src06"),("12","src12")):
   deck=deck.replace(f"Xsw_n_tg_{state} {src} en state_tg_{state} 0 sky130_fd_pr__nfet_01v8 w=1 l=0.15\nXsw_p_tg_{state} {src} enb state_tg_{state} vdd sky130_fd_pr__pfet_01v8 w=1 l=0.15",f"Xphysical_tg_{state} {src} state_tg_{state} en enb vdd 0 transmission_gate")
  deck=deck.replace(".control",f".temp {temp}\n.control",1)
  path=OUT/f"physical_tg_hold_{corner}_{temp}c.cir"; path.write_text(deck,encoding="ascii")
  p=subprocess.run(["docker","run","--rm","-v",f"{ROOT}:/workspace","-w","/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice","--entrypoint","ngspice","eventspikeseg:analog-ngspice36","-b",f"/workspace/{path.relative_to(ROOT).as_posix()}"],capture_output=True,text=True,timeout=180,cwd=ROOT)
  log=p.stdout+p.stderr; (OUT/f"physical_tg_hold_{corner}_{temp}c.log").write_text(log,encoding="utf-8")
  vals={k.lower():float(v) for k,v in re.findall(r"(?im)^\s*(ideal_06_start|ideal_06_end|tg_06_start|tg_06_end|ideal_12_start|ideal_12_end|tg_12_start|tg_12_end)\s*=\s*([-+0-9.eE]+)",log)}
  if p.returncode or len(vals)!=8 or "ngspice-36 done" not in log: raise RuntimeError(log[-4000:])
  results.append({"corner":corner.upper(),"temperature_c":temp,"physical_tg_drift_v":{"0.6V":vals["tg_06_end"]-vals["tg_06_start"],"1.2V":vals["tg_12_end"]-vals["tg_12_start"]},"ideal_control_drift_v":{"0.6V":vals["ideal_06_end"]-vals["ideal_06_start"],"1.2V":vals["ideal_12_end"]-vals["ideal_12_start"]},"physical_tg_start_v":{"0.6V":vals["tg_06_start"],"1.2V":vals["tg_12_start"]},"physical_tg_end_v":{"0.6V":vals["tg_06_end"],"1.2V":vals["tg_12_end"]}})
 report={"test":"extracted_mim_bank_5ms_hold_with_extracted_tg","completed":True,"storage":"existing 21.8pF MIM layout extraction, 3x4 30um MIM array","switch":"DRC/LVS-verified physical 1um NFET + 2um PFET TG with Magic-extracted coupling caps","cases":results,"limitations":"Switch wire resistance not extracted; nominal PDK corner library, no mismatch or transient noise; large-cap storage does not address per-state area."}
 (OUT/"qualification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__": main()

