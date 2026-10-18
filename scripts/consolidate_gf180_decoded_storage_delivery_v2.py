"""Consolidate exact existing module evidence and whole-assembly gaps in one report."""
from pathlib import Path
import json,csv,hashlib,html
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_locally_decoded_storage_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cp=B/'assembly/article_module_catalog_v97.json';cat=json.loads(cp.read_text());mp=D/'physical_assembly.json';m=json.loads(mp.read_text());rows=[];inputs={Path(__file__),cp,mp};cache={}
 def read(p):
  if p not in cache:cache[p]=json.loads(p.read_text())
  inputs.add(p);return cache[p]
 def evidence(entry):
  pending=[R/v for v in entry.get('views',{}).values() if v.endswith('.json') and '/results/' in v];done=set();out=[]
  for p in pending:
   if p in done:continue
   done.add(p);q=read(p);out.append((p,q))
   report=q.get('report')
   if isinstance(report,str) and report.endswith('.json') and '/results/' in report:
    p1=R/report
    if p1.exists() and p1 not in done:pending.append(p1)
   for n in q.get('sha256',{}):
    if '/results/' in n and n.endswith('.json'):
     p1=R/n
     if p1.exists() and p1 not in done:pending.append(p1)
  return out
 entries=cat['modules']+cat['characterization_assemblies'];known={e['cell'] for e in entries}
 for cell in m['native_macro_instances']:
  if cell not in known:
   qp=B/'layout'/cell/'qualification.json';rp=list((B/'results').glob(cell+'*.json'));entry=dict(cell=cell,role='assembly_selected_not_in_catalog96',views={'q':qp.relative_to(R).as_posix(),**{str(i):p.relative_to(R).as_posix() for i,p in enumerate(rp)}},limitations='Inspect report scope; selected physical module is not automatically simulation-qualified.');entries.append(entry)
 for e in entries:
  ev=evidence(e);flags={str(p.relative_to(R)):{k:v for k,v in q.items() if isinstance(v,bool) and any(s in k for s in ['completed','observed','accepted','pass'])} for p,q in ev};completed=any(q.get('module_simulation_completed') is True for p,q in ev);failed=[p.relative_to(R).as_posix()+':'+k for p,q in ev for k,v in q.items() if v is False and isinstance(v,bool) and (k.endswith('_observed') or k.endswith('_pass'))];qf=B/'layout'/e['cell']/'qualification.json';q=read(qf) if qf.exists() else {};fullC=B/'layout'/e['cell']/'flat_cap_full_qualification.json';hasC=fullC.exists() and read(fullC).get('all_flat_extraction_node_ground_caps_verified') is True
  rows.append(dict(cell=e['cell'],role=e.get('role','catalog_characterization_assembly'),placed_native_instances=m['native_macro_instances'].get(e['cell'],0),source_full_drc_count=q.get('magic_drc_count'),gds_full_drc_count=q.get('gds_roundtrip_drc_count'),native_gds_netgen_pass=q.get('native_gds_netgen_pass'),complete_flat_substrate_export_verified=hasC,completed_nominal_report_found=completed,catalog_artifacts_complete=e.get('module_layout_and_nominal_simulation_artifacts_complete',False),recorded_nominal_gate=e.get('nominal_gate'),recorded_nominal_gate_pass=e.get('nominal_gate_pass'),failed_observation_gates=failed,reports=[p.relative_to(R).as_posix() for p,q in ev],report_flags=flags,limitations=e.get('limitations',e.get('limits',''))+' Report completion can cover an isolated phase only; inspect linked scope.'))
 # Explicit latest records override no historical result; keep both scopes visible.
 extra=[B/'results/gf180_tile_v3_fullcap_three_state_beta_summary_v1.json',B/'results/gf180_resident_adaptation_expiry_v3_fullcap_nominal_src98bffbb7a8dd.json',B/'results/gf180_shared_reader_serial_budget_v2.json',B/'results/gf180_independent_bank_pair_v4_access_summary_v1.json',B/'results/gf180_independent_bank_pair_v4_trace_review_v1.json']
 latest={p.relative_to(R).as_posix():read(p) for p in extra}
 integration_path=B/'assembly/full25_physical_candidate_v5/verification/actor_00_v3/qualification_attempt.json'
 integration=read(integration_path) if integration_path.exists() else {'parent_native_command_completed':False,'full_parent_drc_count':None}
 exact_path=integration_path.with_name('parent_exact_connectivity_attempt.json')
 if exact_path.exists():integration={**integration,'independent_connectivity_attempt':read(exact_path),'independent_connectivity_accepted':read(exact_path)['independent_connectivity_accepted']}
 identity_path=D/'independent_bank_identity_readback_v1.json';identity=read(identity_path);assert identity['all_emitted_local_decoder_bank_identities_bijective']
 patch=dict(identity_binding_scope='Actual emitted locally decoded native pair/single placements independently bound to original bank identities; replaces inherited historical raw-capacity paths.25first compute banks remain in original actor cells.',bindings=[dict(actor=p['actor'],state_kind=p['state_kind'],candidate_state_plane_cell=p['candidate_cell'],identity_binding=p['identity_binding']) for p in m['state_planes']],independent_readback=identity_path.relative_to(R).as_posix(),corrected_atlas_bbox_um=m['atlas_bbox_um'],footprint_is_not_dense_die_area=True)
 (D/'identity_and_bounds_binding_v2.json').write_text(json.dumps(patch,indent=2)+'\n')
 requirements=[
  ('All original resident identities physically included','geometry_and_bank_identity_bijection_verified','54,630,400active identities/all56planes; independently checked866,055decoded native bank identities plus25original compute banks.'),
  ('Original continuous parameter values','targets_and_capacity_only','147,567continuous targets/native capacity slots; programming/distribution/precision incomplete.'),
  ('Analog bank access','local_row_decode_throughout_capacity_global_access_incomplete','866,055bank equivalents in433,015independently selected native pairs and25singles; original25compute banks retained. Global bank selection/shared reader/writeback/compute binding absent.50us isolation sequence complete;write error23.56mV,untargeted peak8.340mV/final.615mV;UIC startup2.37V,native initialization missing.'),
  ('Signed weight to charge','first_actor_physical_connections_qualified_nominal_parent_missing','First actor native DRC0 and exact1191primitive connectivity;25actor cells preserved byte-identically. Other actors/combined transient and trained weight distribution unqualified.'),
  ('Learned beta/state update','phase_characterized_precision_unaccepted','Three complete-C beta cases; largest trained residual20.763mV. Complete corrected tile cycle unfinished.'),
  ('Decision and subtractive reset','partial','Native children have nominal reports; shared clipped-threshold connection/voltage interface unfinished.'),
  ('Peer inhibition','partial','Actuator and phase/own-spike/state connections placed; all-channel ANY_SPIKE producer unbound.'),
  ('Adaptation age/amplitude/triangle/product','completed_imperfect_local_run','Complete-C resident sequence: initialization/reset/resume observed; expiry block false. Resident plane access unbound.'),
  ('Adaptation SUM64 and clipped threshold','completed_local_nominal','3cases;maxsum5.606mV,maxclippedthreshold4.936mV. External perfeature producer voltages.'),
  ('Adaptation SUM128 and clipped threshold','layout_only','Source/GDS DRC0 and exact source/GDS device connectivity; fresh flat EXT truncated/rejected, no completed nominal simulation.'),
  ('RMS64','partial_nominal_evidence','Native physical energy formatter/kernel/reduction blocks exist; accuracy unaccepted.'),
  ('RMS128','missing_final_reduction','Two native64components placed; combination into exact128channel RMS remains absent.'),
  ('Autonomous categorical control','local_children_only','Native event/bin controllers and selected phase connections placed; full bank scheduling/graph protocol incomplete.'),
  ('Global43node54edge event graph','logical_graph_and_physical_corridors','All54edges/2754categorical wires end at interface pads; semantic operators and endpoints unbound.'),
  ('Six-class readout','local_macro_only','Native6class macro placed; all1,689,600class-current identities included; plane access/50ms qualification incomplete.'),
  ('Full-chip physical/electrical verification','incomplete','First actor native DRC0 and exact1191primitive connectivity. Native decoded bank pair source/GDS DRC0/Netgen pass. Independent all-bank identity readback passes; whole-chip DRC/LVS/extraction incomplete.'),
  ('5ms and original-float accuracy','unproven','No fullpopulation service or original-float model acceptance evidence.')]
 with (D/'module_simulation_coverage_v2.csv').open('w',newline='') as f:
  fields=['cell','role','placed_native_instances','source_full_drc_count','gds_full_drc_count','complete_flat_substrate_export_verified','completed_nominal_report_found','recorded_nominal_gate','recorded_nominal_gate_pass','failed_observation_gates','reports'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
 out=dict(catalog_revision=97,catalog_module_sets=20,catalog_characterization_assemblies=76,reviewed_rows=len(rows),requirements=[dict(requirement=a,status=b,evidence_and_gap=c) for a,b,c in requirements],modules=rows,latest_scoped_reports=latest,latest_actor_parent_integration=integration,assembly_full_function_accepted=False,coverage_is_not_a_fullmodel_simulation=True,sha256={p.relative_to(R).as_posix():sha(p) for p in inputs});(D/'module_simulation_coverage_v2.json').write_text(json.dumps(out,indent=2)+'\n')
 esc=html.escape
 table=''.join('<tr><td>'+esc(a)+'</td><td>'+esc(b.replace('_',' '))+'</td><td>'+esc(c)+'</td></tr>' for a,b,c in requirements)
 h='<!doctype html><meta charset="utf-8"><title>EventSpikeSeg140k assembly delivery</title><style>body{font:16px system-ui;margin:40px;max-width:1300px;background:#101827;color:#edf2f7}h1{font-size:28px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #465164;padding:10px;text-align:left;vertical-align:top}a{color:#7dd3fc}.gap{background:#3b2b19;padding:18px}img{width:100%;background:#0c1423}small{color:#bac6d9}</style><h1>EventSpikeSeg140k physical integration candidate</h1><p class="gap">A combined GDS exists. Functional full-chip layout, original-float accuracy and5ms service are still incomplete.</p><p>54,630,400resident identities ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â·147,567parameter targets ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â·25representative compute/control clusters ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â·54graph corridors.</p><p><a href="eventspikeseg140k_locally_decoded_storage_v1.gds">GDS</a> ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â· <a href="physical_assembly.json">Assembly manifest</a> ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â· <a href="identity_and_bounds_binding_v2.json">Identity/bounds correction</a> ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â· <a href="module_simulation_coverage_v2.csv">Module simulation CSV</a> ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â· <a href="module_simulation_coverage_v2.json">Full linked evidence</a></p><small>Blue/purple: actual resident bank arrays; green: sparse characterization macro clusters; amber: parameter capacity. Pink: unbound protocol corridors. Atlas footprint is not compact die area.</small><details><summary>Physical overview</summary><img src="assembly_overview.svg"></details><h2>Required functions and actual coverage</h2><table><tr><th>Requirement</th><th>Status</th><th>Evidence / remaining work</th></tr>'+table+'</table>'
 h+='<h2>Latest actor integration check</h2><pre>'+esc(json.dumps({k:v for k,v in integration.items() if k!='sha256'},indent=2))+'</pre><p><a href="../full25_physical_candidate_v5/verification/actor_00_v3/qualification_attempt.json">Native parent check evidence</a></p>'
 h+='<h2>Full-capacity local access upgrade</h2><p>433,015native independently selected128state pairs +25decoded single banks +25original compute banks. All866,080bank equivalents and54,630,400active state identities retained. <a href="independent_bank_identity_readback_v1.json">Independent emitted-GDS identity proof</a>.</p><p>Actual locally decoded native macro footprints total34,801.03mm2 in this spacious prototype. This includes decoding and routing; it is neither the1,215mm2bare-plate estimate nor a compact manufacturable die.</p><p>New50us full-C native bank sequence completed. Opposite-bank change during write0.437mV;112untargeted states peak8.340mV during read-enable/final0.615mV;maximum write error23.56mV. Original20mV combined gate remains false. Requested1.2V.ic startup actually settles2.372..2.375V before writes; native initialization,5ms parent retention/global service not proven.</p><p><a href="bank_pair_native_sequence_v2.png">Native simulation figure</a></p>'
 (D/'delivery_report_v2.html').write_text(h,encoding='utf-8');print(json.dumps({'coverage_rows':len(rows),'requirements':len(requirements),'assembly_report':str(D/'delivery_report_v2.html'),'functional_fullchip_complete':False}))
if __name__=='__main__':main()
