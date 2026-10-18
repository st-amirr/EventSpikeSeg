from pathlib import Path
import json, hashlib, math

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
MANIFEST=BASE/'assembly/membrane_voltage_scale_manifest_v2.json'
PULSE_SCRIPT=ROOT/'scripts/screen_gf180_tracking_park_local_gain.py'
OUT=BASE/'results/gf180_membrane_scale_hardware_requirements_v1.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def quantile(sorted_values, q):
    x=(len(sorted_values)-1)*q; lo=math.floor(x); hi=math.ceil(x)
    return sorted_values[lo] if lo==hi else sorted_values[lo]*(hi-x)+sorted_values[hi]*(x-lo)

def main():
    assert not OUT.exists(), f'preserve existing report: {OUT}'
    m=json.loads(MANIFEST.read_text())
    assert m['manifest_completed'] and m['checkpoint_sha256']=='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
    half=m['physical_voltage_contract']['usable_signed_half_swing_v']
    center=m['physical_voltage_contract']['center_v']
    err=m['physical_voltage_contract']['measured_max_round_trip_error_mv']/1000
    banks=[]; all_scales=[]; actor_results=[]
    for a in m['actors']:
        ranges=sorted(map(float,a['range_abs_model_units']))
        scales=[half/r for r in ranges]
        all_scales.extend(scales)
        actor_results.append({
            'actor':a['actor'],'bank_count':len(ranges),
            'range_abs_model_units':{'min':ranges[0],'p50':quantile(ranges,.5),'p90':quantile(ranges,.9),'p99':quantile(ranges,.99),'max':ranges[-1]},
            'scale_v_per_model_unit':{'min':min(scales),'p50':quantile(sorted(scales),.5),'max':max(scales)},
            'banks_with_range_le_2':sum(x<=2 for x in ranges),
            'banks_with_range_le_10':sum(x<=10 for x in ranges),
            'round_trip_error_in_model_units_at_min_range':err/min(ranges),
            'round_trip_error_in_model_units_at_max_range':err/max(ranges),
        })
    all_scales.sort(); all_ranges=sorted(float(x) for a in m['actors'] for x in a['range_abs_model_units'])
    pulse_text=PULSE_SCRIPT.read_text(encoding='utf-8')
    assert 'assert all(.05<=x<=3 for x in widths)' in pulse_text
    result={
      'analysis_completed':True,
      'checkpoint_sha256':m['checkpoint_sha256'],
      'source_manifest':MANIFEST.relative_to(ROOT).as_posix(),
      'bank_count':m['scale_count'],'active_state_count':m['active_membrane_states'],
      'scale_cells_per_state':m['scale_count']/m['active_membrane_states'],
      'voltage_contract':{'center_v':center,'endpoints_v':m['physical_voltage_contract']['measured_endpoints_v'],'usable_half_swing_v':half,'sampled_max_round_trip_error_mv':err*1000},
      'all_bank_range_abs_model_units':{'min':all_ranges[0],'p50':quantile(all_ranges,.5),'p90':quantile(all_ranges,.9),'p99':quantile(all_ranges,.99),'max':all_ranges[-1]},
      'all_bank_scale_v_per_model_unit':{'min':all_scales[0],'p01':quantile(all_scales,.01),'p10':quantile(all_scales,.1),'p50':quantile(all_scales,.5),'p90':quantile(all_scales,.9),'p99':quantile(all_scales,.99),'max':all_scales[-1],'dynamic_ratio':all_scales[-1]/all_scales[0]},
      'measured_round_trip_error_in_model_units_at_extremes':{'at_smallest_range':err/all_ranges[0],'at_largest_range':err/all_ranges[-1],'fraction_of_bank_half_range':err/half},
      'existing_pulse_duration_command_window_us':[0.05,3.0],
      'existing_pulse_duration_command_ratio':60.0,
      'required_scale_ratio_over_pulse_window':(all_scales[-1]/all_scales[0])/60.0,
      'actors':actor_results,
      'engineering_conclusion':'Per-bank range mapping is necessary to use storage swing efficiently, but the current pulse-duration command window alone cannot span the mapped 12,000:1 bank-scale range. Keep state and trained weights analog; add and characterize a separate continuous bank-scale control path (or a range-plus-fine analog control) before claiming the voltage map is implemented. The 8.238mV round-trip bound corresponds to 0.915% of the signed half-range at any bank; its absolute float-unit equivalent scales with that bank range.',
      'limitations':['Uses eight calibration records and the existing guarded ranges only; unseen scenes and drift are not included.','The 8.238mV figure is a coarse nominal extracted sampler/read/restore result, not a noise/PVT bound.','Pulse-duration window is a command constraint from the existing diagnostic script, not an experimentally accepted scale-transfer curve.','No scale cell circuit, storage overhead layout, update path, model accuracy, or 5ms service is qualified.'],
      'sha256':{MANIFEST.relative_to(ROOT).as_posix():sha(MANIFEST),PULSE_SCRIPT.relative_to(ROOT).as_posix():sha(PULSE_SCRIPT),Path(__file__).relative_to(ROOT).as_posix():sha(Path(__file__))}
    }
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':OUT.relative_to(ROOT).as_posix(),'bank_count':result['bank_count'],'scale_ratio':result['all_bank_scale_v_per_model_unit']['dynamic_ratio'],'pulse_range_ratio':result['existing_pulse_duration_command_ratio'],'round_trip_fraction_half_range_percent':100*result['measured_round_trip_error_in_model_units_at_extremes']['fraction_of_bank_half_range']},indent=2))

if __name__=='__main__': main()
