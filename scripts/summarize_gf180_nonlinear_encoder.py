"""Audit physical encoder experiments without inferring SNN or chip acceptance."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = {Path(__file__)}
    cases = []
    dynamic_reports = []
    for path in sorted((BASE / 'results').glob('gf180_nonlinear_encoder_*.json')):
        report = json.loads(path.read_text())
        if 'command_arguments' not in report:
            continue
        sources.add(path)
        snapshot = ROOT / report['source_snapshot']
        if digest(snapshot) != report['sha256']['scripts/screen_gf180_nonlinear_encoder.py']:
            raise ValueError(f'Source snapshot mismatch: {path}')
        sources.add(snapshot)
        for name, expected in report['sha256'].items():
            if name == 'scripts/screen_gf180_nonlinear_encoder.py':
                continue  # Immutable historical source checked above.
            source = ROOT / name
            if digest(source) != expected:
                raise ValueError(f'Input provenance mismatch: {source}')
            sources.add(source)
        for qualification in report['qualified_layout_components']:
            cell = qualification['cell']
            for name, expected in qualification['sha256'].items():
                source = BASE / 'layout' / cell / name
                if digest(source) != expected:
                    raise ValueError(f'Physical view provenance mismatch: {source}')
                sources.add(source)
        case = {key: report.get(key) for key in ['simulation_completed',
                'simulator_returncode', 'operating_point_solver_warning', 'analysis', 'dc_source']}
        case['settings'] = report['command_arguments']
        case['dc_reference_has_solver_warning'] = (json.loads((ROOT/report['dc_source']).read_text()).get('operating_point_solver_warning',False) if report.get('dc_source') else None)
        case['control_window_peak_to_peak_v'] = max((row['controlmax']-row['controlmin'] for row in report.get('rows',[]) if 'controlmax' in row),default=None)
        case['dynamic_only_without_dc'] = report['command_arguments'].get('transient_without_dc',False)
        case['evidence'] = path.relative_to(ROOT).as_posix()
        case['scope'] = report['scope']
        case['late_window_measured'] = bool(report.get('rows') and 'late_window_peak_to_peak_uv' in report['rows'][0])
        cases.append(case)
        if report.get('simulation_completed') and report['command_arguments'].get('transient_without_dc'):
            dynamic_reports.append((path,report))
    comparisons=[]
    physical_keys=['corner','temp_c','span_v','reference_ua','buffer_reference_ua','physical_compensation_controller','physical_controller_threshold_scale','physical_controller_hysteresis','compensation_bank_clamp','input_feedback_mim_count','mirrored_feedback','self_biased_span','calibration_na','source_lifted','lift_reference_na','lift_reference_node','switched_compensation','minimum_feedback_size_um','feedback_scale']
    for path,report in dynamic_reports:
        settings=report['command_arguments']
        candidates=[(rp,rr) for rp,rr in dynamic_reports if rr['command_arguments'].get('phase_us')==1000 and all(rr['command_arguments'].get(key)==settings.get(key) for key in physical_keys) and rr['qualified_layout_components']==report['qualified_layout_components']]
        if not candidates:continue
        reference_path,reference=max(candidates,key=lambda item:item[0].stat().st_mtime)
        if len(report['rows'])!=len(reference['rows']):continue
        if any(a['input_current_na']!=b['input_current_na'] for a,b in zip(report['rows'],reference['rows'])):continue
        comparisons.append({'evidence':path.relative_to(ROOT).as_posix(),'long_hold_reference':reference_path.relative_to(ROOT).as_posix(),'phase_us':settings['phase_us'],'max_step_ns':settings.get('transient_max_step_ns',50),'maximum_late_endpoint_difference_uv':max(abs(a['late']-b['late'])*1e6 for a,b in zip(report['rows'],reference['rows'])),'zero_return_minus_initial_uv':(report['rows'][-1]['late']-report['rows'][0]['late'])*1e6,'scope':'History-dependent deterministic trajectory compared to a longer hold, not trusted DC error or physical state accuracy. Reference max timestep and solver warnings remain explicit in reports.'})
    result = {
        'cases': cases, 'case_count': len(cases),
        'dynamic_long_hold_comparisons': comparisons,
        'simulations_completed': sum(case['simulation_completed'] for case in cases),
        'physical_view_and_input_provenance_verified': True,
        'dc_reports_without_solver_fallback': sum(case['simulation_completed'] and not case['settings'].get('noise') and not case['settings'].get('transient') and not case['operating_point_solver_warning'] for case in cases),
        'transients_using_dc_with_solver_warning': sum(case['dc_reference_has_solver_warning'] is True for case in cases),
        'encoder_accepted': False, 'physical_state_accepted': False,
        'original_float_accuracy_accepted': False, 'full_chip_accepted': False,
        'scope': 'Separate routed components with capacitance extraction. DC current compression and deterministic current-step settling only. Completion, monotonicity and a single late sample do not establish acceptance. Historical scope strings mentioning two-MOS feedback must be interpreted with explicit mirrored_feedback settings and embedded six-MOS qualification. No physical inverse, integrated event/state updates, sampled noise, calibration, combined layout, resistance extraction, silicon leakage or full population service.',
        'next_step': 'Resolve physical adaptive-compensation stability and DC solver fallback without treating untrusted reference curves as settling evidence; implement inverse and exact signed-charge PLIF state interface before model replay and assembled layout expansion.',
        'sha256': {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(sources)},
    }
    target = BASE / 'results/gf180_nonlinear_encoder_boundary.json'
    target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'evidence': str(target), 'case_count': len(cases),
                      'simulations_completed': result['simulations_completed']}))


if __name__ == '__main__':
    main()
