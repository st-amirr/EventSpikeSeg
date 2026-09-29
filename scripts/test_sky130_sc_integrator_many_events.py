from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'artifacts/analog_asic'; BENCH=OUT/'benches'; RES=OUT/'results'
COMMON='''.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
'''
def main():
  import re,sys
  arg=lambda k,d: next((x.split('=',1)[1] for x in sys.argv[1:] if x.startswith(k+'=')),str(d))
  count=int(arg('--events',100)); packet=float(arg('--packet-cap-um',1)); cmem=float(arg('--membrane-cap-um',100)); step=float(arg('--packet-step-v',.3)); tstep=float(arg('--tstep-ns',20)); timeout=int(arg('--timeout-s',180))
  times=[500+i*4000/max(count-1,1) for i in range(count)]
  cases={'ref':[],'p_train':['p']*count,'n_train':['n']*count,'mixed':['p' if i%2==0 else 'n' for i in range(count)]}
  lines=['SKY130 TT active OTA virtual-node SC integrator many-event screen',COMMON,'Vdd vdd 0 1.8','Vcm vcm 0 0.9','Vbp vbiasp 0 0.75']
  for name,seq in cases.items():
    lines += [f'Vbn_{name} vbiasn_{name} 0 0.65',f'.ic v(out_{name})=0 v(sum_{name})=0.9',
      f'Vreset_{name} reset_{name} 0 0',f'Vresetb_{name} resetb_{name} 0 1.8',
      f'Vinit_{name} init_{name} 0 0',f'Vinitb_{name} initb_{name} 0 1.8']
    for ctrl in ('packet_reset','connect'):
      off,on=(0,1.8)
      pts=[('0',str(1.8 if ctrl=='packet_reset' else 0))]
      if ctrl=='packet_reset':
        for i,t in enumerate(times):
          pts += [(f'{t-1.1:g}u','0'),(f'{t+1.6:g}u','1.8')]
          if i+1<len(times): pts.append((f'{times[i+1]-1.1:g}u','0'))
        if count==0: pts.append(('5005u','1.8'))
      else:
        for t in times: pts += [(f'{t-.5:g}u','0'),(f'{t-.4:g}u','1.8'),(f'{t+1.4:g}u','1.8'),(f'{t+1.5:g}u','0')]
      if ctrl=='connect': pts.append(('5005u','0'))
      wave='PWL('+' '.join(f'{t} {v}' for t,v in pts)+')'
      lines += [f'V{ctrl}_{name} {ctrl}_{name} 0 {wave}',f'V{ctrl}b_{name} {ctrl}b_{name} 0 '+('PWL('+' '.join(f'{t} {1.8-float(v):g}' for t,v in pts)+')')]
    pts=[('0','0.9')]
    for t,s in zip(times,seq):
      level=0.9+step if s=='p' else 0.9-step
      pts += [(f'{t-.1:g}u','0.9'),(f'{t:g}u',f'{level:g}'),(f'{t+1.4:g}u',f'{level:g}'),(f'{t+1.5:g}u','0.9')]
    pts.append(('5005u','0.9'))
    if name=='ref': pts=[('0','0.9'),('5005u','0.9')]
    lines += [f'Vpkt_{name} ptop_{name} 0 PWL('+' '.join(f'{t} {v}' for t,v in pts)+')',
      f'Xcell_{name} out_{name} sum_{name} ptop_{name} pbot_{name} reset_{name} resetb_{name} packet_reset_{name} packet_resetb_{name} 0 init_{name} initb_{name} connect_{name} connectb_{name} vbiasn_{name} vbiasp vdd 0 vcm sky130_sc_charge_integrator cpacket_um={packet:g} cmem_um={cmem:g}']
  lines += ['.control','set numdgt=15',f'tran {tstep:g}n 5.005m uic']
  for tm,tag in [('499u','pre'),('2.5m','mid'),('4.9m','late'),('5m','final')]:
    for name in cases: lines += [f'meas tran {tag}_{name} find v(out_{name}) at={tm}']
  lines += ['quit','.endc','.end']
  BENCH.mkdir(parents=True,exist_ok=True); RES.mkdir(parents=True,exist_ok=True)
  tag=f'n{count}_cp{packet:g}_cm{cmem:g}_step{step:g}_ts{tstep:g}n'
  deck=BENCH/f'sky130_sc_integrator_many_events_{tag}.cir'; deck.write_text('\n'.join(lines)+'\n')
  cmd=['docker','run','--rm','--memory','8g','--cpus','2','--volume',f'{ROOT}:/workspace:ro','--volume',f'{OUT}:/workspace/artifacts/analog_asic','--workdir','/workspace/artifacts/analog_asic/benches','--entrypoint','timeout','eventspikeseg:analog-ngspice36',str(timeout),'ngspice','-b',deck.name]
  proc=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout+15); log=proc.stdout+proc.stderr; (RES/f'sky130_sc_integrator_many_events_{tag}.log').write_text(log)
  vals={f'{phase}_{name}':float(value) for phase,name,value in re.findall(r'(?im)^\s*(pre|mid|late|final)_(ref|p_train|n_train|mixed)\s*=\s*([-+0-9.eE]+)',log)}
  complete=proc.returncode==0 and len(vals)==16
  changes={}
  if complete:
    for name in ('p_train','n_train','mixed'): changes[name]={phase:(vals[f'{phase}_{name}']-vals[f'{phase}_ref'])*1e3 for phase in ('pre','mid','late','final')}
  report={'test':'sky130_tt_active_ota_sc_virtual_node_many_event_screen','simulation_completed':complete,'return_code':proc.returncode,'event_count_per_train':count,'packet_cap_square_um':packet,'membrane_feedback_cap_square_um':cmem,'packet_topplate_step_v':step,'event_times_us':[times[0],times[-1]],'requested_action_window_us':2.0,'read_state_difference_from_no_event_reference_mv':changes,'measured_absolute_nodes_v':vals,'scope':'One active OTA virtual-summing-node integrator, fixed-amplitude repeated packet pulses, TT schematic. Differential signal-minus-reference is a matched simulator subtraction. No actual float weights, weight-amplitude DAC, threshold/reset/adaptation, mismatch/noise/PVT, layout/extraction, or network feedback.'}
  out=RES/f'sky130_sc_integrator_many_events_{tag}.json'; out.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2)); return 0 if complete else 2
if __name__=='__main__': raise SystemExit(main())
