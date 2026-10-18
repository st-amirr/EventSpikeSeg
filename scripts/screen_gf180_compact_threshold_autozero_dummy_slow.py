"""Bounded extracted compact threshold DC trip/offset screen."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=[0,29],default=0);a=p.parse_args();files={Path(__file__)};texts=[];cell='gf180_compact_nf_threshold_shielded';inv='gf180_phase_inverter_fullroute'
 for name in [cell,inv,'gf180_fixed_body_tg_quarter_shorttracks','gf180_mim_5x5_ports_routed','gf180_fixed_body_nf025_shorttracks']:
  d=BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback']
  if name!='gf180_mim_5x5_ports_routed':assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique']
  else:
   ap=BASE/'results/gf180_minimum_mim_routed_gds_integrity.json';au=json.loads(ap.read_text());assert au['audit_completed'] and au['cases'][0]['physical_layout_accepted'];files.add(ap)
   for n,h in au['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert sha(f)==h,n;files.add(f)
  texts.append((d/(name+'_cap.spice')).read_text())
 stem=f'gf180_compact_threshold_autozero_dummy_slow_seed{a.seed}_src{sha(Path(__file__))[:12]}';rp=BASE/'results'/(stem+'.json');assert not rp.exists();models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();data=BASE/'results'/(stem+'.dat')
 lines=['Compact shielded autozero comparator',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.param sw_stat_global=0 sw_stat_mismatch={int(bool(a.seed))}','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcm vcm 0 1.65','Vbias bias 0 .75','Vsig sig 0 PWL(0 1.85 7.99u 1.85 8u 1.80 108u 1.90 110u 1.90)','Vaz az_command 0 PWL(0 3.3 4.99u 3.3 5u 0 110u 0)',f'Xazb az_command azb vdd 0 {inv}',f'Xazc azb az vdd 0 {inv}',f'Xcmp sig azin out vdd 0 bias cmp {cell}','Xaz out azin az azb 0 vdd gf180_fixed_body_tg_quarter_shorttracks','Xdummy azin azin azb 0 gf180_fixed_body_nf025_shorttracks','Xcomp out cmp 0 gf180_mim_5x5_ports_routed',f'Xbuf1 out spikeb vdd 0 {inv}',f'Xbuf2 spikeb spike vdd 0 {inv}','.ic v(azin)=1.85 v(out)=1.85']
 for i in range(9):lines.append(f'Xstore{i} azin vcm 0 gf180_mim_5x5_ports_routed')
 lines +=['.control','set numdgt=15']
 if a.seed:lines +=[f'setseed {a.seed}','reset']
 lines +=['tran .005u 110u 0 .02u uic','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' v(sig) v(out) v(spike) v(cmp) v(azin) v(az) i(Vdd)','quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 w=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,8));complete=run.returncode==0 and w.ndim==2 and w.shape[1]==8 and len(w)>1 and np.isfinite(w).all() and abs(w[-1,0]-110e-6)<1e-12 and 'aborted' not in log.lower();metrics={}
 if data.exists():files.add(data)
 if complete:
  mask=(w[:,0]>=8e-6)&(w[:,0]<=108e-6);v=w[mask];crossing=np.where((v[:-1,3]<1.65)&(v[1:,3]>=1.65))[0];trip=None
  if len(crossing)==1:
   i=int(crossing[0]);trip=float(v[i,1]+(1.65-v[i,3])*(v[i+1,1]-v[i,1])/(v[i+1,3]-v[i,3]))
  sample=lambda t,c:float(np.interp(t*1e-6,w[:,0],w[:,c]));hold=sample(4.5,5);released=sample(5.5,5)
  metrics={'rising_logic_crossings':len(crossing),'trip_input_v':trip,'trip_offset_vs_calibration_v':trip-1.85 if trip is not None else None,'sampled_reference_before_release_v':hold,'sampled_reference_after_release_v':released,'autozero_release_reference_shift_v':released-hold,'reference_end_minus_after_release_v':sample(109.5,5)-released,'logic_scan_endpoint_v':[float(v[0,3]),float(v[-1,3])],'mean_supply_current_during_scan_a':float(np.mean(-v[:,7])),'maximum_azin_v':float(np.max(w[:,5])),'minimum_azin_v':float(np.min(w[:,5]))}
 result={'simulation_completed':bool(complete),'seed':a.seed,'simulator_returncode':run.returncode,**metrics,'scope':'Shielded extracted7MOS comparator with native quarterTG output-to-negative-input autozero and opposite-phase minimumNF dummy at stored input, nine real minimum MIM reference units and one real compensation MIM, native clock/buffers. Input held at1.85V for calibration then fresh1.80..1.90V ramp at1mV/us (ten times slower); bias continuously .75V. Ideal signal source, parent schematic. Seed29 is one configured native case, not matched per-device statistics to earlier DC topology. No state loading, RPEX/native sampled noise/retention/PVT/yield, reference generation, subtractive reset/model/service/full-parent layout acceptance','acceptance':{'threshold_interface':False,'complete_PLIF':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),**metrics},indent=2))
 if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
