"""Audit dense-storage sensitivity, frozen calibration and repaired physical primitive."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    for name, expected in data.get('sha256',{}).items():
        assert sha(ROOT/name) == expected, name
    return data

def main():
    paths = [BASE/'results/gf180_minimum_mim_storage_record8_src97b5266bfc26.json',
             BASE/'results/gf180_tile_mim_storage_record8_src2c7b9cbd4128.json',
             BASE/'results/gf180_tile_mim_storage_record64_src2c7b9cbd4128.json',
             BASE/'results/gf180_channel_mim_storage_record8_src00f6fc7164ea.json']
    cases = []
    for path in paths:
        d = read(path)
        assert d['simulation_completed'] and d['baseline_reproduced']
        assert len(d['results']) == 3 and not d['qat_or_quantized_reference_used']
        baseline = d['results'][0]['mean_iou']
        cases.append({'report':path.relative_to(ROOT).as_posix(), 'sha256':sha(path),
                      'record_index':d['record_index'], 'baseline_iou':baseline,
                      'zero_noise_control_iou':d['results'][1]['mean_iou'],
                      'minimum_MIM_proxy_iou':d['results'][2]['mean_iou'],
                      'proxy_iou_delta_from_float':d['results'][2]['mean_iou']-baseline,
                      'pixel_change_fraction':d['results'][2]['pixel_change_fraction'],
                      'storage_sigma_uv':d['results'][2]['storage_sigma_uv'], 'scope':d['scope']})
    cp = BASE/'results/gf180_float_state_tile_calibration_dc685af8e3_srcc47640d01bc7.json'
    c = read(cp)
    assert len(c['records']) == 8
    prior = read(BASE/'results/gf180_float_spatial_calibration_dc685af8e3_src9258811ed52c.json')
    for row in c['records']:
        old = next(x for x in prior['records'] if x['validation_record_index']==row['validation_record_index'])
        assert all(row[k]==old[k] for k in ['input_sequence_sha256','target_sha256','prediction_sha256'])
    histogram = {str(g):0 for g in [1,2,4,8,16]}
    for name, value in c['state_tile8_ranges'].items():
        tile = np.asarray(value)
        channel = np.asarray(c['channel_fixed_calibration_absmax'][name])[None,:,None,None]
        gain = np.clip(2.**np.floor(np.log2(channel/tile)),1,16)
        for g in histogram:
            histogram[g] += int((gain==int(g)).sum())
    groups = sum(histogram.values())
    physical = []
    for name in ['gf180_minimum_mim_gds_integrity.json','gf180_minimum_mim_routed_gds_integrity.json']:
        path = BASE/'results'/name
        d = read(path)
        assert d['audit_completed'] and len(d['cases']) == 1
        physical.append({'report':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'case':d['cases'][0]})
    assert not physical[0]['case']['physical_layout_accepted'] and physical[1]['case']['physical_layout_accepted']
    repair = BASE/'layout/gf180_mim_5x5_ports_routed/qualification.json'
    q = json.loads(repair.read_text(encoding='utf-8'))
    for name, expected in q['sha256'].items():
        assert sha(repair.parent/name) == expected
    for name, expected in q['input_sha256'].items():
        assert sha(ROOT/name) == expected
    failed = BASE/'layout/gf180_mim_5x5_ports_fullroute/failure.json'
    assert not json.loads(failed.read_text())['build_completed']
    files = [Path(__file__),cp,repair,failed,*paths,*[BASE/'results'/p['report'].split('/')[-1] for p in physical]]
    snapshot = BASE/'tools/source_snapshots'/('summarize_gf180_dense_storage_'+sha(Path(__file__))+'.py')
    snapshot.write_bytes(Path(__file__).read_bytes())
    files.append(snapshot)
    result = {
        'audit_completed':True, 'stage':'Dense analog storage representation and minimum physical primitive; complete memory service unfinished',
        'new_float_forwards':20, 'calibration_forwards':8, 'sensitivity_forwards':12,
        'calibration':{'report':cp.relative_to(ROOT).as_posix(),'eight_prior_baseline_hashes_reproduced':True,
                       'heldouts_excluded':[8,64], 'fixed_state_range_groups':groups, 'gain_histogram':histogram,
                       'three_bit_configuration_payload_bytes':(groups*3+7)//8,
                       'configuration_scope':'Hypothetical static range-selection payload, not membrane/weight quantization. Excludes physical references, gain circuits, decoding, storage implementation and routing.'},
        'sensitivity_cases':cases, 'physical_primitive_audits':physical,
        'repaired_cell':'gf180_mim_5x5_ports_routed',
        'repaired_cell_bbox_um':q['bbox_um'],
        'failed_first_repair':{'report':failed.relative_to(ROOT).as_posix(),'scope':'Direct top-contact label extraction aborted; immutable failed build source and geometry retained. Separate external strap repair subsequently qualified.'},
        'interpretation':'Post-reset all-actor fixed tile scaling materially reduces the nominal50fF storage-noise proxy penalty on two same-sequence heldouts. Channel-only control is substantially worse on record8. Earlier candidate-calibrated stem-only case uses different ranges and is not a pure spatial-gain ablation. No universal analog noise floor or acceptable accuracy tolerance is established. Nominal kTC model and noiseless range conversion are optimistic circuit assumptions; actual sampled covariance and longer sequences remain open.',
        'next_action':'Build a small write/hold/read memory module using the repaired capacitor; quantify real storage error, retention and conversion gain against the model sensitivity before array replication. Preserve dense state/high-fan-in architecture work and5ms requirements.',
        'MIM_rule_source':'https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_10_4_2.html',
        'area_scope':'Minimum MIM plate inventory remains774.4mm2 for membranes alone; spatial scaling improves representation precision, not state count or plate geometry. Packed array, adaptation/readout, switches, references and compute remain unimplemented; no feasible chip footprint established.',
        'physical_storage_accepted':False, 'original_float_accuracy_accepted':False, 'complete_PLIF_accepted':False,
        'full_5ms_population_service_accepted':False, 'full_chip_accepted':False,
        'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files},
    }
    out = BASE/'results/gf180_dense_storage_boundary.json'
    assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(out),'new_float_forwards':20,'state_range_groups':groups,
                      'repaired_primitive_passed':True,'cases':[{k:x[k] for k in ['record_index','baseline_iou','minimum_MIM_proxy_iou','pixel_change_fraction']} for x in cases]},indent=2))

if __name__ == '__main__':
    main()
