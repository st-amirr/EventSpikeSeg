"""Per-module flat-extracted tracking/autozero parking simulation."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_tracking_autozero_parking_v1';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
 files={Path(__file__)};texts=[];cache_changes=[]
 for name in [cell,inv]:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    p=folder/n if key=='sha256' else ROOT/n;actual=sha(p)
    if actual!=h:
     assert p.suffix=='.ext',n
     cache_changes.append({'path':p.relative_to(ROOT).as_posix(),'qualified_sha256':h,'current_sha256':actual,'reason':'Generated hierarchical extraction cache rewritten by parent extraction; not a consumed simulation source. Geometry, GDS, device/cap netlists and flat qualification verified separately.'})
    files.add(p)
  if name==cell:
   fqpath=folder/'flat_cap_qualification.json';fq=json.loads(fqpath.read_text());files.add(fqpath);assert fq['flat_extraction_completed'] and not fq['negative_aggregate_branches']
   for n,h in fq['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
   txt=(folder/(fq['flat_subcircuit']+'_cap.spice')).read_text().replace(fq['flat_subcircuit'],cell)
  else:txt=(folder/(name+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if child!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',name+'__'+child,txt)
  texts.append(txt)
 stem='gf180_tracking_autozero_module_standalone_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native tracking/autozero parking physical module',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vvcm vcm 0 1.65','Iparkref bias 0 1u','Xparkref bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u','Vaz azcommand 0 PWL(0 3.3 1019.99u 3.3 1020u 0 6050u 0)']
 lines +=[f'Xb_az azcommand azb vdd 0 {inv}',f'Xc_az azb az vdd 0 {inv}']
 cases=[('near',1.67),('high',2.0),('low',1.45)];nodes=[]
 for tag,voltage in cases:
  lines +=[f'Vstate_{tag} state_{tag} 0 PWL(0 1.65 1029.99u 1.65 1030u {voltage} 6050u {voltage})',f'Xpark_{tag} state_{tag} park_{tag} vcm az azb vdd 0 bias {cell}',f'.ic v(park_{tag})=1.65']
  nodes +=[f'v(state_{tag})',f'v(park_{tag})']
 lines +=['.control','set numdgt=15','tran .005u 6050u 0 1u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'scope':'Actual13MOS39MIM tracking/autozero parking layout with same-geometry flat extraction and nonnegative routing capacitances. Native inverter AZ/AZB drivers, external1uA bias with schematic PF diode and externalVCM reference. STATE is an external bench stimulus held atVCM through autzero, stepped after release and observed over5ms. This measures the module tracking interface; bias/reference generator and connections to reset/state modules remain external. Nominal only, no trimming or model/fullchip acceptance.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-.00605)<1e-12 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   sample=lambda n,t:float(np.interp(t*1e-6,w[:,0],w[:,1+nodes.index(n)]))
   report['cases']=[{'case':tag,'target_v':v,'park_before_release_v':sample(f'v(park_{tag})',1019.5),'park_before_step_v':sample(f'v(park_{tag})',1029.5),'park_1us_after_step_v':sample(f'v(park_{tag})',1031),'park_10us_after_step_v':sample(f'v(park_{tag})',1040),'park_100us_after_step_v':sample(f'v(park_{tag})',1130),'park_late_v':sample(f'v(park_{tag})',6049.5),'tracking_error_10us_v':sample(f'v(park_{tag})',1040)-v,'tracking_error_late_v':sample(f'v(park_{tag})',6049.5)-v,'hold_drift_v':sample(f'v(park_{tag})',6049.5)-sample(f'v(park_{tag})',1130)} for tag,v in cases]

 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
