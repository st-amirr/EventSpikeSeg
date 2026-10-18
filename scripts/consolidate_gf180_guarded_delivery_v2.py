"""Refresh the operational index from finished reset evidence; retain historical artifacts."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def main():
 result=B/'results/gf180_guarded_tile_loaded_reset_duration_v1.json';q=json.loads(result.read_text());d=B/'assembly/full25_locally_decoded_storage_v3';report=d/'delivery_report_v2.html';assert not report.exists()
 status='Observed in the measured repair case' if q['repair_observed'] else 'Still failing or incomplete'
 metrics=(f"The adjusted reset pulse lasts {q['predicted_loaded_reset_width_us']:.3f} microseconds. " + (f"Measured reset: {q['actual_reset_step_v']*1000:.3f} mV; requested: -6.875 mV. Writeback error: {q['writeback_error_vs_actual_column_v']*1000:.3f} mV." if q['completed'] else 'The bounded repair simulation did not finish.'))
 report.write_text('''<!doctype html><meta charset="utf-8"><title>Analog ASIC delivery status</title>
<style>body{font:17px/1.65 system-ui;max-width:1000px;margin:40px auto;padding:0 20px;color:#172234}table{border-collapse:collapse;width:100%}td,th{padding:12px;border:1px solid #d2d7dd;text-align:left}.gap{background:#fff0d5;padding:16px}h1,h2{line-height:1.2}</style>
<h1>EventSpikeSeg analog ASIC: delivery status</h1>
<p class="gap"><strong>The requested full functional layout and per-module simulation package is incomplete.</strong> The current stage is connected module integration.</p>
<table><tr><th>Stage</th><th>Current result</th></tr>
<tr><td>Storage and shared access modules</td><td>Physical layouts exist. Retention and selected access simulations are available, with recorded errors.</td></tr>
<tr><td>One connected neuron update</td><td>'''+status+'''</td></tr>
<tr><td>Whole-model physical assembly</td><td>Storage capacity and 25 representative compute clusters are placed. Global bank service and network connections remain unfinished.</td></tr>
<tr><td>All required module simulations</td><td>Partial coverage. Missing operator and connected-parent results remain explicit in the coverage table.</td></tr>
<tr><td>Article deliverable</td><td>Not complete.</td></tr></table>
<h2>Latest concrete results</h2><p>The guarded compute tile has zero source, flat and GDS DRC violations, with independent exact connectivity for all 759 native primitives. The updated first actor has zero DRC violations and exact connectivity for all 1,357 primitives.</p>
<p>The original connected 230 microsecond simulation finishes but fails subtractive reset. Internal signals show the switch turns on; discharge is too small for the old pulse duration. '''+metrics+'''</p>
<p>This repair uses the measured failing case to calculate one pulse duration. It is calibration evidence, not independent precision validation. Layout, biases and the trained beta reference are unchanged; capture and writeback are delayed to preserve phase order. The duration generator remains external.</p>
<h2>Remaining delivery work</h2><ol><li>Complete shared bank access and compute scheduling across the resident capacity.</li><li>Connect graph operators, parameter programming and control.</li><li>Finish missing module simulations and publish the assembled layout with explicit limitations.</li></ol>
<p>The GDS preserves all 54,630,400 active state identities. Its spacious storage-macro projection is 34,801 mm², not a compact die. Whole-model accuracy and 5 ms service remain unproven.</p>
<h2>Files</h2><ul><li><a href="eventspikeseg140k_locally_decoded_storage_v3.gds">Current assembly GDS</a></li><li><a href="physical_assembly.json">Assembly inventory and exclusions</a></li><li><a href="module_simulation_coverage_v1.json">Module simulation coverage</a></li><li><a href="../../results/gf180_guarded_tile_loaded_reset_duration_v1.json">Measured reset repair result</a></li><li><a href="../../results/gf180_guarded_tile_reset_internal_diagnosis_v1.json">Reset internal signal diagnosis</a></li><li><a href="delivery_report_v1.html">Prior guarded assembly evidence</a></li></ul>''',encoding='utf-8')
 p=R/'docs/project_spec.yaml';b=p.read_bytes()
 updates={'full25_physical_candidate':'artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/physical_assembly.json','article_delivery_report':'artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/delivery_report_v2.html','module_simulation_coverage':'artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/module_simulation_coverage_v1.json','evidence':'artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/independent_bank_identity_readback_v2.json','current_stage':'guarded_connected_update_loaded_reset_repair_global_bank_service_and_graph_binding_incomplete'}
 for key,val in updates.items():
  b,n=re.subn(('  '+key+': [^\\r\\n]+').encode(),('  '+key+': '+val).encode(),b,count=1);assert n==1,key
 b,n=re.subn(rb'  live_sessions: [^\r\n]+',b'  live_sessions: []',b,count=1);assert n==1;p.write_bytes(b)
 note='\n\n## Measured loaded reset repair - 2026-10-11\n\n'+status+'. '+metrics+' This is one donor-derived pulse-duration repair, not independent reset precision acceptance. The complete native reset path turns on correctly; prior pulse was too short under actual loading. No geometry/bias or beta-reference change; post-reset capture/commit delayed30us. Full functional assembly, global bank service, graph/operator binding and missing module simulations remain unfinished. Updated delivery report: artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/delivery_report_v2.html.\n'
 for name in ['ACTIVE_TASKS.md','RESULTS.md','PROGRESS.md','DECISIONS.md']:
  p=R/'docs'/name;p.write_bytes(p.read_bytes()+note.encode())
 print(report);print(status);print(metrics)
if __name__=='__main__':main()
