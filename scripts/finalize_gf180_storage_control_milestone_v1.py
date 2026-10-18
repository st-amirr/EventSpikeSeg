"""Publish the terminal decoded-bank result, supplemental evidence and concise current plan."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,zipfile
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(R).as_posix()
def main():
 script=R/'scripts/screen_gf180_addressed_bank8x8_v2_native_sequence_660s.py';rp=B/'results'/('gf180_addressed_memory_bank8x8_v2_native_decoded_sequence_src'+sha(script)[:12]+'.json');r=json.loads(rp.read_text());cell='gf180_addressed_memory_bank8x8_v2'
 latest=max(B.glob('assembly/article_module_catalog_v*.json'),key=lambda p:int(re.search(r'_v(\d+)',p.name)[1]));revision=int(re.search(r'_v(\d+)',latest.name)[1])+1
 if r['module_simulation_completed']:
  note='Actual174MOS3to8 categorical decoder joins256MOS64MIM bank,430MOS total; all8rows initialized, onlyrow7 overwritten,64states held5ms and rows0and7 read. Preserve measured errors; spacious6.4mm integration fixture is not selected dense area. No numerical digital state or full-chip claim.'
  subprocess.run(['python',str(R/'scripts/publish_gf180_characterization_assembly_20261011_v2.py'),'--cell',cell,'--revision',str(revision),'--report',rel(rp),'--role','native_addressed_8x8_analog_memory_bank','--gate','native_decoded_bank_sequence_observed','--note',note],check=True)
  latest=B/'assembly'/f'article_module_catalog_v{revision}.json';revision+=1
 c=json.loads(latest.read_text());supp=B/'results/gf180_parameter_and_retention_supplement_v1.json';param=B/'assembly/float_parameter_capacity_v1/parameter_capacity_assembly.json'
 extra=[supp,param,rp,B/'results/gf180_compact_analog_memory_4t_v4_three_native_50ms_srcf745b3914a1a.json',B/'results/gf180_compact_memory_bank8x8_v1_native_50ms_select_write_hold_read_src59f711035ce9.json']
 for n,h in c['sha256'].items():assert sha(R/n)==h,n
 for e in c['characterization_assemblies']:
  if e['cell']=='gf180_compact_analog_memory_4t_v4':e['supplemental_50ms_retention']=rel(extra[3])
  if e['cell']=='gf180_compact_memory_bank8x8_v1':e['supplemental_50ms_retention']=rel(extra[4])
 if not r['module_simulation_completed']:
  c['in_progress_assemblies'].append(dict(cell=cell,source_GDS_flat_LEF_complete=True,native_loaded_sequence_complete=False,report=rel(rp),next_action='Diagnose decoded transition/load runtime before any focused repair; no blind retry.'))
 c.update(revision=revision,previous_catalog=rel(latest),float_parameter_capacity=rel(param),supplemental_retention_evidence=rel(supp));c['sha256'].update({rel(p):sha(p) for p in extra});new=B/'assembly'/f'article_module_catalog_v{revision}.json';assert not new.exists();new.write_text(json.dumps(c,indent=2)+'\n');n=len(c['modules']);m=len(c['characterization_assemblies'])
 docs=[R/'docs'/name for name in ['AGENTS.md','ACTIVE_TASKS.md','ARCHITECTURE.md','DECISIONS.md','RESULTS.md','PROGRESS.md','project_spec.yaml']];stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');zp=B/'documentation_history'/('project_docs_before_storage_control_milestone_'+stamp+'.zip')
 with zipfile.ZipFile(zp,'x',zipfile.ZIP_DEFLATED) as z:
  for p in docs:z.writestr(rel(p),p.read_bytes())
 zp.with_suffix('.json').write_text(json.dumps({'archive_sha256':sha(zp),'files':{rel(p):sha(p) for p in docs}},indent=2)+'\n')
 decoded=(f'Connected decoded-bank simulation completes; nominal gate={r["native_decoded_bank_sequence_observed"]}, maximum write error{r["max_write_error_v"]*1000:.2f}mV, hold excursion{r["max_hold_excursion_v"]*1000:.2f}mV and read disturbance{r["max_read_disturbance_v"]*1000:.2f}mV.' if r['module_simulation_completed'] else 'Decoded-bank source/GDS/flat/LEF complete; connected native sequence incomplete after bounded runtime extension. Retain independent completed bank5ms/50ms sequences; do not infer loaded decoder success.')
 active=f'''# Active tasks

Updated2026-10-11. Read this page first, then only evidence needed for the next decision.

## Current stage

**Physical modules and storage/control integration. Full ASIC assembly remains incomplete.**

Goal: article-suitable original-float EventSpikeSeg140k analog ASIC, with full layout and per-module simulations. Preserve trained semantics and5ms updates. Record imperfections now; precision refinement follows this milestone. Manufacture-ready signoff is outside scope.

| Position | Summary |
| --- | --- |
| Completed artifacts | {n} reusable module sets and{m} characterization assemblies; catalog revision{revision} |
| Storage | Compact4T/50fF cell and real8x8 bank; native5ms and50ms hold/write/read sequences complete |
| Addressed bank | {decoded} |
| RMS/frontend | Source/GDS/LEF,3DC points and exploratory hierarchical-PEX6us transient complete;17.40mV settling error retained; flat-cap equivalence unaccepted |
| Model assembly | Original25actor43node54edge graph and56state-plane map; storage and parameter capacity GDS written |
| Unfinished | Complete connected analog compute path, programming/read calibration, global routing, model accuracy and full-population5ms service |
| Live jobs | None; terminal results preserved |

## Next work package

1. Complete connected analog compute/control interfaces using the qualified modules. Preserve observed signed-injection, beta, adaptation and reset errors; avoid repeating finished precision gates.
2. Resolve read offset, analog programming/refresh and dense decoder/driver integration. The addressed-bank fixture uses spacious routing and is not a dense area estimate.
3. Assemble actual functional tiles, then full-model physical interconnect and hierarchy. Storage-only GDS does not meet full-chip completion.
4. Characterize assembled accuracy,5ms service, area and power. No full-model native SPICE campaign.

No critical user decision is pending. Continue autonomously; raise only a consequential unresolved architecture/scope tradeoff.

## Evidence and area boundary

- Catalog: `artifacts/analog_asic/assembly/article_module_catalog_v{revision}.json`.
- State capacity: `artifacts/analog_asic/assembly/full_capacity_storage_gds_v1/capacity_assembly.json`;54,630,400 active identities,866,080 actual8x8 banks,14,545.65mm2 bank geometry. Global routing and compute absent; native whole-atlas read/DRC/LVS incomplete.
- Parameters: `artifacts/analog_asic/assembly/float_parameter_capacity_v1/parameter_capacity_assembly.json`;143,824 weights and1,856 beta channels among147,567 continuous original-float requests,39.43mm2 bank geometry. No QAT or integer DAC codes; physical programming calibration remains incomplete.
- Retention: `artifacts/analog_asic/results/gf180_parameter_and_retention_supplement_v1.json`; actual8x8 bank50ms hold excursion11.67mV. Typical/noise-off fixture evidence, not population precision.
- User accepted1,215mm2 conditional state/auxiliary bare-plate estimate. It excludes switches/peripherals/routes and is not the physical bank or full-chip area.
- Longest same-bin dependency is23PLIF stages. Storage8x8 grouping does not select64-site compute sharing or prove throughput.

## Lightweight workflow

- One question, matching baseline, one changed mechanism, named metric and next action. Reuse existing evidence.
- Initially at most3cases,120s,2CPU/2GB and one simulator; maximum2independent jobs. Measured runtime extensions need explicit basis.
- Two similar failures require diagnosis; one unsuccessful focused repair requires method review. No blind parameter/tolerance/runtime sweep.
- Freeze calibration before independent comparisons. Qualified children do not qualify a new parent. Record complete runs even when precision gates fail.
- Keep raw detail in JSON/logs/source snapshots. Update this page on stage/job changes; RESULTS owns findings, DECISIONS choices, ARCHITECTURE semantics, PROGRESS milestones. YAML mirrors the operational index.
- Archive exact existing docs before meaningful edits. Preserve consumed scripts/reports; version changes. No new Markdown, subagents, commits/remotes or deletes.

## Fixed scope and navigation

GF180 prototype, original epoch58 float checkpoint, analog numerical state. Categorical control/address bits are allowed. QAT/digital membrane fallback and XL/digital campaigns stay paused. Full goal remains active and incomplete.

[ARCHITECTURE](ARCHITECTURE.md) / [RESULTS](RESULTS.md) / [DECISIONS](DECISIONS.md) / [PROGRESS](PROGRESS.md) / [project_spec.yaml](project_spec.yaml).
'''
 (R/'docs/ACTIVE_TASKS.md').write_bytes(active.replace('\n','\r\n').encode())
 sections={
  'RESULTS.md':decoded+' Compact cell and8x8 bank50ms nominal retention complete; maximum excursions9.07mV and11.67mV. Full64 connected RMS/frontend6us exploratory transient completes after one100ns external input-slew diagnostic; root settling error17.40mV and sampled adaptation amplitude1.19437/1.19759/1.19371V are retained, including nonmonotonic transient output. Native hierarchy capacitance differs from geometric-flat baseline; no flat equivalence or model accuracy acceptance. Catalog'+str(revision)+f':{n} module sets/{m} assemblies.',
  'ARCHITECTURE.md':'Continuous original-float parameter requests cover143,824 weights and1,856 beta channels among147,567 stored values. Voltage requests1.2+0.2*value/max_abs are invertible mathematical targets with no QAT/bit-depth conversion; they are not calibrated achieved transistor controls. Affine gain is already folded into weights. Categorical3to8 row decoding controls analog memory without digitizing numerical state. State and parameter GDS are separate capacity atlases, with full-chip compute/interconnect still absent.',
  'DECISIONS.md':'Close RMS settling refinement for this milestone after the completed native100ns-input-edge run. Preserve initial180s timeout,660s first-edge abort, successful focused slew diagnostic and failed geometric-flat extraction; no tolerance or further precision sweep. Preserve independent5ms/50ms storage evidence and explicit loaded decoder status. Native hierarchy algebraic expansion requires formal-port scoping; the first erroneous global VSUBS expansion was rejected by independent device comparison and remains preserved. The corrected device graph passes, but capacitance matrices are not flat-equivalent. Do not use spacious decoder/RMS fixture footprints as dense replicated chip area.',
  'PROGRESS.md':f'Catalog{revision}:{n} reusable module sets/{m} characterization assemblies. '+decoded+' Original-float parameter atlas and continuous targets complete;50ms storage checks complete. Full ASIC goal remains incomplete. Operational plan shortened; exact prior documents archived at '+rel(zp)+'.'
 }
 for name,text in sections.items():
  p=R/'docs'/name;b=p.read_bytes();i=b.index(b'\n## ');p.write_bytes(b[:i]+('\n## Storage control and article evidence milestone - 2026-10-11\n\n'+text+'\n\nEvidence: `'+rel(new)+'`, `'+rel(supp)+'`, `'+rel(rp)+'`.\n').encode()+b[i:])
 p=R/'docs/project_spec.yaml';b=p.read_bytes();h,t=b.split(b'\ndocument:',1);h=re.sub(rb'  module_catalog: [^\r\n]+',b'  module_catalog: '+rel(new).encode(),h,count=1);h=re.sub(rb'  live_sessions: [^\r\n]+',b'  live_sessions: []',h,count=1);h=re.sub(rb'  storage_candidate: [^\r\n]+',b'  storage_candidate: compact_4T_50fF_8x8_bank_nominal5ms50ms_read_offset_uncalibrated',h,count=1);h=re.sub(rb'  latest_documentation_archive: [^\r\n]+',b'  latest_documentation_archive: '+rel(zp).encode(),h,count=1);h=re.sub(rb'    report: [^\r\n]+',b'    report: '+rel(rp).encode(),h,count=1);h=re.sub(rb'    status: [^\r\n]+',f'    status: {n}_modules_{m}_assemblies_fullchip_incomplete'.encode(),h,count=1);h=re.sub(rb'    next_action: [^\r\n]+',b'    next_action: connected_analog_compute_calibration_then_dense_tile_and_global_layout',h,count=1)
 h=h.replace(b'  full_population_manifest:',b'  float_parameter_capacity: '+rel(param).encode()+b'\r\n  storage_retention_supplement: '+rel(supp).encode()+b'\r\n  full_population_manifest:',1);p.write_bytes(h+b'\ndocument:'+t)
 print(json.dumps({'catalog':rel(new),'modules':n,'assemblies':m,'decoded_bank_complete':r['module_simulation_completed'],'full_chip_layout_complete':False,'archive':rel(zp)},indent=2))
if __name__=='__main__':main()
