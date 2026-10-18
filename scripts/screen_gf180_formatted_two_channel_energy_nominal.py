"""Native formatted amplitude-times-triangle product voltage characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_formatted_two_channel_energy_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native candidate-minus-penalty formatted energy',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vbase base 0 .9','Vzero vzero 0 1.2','Vpen penalty 0 1.2','Ireference bias 0 2u','Va candidatea 0 PWL(0 1.2 14.99u 1.2 15u 2.0 50u 2.0)','Vb candidateb 0 PWL(0 1.2 29.99u 1.2 30u .4 50u .4)',f'Xenergy candidatea candidateb penalty base vzero root bias vdd 0 {cell}','.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .005u 50u 0 .02u','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' v(candidatea) v(candidateb) v(root) v(bias)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native72MOS88R32MIM compensated candidate-minus-shared-penalty differential formatting into native two-channel energy-square/current-sum/root circuit, actual flat extracted parasitics, typical27C. Three sequential zero/one-active/two-opposite-sign fixtures. CANDIDATE_A/B1.2/2.0/.4V, PENALTY/VZERO1.2V, VBASE.9V, two physical reference diodes with external2uA. Native formatter produces plus/minus (candidate-penalty)/8; no ideal subtractor, gate formatter or sqrt inside cell. Four unused sum OTA branches remain to reuse qualified physical formatter; this is characterization geometry, not a dense optimized frontend. Root threshold offset/nonideal RMS gain, epsilon, clip, learned strength, actual all-channel count/loading and model/population5ms/full-chip acceptance remain unfinished.','complete_RMS_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==5 and np.isfinite(t).all() and abs(t[-1,0]-50e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));r['cases']=[]
   for tag,va,vb,us in [('zero',1.2,1.2,14.5),('one_active',2.0,1.2,29.5),('two_active_opposite_sign',2.0,.4,49.5)]:
    r['cases'].append({'case':tag,'candidate_a_v':va,'candidate_b_v':vb,'shared_penalty_v':1.2,'native_formatted_a_deviation_v':(va-1.2)/8,'native_formatted_b_deviation_v':(vb-1.2)/8,'ideal_formatted_input_rms_v':float(np.sqrt((((va-1.2)/8)**2+((vb-1.2)/8)**2)/2)),'root_v':sample(3,us),'receiver_vsg_v':3.3-sample(3,us),'last0p5us_root_change_v':sample(3,us)-sample(3,us-.5),'bias_v':sample(4,us)})
   v=[c['receiver_vsg_v'] for c in r['cases']];r['one_to_two_zero_subtracted_response_ratio']=float((v[1]-v[0])/(v[2]-v[0]));r['ideal_one_to_two_ratio']=float(1/np.sqrt(2));r['monotonic_native_formatted_energy_observed']=bool(0<v[0]<v[1]<v[2]<3.3)

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
