"""Audit native trim-bank reachability and external code selection evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/results'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 sources={Path(__file__)};cases=[]
 for path in sorted(OUT.glob('gf180_trim_bank_*.json')):
  if path.name=='gf180_trim_bank_boundary.json':continue
  r=json.loads(path.read_text());sources.add(path)
  for name,sha in r['sha256'].items():
   f=ROOT/name
   if digest(f)!=sha:raise ValueError('Source/native input differs')
   sources.add(f)
  snapshot=ROOT/r['source_snapshot'];sha=snapshot.stem.rsplit('_',1)[-1]
  if not re.fullmatch('[a-f0-9]{64}',sha) or digest(snapshot)!=sha:raise ValueError('Immutable executable differs')
  for q in r['qualified_layout_components']:
   if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Native qualification differs')
   for name,h in q['sha256'].items():
    if digest(ROOT/'artifacts/analog_asic/layout'/q['cell']/name)!=h:raise ValueError('Native geometry differs')
  pairs={(x['code'],round(x['voltage_difference_v'],3)) for x in r['rows']}
  if r['simulation_completed']:
   if pairs!={(i,v) for i in range(128) for v in [-.2,.2]}:raise ValueError('DC code/polarity coverage differs')
   best=r['analysis']['best_external_dc_code'];actual=min((max(abs(x['diagnostic_untrimmed_gain_error_percent']) for x in r['rows'] if x['code']==i),i) for i in range(128))
   if actual!=(best['maximum_two_polarity_rc_gain_error_percent'],best['externally_selected_code']):raise ValueError('External selection differs from actual rows')
  cases.append({'evidence':path.relative_to(ROOT).as_posix(),'simulation_completed':r['simulation_completed'],'simulator_returncode':r['simulator_returncode'],'settings':r['settings'],'operating_point_solver_warning':r.get('operating_point_solver_warning',True),'observed_dc_samples':len(r['rows']),'analysis':r['analysis'],'scope':r['scope'],'dc_numerical_precision_qualified':False})
 imp_path=OUT/'gf180_component_lef_import.json';imp=json.loads(imp_path.read_text());sources.add(imp_path)
 for name,h in imp['sha256'].items():
  f=ROOT/name
  if digest(f)!=h:raise ValueError('Abstract/router inputs differ')
  sources.add(f)
 result={'cases':cases,'case_count':len(cases),'simulations_completed':sum(x['simulation_completed'] for x in cases),'source_native_and_external_selection_provenance_verified':True,'router_import_verified':imp['router_import_verified'],'autonomous_calibration_controller_implemented':False,'combined_trim_bank_layout_qualified':False,'physical_writeback_accepted':False,'full_chip_accepted':False,'scope':'Actual native resistor/TG/inverter DC code reachability including independent passive/MOS corners and typical feedbackMIM capacitance metrology. External search selects a code from128settings; no autonomous calibration circuit, dynamic writeback/noise/mismatch/controller accuracy/5ms or combined layout acceptance. Historical first overly strict OP-warning completion rejection retained separately as incomplete.','sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
 target=OUT/'gf180_trim_bank_boundary.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(target),'case_count':len(cases),'simulations_completed':result['simulations_completed']}))
if __name__=='__main__':main()
