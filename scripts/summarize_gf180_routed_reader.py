"""Audit combined routed reader and preserve incomplete capture diagnostics."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[];captures=[]
 for p in sorted((BASE/'results').glob('gf180_sampler_reader_capture_window*.json')):
  v=json.loads(p.read_text())
  for n,x in v['sha256'].items():
   if digest(ROOT/n)!=x:raise ValueError('Changed capture evidence: '+n)
  captures.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'simulation_completed':v['simulation_completed'],'settings':v['settings']})
 for suffix,flags in [('',{'shielded_reader':False,'vertical_guards':False}),('_shielded',{'shielded_reader':True,'vertical_guards':False}),('_guarded',{'shielded_reader':False,'vertical_guards':True})]:
  cell='gf180_active_charge_reader_fullroute'+suffix;directory=BASE/'layout'/cell;q=json.loads((directory/'qualification.json').read_text())
  if q['magic_drc_count'] or q['gds_roundtrip_drc_count'] or not q['gds_roundtrip_lvs_unique']:raise ValueError('Physical reader unqualified')
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,x in q[key].items():
    p=directory/n if key=='sha256' else ROOT/n
    if digest(p)!=x:raise ValueError('Changed physical evidence')
  candidates=[]
  for p in (BASE/'results').glob('gf180_sampler_routed_reader_window*src1db4c1a11051.json'):
   v=json.loads(p.read_text())
   if all(v['settings'].get(k)==x for k,x in flags.items()):candidates.append((p,v))
  assert len(candidates)==1
  p,v=candidates[0]
  for n,x in v['sha256'].items():
   if digest(ROOT/n)!=x:raise ValueError('Changed simulation evidence')
  assert v['simulation_completed']
  text=(directory/(cell+'_cap.spice')).read_text();body=text[text.index('.subckt '+cell+' '):]
  capacitors={}
  for a,b,value in re.findall(r'(?m)^C\S+\s+(\S+)\s+(\S+)\s+([-+0-9.eE]+[fp]?)',body):
   if 'SUM' in [a,b] and any(n in [a,b] for n in ['READ','READB','RESET','RESETB']):
    suffix_unit=value[-1] if value[-1] in 'fp' else '';value_num=float(value[:-1] if suffix_unit else value)*{'':1,'f':1e-15,'p':1e-12}[suffix_unit]
    capacitors['-'.join(sorted([a,b]))]=value_num*1e15
  x1,y1,x2,y2=q['bbox_um'];lo,mid,hi=v['cases']
  rows.append({'cell':cell,'qualification_sha256':digest(directory/'qualification.json'),'report':p.relative_to(ROOT).as_posix(),'report_sha256':digest(p),'source_sha256':digest(ROOT/v['source_snapshot']),'physical_drc_gds_lvs_pass':True,'bbox_area_um2':(x2-x1)*(y2-y1),'parent_layout_sum_clock_caps_ff':capacitors,'zero_output_mv':mid['output_after_transfer_mv'],'signed_output_mv':[lo['output_after_transfer_mv'],hi['output_after_transfer_mv']],'signed_span_gain':(lo['output_after_transfer_mv']-hi['output_after_transfer_mv'])/1000/(hi['measurements_v']['stored_before_read']-lo['measurements_v']['stored_before_read']),'read_disconnect_output_change_mv':[1000*(c['measurements_v']['read_after_read']-c['measurements_v']['read_during_read']) for c in v['cases']]})
 assert len({r['source_sha256'] for r in rows})==1
 output={'reader_rows':rows,'same_simulation_executable':True,'capture_diagnostics':captures,'selected_next_candidate':'guarded reader; output capture and restore unresolved','physical_storage_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'scope':'Three independently qualified actual routed readers,50us typical27C nominal simulations. Guard spacing and capacitance loads differ, so no unique suppression causality or precision claim. Parent clock-cap table excludes child layout/device capacitances. Capture failures preserved; no capture or inverse restore accepted. No model accuracy or population5ms qualification.'}
 p=BASE/'results/gf180_routed_reader_boundary.json';p.write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps({'report':str(p),'reader_rows':rows,'capture_diagnostics':len(captures)},indent=2))
if __name__=='__main__':main()
