"""Native triangle rising, falling, and inactive/expired trajectory characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_buffered_adaptation_triangle_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native adaptation triangle',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vpeak peak 0 1.6','Vzero vzero 0 1.2'];cases=[('rising',[1.2,1.4,1.6]),('falling',[1.6,1.8,2.0]),('inactive_expired',[1.1,2.2,2.3])];nodes=[]
 for tag,values in cases:
  a,b,c=values;lines +=[f'Ireference_{tag} bias_{tag} 0 1u',f'Vage_{tag} age_{tag} 0 PWL(0 {a} 4.99u {a} 5u {b} 9.99u {b} 10u {c} 15u {c})',f'Xtriangle_{tag} age_{tag} peak vzero triangle_{tag} bias_{tag} vdd 0 {cell}'];nodes +=[f'v(age_{tag})',f'v(triangle_{tag})',f'v(bias_{tag})']
 lines +=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .005u 15u 0 .02u uic','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native41MOS2R4MIM buffered triangle shaper with flat extracted interconnect. Three trajectories rising/falling/inactive-expired, each with three age levels around fixedVPEAK1.6/VZERO1.2V and physicalPF20/2 reference driven1uA. No ideal reflection, comparator, min/max or analog switch inside circuit; age/reference fixtures ideal. Native unity input follower now removes direct resistor loading of AGE; actual connected resident capacitor still requires simulation. Normalized10mV output bringup gate is local, not trained precision. Actual resident-age source load, calibrated continuous duration and amplitude multiplication/channel reduction still absent. No full-model accuracy/PVT/noise/population5ms/full-chip acceptance.','complete_adaptation_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==10 and np.isfinite(t).all() and abs(t[-1,0]-15e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));cc=[]
   for i,(tag,values) in enumerate(cases):
    points=[]
    for va,us in zip(values,[4.5,9.5,14.5]):
     target=max(1.2,min(va,3.2-va));obs=sample(2+3*i,us);points.append({'age_v':va,'ideal_triangle_v':target,'observed_triangle_v':obs,'output_error_v':obs-target,'ideal_normalized_triangle':(target-1.2)/.4,'observed_normalized_triangle':(obs-1.2)/.4})
    cc.append({'case':tag,'points':points,'max_abs_output_error_v':max(abs(p['output_error_v']) for p in points)})
   r['cases']=cc;r['max_abs_output_error_v']=max(c['max_abs_output_error_v'] for c in cc);r['nominal_triangle_10mv_gate_pass']=bool(r['max_abs_output_error_v']<.01)
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
