"""Audit switched and active-charge read diagnostics; no storage acceptance."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic/results'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[]; reports=[]
 for pattern in ['gf180_sampler_switched_read_window*.json','gf180_sampler_active_reader_window*.json']:
  for p in sorted(BASE.glob(pattern)):
   v=json.loads(p.read_text())
   for name,expected in v['sha256'].items():
    if digest(ROOT/name)!=expected:raise ValueError('Changed evidence: '+name)
   reports.append((p,v));rows.append({'report':p.relative_to(ROOT).as_posix(),'report_sha256':digest(p),'settings':v['settings'],'simulation_completed':v['simulation_completed'],'held_time_s':v['held_measurement_time_s'],'five_ms_hold_completed':v['five_ms_hold_completed'],'cases':v['cases']})
 comparison=[]
 for p,v in reports:
  if not v['settings'].get('reset_dummy') or not v['simulation_completed']:continue
  settings=dict(v['settings']);settings['reset_dummy']=False
  for q,w in reports:
   if w['settings']!=settings or digest(ROOT/w['source_snapshot'])!=digest(ROOT/v['source_snapshot']) or not w['simulation_completed']:continue
   def deck(rep):
    d=[ROOT/n for n in rep['sha256'] if '/benches/' in n and n.endswith('.spice')]
    assert len(d)==1
    return re.sub(r'(?m)^Xresetdummy_.*\n','',d[0].read_text())
   if deck(v)!=deck(w):raise ValueError('Reset comparison differs beyond dummy')
   def endpoints(rep):
    low,mid,high=rep['cases']
    slope=(low['output_after_transfer_mv']-high['output_after_transfer_mv'])/1000/(high['measurements_v']['stored_before_read']-low['measurements_v']['stored_before_read'])
    return {'signed_span_gain':slope,'zero_output_mv':mid['output_after_transfer_mv'],'zero_output_referred_mv_diagnostic_only':mid['output_after_transfer_mv']/slope}
   comparison.append({'dummy_report':p.name,'baseline_report':q.name,'same_snapshot':True,'exact_decks_match_except_dummy':True,'baseline':endpoints(w),'dummy':endpoints(v)})
 output={'reports':rows,'reset_dummy_comparisons':comparison,'selected_next_layout_candidate':'corrected active charge reader with physical reset dummy; provisional, restore and accuracy unqualified','storage_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'scope':'50us nominal deterministic schematic assemblies of extracted components. Active read destroys state; an explicit physically calibrated inverse/restore cycle remains necessary. No ideal subtraction applied. Secant gain and referred pedestal are metrology, not implemented compensation or neural accuracy.'}
 p=BASE/'gf180_sampler_read_access_boundary.json';p.write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps({'report':str(p),'reports':len(rows),'reset_dummy_comparisons':comparison},indent=2))
if __name__=='__main__':main()
