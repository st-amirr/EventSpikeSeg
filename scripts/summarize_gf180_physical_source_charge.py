"""Audit physical source layouts and compact-source bias diagnostics."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 layouts=[]
 for cell in ['gf180_source_pf05_l1_fullroute','gf180_source_nf05_l1_compact','gf180_source_pf05_l1_compact','gf180_signed_cascode_source_fullroute_spaced_guarded','gf180_signed_cascode_source_compact_guarded']:
  d=BASE/'layout'/cell;q=json.loads((d/'qualification.json').read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():assert digest(d/n if key=='sha256' else ROOT/n)==h,n
  aq=d/'abstract_qualification.json'
  if aq.exists():
   for n,h in json.loads(aq.read_text())['sha256'].items():assert digest(ROOT/n)==h,n
  bbox=q['bbox_um'];layouts.append({'cell':cell,'qualification_sha256':digest(d/'qualification.json'),'size_um':[bbox[2]-bbox[0],bbox[3]-bbox[1]],'area_um2':(bbox[2]-bbox[0])*(bbox[3]-bbox[1]),'gds_full_drc_lvs_readback_pass':True,'lef_qualified':aq.exists()})
 rows=[]
 for pattern in ['gf180_routed_source_autozero_charge_*_src*.json','gf180_compact_source_autozero_charge_*_src*.json','gf180_compact_source_bias_charge_*_src*.json']:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text());assert r['simulation_completed']
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   rows.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'settings':r['settings'],'measurements':r['measurements']})
 strong=[r for r in rows if r['settings'].get('pf_gate_v')==2.55 and r['settings'].get('nf_gate_v')==.6 and r['settings']['sequence']=='p' and r['settings']['width_us']==.1 and r['settings']['mismatch_seed']==29]
 assert len(strong)==2
 strong.sort(key=lambda r:r['settings']['max_step_ns']);a,b=strong
 def deck(row):
  q=json.loads((ROOT/row['report']).read_text());ns=[n for n in q['sha256'] if '/benches/' in n and n.endswith('.spice')];assert len(ns)==1;return (ROOT/ns[0]).read_text()
 assert re.sub(r'(?m)^tran .*$', 'TRAN',deck(a))==re.sub(r'(?m)^tran .*$', 'TRAN',deck(b))
 p=BASE/'results/gf180_physical_source_charge_boundary.json'
 report={'stage':'physical_source_qualification_and_bias_charge_mapping','completed_reports':len(rows),'all_provenance_hashes_match':True,'layouts':layouts,'rows':rows,'compact_source_area_reduction_percent':100*(1-layouts[-1]['area_um2']/layouts[-2]['area_um2']),'matched_step_convergence_uv':abs(a['measurements']['signal_delta']-b['measurements']['signal_delta'])*1e6,'decks_identical_except_tran':True,'failed_original_source_layout':'gf180_signed_cascode_source_fullroute_guarded: DRC0 but LVS supply short; adjacent childM3/body fanout touched. Preserved failed directory; spaced and compact variants independently qualify.','leading_candidate':'compact_extracted_cascode_source_with_higher_bias_into_routed_autozero_integrator_for_characterization_only','scope':'Same native0.5um/L1um transistor geometry, actual body taps and source route extraction. Source modules and integrator qualified separately; their steering/pair/clock/bias links remain schematic. Low-bias short positive pulse still wrong-signed under seed29 after compaction. HigherPF2.55/NF0.6 gate bias restores both signs in two tested seeds but changes voltage scale, duration response and power; signed gain mismatch and residual event errors remain. No original-float weight mapping, noise/globalPVT/qualified gateleak/RPEX/service/PLIF/writeback/chip acceptance. Seed comparisons across geometry are not guaranteed matched statistical realizations. No numerical neutral correction physically applied to state.','live_sessions':[],'weighted_charge_accepted':False,'complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'audit_source_sha256':digest(Path(__file__))}
 p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'completed_reports':len(rows),'compact_source_area_reduction_percent':report['compact_source_area_reduction_percent'],'matched_step_convergence_uv':report['matched_step_convergence_uv']},indent=2))
if __name__=='__main__':main()
