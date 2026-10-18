"""Native extracted peer-inhibition actuator: no trigger, peer, and own-spiker cases."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_peer_inhibition_v1';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 files={Path(__file__)};texts=[]
 for name in [cell,inv,tg,mim]:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    p=folder/n if key=='sha256' else ROOT/n
    if p.suffix!='.ext':assert sha(p)==h,n
    files.add(p)
  if name==cell:
   fqpath=folder/'flat_cap_qualification.json';fq=json.loads(fqpath.read_text());files.add(fqpath);assert fq['flat_extraction_completed'] and not fq['negative_aggregate_branches']
   for n,h in fq['sha256'].items():
    if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
    files.add(ROOT/n)
   txt=(folder/(fq['flat_subcircuit']+'_cap.spice')).read_text().replace(fq['flat_subcircuit'],cell)
  else:txt=(folder/(name+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',name+'__'+child,txt)
  texts.append(txt)
 stem='gf180_peer_inhibition_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native reset physical module standalone',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vprogram program 0 .45','Vcas cas 0 1.1','Vwrite writecommand 0 PWL(0 3.3 1009.99u 3.3 1010u 0 6050u 0)',f'Vreset resetcommand 0 PWL(0 0 1043.99u 0 1044u 3.3 {1044+width-.01}u 3.3 {1044+width}u 0 6050u 0)']
 for ph in ['write','reset']:lines +=[f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 cases=[('no_trigger',1.66,False,False),('peer',1.66,True,False),('own_spiker',1.66,True,True)];nodes=[]
 for tag,voltage,anyspike,ownspike in cases:
  lines +=[f'Vtarget_{tag} target_{tag} 0 {voltage}']
  for signal,on in [('any',anyspike),('own',ownspike)]:lines +=[f'V{signal}_{tag} {signal}command_{tag} 0 {3.3 if on else 0}',f'X{signal}b_{tag} {signal}command_{tag} {signal}b_{tag} vdd 0 {inv}',f'X{signal}_{tag} {signal}b_{tag} {signal}_{tag} vdd 0 {inv}']
  lines +=[f'Xwrite_{tag} state_{tag} target_{tag} write writeb 0 vdd {tg}',f'Xstore0_{tag} state_{tag} 0 0 {mim}',f'Xstore1_{tag} state_{tag} 0 0 {mim}',f'Vmeter_{tag} state_{tag} tap_{tag} 0',f'Xinhibit_{tag} tap_{tag} target_{tag} program cas reset any_{tag} own_{tag} vdd 0 eligible_{tag} {cell}',f'.ic v(state_{tag})={voltage}']
  nodes +=[f'v(state_{tag})',f'i(Vmeter_{tag})',f'v(eligible_{tag})']
 lines +=['.control','set numdgt=15','tran .005u 6050u 0 1u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native20MOS peer-inhibition actuator with flat91 passive branches, native inverter drivers/writer and two minimumMIM state plates per case. Three isolated no-any-spike/selected-peer/own-spiker fixtures, fixed1ms prebias then one1.609us inhibition pulse and5ms hold. Same external PROGRAM0.45V,CASCODE1.1V,PARK1.66V. External flags emulate latched decisions; retinotopic RMS/learned decrement product, any-spike reduction and upstream snapshot remain unfinished. Record charge/hold error, not original-float amplitude accuracy, complete neuron or population5ms/full-chip acceptance.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-.00605)<1e-12 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   sample=lambda n,t:float(np.interp(t*1e-6,w[:,0],w[:,1+nodes.index(n)]))
   report['cases']=[{'case':tag,'initialized_target_v':v,'any_spike':anyspike,'own_spike':ownspike,'expected_eligible':anyspike and not ownspike,'eligible_during_inhibit_v':sample(f'v(eligible_{tag})',1044.5),'before_inhibit_v':sample(f'v(state_{tag})',1043.5),'after_inhibit_v':sample(f'v(state_{tag})',1049.5),'state_step_v':sample(f'v(state_{tag})',1049.5)-sample(f'v(state_{tag})',1043.5),'hold_drift_v':sample(f'v(state_{tag})',6049.5)-sample(f'v(state_{tag})',1049.5)} for tag,v,anyspike,ownspike in cases]
   cc=report['cases'];peer=cc[1]['state_step_v'];report['selection_levels_pass']=all(c['eligible_during_inhibit_v']>2.9 if c['expected_eligible'] else c['eligible_during_inhibit_v']<.4 for c in cc);report['selected_peer_negative_charge_observed']=peer<0;report['excluded_to_selected_step_ratios']={c['case']:abs(c['state_step_v']/peer) if peer else None for c in [cc[0],cc[2]]}
 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
