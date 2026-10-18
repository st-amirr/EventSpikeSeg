"""One measured loaded-reset duration repair; original donor retained, no geometry/bias fit."""
from pathlib import Path
import json,re,subprocess,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def main():
 donor=B/'results/gf180_guarded_tile_reset_internal_diagnosis_v1.json';d=json.loads(donor.read_text());assert d['completed'];e=d['reset_epochs_v'];slope=(e['110.5']['C_STATE']-e['111']['C_STATE'])/.5;step=e['116']['C_STATE']-e['109.5']['C_STATE'];cal=json.loads((B/'results/gf180_combined_v6_joint_reference_reset_calibration.json').read_text());target=.006875;width=cal['frozen_reset_width_us']+(target+step)/slope;assert 15<width<30
 src=B/'benches/gf180_guarded_tile_reset_internal_diagnosis_v1.spice';s=src.read_text();stem='gf180_guarded_tile_loaded_reset_duration_v1';rp=B/'results'/(stem+'.json');assert not rp.exists();deck=B/'benches'/(stem+'.spice');raw=rp.with_suffix('.raw')
 # Move subsequent capture/commit/read-disable30us later to keep reset ahead of writeback.
 def command(m):
  name=m[1];body=m[2];tokens=body.split();assert len(tokens)%2==0
  points=[]
  for i in range(0,len(tokens),2):
   old=float(tokens[i].removesuffix('u'));new=old
   if name=='C_RESET' and 111<old<112:new=110+width-(.1 if tokens[i+1]=='3.3' else 0)
   elif old>=119.8:new=old+30
   points.extend([format(new,'.16g')+'u',tokens[i+1]])
  return 'Vctrl_'+name+' '+name+'_CMD_DRIVER 0 PWL('+' '.join(points)+')'
 s,n=re.subn(r'(?m)^Vctrl_(\S+) \S+ 0 PWL\(([^\n]+)\)$',command,s);assert n>30;s=s.replace('.tran .02u 230u 0 10u','.tran .02u 260u 0 10u');deck.write_text(s)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);lp=rp.with_suffix('.log');lp.write_text(p.stdout+p.stderr)
 o={'completed':False,'returncode':p.returncode,'predicted_loaded_reset_width_us':width,'donor_plateau_v_per_us':slope,'donor_reset_step_v':step,'requested_base_reset_v':target,'repair_observed':False,'independent_reset_accuracy_accepted':False,'full_chip_layout_complete':False,'scope':'One measured reset-duration repair derived from prior completed failing cycle, same native GDS/5337C/biases/commands/numerics. Subsequent capture,commit and read-disable delayed30us to preserve phase order. Donor and repair share one scenario: no independent reset precision/model acceptance. No per-state correction or geometry change; duration generator still external.'}
 if raw.exists():
  h,b=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',h)[1]);names=[l.split()[1] for l in h.decode().split('Variables:\n')[1].splitlines() if l.strip()];w=np.frombuffer(b[:len(b)//(nv*8)*(nv*8)],dtype='<f8').reshape(-1,nv);t=w[:,0];np.savez_compressed(rp.with_suffix('.npz'),waveforms=w,variables=np.array(names));at=lambda n,us:float(np.interp(us*1e-6,t,w[:,names.index('v('+n.lower()+')')]));o['last_time_s']=float(t[-1]);o['completed']=bool(p.returncode==0 and abs(t[-1]-260e-6)<1e-12 and 'aborted' not in (p.stdout+p.stderr).lower())
  if o['completed']:
   actual=at('C_STATE',146)-at('C_STATE',109.5);held=at('DATA0',169);final=at('STATE70',259);o.update(actual_reset_step_v=actual,reset_error_v=actual+target,spike_before_reset_v=at('C_SPIKE',109.5),held_write_column0_v=held,final_bank_state70_v=final,writeback_error_vs_actual_column_v=final-held,max_unselected_rows_change_v=max(abs(at(f'STATE{r}{c}',259)-at(f'STATE{r}{c}',55.5)) for r in range(7) for c in range(8)));o['repair_observed']=bool(actual<0 and o['spike_before_reset_v']>3 and abs(final-held)<.06 and o['max_unselected_rows_change_v']<.03)
 o['sha256']={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),donor,src,deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))
if __name__=='__main__':main()
