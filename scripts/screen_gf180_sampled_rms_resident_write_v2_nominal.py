"""Native connected resident adaptation product local sequence."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_sampled_rms_resident_write_v2';inv='gf180_phase_inverter_fullroute';texts=[];files={Path(__file__)};files.update(BASE/'results'/n for n in ['gf180_formatted_two_channel_energy_v1_nominal_srcd0887bd0b827.json','gf180_high_common_mode_buffer_v1_nominal_src13f24e93708a.json','gf180_rms_clip_strength_frontend_v2_nominal_src52ae34a21229.json'])
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
 lines=['Native analog adaptation resident storage',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vprogram program 0 2.6','Vcas cas 0 2.2','Vreset vreset 0 1.2','Vpark park 0 1.2','Vpeak peak 0 1.6','Ireference bias 0 10u','Infref vdd nfbias 1u','Vrootref rootref 0 2.412488477821002','Vstrength strength 0 1.4','Vmin vmin 0 1.2','Vmax vmax 0 1.8','Vroot root 0 PWL(0 2.4290092931741545 8.99u 2.4290092931741545 9u 1.5 19.99u 1.5 20u 2.32476373960146 28.99u 2.32476373960146 29u 2.4290092931741545 39.99u 2.4290092931741545 40u 1.5 48.99u 1.5 49u 2.32476373960146 60u 2.32476373960146)','Vinactive vinactive 0 2.2','Vexpire vexpire 0 2.0','Vinit initcommand 0 PWL(0 3.3 4.99u 3.3 5u 0 60u 0)','Vbase base 0 .9','Vcom vcom 0 1.2','Vspike spikecommand 0 PWL(0 0 9.99u 0 10u 3.3 14.99u 3.3 15u 0 29.99u 0 30u 3.3 34.99u 3.3 35u 0 49.99u 0 50u 3.3 54.99u 3.3 55u 0 60u 0)','Vadvance advancecommand 0 0','Vcapture capturecommand 0 PWL(0 3.3 7.99u 3.3 8u 0 25.99u 0 26u 3.3 27.99u 3.3 28u 0 45.99u 0 46u 3.3 47.99u 3.3 48u 0 60u 0)']
 for ph in ['spike','advance','init','capture']:lines +=[f'Xb_{ph} {ph}command {ph}b vdd 0 {inv}',f'Xc_{ph} {ph}b {ph} vdd 0 {inv}']
 lines +=[f'Xresident age amplitude vreset park program cas advance spike spikeb peak triangle trianglebuf ampbuf base vcom penalty init initb vinactive vexpire active expired root rootref strength vmin vmax rmsraw rmsclip adaptamp capture captureb ampcapture rmscapture ampcapturebuf nfbias bias vdd 0 {cell}','.control','set numdgt=15','tran .01u 60u 0 .05u','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+dp.relative_to(ROOT).as_posix()+' v(age) v(amplitude) v(advance) v(spike) v(triangle) v(ampbuf) v(penalty) v(adaptamp) v(rmsraw) v(rmsclip) v(ampcapture) v(rmscapture) v(ampcapturebuf)','quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native236MOS98R72MIM capture of RMS/strength amplitude before spike/reset with high-impedance held nodes confined to a local shielded island, native unity buffer isolates captured amplitude from actual resident write TGs, native resident age/amplitude/expiry retained. Actual flat extraction, typical27C,60us three ordered fixtures. CAPTURE ends8/28/48us; ROOT deliberately changes9/29/49us; SPIKE writes10..15/30..35/50..55us. Sampling and write phases never overlap. First capture is physically active at DC operating point; no ideal held state, ADC, quantized state or measured-output correction. Frozen ROOT_REF2.412488477821002 and external10uA PMOS/1uA NF masters. ROOT is still external; no all-channel energy reduction connection or native autonomous phase schedule/full model/5ms/full-chip acceptance. Known amplitude gain, capture/write kick and init/expiry errors retained.','complete_adaptation_accepted':False,'root_reference_calibration_v':2.412488477821002}
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);ok=bool(run.returncode==0 and w.shape[1]==14 and np.isfinite(w).all() and abs(w[-1,0]-60e-6)<1e-12 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,w[:,0],w[:,k]));r['cases']=[]
   for tag,cap,pre,on,off in [('zero',7.5,9.5,14.5,19.),('mid',27.5,29.5,34.5,39.),('overrange',47.5,49.5,54.5,59.)]:
    r['cases'].append({'case':tag,'amplitude_source_at_capture_v':sample(8,cap),'amplitude_capture_on_v':sample(11,cap),'held_amplitude_before_write_v':sample(11,pre),'held_amplitude_during_write_v':sample(11,on),'capture_release_shift_v':sample(11,pre)-sample(8,cap),'held_change_during_write_v':sample(11,on)-sample(11,pre),'source_after_counterfactual_root_change_v':sample(8,on),'buffered_captured_data_v':sample(13,on),'written_amplitude_v':sample(2,on),'on_write_tracking_error_v':sample(2,on)-sample(13,on),'released_amplitude_v':sample(2,off),'write_release_change_v':sample(2,off)-sample(2,on),'held_rms_v':sample(12,on)})
   cs=r['cases'];r['max_abs_on_write_tracking_error_v']=max(abs(c['on_write_tracking_error_v']) for c in cs);r['max_abs_capture_release_shift_v']=max(abs(c['capture_release_shift_v']) for c in cs);r['max_abs_held_change_during_write_v']=max(abs(c['held_change_during_write_v']) for c in cs);r['pre_reset_capture_write_sequence_observed']=bool(r['max_abs_on_write_tracking_error_v']<.01 and r['max_abs_capture_release_shift_v']<.01 and r['max_abs_held_change_during_write_v']<.01);r['max_abs_write_release_change_v']=max(abs(c['write_release_change_v']) for c in cs)

 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
