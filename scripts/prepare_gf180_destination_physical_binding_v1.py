"""Freeze native/ingress endpoints for the routed destination-controller join."""
from pathlib import Path
import collections,json
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/destination_physical_binding_v1'


def main():
    assert not OUT.exists();OUT.mkdir(parents=True)
    dd=BASE/'assembly/full25_accumulation_dispatch_v1'; prepared_path=dd/'prepared.json'
    prepared=json.loads(prepared_path.read_text()); widths={n:w for _,w,n in prepared['ports']}
    directions={n:d for d,_,n in prepared['ports']}
    native_dir=BASE/'assembly/full25_membrane_address_breakouts_v18'
    nm_path=native_dir/'physical_assembly.json';native=json.loads(nm_path.read_text())
    proof_path=native_dir/'independent_readback_v1.json';assert json.loads(proof_path.read_text())['readback_pass']
    escape_path=native_dir/'escape_plan.json';escape=json.loads(escape_path.read_text())
    im_path=BASE/'assembly/full25_actor_ingress_v2/physical_macro.json';ingress=json.loads(im_path.read_text())
    pair_path=BASE/'assembly/accumulation_fabric_ingress_v1/route_plan.json';pair=json.loads(pair_path.read_text())
    v17_path=BASE/'assembly/full25_accumulation_architecture_v17/physical_assembly.json';v17=json.loads(v17_path.read_text())
    ox=v17['sha256'] # The proof below fixes actual source placement, not this helper's intention.
    v17_plan_path=BASE/'assembly/full25_accumulation_architecture_v17/route_plan.json';v17plan=json.loads(v17_plan_path.read_text())
    origin=[pair['origins_dbu']['INGRESS'][k]+v17plan['pair_origin_dbu'][k] for k in [0,1]]
    groups=collections.defaultdict(list)
    for e in escape['escapes']:
        ai=e['actor_index'];port=e['dispatcher_port'];bit=e['dispatcher_bit'];width=widths[port]
        assert directions[port]=='output' and bit<width
        driver=f'{port}[{ai*width+bit}]'
        groups[driver].append(dict(kind='native_membrane',actor_index=ai,native_pin=e['native_pin'],
                                  layer=81,xy_top_dbu=e['escaped_top_dbu'],label=e['escape_label'],
                                  cell=native['actors'][ai]['breakout_cell']))
    joins=[('group_valid_o','group_valid_i'),('group_ready_i','group_ready_o'),
           ('output_channel_base_o','channel_base_i'),('output_lane_count_o','lane_count_i'),
           ('output_x_o','x_i'),('output_y_o','y_i'),('contribution_bin_tag_o','bin_tag_i'),
           ('group_settled_done_i','group_settled_done_o')]
    ingress_nets=[]
    for source,target in joins:
        width=widths[target]
        for ai in range(25):
            for bit in range(width):
                k=ai*width+bit;pin=f'{source}[{k}]';controller=f'{target}[{k}]'
                record=ingress['ports'][pin]
                assert record['direction'].lower()!=directions[target]
                r=record['rectangles'][0];x,y=[round(v*1000) for v in r['center_um']]
                ingress_nets.append(dict(ingress_pin=pin,controller_pin=controller,
                                         ingress_direction=record['direction'],
                                         controller_direction=directions[target],actor_index=ai,
                                         layer={'Metal3':42,'Metal4':46}[r['layer']],
                                         xy_top_dbu=[x+origin[0],y+origin[1]]))
    assert len(ingress_nets)==1575
    native_nets=[dict(controller_pin=pin,endpoints=ends) for pin,ends in sorted(groups.items())]
    assert sum(len(n['endpoints']) for n in native_nets)==1622
    report=dict(stage='native_and_ingress_endpoint_contract',actor_count=25,
                ingress_controller_signal_bits=1575,controller_native_output_nets=len(native_nets),
                native_endpoint_fanout_count=1622,ingress_origin_top_dbu=origin,
                ingress_connections=ingress_nets,native_connections=native_nets,
                controller_physical_pins_pending=True,physical_parent_joins_built=False,
                service_kind_contract={0:'Native local64 membrane bank',1:'Native local128 bank pair',
                                       2:'Native local1024 page',3:'Full-population membrane forest'},
                externally_driven_analog_service_contract=[
                    'Accept service_valid only while required destination and address are settled',
                    'Quiet all read/write/restore gates before changing any selected address',
                    'Enable only the service_kind-selected local/forest restore and write path',
                    'Preserve the other seven columns when committing an eight-holder row',
                    'Apply the signed external analog contribution to the selected restored membrane',
                    'Assert a fresh service_done only after the actual required analog accumulation and writeback',
                    'Never advance a destination using a stale-high done or a command-issued pulse',
                ],
                source_state_and_existing_event_routes_preserved_by_native_readback=True,
                full_architecture_layout_complete=False,accumulation_5ms_accepted=False,
                scope='Actual readback-qualified native escape coordinates and existing physical ingress terminals; logical destination-controller pins await the live ORFS job. This file is a routing contract, not evidence of completed parent metal. Analog operation phases/magnitude/sign remain external research interfaces.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in
                        [Path(__file__),prepared_path,nm_path,proof_path,escape_path,im_path,pair_path,v17_path,v17_plan_path]})
    (OUT/'binding_contract.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['ingress_controller_signal_bits','controller_native_output_nets','native_endpoint_fanout_count','controller_physical_pins_pending']}))


if __name__=='__main__':main()
