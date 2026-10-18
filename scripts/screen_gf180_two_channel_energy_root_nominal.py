"""Native two-channel current sum and PMOS square-root receiver characterization."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_two_channel_energy_root_v1';folder=BASE/'layout'/cell;qp=folder/'qualification.json';fp=folder/'flat_cap_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and f['flat_lvs_unique'] and not f['negative_aggregate_branches'];files={Path(__file__),qp,fp}
 for n,h in f['sha256'].items():
  if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
  files.add(ROOT/n)
 flat=folder/(f['flat_subcircuit']+'_cap.spice');files.add(flat);model=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(model.rglob('*.spice'));prefix='/workspace/'+model.relative_to(ROOT).as_posix();stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'_dc.dat');tp=BASE/'results'/(stem+'_transient.dat')
 lines=['Native two-channel energy root',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',flat.read_text().replace(f['flat_subcircuit'],cell),'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 PWL(0 0 .99u 0 1u 3.3 20u 3.3)','Vbase base 0 PWL(0 0 .99u 0 1u .9 20u .9)'];cases=[('zero',0.,0.),('one_active',.1,0.),('two_active_opposite_sign',.1,-.1)];nodes=[]
 for tag,va,vb in cases:
  for ch,v in [('a',va),('b',vb)]:lines +=[f'Vdelta_{ch}_{tag} delta_{ch}_{tag} 0 PWL(0 0 .99u 0 1u {v} 20u {v})',f'Eplus_{ch}_{tag} {ch}p_{tag} base delta_{ch}_{tag} 0 1',f'Eminus_{ch}_{tag} {ch}n_{tag} base delta_{ch}_{tag} 0 -1']
  lines +=[f'Xenergy_{tag} ap_{tag} an_{tag} bp_{tag} bn_{tag} base root_{tag} vdd 0 {cell}'];nodes.append(f'v(root_{tag})')
 lines +=['.control','set numdgt=15','set wr_singlescale','set wr_vecnames','tran .005u 20u 0 .02u uic','wrdata /workspace/'+tp.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native14MOS two-channel kernel-sum/diode-receiver assembly, actual extracted interconnect, three zero/one-active/two-active-opposite-sign fixtures. Supply/common bias ramp at1us, record20us. Differential signed inputs externally formatted around0.9V; ROOT has no forced voltage or behavioral sqrt. Channel normalization is geometric receiver count only; threshold offset, kernel balance error and true RMS mapping remain unaccepted. No candidate-minus-adaptation subtractor, learned-strength multiplier, trained clip, actual full-channel load or full-model/population5ms/full-chip acceptance.','complete_RMS_accepted':False}
 try:
  t=np.loadtxt(tp,skiprows=1);files.add(tp);ok=bool(run.returncode==0 and t.shape[1]==4 and np.isfinite(t).all() and abs(t[-1,0]-20e-6)<1e-15 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,t[:,0],t[:,k]));r['cases']=[{'case':tag,'channel_a_input_v':va,'channel_b_input_v':vb,'ideal_input_rms_v':float(np.sqrt((va*va+vb*vb)/2)),'root_19p5us_v':sample(i+1,19.5),'receiver_vsg_v':3.3-sample(i+1,19.5),'last4p5us_root_change_v':sample(i+1,19.5)-sample(i+1,15.)} for i,(tag,va,vb) in enumerate(cases)];v=[c['receiver_vsg_v'] for c in r['cases']];r['one_to_two_zero_subtracted_response_ratio']=float((v[1]-v[0])/(v[2]-v[0])) if v[2]!=v[0] else None;r['monotonic_energy_response_observed']=bool(0<v[0]<v[1]<v[2]<3.3)
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
