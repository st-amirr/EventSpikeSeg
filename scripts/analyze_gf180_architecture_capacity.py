"""Full-inventory storage and serial-service envelope; no ASIC acceptance claim."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic/results'
EXPECTED = 'c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = Path(__file__)
    occupancy_path = OUT / 'sky130_float_fullframe_state_occupancy.json'
    occupancy = json.loads(occupancy_path.read_text())
    checkpoint = ROOT / 'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
    if sha(checkpoint) != EXPECTED or occupancy['checkpoint_sha256'] != EXPECTED or occupancy['qat_enabled'] or not occupancy['full_frame']:
        raise ValueError('Original full-float inventory/reference differs')
    actors = occupancy['records'][0]['actors']
    states = sum(actor['resident'] for actor in actors.values())
    if states != 30976000 or len(actors) != 25:
        raise ValueError('Resident inventory differs')
    sources = {source, occupancy_path, checkpoint}
    audit_path = OUT / 'gf180_gds_integrity_boundary.json'
    audit = json.loads(audit_path.read_text())
    sources.add(audit_path)
    passes = {case['cell'] for case in audit['cases'] if case['physical_layout_accepted']}
    storage = []
    for width in [7]:
        cell = f'gf180_mim_{width}x{width}'
        path = ROOT / 'artifacts/analog_asic/layout' / cell / 'qualification.json'
        q = json.loads(path.read_text())
        if cell not in passes or q['square_size_um'] != width:
            raise ValueError('Required standalone storage geometry not audited')
        sources.add(path)
        for name, digest in q['sha256'].items():
            artifact = path.parent / name
            if sha(artifact) != digest:
                raise ValueError('Native geometry changed')
            sources.add(artifact)
        x0, y0, x1, y1 = q['bbox_um']
        storage.append({
            'native_cell': cell,
            'single_ended_one_cap_per_membrane_plate_only_mm2': states * width**2 / 1e6,
            'differential_two_caps_per_membrane_plate_only_mm2': 2 * states * width**2 / 1e6,
            'isolated_cell_bbox_replication_mm2': states * (x1-x0) * (y1-y0) / 1e6,
            'scope': 'Standalone geometry extrapolation, excludes adaptation, switches and peripherals; bbox replication is not packed array layout or a minimum.',
        })
    bank_path = ROOT / 'artifacts/analog_asic/layout/gf180_mim_bank_22x22_n8/qualification.json'
    bank = json.loads(bank_path.read_text())
    sources.add(bank_path)
    if 'gf180_mim_bank_22x22_n8' not in passes:
        raise ValueError('Feedback bank not audited')
    for name, digest in bank['sha256'].items():
        artifact = bank_path.parent / name
        if sha(artifact) != digest:
            raise ValueError('Feedback bank changed')
        sources.add(artifact)
    bx0, by0, bx1, by1 = bank['bbox_um']
    feedback_plate = 8 * 22**2
    feedback_bbox = (bx1-bx0) * (by1-by0)
    service = []
    for slot_us in [1, 5, 10, 20, 25, 50]:
        slots = math.floor(5000 / slot_us)
        channels = {name: math.ceil(actor['resident']/slots) for name, actor in actors.items()}
        count = sum(channels.values())
        service.append({
            'assumed_total_serial_slot_us': slot_us,
            'required_channels': count,
            'actor_channel_counts': channels,
            'feedback_plates_mm2': count * feedback_plate / 1e6,
            'feedback_isolated_bank_bboxes_mm2': count * feedback_bbox / 1e6,
            'complete_slot_duration_measured': False,
        })
    envelopes = []
    for total_area in [100, 300, 600]:
        # Illustrative allocations, not requirements or accepted design choices.
        state_area = total_area * 0.5
        feedback_area = total_area * 0.25
        envelopes.append({
            'illustrative_total_area_mm2': total_area,
            'assumed_membrane_plate_allocation_mm2': state_area,
            'maximum_single_cap_plate_area_um2_per_state': state_area*1e6/states,
            'maximum_single_cap_square_side_um': math.sqrt(state_area*1e6/states),
            'assumed_feedback_plate_allocation_mm2': feedback_area,
            'optimistic_continuous_serial_slot_limit_us': 5000*feedback_area*1e6/(states*feedback_plate),
            'scope': 'Ignores actor rounding, adaptation storage, routing and graph dependency; hypothetical allocation, not qualified small-cap geometry or service.',
        })
    result = {
        'checkpoint_sha256': EXPECTED,
        'qat_or_quantized_reference_used': False,
        'resident_membrane_states': states,
        'adaptation_enabled_states': 10982400,
        'membrane_updates_per_second_if_all_serviced_each_bin': states/0.005,
        'storage_geometry_extrapolations': storage,
        'serial_service_scenarios': service,
        'illustrative_area_envelopes': envelopes,
        'conclusion': 'Current audited 7um MIM geometry consumes over a thousand mm2 for membranes alone. Faster sharing reduces feedback replication but does not reduce the resident-state count. Neither sparsity nor population removal is assumed. Density and total slot latency must be resolved together before full-chip replication.',
        'next_required_evidence': [
            'Original-float sensitivity to state noise, offset, gain and retention including adaptation and graph propagation.',
            'Smaller state-storage technology with actual geometry and retention/read-disturb evidence.',
            'Complete signed weighted-event PLIF service slot including beta, threshold, subtractive reset, adaptation and restore.',
            'Actor/DAG schedule including event fan-in, dependencies and readout within 5ms.',
        ],
        'full_chip_accepted': False,
        'full_5ms_population_service_accepted': False,
        'sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(sources)},
    }
    target = OUT / 'gf180_architecture_capacity_boundary.json'
    target.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'report': str(target), 'storage': storage, 'envelopes': envelopes}, indent=2))


if __name__ == '__main__':
    main()
