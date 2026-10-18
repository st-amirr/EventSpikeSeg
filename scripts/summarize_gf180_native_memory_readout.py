"""Audit physical memory readout, write correction and original-float transfer replays."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files={Path(__file__)}
 def verify(p):
  d=json.loads(p.read_text(encoding='utf-8'));files.add(p)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for name,h in d.get(key,{}).items():
    item=p.parent/name if key=='sha256' and not name.startswith(('artifacts/','scripts/','docs/','src/')) else ROOT/name
    assert sha(item)==h,str(item)
    files.add(item)
  return d
 prediction=verify(BASE/'results/gf180_writer_memory_reference_prediction.json')
 calibration=verify(ROOT/prediction['calibration_report'])
 assert sha(ROOT/prediction['calibration_report'])==prediction['calibration_sha256']
 circuit=[]
 for pattern in ['gf180_writer_memory_reference_corrected_*.json','gf180_regulated_current_readout_dc_*.json','gf180_writer_memory_native_readout_*.json','gf180_writer_memory_parked_readout_*.json','gf180_writer_memory_extracted_readout_*.json','gf180_writer_memory_readout_settling_*.json']:
  for p in sorted((BASE/'results').glob(pattern)):
   d=verify(p);assert d['simulation_completed']
   row={'report':p.relative_to(ROOT).as_posix()}
   if 'measurements' in d:
    m=d['measurements'];targets=d['target_levels_v']
    row.update({'target_levels_v':targets,'max_initial_write_error_v':max(abs(m[n+'_state_baseline']-v) for n,v in targets.items()),'max_hold_error_v':max(abs(m[n+'_hold_error']) for n in targets),'max_persistent_read_error_v':max(abs(m[n+'_read_error']) for n in targets)})
    if all(n+'_decoded_late' in m for n in targets):
     row.update({'decoded_levels_v':{n:m[n+'_decoded_late'] for n in targets},'max_late_target_error_v':max(abs(m[n+'_decoded_late']-v) for n,v in targets.items()),'max_reading_decode_error_v':max(abs(m[n+'_decoded_late']-m[n+'_state_reading']) for n in targets),'max_five_us_to_late_change_v':max(abs(m[n+'_decoded_late']-m[n+'_decoded_five']) for n in targets),'readout_layout_qualified':d.get('readout_layout_qualified',False)})
    if all(n+'_decoded_window_min' in m for n in targets):
     row['max_late_decode_window_v']=max(m[n+'_decoded_window_max']-m[n+'_decoded_window_min'] for n in targets)
     row['readout_cell']=d['readout_cell']
   else:row['max_DC_decode_error_v']=d['max_absolute_decode_error_v']
   circuit.append(row)
 assert len(circuit)==10
 qpath=BASE/'layout/gf180_regulated_current_readout/qualification.json';q=verify(qpath)
 assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
 aq=verify(qpath.parent/'abstract_qualification.json');assert aq['physical_ports_and_size_verified'] and aq['routing_obstructions_present']
 cq=verify(BASE/'layout/gf180_regulated_current_readout_comp4/qualification.json')
 assert cq['magic_drc_count']==cq['gds_roundtrip_drc_count']==0 and cq['lvs_unique'] and cq['gds_roundtrip_lvs_unique']
 caq=verify(BASE/'layout/gf180_regulated_current_readout_comp4/abstract_qualification.json')
 replays=[]
 for pattern in ['gf180_measured_memory_transfer_record*_src*.json','gf180_extracted_memory_transfer_record*_src*.json']:
  for p in sorted((BASE/'results').glob(pattern)):
   d=verify(p);assert d['simulation_completed'] and d['baseline_reproduced'] and not d['qat_or_quantized_reference_used']
   assert len(d['results'])==3 and len(d['state_counts'])==25 and sum(d['state_counts'].values())==30976000
   replays.append({'report':p.relative_to(ROOT).as_posix(),'record_index':d['record_index'],'scope':d['scope'],'results':[{k:r[k] for k in ['policy','mean_iou','pixel_change_fraction','prediction_sha256']} for r in d['results']]})
 assert len(replays)==2
 report={'audit_completed':True,'calibration_prediction':prediction,'circuit_cases':circuit,'physical_readout':{'cell':q['cell'],'mos_count':q['mos_count'],'native_mim_count':q['native_mim_count'],'size_um':aq['size_um'],'ports':len(aq['ports'])},'compensation_repair':{'cell':cq['cell'],'native_mim_count':cq['native_mim_count'],'size_um':caq['size_um']},'original_float_replays':replays,
 'decision':'Native idle parking removes millivolt persistent read disturbance in nominal simulations. Extracted baseline endpoint still varies with read aperture; one physical compensation repair is compared with identical late-window measurements. Keep frozen external scalar write-reference correction. Resolve settling before extracted-transfer replay and reference/phase/range-conversion integration; no pointwise trim.',
 'scope':'Schematic-readout replay only: extracted-transfer replay deliberately withheld because endpoint settling is unresolved. Measured nominal writer-memory and readout modules; their combined connection remains schematic. Replays interpolate five nominal mean-transfer levels after each update, use ideal fixed spatial scaling and ideal other PLIF operations, two heldouts from one sequence. No sampling noise, statistical cell/lane spread, source/clock history or full population schedule. Better two-record IoU does not establish preserved dataset accuracy; pixel changes remain material.25us read window is characterization, not5ms population throughput.',
 'physical_storage_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 p=BASE/'results/gf180_native_memory_readout_boundary.json';assert not p.exists(),'Preserve prior audit';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'report':str(p),'circuit_cases':len(circuit),'float_replays':len(replays),'physical_readout':report['physical_readout']},indent=2))
if __name__=='__main__':main()
