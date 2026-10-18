"""Native extracted analog age steps and spike-conditioned amplitude overwrite."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_adaptation_resident_v2';inv='gf180_phase_inverter_fullroute';texts=[];files={Path(__file__)}
 for name in [cell,inv]:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    pp=folder/n if key=='sha256' else ROOT/n
    if pp.suffix!='.ext':assert sha(pp)==h,n
    files.add(pp)
  if name==cell:
   fp=folder/'flat_cap_qualification.json';fq=json.loads(fp.read_text());files.add(fp);assert fq['flat_lvs_unique'] and not fq['negative_aggregate_branches']
   for n,h in fq['sha256'].items():
    if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
    files.add(ROOT/n)
   txt=(folder/(fq['flat_subcircuit']+'_cap.spice')).read_text().replace(fq['flat_subcircuit'],name)
  else:txt=(folder/(name+'_cap.spice')).read_text()
  for ch in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if ch!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(ch)+r'(?![A-Za-z0-9_])',name+'__'+ch,txt)
  texts.append(txt)
 stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'.dat');models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Native analog adaptation resident storage',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vprogram program 0 2.6','Vcas cas 0 2.2','Vreset vreset 0 1.2','Vpark park 0 1.2','Vdata ampdata 0 PWL(0 1.5 10000u 1.5 10001u 1.8 16050u 1.8)','Vspike spikecommand 0 PWL(0 3.3 1009.99u 3.3 1010u 0 11029.99u 0 11030u 3.3 11039.99u 3.3 11040u 0 16050u 0)','Vadvance advancecommand 0 PWL(0 0 1043.99u 0 1044u 3.3 1045.59u 3.3 1045.6u 0 6043.99u 0 6044u 3.3 6045.59u 3.3 6045.6u 0 11059.99u 0 11060u 3.3 11061.59u 3.3 11061.6u 0 16050u 0)']
 for ph in ['spike','advance']:lines +=[f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 lines +=[f'Xresident age amplitude ampdata vreset park program cas advance advanceb spike spikeb vdd 0 {cell}', '.ic v(age)=1.2 v(amplitude)=1.5','.control','set numdgt=15','tran .005u 16050u 0 1u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+dp.relative_to(ROOT).as_posix()+' v(age) v(amplitude) v(advance) v(spike)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native10MOS2MIM analog adaptation resident storage, extracted routing and native phase drivers. One sequence, fixed1ms common startup, two isolated age advances5ms apart, spike-driven age reset/amplitude overwrite, then another advance and5ms hold. External PP2.6V,PCAS2.2V,PARK/VRESET1.2V, amplitude data1.5 then1.8V. Age voltage is uncalibrated; no RMS/strength generation, triangle shaping/duration normalization, expiry control, penalty reduction, full-neuron accuracy or population5ms/full-chip acceptance.'}
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);ok=bool(run.returncode==0 and w.shape[1]==5 and np.isfinite(w).all() and abs(w[-1,0]-.01605)<1e-12 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,w[:,0],w[:,k]));times=[1043.5,1049.5,6043.5,6049.5,11029.5,11039.5,11049.5,11059.5,11065.5,16049.5];samples={str(us):{'age_v':sample(1,us),'amplitude_v':sample(2,us)} for us in times};steps=[sample(1,b)-sample(1,a) for a,b in [(1043.5,1049.5),(6043.5,6049.5),(11059.5,11065.5)]]
   r['cases']=[{'case':'advance_twice_reset_overwrite_advance','samples_v':samples,'age_steps_v':steps,'age_reset_error_v':sample(1,11039.5)-1.2,'amplitude_initial_hold_drift_v':sample(2,6049.5)-sample(2,1049.5),'amplitude_before_spike_after_data_change_v':sample(2,11029.5),'amplitude_after_overwrite_v':sample(2,11049.5),'amplitude_final_hold_drift_v':sample(2,16049.5)-sample(2,11065.5),'age_final_hold_drift_v':sample(1,16049.5)-sample(1,11065.5)}];r['storage_sequence_observed']=bool(all(v>0 for v in steps) and abs(sample(1,11039.5)-1.2)<.01 and sample(2,11029.5)<1.6 and sample(2,11049.5)>1.7)
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
