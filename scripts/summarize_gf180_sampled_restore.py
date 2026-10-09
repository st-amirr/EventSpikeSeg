"""Collect deterministic physical sampler/restore evidence without acceptance claims."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'


def main():
    sources = [Path(__file__)]
    cases = []
    for path in sorted((BASE / 'results').glob('gf180_sensor_zero_servo_*sampledrestore*.json')):
        report = json.loads(path.read_text())
        sources.append(path)
        case = {key: report.get(key) for key in [
            'simulation_completed','simulator_returncode','simulation_timeout_s', 'local_mismatch_enabled', 'seed', 'corner', 'temperature_c',
            'hold_mim_count', 'physical_offset_storage_subtraction', 'offset_mim_count',
            'offset_extra_mim_count', 'total_offset_mim_count',
            'combined_routed_offset_module', 'bottom_plate_stagger_ns', 'offset_acquire_us',
            'offset_refresh_on_read', 'offset_dedicated_read', 'combined_routed_offset_short_split',
            'offset_isolated_routes', 'integration_method', 'max_step_ns', 'diagnostic_ideal_charge_fc',
            'sample_acquisition_us','sample_switch_nf_width_um', 'scheduled_slot_us', 'physical_sample_buffer','physical_acquisition_buffer', 'offset_reversed_plates',
            'restore_extra_us','write_feedback_duration_us',
            'reference_extra_us','reference_read_duration_us','reference_calibration_acquisition_us',
            'offset_dummy_bottom', 'offset_refresh_each_slot','offset_continuous_use','offset_continuous_clamp_startup_only', 'physical_zero_reference_cells', 'energy_measured',
            'offset_split_sample','offset_sample_bottom_advance_ns',
            'offset_switch_width_scale','offset_sample_dummy_bottom','offset_sample_clock_trim_um','offset_sample_clock_trim_net',
            'calibration_dummy_nf_width_um',
            'writer_reference_current_ua', 'verify_next_read',
            'writer_input_pair_width_um',
            'follow_delay_from_last_slot_start_us', 'minimum_idle_hold_after_hold_reset_us']}
        case['source'] = path.relative_to(ROOT).as_posix()
        # Early trim reports retain settings in their recorded command arguments.
        for key in ['offset_sample_clock_trim_um','offset_sample_clock_trim_net']:
            if case[key] is None:
                case[key]=report.get('command_arguments',{}).get(key)
        if case['offset_sample_clock_trim_um'] and case['offset_sample_clock_trim_net'] is None:
            case['offset_sample_clock_trim_net']='SAMPLEB'
        rows = report['rows']
        mean_program=report.get('statistics',{}).get('program_mean_v')
        if mean_program is not None:
            case['initial_program_mean_minus_setpoint_mv']=(mean_program-report.get('setpoint_v',1.2))*1000
            case['coarse_initialization_within_5mv']=abs(case['initial_program_mean_minus_setpoint_mv'])<=5
            case['coarse_sanity_scope']='5mV initialization screen detects large programming failure; not an analog accuracy tolerance or model acceptance.'
        if report.get('energy_measured'):
            case['energy_statistics'] = report.get('statistics', {})
            energy = report.get('statistics', {}).get('energyserviceperiod_mean_pj')
            if energy is not None:
                if case.get('coarse_initialization_within_5mv'):
                    case['conditional_full_inventory_restore_vdd_w'] = energy*1e-12*30976000/.005
                case['power_estimate_scope'] = 'Conditional repeat of continuously biased measured module service over all30,976,000states every5ms; excludes full PLIF/event processing and external reference/control generation. Not accepted full-chip power.'
        if report['simulation_completed'] and rows:
            for key in ['sample_error_mv', 'roundtrip_bus_error_mv']:
                case[key + '_range'] = [min(row[key] for row in rows), max(row[key] for row in rows)]
            case['beforecapture_range_v'] = [min(row['beforecapture'] for row in rows), max(row['beforecapture'] for row in rows)]
            if all('next_read_error_mv' in row for row in rows):
                case['next_read_error_mv_range']=[min(row['next_read_error_mv'] for row in rows),max(row['next_read_error_mv'] for row in rows)]
                case['zero_control_next_read_error_mv']=rows[0]['next_read_error_mv']
                case['signal_next_read_error_mv']=[row['next_read_error_mv'] for row in rows[1:]]
                if report.get('diagnostic_ideal_charge_fc'):
                    case['zero_relative_signal_gain']=[
                        (row['followread']-rows[0]['followread'])/(row['beforecapture']-rows[0]['beforecapture'])
                        for row in rows[1:]
                        if abs(row['beforecapture']-rows[0]['beforecapture'])>1e-12]
                    case['zero_relative_gain_scope']='Offline diagnostic separating zero-control offset from signal gain; no correction drives the circuit and no model accuracy acceptance.'
                if all(all(key in row for key in ['captured','heldafteruse','topduringuse','bottomduringuse','restoreprogram']) for row in rows):
                    phases=['beforecapture','captured','heldafteruse','topduringuse','bottomduringuse','restoreprogram','followread']
                    case['zero_relative_phase_signal_mv']=[
                        {key:(row[key]-rows[0][key])*1000 for key in phases} for row in rows[1:]]
                    case['zero_relative_phase_changes_mv']=[
                        {b+'_minus_'+a:signal[b]-signal[a] for a,b in zip(phases,phases[1:])}
                        for signal in case['zero_relative_phase_signal_mv']]
                    case['phase_diagnostic_scope']='Differences of measured nodes and phases versus slot0 control; localizes aggregate error but does not prove unique device causation or implement correction.'
            if all('heldafteruse' in row for row in rows):
                case['held_sample_use_movement_mv'] = [(row['heldafteruse']-row['captured'])*1000 for row in rows]
            if all('referencebus' in row for row in rows):
                case['reference_bus_range_v'] = [min(row['referencebus'] for row in rows),max(row['referencebus'] for row in rows)]
                case['reference_gate_change_mv'] = (rows[-1]['referencegate']-rows[0]['referencegate'])*1000
            for field in ['calibration_release_delta_uv','calibration_settled_delta_uv',
                          'offset_calibration_to_preuse_delta_uv','offset_use_phase_steps_uv','sampling_phase_diagnostics_uv','sample_track_end_minus_acquisition_buffer_uv',
                          'buffer_calibration_release_step_uv']:
                if all(field in row for row in rows):
                    case[field]=[row[field] for row in rows]
            if report.get('physical_offset_storage_subtraction'):
                case['offset_before_first_mv'] = rows[0]['offsetbefore'] * 1000
                case['offset_after_last_mv'] = rows[-1]['offsetafter'] * 1000
                case['reuse_offset_changes_mv'] = [(row['offsetafter']-row['offsetbefore'])*1000 for row in rows]
        if rows and all('sampling_phase_diagnostics_uv' in row for row in rows):
            control=rows[0]['sampling_phase_diagnostics_uv']
            case['zero_relative_sampling_phase_diagnostics_uv']=[
                {key:row['sampling_phase_diagnostics_uv'][key]-control[key] for key in control} for row in rows[1:]]
        cases.append(case)
    qualification = BASE / 'layout/gf180_offset_subtractor/qualification.json'
    sources.append(qualification)
    variants = []
    plate_coupling = {}
    for cell in ['gf180_offset_subtractor_short_split4', 'gf180_offset_subtractor_short_split4_isolated',
                 'gf180_offset_subtractor_short_split4_isolated_reversed',
                 'gf180_offset_subtractor_short_split4_isolated_reversed_halfswitch',
                 'gf180_offset_subtractor_short_split4_isolated_reversed_splitsample',
                 'gf180_offset_subtractor_short_split4_isolated_reversed_sampledummybottom',
                 'gf180_offset_subtractor_short_split4_isolated_reversed_sampledummybottom_clocktrim2',
                 'gf180_offset_subtractor_short_split4_isolated_reversed_sampledummybottom_clocktrim4_sample',
                 'gf180_offset_subtractor_short_split4_isolated_reversed_sampledummybottom_nf0p33',
                 'gf180_offset_subtractor_short_split4_isolated_reversed_sampledummybottom_nf0p25',
                 'gf180_offset_subtractor_short_split4_isolated_reversed_dummybottom']:
        path = BASE / 'layout' / cell / 'qualification.json'
        if path.exists():
            sources.append(path)
            variants.append(json.loads(path.read_text()))
            netlist = path.parent / (cell + '_cap.spice')
            sources.append(netlist)
            plate_coupling[cell] = {}
            for a,b,value in re.findall(r'(?m)^C\S+\s+(\S+)\s+(\S+)\s+([0-9.eE+-]+)f', netlist.read_text()):
                if ((a in ['TOP','BOTTOM'] and b.startswith(('SAMPLE','USE'))) or
                    (b in ['TOP','BOTTOM'] and a.startswith(('SAMPLE','USE')))):
                    plate_coupling[cell][a+'_'+b+'_ff']=float(value)
                if {a,b} in [{'TOP','USEB'}, {'TOP','USE'}, {'BOTTOM','USEBOTTOM'}, {'BOTTOM','USEBOTTOMB'}]:
                    plate_coupling[cell][a+'_'+b+'_ff'] = float(value)
                if {a,b} in [{'TOP','VSS'}, {'BOTTOM','VSS'}]:
                    plate_coupling[cell][a+'_'+b+'_ff'] = float(value)
    noise=[]
    writer_variants=[]
    for qualification_path in sorted((BASE/'layout').glob('gf180_sensor_servo_writer*/qualification.json')):
        sources.append(qualification_path)
        writer_variants.append(json.loads(qualification_path.read_text()))
    for path in sorted((BASE/'results').glob('gf180_restore_phase_noise_*.json')):
        report=json.loads(path.read_text());sources.append(path)
        noise.append({key:report.get(key) for key in ['simulation_completed','writer_reference_current_ua',
            'writer_input_pair_width_um','sample_switch_nf_width_um','physical_acquisition_buffer','offset_extra_mim_count','offset_continuous_use','offset_continuous_clamp_startup_only',
            'transient_source','values','integration_band_hz','dc_minus_transient_mv',
            'bias_matches_transient_within_100uv','scope']})
    output = {
        'physical_state_accepted': False, 'full_chip_accepted': False,
        'offset_layout': json.loads(qualification.read_text()), 'offset_layout_variants': variants, 'cases': cases,
        'extracted_clock_plate_capacitance_ff': plate_coupling,
        'stationary_restore_noise':noise,
        'writer_layout_variants':writer_variants,
        'scope': 'Small deterministic zero/nonzero-state round trips with extracted capacitances and physical switches/MIM/OTA. Ideal diagnostic event charge, control/reference/read currents. MIM typical only; no resistance extraction, sampled noise, silicon gate leakage, complete SNN update, original-float accuracy or population service qualification.',
        'conclusion': 'Physical reference refresh removes accumulated calibration drift in small nominal benches. Lower writer/buffer bias reduces measured energy;0.5uA fails initialization.1uA immediate post-release error relaxes substantially after writer idle and physical next read, so immediate samples alone cannot select bias.1/2/20uA stationary noise benches match completed transient bias but do not establish sampled noise. Signal-dependent error, noise, reference/bias implementation, long-term retention, assembly/density and full5ms PLIF/model service remain unqualified.',
        'next_step': 'Continuous physical offset-bank use with startup-only reference clamp improves nominal signed transfer; qualify numerical sensitivity, sampling disturbance, PVT/mismatch and matched noise before selection. Smaller switches and passive clock trims remain unselected. Continue physical gain/offset correction and sampled-noise/nonlinear encoding before fully routed sampler/reference assembly, exact PLIF, original-float accuracy, density and population service. One post-hold followread is not repeated multibin PLIF or silicon retention qualification. Conditional power repeat is not accepted chip power.',
        'sha256': {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}}
    target = BASE / 'results/gf180_sampled_restore_boundary.json'
    target.write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({'report': str(target), 'cases': len(cases),
                      'complete': sum(bool(case['simulation_completed']) for case in cases)}, indent=2))


if __name__ == '__main__':
    main()
