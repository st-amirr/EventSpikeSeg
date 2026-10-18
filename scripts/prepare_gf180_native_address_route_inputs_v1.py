"""Resolve all947 native address-net drivers to actual final GDS placement."""
from pathlib import Path
import json
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/native_address_route_inputs_v1'


def main():
    assert not OUT.exists();OUT.mkdir(parents=True)
    vd=BASE/'assembly/full25_accumulation_dispatch_v19'
    vm_path=vd/'physical_assembly.json';vm=json.loads(vm_path.read_text())
    vp=vd/'independent_readback_v1.json';assert json.loads(vp.read_text())['readback_pass']
    binding_path=BASE/'assembly/destination_physical_binding_v1/binding_contract.json'
    binding=json.loads(binding_path.read_text())
    cm_path=BASE/'assembly/full25_accumulation_dispatch_v1/physical_macro.json';cm=json.loads(cm_path.read_text())
    lm_path=BASE/'assembly/accumulation_dispatch_link_v2/physical_assembly.json';lm=json.loads(lm_path.read_text())
    lp_path=BASE/'assembly/accumulation_dispatch_link_v2/route_plan.json';lp=json.loads(lp_path.read_text())
    pp_path=BASE/'assembly/accumulation_fabric_ingress_v1/route_plan.json';pp=json.loads(pp_path.read_text())
    v17_path=BASE/'assembly/full25_accumulation_architecture_v17/route_plan.json';v17=json.loads(v17_path.read_text())
    ox,oy=v17['pair_origin_dbu'];dx,dy=lp['dispatcher_origin_dbu'];origin=[ox+dx,oy+dy]
    w,h=[round(v*1000) for v in cm['size_um']]
    control_macro_box=[origin[0],origin[1],origin[0]+w,origin[1]+h]
    nets=[]
    for net in binding['native_connections']:
        pin=net['controller_pin'];port=cm['ports'][pin];assert port['direction']=='OUTPUT'
        r=port['rectangles'][0];x,y=[round(v*1000) for v in r['center_um']]
        nets.append(dict(net=pin,source=dict(cell=lm['dispatcher_cell'],pin=pin,
                    layer={'Metal3':42,'Metal4':46}[r['layer']],xy_top_dbu=[x+origin[0],y+origin[1]]),
                    endpoints=net['endpoints']))
    assert len(nets)==947 and sum(len(n['endpoints']) for n in nets)==1622
    v13_path=BASE/'assembly/full25_class_current_service_v13/physical_assembly.json';v13=json.loads(v13_path.read_text())
    v15_path=BASE/'assembly/full25_spike_breakouts_v15/physical_assembly.json';v15=json.loads(v15_path.read_text())
    native_plan_path=BASE/'assembly/full25_membrane_address_breakouts_v18/escape_plan.json';native=json.loads(native_plan_path.read_text())
    by_actor={a['actor_index']:[] for a in v15['actors']}
    for e in native['escapes']:by_actor[e['actor_index']].append(e['escaped_top_dbu'])
    bounds=[];actor_bounds={}
    for a in v15['actors']:
        bb=list(a['enclosing_top_bbox_dbu']);points=by_actor[a['actor_index']]
        bb[0]=min([bb[0]]+[p[0]-220 for p in points]);bb[1]=min([bb[1]]+[p[1]-220 for p in points])
        bb[2]=max([bb[2]]+[p[0]+220 for p in points]);bb[3]=max([bb[3]]+[p[1]+220 for p in points])
        actor_bounds[a['actor_index']]=bb;bounds.append(dict(kind='native_actor',actor_index=a['actor_index'],bbox_dbu=bb))
    actor_cells={a['enclosing_top_cell'] for a in v15['actors']}
    for p in v13['top_placements']:
        if p['cell'] not in actor_cells:bounds.append(dict(kind='other_native',cell=p['cell'],bbox_dbu=p['bbox_dbu']))
    local_boxes=list(pp['bounds_dbu'].values())+list(lp['source_bounds_dbu'].values())
    local_boxes += [b for plan in [pp,lp] for net in plan['routes'] for l,b in net['shapes']]
    control_box=[min(b[0] for b in local_boxes)+ox,min(b[1] for b in local_boxes)+oy,
                 max(b[2] for b in local_boxes)+ox,max(b[3] for b in local_boxes)+oy]
    bounds.append(dict(kind='categorical_control_and_parent_wiring',bbox_dbu=control_box))
    assert max(abs(v) for b in bounds for v in b['bbox_dbu'])<2100000000
    report=dict(stage='physical_native_address_routing_inputs',native_address_nets=947,native_sink_endpoints=1622,
                nets=nets,dispatcher_macro_bbox_dbu=control_macro_box,dispatcher_origin_top_dbu=origin,
                categorical_block_bbox_dbu=control_box,obstacles=bounds,actor_bounds_dbu=actor_bounds,
                physical_driver_and_native_sink_coordinates_resolved=True,global_native_address_metal_built=False,
                full_architecture_layout_complete=False,accumulation_5ms_accepted=False,
                scope='Readback-qualified V19 placements and real final dispatcher pin metal anchors, grouped947output nets to1622native sinks. Obstacles include complete native wrappers/address escapes and existing categorical parent-routing envelope. Routing input only; no new global conductors or global timing proof.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),vm_path,vp,binding_path,cm_path,lm_path,lp_path,pp_path,v17_path,v13_path,v15_path,native_plan_path]})
    (OUT/'routing_inputs.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['native_address_nets','native_sink_endpoints','physical_driver_and_native_sink_coordinates_resolved','global_native_address_metal_built']}))


if __name__=='__main__':main()
