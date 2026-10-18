"""Native connected resident adaptation product local sequence."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_resident_adaptation_product_v2';inv='gf180_phase_inverter_fullroute';texts=[];files={Path(__file__)}
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
 lines=['Native analog adaptation resident storage',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vprogram program 0 2.6','Vcas cas 0 2.2','Vreset vreset 0 1.2','Vpark park 0 1.2','Vpeak peak 0 1.6','Ireference bias 0 3u','Vbase base 0 .9','Vcom vcom 0 1.65','Vdata ampdata 0 PWL(0 1.5 89.99u 1.5 90u 1.8 200u 1.8)','Vspike spikecommand 0 PWL(0 3.3 9.99u 3.3 10u 0 99.99u 0 100u 3.3 109.99u 3.3 110u 0 200u 0)','Vadvance advancecommand 0 PWL(0 0 19.99u 0 20u 3.3 21.59u 3.3 21.6u 0 59.99u 0 60u 3.3 61.59u 3.3 61.6u 0 129.99u 0 130u 3.3 131.59u 3.3 131.6u 0 200u 0)']
 for ph in ['spike','advance']:lines +=[f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 lines +=[f'Xresident age amplitude ampdata vreset park program cas advance advanceb spike spikeb peak triangle ampbuf base vcom penalty bias vdd 0 {cell}', '.ic v(age)=1.2 v(amplitude)=1.5','.control','set numdgt=15','tran .02u 200u 0 .1u','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+dp.relative_to(ROOT).as_posix()+' v(age) v(amplitude) v(advance) v(spike) v(triangle) v(ampbuf) v(penalty)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native101MOS48R18MIM resident age/amplitude to native buffered triangle and amplitude buffer to native formatter/product/linear receiver. Actual extracted interconnect, native phase drivers, typical27C. One bounded200us local sequence initialized by DC operating point with SPIKE asserted (resident storage physically written/reset); not a cold-start or5ms retention test. Release write, two age advances, amplitude data changes while write off, spike overwrite/reset, third advance. No ideal AGE/AMPLITUDE/TRIANGLE/product/output clamp. External3uA shared bias for3native references, PP2.6/PCAS2.2/PARK/VZERO1.2,VPEAK1.6,VBASE.9,VCOM1.65V. Analog age voltage uncalibrated; actual model duration/RMS amplitude/expiry/all-channel mapping and dense placement unfinished. Known write-release and cross-coupling errors retained. No model accuracy, complete adaptation/population5ms/full-chip acceptance.','complete_adaptation_accepted':False}
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);ok=bool(run.returncode==0 and w.shape[1]==8 and np.isfinite(w).all() and abs(w[-1,0]-.0002)<1e-12 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,w[:,0],w[:,k]));times=[9.5,19.5,35.,59.5,75.,99.5,109.5,124.5,129.5,150.,199.5];samples={str(us):{'age_v':sample(1,us),'amplitude_v':sample(2,us),'triangle_v':sample(5,us),'buffer_v':sample(6,us),'penalty_v':sample(7,us)} for us in times}
   r['cases']=[{'case':'advance_twice_reset_overwrite_advance_200us','samples_v':samples,'write_release_storage_error_v':sample(2,124.5)-1.8,'penalty_rise_after_two_advances_v':sample(7,75)-sample(7,19.5),'buffer_minus_storage_after_overwrite_v':sample(6,124.5)-sample(2,124.5)}];r['triangle_tracking_max_abs_error_v']=max(abs(v['triangle_v']-max(1.2,min(v['age_v'],3.2-v['age_v']))) for v in samples.values());r['buffer_tracking_max_abs_error_v']=max(abs(v['buffer_v']-v['amplitude_v']) for v in samples.values());r['resident_native_product_sequence_observed']=bool(r['triangle_tracking_max_abs_error_v']<.01 and r['buffer_tracking_max_abs_error_v']<.01 and sample(7,75)>sample(7,19.5));r['final_penalty_voltage_v']=sample(7,199.5)
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
