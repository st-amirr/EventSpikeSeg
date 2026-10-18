"""Native connected resident adaptation product local sequence."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_resident_adaptation_expiry_v3';inv='gf180_phase_inverter_fullroute';texts=[];files={Path(__file__)}
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
 lines=['Native analog adaptation resident storage',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vprogram program 0 2.6','Vcas cas 0 2.2','Vreset vreset 0 1.2','Vpark park 0 1.2','Vpeak peak 0 1.21','Ireference bias 0 5u','Vinactive vinactive 0 1.35','Vexpire vexpire 0 1.22','Vinit initcommand 0 PWL(0 3.3 4.99u 3.3 5u 0 200u 0)','Vbase base 0 .9','Vcom vcom 0 1.65','Vdata ampdata 0 1.5','Vspike spikecommand 0 PWL(0 0 19.99u 0 20u 3.3 29.99u 3.3 30u 0 139.99u 0 140u 3.3 149.99u 3.3 150u 0 200u 0)','Vadvance advancecommand 0 PWL(0 0 9.99u 0 10u 3.3 11.59u 3.3 11.6u 0 39.99u 0 40u 3.3 41.59u 3.3 41.6u 0 79.99u 0 80u 3.3 81.59u 3.3 81.6u 0 119.99u 0 120u 3.3 121.59u 3.3 121.6u 0 169.99u 0 170u 3.3 171.59u 3.3 171.6u 0 200u 0)']
 for ph in ['spike','advance','init']:lines +=[f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 lines +=[f'Xresident age amplitude ampdata vreset park program cas advance spike spikeb peak triangle trianglebuf ampbuf base vcom penalty init initb vinactive vexpire active expired bias vdd 0 {cell}', '.ic v(age)=1.2 v(amplitude)=1.5','.control','set numdgt=15','tran .02u 200u 0 .1u','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+dp.relative_to(ROOT).as_posix()+' v(age) v(amplitude) v(advance) v(spike) v(triangle) v(ampbuf) v(penalty) v(active) v(expired) v(init)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native131MOS48R34MIM resident adaptation, loaded analog expiry comparator and advance gate, two initialization TGs, actual extracted interconnect and native control inverters.200us nominal typical27C: physical INIT writes inactive AGE1.35 and zero amplitude1.2, initial advance must be blocked; spike writes AMP1.5 and resets AGE1.2, two advances approach/cross expiry1.22, later advance must be blocked, second spike resets and permits another advance. VPEAK1.21,VEXPIRE1.22 is a local analog fixture and not trained all-channel calibration. Five physical PMOS references with external5uA. Known write/age-step/product errors retained. No full-model accuracy, retention/noise/corners or full-population5ms/full-chip acceptance.','complete_adaptation_accepted':False}
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);ok=bool(run.returncode==0 and w.shape[1]==11 and np.isfinite(w).all() and abs(w[-1,0]-.0002)<1e-12 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,w[:,0],w[:,k]));times=[4.5,9.,18.,29.5,39.,55.,95.,119.,135.,149.5,165.,199.5];samples={str(us):{'age_v':sample(1,us),'amplitude_v':sample(2,us),'triangle_v':sample(5,us),'buffer_v':sample(6,us),'penalty_v':sample(7,us),'active_v':sample(8,us),'expired_v':sample(9,us)} for us in times}
   initpass=sample(9,9)>2.9 and sample(8,9)<.4 and abs(sample(1,18)-sample(1,9))<.002
   resetpass=sample(8,39)>2.9 and abs(sample(1,29.5)-1.2)<.01
   expirypass=sample(9,119)>2.9 and sample(8,119)<.4 and abs(sample(1,135)-sample(1,119))<.002
   resumepass=sample(8,165)>2.9 and sample(1,199.5)>sample(1,165)+.005
   r['cases']=[{'case':'inactive_init_then_spike_advance_expire_reset_resume','samples_v':samples,'initialization_blocks_advance':bool(initpass),'spike_resets_and_enables':bool(resetpass),'expired_blocks_advance':bool(expirypass),'second_spike_reenables_advance':bool(resumepass),'expired_block_age_change_v':sample(1,135)-sample(1,119)}];r['resident_expiry_initialization_sequence_observed']=bool(initpass and resetpass and expirypass and resumepass)

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
