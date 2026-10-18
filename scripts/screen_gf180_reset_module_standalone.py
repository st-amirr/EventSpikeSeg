"""Per-module extracted reset simulation with explicit driven interface fixtures."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_reset_current_steering_v1';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 files={Path(__file__)};texts=[]
 for name in [cell,inv,tg,mim]:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    p=folder/n if key=='sha256' else ROOT/n;assert sha(p)==h,n;files.add(p)
  if name==cell:
   fqpath=folder/'flat_cap_qualification.json';fq=json.loads(fqpath.read_text());files.add(fqpath);assert fq['flat_extraction_completed'] and not fq['negative_aggregate_branches']
   for n,h in fq['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
   txt=(folder/(fq['flat_subcircuit']+'_cap.spice')).read_text().replace(fq['flat_subcircuit'],cell)
  else:txt=(folder/(name+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',name+'__'+child,txt)
  texts.append(txt)
 stem='gf180_reset_module_standalone_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native reset physical module standalone',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vprogram program 0 .45','Vcas cas 0 1.1','Vwrite writecommand 0 PWL(0 3.3 1009.99u 3.3 1010u 0 6050u 0)',f'Vreset resetcommand 0 PWL(0 0 1043.99u 0 1044u 3.3 {1044+width-.01}u 3.3 {1044+width}u 0 6050u 0)']
 for ph in ['write','reset']:lines +=[f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 cases=[('near',1.66,True),('high',1.95,True),('unfired',1.66,False)];nodes=[]
 for tag,voltage,fire in cases:
  lines +=[f'Vtarget_{tag} target_{tag} 0 {voltage}',f'Vdecision_{tag} decision_{tag} 0 {3.3 if fire else 0}',f'Xdecisionb_{tag} decision_{tag} decisionb_{tag} vdd 0 {inv}',f'Xdecisionc_{tag} decisionb_{tag} spike_{tag} vdd 0 {inv}',f'Xwrite_{tag} state_{tag} target_{tag} write writeb 0 vdd {tg}',f'Xstore0_{tag} state_{tag} 0 0 {mim}',f'Xstore1_{tag} state_{tag} 0 0 {mim}',f'Vmeter_{tag} state_{tag} tap_{tag} 0',f'Xreset_{tag} tap_{tag} target_{tag} program cas reset spike_{tag} vdd 0 {cell}',f'.ic v(state_{tag})={voltage}']
  nodes +=[f'v(state_{tag})',f'i(Vmeter_{tag})',f'v(spike_{tag})']
 lines +=['.control','set numdgt=15','tran .005u 6050u 0 1u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Per-module actual12MOS reset layout with flat extraction. Two real minimumMIM load plates, native writer/decision/phase drivers; externally held parking voltage and program/cascode supplies. Driven decision interface deliberately avoids the unfinished sampled-latch integrated interface that fails numerically at release. This qualifies neither sampled-decision integration nor tracking/reference generation. Nominal only, one pulse,5ms hold; no precision tuning or model/service/full-chip acceptance.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-.00605)<1e-12 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   sample=lambda n,t:float(np.interp(t*1e-6,w[:,0],w[:,1+nodes.index(n)]))
   report['cases']=[{'case':tag,'initialized_target_v':v,'commanded_spike':fire,'before_reset_v':sample(f'v(state_{tag})',1043.5),'after_reset_v':sample(f'v(state_{tag})',1049.5),'state_step_v':sample(f'v(state_{tag})',1049.5)-sample(f'v(state_{tag})',1043.5),'hold_drift_v':sample(f'v(state_{tag})',6049.5)-sample(f'v(state_{tag})',1049.5)} for tag,v,fire in cases]
 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
