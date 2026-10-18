"""Bounded extracted compact threshold DC trip/offset screen."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=[0,29],default=0);a=p.parse_args();files={Path(__file__)};texts=[];cell='gf180_compact_nf_threshold_fullroute';inv='gf180_phase_inverter_fullroute'
 for name in [cell,inv]:
  d=BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else ROOT/n;assert sha(f)==h,n;files.add(f)
  texts.append((d/(name+'_cap.spice')).read_text())
 stem=f'gf180_compact_threshold_dc_seed{a.seed}_src{sha(Path(__file__))[:12]}';rp=BASE/'results'/(stem+'.json');assert not rp.exists();models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix();data=BASE/'results'/(stem+'.dat')
 lines=['Compact extracted comparator DC',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.param sw_stat_global=0 sw_stat_mismatch={int(bool(a.seed))}','.temp 27','.options reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vbias bias 0 .75','Vref ref 0 1.85','Vsig sig 0 1.1',f'Xcmp sig ref out vdd 0 bias cmp {cell}',f'Xbuf1 out spikeb vdd 0 {inv}',f'Xbuf2 spikeb spike vdd 0 {inv}','.control','set numdgt=15']
 if a.seed:lines +=[f'setseed {a.seed}','reset']
 lines +=['dc Vsig 1.1 2.4 .001','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' v(sig) v(out) v(spike) v(cmp) i(Vdd)','quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 w=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,6));complete=run.returncode==0 and w.ndim==2 and w.shape[1]==6 and len(w)>=1300 and np.isfinite(w).all() and abs(w[-1,0]-2.4)<1e-6 and 'aborted' not in log.lower();metrics={}
 if data.exists():files.add(data)
 if complete:
  crossing=np.where((w[:-1,3]<1.65)&(w[1:,3]>=1.65))[0];trip=None
  if len(crossing)==1:
   i=int(crossing[0]);trip=float(w[i,1]+(1.65-w[i,3])*(w[i+1,1]-w[i,1])/(w[i+1,3]-w[i,3]))
  metrics={'rising_logic_crossings':len(crossing),'trip_input_v':trip,'trip_offset_vs_reference_v':trip-1.85 if trip is not None else None,'max_static_supply_current_a':float(np.max(-w[:,5])),'logic_endpoint_v':[float(w[0,3]),float(w[-1,3])],'raw_output_endpoint_v':[float(w[0,2]),float(w[-1,2])]}
 result={'simulation_completed':bool(complete),'seed':a.seed,'simulator_returncode':run.returncode,**metrics,'scope':'Extracted seven-MOS smallNF-input differential threshold candidate plus two native inverter buffers; external ideal3.3V supply,.75V bias,1.85V threshold reference. Broad bounded DC input sweep. No state loading/kickback, sampled noise, PVT/yield, offset cancellation, gated-bias settling, parent combined layout, model/service/subtractive-reset or completePLIF acceptance.','acceptance':{'threshold_interface':False,'complete_PLIF':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),**metrics},indent=2))
 if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
