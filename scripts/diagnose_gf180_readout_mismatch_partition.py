"""Static native headroom diagnosis using the unchanged failed transient device hierarchy."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['native','ideal_ota','ideal_ota_current'],required=True);args=parser.parse_args()
 donor=BASE/'results/gf180_writer_memory_readout_headroom020_bf2c02cc26_src5804b639b2e2.json';d=json.loads(donor.read_text());source=Path(__file__);files={source,donor}
 for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
 original=next(ROOT/n for n in d['sha256'] if '/benches/' in n and n.endswith('.spice'));text=original.read_text().split('.control')[0]
 for phase,value in [('write',3.3),('outer',3.3),('midclamp',0),('read',3.3),('park',0)]:text=re.sub(r'(?m)^V'+phase+r' '+phase+r'_command 0 .*$',f'V{phase} {phase}_command 0 {value}',text)
 for name,value in [('low',.75),('mid',1.65),('high',2.55)]:text=re.sub(r'(?m)^Vbus_'+name+r' bus_source_'+name+r' 0 .*$',f'Vbus_{name} bus_source_{name} 0 {value}',text)
 stem='gf180_readout_mismatch_partition_'+args.mode+'_src'+sha(source)[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();data=BASE/'results'/(stem+'.dat')
 if args.mode!='native':
  assert text.count('Xclamp COLUMN CLAMP MIRROR ')==1 and text.count('Xinverse REPCOL CLAMP OUT ')==1
  text=text.replace('Xclamp COLUMN CLAMP MIRROR ','Xclamp COLUMN CLAMP clamp_native_out ').replace('Xinverse REPCOL CLAMP OUT ','Xinverse REPCOL CLAMP inverse_native_out ')
  # Insert diagnostic control sources inside only the readout parent.
  marker='Xrepfeed REPCOL MIRROR VDD VDD VSS '
  assert text.count(marker)==1
  index=text.index(marker)
  text=text[:index]+"Bdiagnostic_clamp MIRROR VSS V={min(3.3,max(0,2.5+1e5*(v(COLUMN)-v(CLAMP))))}\nBdiagnostic_inverse OUT VSS V={min(3.3,max(0,1.65+1e5*(v(REPCOL)-v(CLAMP))))}\n"+text[index:]
 if args.mode=='ideal_ota_current':
  assert text.count('Xfeed COLUMN MIRROR ')==1
  text=text.replace('Xfeed COLUMN MIRROR ','Xfeed measured_feed MIRROR ').replace('Xrepfeed REPCOL MIRROR ','Xrepfeed unused_repfeed MIRROR ')
  index=text.index('Xrepfeed unused_repfeed')
  text=text[:index]+'Vdiagnostic_current measured_feed COLUMN 0\nFdiagnostic_replica VDD REPCOL Vdiagnostic_current 1\nRunused_repfeed unused_repfeed VSS 10000\n'+text[index:]
 modeldump=BASE/'results'/(stem+'_models.txt')
 vectors=['v(bus_source_low)','v(state_low)','v(decoded_low)','v(column_low)','v(refcol_low)','v(state_mid)','v(decoded_mid)','v(state_high)','v(decoded_high)']
 text+='\n.control\nset numdgt=15\nsetseed 29\nreset\nset wr_singlescale\nset wr_vecnames\ndc Vbus_low .75 2.55 .15\nwrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(vectors)+'\nshowmod > /workspace/'+modeldump.relative_to(ROOT).as_posix()+'\nquit\n.endc\n.end\n'
 deck=BASE/'benches'/(stem+'.spice');deck.write_text(text,encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(source.read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 rows=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,10));complete=run.returncode==0 and rows.shape==(13,10) and np.isfinite(rows).all() and 'aborted' not in log.lower()
 if data.exists():files.add(data)
 if modeldump.exists():files.add(modeldump)
 report={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,'diagnostic_mode':args.mode,'model_dump_sha256':sha(modeldump) if modeldump.exists() else None,'mismatch_seed':29,'column_reference_v':.2,'points':[dict(zip(['sweep_v',*vectors],map(float,row))) for row in rows],'scope':'Static diagnostic partition: native baseline, ideal high-gain clipped column/decoder controls, or ideal controls plus exact input-feed current copy. All native MOS instances/names/dimensions/cards retained in their original hierarchy and seed29/reset order; disconnected native outputs/replica feed have diagnostic loads. Model dumps are captured to verify identical statistical parameters before attributing differences. Ideal replacements are NOT proposed hardware or qualified extracted circuitry, and never force retained membrane STATE. Writers/selects stay ON; source swept13points. No retention, settling, model accuracy or physical/service acceptance. Compare decoded voltage to actual state, not desired write source','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),'diagnostic_mode':args.mode,'model_dump_sha256':report['model_dump_sha256'],'points':report['points']},indent=2))
 if not complete:raise RuntimeError(log[-1800:])
if __name__=='__main__':main()
