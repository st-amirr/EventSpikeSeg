"""Collect a reviewable local evidence package, retaining all completion limitations."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cp=B/'assembly/article_module_catalog_v70.json';c=json.loads(cp.read_text());selected={cp,Path(__file__)};queue=[]
 def add(p):
  if not p.is_file() or p in selected:return
  selected.add(p)
  if p.suffix=='.json':queue.append(p)
 for section in ['modules','characterization_assemblies']:
  for e in c[section]:
   for n in e['views'].values():add(R/n)
   add(B/'layout'/e['cell']/(e['cell']+'.mag'))
   for k in ['supplemental_50ms_retention']:
    if k in e:add(R/e[k])
 for folder in ['assembly/full_capacity_storage_gds_v1','assembly/float_parameter_capacity_v1','assembly/article_evidence_table_v2']:
  for p in (B/folder).iterdir():add(p)
 for n in ['full25actor_analog_connectivity_v1.json','full25actor_permanent_analog_state_selectors_v1.json','full25actor_original_float_population_manifest_v1.json']:add(B/'assembly'/n)
 for n in ['eventspikeseg140k_float_reference.json','eventspikeseg140k_float_parameters.npz']:add(B/'model_reference'/n)
 for p in (R/'docs').iterdir():
  if p.name in ['AGENTS.md','ACTIVE_TASKS.md','ARCHITECTURE.md','DECISIONS.md','RESULTS.md','PROGRESS.md','project_spec.yaml']:add(p)
 # Include raw native result traces/logs/decks and consumed source snapshots.
 # Do not recurse through PDK/model or historical catalog dependency trees.
 while queue:
  p=queue.pop();d=json.loads(p.read_text());mapping=d.get('sha256',{})
  for n in mapping:
   q=R/n if '/' in n else p.parent/n
   if str(q).startswith(str(B/'results')) or str(q).startswith(str(B/'benches')) or str(q).startswith(str(B/'tools/source_snapshots')):add(q)
   elif str(q).startswith(str(R/'scripts')):add(q)
 total=sum(p.stat().st_size for p in selected);assert total<1_000_000_000,'Review package would exceed1GB; preserve manifest without copying excessive data.'
 out=B/'assembly/article_evidence_package_v1';assert not out.exists();out.mkdir();manifest=out/'package_manifest.json'
 meta=dict(catalog_revision=70,reusable_module_sets=20,completed_characterization_assemblies=52,includes_one_exploratory_hierarchical_PEX_assembly=True,full_chip_layout_complete=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,file_count=len(selected),uncompressed_bytes=total,
  scope='Local article/review evidence collection: actual module GDS/LEF/SPICE/MAG, qualifications, nominal reports with raw traces/logs/decks and source snapshots, full-model logical graph, storage/parameter capacity atlases and continuous float targets. Completed characterization does not mean every precision gate passed. Full64 RMS uses exploratory hierarchical PEX and lacks flat equivalence. Full-chip compute/global wiring and acceptance remain incomplete. Capacity GDS are storage/parameter-only, not routed full ASICs. PDK/model binaries and Docker images are external dependencies; this archive is not a standalone reproducible environment or fabrication package.',
  files={p.relative_to(R).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(selected)})
 manifest.write_text(json.dumps(meta,indent=2)+'\n');zp=out/'EventSpikeSeg_GF180_article_evidence_v1.zip'
 with zipfile.ZipFile(zp,'x',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
  for p in sorted(selected):z.write(p,p.relative_to(R).as_posix())
  z.write(manifest,'package_manifest.json')
 receipt=out/'package_receipt.json';receipt.write_text(json.dumps({'zip':zp.relative_to(R).as_posix(),'zip_bytes':zp.stat().st_size,'zip_sha256':sha(zp),'manifest':manifest.relative_to(R).as_posix(),'full_chip_layout_complete':False},indent=2)+'\n');print(receipt.read_text())
if __name__=='__main__':main()
