"""Compare native pulse charge against original-float effective weights."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ck=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';assert digest(ck)==EXPECTED
 ref=BASE/'model_reference';fresh=ref/'gf180_source_mapping_float';metadata=json.loads((fresh/'eventspikeseg140k_float_reference.json').read_text());assert metadata['checkpoint_sha256']==EXPECTED and metadata['epoch']==metadata['best_epoch']==58 and metadata['is_best']
 a=np.load(ref/'eventspikeseg140k_float_parameters.npz');b=np.load(fresh/'eventspikeseg140k_float_parameters.npz');assert set(a.files)==set(b.files) and all(np.array_equal(a[k],b[k]) for k in a.files)
 tp=ref/'float_patch_trace_all.json';trace=json.loads(tp.read_text());assert trace['checkpoint_sha256']==EXPECTED and trace['float_path'] and not trace['qat_or_quantized_reference_used'] and len(trace['sampled_stages'])==25
 physical=[];source_paths=[ck,tp,ref/trace['trace_archive'],fresh/'eventspikeseg140k_float_reference.json',fresh/'eventspikeseg140k_float_parameters.npz',ref/'eventspikeseg140k_float_parameters.npz',ROOT/'scripts/export_sky130_float_reference.py',ROOT/'src/eventspikeseg/model.py',ROOT/'src/eventspikeseg/model_components.py',ROOT/'src/eventspikeseg/asic/export.py',Path(__file__)]
 for p in sorted((BASE/'results').glob('gf180_source_duration_mapping_*_srcf398d17cbc45.json')):
  r=json.loads(p.read_text());assert r['simulation_completed'];s=r['settings'];assert s['width_us']==.02 and s['pf_gate_v']==2.55 and s['nf_gate_v']==.6 and s['mismatch_seed']==29
  for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
  physical.append({'report':p.relative_to(ROOT).as_posix(),'settings':s,'measurements':r['measurements'],'sha256':digest(p)});source_paths.append(p)
 assert len(physical)==2
 floor={r['settings']['sequence']:abs(r['measurements']['signal_delta']) for r in physical}
 rows=[];counts=[]
 for swing in [.1,.3,.6]:
  total=below=0
  for tr in trace['sampled_stages']:
   name=tr['name'];w=b['weight__'+name.replace('.','__')].astype(np.float64);stats=tr['candidate_before_threshold_and_reset'];maximum=max(abs(stats['min']),abs(stats['max']));assert maximum>0
   scale=swing/maximum;required=np.abs(w)*scale;minimum=np.where(w>=0,floor['p'],floor['n']);bad=int(np.count_nonzero(required<minimum));total+=w.size;below+=bad
   rows.append({'actor':name,'state_headroom_v':swing,'weight_count':int(w.size),'volts_per_model_unit':scale,'observed_patch_candidate_absmax':maximum,'required_abs_contribution_uv_p1_p50_p99_max':(np.percentile(required,[1,50,99,100])*1e6).tolist(),'fraction_below_smallest_tested_nonzero_pulse':bad/w.size,'abs_weight_p1_p50_p99_max':np.percentile(np.abs(w),[1,50,99,100]).tolist(),'hypothetical_linear_duration_ns_p1_p50_p99':np.percentile(required/np.where(w>=0,.0190005,.0271669)*1000,[1,50,99]).tolist()})
  counts.append({'state_headroom_v':swing,'neuron_weight_count':total,'below_smallest_tested_pulse_count':below,'below_smallest_tested_pulse_fraction':below/total})
 assert total==143728 and b['weight__head_synapse'].size==96 and total+96==metadata['inference_synaptic_weight_count']
 report={'stage':'original_float_weight_vs_physical_pulse_mapping_gap','checkpoint_sha256':EXPECTED,'checkpoint_epoch':58,'qat_or_quantized_reference_used':False,'fresh_export_uses_current_repository_src':True,'fresh_export_arrays_identical_to_historical_reference':True,'source_environment':'PYTHONPATH=/workspace/src; bundled Docker-installed package must not take precedence','physical_minimum_tested_pulse_us':.02,'positive_minimum_tested_increment_uv':floor['p']*1e6,'negative_minimum_tested_increment_abs_uv':floor['n']*1e6,'physical_reports':physical,'actor_rows':rows,'aggregate':counts,'unmapped_readout_weight_count':96,'scope':'Static coefficient coverage screen using current-source native extracted transient at a single tested bias/seed and25 actor candidate maxima from three historical64x64 patches. Headroom/actor voltage scales are ideal illustrative assumptions from those patches, not a implemented encoder or full-frame bounds. Smallest tested pulse is not a physical minimum proof or achievable accuracy guarantee. Hypothetical linear durations ignore edge offsets and nonlinear measured transfer; not a calibrated implementation. Coefficient frequencies are not spike/event frequencies or validation accuracy. No weights clipped, deleted, quantized or applied to inference. No physical timing/weight DAC/current-range selection, zero-packet calibration or source/pair layout assembly.143728 neuron weights plus96 analog readout weights=143824. Strong fixed-bias duration-only operating point has major coefficient-coverage gap; explore calibrated current ranges/amplitude-controlled fixed-window contributions without QAT/digital-compute fallback.','next':'amplitude_or_calibrated_current_range_with_physical_event_offset_and_baseline_cancellation_then_original_float_error_replay','live_sessions':[],'weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in source_paths}}
 p=BASE/'results/gf180_original_float_pulse_mapping_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'aggregate':counts,'smallest_tested_increments_uv':{k:v*1e6 for k,v in floor.items()}},indent=2))
if __name__=='__main__':main()
