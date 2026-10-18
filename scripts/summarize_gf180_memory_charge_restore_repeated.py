"""Validate repeated native restore histories and first-cycle matching to frozen donors."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_memory_charge_restore_repeated_boundary.json';assert not out.exists();files={Path(__file__)};cases=[]
 for seed in [0,29]:
  p=BASE/f'gf180_memory_charge_restore_repeated3_seed{seed}_src08fb15506b4d.json';d=json.loads(p.read_text());files.add(p);assert d['simulation_completed'] and d['simulator_returncode']==0 and len(d['measurements'])==54
  for n,h in d['sha256'].items():
   f=ROOT/n;assert sha(f)==h,n;files.add(f)
  donor=BASE/f'gf180_memory_charge_restore_corrected_independent_on_seed{seed}_src529813f902c1.json';prior=json.loads(donor.read_text());m=prior['measurements'];values=d['measurements'];errors=[]
  for tag in ['low','mid','high']:
   for label,prior_label in [('held','state_held'),('restored','state_restored'),('prerelease','state_restoring'),('baseline','out_held'),('read','out_read_late'),('restore_output','restore_out_read_late')]:
    errors.append(abs(values[f'{tag}_c0_{label}']-m[f'{tag}_{prior_label}']))
  assert max(errors)<1e-5
  rows=np.loadtxt(p.with_suffix('.dat'),skiprows=1);assert rows.shape[1]==16 and np.isfinite(rows).all() and rows[-1,0]>=315e-6-1e-12
  histories={}
  for i,tag in enumerate(['low','mid','high']):
   col=1+5*i;at=lambda t:float(np.interp(t,rows[:,0],rows[:,col]));initial=at(59e-6);hist=[]
   for k in range(3):
    held=at((100*k+59)*1e-6);restored=at((100*k+114)*1e-6)
    assert abs(restored-values[f'{tag}_c{k}_restored'])<1e-5
    hist.append({'cycle':k,'held_v':held,'restored_v':restored,'incremental_error_v':restored-held,'cumulative_change_v':restored-initial})
   histories[tag]=hist
  cases.append({'report':p.relative_to(ROOT).as_posix(),'seed':seed,'cycles':3,'maximum_first_cycle_difference_v':max(errors),'histories':histories,'worst_cumulative_drift_v':max(abs(r['cumulative_change_v']) for h in histories.values() for r in h)})
 report={'status':'completed_two_native_three_cycle_comparisons','cases':cases,'conclusion':'First cycles reproduce frozen donor observations at printed precision. Drift persists per access: nominal worst10.83mV and selected native mismatch worst21.50mV after three cycles. One-cycle restore fitting is not drift acceptance.','next_action':'Original-float replay of measured nominal held-to-restored transfer, then disconnect/release error diagnosis or native baseline/offset correction according to task sensitivity. No additional ratio fitting without mechanism evidence.','scope':'Accelerated100us access period,40us initial/about49us subsequent holds, three independent lanes per seed. No5ms retention,no random sampled noise or population service proof. External references/timing, schematic parent/fractionalMIM. Same seed/hierarchy as each own donor, not prior-current-reader population.','acceptance':{'readout':False,'original_float_accuracy':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'worst_cumulative_drift_v':[c['worst_cumulative_drift_v'] for c in cases]}))
if __name__=='__main__':main()
