"""Use preserved original-float traffic to reject insufficient serial services."""
from pathlib import Path
import hashlib,json,math

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
SHA='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'

def main():
    live_mapping=BASE/'assembly/full25_actor_ingress_v2/status.json'
    mapping=BASE/'assembly/full25_actor_ingress_v2/measured_requirements_input_status.json'
    if not mapping.exists():mapping.write_bytes(live_mapping.read_bytes())
    spec=json.loads(mapping.read_text());assert spec['checkpoint_sha256']==SHA
    paths=[BASE/f'results/gf180_float_bin_activity_record{i}_src078e0a1bbb89.json' for i in [8,64]]
    reports=[json.loads(p.read_text()) for p in paths]
    assert all(r['measurement_completed'] and r['checkpoint_sha256']==SHA and r['prior_baseline_reproduced'] and not r['qat_or_quantized_reference_used'] for r in reports)
    capacity=200000 # 40MHz * 5ms, ideal one packet/tap per clock.
    actors=[]
    for actor in spec['actors']:
        p=actor['parameters'];name=actor['actor'];lanes=actor['output_lanes'];taps=p['KERNEL_WIDTH']*p['KERNEL_HEIGHT']
        peak=max(r['activity'][name]['peak_bin_weighted_deliveries'] for r in reports)
        assert peak%lanes==0
        groups=peak//lanes
        events_min=math.ceil(groups/taps)
        states=math.prod(actor['output_shape_chw'])
        actors.append(dict(actor=name,output_lanes_per_group=lanes,peak_measured_weighted_deliveries=peak,
                           exact_peak_required_spatial_tap_groups=groups,
                           presynaptic_packets_lower_bound=events_min,
                           ideal_one_group_per_clock_seconds=groups/40e6,
                           minimum_ideal_independent_group_issue_paths=math.ceil(groups/capacity),
                           minimum_ideal_independent_packet_paths=math.ceil(events_min/capacity),
                           minimum_ideal_three_cycle_decision_services=math.ceil(states*3/capacity)))
    out=BASE/'assembly/full25_actor_ingress_v2/measured_parallel_service_requirements_v1.json'
    assert not out.exists()
    result=dict(checkpoint_sha256=SHA,clock_hz=40000000,required_bin_seconds=.005,
                user_confirmed_real_time_requirement=True,actors=actors,
                actors_exceeding_ideal_serial_packet_capacity=sum(a['minimum_ideal_independent_packet_paths']>1 for a in actors),
                actors_exceeding_ideal_serial_group_capacity=sum(a['minimum_ideal_independent_group_issue_paths']>1 for a in actors),
                serial_services_meet_5ms=False,full_5ms_population_service_accepted=False,
                scope='Exact weighted delivery counts from two preserved epoch58 float records. Group counts divide by connected output channels. Packet counts are lower bounds because each packet reaches at most kernel-taps groups; padding/stride can reduce this. All bounds optimistically allow one transaction per40MHz clock and ignore analog service, memory contention, DAG phases and routing. These are necessary minima, not a hardware sizing choice or worst-case coverage. Serial address macros are reusable building blocks, not a real-time architecture.',
                required_changes=['independent storage roots and native parallel compute services','parallel categorical event/group dispatch preserving repeated events','parallel weight read and signed analog injection','ordered spike result merging or wider event fabric with exact completion barriers','loaded service timing and DAG deadline validation'],
                sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths+[mapping,Path(__file__)]})
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['actors_exceeding_ideal_serial_packet_capacity','actors_exceeding_ideal_serial_group_capacity','serial_services_meet_5ms']},indent=2))
    print(json.dumps(sorted(actors,key=lambda a:a['minimum_ideal_independent_group_issue_paths'],reverse=True)[:3],indent=2))

if __name__=='__main__':main()
