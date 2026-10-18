"""Bundle the current complete physical state inventory and reusable module evidence."""
from pathlib import Path
import hashlib,json,re,zipfile
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def main():
 d=B/'assembly/full25_class_current_service_v13';catalog=B/'assembly/article_module_catalog_v104.json';cat=json.loads(catalog.read_text());cov=d/'module_simulation_coverage_v1.json';manifest=d/'physical_assembly.json';audit=d/'independent_top_inventory_v1.json';
 files={d/'eventspikeseg140k_class_current_service_v13.gds',manifest,audit,cov,d/'module_and_parent_summary_v1.json',d/'article_report_v1.html',d/'assembly_overview_v1.svg',catalog,B/'assembly/full25actor_analog_connectivity_v1.json',B/'assembly/full25actor_permanent_analog_state_selectors_v1.json',B/'assembly/float_parameter_capacity_v1/parameter_capacity_assembly.json',B/'model_reference/eventspikeseg140k_float_reference.json'}
 # Reusable module GDS, qualification, extracted C view and its evidence where cataloged.
 for entry in cat['modules']+cat['characterization_assemblies']:
  cell=entry.get('cell')
  if not cell:continue
  ld=B/'layout'/cell
  for n in [f'{cell}.gds','qualification.json','flat_cap_qualification.json','flat_cap_full_qualification.json']:
   p=ld/n
   if p.exists():files.add(p)
  for key in ('views','artifacts'):
   values=entry.get(key,{})
   if isinstance(values,dict):
    for rel in values.values():
     if isinstance(rel,str):
      p=R/rel
      if p.is_file():files.add(p)
 # Coverage entries often point to machine-readable simulation results.
 obj=json.loads(cov.read_text())
 def walk(v):
  if isinstance(v,dict):
   for x in v.values():walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
  elif isinstance(v,str) and v.startswith('artifacts/analog_asic/'):
   p=R/v
   if p.is_file():files.add(p)
 walk(obj)
 files.update(p for p in (B/'results').glob('*.json') if p.name.startswith(('gf180_class_current_shared_io_v1_native_readout_restore_capture_v2','gf180_adaptation_shared_state_io_v6_native_restore_capture')))
 files={p.resolve() for p in files if p.is_file()};notes='EventSpikeSeg140k original-float analog ASIC article candidate\nDate: 2026-10-12\nPDK: GF180\nCheckpoint SHA-256: c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7\n\nPrimary layout: the hierarchical V13 GDS contains all 54,630,400 analog-state identities and shared physical state-access paths. The independent hierarchy and placement audit verifies 56 forest roots, 25 actors, 54,130 native 1024-state pages, disjoint top regions, and the new class-current connection.\n\nScope: research article layout, not fabrication signoff. The layout is spacious. Global operators, trained parameter programming/distribution, categorical sequencing, long-parent RC, complete 5 ms service, and original-model accuracy remain unqualified. The GDS and module reports preserve these limits.\n\nKnown measured errors are retained in the coverage and module reports. Native Netgen mismatches are not represented as passes; independent exact primitive connectivity checks are separately identified.\n'
 dest=B/'delivery/eventspikeseg140k_article_layout_candidate_2026-10-12.zip';assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_STORED) as z:
  z.writestr('DELIVERY_NOTES.txt',notes)
  for p in sorted(files):z.write(p,p.relative_to(R).as_posix())
 with zipfile.ZipFile(dest) as z:
  bad=z.testzip();assert bad is None;names=z.namelist();g='artifacts/analog_asic/assembly/full25_class_current_service_v13/eventspikeseg140k_class_current_service_v13.gds';assert g in names and any(n.endswith('/article_report_v1.html') for n in names)
 idx={'archive':dest.relative_to(R).as_posix(),'bytes':dest.stat().st_size,'file_count':len(names),'zip_integrity_pass':True,'full_assembly_gds_sha256':sha(files and R/g),'archive_sha256':sha(dest),'included_module_sets':len(cat['modules']),'included_characterization_assemblies':len(cat['characterization_assemblies']),'scope':notes}
 (dest.with_suffix('.json')).write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps(idx,indent=2))
if __name__=='__main__':main()
