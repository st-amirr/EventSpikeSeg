"""Audit analog stored-weight/current-cell evidence without accepting full ASIC."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 patterns=['gf180_prebiased_weight_bank_*_src*.json','gf180_sampled_weight_bank_*_srcee899f950b02.json','gf180_weight_bank_startup_*_src59bc15ff2f55.json','gf180_routed_weight_bank_*_src4fbcff82dc1a.json','gf180_weight_bank_5ms_revisit_*_src2923bb6824d2.json','gf180_weight_bank_5ms_adaptive_*_srcb6e3761a38bc.json']
 records=[]
 for pattern in patterns:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text())
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   assert not any(r.get(k,False) for k in ['weighted_charge_accepted','complete_PLIF_accepted','original_float_accuracy_accepted','full_chip_accepted'])
   records.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'completed':r['simulation_completed'],'settings':r['settings'],'measurements':r['measurements'],'simulator_returncode':r.get('simulator_returncode')})
 completed=sum(r['completed'] for r in records)
 assert len(records)==12 and completed==11,(len(records),completed)
 cell='gf180_sampled_weight_current_cell_fullroute_complete_guarded';folder=BASE/'layout'/cell
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
 report={'stage':'analog_weight_storage_and_continuously_biased_current_cell_characterization','completed_diagnostics':completed,'incomplete_diagnostics':len(records)-completed,'all_provenance_hashes_match':True,'records':records,'physical_cell':physical,'findings':['Startup settling explains much of early weak-cell inconsistency. At program2.65/2.55V,100us and1ms warmups give nearly identical repeat contributions; this is range-specific.','Routed stored-weight cell gives2.86419/21.6055/2.83349/21.5747mV for A/B/A/B; residual repeat error and nonzero neutral packets remain.','Weak2.75V cell still settles after1ms and changes164.595 to202.112uV between selections; no weight precision acceptance.','Fine20ns5ms revisit timed out before completion; adaptive1us run completed but long-run convergence, gate leakage and sampled noise remain unqualified.','Prior minimum-tested-pulse coverage is initialization/bias-specific, not a physical lower bound or proof of analog impossibility.'], 'scope':'Positive-weight cell only; program voltage ideal at writer input, stored gate physically released. Cap extraction without RPEX. Qualified reusable cell is660.3x352.9um characterization geometry, not a dense weight tile. Full bank/pair routing, negative weights, physical output-baseline/neutral cancellation, calibration, noise/PVT, actual-float coefficient mapping, PLIF semantics, population service and full-chip layout incomplete. Preserve failed missing-leaf layout variant and timed-out fine revisit. No QAT/digital fallback.', 'next':'Stabilize weak-current range and physically compensate event/baseline errors; qualify negative path and measured weight errors against original float before dense assembly.', 'weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'live_sessions':[],'audit_source_sha256':digest(Path(__file__))}
 p=BASE/'results/gf180_weight_bank_storage_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'completed':completed,'incomplete':len(records)-completed,'physical_checks':True}))
if __name__=='__main__':main()
