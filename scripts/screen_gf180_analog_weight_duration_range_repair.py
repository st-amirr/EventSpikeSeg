"""Three-level nominal sampled analog weight-to-duration characterization."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_analog_weight_duration_v1';inv='gf180_phase_inverter_fullroute';tg='gf180_fixed_body_tg_quarter_shorttracks';mim='gf180_mim_5x5_ports_routed'
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
 stem='gf180_analog_weight_duration_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();width=1.609384125256789
 lines=['Native sampled analog magnitude to pulse duration',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vbias bias 0 .75','Vwrite writecommand 0 PWL(0 3.3 1009.99u 3.3 1010u 0 1080u 0)','Varm armcommand 0 PWL(0 0 1039.99u 0 1040u 3.3 1059.99u 3.3 1060u 0 1080u 0)','Vramp ramp 0 PWL(0 1.2 1040u 1.2 1060u 1.95 1080u 1.95)']
 for ph in ['write','arm']:lines +=[f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 cases=[('small',1.5),('middle',1.65),('large',1.8)];nodes=[]
 for tag,voltage in cases:
  lines +=[f'Vdata_{tag} data_{tag} 0 PWL(0 {voltage} 1014.99u {voltage} 1015u 1.4 1080u 1.4)',f'Xduration_{tag} data_{tag} write writeb ramp arm bias vdd 0 pulse_{tag} pulseb_{tag} held_{tag} comp_{tag} out_{tag} {cell}']
  nodes +=[f'v(held_{tag})',f'v(pulse_{tag})',f'v(pulseb_{tag})',f'v(out_{tag})']
 lines +=['.control','set numdgt=15','tran .01u 1080u 0 .05u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 report={'module_simulation_completed':False,'simulator_returncode':run.returncode,'generated_cache_changes':cache_changes,'focused_range_repair':'Original1.4V ramp floor exceeded lowest held magnitude after write release, suppressing the small pulse. Lower common ramp floor to1.2V for all three independent cases; no per-case held-state correction or transistor/layout retuning. Original report preserved.','scope':'Actual19MOS2MIM sampled magnitude-to-duration physical module, flat extraction116 nonnegative routing branches. Three held magnitude data levels, native write/ARM drivers and external linear ramp1.2-to1.95V in20us. Programming data changes after native writer release; no ideal source forces the held node. Rising-ramp comparator terminates ARM-gated output pulse. Nominal monotonic mechanism test, no timing calibration, signed injector connection, autonomous ramp/phase implementation or original-float weight map/model/service/chip acceptance.'}
 try:
  w=np.loadtxt(data,skiprows=1);files.add(data);complete=bool(run.returncode==0 and w.shape[1]==1+len(nodes) and np.isfinite(w).all() and abs(w[-1,0]-.00108)<1e-12 and 'aborted' not in log.lower());report['module_simulation_completed']=complete
  if complete:
   sample=lambda n,t:float(np.interp(t*1e-6,w[:,0],w[:,1+nodes.index(n)]))
   results=[]
   for tag,v in cases:
    y=w[:,1+nodes.index(f'v(pulse_{tag})')];t=w[:,0];mask=(t>=1039e-6)&(t<=1061e-6)
    ii=np.where((y[:-1]<1.65)&(y[1:]>=1.65)&mask[:-1])[0];jj=np.where((y[:-1]>=1.65)&(y[1:]<1.65)&mask[:-1])[0]
    cross=lambda i:float(t[i]+(1.65-y[i])*(t[i+1]-t[i])/(y[i+1]-y[i]))
    rises=[cross(int(i)) for i in ii];falls=[cross(int(i)) for i in jj];width_us=(falls[0]-rises[0])*1e6 if len(rises)==len(falls)==1 else None
    results.append({'case':tag,'programmed_magnitude_v':v,'held_before_ramp_v':sample(f'v(held_{tag})',1039),'rising_edges_s':rises,'falling_edges_s':falls,'pulse_width_us':width_us,'pulse_late_v':sample(f'v(pulse_{tag})',1079)})
   report['cases']=results;report['three_positive_monotonic_widths']=bool(all(c['pulse_width_us'] is not None and c['pulse_width_us']>0 for c in results) and all(results[i]['pulse_width_us']<results[i+1]['pulse_width_us'] for i in range(2)))

 except Exception as e:report['postprocess_error']=str(e)
 report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k!='sha256'}},indent=2))
 assert report['module_simulation_completed']
if __name__=='__main__':main()
