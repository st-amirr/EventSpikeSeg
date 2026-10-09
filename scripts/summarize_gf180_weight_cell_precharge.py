"""Audit analog stored-weight/current-cell evidence without accepting full ASIC."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 patterns=['gf180_weight_cell_precharge_*_src48777b529016.json','gf180_routed_precharged_weight_cell_*_srcc058ed2936a6.json']
 records=[]
 for pattern in patterns:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text())
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   assert not any(r.get(k,False) for k in ['weighted_charge_accepted','complete_PLIF_accepted','original_float_accuracy_accepted','full_chip_accepted'])
   records.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'completed':r['simulation_completed'],'settings':r['settings'],'measurements':r['measurements'],'simulator_returncode':r.get('simulator_returncode')})
 completed=sum(r['completed'] for r in records)
 assert len(records)>=7 and completed>=6,(len(records),completed)
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
 report={'stage':'physical_startup_precharge_for_weak_analog_weight_currents','completed_diagnostics':completed,'incomplete_diagnostics':len(records)-completed,'all_provenance_hashes_match':True,'records':records,'physical_cell':physical,'findings':['Actual startup TG released at10us improves weak-cell internal settling and repeated positive contributions.','External2.9V precharge seed29 A/B/A/B gives211.366/869.182/211.180/869.143uV;10ns refinement changes first contribution0.021uV.','External3V alternative gives199.228/861.990/200.685/863.262uV; reference choice affects delivered charge.','External seed17 20ns run aborts at133.99us on event transition; partial measurements are not completed evidence.','New routed8MOS/9MIM precharge cell seed29 gives285.002/515.373/285.374/515.513uV. Different hierarchy/mismatch assignment prevents attributing difference from external variant solely to parasitics.'],'scope':'Startup reference remains ideal bench input; clocks extracted, cell source/writer/hold/startup wiring fully cap-extracted, bank/pair interfaces schematic. Zero-event error, physical output baseline cancellation, calibrated full-float mapping, noise/PVT/gate leakage, signed weights/full PLIF and full-chip remain incomplete. Macro660.3x361.9um is characterization geometry only.','next':'Physically cancel neutral selection packets and output baseline, calibrate signed weight transfer, then integrate full PLIF and dense assembly.','weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'live_sessions':[],'audit_source_sha256':digest(Path(__file__))}
 p=BASE/'results/gf180_weight_cell_precharge_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'completed':completed,'incomplete':len(records)-completed,'physical_checks':True}))
if __name__=='__main__':main()
