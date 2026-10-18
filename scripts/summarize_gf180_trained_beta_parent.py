"""Compare a physically targeted parent against its unchanged trained beta."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';R=BASE/'results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_state_update_detailstem_ch3_pad06_v2';out=R/'gf180_trained_beta_detailstem_ch3_boundary.json';assert not out.exists();qp=BASE/'layout'/cell/'qualification.json';q=json.loads(qp.read_text());target=q['target_float_channel'];beta=target['trained_beta'];files={Path(__file__),qp};cases=[]
 for mode,seed in [('baseline',0),('check',0),('check',29)]:
  rp=R/f'{cell}_complete_cycle_{mode}_seed{seed}_src69ba06d255d6.json';d=json.loads(rp.read_text());assert d['simulation_completed'] and d['parent_cell']==cell;files.add(rp)
  for n,h in d['sha256'].items():assert sha(ROOT/n)==h,n
  w=np.loadtxt(rp.with_suffix('.dat'),skiprows=1);assert w.shape[1]==9 and np.isfinite(w).all() and abs(w[-1,0]-315e-6)<1e-12
  curves=[]
  for k in range(3):
   row=[]
   for i,tag in enumerate(['low','mid','high']):
    v={label:float(np.interp((100*k+t)*1e-6,w[:,0],w[:,1+2*i])) for label,t in [('before',19),('sharing',20.45),('after',21.5),('rearmed',31.5),('late',99.5)]}
    for label,value in v.items():assert abs(value-d['measurements'][f'{tag}_c{k}_state_{label}'])<6e-6
    row.append(v)
   curves.append(row)
  first=curves[0];x=[row['before'] for row in first];y=[row['rearmed'] for row in first];slope=(y[2]-y[0])/(x[2]-x[0]);err=[y[i]-1.65-beta*(x[i]-1.65) for i in range(3)]
  cumulative=[curves[k][i]['late']-1.65-beta**(k+1)*(x[i]-1.65) for k in range(3) for i in range(3)]
  cases.append({'report':rp.relative_to(ROOT).as_posix(),'mode':mode,'seed':seed,'transfer_before_v':x,'transfer_after_full_commit_v':y,'measured_slope':slope,'slope_error_vs_trained_beta':slope-beta,'frozen_aux_reference_v':d['frozen_auxiliary_reference_v'],'first_cycle_residual_vs_trained_beta_v':err,'worst_three_cycle_residual_vs_trained_beta_v':max(map(abs,cumulative)),'primary_measures_verified':True})
 result={'audit_completed':True,'cell':cell,'target':target,'cases':cases,'conclusion':'Representative actual trained coefficient targeted with legal physical overlap sizing. Compare against trained beta rather than fitting each check. Nominal and one mismatch seed provide measured curves for limited original-model replay; no tolerance or full channel coverage is accepted.','scope':'Actual capacitively extracted parent,3accelerated100us cycles,external refs/data/native clocks; no native noise/dielectric leakage/PVT/yield,full5ms/service/model/completePLIF acceptance.','acceptance':{'learned_beta_coverage':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'target':target,'cases':cases},indent=2))
if __name__=='__main__':main()
