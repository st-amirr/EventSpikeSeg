"""Bounded extracted memory-readout to native signed-injector integration."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pref(p):return '/workspace/'+p.relative_to(ROOT).as_posix()
def main():
 mem='gf180_bank_pair_shared_readout_v3';inj='gf180_sequenced_signed_injector_v2';bridge='gf180_storage_compute_level_bridge_v1';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 folders=[BASE/'layout'/n for n in [mem,inj,bridge,inv,tg,mim]];quals=[json.loads((d/'qualification.json').read_text()) for d in folders]
 for q in quals:assert q['magic_drc_count']==0 and q['lvs_unique']
 mq=json.loads((folders[0]/'flat_cap_full_qualification.json').read_text());iq=json.loads((folders[1]/'flat_cap_qualification.json').read_text())
 assert mq['flat_extraction_completed'] and mq['all_flat_extraction_node_ground_caps_verified'] and iq['flat_extraction_completed'] and not iq['negative_aggregate_branches']
 bq=json.loads((folders[2]/'flat_cap_qualification.json').read_text());assert bq['flat_extraction_completed'] and bq['flat_lvs_unique']
 sources=[folders[0]/(mq['flat_subcircuit']+'_fullcap.spice'),folders[1]/(iq['flat_subcircuit']+'_cap.spice'),folders[2]/(bq['flat_subcircuit']+'_cap.spice'),folders[3]/(inv+'_cap.spice'),folders[4]/(tg+'_cap.spice'),folders[5]/(mim+'_cap.spice')]
 used={p for p in sources}
 texts=[]
 for i,p in enumerate(sources):
  txt=p.read_text();top=[mem,inj,bridge,inv,tg,mim][i]
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=top:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',f'{top}__{child}',txt)
  texts.append(txt)
 stem='gf180_readout_bridge_to_signed_injector_native_v1';report_path=BASE/'results'/(stem+'.json');assert not report_path.exists();data=BASE/'results'/(stem+'.dat');deck=BASE/'benches'/(stem+'.spice');logp=BASE/'results'/(stem+'.log')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';modelprefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Combined extracted memory-to-injector event test',f'.include {modelprefix}/design.spice',f'.lib {modelprefix}/sm141064.spice typical',f'.lib {modelprefix}/sm141064.spice mimcap_typical',f'.lib {modelprefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-4 abstol=1e-16 vntol=1e-7 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.65','Ib0 0 B0_BIAS 1u','Ib1 0 B1_BIAS 1u','Vpprogram PPROGRAM 0 2.5','Vnprogram NPROGRAM 0 .613','Vpcas PCAS 0 2.2','Vncas NCAS 0 1.1','Vresetref RESET_REFERENCE 0 1.0','Vbias BIAS 0 .75','Vsref SREF 0 1.626','Vcref CREF 0 2.5','Ibbridge BRIDGE_BIAS 0 6u','Creturnw RETURN_WEIGHT 0 100f','Creturnz RETURN_ZERO 0 100f','Vrampbias RAMP_BIAS 0 2.6','Vrampcas RAMP_CAS 0 2.2','Vsignp SIGNP 0 0','Vsignn SIGNN 0 3.3','Vclock_src CLOCK_SRC 0 PULSE(0 3.3 .2u .01u .01u 9.99u 20u)','Vreset_src RESET_SRC 0 PWL(0 3.3 29.9u 3.3 30u 0 100u 0)','Vrequest_src REQUEST_SRC 0 PWL(0 0 34.9u 0 35u 3.3 50.9u 3.3 51u 0 100u 0)','Vaddr0 A0 0 0','Vaddr1 A1 0 0','Vaddr2 A2 0 0','Vbank BANK_SELECT 0 0','Vwrite WRITE_CMD 0 PWL(0 3.3 5.9u 3.3 6u 0 100u 0)','Vread READ_CMD 0 PWL(0 0 19.9u 0 20u 3.3 100u 3.3)']
 for ph in ['CLOCK','RESET','REQUEST']:
  lines += [f'Xb_{ph.lower()} {ph}_SRC {ph}B VDD VSS {inv}',f'Xc_{ph.lower()} {ph}B {ph} VDD VSS {inv}']
 for c in range(8):lines.append(f'Vdata{c} DATA{c} 0 {1.4 if c==0 else 1.0}')
 mports=quals[0]['ports'];lines.append('Xmemory '+' '.join(mports)+' '+mq['flat_subcircuit']);lines += ['Xbridge_weight READOUT0 MAG_DATA RETURN_WEIGHT BRIDGE_BIAS SREF CREF VDD VSS '+bridge+'__'+bq['flat_subcircuit'], 'Xbridge_zero READOUT1 MAG_ZERO RETURN_ZERO BRIDGE_BIAS SREF CREF VDD VSS '+bridge+'__'+bq['flat_subcircuit']]
 states=[f'B{b}_STATE{r}{c}' for b in range(2) for r in range(8) for c in range(8)]
 for sign,signnet in [('P','SIGNP')]:
  lines += [f'Xstate_{sign} STATE_{sign} 0 0 {mim}',f'Xstateb_{sign} STATE_{sign} 0 0 {mim}',f'Vstate_meter_{sign} STATE_{sign} TAP_{sign} 0',f'Xinjector_{sign} CLOCK RESET REQUEST MAG_DATA {signnet} TAP_{sign} 0 PPROGRAM NPROGRAM PCAS NCAS BIAS RESET_REFERENCE RAMP_BIAS RAMP_CAS VDD VSS READY_{sign} SAMPLE_{sign} ARM_{sign} RECOVER_{sign} DONE_{sign} PULSE_{sign} POS_{sign} NEG_{sign} {inj}__{iq["flat_subcircuit"]}']
  lines += [f'Xreset_writer_{sign} STATE_{sign} VCM RESET RESETB VSS VDD {tg}']
 nodes=['v(READOUT0)','v(READOUT1)','v(MAG_DATA)','v(MAG_ZERO)','v(B0_STATE00)','v(B0_STATE01)']
 for sign in ['P']:nodes += [f'v({x}_{sign})' for x in ['STATE','READY','SAMPLE','ARM','RECOVER','DONE','PULSE','POS','NEG']]+[f'i(Vstate_meter_{sign})']
 lines += ['.control','set numdgt=15',f'tran .01u 100u 0 .05u','set wr_singlescale','set wr_vecnames',f'wrdata {pref(data)} '+' '.join(nodes),'quit','.endc','.end']
 deck.write_text('\n'.join(lines)+'\n')
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','180','ngspice','-b',pref(deck)],capture_output=True,text=True,timeout=195)
 log=run.stdout+run.stderr;logp.write_text(log)
 result={'module_simulation_completed':False,'simulator_returncode':run.returncode,'full_chip_layout_complete':False,'original_float_accuracy_accepted':False,'full_5ms_service_accepted':False,'scope':'Combined routed GF180 shared two-bank readout parent using 7,885 verified extracted routing-cap branches and the physically extracted 230-MOS/4-MIM sequencer/injector. Row0 bank0 contains a 1.4V full-magnitude candidate in DATA0 and 1.0V zero candidate in DATA1; actual READOUT0 drives injector MAG_DATA and actual READOUT1 drives injector VRESET. One positive-sign injector receives a common native request and clock. This characterizes one memory-to-charge event at typical 27C; it is not model accuracy, mismatch/PVT, complete array access or 5ms population service.'}
 try:
  w=np.loadtxt(data,skiprows=1);names=[x.strip().lower() for x in data.read_text().splitlines()[0].split()];t=w[:,0];assert np.isfinite(w).all() and np.all(np.diff(t)>=0)
  result['module_simulation_completed']=bool(run.returncode==0 and abs(t[-1]-100e-6)<1e-12 and 'aborted' not in log.lower());sample=lambda name,us:float(np.interp(us*1e-6,t,w[:,names.index(name.lower())]))
  if result['module_simulation_completed']:
   result['readout_zero_reference_v_at_35us']=sample('v(readout1)',35);result['readout_weight_v_at_35us']=sample('v(readout0)',35);result['readout_delta_v_at_35us']=result['readout_weight_v_at_35us']-result['readout_zero_reference_v_at_35us'];rows=[]
   for sign in ['P']:
    yy=w[:,names.index(f'v(pulse_{sign.lower()})')];mask=(t>=79e-6)&(t<=95e-6);rise=np.where((yy[:-1]<1.65)&(yy[1:]>=1.65)&mask[:-1])[0];fall=np.where((yy[:-1]>=1.65)&(yy[1:]<1.65)&mask[:-1])[0]
    cross=lambda i:float(t[i]+(1.65-yy[i])*(t[i+1]-t[i])/(yy[i+1]-yy[i]));rs=[cross(int(i)) for i in rise];fs=[cross(int(i)) for i in fall];wd=(fs[0]-rs[0])*1e6 if len(rs)==len(fs)==1 else None
    rows.append({'sign':sign,'state_before_v':sample(f'v(state_{sign.lower()})',79),'state_after_v':sample(f'v(state_{sign.lower()})',95),'state_step_v':sample(f'v(state_{sign.lower()})',95)-sample(f'v(state_{sign.lower()})',79),'pulse_width_us':wd,'rising_edges_s':rs,'falling_edges_s':fs,'ready_end_v':sample(f'v(ready_{sign.lower()})',99),'done_end_v':sample(f'v(done_{sign.lower()})',99),'net_charge_into_state_c':float(-np.trapezoid(w[(t>=79e-6)&(t<=95e-6),names.index(f'i(vstate_meter_{sign.lower()})')],t[(t>=79e-6)&(t<=95e-6)]))})
   result['signed_event_results']=rows;result['positive_event_observed']=bool(rows[0]['state_step_v']>0)
 except Exception as e:result['postprocess_error']=str(e)
 result['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),*sources,*[d/'qualification.json' for d in folders],folders[0]/'flat_cap_full_qualification.json',folders[1]/'flat_cap_qualification.json',folders[2]/'flat_cap_qualification.json',deck,logp,data]+[models/n for n in ['design.spice','sm141064.spice','sm141064_mim.spice','smbb000149.spice']]};report_path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(report_path),**result},indent=2));assert result['module_simulation_completed']
if __name__=='__main__':main()
