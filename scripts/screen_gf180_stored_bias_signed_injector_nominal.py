"""Extracted physically joined stored-bias signed-injector characterization."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_stored_bias_signed_injector_v1';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 files={Path(__file__)};texts=[];cache_changes=[]
 for name in [cell,inv,tg,mim]:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    p=folder/n if key=='sha256' else ROOT/n;actual=sha(p)
    if actual!=h:
     assert p.suffix=='.ext',n
     cache_changes.append({'path':p.relative_to(ROOT).as_posix(),'qualified_sha256':h,'current_sha256':actual,'reason':'Generated extraction cache only, not consumed simulation geometry/netlist; all other source hashes remain enforced.'})
    files.add(p)
  if name==cell:
   fqpath=folder/'flat_cap_qualification.json';fq=json.loads(fqpath.read_text());files.add(fqpath);assert fq['flat_extraction_completed'] and not fq['negative_aggregate_branches']
   for n,h in fq['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
   txt=(folder/(fq['flat_subcircuit']+'_cap.spice')).read_text().replace(fq['flat_subcircuit'],name)
  else:txt=(folder/(name+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',name+'__'+child,txt)
  texts.append(txt)
 stem='gf180_stored_bias_signed_injector_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native signed pulse-duration injection physical module',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vvcm vcm 0 1.65','Vpdata pdata 0 PWL(0 2.5 1014.99u 2.5 1015u 3.3 6050u 3.3)','Vndata ndata 0 PWL(0 .45 1014.99u .45 1015u 0 6050u 0)','Vpcas pcas 0 2.2','Vncas ncas 0 1.1','Vwrite writecommand 0 PWL(0 3.3 1009.99u 3.3 1010u 0 6050u 0)']
 lines +=[f'Xb_write writecommand writeb vdd 0 {inv}',f'Xc_write writeb write vdd 0 {inv}']
 cases=[('positive',True,False),('negative',False,True),('idle',False,False)];nodes=[]
 for tag,pos,neg in cases:
  for phase,enabled in [('pos',pos),('neg',neg)]:
   wave=f'PWL(0 0 1043.99u 0 1044u 3.3 {1044+width-.01}u 3.3 {1044+width}u 0 6050u 0)' if enabled else '0'
   lines +=[f'V{phase}_{tag} {phase}command_{tag} 0 {wave}',f'Xb_{phase}_{tag} {phase}command_{tag} {phase}b_{tag} vdd 0 {inv}',f'Xc_{phase}_{tag} {phase}b_{tag} {phase}_{tag} vdd 0 {inv}']
  lines +=[f'Xwrite_{tag} state_{tag} vcm write writeb 0 vdd {tg}',f'Xstore0_{tag} state_{tag} 0 0 {mim}',f'Xstore1_{tag} state_{tag} 0 0 {mim}',f'Vmeter_{tag} state_{tag} tap_{tag} 0',f'Xinject_{tag} tap_{tag} vcm pdata ndata write writeb pcas ncas pos_{tag} posb_{tag} neg_{tag} negb_{tag} vdd 0 pprogram_{tag} nprogram_{tag} {cell}',f'.ic v(state_{tag})=1.65']
  nodes +=[f'v(state_{tag})',f'i(Vmeter_{tag})',f'v(pprogram_{tag})',f'v(nprogram_{tag})']
 lines +=['.control','set numdgt=15','tran .005u 6050u 0 1u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'pulse_width_us':width,'programmed_p_v':2.5,'programmed_n_v':.45,'scope':'Actual physically joined16MOS2MIM stored-bias signed injector, same-geometry flat extraction with164 nonnegative routing branches. Native phase/state writer and two minimumMIM state loads per arm. Programming data changes to opposite off-state references after physical writers release; held outputs remain connected to actual PF/NF injector gates. Positive/negative/idle pulse and5ms loaded retention measured. Storage-to-source-gate wiring is actual parent metal; state loads and phase drivers remain external extracted fixtures. This characterizes bias storage and source loading, not a calibrated original-float weight-voltage map or weight-to-duration converter. External analog programmer/cascode/PARK/phase commands; no QAT/digital membrane fallback or completePLIF/model/service/chip acceptance.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-.00605)<1e-12 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   sample=lambda n,t:float(np.interp(t*1e-6,w[:,0],w[:,1+nodes.index(n)]))
   report['cases']=[{'case':tag,'before_event_v':sample(f'v(state_{tag})',1043.5),'after_event_v':sample(f'v(state_{tag})',1049.5),'state_step_v':sample(f'v(state_{tag})',1049.5)-sample(f'v(state_{tag})',1043.5),'p_held_before_event_v':sample(f'v(pprogram_{tag})',1043.5),'n_held_before_event_v':sample(f'v(nprogram_{tag})',1043.5),'p_held_late_v':sample(f'v(pprogram_{tag})',6049.5),'n_held_late_v':sample(f'v(nprogram_{tag})',6049.5),'p_held_5ms_drift_v':sample(f'v(pprogram_{tag})',6049.5)-sample(f'v(pprogram_{tag})',1049.5),'n_held_5ms_drift_v':sample(f'v(nprogram_{tag})',6049.5)-sample(f'v(nprogram_{tag})',1049.5),'hold_drift_v':sample(f'v(state_{tag})',6049.5)-sample(f'v(state_{tag})',1049.5),'integrated_charge_into_state_c':float(-np.trapezoid(w[(w[:,0]>=1043.5e-6)&(w[:,0]<=1049.5e-6),1+nodes.index(f'i(Vmeter_{tag})')],w[(w[:,0]>=1043.5e-6)&(w[:,0]<=1049.5e-6),0]))} for tag,pos,neg in cases]
   report['signed_response_observed']=bool(report['cases'][0]['state_step_v']>0 and report['cases'][1]['state_step_v']<0)

 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
