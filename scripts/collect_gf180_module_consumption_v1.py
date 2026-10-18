"""Collect completed representative native power/energy evidence for the article."""
from pathlib import Path
import json,datetime,sys,re,zipfile
import measure_gf180_module_consumption_v1 as m
R=m.R;B=m.B;O=m.O
sets=[['membrane_cell_v2'],['plif_core_fast_sources'],['signed_injector_sources'],['control_gates_sources'],['transfer_gate'],['sampled_decision_v2'],['weight_duration_sources','weight_duration_fast_sources'],['inhibition_sources','inhibition_fast_sources'],['affine_subtractor_v2'],['resident_adaptation_sources','resident_adaptation_fast_sources'],['adaptation_io_sources','adaptation_io_fast_sources'],['class_current_io_sources','class_current_io_fast_sources'],['six_class_readout_sources','six_class_readout_fast_sources'],['event_sequencer_sources','event_sequencer_fast_sources'],['bin_sequencer_sources','bin_sequencer_fast_sources'],['page_frontend_fast_sources'],['bias_reference_fast_sources'],['square_kernel_fast_sources']]
rows=[];sources={}
def evidence(p):sources[m.rel(p)]=m.sha(p);return m.rel(p)
for tags in sets:
 for tag in tags:
  p=O/tag/'consumption.json'
  if not p.exists():continue
  j=json.loads(p.read_text())
  if not j.get('completed'):continue
  ep=evidence(p)
  for a in j['instances']:
   for w in a['windows']:
    rows.append(dict(cell=a['cell'],instance=a['instance'],window=w['name'],duration_s=w['duration_s'],VDD_mean_power_W=w['VDD_mean_power_W'],VDD_energy_J=w['VDD_energy_J'],measured_positive_import_J=w.get('positive_terminal_import_energy_J',w.get('measured_source_positive_energy_J')),basis='native transient, one physical instance',evidence=ep,scope=j['scope']))
  break
items=[('gf180_bank_pair_shared_reader_v1_native_two_bank_one_reader_v1','gf180_bank_pair_shared_reader_v1','one128-state bank pair and shared reader; external analog/clock/reference/master energy excluded'),('gf180_adaptation_sum64_threshold_v2_fullcap_native_add_clip_src5ef4294278f4','gf180_adaptation_sum64_threshold_v2','one64-input adaptation sum/clip; ideal inputs and bias master excluded'),('gf180_adaptation_sum128_threshold_v2_native_primitives_nominal_src7b90b512583f','gf180_adaptation_sum128_threshold_v2','one128-input adaptation sum/clip; ideal inputs and bias master excluded'),('gf180_underplate_biased_bank8x8_v1_native_select_write_hold_read_srcaa37c91093be','gf180_underplate_biased_bank8x8_v1','one64-state native bank; independent DATA/control/reference/master energy excluded'),('gf180_page1024_read_frontend_partition_v1_native_A_B_A','shared_reader_page1024_v1','decoder/mux/reader partition and36 external native command inverters; excludes eight storage children, uses frozen RAW fixtures. Not full1024-state-page power.'),('gf180_decoded_shared_compute_tile_v2_native_selected_row_cycle_v1','gf180_decoded_shared_compute_tile_v2','one64-state compute tile including external native command drivers on VDD; independent analog/reference/master energy excluded. Not one PLIF or one membrane.')]
for stem,cell,scope in items:
 p=B/'results'/(stem+'.json');j=json.loads(p.read_text());raw=p.with_suffix('.raw');dat=p.with_suffix('.dat')
 if raw.exists():w=m.Trace(raw);t=w.t;current=w.col('i(vdd)');trace=raw
 else:
  with dat.open() as f:
   head=f.readline().lower().split();idx=head.index('i(vdd)');t=[];current=[]
   for line in f:
    if line.strip():a=line.split();t.append(float(a[0]));current.append(float(a[idx]))
  trace=dat
 power=[-3.3*i for i in current];dt=t[-1]-t[0];energy=m.integral(t,power,t[0],t[-1]);rows.append(dict(cell=cell,instance='one physical shared module/partition',window='existing_completed_nominal_trace',duration_s=dt,VDD_mean_power_W=energy/dt,VDD_energy_J=energy,basis='reused native transient supply current',evidence=evidence(p),trace=evidence(trace),scope=scope+' '+j.get('scope','')))
p=B/'results/gf180_formatted_energy64_v3_native_hierarchy_dc_src06716ac6c5d8.json';j=json.loads(p.read_text())
for a in j['cases']:rows.append(dict(cell='gf180_formatted_energy64_v3',instance='one64-channel formatted RMS module',window=a['case'],duration_s=None,VDD_mean_power_W=a['supply_power_w'],VDD_energy_J=None,basis='native hierarchy DC supply power',evidence=evidence(p),scope=j['scope']+' No transient energy or external master-generation power asserted.'))
p=B/'results/gf180_energy_mean_root128_v1_three_transient_srcc9c7ea27b3b8.json';j=json.loads(p.read_text())
for a in j['cases']:rows.append(dict(cell='gf180_energy_mean_root128_v1',instance='one128-channel unformatted RMS reducer',window=a['case'],duration_s=None,VDD_mean_power_W=3.3*a['supply_current_a'],VDD_energy_J=None,basis='native transient settled supply sample',evidence=evidence(p),scope=j['scope']))
for name in ['full25_packet_fabric_v1','full25_actor_ingress_v2','full25_accumulation_dispatch_v1']:
 p=B/'assembly'/name/'physical_macro.json';j=json.loads(p.read_text());q=j['final_metrics'];rows.append(dict(cell=j['design'],instance='one routed shared categorical macro',window='ORFS default activity estimate',duration_s=None,VDD_mean_power_W=q['finish__power__total'],VDD_energy_J=None,internal_power_W=q['finish__power__internal__total'],switching_power_W=q['finish__power__switching__total'],leakage_power_W=q['finish__power__leakage__total'],basis='routed OpenROAD/OpenSTA library power estimate; not transistor transient',evidence=evidence(p),scope=j['timing_voltage_scope']+' Inherited ORFS clock/activity assumptions; no measured energy per packet/event asserted.'))
invpath=O/'consumption_inventory.json';inv=json.loads(invpath.read_text());covered={a['cell'] for a in rows};coverage=[]
for f in inv['families']:
 c=f['cell'];key='single_resident_membrane_cell' if c.startswith('single_cell_of_') else c;coverage.append(dict(cell=c,covered=key in covered,basis='partition and leaf characterization; full1024 connected-page power unavailable' if c=='shared_reader_page1024_v1' else 'representative native module/element supply characterization with listed exclusions'))
gaps=[a['cell'] for a in coverage if not a['covered']];complete=not gaps
out=dict(representative_consumption_characterization_complete=complete,required_families=len(coverage),covered_families=len(coverage)-len(gaps),remaining_families=gaps,coverage=coverage,rows=rows,source_sha256=sources,units=dict(power='W',energy='J',duration='s'),scope='Article representative consumption per distinct element and shared physical module, not every replicated instance. Native operation windows, DC/settled RMS samples and routed digital library estimates are distinguished. Full1024-page power, shared reference/phase generation losses and whole-chip power remain unqualified.',caveats=['VDD energy includes standing bias during each stated window. It is not always total internal dissipation.','Positive terminal imports may include reactive charging; signed net terminal energy includes changes of stored energy.','Very small hold/off currents depend on model/gmin/numerical tolerances. MIM zero model leakage is not a silicon leakage guarantee.','Do not sum overlapping core/submodule/bank/whole-tile rows or multiply shared cores/readers by logical membrane count.','Independent ideal-source measurements isolate one physical module; unmeasured native-driven/current-master ports are identified in their detailed reports.','Fast nominal runs use KLU/reltol1e-4/vntol1e-7 and adaptive maximum step. Failed/timeout attempts are preserved and excluded.'],updated_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
summary=O/'consumption_summary.json';summary.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
if complete:
 for f in inv['families']:f['consumption_status']='characterized_representative_supply_with_explicit_exclusions' if f['cell']!='shared_reader_page1024_v1' else 'characterized_frontend_partition_plus_storage_leaf_not_full_page_power'
 inv.update(per_element_consumption_complete=True,completion_definition=out['scope'],consumption_summary=m.rel(summary));invpath.write_text(json.dumps(inv,indent=2)+'\n',encoding='utf-8')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');zp=B/'documentation_history'/('project_docs_before_consumption_delivery_'+stamp+'.zip')
 with zipfile.ZipFile(zp,'x',zipfile.ZIP_DEFLATED) as z:
  for n in ['ACTIVE_TASKS.md','AGENTS.md','ARCHITECTURE.md','DECISIONS.md','PROGRESS.md','RESULTS.md','project_spec.yaml']:z.write(R/'docs'/n,'docs/'+n)
 section='''## Representative per-element consumption delivered — 2026-10-14

The article layout and representative consumption characterization are complete under the user's clarified scope. `artifacts/analog_asic/results/module_consumption_v1/consumption_summary.json` covers all22 required element/module families, plus native capacitor, sampled decision, bias/normalization kernels and the three shared categorical macro estimates. One physical PLIF core, one3T+MIM resident cell, signed injector, adaptation, inhibition, normalization, readout, access and controls are distinguished. Each transient row states its window and supply energy/power; detailed reports retain input-port accounting. Core beta/decision/reset windows are measurements of the whole core during those phases, not standalone leaf powers.

Coverage combines newly completed native transients, reused complete rail-current traces, native RMS DC/settled samples and explicitly labeled routed-library digital power estimates. Shared1024-state reader power is partition/leaf characterization, not a completed full connected-page power simulation. Bias/reference/phase-generator overhead outside the measured boundary remains excluded unless stated. No measured full-chip power, calibrated behavior or5ms full-population deadline is claimed. Do not sum overlapping modules or replicate shared-core cost per logical membrane. Further circuit optimization is optional.

'''
 for n in ['ACTIVE_TASKS.md','AGENTS.md']:
  p=R/'docs'/n;s=p.read_text(encoding='utf-8');s=s.replace('## Active remaining task: consumption per element type — 2026-10-14','## Historical consumption task definition — 2026-10-14',1).replace('per-element consumption is not yet complete.','Representative consumption delivery is now recorded above; this paragraph preserves the task definition.',1);p.write_text(section+s,encoding='utf-8',newline='\n')
 for n in ['ARCHITECTURE.md','DECISIONS.md','PROGRESS.md']:
  p=R/'docs'/n;p.write_text(p.read_text(encoding='utf-8')+'\n\n'+section,encoding='utf-8',newline='\n')
 p=R/'docs/RESULTS.md';s=p.read_text(encoding='utf-8')+'\n\n'+section+'### Representative consumption table\n\n| Circuit / instance | Window | Mean VDD power (uW) | VDD energy (pJ) | Basis |\n|---|---|---:|---:|---|\n'
 for a in rows:
  energy='—' if a['VDD_energy_J'] is None else f"{a['VDD_energy_J']*1e12:.6g}";s+=f"| {a['cell']} / {a['instance']} | {a['window']} | {a['VDD_mean_power_W']*1e6:.6g} | {energy} | {a['basis']} |\n"
 s+='\nThe membrane cell write/read total positive terminal imports are reported in the JSON in addition to VDD, which alone omits DATA/clock energy. Very small hold currents are numerical/model-dependent. Digital library estimates retain their original activity assumptions.\n';p.write_text(s,encoding='utf-8',newline='\n')
 p=R/'docs/project_spec.yaml';s=p.read_text(encoding='utf-8').replace('  remaining_task: per_element_power_and_energy_characterization','  remaining_task: none_for_article_layout_and_representative_consumption_scope',1).replace('  per_element_consumption_complete: false','  per_element_consumption_complete: true\n  per_element_consumption_summary: artifacts/analog_asic/results/module_consumption_v1/consumption_summary.json\n  consumption_coverage_basis: native_transients_reused_rails_DC_samples_and_labeled_library_estimates\n  full1024_connected_page_power_measured: false\n  measured_full_chip_power_available: false',1).replace('  status: article_layout_delivered_consumption_characterization_active','  status: article_layout_and_representative_consumption_delivered',1);p.write_text(s,encoding='utf-8',newline='\n');sys.path.insert(0,str(B/'tools/yaml_validation'));import yaml;yaml.safe_load(s)
print(json.dumps(dict(complete=complete,covered=len(coverage)-len(gaps),required=len(coverage),remaining=gaps,rows=len(rows),summary=str(summary)),indent=2))
