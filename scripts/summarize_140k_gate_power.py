import json
import re
from pathlib import Path

root = Path('/workspace')
out = root/'artifacts/ASIC/primitive_characterization/base_140k_inventory'
manifest = json.loads((out/'gate_manifest.json').read_text())
rows=[]
passed=[]
pending=[]
for item in manifest:
    label=item['block']
    block_dir=root/item['result_directory']
    log=(block_dir/f'{label}_simulation.log').read_text()
    if f'PASS {label}:' not in log or 'FATAL' in log:
        pending.append({'block':label,'status':'reference_trace_mismatch; no new power accepted','log':log})
        continue
    annotation=(block_dir/f'{label}_annotation.rpt').read_text()
    missing=int(re.search(r'unannotated\s+(\d+)',annotation).group(1))
    if missing:
        assert label == 'readout' and missing == 2
        details=(block_dir/'readout_unannotated.rpt').read_text()
        assert set(details.split('Unannotated pins:',1)[1].split()) == {'prediction_x_o[0]','prediction_y_o[0]'}
        # Both coordinate outputs are checked as zero by the passing 1x1 test.

    values=re.search(r'^Total\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)',(block_dir/f'{label}_power.rpt').read_text(),re.M)
    internal,switching,leakage,total=map(float,values.groups())
    duration_ps=int(re.search(r'finish called at (\d+)',log).group(1))
    dynamic=internal+switching
    operations={'plif':10,'conv9':128,'readout':1}[label]
    metrics=json.loads((root/'artifacts/OpenROAD/logs/asap7'/item['top']/'checkpoint_exact/6_report.json').read_text())
    item.update(dynamic_w=dynamic,leakage_w=leakage,total_trace_w=total,
                trace_duration_ps=duration_ps,operations=operations,
                dynamic_pj_per_operation=dynamic*duration_ps/operations,
                cell_area_um2=metrics['finish__design__instance__area'],
                die_area_um2=metrics['finish__design__die__area'],
                fmax_mhz=metrics['finish__timing__fmax']/1e6,
                vcd_pins=int(re.search(r'vcd\s+(\d+)',annotation).group(1)),unannotated_pins=missing)
    rows.append(f"| {label} | {item['checks']} | {dynamic*1e6:.3f} | {leakage*1e6:.4f} | {item['dynamic_pj_per_operation']:.4f} | {item['die_area_um2']:.3f} |")
    passed.append(item)
(out/'gate_results.json').write_text(json.dumps(passed,indent=2)+'\n')
(out/'gate_pending.json').write_text(json.dumps(pending,indent=2)+'\n')
text = "# 140k gate-power results from existing routed blocks\n\n"
text += "Primary target: EventSpikeSeg140k v8, epoch 80, seed 17. XL layouts remain secondary preserved evidence.\n\n"
text += "| Block | Checked output snapshots | Dynamic trace power (uW) | Leakage (uW) | Dynamic energy (pJ/operation) | Die footprint (um²) |\n|---|---:|---:|---:|---:|---:|\n" + "\n".join(rows) + "\n\n"
text += "PLIF operation is one bin update; conv9 operation is one nine-term evaluation; readout operation is one ten-bin prediction for one pixel. These synthetic tests include startup/control overhead. PLIF and conv9 have zero unannotated pins. Readout annotates 45,229 pins; the two unannotated one-pixel coordinate outputs are checked as zero in simulation. Functional zero-delay gate simulation supplies activity; retained ODB/SDC/SPEF supply extracted-layout power. No SDF glitch, full-chip power, or real-time throughput claim is made.\n\n"
text += "Gate traces, testbenches, logs and power reports are alongside the existing block results; no separate block implementation or layout flow is introduced. The prior 2.013376 W subtotal is historical partial evidence: its PLIF input-only trace left 12,869 pins unannotated and differs materially from the current gate-VCD measurement.\n\n"
for item in manifest:
    directory = item['result_directory'].split('/')[-1]
    text += f"- [{item['block']} reports](../{directory}/); [existing GDS](../../../OpenROAD/results/asap7/{item['top']}/checkpoint_exact/6_final.gds)\n"
text += "\nReadout passed 49 pre-edge reference checks, including prediction/class, frame completion, backpressure and coordinates. The earlier mismatch was a pre-edge/post-edge testbench sampling error; no RTL, netlist or layout change was needed. See gate_pending.json for any remaining failures. Existing final layouts and useful XL data are retained.\n"
text += "\nHelpers: scripts/prepare_140k_gate_power.py creates testbenches in the existing block folders; scripts/summarize_140k_gate_power.py reads their logs. Use the preserved ASAP7 compatibility models at artifacts/ASIC_XL/activity/enc1_depthwise_1x1_beta48_gate/sim_models/stdcells when compiling the retained 6_final.v netlists. Run each testbench from its block folder, then its <block>_power.tcl in OpenROAD. No new synthesis or routing is needed.\n"
# Illustrative scaling uses existing 140k inventory, never XL state/term counts.
by_label={item['block']:item for item in passed}
if set(by_label)=={'plif','conv9','readout'}:
    inventory=json.loads((out/'inventory.json').read_text())
    assert inventory['model']['actor_count']==25
    assert inventory['model']['logical_plifs']==30_976_000
    counts={'plif':17_740_800,'conv9':3_730_918_400/9,'readout':281_600}
    rates={'plif':200,'conv9':200,'readout':20}
    terms={key:{'instance_multiplier':counts[key],
                'dynamic_w':by_label[key]['dynamic_pj_per_operation']*1e-12*counts[key]*rates[key],
                'leakage_w':by_label[key]['leakage_w']*counts[key]}
           for key in counts}
    estimate={'scope':'three measured block proxies only; not full-chip power',
              'assumption':'synthetic traces representative; dense convolution term scaling; 20 predictions/s',
              'excluded':['adaptation','inhibition','graph/control','top-level clock/routing','spike-sparsity calibration'],
              'blocks':terms,
              'dynamic_w':sum(x['dynamic_w'] for x in terms.values()),
              'leakage_w':sum(x['leakage_w'] for x in terms.values())}
    (out/'gate_scaled_estimate.json').write_text(json.dumps(estimate,indent=2)+'\n')
    text += f"\nIllustrative three-block scaling at 20 predictions/s: {estimate['dynamic_w']:.6f} W dynamic and {estimate['leakage_w']:.3f} W leakage. This uses 17,740,800 ordinary PLIFs, 3,730,918,400 dense actor terms per bin (nine terms per proxy), and 281,600 readout pixels. It excludes adaptation, inhibition, graph/control, top-level clocks/routing and measured spike sparsity. It assumes synthetic block activity and one kernel's per-term cost transfer to the model; these are feasibility proxies, not measured whole-chip power. Leakage is not duty-cycle scaled without an implemented power-gating scheme. See gate_scaled_estimate.json.\n"
(out/'GATE_RESULTS.md').write_text(text)
print(f"Summarized {len(passed)} passing blocks; {len(pending)} pending. Existing layout data unchanged.")


# Append mechanism measurements to the same 140k report, with explicit physical coverage.
mechanism_manifest_path=out/'mechanism_gate_manifest.json'
if mechanism_manifest_path.exists():
    import hashlib
    manifest_m=json.loads(mechanism_manifest_path.read_text())
    status={x['block']:x for x in json.loads((out/'mechanism_gate_status.json').read_text())}
    counts={'inhibition':70400,'penalty_lane':10982400,'square_lane':10982400,
            'commit_lane':10982400,'penalty_direct':92400,'penalty_lower':79200,
            'penalty_upper':39600,'energy64':92400,'energy128':39600}
    accepted=[]; blocked=[]
    for item in manifest_m:
        label=item['block']; directory=root/item['result_directory']
        if status[label]['status']!='power_complete_pending_audit':
            blocked.append(dict(item,status=status[label]['status'])); continue
        sim=(directory/f'{label}_simulation.log').read_text()
        powerlog=(directory/f'{label}_power.log').read_text()
        assert f"PASS {label}: {item['checks']} output checks" in sim and 'FATAL' not in sim
        assert f'POWER_PASS {label}' in powerlog and '[ERROR' not in powerlog
        annotation=(directory/f'{label}_annotation.rpt').read_text()
        missing=int(re.search(r'unannotated\s+(\d+)',annotation).group(1))
        if missing:
            blocked.append(dict(item,status='annotation_incomplete',unannotated_pins=missing)); continue
        values=re.search(r'^Total\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)',(directory/f'{label}_power.rpt').read_text(),re.M)
        internal,switching,leakage,total=map(float,values.groups())
        detailed=item['physical_stage']=='detailed_route'
        checkpoint='6_final' if detailed else '5_1_grt'
        layout=root/'artifacts/OpenROAD/results/asap7'/item['top']/'checkpoint_exact'/f'{checkpoint}.odb'
        assert hashlib.sha256(layout.read_bytes()).hexdigest()==item['layout_sha256']
        report='6_report.json' if detailed else '5_1_grt.json'
        metrics=json.loads((root/'artifacts/OpenROAD/logs/asap7'/item['top']/'checkpoint_exact'/report).read_text())
        prefix='finish' if detailed else 'globalroute'
        duration=int(re.search(r'finish called at (\d+)',sim).group(1))
        assert duration==item['trace_duration_ps']
        energy=(internal+switching)*duration/item['operations']
        item.update(dynamic_w=internal+switching,leakage_w=leakage,
                    dynamic_pj_per_evaluation=energy,
                    trace_duration_ps=duration,
                    vcd_pins=int(re.search(r'vcd\s+(\d+)',annotation).group(1)),unannotated_pins=0,
                    die_area_um2=metrics.get(prefix+'__design__die__area'),
                    cell_area_um2=metrics.get(prefix+'__design__instance__area'),
                    instance_multiplier=counts[label],
                    scaled_dynamic_w=energy*1e-12*counts[label]*200,
                    scaled_leakage_w=leakage*counts[label],
                    netlist_sha256=hashlib.sha256((root/item['netlist']).read_bytes()).hexdigest())
        accepted.append(item)
    result={'scope':'140k existing mechanism blocks; bounded small-sample synthetic proxies',
            'accepted':accepted,'pending':blocked,
            'scaled_mechanism_dynamic_w':sum(x['scaled_dynamic_w'] for x in accepted),
            'scaled_mechanism_leakage_w':sum(x['scaled_leakage_w'] for x in accepted)}
    (out/'mechanism_gate_results.json').write_text(json.dumps(result,indent=2)+'\n')
    text=(out/'GATE_RESULTS.md').read_text()+'\n## Inhibition and adaptation — 2026-09-22\n\n'
    text+='Reused the existing layouts. Each case checks the sample count shown below, using evenly spaced samples from its original checkpoint-derived synthetic pool. The 4/8/16-sample cases are limited smoke checks with especially uncertain energy estimates; sampling is approximately population-weighted; it is not a dataset activity measurement. Global-route entries use estimated routing parasitics and have no completed detailed-route GDS claim. All accepted cases have zero unannotated pins.\n\n'
    text+='| Block / activity role | Physical stage | Checks | Dynamic pJ/evaluation | Leakage uW |\n|---|---|---:|---:|---:|\n'
    for x in accepted:
        text+=f"| {x['block']} | {x['physical_stage']} | {x['checks']} | {x['dynamic_pj_per_evaluation']:.4f} | {x['leakage_w']*1e6:.4f} |\n"
    text+=f"\nAccepted {len(accepted)}/9 activity cases. Three penalty-reducer activity roles share one physical design. Pending: {', '.join(x['block']+': '+x['status'] for x in blocked) or 'none'}.\n"
    text+=f"\nUsing the existing 140k instance counts at 200 bin updates/s, these mechanism-only proxies sum to {result['scaled_mechanism_dynamic_w']:.6f} W dynamic and {result['scaled_mechanism_leakage_w']:.3f} W leakage. This is not full-chip power: mechanism wrappers are combinational and omit their surrounding resident state/learned-beta update circuitry, while graph/control, clock distribution, full-chip routing and measured spike sparsity also remain uncovered. Do not present the three-block plus mechanism subtotal as complete neuron or chip coverage. Area/leakage for configuration-input lane macros can change when checkpoint constants are tied during integration.\n"
    text+='\nThe source indices, layout/netlist hashes, physical stages and per-block multipliers are in mechanism_gate_manifest.json and mechanism_gate_results.json. Tap cells were omitted only from simulation exports; original ODBs and XL data were not changed.\n'
    (out/'GATE_RESULTS.md').write_text(text)
    print(f'Mechanisms: {len(accepted)} accepted, {len(blocked)} pending.')
