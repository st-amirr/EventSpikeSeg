"""Audit analog stored-weight/current-cell evidence without accepting full ASIC."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 patterns=['gf180_differential_stored_weight_*_srcec64df3c23a2.json']
 records=[]
 for pattern in patterns:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text())
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   assert not any(r.get(k,False) for k in ['weighted_charge_accepted','complete_PLIF_accepted','original_float_accuracy_accepted','full_chip_accepted'])
   records.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'completed':r['simulation_completed'],'settings':r['settings'],'measurements':r['measurements'],'simulator_returncode':r.get('simulator_returncode')})
 completed=sum(r['completed'] for r in records)
 assert len(records)==8 and completed==8,(len(records),completed)
 cell='gf180_precharged_weight_current_cell_fullroute_guarded';folder=BASE/'layout'/cell
 physical={}
 for name in ['qualification.json','abstract_qualification.json']:
  p=folder/name;r=json.loads(p.read_text())
  for key,values in r.items():
   if 'sha256' in key and isinstance(values,dict):
    for n,h in values.items():
     target=ROOT/n if '/' in n else folder/n
     assert digest(target)==h,str(target)
  physical[name]={'sha256':digest(p),'checks':{k:v for k,v in r.items() if 'sha256' not in k}}
 q=physical['qualification.json']['checks']
 assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and q['extraction_feedback']==''
 fine=[r for r in records if r['settings']['max_step_ns']==10];coarse=[r for r in records if r['settings']['max_step_ns']==20 and r['settings']['pf_reference_levels']=='2.690621293803461,2.7261317910513436,2.7,2.7' and r['settings']['pf_program_levels']=='2.7,2.7,2.7,2.7'];assert len(fine)==len(coarse)==1
 differences={f'eventstep_{i}':(fine[0]['measurements'][f'eventstep_{i}']-coarse[0]['measurements'][f'eventstep_{i}'])*1e6 for i in range(4)}
 calpath=BASE/'results/gf180_differential_weight_calibration_trial.json';cal=json.loads(calpath.read_text())
 for n,h in cal['input_reports'].items():assert digest(BASE/'results'/n)==h,n
 report={'fine_minus_coarse_event_increment_uv':differences,'calibration_trial':cal,'calibration_trial_sha256':digest(calpath),'stage':'differential_stored_analog_weight_and_physical_zero_event_trim','completed_diagnostics':completed,'incomplete_diagnostics':len(records)-completed,'all_provenance_hashes_match':True,'records':records,'physical_cell':physical,'findings':['Both arms independently retain analog gate voltages through real writers; weight is difference between continuously biased currents.','Nominal equal programming2.7V cancels to numerical precision under exact matching/no noise; this is not physical accuracy qualification.','Nominal programming2.699/2.701V against2.7V references produces19.9389/-19.5176uV.','Mismatchseed29 equal programs produces209.128/-466.686uV offsets; zero weight requires per-cell calibration.','Two reference trial points feed secant tuning of actual PROGRAM voltages, not arithmetic correction of physical output.','Trimmed zero programs give0.920265/0.0176325/0.931246/0.0150372uV; same reference trim with2.699/2.701V weights gives26.0699/-13.3962/26.0638/-13.4127uV. Asymmetric signed gain still needs calibration.'],'scope':'Physical8MOS/9MIM source-storage-startup macros unchanged and qualified. Paired bank/interfaces still schematic. Both signed contributions use PF current difference, NF off. Ideal reference/program supplies and offline measured tuning are diagnostic; physical calibration servo and reference programmer incomplete. Output-baseline offset remains. No sampled noise/globalPVT/RPEX/gate-leakage/retention/model-accuracy/population-service/fullPLIF/fullchip acceptance.','next':'Implement physical output-baseline capture and calibration/reference interface, characterize signed range/state dependence, then original-float weight mapping/fullPLIF/dense assembly.','weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'live_sessions':[],'audit_source_sha256':digest(Path(__file__))}
 p=BASE/'results/gf180_differential_stored_weight_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'completed':completed,'incomplete':len(records)-completed,'physical_checks':True}))
if __name__=='__main__':main()
