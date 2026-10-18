"""Native connected resident adaptation product local sequence."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_rms_resident_write_v1';inv='gf180_phase_inverter_fullroute';texts=[];files={Path(__file__)};files.update(BASE/'results'/n for n in ['gf180_formatted_two_channel_energy_v1_nominal_srcd0887bd0b827.json','gf180_high_common_mode_buffer_v1_nominal_src13f24e93708a.json','gf180_rms_clip_strength_frontend_v2_nominal_src52ae34a21229.json'])
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
 lines=['Native analog adaptation resident storage',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vprogram program 0 2.6','Vcas cas 0 2.2','Vreset vreset 0 1.2','Vpark park 0 1.2','Vpeak peak 0 1.6','Ireference bias 0 9u','Infref vdd nfbias 1u','Vrootref rootref 0 2.412488477821002','Vstrength strength 0 1.4','Vmin vmin 0 1.2','Vmax vmax 0 1.8','Vroot root 0 PWL(0 2.4290092931741545 19.99u 2.4290092931741545 20u 2.32476373960146 39.99u 2.32476373960146 40u 1.5 60u 1.5)','Vinactive vinactive 0 2.2','Vexpire vexpire 0 2.0','Vinit initcommand 0 PWL(0 3.3 4.99u 3.3 5u 0 60u 0)','Vbase base 0 .9','Vcom vcom 0 1.2','Vspike spikecommand 0 PWL(0 0 9.99u 0 10u 3.3 14.99u 3.3 15u 0 29.99u 0 30u 3.3 34.99u 3.3 35u 0 49.99u 0 50u 3.3 54.99u 3.3 55u 0 60u 0)','Vadvance advancecommand 0 0']
 for ph in ['spike','advance','init']:lines +=[f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 lines +=[f'Xresident age amplitude vreset park program cas advance spike spikeb peak triangle trianglebuf ampbuf base vcom penalty init initb vinactive vexpire active expired root rootref strength vmin vmax rmsraw rmsclip adaptamp nfbias bias vdd 0 {cell}','.control','set numdgt=15','tran .01u 60u 0 .05u','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+dp.relative_to(ROOT).as_posix()+' v(age) v(amplitude) v(advance) v(spike) v(triangle) v(ampbuf) v(penalty) v(adaptamp) v(rmsraw) v(rmsclip)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native224MOS98R66MIM RMS root conversion/clip/strength output directly drives resident amplitude write TGs, with initialization/expiry/triangle/product retained. Actual flat extracted wiring, typical27C;60us three sequential ROOT fixtures (zero,mid,overrange), each followed by5us spike write and release. No ideal AMP_DATA driver, output correction or fitted subtraction. External ROOT remains an interface fixture; no all-channel energy reduction/feedback. Frozen ROOT_REF2.412488477821002 from independent high-common-mode buffer characterization, supplied1uA NF and drained9uA PMOS masters. ADC and quantized numerical state absent. Known native product gain/offset and write kick retained; no trained normalization, complete bin/RMS sample sequencing, model/population5ms/full-chip acceptance.','complete_adaptation_accepted':False,'root_reference_calibration_v':2.412488477821002}
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);ok=bool(run.returncode==0 and w.shape[1]==11 and np.isfinite(w).all() and abs(w[-1,0]-60e-6)<1e-12 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,w[:,0],w[:,k]));r['cases']=[]
   for tag,on,off in [('zero',14.5,19.),('mid',34.5,39.),('overrange',54.5,59.)]:
    r['cases'].append({'case':tag,'written_amplitude_v':sample(2,on),'native_write_data_v':sample(8,on),'on_write_tracking_error_v':sample(2,on)-sample(8,on),'released_amplitude_v':sample(2,off),'write_release_change_v':sample(2,off)-sample(2,on),'rms_raw_v':sample(9,on),'rms_clip_v':sample(10,on),'age_on_write_v':sample(1,on)})
   cs=r['cases'];v=[c['written_amplitude_v'] for c in cs];r['max_abs_on_write_tracking_error_v']=max(abs(c['on_write_tracking_error_v']) for c in cs);r['native_rms_amplitude_write_observed']=bool(v[0]<v[1]<v[2] and r['max_abs_on_write_tracking_error_v']<.01);r['max_abs_write_release_change_v']=max(abs(c['write_release_change_v']) for c in cs)

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
