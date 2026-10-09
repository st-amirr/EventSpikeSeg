"""Audit physical output-capture progression and matched numerical controls."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized_deck(v,remove_dummy=False):
 paths=[ROOT/n for n in v['sha256'] if '/benches/' in n and n.endswith('.spice')];assert len(paths)==1
 text=paths[0].read_text()
 if remove_dummy:text=re.sub(r'(?m)^Xcapture_dummy_.*\n','',text)
 return re.sub(r'(?m)^tran .*$', 'TRAN_NORMALIZED',text)
def main():
 reports=[];rows=[];controls=[];convergence=[]
 for p in sorted(BASE.glob('gf180_sampler_reader_capture_window*.json')):
  v=json.loads(p.read_text())
  for n,x in v['sha256'].items():
   if digest(ROOT/n)!=x:raise ValueError('Changed evidence: '+n)
  reports.append((p,v));rows.append({'report':p.relative_to(ROOT).as_posix(),'report_sha256':digest(p),'settings':v['settings'],'simulation_completed':v['simulation_completed'],'held_time_s':v['held_measurement_time_s'],'cases':v['cases']})
 for p,v in reports:
  if not v['simulation_completed']:continue
  if v['settings'].get('capture_dummy') and not v['settings'].get('combined_capture'):
   desired=dict(v['settings']);desired['capture_dummy']=False
   for q,w in reports:
    if w['settings']!=desired or not w['simulation_completed'] or digest(ROOT/v['source_snapshot'])!=digest(ROOT/w['source_snapshot']):continue
    if normalized_deck(v,True)!=normalized_deck(w,True):raise ValueError('Dummy decks differ beyond dummy')
    controls.append({'dummy':p.name,'baseline':q.name,'exact_decks_match_except_dummy':True,'baseline_capture_errors_mv':[c['capture_preservation_error_mv'] for c in w['cases']],'dummy_capture_errors_mv':[c['capture_preservation_error_mv'] for c in v['cases']]})
  if v['settings'].get('max_step_ns')==10:
   desired=dict(v['settings']);desired['max_step_ns']=20
   for q,w in reports:
    if w['settings']!=desired or not w['simulation_completed'] or digest(ROOT/v['source_snapshot'])!=digest(ROOT/w['source_snapshot']):continue
    if normalized_deck(v)!=normalized_deck(w):raise ValueError('Convergence decks differ beyond tran')
    convergence.append({'fine':p.name,'coarse':q.name,'exact_deck_match_except_tran':True,'max_observed_endpoint_difference_uv':max(abs(c['measurements_v'][key]-d['measurements_v'][key])*1e6 for c,d in zip(v['cases'],w['cases']) for key in c['measurements_v']),'max_captured_held_difference_uv':max(abs(c['measurements_v']['captured_held']-d['measurements_v']['captured_held'])*1e6 for c,d in zip(v['cases'],w['cases']))})
 output={'report_count':len(rows),'completed_count':sum(r['simulation_completed'] for r in rows),'reports':rows,'dummy_controls':controls,'convergence':convergence,'capture_accuracy_accepted':False,'inverse_restore_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'scope':'All qualified component/model/deck/log/snapshot hashes checked.50us nominal diagnostics, including isolation and incomplete solver cases. Physical clock and capture macro evidence does not establish combined reader-capture-driver interconnect layout, noise, mismatch/PVT,5ms hold or population service and model accuracy. No numerical offset correction applied.'}
 p=BASE/'gf180_reader_capture_boundary.json';p.write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps({'report':str(p),'reports':len(rows),'completed':output['completed_count'],'dummy_controls':controls,'convergence':convergence},indent=2))
if __name__=='__main__':main()
