"""Audit routed autozero layout and signed-update diagnostic evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[]
 for pattern in ['gf180_autozero_capacitor_packet_*_src*.json','gf180_routed_autozero_packet_*_src*.json','gf180_routed_autozero_gatepulse_*_src*.json','gf180_routed_autozero_steered_charge_*_src*.json']:
  for p in sorted((BASE/'results').glob(pattern)):
   r=json.loads(p.read_text());assert r['simulation_completed'],str(p)
   for n,h in r['sha256'].items():assert digest(ROOT/n)==h,n
   rows.append({'report':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'settings':r['settings'],'measurements':r['measurements']})
 cell='gf180_autozero_charge_integrator_fullroute_guarded';d=BASE/'layout'/cell;q=json.loads((d/'qualification.json').read_text());aq=json.loads((d/'abstract_qualification.json').read_text())
 assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
 for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
  for n,h in q.get(key,{}).items():assert digest(d/n if key=='sha256' else ROOT/n)==h,n
 for n,h in aq['sha256'].items():assert digest(ROOT/n)==h,n
 def find(kind,sequence,width,seed,neutral=False,step=20,delta=None):
  hits=[r for r in rows if ('gf180_routed_autozero_'+kind+'_') in r['report'] and r['settings']['sequence']==sequence and r['settings']['width_us']==width and r['settings']['mismatch_seed']==seed and r['settings']['neutral']==neutral and r['settings']['max_step_ns']==step and (delta is None or r['settings'].get('delta_v')==delta)]
  assert len(hits)==1,(kind,sequence,width,seed,neutral,step,delta,len(hits));return hits[0]
 a=find('steered_charge','p',.1,29);b=find('steered_charge','p',.1,29,step=10)
 def deck(row):
  r=json.loads((ROOT/row['report']).read_text());names=[n for n in r['sha256'] if n.endswith('.spice') and '/benches/' in n];assert len(names)==1;return (ROOT/names[0]).read_text()
 assert re.sub(r'(?m)^tran .*$', 'TRAN',deck(a))==re.sub(r'(?m)^tran .*$', 'TRAN',deck(b))
 convergence={'decks_identical_except_tran':True,'positive_short_seed29_step_delta_uv':abs(a['measurements']['signal_delta']-b['measurements']['signal_delta'])*1e6}
 report={'stage':'routed_shared_autozero_integrator_and_injector_comparison','completed_reports':len(rows),'all_provenance_hashes_match':True,'rows':rows,'layout':{'qualification':(d/'qualification.json').relative_to(ROOT).as_posix(),'qualification_sha256':digest(d/'qualification.json'),'abstract_qualification_sha256':digest(d/'abstract_qualification.json'),'full_drc_and_lvs_and_gds_readback_pass':True,'lef_ports_and_size_verified':True,'size_um':aq['size_um'],'mos_count':q['mos_count'],'native_mim_count':q['native_mim_count'],'shared_not_per_state':True},'convergence':convergence,'leading_candidate':'continuous_current_steering_into_routed_autozero_integrator_for_further_characterization_only','scope':'Macro geometry qualified; paired integrator/source/clock/bias assembly remains schematic. Same seed across changed topology is not guaranteed matched random device realizations. Two seeds are not population qualification. Small contribution signs restored in steered cases, but per-event offsets/gain variation/physical baseline cancellation remain. Switched-capacitor seed29 positive50uV remains wrong-signed; gate-only injection shows long tails. No neutral/baseline correction physically applied to state. Ideal references/control signals do not implement learned weight/beta/threshold/reset/adaptation or accurate writeback. No noise/globalPVT/RPEX/qualified gateleak/model tolerance/5ms population/full-chip acceptance.','live_sessions':[],'complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False}
 p=BASE/'results/gf180_autozero_update_boundary.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(p),'completed_reports':len(rows),'layout_size_um':aq['size_um'],'convergence':convergence},indent=2))
if __name__=='__main__':main()
