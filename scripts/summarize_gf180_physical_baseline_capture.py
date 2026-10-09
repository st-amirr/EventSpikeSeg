"""Audit analog stored-weight/current-cell evidence without accepting full ASIC."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 patterns=['gf180_physical_baseline_capture_*_src*.json','gf180_routed_baseline_capture_*_srcf5630fa83553.json']
 records=[]
 for pattern in patterns:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text())
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   assert not any(r.get(k,False) for k in ['weighted_charge_accepted','complete_PLIF_accepted','original_float_accuracy_accepted','full_chip_accepted'])
   records.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'completed':r['simulation_completed'],'settings':r['settings'],'measurements':r['measurements'],'simulator_returncode':r.get('simulator_returncode')})
 completed=sum(r['completed'] for r in records)
 assert len(records)==9 and completed==9,(len(records),completed)
 cell='gf180_output_baseline_capture_fullroute_guarded';folder=BASE/'layout'/cell
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
 trimpath=BASE/'results/gf180_baseline_reference_trim_trial.json';trim=json.loads(trimpath.read_text())
 for n,h in trim['input_report_sha256'].items():assert digest(BASE/'results'/n)==h,n
 report={'baseline_trim_trial':trim,'baseline_trim_trial_sha256':digest(trimpath),'stage':'physical_output_baseline_capture_layout_and_transfer','completed_diagnostics':completed,'incomplete_diagnostics':len(records)-completed,'all_provenance_hashes_match':True,'records':records,'physical_cell':physical,'findings':['Physical MIM coupling with actual clamp switch captures initial OUT baseline; physical captured signal is floating read_r minus read_w, no arithmetic baseline subtraction.','Schematic single-bank no-event capture residual30.8565uV versus initial amplifier difference-1346.08uV; four banks reduce residual5.6082uV with added load/area.','Routed2MOS/9MIM module no-event residual347.856uV before trim; reference trim is delivered through actual switch during capture.','Routed reference trim-348uV leaves-3.13457uV initially/-3.18418uV late; secant-344.8921377uV with10ns step leaves+0.0633345uV initially/+0.607989uV late. Changed trim and timestep together are not a matched convergence comparison.','Nominal signed routed capture preserves positive17.5432uV and negative17.172481uV increment with attenuation about0.88; exact matching/no noise only.'],'scope':'Baseline capture source/module/clock/read wiring physical within independently qualified macro; inter-macro bank/pair wiring still schematic. Read nodes floating without realistic buffer/load qualification. Capture switch injection, reference precision, calibration controller, thermal/shot/sampled noise, gate leakage/PVT/RPEX/5ms service/float accuracy incomplete. Previous weight trim not valid for changed mismatch hierarchy. Characterization660.3x337.9um module not dense chip geometry.','next':'Qualify sampled baseline/reference trim with loaded read buffer and noise; recalibrate signed weight transfer for assembled hierarchy, map actual float coefficients and integrate full PLIF before dense assembly.','weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'live_sessions':[],'audit_source_sha256':digest(Path(__file__))}
 p=BASE/'results/gf180_physical_baseline_capture_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'completed':completed,'incomplete':len(records)-completed,'physical_checks':True}))
if __name__=='__main__':main()
