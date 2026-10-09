"""Preserve the precision-amplifier experiment including incomplete transients."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic/results'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[]
 for p in sorted(BASE.glob('gf180_capacitive_precision_preamp_*_src53c826e6ee5b.json')):
  r=json.loads(p.read_text(encoding='utf-8'))
  for name,h in r['sha256'].items(): assert sha(ROOT/name)==h,name
  row={'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'settings':r['settings'],'completed':r['simulation_completed'],'returncode':r['simulator_returncode'],'measurements':r['measurements']}
  if r['simulation_completed'] and r['settings']['mode']=='noise':
   spec=np.loadtxt(ROOT/r['spectrum'],skiprows=1); ac=np.loadtxt(ROOT/r['ac_transfer'],skiprows=1)
   gain=float(np.interp(1000,ac[:,0],np.hypot(ac[:,1],ac[:,2])))
   row['actual_ac_gain_at_1khz']=gain
   row['ideal_boxcar_conditional_input_proxy_uv']={str(us):float(np.sqrt(np.trapezoid(spec[:,1]**2*np.sinc(spec[:,0]*us*1e-6)**2,spec[:,0]))/gain*1e6) for us in [4,20]}
   row['stationary_op_not_matched_to_post_reset_transient']=True
  rows.append(row)
 assert len(rows)==6 and sum(r['completed'] for r in rows)==4
 report={'stage':'Analog precision feasibility; preamplifier not selected','cases':rows,'finding':'Four stationary noise diagnostics completed; two reset-and-settling diagnostics ended at bounded timeout124 with no completed measurements. Neither timeout proves physical circuit failure. Noise evaluated around about1.14V output, not demonstrated reset-released operating point. Conditional gain-referred ideal boxcar proxies exclude reset/sample/storage/upstream noise and are not achieved membrane precision. Largest parallel pair draws2.628mA; dense area, service and fullchain unqualified. Do not continue scaling parallel OTAs solely from stationary proxy.','next_method':'Evaluate independently calibrated fixed spatial ranges for sensitive stem stage before committing further precision circuit area. Preserve checkpoint and float semantics. Local physical gain/reference/threshold/reset/adaptation interfaces remain required.','original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False}
 dest=BASE/'gf180_preamp_method_boundary.json';dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'report':str(dest),'completed':4,'bounded_incomplete':2,'cases':[{k:v for k,v in x.items() if k in ['settings','actual_ac_gain_at_1khz','ideal_boxcar_conditional_input_proxy_uv']} for x in rows]},indent=2))
if __name__=='__main__': main()
