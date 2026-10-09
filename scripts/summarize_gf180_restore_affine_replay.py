"""Join bounded physical restore evidence to explicitly extrapolated float sensitivity."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'artifacts/analog_asic/results'
CHECKPOINT_SHA='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'


def main():
    sources=[Path(__file__)]
    rows=[]
    for path in sorted(RESULTS.glob('analog_float_affine_restore_record*_all_neurons_full_*.json')):
        r=json.loads(path.read_text())
        if r['checkpoint_sha256']!=CHECKPOINT_SHA or r['qat_or_quantized_reference_used'] is not False or not r['full_frame'] or r['scope']!='all-neurons' or r['encoding']!='linear-clipped':
            raise ValueError('replay contract mismatch: '+str(path))
        sources.append(path)
        rows.append({'source':path.relative_to(ROOT).as_posix(),
                     'record_index':r['record_index'],
                     'gain_positive':r['restore_gain_positive'],
                     'gain_negative':r['restore_gain_negative'],
                     'offset_uv_legacy0p9v':r['restore_offset_uv_in_0p9v_normalization'],
                     'baseline_mean_iou':r['baseline_present_class_mean_iou'],
                     'trials':r['trials'],'replay_source_sha256':r['replay_source_sha256']})
    identity=RESULTS/'sky130_float_state_saturation_validation_0_all_neurons_full_none_g1.json'
    r=json.loads(identity.read_text())
    if r.get('affine_restore_active') is not False or any(t['final_fuse_spike_mismatch']!=0 or t['segmentation_pixel_agreement_with_float']!=1 for t in r['trials']):
        raise ValueError('identity replay did not preserve float baseline')
    sources.append(identity)
    physical=[]
    combined=next(row for row in rows if row['record_index']==0 and row['offset_uv_legacy0p9v']==64.06 and row['gain_positive']==0.98239)
    provenance=json.loads((ROOT/combined['source']).read_text())['restore_source_sha256']
    for stem in ['gf180_sensor_zero_servo_typical27_sampledrestore_9e3e1f9ed18e47f215b6',
                 'gf180_sensor_zero_servo_typical27_sampledrestore_682518ba992de5ecab90']:
        path=RESULTS/(stem+'.json')
        expected=next(digest for name,digest in provenance.items() if name.endswith(stem+'.json'))
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            path=RESULTS/('gf180_restore_source_snapshot_'+expected+'.json')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('physical replay source hash mismatch')
        p=json.loads(path.read_text());sources.append(path)
        if not p['simulation_completed'] or p['writer_input_pair_width_um']!=2.5 or p['diagnostic_ideal_charge_fc'] not in [-1,1]:
            raise ValueError('physical source mismatch')
        physical.append({'source':path.relative_to(ROOT).as_posix(),
                         'diagnostic_charge_fc':p['diagnostic_ideal_charge_fc'],
                         'input_signal_mv':[(x['beforecapture']-p['rows'][0]['beforecapture'])*1000 for x in p['rows'][1:]],
                         'zero_control_error_uv':p['rows'][0]['next_read_error_mv']*1000})
    output={'checkpoint_sha256':CHECKPOINT_SHA,'qat_or_quantized_reference_used':False,
            'physical_state_accepted':False,'full_chip_accepted':False,'model_accuracy_qualified':False,
            'physical_small_signal_sources':physical,'full_frame_sensitivity_replays':rows,
            'identity_replay_source':identity.relative_to(ROOT).as_posix(),
            'proxy_mapping':'Physical per-polarity gain rounded0.98239/0.98062; zero offset106.77uV mapped by0.9/1.5 to64.06uV. GF native rails do not prove this ideal encoding is implemented. Smaller offsets are hypothetical targets.',
            'scope':'Two validation frames, ideal per-record actor-linear ranges, gain1. Constant per-polarity affine extrapolation of +/-16mV bench beyond measured voltages; applied after each post-reset bin, initialization ideal, no noise/physical encoder/injector/hold/mismatch/service. Not a validation-set accuracy estimate or qualified circuit transfer.',
            'next_step':'Use gain-versus-offset sensitivity to prioritize physical zero-offset compensation. Qualify actual transfer over model operating range and sampled noise before acceptance; nonlinear encoding, exact PLIF, dense layout and5ms population service remain required.',
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    target=RESULTS/'gf180_restore_affine_float_sensitivity_boundary.json'
    target.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'report':str(target),'replays':rows},indent=2))


if __name__=='__main__':
    main()
