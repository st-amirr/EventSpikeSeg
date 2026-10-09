"""Audit loop rejection, isolated charge-transfer diagnosis and tracking parking."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic/results'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(p):
    r = json.loads(p.read_text(encoding='utf-8'))
    exceptions = []
    for name, expected in r['sha256'].items():
        if sha(ROOT / name) != expected:
            # Initial netlist-rejected reports recorded the mutable working script
            # as well as its immutable snapshot. Preserve both; audit the archive.
            snaps = [ROOT / n for n in r['sha256'] if 'source_snapshots/' in n and n.endswith('.py')]
            assert name == 'scripts/screen_gf180_source_compliance_isolation.py'
            assert not r['simulation_completed'] and len(snaps) == 1
            assert sha(snaps[0]) == expected
            exceptions.append({'mutable_source': name, 'archived_source': snaps[0].relative_to(ROOT).as_posix(),
                               'archived_sha256': expected})
    return r, exceptions


def row(p):
    r, exceptions = audit(p)
    return {'report': p.relative_to(ROOT).as_posix(), 'sha256': sha(p),
            'completed': r['simulation_completed'], 'settings': r['settings'],
            'measurements': r['measurements'], 'archived_source_resolution': exceptions,
            'failure_class': None if r['simulation_completed'] else
                ('bounded_timeout' if r['simulator_returncode'] == 124 else 'abort_or_incomplete_measurements')}


def main():
    loops = []
    for pattern in ['gf180_cascaded_loop_local_gain_*.json', 'gf180_cascaded_loop_split_comp_*.json']:
        for p in sorted(BASE.glob(pattern)):
            x = row(p)
            assert x['completed']
            m = x['measurements']
            voltage_samples = {k: v for k, v in m.items() if k.startswith(('out_w_', 'out_r_', 'sum_w_', 'sum_r_'))}
            x.update({'operating_point_accepted': False,
                      'rail_or_outside_supply_samples': {k: v for k, v in voltage_samples.items() if v < .05 or v > 3.25},
                      'rejection': 'Output saturation or large baseline/drift invalidates the charge-integrator operating point. Completion is not acceptance.'})
            assert x['rail_or_outside_supply_samples']
            loops.append(x)
    assert len(loops) == 6
    isolation = []
    rejections = []
    for p in sorted(BASE.glob('gf180_source_compliance_isolation_*.json')):
        r, _ = audit(p)
        x = row(p)
        if x['completed']:
            x['idle_subtracted_charge_c'] = r['idle_subtracted_charge_c']
            isolation.append(x)
        else:
            x['failure'] = 'Duplicate voltage-source identifier; netlist rejected before simulation.'
            assert not x['measurements']
            rejections.append(x)
    base = next(x for x in isolation if x['settings']['sum_w_v'] == 1.65
                and x['settings'].get('park_mode', 'vcm') == 'vcm' and not x['settings']['clock_only'])
    for x in isolation:
        x['charge_change_from_original_zero_sum_c'] = [v - b for v, b in zip(x['idle_subtracted_charge_c'], base['idle_subtracted_charge_c'])]
    tracking = []
    for pattern in ['gf180_tracking_park_local_gain_*.json', 'gf180_settled_tracking_park_*.json',
                    'gf180_autozero_tracking_park_*.json']:
        for p in sorted(BASE.glob(pattern)):
            tracking.append(row(p))
    assert len(isolation) >= 7 and len(rejections) == 3 and len(tracking) >= 3
    controls = [x for x in tracking if x['completed'] and x['settings']['preload_differential_v'] == 0
                and not x['settings']['no_events']]
    for x in tracking:
        if x['completed'] and controls and not x['settings']['no_events']:
            # Compare actual same-hierarchy packet increments; inherited old
            # seed29 programming does not establish targets for this new topology.
            controls_same = [c for c in controls if c['report'].rsplit('_src', 1)[1] == x['report'].rsplit('_src', 1)[1]
                             and c['settings'].get('settle_us', 0) == x['settings'].get('settle_us', 0)
                             and c['settings']['max_step_ns'] == x['settings']['max_step_ns']
                             and all(c['settings'][key] == x['settings'][key]
                             for key in ['mismatch_seed', 'cell_order', 'base_widths_us', 'local_gain',
                                         'duration_offset_ns', 'pf_program_levels', 'pf_reference_levels'])]
            if controls_same:
                c = controls_same[0]
                x['packet_change_from_own_zero_state_uv'] = [(x['measurements'][f'eventstep_{i}'] - c['measurements'][f'eventstep_{i}']) * 1e6 for i in range(4)]
                state_change = x['measurements']['signal_before'] - c['measurements']['signal_before']
                if abs(state_change) > .01:
                    x['diagnostic_state_sensitivity_per_packet'] = [v * 1e-6 / state_change
                                                                   for v in x['packet_change_from_own_zero_state_uv']]
                    x['state_sensitivity_scope'] = 'Finite difference at two selected weights and one seed; systematic event-by-event bias, not a Gaussian noise sigma or globally validated model.'
    calibration = None
    cp = BASE / 'gf180_autozero_parking_programming_calibration.json'
    if cp.exists():
        c = json.loads(cp.read_text(encoding='utf-8'))
        for name, h in c['sha256'].items():
            assert sha(ROOT / name) == h, name
        calibration = {'report': cp.relative_to(ROOT).as_posix(), 'sha256': sha(cp),
                       'iterations': c['iterations'], 'scope': c['scope']}
        last = c['iterations'][-1]
        for x in tracking:
            a = x['settings']
            if (x['completed'] and not a['no_events']
                    and x['report'].rsplit('_src', 1)[1] == last['report'].rsplit('_src', 1)[1]
                    and [float(v) for v in a['pf_program_levels'].split(',')][:2] == last['program_v']):
                order = [int(v) for v in a['cell_order'].split(',')]
                if all(v in [0, 1] for v in order):
                    targets = [last['targets_uv'][v] for v in order]
                    x['calibrated_weight_target_error_uv'] = [x['measurements'][f'eventstep_{i}'] * 1e6 - t
                                                              for i, t in enumerate(targets)]
    out = {'stage': 'Source parking charge-transfer diagnosis and native tracking-buffer experiment',
           'rejected_cascaded_loops': loops, 'isolation_cases': isolation,
           'pre_simulation_netlist_rejections': rejections, 'integrated_tracking_cases': tracking,
           'external_autozero_parking_programming_calibration': calibration,
           'interpretation': ['Common-mode receiving-node movement causes little isolated charge change; a differential710uV displacement with fixedVCM parking adds approximately0.105fC.',
                              'Equal-program zero-weight control reproduces the unwanted packet while plateau differential current is near zero. This implicates charge transferred by the switched output/parking network; it does not uniquely separate device capacitances.',
                              'Ideal matching parking is a diagnostic only. Native unity-follower parking reproduces most of that reduction in fixed-voltage isolated fixtures; integrated behavior is reported separately.',
                              'Nominal isolated tests do not transplant prior seed29 calibration, establish total noise, or qualify the complete PLIF.'],
           'alternatives': {'next_candidate': 'Tracking idle parking with an actual native follower shared by the injection lane; preserve original analog state and event semantics.',
                            'conditional_fallback': 'Switched-capacitor weighted charge packets; still requires stable receiving node, switch-charge/noise characterization and original-float replay.',
                            'stopped_branch': 'Blind cascaded-OTA gain and compensation-capacitance scaling.'},
           'native_random_noise_qualified': False, 'combined_layout_qualified': False,
           'weighted_charge_accepted': False, 'complete_PLIF_accepted': False,
           'original_float_accuracy_accepted': False, 'full_5ms_population_service_accepted': False,
           'full_chip_accepted': False}
    p = BASE / 'gf180_tracking_parking_boundary.json'
    p.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(p), 'loops_rejected': len(loops), 'isolation_complete': len(isolation),
                      'integrated': [{'report': x['report'], 'complete': x['completed'],
                                      'state_v': x['measurements'].get('signal_before'),
                                      'changes_uv': x.get('packet_change_from_own_zero_state_uv')} for x in tracking]}, indent=2))


if __name__ == '__main__':
    main()
