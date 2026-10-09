"""Audit measured-curve full-float sensitivity, without physical inverse acceptance."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
    if digest(checkpoint)!=EXPECTED:raise ValueError('Original float checkpoint mismatch')
    sources={Path(__file__),checkpoint}
    cases=[]
    for path in sorted((BASE/'results').glob('gf180_measured_encoder_float_record*.json')):
        report=json.loads(path.read_text());profile=report['measured_encoder']
        if report['checkpoint_sha256']!=EXPECTED or report['qat_or_quantized_reference_used'] or report['scope']!='all-neurons' or not report['full_frame']:
            raise ValueError('Full-float full-frame replay contract mismatch')
        sources.add(path)
        sha=report['replay_source_sha256']
        snapshot=ROOT/report.get('replay_source_snapshot',f'artifacts/analog_asic/tools/source_snapshots/float_state_replay_{sha}.py')
        if digest(snapshot)!=sha:raise ValueError('Immutable replay source mismatch')
        sources.add(snapshot)
        physical={}
        for kind in ['dc','noise']:
            source=ROOT/profile[f'{kind}_source']
            if digest(source)!=profile[f'{kind}_sha256']:raise ValueError('Physical report mismatch')
            sources.add(source);physical[kind]=json.loads(source.read_text())
        dc,noise=physical['dc'],physical['noise']
        settings=dc['command_arguments']
        if not dc['simulation_completed'] or not noise['simulation_completed']:
            raise ValueError('Incomplete physical DC/noise input')
        rows={row['input_current_na']:row['v(enc)'] for row in dc['rows']}
        positive=max(rows);halfspan=(rows[positive]-rows[-positive])/2
        inferred_gain=(rows[.1]-rows[-.1])/.2*positive/halfspan
        trials=report['trials']
        if not trials:raise ValueError('Missing replay trials')
        metrics=['final_fuse_spike_mismatch','segmentation_pixel_agreement_with_float','present_class_mean_iou','labeled_pixel_accuracy']
        cases.append({'evidence':path.relative_to(ROOT).as_posix(),
                      'record_index':report['record_index'],'settings':settings,
                      'baseline_present_class_mean_iou':report['baseline_present_class_mean_iou'],
                      'noise_scale':profile.get('hypothetical_noise_scale',1),
                      'injected_state_noise_sigma_uv_rms':report['injected_state_noise_sigma_uv_rms'],
                      'measured_stationary_output_noise_uv_rms':noise['analysis']['encoded_output_rms_uv'],
                      'central_secant_gain_relative_to_linear_inferred_from_DC':inferred_gain,
                      'near_zero_0p1pa_gain_relative_to_linear':dc['analysis'].get('near_zero_0p1pa_gain_mv_per_na',inferred_gain*halfspan/positive*1000)/1000*positive/halfspan,
                      'seeds':[trial['seed'] for trial in trials],
                      'means':{metric:sum(trial[metric] for trial in trials)/len(trials) for metric in metrics},
                      'scope':profile['scope']})
    boundary=BASE/'results/gf180_nonlinear_encoder_boundary.json'
    physical_boundary=json.loads(boundary.read_text());sources.add(boundary)
    # Recheck immutable physical inputs; historical executable source uses its snapshot.
    for name,sha in physical_boundary['sha256'].items():
        if name.startswith('scripts/'):
            continue
        source=ROOT/name
        if digest(source)!=sha:raise ValueError(f'Physical boundary provenance mismatch: {name}')
        sources.add(source)
    result={'checkpoint_sha256':EXPECTED,'qat_or_quantized_reference_used':False,
            'cases':cases,'case_count':len(cases),'trial_count':sum(len(case['seeds']) for case in cases),
            'physical_and_replay_provenance_verified':True,
            'physical_inverse_implemented':False,'noise_reduction_implemented':False,
            'physical_state_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,
            'interpretation':'The2nA reference encoder has insufficient near-zero gain under the independent stationary-noise proxy. Source elevation and10pA calibration increase actual near-zero gain and restore near-baseline mean IoU on two frames while many pixels/spikes still change. Exact mathematical inverse, ideal per-record normalization and independent zero-bias stationary noise are optimistic sensitivity assumptions. Zero-noise float32 interpolation has small trajectory differences; it is not a bit-exact control. Older first replay incorrectly labeled near-zero gain1; this boundary recomputes it from the matched DC curve. Dynamic settling, sampled noise, reference generation, physical inverse/update and population service remain gates.',
            'sha256':{path.relative_to(ROOT).as_posix():digest(path) for path in sorted(sources)}}
    target=BASE/'results/gf180_measured_encoder_float_boundary.json'
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'evidence':str(target),'case_count':len(cases),'cases':cases},indent=2))


if __name__=='__main__':main()
