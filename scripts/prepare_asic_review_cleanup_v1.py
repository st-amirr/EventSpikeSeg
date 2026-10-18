"""Prepare a reversible, file-accounted ASIC documentation cleanup plan."""
from pathlib import Path
import os,json,hashlib,datetime,collections,re,stat
R=Path(__file__).resolve().parents[1];A=R/'artifacts/analog_asic';AF='artifacts/analog_asic/final';D1='artifacts/ASIC/final';DX='artifacts/ASIC_XL/final';stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');BIN=R/'bin'/('asic_cleanup_2026-10-14_'+stamp);BIN.mkdir(parents=True,exist_ok=False)
roots=['artifacts/analog_asic','artifacts/ASIC','artifacts/ASIC_XL','artifacts/OpenROAD'];keep={};reasons={};missing=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def add(rel,target,why):
 p=R/rel
 if not p.is_file():missing.append(rel);return
 assert p.resolve().is_relative_to(R.resolve()) and not p.is_symlink(),rel
 if rel in keep:return
 assert target not in keep.values(),target
 keep[rel]=target;reasons[rel]=why
def analog_target(rel):
 s=rel.removeprefix('artifacts/analog_asic/')
 if s.startswith('results/module_consumption_v1/'):
  tail=s.removeprefix('results/module_consumption_v1/')
  if '/' in tail:return AF+'/consumption/measurements/'+tail
  return AF+'/evidence/source_manifests/'+tail
 if s.startswith('results/'):return AF+'/evidence/module_results/'+s[8:]
 if s.startswith('benches/'):return AF+'/evidence/benches/'+s[8:]
 if s.startswith('layout/'):return AF+'/components/'+s[7:]
 if s.startswith('assembly/'):return AF+'/evidence/'+s
 if s.startswith('orfs/'):return AF+'/evidence/control_flow/'+s[5:]
 if s.startswith('pdk/gf180_primitive_source/models/ngspice/'):return AF+'/support/gf180_models/'+s.split('/ngspice/',1)[1]
 return AF+'/support/'+s

def analog(rel,why='final analog evidence'):add(rel,analog_target(rel),why)
# Final hierarchical layout and its current audited boundaries.
v='artifacts/analog_asic/assembly/full25_native_controls_v31/'
add(v+'eventspikeseg140k_native_controls_v31.gds',AF+'/layout/EventSpikeSeg140k_GF180_Analog.gds','delivered complete hierarchical research layout; bytes unchanged')
for n in ['article_layout_delivery_v1.json','physical_assembly.json','independent_readback_v1.json','research_boundary_v1.json','native_operation_pads_v2.json','module_evidence_v2.json','escape_plan.json']:analog(v+n)
for p in (R/v/'layout_images_v2').iterdir():
 if p.is_file() and p.suffix in ['.png','.svg','.json']:add(p.relative_to(R).as_posix(),AF+'/images/'+p.name,'final PNG/SVG image and provenance; excludes previews')
# Current consumption outputs, successful raw evidence and their original source fixtures.
cs='artifacts/analog_asic/results/module_consumption_v1/consumption_summary.json';summary=json.loads((R/cs).read_text());assert summary['representative_consumption_characterization_complete'];analog(cs)
for n in ['consumption_inventory.json','delivery_status.json','membrane_source.spice','membrane_partition_source.json','bias_reference_source.spice','bias_reference_partition_source.json']:analog(str(Path(cs).parent/n).replace('\\','/'))
selected=set(summary['source_sha256'])|{a['evidence'] for a in summary['rows']}|{a['trace'] for a in summary['rows'] if a.get('trace')}
me=json.loads((R/v/'module_evidence_v2.json').read_text());selected|={a['report'] for f in me['families'] for a in f['completed_nominal_reports']}
selected|={'artifacts/analog_asic/results/selected_accumulation_retention_v2/simulation.json','artifacts/analog_asic/results/native_control_gates_v1/simulation.json','artifacts/analog_asic/results/native_transfer_gate_v1/simulation.json'}
parsed=set()
def report(rel,depth=0):
 if rel in parsed:return
 parsed.add(rel);analog(rel)
 p=R/rel
 if not p.exists() or p.suffix!='.json':return
 try:j=json.loads(p.read_text())
 except (ValueError,UnicodeError):return
 if '/results/module_consumption_v1/' in rel and p.name=='consumption.json':
  assert j.get('completed'),rel
  for f in p.parent.iterdir():
   if f.is_file():analog(f.relative_to(R).as_posix(),'selected completed consumption measurement')
 refs=set(j.get('sha256',{}))|set(j.get('source_sha256',{}))
 job=j.get('job',{})
 for key in ['source_report','deck','measurement_deck']:
  if isinstance(job.get(key),str):refs.add(job[key])
 for ref in sorted(refs):
  ref=ref.replace('\\','/')
  if not ref.startswith('artifacts/analog_asic/'):continue
  tail=ref.removeprefix('artifacts/analog_asic/')
  if tail.startswith(('results/','benches/','layout/','verification/','tools/source_snapshots/')) and not ref.endswith(('.ext','.npz')):
   if (R/ref).is_file():
    analog(ref,'direct source/result dependency of retained nominal evidence')
    if depth<1 and tail.startswith('results/') and ref.endswith('.json'):report(ref,depth+1)
for s in sorted(selected):report(s)
# Current native top modules and their qualified source views.
cells={f['cell'] for f in me['families']}|{'gf180_neuron_five_module_parent_v6','gf180_signed_event_injection_v1','gf180_sampled_decision_hold_v2','gf180_mim_5x5_ports_routed','gf180_pmos_bias_reference_fullroute_v2','gf180_energy_square_kernel_v1','gf180_energy_mean_root128_v1'}
for c in cells:
 d=A/'layout'/c
 if not d.exists():continue
 for p in d.iterdir():
  if p.is_file() and p.suffix in ['.gds','.lef','.spice','.mag','.json','.log','.feedback','.py','.tcl']:analog(p.relative_to(R).as_posix(),'actual retained native module source/qualification')
# Essential topology and final integration audits, without older full-chip GDS copies.
for rel in ['assembly/full25actor_original_float_population_manifest_v1.json','assembly/full25actor_analog_connectivity_v1.json','assembly/full25_page_forest_v9/physical_assembly.json','assembly/full25_class_infrastructure_v30/integration_readback_v1.json','assembly/full25_native_address_routes_v23/independent_readback_v1.json','assembly/full25_accumulation_architecture_v17/independent_readback_v1.json','assembly/shared_reader_page1024_v1/physical_partition.json','model_reference/eventspikeseg140k_float_parameters.npz','model_reference/eventspikeseg140k_float_reference.json','toolchain.json']:
 if (A/rel).exists():analog('artifacts/analog_asic/'+rel)
# Preserve final categorical macros and their routed views/reports.
for name in ['full25_packet_fabric_v1','full25_actor_ingress_v2','full25_accumulation_dispatch_v1']:
 p=A/'assembly'/name/'physical_macro.json';j=json.loads(p.read_text());analog(p.relative_to(R).as_posix())
 for ref in j.get('sha256',{}):
  f=R/ref
  if f.exists() and (f.name.startswith('6_') or f.suffix in ['.lef','.lib']):analog(ref,'final routed categorical macro view or report')
 design=j['design'];variant=j['variant']
 d=A/'orfs/reports/gf180'/design/variant
 if d.exists():
  for f in d.glob('6*'):
   if f.is_file():analog(f.relative_to(R).as_posix(),'final categorical macro timing/power report')
# GF180 simulator models actually needed by preserved benches; regression/test trees are historical.
md=A/'pdk/gf180_primitive_source/models/ngspice'
for p in md.rglob('*'):
 if p.is_file() and not any(x in ['testing','.git'] for x in p.relative_to(md).parts):analog(p.relative_to(R).as_posix(),'GF180 native model dependency')
# Retain current digital exports and latest documentation/accepted views only.
for root,dest in [('artifacts/ASIC',D1),('artifacts/ASIC_XL',DX)]:
 p=R/root
 for n in ['model_spec.yaml','class_mapping.json','layer_graph.json','quantized_weights.npz','sram_manifest.json','resident_tile_plan_8x8.json','resident_tile_plan.json','eventspikeseg140k_dag_top.sv','eventspikeseg140k_resident_dag_top.sv','generated_eventspikesegxl_dag_top.sv','lane_config.json']:
  if (p/n).exists():add(root+'/'+n,dest+'/model/'+n,'latest digital export for documentation only')
 for folder in ['parameters','weights']:
  for f in (p/folder).rglob('*'):
   if f.is_file():add(f.relative_to(R).as_posix(),dest+'/model/'+folder+'/'+f.relative_to(p/folder).as_posix(),'final exported model constants')
 hp=p/'hard_hierarchy';cat=json.loads((hp/'hard_macro_catalog.json').read_text());masters={a['module'] for a in cat['masters']}
 for f in hp.iterdir():
  if f.is_file() and f.name!='desktop.ini':add(f.relative_to(R).as_posix(),dest+'/hierarchy/'+f.name,'latest exact hierarchy inventory/status; no full-chip-layout claim')
 for folder in ['masters','views']:
  for d in (hp/folder).iterdir():
   if d.is_dir() and d.name in masters:
    for f in d.rglob('*'):
     if f.is_file() and f.suffix in ['.gds','.lef','.lib','.sv','.json']:add(f.relative_to(R).as_posix(),dest+'/hierarchy/'+folder+'/'+f.relative_to(hp/folder).as_posix(),'current referenced master RTL or final staged physical view')
 pc=p/'primitive_characterization'
 for f in pc.rglob('*'):
  if f.is_file() and f.suffix in ['.json','.rpt','.md','.sv','.v','.tcl'] and 'desktop.ini'!=f.name:add(f.relative_to(R).as_posix(),dest+'/reports/primitive_characterization/'+f.relative_to(pc).as_posix(),'final primitive characterization documentation; bulk waveforms/compile attempts archived')
 if root.endswith('ASIC_XL'):
  for n in ['capacity_gate.json','preflight_tiled_readout.json']:
   if (p/'full_chip_layout'/n).exists():add(root+'/full_chip_layout/'+n,dest+'/reports/full_chip_status/'+n,'last full-chip capacity/status; not a completed layout')
  for d in (p/'activity').iterdir():
   if not d.is_dir() or d.name.endswith(';C') or 'verify_fix' in d.name:continue
   for f in d.iterdir():
    if f.is_file() and (f.suffix in ['.json','.rpt'] or f.name in ['gate_functional_replay_v3.log','gate_replay_compat_v5.log','xl_enc1_depthwise_gate_tb.sv']):add(f.relative_to(R).as_posix(),dest+'/reports/activity/'+d.name+'/'+f.name,'last activity/power documentation')
# Final-only digital physical flow views. Older beta variant and intermediate databases stay in bin.
openroot=R/'artifacts/OpenROAD';physical_variants=[]
for f in (openroot/'results').rglob('6_final.gds'):
 tech,design,variant=f.relative_to(openroot/'results').parts[:3]
 if design=='resident_actor_tile_pnr_top' and variant=='xl_enc1_depthwise_1x1':continue
 dest=DX if design.startswith(('xl_','xl_hm_')) or variant.startswith('xl_') else D1
 physical_variants.append([design,variant,dest])
 for p in f.parent.iterdir():
  if p.is_file() and p.name.startswith('6_final.') and p.suffix in ['.gds','.lef','.lib','.def','.v','.sdc','.spef','.json']:
   # Staged GDS is canonical when byte-identical; original duplicate remains reviewable in bin.
   view=R/dest/'hierarchy/views'/design/(design+'.gds');original_view=R/('artifacts/ASIC_XL' if dest==DX else 'artifacts/ASIC')/'hard_hierarchy/views'/design/(design+'.gds')
   if p.suffix=='.gds' and original_view.exists() and sha(p)==sha(original_view):continue
   add(p.relative_to(R).as_posix(),dest+'/physical/'+design+'/'+variant+'/'+p.name,'last completed routed physical view; no intermediate ODB/cache')
 for tree in ['reports','logs']:
  d=openroot/tree/tech/design/variant
  if d.exists():
   for p in d.iterdir():
    if p.is_file() and (p.name.startswith('6_') or p.name in ['5_2_route.json']):add(p.relative_to(R).as_posix(),dest+'/physical/'+design+'/'+variant+'/'+tree+'/'+p.name,'final timing/power/route report')
# Last accepted global-route-only mechanism evidence has no6_final GDS.
for design in ['primitive_140k_stem_inhibition_32_pnr_top','primitive_140k_down2_adaptation_penalty_lane_pnr_top','primitive_140k_down2_adaptation_energy_reduce64_pnr_top','primitive_140k_adaptation_energy_reduce128_pnr_top']:
 for tree in ['reports','logs']:
  d=openroot/tree/'asap7'/design/'checkpoint_exact'
  if d.exists():
   for p in d.iterdir():
    if p.is_file() and p.name.startswith(('5_1_','5_2_')):add(p.relative_to(R).as_posix(),D1+'/reports/global_route_only/'+design+'/'+tree+'/'+p.name,'accepted partial physical stage, explicitly not final routing')
# Original file inventory; directory moves never traverse/remove contained reparse targets.
files=[];links=[]
for root in roots:
 for base,dirs,names in os.walk(R/root,followlinks=False):
  for n in list(dirs):
   p=Path(base)/n
   if p.is_symlink():links.append({'path':p.relative_to(R).as_posix(),'target':os.readlink(p)});dirs.remove(n)
  for n in names:
   p=Path(base)/n;st=p.lstat();rel=p.relative_to(R).as_posix();files.append({'original':rel,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'retained':rel in keep,'current':keep.get(rel,(BIN/R.relative_to(R)/rel).relative_to(R).as_posix())})
# Hash every retained artifact before moves. Archived trees are preserved by same-volume renames.
retained=[]
for rel,dest in sorted(keep.items()):
 p=R/rel;retained.append({'original':rel,'current':dest,'bytes':p.stat().st_size,'sha256':sha(p),'reason':reasons[rel]})
plan={'workspace':str(R),'bin':str(BIN),'roots':[{'source':str(R/x),'archive':str(BIN/x)} for x in roots],'retained_files':retained,'original_files':files,'links':links,'original_file_count':len(files),'original_bytes':sum(x['bytes'] for x in files),'retained_file_count':len(retained),'retained_bytes':sum(x['bytes'] for x in retained),'missing_optional_inputs':sorted(set(missing)),'final_packages':[AF,D1,DX],'physical_variants':physical_variants,'policy':'Move-only cleanup; no permanent deletion. Preserve original evidence bytes and map historical paths. Digital packages are final retained reference snapshots, not completed full-chip layouts.'}
(BIN/'cleanup_plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');(R/'artifacts/asic_cleanup_pending.json').write_text(json.dumps({'plan':str(BIN/'cleanup_plan.json'),'bin':str(BIN)},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'plan':str(BIN/'cleanup_plan.json'),'original_files':len(files),'original_GB':round(plan['original_bytes']/1e9,3),'retained_files':len(retained),'retained_GB':round(plan['retained_bytes']/1e9,3),'archived_GB':round((plan['original_bytes']-plan['retained_bytes'])/1e9,3),'missing_optional':plan['missing_optional_inputs'],'symlink_dirs':len(links)},indent=2))
