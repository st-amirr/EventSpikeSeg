from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic'; BENCH=OUT/'benches'; RES=OUT/'results'
HEADER=r'''* SKY130 passive switched-capacitor membrane packet test
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
Vdd vdd 0 1.8
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
Vcm vcm 0 0.9
'''
def main():
 import sys
 seq=next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--sequence=')),'pn')
 step=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--packet-step-v=')),'0.05'))
 cmem=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--membrane-um=')),'100'))
 cpacket=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--packet-um=')),'1'))
 code=int(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--threshold-dac-code=')),'-1'))
 state_v=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--initial-state-v=')),'0.9'))
 track_cm='--packet-common-mode=state' in sys.argv
 leak=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--leak-ohm=')),'1e15'))
 maxstep=float(next((a.split('=',1)[1] for a in sys.argv[1:] if a.startswith('--max-step-ns=')),'100'))
 if len(seq)!=2 or any(x not in 'pnz' for x in seq): raise ValueError('sequence must be two p/n/z slots')
 conn_pts=[('0','0')]; connb_pts=[('0','1.8')]
 for idx,symbol in enumerate(seq):
  if symbol=='z': continue
  if idx==0:
   pts=[('499u','0'),('499.1u','1.8'),('501.9u','1.8'),('502u','0')]
  else:
   pts=[('4.499m','0'),('4.4991m','1.8'),('4.5019m','1.8'),('4.502m','0')]
  conn_pts += pts; connb_pts += [(t,'1.8' if v=='0' else '0') for t,v in pts]
 conn_pts.append(('5.005m','0')); connb_pts.append(('5.005m','1.8'))
 conn_pwl='PWL('+' '.join(f'{t} {v}' for t,v in conn_pts)+')'
 connb_pwl='PWL('+' '.join(f'{t} {v}' for t,v in connb_pts)+')'
 reset_pts=[('0','0')]
 resetb_pts=[('0','1.8')]
 for idx,symbol in enumerate(seq):
  if symbol=='z': continue
  if idx==0:
   pre=[('498.5u','0'),('498.6u','1.8'),('498.9u','1.8'),('499u','0')]
   post=[('502.1u','0'),('502.2u','1.8'),('502.5u','1.8'),('502.6u','0')]
  else:
   pre=[('4.4985m','0'),('4.4986m','1.8'),('4.4989m','1.8'),('4.499m','0')]
   post=[('4.5021m','0'),('4.5022m','1.8'),('4.5025m','1.8'),('4.5026m','0')]
  reset_pts += pre+post
  resetb_pts += [(t,'1.8' if v=='0' else '0') for t,v in pre+post]
 reset_pts.append(('5.005m','0')); resetb_pts.append(('5.005m','1.8'))
 rst_pwl='PWL('+' '.join(f'{t} {v}' for t,v in reset_pts)+')'
 rstb_pwl='PWL('+' '.join(f'{t} {v}' for t,v in resetb_pts)+')'
 tag=f'{seq}_p{step:g}v_s{maxstep:g}n'+(f'_m{cmem:g}_c{cpacket:g}' if (cmem,cpacket)!=(100.0,1.0) else '')+(f'_dac{code}' if code>=0 else '')+(f'_v{state_v:g}' if state_v!=0.9 and code<0 else '')+('_trackcm' if track_cm else '')+(f'_r{leak:g}' if leak!=1e15 else '')
 lines=[f'SKY130 passive MIM membrane {tag}',HEADER,
 '.subckt passive_membrane state init_level ptop conn conn_b init init_b rst rst_b rst_level vcm vdd',
 f'Xmem state vcm membrane_mim w_um={cmem:g} l_um={cmem:g}',
 f'Xpacket ptop pbot membrane_mim w_um={cpacket:g} l_um={cpacket:g}',
 'Xpacket_switch pbot state conn conn_b vdd 0 transmission_gate',
 'Xpacket_reset pbot rst_level rst rst_b vdd 0 transmission_gate',
 'Xstate_init state init_level init init_b vdd 0 transmission_gate',
 f'Rleak state vcm {leak:g}', '.ends passive_membrane',
 'Vinit init 0 PWL(0 1.8 2.499u 1.8 2.5u 0 5.005m 0)',
 'Vinitb initb 0 PWL(0 0 2.499u 0 2.5u 1.8 5.005m 1.8)',
 f'Vconn conn 0 {conn_pwl}',
 f'Vconnb conn_b 0 {connb_pwl}',
 f'Vrst rst 0 {rst_pwl}',
 f'Vrstb rst_b 0 {rstb_pwl}']
 lines += [f'Vinitlvl initlvl 0 {state_v:g}']
 pkt_base=state_v if track_cm else 0.9
 reset_level='initlvl' if track_cm and code<0 else 'vcm'
 p1=(pkt_base+step if seq[0]=='p' else (pkt_base-step if seq[0]=='n' else pkt_base)); p2=(pkt_base+step if seq[1]=='p' else (pkt_base-step if seq[1]=='n' else pkt_base))
 lines += [f'Vpkt ptop 0 PWL(0 {pkt_base:g} 499.9u {pkt_base:g} 500u {p1:g} 501.9u {p1:g} 502u {pkt_base:g} 4.4999m {pkt_base:g} 4.5m {p2:g} 4.5019m {p2:g} 4.502m {pkt_base:g} 5.005m {pkt_base:g})',
 'Vrefconn ref_conn 0 0','Vrefconnb ref_connb 0 1.8','Vrefrst ref_rst 0 0','Vrefrstb ref_rstb 0 1.8',
 f'Xpassive state {"vcm" if code>=0 else "initlvl"} ptop conn conn_b init initb rst rst_b {reset_level} vcm vdd passive_membrane']
 measure_lines=['.control','set wr_singlescale','set wr_vecnames',f'tran {maxstep:g}n 5.005m uic',
 'meas tran initial find v(state) at=100u','meas tran after1 find v(state) at=510u','meas tran before2 find v(state) at=4.49m','meas tran final find v(state) at=4.9m']
 if code>=0:
  dac=['Vhi vhi 0 0.95','Vlo vlo 0 0.9']+[f'Vb{bit} b{bit} 0 {1.8 if (code>>bit)&1 else 0:g}' for bit in range(24)]
  dac += ['Xthreshold thrref b23 b22 b21 b20 b19 b18 b17 b16 b15 b14 b13 b12 b11 b10 b9 b8 b7 b6 b5 b4 b3 b2 b1 b0 vhi vlo vdd 0 r2r_dac_u24','Rthreshold thrref thrinit 1']
  lines.remove('Vinitlvl initlvl 0 0.9')
  lines += dac+['Xreference ref thrinit vcm ref_conn ref_connb init initb ref_rst ref_rstb vcm vcm vdd passive_membrane']
  measure_lines += ['meas tran signal_init find v(state) at=100u','meas tran reference_init find v(ref) at=100u','meas tran signal_final find v(state) at=4.9m','meas tran reference_final find v(ref) at=4.9m','meas tran dac_level find v(thrref) at=4.9m']
 wrvec=' v(state) v(ref) v(thrref) v(pbot) v(ptop)' if code>=0 else ' v(state) v(pbot) v(ptop)'
 lines += measure_lines+[f'wrdata ../results/sky130_passive_membrane_{tag}.dat'+wrvec,'quit','.endc','.end']
 BENCH.mkdir(parents=True,exist_ok=True); RES.mkdir(parents=True,exist_ok=True)
 deck=BENCH/f'sky130_passive_membrane_{tag}.cir'; deck.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36','120','ngspice','-b',deck.name]
 run=subprocess.run(cmd,text=True,capture_output=True,timeout=135); log=run.stdout+run.stderr
 (RES/f'sky130_passive_membrane_{tag}.log').write_text(log,encoding='utf-8')
 import re
 vals={k:float(v) for k,v in re.findall(r'(?im)^\s*(initial|after1|before2|final|signal_init|reference_init|signal_final|reference_final|dac_level)\s*=\s*([-+0-9.eE]+)',log)}
 report={'test':'sky130_passive_mim_membrane_two_signed_charge_packets','sequence':seq,'membrane_cap_side_um':cmem,'packet_cap_side_um':cpacket,'packet_topplate_step_v':step,'initial_state_v':state_v if code<0 else 0.9,'packet_common_mode_tracks_initial_state':track_cm,'state_leakage_resistance_ohm':leak,'max_transient_step_ns':maxstep,'measurements_v':vals,'completed':run.returncode==0 and all(k in vals for k in ('initial','after1','before2','final')),'return_code':run.returncode,'scope':f'one passive {cmem:g}um MIM membrane plus {cpacket:g}um packet capacitor, physical SKY130 transmission gates, schematic TT, no OTA during integration, explicit {leak:g}ohm shunt plus device leakage, '+('packet common mode follows initial state' if track_cm else 'packet common mode fixed at VCM')+', '+('R2R DAC threshold initialization tested' if code>=0 else 'ideal fixed-level state initialization')+', no comparator/mismatch/noise/extraction'}
 if code>=0 and 'reference_init' in vals:
  report['threshold_dac_code']=code
  report['signal_minus_reference_at_100us_uv']=(vals['signal_init']-vals['reference_init'])*1e6
  report['signal_minus_reference_at_4p9ms_uv']=(vals['signal_final']-vals['reference_final'])*1e6
  report['dac_output_from_vcm_at_4p9ms_uv']=(vals['dac_level']-0.9)*1e6
 if len(vals)>=4:
  report['first_packet_change_uv']=(vals['after1']-vals['initial'])*1e6
  report['hold_change_before_second_uv']=(vals['before2']-vals['after1'])*1e6
  report['second_packet_change_uv']=(vals['final']-vals['before2'])*1e6
 (RES/f'sky130_passive_membrane_{tag}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,indent=2)); return 0 if report['completed'] else 1
if __name__=='__main__': raise SystemExit(main())
