"""Consolidate current physical evidence without relabeling partial simulations as passes."""
from pathlib import Path
import collections, hashlib, html, json, re

R = Path(__file__).resolve().parents[1]
B = R / 'artifacts/analog_asic'
D = B / 'assembly/full25_external_bank_service_v5'

def read(p):
    return json.loads(p.read_text())

def main():
    mf = D / 'physical_assembly.json'
    m = read(mf)
    groups = read(D / 'independent_actor_geometry_equivalence_v2.json')
    drc = {}
    for ix in [0, 2, 6, 12]:
        folder = (f'actor_{ix:02d}_external_service_DRC_only_v1' if ix in [2, 12]
                  else f'actor_{ix:02d}_external_service_v5')
        p = D / 'verification' / folder / 'qualification_attempt.json'
        q = read(p)
        drc[str(ix)] = {'report': p.relative_to(R).as_posix(),
                        'native_full_drc_count': q['full_parent_drc_count']}
    exact = read(D / 'verification/actor_00_external_service_v5/parent_exact_connectivity_attempt.json')
    caps = read(D / 'verification/actor_00_external_service_fullcap_v1/qualification.json')
    assert exact['independent_connectivity_accepted'] and caps['full_cap_extraction_completed']
    stem = 'gf180_external_actor_native_neuron_update_clock10ns_v2'
    latest = B / 'results' / (stem + '.json')
    assert latest.exists(), 'Wait for the focused case to terminate before publishing.'
    sim = read(latest)
    roundtrip = B / 'results/gf180_external_actor_restore_writeback_klu_v2.json'
    prior = read(roundtrip)
    assert prior['completed']
    inventory = dict(collections.Counter(p['cell'] for a in m['actor_regions'] for p in a['modules']))
    cov = read(B / 'assembly/full25_external_bank_service_v4/module_simulation_coverage_v2.json')
    cov['current_assembly'] = mf.relative_to(R).as_posix()
    cov['current_direct_actor_module_inventory'] = inventory
    cov['historical_module_row_placement_counts_are_not_current_inventory'] = True
    cov['actor_geometry_groups'] = groups
    cov['current_representative_DRC'] = drc
    cov['latest_actor_parent_integration'] = {
        'physical_revision': 5, 'native_primitives': 2362, 'routing_C_branches': 17268,
        'exact_primitive_graph_accepted': True,
        'latest_selected_neuron_case': sim,
        'previous_completed_storage_roundtrip_revision': 4,
        'previous_completed_storage_roundtrip': prior,
        'scope': 'Firstactor exact proof has2362 primitives; inherited1191 prose is stale. '
                 'Native Netgen is not claimed clean. V4 completed roundtrip is retained as V4 evidence. '
                 'V5 fresh capacitances are distinct. Other geometry groups do not inherit firstactor connectivity or nominal.'}
    updates = {
        'All original resident identities physically included': ('verified_capacity',
            '54,630,400 distinct active analog states;866005 raw-plane bank equivalents plus75 actor bank equivalents. Capacity does not imply serviced population.'),
        'Analog bank access': ('selected_service_complete_global_binding_missing',
            '192 physical sites per actor connected to compute/service;4800 total. Remaining866005 raw-plane banks have local row decode but no global shared service binding.'),
        'Signed weight to charge': ('native_parent_partial_trace',
            'V5 firstactor exact2362 primitives and17268 complete native routingC. Native weighted positive injection observed; pulse width/weight distribution and full cycle remain separately reported.'),
        'Learned beta/state update': ('completed_imperfect_module_partial_parent',
            'Existing complete tile cycle retained with12.396mV beta residual. Native V5 beta phase and negative state step observed; no precision sweep.'),
        'Decision and subtractive reset': ('completed_imperfect_tile_parent_case_separate',
            'Tile260us complete: reset-6.722mV vs-6.875mV requested; donor-derived23.614us duration. Latest external-storage parent case reported independently.'),
        'Full-chip physical/electrical verification': ('representative_DRC_complete_fullchip_incomplete',
            'Four V5 emitted geometry groups cover25actors:24 reuse DRC0 representative geometry;stem oneM5 spacing violation. Firstactor exact2362 primitive proof only; larger-parent exact extraction incomplete. No top-level DRC/LVS claim.'),
        'Autonomous categorical control': ('native_children_complete_full_scheduler_missing',
            'Native event and bin controllers have child results. Connected case uses external nonuniform clock and completion fixtures. Higher-bank scheduler and graph protocol remain unbound.'),
        '5ms and original-float accuracy': ('unmeasured_article_limitations',
            'No full-population5ms or original-float inference acceptance. Document limitations; do not delay missing layout/functions for precision tuning.')}
    for row in cov['requirements']:
        if row['requirement'] in updates:
            row['status'], row['evidence_and_gap'] = updates[row['requirement']]
    cov['assembly_full_function_accepted'] = False
    cov['coverage_basis'] = 'Preserve historical107 characterization rows; current direct actor placements and integration evidence are separate explicit fields. Imperfect completed runs count as simulations, not accuracy passes.'
    cp = D / 'module_simulation_coverage_v1.json'
    assert not cp.exists()
    cp.write_text(json.dumps(cov, indent=2) + '\n')
    checklist = [
        ('Reusable modules', 'Available', '20 module sets,84 characterization assemblies; preserve measured imperfect results.'),
        ('Analog state capacity', 'Laid out', '54,630,400 distinct states retained in actual hierarchical GDS.'),
        ('Selected storage/compute service', 'Demonstrated in V4', '120us native roundtrip completed;34.63mV state change retained. V5 neuron-cycle status below.'),
        ('Actor layout variants', 'DRC reviewed', 'Four representatives cover25 actor geometries:24 DRC0;stem one spacing violation. Firstactor exact2362 primitive graph.'),
        ('All-bank service', 'Missing', 'Bind higher bank selection, shared readout and writeback to866005 remaining plane banks.'),
        ('Network and parameters', 'Missing connections', '54 graph corridors exist; operators/endpoints, parameter programming and adaptation plane service remain incomplete.'),
        ('Remaining module simulation', 'Incomplete', 'SUM128 final nominal, full RMS128 reduction and connected adaptation/readout functions remain.'),
        ('Full ASIC deliverable', 'Incomplete', 'Full connected layout and per-module coverage are the completion target; precision optimization follows.')]
    rows = ''.join('<tr><td>'+html.escape(a)+'</td><td>'+html.escape(b)+'</td><td>'+html.escape(c)+'</td></tr>' for a,b,c in checklist)
    completed = sim.get('completed', False)
    cycle = ('Completed; inspect measured function/error fields.' if completed else
             'Incomplete: reached %.3fus of180us; retained as partial evidence.' % (sim.get('last_time_s',0)*1e6))
    report = D / 'delivery_report_v1.html'
    assert not report.exists()
    report.write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>Analog ASIC delivery status</title>
<style>body{font:16px system-ui;max-width:1100px;margin:40px auto;color:#183042;padding:0 24px}h1{font-size:30px}table{border-collapse:collapse;width:100%}td,th{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #ccd6df}th{background:#edf3f8}.stage{padding:16px;background:#edf3f8;border-left:5px solid #256884}a{color:#155fa0}code{word-break:break-all}</style>
<h1>EventSpikeSeg140k analog ASIC</h1><p>GF180 · original epoch58 float model · article research implementation · 12 October2026</p>
<p class="stage"><b>Stage: module integration and full-layout connections.</b> A full connected ASIC is not complete. Measured precision errors are retained while missing functions and wiring are finished.</p>
<table><tr><th>Deliverable</th><th>Stage</th><th>Evidence / remaining work</th></tr>'''+rows+'''</table>
<h2>Latest connected case</h2><p>'''+html.escape(cycle)+''' Native V5 firstactor:2362 primitives,17268 verified routing-capacitance branches. Only sequencer clock edges changed100ns to10ns in the focused repair. This case is separate from the completed V4 storage roundtrip.</p>
<h2>Current physical revision</h2><p>V5 moves service escape wires into a clear left gutter after native V4 larger-actor extraction exposed signal/supply shorts. V5 larger-parent extraction remains incomplete; partial files are not connectivity passes.</p>
<p>Download <a href="eventspikeseg140k_external_bank_service_v5.gds">current hierarchical GDS</a> (23.94MB), <a href="physical_assembly.json">physical inventory</a>, <a href="module_simulation_coverage_v1.json">simulation coverage</a>, <a href="independent_actor_geometry_equivalence_v2.json">geometry groups</a>.</p>
<h2>Area and timing scope</h2><p>The accepted1215mm² figure is a conditional capacitor-plate estimate. The spacious storage/decoder atlas is not a compact die. Full-chip area,5ms population service and trained-model accuracy are unmeasured. These limits must accompany article results.</p></html>''',encoding='utf8')
    note = ('\n\n## Article delivery priority and current revision - 2026-10-12\n\n'
            'User accepts imperfect results: finish connected layout and per-module simulations first; retain measured errors and defer precision optimization. '
            'V5 service escapes moved to a clear left gutter after V4 larger-actor supply/signal shorts were found. All54,630,400 state identities preserved. '
            'Four recursively audited geometry groups cover25actors;24 actor geometries inherit representative DRC0,stem retains oneM5 spacing violation. '
            'Firstactor exact2362 primitive graph and fresh17268 routingC pass; larger-parent exact extraction incomplete and partialEXT rejected. '
            'Latest180us native neuron case: '+cycle+' '
            'Full global bank service,graph/operator/parameter bindings and remaining module functions are still missing. '
            'Current delivery report: '+report.relative_to(R).as_posix()+'.\n')
    for name in ['RESULTS.md','PROGRESS.md','DECISIONS.md']:
        p=R/'docs'/name;p.write_bytes(p.read_bytes()+note.encode())
    p=R/'docs/ARCHITECTURE.md';p.write_bytes(p.read_bytes()+('\n\n## External service routing revision5 - 2026-10-12\n\nNew service M4 spines are outside macro interiors in a reserved left gutter. This repairs V4 RMS-variant hidden supply/signal crossings;firstactor V4 measurements remain scoped toV4. V5 retains the same original analog identities,qualified child modules and analog service bindings. Recursive actual-GDS equivalence establishes four representative geometry groups,not identical parameters. Hierarchical capacity and192 serviced sites peractor are separate coverage.\n').encode())
    p=R/'docs/ACTIVE_TASKS.md';b=p.read_bytes()
    b,n=re.subn(rb'\| Full model \|[^\r\n]+', b'| Full model | V5 hierarchical GDS23.94MB preserves54,630,400states. Four geometry groups:24actor layouts reuse DRC0 representatives;stem has one spacing violation. Firstactor exact2362 primitives/17268 routingC;4800sites serviced,remaining866005plane banks and global graph unbound. |',b,count=1);assert n==1
    b=b.replace(b'full25_external_bank_service_v4/delivery_report_v2.html',report.relative_to(R).as_posix().encode(),1)
    p.write_bytes(b+note.encode())
    p=R/'docs/project_spec.yaml';b=p.read_bytes()
    changes={'current_stage':'article_layout_integration_missing_global_bindings_precision_refinement_deferred',
             'full25_physical_candidate':mf.relative_to(R).as_posix(),
             'article_delivery_report':report.relative_to(R).as_posix(),
             'module_simulation_coverage':cp.relative_to(R).as_posix(),'evidence':latest.relative_to(R).as_posix()}
    for k,v in changes.items():
        b,n=re.subn(('  '+k+': [^\\r\\n]+').encode(),('  '+k+': '+v).encode(),b,count=1);assert n==1,k
    b,n=re.subn(rb'(  latest_experiment:\r?\n    report: )[^\r\n]+',lambda x:x[1]+latest.relative_to(R).as_posix().encode(),b,count=1);assert n==1
    p.write_bytes(b)
    print(json.dumps({'report':str(report),'latest_neuron_case_completed':completed,'full_chip_complete':False},indent=2))

if __name__=='__main__':main()
