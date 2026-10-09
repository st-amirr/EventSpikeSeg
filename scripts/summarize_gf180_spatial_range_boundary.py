"""Audit fixed spatial analog range exploration against unchanged float references."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic/results'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 r=json.loads(p.read_text(encoding='utf-8'))
 assert r['simulation_completed']
 for name,h in r['sha256'].items(): assert sha(ROOT/name)==h,name
 return r

def main():
 cp=next(BASE.glob('gf180_float_spatial_calibration_*_src9258811ed52c.json'));c=read(cp)
 old=read(BASE/'gf180_float_channel_calibration_dc685af8e3_src224604b6e23d.json')
 assert c['records']==old['records'] or all(a['prediction_sha256']==b['prediction_sha256'] for a,b in zip(c['records'],old['records']))
 assert c['channel_fixed_calibration_absmax']==old['channel_fixed_calibration_absmax']
 ranges=[];gain_maps={};g=np.array(c['channel_fixed_calibration_absmax']['stem']).reshape(1,-1,1,1)
 for size,value in c['stem_tile_ranges'].items():
  a=np.array(value)
  gains=np.clip(2.0**np.floor(np.log2(g/a)),1,16).astype(int)
  gain_maps[size]={'tile_gain_shape':list(gains.shape),'gains':gains.tolist(),'gain_setting_counts':{str(k):int((gains==k).sum()) for k in [1,2,4,8,16]},'stem_output_height':220,'stem_output_width':320,'edge_tiles_truncated':True}
  ranges.append({'tile_side_output_sites':int(size),'range_reference_count':a.size,'relative_gain_percentiles_0_25_50_75_95_100':np.percentile(g/a,[0,25,50,75,95,100]).tolist()})
 rows=[];forwards=8
 for pattern in ['gf180_float_spatial_precision_record*_src*.json','gf180_float_spatial_capped_gain_record*_src*.json']:
  for p in sorted(BASE.glob(pattern)):
   r=read(p);index=r['record']['validation_record_index'];assert index not in [x['validation_record_index'] for x in c['records']]
   previous=read(next(BASE.glob(f'gf180_float_fixed_precision_allocation_record{index}_src*.json')))
   assert r['input_sequence_sha256']==previous['input_sequence_sha256'] and r['target_sha256']==previous['target_sha256']
   assert r['results'][0]['prediction_sha256']==previous['results'][0]['prediction_sha256']
   for case in r['results']:
    if case['precision_policy'] in ['uniform15','stem3_other15']:
     prior=next(x for x in previous['results'] if x['precision_policy']==case['precision_policy'] and x['seed']==case['seed'])
     assert case['prediction_sha256']==prior['prediction_sha256']
   groups=[]
   for policy,sigma in dict.fromkeys((x['precision_policy'],x['other_actor_candidate_error_sigma_uv']) for x in r['results']):
    a=[x for x in r['results'] if x['precision_policy']==policy and x['other_actor_candidate_error_sigma_uv']==sigma]
    groups.append({'policy':policy,'sigma_uv':sigma,'seed_count':len(a),'mean_iou':sum(x['mean_iou'] for x in a)/len(a),'mean_changed_pixel_fraction':sum(x['pixel_change_fraction'] for x in a)/len(a),'candidate_excursions':[x['candidate_rail_excursions'] for x in a],'post_state_excursions':[x['post_state_rail_excursions'] for x in a],'prediction_equal_original':[x['prediction_sha256']==r['results'][0]['prediction_sha256'] for x in a]})
   forwards+=len(r['results']);rows.append({'report':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'record_index':index,'capped_gain': 'capped_gain' in p.name,'cases':groups})
 assert len(rows)==4
 out={'stage':'Alternative analog encoding feasibility, before complete PLIF and fullchip','calibration_report':cp.relative_to(ROOT).as_posix(),'calibration_sha256':sha(cp),'calibration_record_count':8,'evaluation_records':[8,64],'same_sequence_only':True,'model_forwards':forwards,'calibration_baselines_and_evaluation_controls_reproduce_prior_predictions':True,'range_reference_cost':ranges,'evaluations':rows,'scope':'Fixed spatial channel ranges calibrated on8 separate records, no target adaptation, float checkpoint epoch58 unchanged. Hypothetical independent15uV noise plus ideal clipping; capped gains1,2,4,8,16 are analog representation choices not model quantization. Zero-error capped controls isolate clipping. Uncapped controls not independently rail-isolated here. No physical localgain/reference/weighted-event/beta/reset/inhibition/adaptation circuitry, samplednoise, retention, PVT or5ms service qualified. Different spatial/channel gains require physically converting cross-channel competition and RMS adaptation/inhibition to common model units; do not compare raw encoded voltages. No layout area saving or dataset-wide accuracy claim.','original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False}
 manifest={'checkpoint_sha256':c['checkpoint_sha256'],'calibration_sha256':sha(cp),'actor':'stem','gain_settings_relative_to_original_channel_range':[1,2,4,8,16],'original_channel_ranges':c['channel_fixed_calibration_absmax']['stem'],'tile_candidates':gain_maps,'scope':'Provisional fixed analog scale settings, no model quantization. Physical scalar gain, references, cross-channel normalization, update and readout remain unimplemented. No array area or accuracy acceptance.'}
 mp=BASE/'gf180_spatial_gain_candidates.json';mp.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');out['gain_candidate_manifest']=mp.relative_to(ROOT).as_posix();out['gain_candidate_manifest_sha256']=sha(mp)
 p=BASE/'gf180_spatial_range_boundary.json';p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
if __name__=='__main__': main()
