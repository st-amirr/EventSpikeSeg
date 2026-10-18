"""Concise article evidence table from existing qualified artifacts; no new simulation."""
from pathlib import Path
import csv,hashlib,json
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cp=B/'assembly/article_module_catalog_v70.json';c=json.loads(cp.read_text());out=B/'assembly/article_evidence_table_v2';assert not out.exists() or not list(out.iterdir());out.mkdir(exist_ok=True);rows=[]
 for kind in ['modules','characterization_assemblies']:
  for e in c[kind]:
   bbox=e.get('bbox_um',[0,0,*e.get('size_um',[0,0])]);files=list(e['views'].values());reports=[]
   for n in files:
    if n.endswith('.json'):
     p=R/n;r=json.loads(p.read_text())
     if 'module_simulation_completed' in r or 'nominal_gate_pass' in r:reports.append(n)
   rows.append(dict(kind=kind,role=e.get('role','five_module_neuron_parent'),cell=e['cell'],MOS=e['mos_count'],MIM=e.get('native_mim_count',''),native_R=e.get('native_resistor_count',''),width_um=bbox[2]-bbox[0],height_um=bbox[3]-bbox[1],area_um2=(bbox[2]-bbox[0])*(bbox[3]-bbox[1]),layout_and_nominal_artifacts_complete=e.get('module_layout_and_nominal_simulation_artifacts_complete',e.get('physical_layout_and_nominal_simulation_artifacts_complete',False)),nominal_gate=e.get('nominal_gate','recorded_in_boundary'),nominal_gate_pass=e.get('nominal_gate_pass','see_boundary'),evidence=';'.join(reports or [n for n in files if n.endswith('.json')]),limitations=e.get('limitations',e.get('limits','see_boundary'))))
 p=out/'module_layout_and_simulation.csv'
 with p.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary=dict(catalog=cp.relative_to(R).as_posix(),reusable_module_artifact_sets=len(c['modules']),completed_characterization_assemblies=len(c['characterization_assemblies']),completed_table_rows=len(rows),explicit_nominal_gate_false=sum(r['nominal_gate_pass'] is False for r in rows),complete_qualified_full_PLIF=False,full_chip_layout_complete=False,accepted_original_float_accuracy=False,full_5ms_population_service_accepted=False,
  broad_stage='Physical modules and real storage-bank prototype completed; full ASIC assembly incomplete.',
  reached=['20 reusable module artifact sets and52 characterization assemblies with layout/nominal evidence','Actual64state shared-row/column bank with5ms native retention/write/read sequence','Original25actor43node54edge graph and disjoint56plane analog-state map','Storage-only physical GDS capacity for54.63million identities','Original-float continuous programming targets and separate parameter-storage GDS'],
  still_required=['Physically connected complete PLIF/adaptation/inhibition/readout/weight path','Calibration/programming/refresh and decoder/driver circuits','Full-chip global interconnect and complete hierarchy qualification','Assembled model-accuracy, throughput and power characterization'],
  scope='Evidence table preserves completed artifacts and measured gate failures. Characterization bbox areas are not selected dense macro areas or chip-area contributions. Storage/parameter atlases omit global wiring and compute; not full-chip layouts. No new tests/simulations or silent acceptance changes.',sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),cp,p]})
 rp=out/'stage_summary.json';rp.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
