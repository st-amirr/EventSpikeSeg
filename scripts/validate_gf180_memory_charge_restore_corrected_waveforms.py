"""Validate primary corrected-case waveforms; preserve earlier donor-waveform selection error."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_memory_charge_restore_corrected_waveform_validation.json';assert not out.exists()
 files={Path(__file__)};cases=[];settings=[]
 for levels,seed in [('endpoints',0),('independent',0),('independent',29)]:
  p=BASE/f'gf180_memory_charge_restore_corrected_{levels}_on_seed{seed}_src529813f902c1.json';d=json.loads(p.read_text());files.add(p)
  assert d['simulation_completed'] and d['simulator_returncode']==0 and len(d['measurements'])==111
  for n,h in d['sha256'].items():
   f=ROOT/n;assert sha(f)==h,n;files.add(f)
  waveform=p.with_suffix('.dat');assert waveform.relative_to(ROOT).as_posix() in d['sha256'];rows=np.loadtxt(waveform,skiprows=1)
  assert rows.shape[1]==16 and np.isfinite(rows).all() and 0<=rows[0,0]<=1e-8 and rows[-1,0]>=115e-6-1e-12 and np.all(np.diff(rows[:,0])>=0)
  settings.append((d['frozen_restore_reference_v'],d['coupling_unit_count'],tuple(d['fractional_plate_um'])))
  m=d['measurements'];error={t:m[t+'_state_restored']-m[t+'_state_held'] for t in ['low','mid','high']}
  intervals={}
  for i,tag in enumerate(['low','mid','high']):
   def at(t,col):return float(np.interp(t,rows[:,0],rows[:,col]))
   state_col=1+5*i;out_col=state_col+1;restore_col=state_col+4
   select=(rows[:,0]>=80e-6)&(rows[:,0]<=84.5e-6)
   assert abs((at(114e-6,state_col)-at(59e-6,state_col))-error[tag])<1e-5
   intervals[tag]={'late_read_output_window_v':float(np.ptp(rows[select,out_col])),'restore_output_change_after_read_disconnect_v':at(109.5e-6,restore_col)-at(84.5e-6,restore_col),'state_release_error_v':at(114e-6,state_col)-at(109.5e-6,state_col),'measured_after_restore_error_v':at(114e-6,state_col)-at(59e-6,state_col)}
  cases.append({'report':p.relative_to(ROOT).as_posix(),'levels':levels,'seed':seed,'restore_error_v':error,'worst_abs_restore_error_v':max(map(abs,error.values())),'waveform':waveform.relative_to(ROOT).as_posix(),'waveform_intervals':intervals})
 assert settings[0]==settings[1]==settings[2]
 original=json.loads((BASE/'gf180_memory_charge_restore_boundary.json').read_text());worst=max(map(abs,original['error_v'].values()))
 report={'status':'primary_case_waveforms_validated','superseded_waveform_audit':'artifacts/analog_asic/results/gf180_memory_charge_restore_corrected_boundary.json','prior_audit_error':'Prior audit selected first provenance .dat, which was the donor waveform, for all three cases. Its measure-derived errors were correct; its waveform intervals were invalid. This report selects each primary case .dat explicitly.','frozen_reference_v':settings[0][0],'input_MIM_equivalent_units':settings[0][1],'fractional_native_plate_um':settings[0][2],'cases':cases,'original_worst_error_v':worst,'conclusion':'One common native capacitor/reference correction reduces nominal endpoint worst restore error92.075mV to8.670mV. Frozen independent nominal levels worst3.630mV; independent seed29 worst7.200mV. These are physical restored-minus-held measurements, not numerical state correction. Residual release and transfer errors, sampled noise and repeated-bin drift remain.','next_action':'Measure repeated native read/restore drift and replay measured state transfer in the original-float model before further calibration or combined layout. Use waveform intervals to distinguish disconnect/release errors; do not assume a fitted line proves circuit accuracy.','scope':'Only40us hold, three independent lanes, one cycle per case, external references/clocks/bias. Fractional MIM is native schematic geometry, not yet physical layout qualified. Qualified extracted child modules do not qualify parent. Seed29 hierarchy differs from earlier current reader. No yield/noise/leakage/5ms retention/full-neuron/model/service/full-chip acceptance.','acceptance':{'readout':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'cases':cases},indent=2))
if __name__=='__main__':main()
