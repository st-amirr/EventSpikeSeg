"""Audit initial native charge-read evidence without treating decoding arithmetic as circuitry."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_memory_charge_read_boundary.json';assert not out.exists()
 files={Path(__file__)};cases={};data={}
 for mode,seed in [('on',0),('off',0),('on',29)]:
  name=f'{mode}_seed{seed}';p=BASE/f'gf180_memory_charge_read_{name}_src5aba4580d681.json';d=json.loads(p.read_text());files.add(p)
  assert d['simulation_completed'] and len(d['measurements'])==66 and d['simulator_returncode']==0
  for n,h in d['sha256'].items():
   f=ROOT/n;assert sha(f)==h,n;files.add(f)
  waveform=next(ROOT/n for n in d['sha256'] if n.endswith('.dat'));rows=np.loadtxt(waveform,skiprows=1)
  assert rows.shape[1]==13 and np.isfinite(rows).all() and 0<=rows[0,0]<=1e-8 and rows[-1,0]>=90e-6-1e-12
  assert np.all(np.diff(rows[:,0])>=0)
  data[name]=d;cases[name]={'report':p.relative_to(ROOT).as_posix(),'summary':d['summary'],'finite_waveform_rows':len(rows)}
 m=data['on_seed0']['measurements'];increment=lambda mm,t:mm[t+'_out_read_late']-mm[t+'_out_held']
 gain=-(m['high_state_held']-m['low_state_held'])/(increment(m,'high')-increment(m,'low'));offset=m['low_state_held']+gain*increment(m,'low')
 absolute_offset=m['low_state_held']+gain*m['low_out_read_late']
 estimates={}
 for name in ['on_seed0','on_seed29']:
  mm=data[name]['measurements'];estimates[name]={t:{'absolute_frozen_fit_error_v':absolute_offset-gain*mm[t+'_out_read_late']-mm[t+'_state_held'],'increment_frozen_fit_error_v':offset-gain*increment(mm,t)-mm[t+'_state_held']} for t in ['low','mid','high']}
 failed=BASE/'gf180_memory_charge_restore_on_seed0_srcd6256a5611c2.json';f=json.loads(failed.read_text());assert not f['simulation_completed'] and f['simulator_returncode']==124 and not f['measurements'];files.add(failed)
 for n,h in f['sha256'].items():
  path=ROOT/n;assert sha(path)==h,n;files.add(path)
 report={'status':'completed_charge_read_feasibility_only','cases':cases,'frozen_nominal_endpoint_fit':{'increment_gain':gain,'increment_intercept_v':offset,'postprocessing_estimates_not_hardware':estimates,'precision':'From six-digit simulator measures; endpoint errors fitted by construction. Midpoint independent of two endpoint fit. Different lanes, not one-lane multi-level sweep.'},'failed_restore':{'report':failed.relative_to(ROOT).as_posix(),'status':'120s_timeout_no_final_measures','summary_defaults_are_not_measured_zero_error':True},'conclusion':'Native charge transfer avoids resident/replica NF matching but destroys state. Absolute mapping has up to88.06mV conditional seed29 error; baseline-referenced mapping is within0.838mV at three tested points. Baseline subtraction here is analysis only: physical baseline capture and native restore must be demonstrated. Resistor restore timed out; one capacitive autozero restore repair is in progress.','scope':'40us hold, native schematic connection of qualified extracted children, no read/restore layout, sampled noise,5ms retention/model accuracy/population service/yield acceptance. Do not compare seed29 draws with previous current reader hierarchy.','acceptance':{'readout':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'conditional_estimates':estimates},indent=2))
if __name__=='__main__':main()
