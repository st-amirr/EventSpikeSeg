"""Conditional architecture budget using actual per-bin original-float activity."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    files = {Path(__file__)}
    measurements = []
    for index in [8, 64]:
        candidates = list((BASE/'results').glob(f'gf180_float_bin_activity_record{index}_src*.json'))
        assert len(candidates) == 1
        path = candidates[0]
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data['measurement_completed'] and data['prior_baseline_reproduced']
        assert not data['qat_or_quantized_reference_used']
        files.add(path)
        for name, expected in data['sha256'].items():
            item = ROOT/name
            assert sha(item) == expected, name
            files.add(item)
        measurements.append(data)
    actors = {name: row['destinations'] for name, row in measurements[0]['activity'].items() if row['is_PLIF_population']}
    assert len(actors) == 25 and sum(actors.values()) == 30976000
    assert all({name: row['destinations'] for name, row in data['activity'].items() if row['is_PLIF_population']} == actors for data in measurements)
    macros = {}
    for cell in ['gf180_autozero_charge_integrator_fullroute_guarded',
                 'gf180_precharged_weight_current_cell_fullroute_guarded',
                 'gf180_pmos_follower_baseline_readout_fullroute_guarded',
                 'gf180_shared_ota_core_pmos_input_fullroute']:
        path = BASE/'layout'/cell/'qualification.json'
        q = json.loads(path.read_text(encoding='utf-8'))
        assert q['magic_drc_count'] == q['gds_roundtrip_drc_count'] == 0
        assert q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
        files.add(path)
        for name, expected in q['sha256'].items():
            item = path.parent/name
            assert sha(item) == expected
            files.add(item)
        x0, y0, x1, y1 = q['bbox_um']
        macros[cell] = {'footprint_mm2': (x1-x0)*(y1-y0)/1e6}
    # Additive reusable-macro footprints are a replication scenario, not a compact layout bound.
    copies = [2, 8, 2, 2]
    partial_lane_footprint = sum(count*row['footprint_mm2'] for count, row in zip(copies, macros.values()))
    peak_by_actor = {name: max(data['activity'][name]['peak_bin_weighted_deliveries'] for data in measurements)
                     for name in measurements[0]['activity']}
    scenarios = []
    for fan_in in [1, 2, 4, 16, 64, 360]:
        lanes = {name: math.ceil(peak*6/(fan_in*5000)) for name, peak in peak_by_actor.items()}
        scenarios.append({
            'concurrent_weight_deliveries_per_group': fan_in,
            'group_interval_us_assumed': 6,
            'qualification': 'Serial/two-source small benchmarks exist; no population service qualification' if fan_in <= 2 else 'Hypothetical; larger-fan-in circuit and sequencing unqualified',
            'conditional_lanes_per_permanent_population_and_readout': lanes,
            'total_conditional_lanes': sum(lanes.values()),
            'replicated_partial_characterization_macro_area_mm2': sum(lanes.values())*partial_lane_footprint,
        })
    storage = []
    for side, count, name in [(7, 1, 'One tested-size plate per membrane'),
                              (5, 1, 'One minimum-rule plate per membrane; not qualified storage'),
                              (7, 2, 'Differential tested-size plates per membrane'),
                              (7, 18, 'Differential nine-plate feedback banks per membrane')]:
        storage.append({'scenario': name, 'plate_side_um': side, 'plates_per_membrane': count,
                        'membrane_plate_only_mm2': sum(actors.values())*side*side*count/1e6})
    snap = BASE/'tools/source_snapshots'/f'{Path(__file__).stem}_{sha(Path(__file__))}.py'
    snap.write_bytes(Path(__file__).read_bytes())
    files.add(snap)
    result = {
        'analysis_completed': True, 'resident_membrane_states': sum(actors.values()),
        'adaptation_states_excluded_from_plate_budget': 10982400,
        'readout_current_destinations_excluded_from_plate_budget': measurements[0]['activity']['head']['destinations'],
        'records': [{'index': data['record_index'], 'deliveries_by_bin_including_readout': data['total_weighted_deliveries_by_bin_including_readout'],
                     'peak_bin_deliveries_including_readout': data['peak_bin_weighted_deliveries_including_readout'],
                     'readout_deliveries_over_50ms': data['activity']['head']['weighted_event_deliveries']}
                    for data in measurements],
        'macro_footprints': macros, 'partial_characterization_lane_footprint_mm2': partial_lane_footprint,
        'macro_copy_counts_in_partial_lane': dict(zip(macros, copies)),
        'conditional_service_scenarios': scenarios, 'storage_plate_scenarios': storage,
        'minimum_MIM_rule_source': 'https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_10_4_1.html',
        'minimum_MIM_rule': 'MIM.8a: minimum FuseTop area 5*5 um2. Plate-only scenario; minimum-rule storage not laid out or qualified here.',
        'scope': 'Observed peaks on two records, not a dataset worst-case. Each population keeps its own lane pool; all pools optimistically have the full5ms. Ceil(peak deliveries*6us/(fanin*5000us)) ignores per-destination packing, distribution, DAG critical path, state access, beta/reset/adaptation, programming and routing. Necessary capacity under these assumptions, not sufficient scheduling. Six microseconds is a small-bench group interval, not a validated minimum. Concurrent currents may change headroom/noise. Existing spacious macro footprints describe literal replication only, not an irreducible compact-design area. Plate budgets omit wells, switches, spacing, routing, adaptation, readout, references and compute; plate area may overlap underlying devices and must not be naively added to transistor area.',
        'decision': 'Do not replicate the characterization lane. Develop a dense analog state/lane organization and high-fan-in summation architecture; simple four-way overlap cannot establish economical full-model implementation. Smaller MIM alone leaves a large resident storage footprint. Switched-capacitor injection would not by itself remove resident-state inventory.',
        'complete_PLIF_accepted': False, 'original_float_accuracy_accepted': False,
        'full_5ms_population_service_accepted': False, 'full_chip_accepted': False,
        'sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)},
    }
    path = BASE/'results/gf180_parallel_area_service_budget.json'
    assert not path.exists(), 'Preserve prior budget'
    path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ['records','partial_characterization_lane_footprint_mm2',
                                                'storage_plate_scenarios','conditional_service_scenarios']}, indent=2))

if __name__ == '__main__':
    main()
