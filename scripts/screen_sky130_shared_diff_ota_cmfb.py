"""Screen a shared fully differential SKY130 OTA-C bucket with main-load CMFB."""
from __future__ import annotations
import json,re,subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SIM="eventspikeseg:analog-ngspice36"
CASES=[("tt",27),("ss",0),("ff",85)]
CSERVO=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--cservo=")),"10p")
REVERSED="--cmfb-reversed" in sys.argv
PASSIVE="--passive-cmfb" in sys.argv
CMFB_INP,CMFB_INN=("mean","vcm") if REVERSED else ("vcm","mean")
WN3=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--wn3=")),"4")
WP3=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--wp3=")),"20")
CC=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--cc=")),"5p")
WIN=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--win=")),"10")
WLOAD=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--wload=")),"20")
BIASREF=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--biasref=")),"0.75")
VBIASCM=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--vbiasn-cm=")),"0.65")
RDEG=next((a.split("=",1)[1] for a in sys.argv if a.startswith("--rdeg=")),"0")
DIFFINIT=float(next((a.split("=",1)[1] for a in sys.argv if a.startswith("--diffinit=")),"0"))
USE_UIC="--uic" in sys.argv
OUT=ROOT/f"artifacts/analog_asic/results/sky130_shared_diff_ota_cmfb_cservo_{CSERVO}_win_{WIN}_wload_{WLOAD}_wn3_{WN3}_wp3_{WP3}_cc_{CC}_biasref_{BIASREF}_vbiasncm_{VBIASCM}_rdeg_{RDEG}_{'uic' if USE_UIC else 'opinit'}_{'passive' if PASSIVE else ('reversed' if REVERSED else 'normal')}"
if DIFFINIT: OUT=OUT.with_name(OUT.name+f"_diffinit_{DIFFINIT:g}")
def main():
 OUT.mkdir(parents=True,exist_ok=True); result=[]
 for corner,temp in CASES:
  deck=OUT/f"shared_diff_cmfb_{corner}_{temp}c.cir"
  deck.write_text(f"""* Shared differential OTA-C state bucket and common-mode servo, SKY130 {corner}/{temp}C
.option scale=1u reltol=1e-4 abstol=1e-15 vntol=1e-8
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"
.include "/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "/workspace/asic/analog/modules.spice"
.include "/workspace/asic/analog/sky130_sc_charge_integrator.spice"
.subckt sky130_sc_cmfb_ota_deg inp inn out vbiasn vbiasp vdd vss
+ params: rdeg=1000 win=10 wload=20 wtail=4 wn3=4 wp3=20 cc=5p
Xn1 n1 inp n1s vss sky130_fd_pr__nfet_01v8 w={{win}} l=1
Xn2 n2 inn n2s vss sky130_fd_pr__nfet_01v8 w={{win}} l=1
Rdeg1 n1s ntail {{rdeg}}
Rdeg2 n2s ntail {{rdeg}}
Xntail ntail vbiasn vss vss sky130_fd_pr__nfet_01v8 w={{wtail}} l=2
Xp1 n1 n1 vdd vdd sky130_fd_pr__pfet_01v8 w={{wload}} l=1
Xp2 n2 n1 vdd vdd sky130_fd_pr__pfet_01v8 w={{wload}} l=1
Xn3 out n2 vss vss sky130_fd_pr__nfet_01v8 w={{wn3}} l=0.5
Xp3 out vbiasp vdd vdd sky130_fd_pr__pfet_01v8 w={{wp3}} l=0.5
Ccomp n2 out {{cc}}
.ends sky130_sc_cmfb_ota_deg
Vdd vdd 0 1.8
Vcm vcm 0 0.9
Vbn vbiasn 0 0.65
Vbncm vbiasn_cm 0 {VBIASCM}
Vbp_ref vbiasp_ref 0 {BIASREF}
Vin_p inp 0 0.9
Vin_n inn 0 0.9
* Integrating nodes start at the VCM operating point.
.ic v(outp)={0.9+DIFFINIT/2:g} v(outn)={0.9-DIFFINIT/2:g} v(vbiasp)={BIASREF}
* One shared NMOS differential pair, tail source, and common-gate PMOS loads.
Xtail ntail vbiasn 0 0 sky130_fd_pr__nfet_01v8 w=4 l=2
Xinp outp inp ntail 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xinn outn inn ntail 0 sky130_fd_pr__nfet_01v8 w=10 l=1
Xloadp outp vbiasp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Xloadn outn vbiasp vdd vdd sky130_fd_pr__pfet_01v8 w=20 l=1
Xmemp outp vcm sky130_fd_pr__cap_mim_m3_2 w=100 l=100 mf=1
Xmemn outn vcm sky130_fd_pr__cap_mim_m3_2 w=100 l=100 mf=1
* Average output senses one shared OTA; its output drives both PMOS loads.
{"" if PASSIVE else "Rmeanp outp mean 1Meg"}
{"" if PASSIVE else "Rmeann outn mean 1Meg"}
{"Rmeanp outp vbiasp 20Meg" if PASSIVE else (f"Xcmfb {CMFB_INP} {CMFB_INN} vbiasp vbiasn_cm vbiasp_ref vdd 0 sky130_sc_cmfb_ota_deg rdeg={RDEG} win={WIN} wload={WLOAD} wn3={WN3} wp3={WP3} cc={CC}" if float(RDEG)>0 else f"Xcmfb {CMFB_INP} {CMFB_INN} vbiasp vbiasn_cm vbiasp_ref vdd 0 sky130_sc_ota win={WIN} wload={WLOAD} wn3={WN3} wp3={WP3} cc={CC}")}
{"Rmeann outn vbiasp 20Meg" if PASSIVE else ""}
{"Rgatebias vbiasp vbiasp_ref 1Meg" if PASSIVE else ""}
Cservo vbiasp 0 {CSERVO}
Rservo vbiasp vbiasp_ref 100Meg
.temp {temp}
.control
set noaskquit
tran 1u 5m {"uic" if USE_UIC else ""}
meas tran outp_100u find v(outp) at=100u
meas tran outn_100u find v(outn) at=100u
meas tran outp_1m find v(outp) at=1m
meas tran outn_1m find v(outn) at=1m
meas tran outp_5m find v(outp) at=5m
meas tran outn_5m find v(outn) at=5m
meas tran cmfb_5m find v(vbiasp) at=5m
quit
.endc
.end
""",encoding="ascii")
  p=subprocess.run(["docker","run","--rm","-v",f"{ROOT}:/workspace","-w","/workspace/artifacts/analog_asic/pdk/sky130_fd_pr/models","--entrypoint","ngspice",SIM,"-b",f"/workspace/{deck.relative_to(ROOT).as_posix()}"],capture_output=True,text=True,timeout=180,cwd=ROOT)
  log=p.stdout+p.stderr;(OUT/f"shared_diff_cmfb_{corner}_{temp}c.log").write_text(log,encoding="utf-8")
  vals={k.lower():float(v) for k,v in re.findall(r"(?im)^\s*(outp_100u|outn_100u|outp_1m|outn_1m|outp_5m|outn_5m|cmfb_5m)\s*=\s*([-+0-9.eE]+)",log)}
  if p.returncode or len(vals)!=7 or "ngspice-36 done" not in log: raise RuntimeError(log[-4000:])
  result.append({"corner":corner.upper(),"temperature_c":temp,"outp_v":{"100us":vals["outp_100u"],"1ms":vals["outp_1m"],"5ms":vals["outp_5m"]},"outn_v":{"100us":vals["outn_100u"],"1ms":vals["outn_1m"],"5ms":vals["outn_5m"]},"differential_v":{"100us":vals["outp_100u"]-vals["outn_100u"],"1ms":vals["outp_1m"]-vals["outn_1m"],"5ms":vals["outp_5m"]-vals["outn_5m"]},"common_mode_v":{"100us":(vals["outp_100u"]+vals["outn_100u"])/2,"1ms":(vals["outp_1m"]+vals["outn_1m"])/2,"5ms":(vals["outp_5m"]+vals["outn_5m"])/2},"cmfb_pmos_gate_5ms_v":vals["cmfb_5m"]})
 report={"test":"sky130_shared_differential_ota_cmfb_hold_screen","completed":True,"cmfb_servo_capacitance":CSERVO,"cmfb_ota":{"win_um":WIN,"wload_um":WLOAD,"wn3_um":WN3,"wp3_um":WP3,"compensation_capacitance":CC,"tail_bias_v":VBIASCM},"cmfb_input_polarity":"passive resistive output-mean feedback with gate bias" if PASSIVE else ("mean-output error drives common PMOS gates" if REVERSED else "vcm to inp, mean output to inn"),"bias_reference_v":BIASREF,"topology":"one shared NMOS differential pair and tail feeding two outputs with common-gate PMOS loads; common-mode correction drives both load gates; 2x 100um MIM storage caps","cases":result,"scope":"5ms zero-event equal-input common-mode/differential hold; schematic transistors and ideal initialization; no mismatch/noise/event updates/layout/PEX. This is topology feasibility only."}
 (OUT/"qualification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2))
if __name__=="__main__":main()
