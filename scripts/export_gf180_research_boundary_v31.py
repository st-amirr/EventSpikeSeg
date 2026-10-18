"""Export physical research interfaces and distinguish existing drivers from inputs."""
from pathlib import Path
import json,collections,re
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'assembly/full25_native_controls_v31'

def main():
    dest=OUT/'research_boundary_v1.json';assert not dest.exists();files={Path(__file__)}
    def read(p):files.add(p);return json.loads(p.read_text())
    meta=read(OUT/'physical_assembly.json');assert read(OUT/'independent_readback_v1.json')['readback_pass']
    assert read(BASE/'assembly/full25_class_infrastructure_v30/integration_readback_v1.json')['readback_pass']
    v24=read(BASE/'assembly/full25_analog_interfaces_v24/escape_plan.json');v31=read(OUT/'escape_plan.json');cl=read(BASE/'assembly/full25_class_interfaces_v28/escape_plan.json')
    local=read(BASE/'assembly/full25_physical_candidate_v5/physical_assembly.json');groups={(n['actor'],n['net']):n['endpoint_pins'] for n in local['local_pin_nets']}
    phases={'WEIGHT_SAMPLE':'event.SAMPLE','WEIGHT_SAMPLE_B':'write_inverse.OUT','WEIGHT_ARM':'event.ARM','WEIGHT_ARM_B':'arm_inverse.OUT','WEIGHT_SIGN_B':'sign_inverse.OUT','POSITIVE_INJECTION':'positive.Y','POSITIVE_INJECTION_B':'positive.YB','NEGATIVE_INJECTION':'negative.Y','NEGATIVE_INJECTION_B':'negative.YB','WEIGHT_PULSE':'duration.PULSE'}
    rails={'VDD','VSS','STORAGE_REFERENCE','COMPUTE_REFERENCE'};entries=[]
    for origin,plan in [('V24',v24),('V31',v31)]:
        for e in plan['escapes']:
            pin=e['native_pin'];role='external_analog_or_control_input';driver=None
            if pin in rails:role='connected_power_or_reference'
            elif pin in phases:role='observation_only';driver=phases[pin]
            elif pin.startswith(('event__','commit__')):
                if pin.split('__')[1] not in ('CLK','RESET','REQUEST','BIN_START','COMPLETE'):role='observation_only';driver=pin.replace('__','.')
                else:role='external_control_input'
            elif pin=='WEIGHT_SIGN':role='external_sign_input'
            elif pin=='duration__MAG_DATA':role='external_analog_magnitude_input'
            entries.append(dict(domain='actor',actor_index=e['actor_index'],actor=e['actor'],native_pin=pin,endpoint_kind=e['endpoint_kind'],escape_label=e['escape_label'],layer=81,xy_top_dbu=e['escaped_top_dbu'],source_revision=origin,role=role,external_drive_allowed=role.startswith('external'),existing_driver=driver,existing_local_endpoints=groups.get((e['actor'],pin),[])))
    for e in cl['escapes']:
        pin=e['native_pin'];role='external_analog_or_control_input'
        if pin in rails:role='connected_power_or_reference'
        elif pin=='RECOV' or re.fullmatch(r'(DATA[0-7]|STATE[0-5]|OUTPUT[0-5]|WIN[0-5]|LABEL[0-5])',pin):role='observation_only'
        entries.append(dict(domain='class_current',native_pin=pin,escape_label=e['escape_label'],layer=81,xy_top_dbu=e['escaped_top_dbu'],role=role,external_drive_allowed=role.startswith('external')))
    pair=read(BASE/'assembly/accumulation_fabric_ingress_v1/route_plan.json');link=read(BASE/'assembly/accumulation_dispatch_link_v2/route_plan.json');v17=read(BASE/'assembly/full25_accumulation_architecture_v17/route_plan.json');binding=read(BASE/'assembly/native_address_route_inputs_v1/routing_inputs.json')
    bound={};drivers=collections.Counter()
    for n in pair['routes']+link['routes']:
        for node in n['nodes']:
            key=node['instance'],node['pin'];assert key not in bound or bound[key]==n['net'];bound[key]=n['net']
    for n in v17['routes']:bound['FABRIC',n['destination']['pin']]=n['net'];drivers[n['net']]+=1
    for n in binding['nets']:bound['DISPATCH',n['source']['pin']]=n['net']
    macros={side:read(BASE/f'assembly/{folder}/physical_macro.json') for side,folder in [('FABRIC','full25_packet_fabric_v1'),('INGRESS','full25_actor_ingress_v2'),('DISPATCH','full25_accumulation_dispatch_v1')]}
    for side,m in macros.items():
        for name,pin in m['ports'].items():
            if (side,name) in bound and pin['direction']=='OUTPUT':drivers[bound[side,name]]+=1
    ox,oy=v17['pair_origin_dbu'];origins={side:[p[0]+ox,p[1]+oy] for side,p in pair['origins_dbu'].items()};origins['DISPATCH']=binding['dispatcher_origin_top_dbu']
    for side,m in macros.items():
        gx,gy=origins[side]
        for name,pin in m['ports'].items():
            net=bound.get((side,name));direction=pin['direction']
            role='internal_connection' if net else 'external_control_input' if direction=='INPUT' else 'observation_only'
            if name in ('VDD','VSS'):role='connected_power_or_reference';net=name
            elif net and drivers[net]==0:role='external_shared_input_net'
            rects=[]
            for r in pin['rectangles']:
                l={'Metal3':42,'Metal4':46,'Metal5':81}[r['layer']];xy=[round(v*1000)+offset for v,offset in zip(r['center_um'],(gx,gy))];rects.append(dict(layer=l,xy_top_dbu=xy))
            entries.append(dict(domain='categorical',instance=side,native_pin=name,direction=direction,role=role,connected_net=net,external_drive_allowed=role.startswith('external'),rectangles=rects))
    # Internal pulse producers must never become external phase drivers merely
    # because a top-level observation escape was added.
    assert all(not e['external_drive_allowed'] for e in entries if e.get('existing_driver'))
    assert sum(e['domain']=='actor' and e['native_pin']=='event__REQUEST' and e['external_drive_allowed'] for e in entries)==25
    sequence=[
        'Accept a categorical destination request and hold it stable until ready. Select exactly one local/forest service family using the routed address outputs.',
        'Read and preserve all eight values in the destination row. Restore the selected membrane into its native analog compute state using the appropriate local, PAGE or FOREST path; keep other restore/initialize gates off.',
        'Supply the analog magnitude and sign before the native event controller samples them. Request exactly one event when event READY is high and use its qualified clock schedule; observe native SAMPLE/ARM/PULSE/DONE without externally driving those outputs.',
        'After pulse termination and analog settling, capture the updated membrane and retain the seven unselected columns in the row holders.',
        'Commit exactly one destination row with WRITE_CMD; release write/restore gates and verify analog state retention. Only then return a fresh service_done low-to-high acknowledgement to the destination dispatcher.',
        'Repeat for every requested contribution before the applicable 5 ms accumulation boundary. Threshold/reset/output completion is a separate later operation and is not part of this deadline.'
    ]
    report=dict(boundary_manifest_exported=True,layout=meta['gds'],top_cell=meta['top_cell'],entries=entries,role_counts=dict(collections.Counter(e['role'] for e in entries)),native_actor_control_inputs_exposed=True,service_sequence=sequence,
                service_done_is_external_bridge_input=True,autonomous_analog_service_bridge_implemented=False,
                internal_phase_outputs_must_not_be_externally_driven=True,global_reference_targets_V={'VDD':3.3,'VSS':0.0,'STORAGE_REFERENCE':1.2,'COMPUTE_REFERENCE':1.65},
                retained_parameter_protocol_scope='Original parameter-capacity and legacy protocol-corridor geometry remains as unprogrammed characterization capacity. No trained weight loading or legacy corridor endpoint functionality is claimed. Native unescaped characterization terminals remain at their source-module pads.',
                external_clock_scope='Categorical controller macro nominal40MHz timing is separate from native analog event/commit clocks. Native event clock must be measured together with pulse duration and settling; do not assume40MHz from the hard-macro timing result.',
                full_architecture_layout_complete=False,accumulation_5ms_accepted=False,
                scope='Physical coordinate/role and research service contract over existing independently verified escape/route artifacts. This exports the explicitly external controller/contribution interfaces allowed by user scope. It does not prove full analog service timing, global loaded wires, autonomous inference or accuracy.',sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)})
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(entries=len(entries),role_counts=report['role_counts'])),flush=True)
if __name__=='__main__':main()
