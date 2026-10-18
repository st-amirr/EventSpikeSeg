"""Recover completed native reset waveform after numpy trapz API failure; no resimulation."""
import hashlib,json,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stem='gf180_resident_subtractive_reset_4fc563dbe5_src177e3f5966b3';files={Path(__file__)}
 for rel in [f'results/{stem}.dat',f'results/{stem}.log',f'results/{stem}_postprocess_failure.json',f'benches/{stem}.spice',f'tools/source_snapshots/{stem}.py']:files.add(BASE/rel)
 snapshot=BASE/f'tools/source_snapshots/{stem}.py';assert sha(snapshot).startswith('177e3f5966b3')
 settings={'width_us':1,'gate_v':.45,'seed':0};assert hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest().startswith('4fc563dbe5')
 deck=(BASE/f'benches/{stem}.spice').read_text();log=(BASE/f'results/{stem}.log').read_text();assert 'aborted' not in log.lower() and 'timestep too small' not in log.lower() and 'Vprogram program 0 0.45' in deck
 names=['gf180_state_update_detailstem_ch3_pad06_v2','gf180_compact_nf_threshold_shielded','gf180_phase_inverter_fullroute','gf180_fixed_body_nf025_shorttracks','gf180_fixed_body_tg_quarter_shorttracks','gf180_mim_5x5_ports_routed','gf180_source_nf05_l1_compact']
 for name in names:
  d=BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert sha(f)==h,n;files.add(f)
 files.update((BASE/'pdk/gf180_primitive_source/models/ngspice').rglob('*.spice'));files.add(BASE/'results/gf180_trained_beta_detailstem_ch3_secant_reference.json')
 targets={'low':1.652,'near':1.664,'high':2.1};arms=['idle','neutral','active'];nodes=[]
 for tag in targets:
  for arm in arms:
   n=arm+'_'+tag;nodes +=['state_'+n,'spike_'+n,'held_'+n,'ng_'+n,'latch_'+n,'i(Vmeter_'+n+')']
 w=np.loadtxt(BASE/f'results/{stem}.dat',skiprows=1);assert w.ndim==2 and w.shape[1]==55 and np.isfinite(w).all() and np.all(np.diff(w[:,0])>0) and abs(w[-1,0]-50e-6)<1e-12
 sample=lambda n,t:float(np.interp(t*1e-6,w[:,0],w[:,1+nodes.index(n)]));mask=(w[:,0]>=43.5e-6)&(w[:,0]<=49.5e-6);cases=[]
 for tag,target in targets.items():
  case={'target_v':target,'arms':{}}
  for arm in arms:
   n=arm+'_'+tag;before=sample('state_'+n,43.5);after=sample('state_'+n,49.5);current=w[:,1+nodes.index('i(Vmeter_'+n+')')]
   case['arms'][arm]={'state_before_v':before,'state_after_v':after,'state_step_v':after-before,'latched_spike_before_v':sample('held_'+n,43.5),'latched_spike_after_v':sample('held_'+n,49.5),'gate_midpulse_v':sample('ng_'+n,44.5),'integrated_sink_charge_c':float(np.trapezoid(current[mask],w[mask,0]))}
  ref=case['arms']['idle'];act=case['arms']['active'];neutral=case['arms']['neutral'];case.update(active_minus_idle_step_v=act['state_step_v']-ref['state_step_v'],neutral_minus_idle_step_v=neutral['state_step_v']-ref['state_step_v'],active_minus_neutral_step_v=act['state_step_v']-neutral['state_step_v']);cases.append(case)
 out=BASE/'results'/(stem+'.json');assert not out.exists();r={'simulation_completed':True,'recovered_from_saved_waveform':True,'settings':settings,'cases':cases,'requested_base_reset_v':.006875,'scope':'Recovery only after native completed trace reached50us and original parser failed on removed numpy.trapz. No native rerun. Nine resident assemblies: three writer targets with matched idle, zero-program neutral pulse and active native cascode sink. Extracted state/beta/comparator, real MIM decision sampler and native switches/buffers; external phases/gate/cascode references. Gate pulse uncalibrated; static mismatch arms not matched per-device statistics. No adaptive reset, repeated cycles, noise/PVT/yield, physical combined parent, original-float accuracy/population service/chip acceptance. Range64 remains unaccepted.','acceptance':{'subtractive_reset':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}};out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(out),'cases':cases},indent=2))
if __name__=='__main__':main()
