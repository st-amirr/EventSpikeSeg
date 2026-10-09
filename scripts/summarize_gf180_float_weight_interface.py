"""Audit original-float sensitivity and physical weight-programming evidence."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 mp=BASE/'results/gf180_original_float_pulse_mapping_boundary.json';mapping=json.loads(mp.read_text())
 for n,h in mapping['sha256'].items():assert digest(ROOT/n)==h,n
 records=[]
 for pattern in ['gf180_float_signed_gain_record*_src60cee0bd359a.json','gf180_float_signed_gain_fine_record*_src1980484eec6d.json']:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text());assert r['simulation_completed'] and r['actor_count']==25 and r['full_frame_shape']==[440,640] and not r['qat_or_quantized_reference_used']
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   records.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'record':r['record'],'input_sequence_sha256':r['input_sequence_sha256'],'target_sha256':r['target_sha256'],'results':r['results']})
 assert len(records)==4
 for index in [0,1]:
  matching=[r for r in records if r['record']['validation_record_index']==index];assert len(matching)==2 and matching[0]['input_sequence_sha256']==matching[1]['input_sequence_sha256'] and matching[0]['target_sha256']==matching[1]['target_sha256'] and matching[0]['results'][0]['prediction_sha256']==matching[1]['results'][0]['prediction_sha256']
 aggregate=[]
 for delta in [0,.0001,.001,.003,.01,.05,.15]:
  cases=[row for r in records for row in r['results'] if row['residual_signed_gain_delta']==delta];byrec={}
  for r in records:
   for row in r['results']:
    if row['residual_signed_gain_delta']==delta:byrec[r['record']['validation_record_index']]=row
  assert len(byrec)==2
  aggregate.append({'residual_error_per_polarity':delta,'mean_of_two_frame_iou':sum(r['mean_iou'] for r in byrec.values())/2,'mean_pixel_change_fraction':sum(r['pixel_change_fraction'] for r in byrec.values())/2})
 physical=[]
 for pattern in ['gf180_source_amplitude_sequence_*_src870d5d861355.json','gf180_source_amplitude_guard_*_srcf8665a68547a.json']:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text());assert r['simulation_completed']
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   physical.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'settings':r['settings'],'measurements':r['measurements']})
 assert len(physical)==3
 report={'stage':'original_float_precision_and_weight_interface_method_change','mapping_report_sha256':digest(mp),'weight_coverage':mapping['aggregate'],'software_replays':records,'aggregate_sensitivity':aggregate,'physical_amplitude_programming':physical,'all_provenance_hashes_match':True,'coarse_and_fine_baseline_inputs_and_predictions_match':True,'next':'prebiased_calibrated_weight_current_cells_or_ranges_with_shared_charge_accumulation_and_physical_offset_baseline_cancellation','scope':'Original best-epoch58 float checkpoint reexported with actual repository src and arrays identical to historical float archive. Fixed strong-current duration-only point lacks coverage for many coefficients at illustrative patch-derived voltage scales; minimum tested20ns is not physical minimum proof. Two full frames test deterministic coherent signed gain error, not physical device noise/model accuracy on validation set or sufficient event-weight precision. No inferred acceptance threshold. A reprogrammed shared gate takes substantial settling: matched twelve-us spacing experiments give468.127uV with1.5us guard vs19000.6uV with6us guard for secondPF2.55 event; longer guard is not5ms population service proof. Next investigate always-biased weight-current cells or ranges to amortize programming at setup; their memory/selection/noise/calibration/area/throughput remain unimplemented. No ideal inverse/calibration applied to physical state, no QAT/digital-compute fallback.','live_sessions':[],'weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'audit_source_sha256':digest(Path(__file__))}
 p=BASE/'results/gf180_float_weight_interface_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'aggregate_sensitivity':aggregate,'physical_amplitude_reports':len(physical)},indent=2))
if __name__=='__main__':main()
