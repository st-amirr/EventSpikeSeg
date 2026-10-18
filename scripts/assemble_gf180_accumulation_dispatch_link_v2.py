"""Join the routed destination dispatcher to the existing event/ingress pair."""
from pathlib import Path
import json,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from assemble_gf180_full25_physical_candidate_v5 import rect,label
from prove_gf180_shared_page_parent_metal_v5 import Paint,VIA
from assemble_gf180_accumulation_fabric_ingress_v1 import sha,wire,renamed,LAYERS

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/accumulation_dispatch_link_v2'


def via(low,high,cut,point):
    # GF180D Via3/4 cut .26um with .10um enclosure; metal pads .46um.
    # The .46um M5 pad exceeds the .44um minimum and avoids the clearance
    # loss caused by the previous .60um pads next to inherited routing.
    x,y=point
    return [(low,(x-230,y-230,x+230,y+230)),
            (high,(x-230,y-230,x+230,y+230)),
            (cut,(x-130,y-130,x+130,y+130))]


def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    pair_dir=BASE/'assembly/accumulation_fabric_ingress_v1'
    pair_path=pair_dir/'physical_assembly.json';pair=json.loads(pair_path.read_text())
    pair_proof=pair_dir/'independent_readback_v1.json';assert json.loads(pair_proof.read_text())['readback_pass']
    old_plan_path=pair_dir/'route_plan.json';old=json.loads(old_plan_path.read_text())
    cm_path=BASE/'assembly/full25_accumulation_dispatch_v1/physical_macro.json';cm=json.loads(cm_path.read_text())
    assert cm['physical_implementation_completed']
    im_path=BASE/'assembly/full25_actor_ingress_v2/physical_macro.json';im=json.loads(im_path.read_text())
    count=1577;max_extra=21000+count*2*2000
    old_boxes=[b for n in old['routes'] for l,b in n['shapes']]+list(old['bounds_dbu'].values())
    oldbb=[min(b[0] for b in old_boxes),min(b[1] for b in old_boxes),max(b[2] for b in old_boxes),max(b[3] for b in old_boxes)]
    dw,dh=[round(v*1000) for v in cm['size_um']]
    origin=(oldbb[2]+2*max_extra+2000000,0)
    bounds={'INGRESS':old['bounds_dbu']['INGRESS'],'DISPATCH':(*origin,origin[0]+dw,dh)}
    origins={'INGRESS':old['origins_dbu']['INGRESS'],'DISPATCH':origin}
    top_y=max(oldbb[3],dh+max_extra)+2000000
    joins=[('group_valid_o','group_valid_i',25),('group_ready_i','group_ready_o',25),
           ('output_channel_base_o','channel_base_i',200),('output_lane_count_o','lane_count_i',200),
           ('output_x_o','x_i',250),('output_y_o','y_i',250),
           ('contribution_bin_tag_o','bin_tag_i',600),('group_settled_done_i','group_settled_done_o',25)]
    def node(side,pin):
        record=(im if side=='INGRESS' else cm)['ports'][pin];r=record['rectangles'][0]
        l=LAYERS[r['layer']];x,y=[round(v*1000) for v in r['center_um']];ox,oy=origins[side]
        return dict(instance=side,pin=pin,layer=l,xy_dbu=[x+ox,y+oy])
    routes=[]
    for a,b,width in joins:
        for bit in range(width):routes.append(dict(net=f'{b}[{bit}]',nodes=[node('INGRESS',f'{a}[{bit}]'),node('DISPATCH',f'{b}[{bit}]')]))
    for pin in ['clk','reset']:routes.append(dict(net=pin,nodes=[node('INGRESS',pin),node('DISPATCH',pin)]))
    assert len(routes)==1577
    terminal=0
    for index,net in enumerate(routes):
        track=top_y+index*3200;xs=[];shapes=[]
        for n in net['nodes']:
            side=n['instance'];l=n['layer'];x,y=n['xy_dbu'];bb=bounds[side]
            extra=21000+terminal*2000;terminal+=1
            if l==42:
                ex=bb[0]-extra if x<(bb[0]+bb[2])/2 else bb[2]+extra
                shapes.append(wire(42,(x,y),(ex,y)));shapes+=via(42,46,40,(ex,y))
                shapes.append(wire(46,(ex,y),(ex,track)));shapes+=via(46,81,41,(ex,track))
            elif l==46:
                ey=bb[1]-extra if y<(bb[1]+bb[3])/2 else bb[3]+extra;ex=bb[0]-extra
                shapes.append(wire(46,(x,y),(x,ey)));shapes+=via(46,81,41,(x,ey))
                shapes.append(wire(81,(x,ey),(ex,ey)));shapes+=via(46,81,41,(ex,ey))
                shapes.append(wire(46,(ex,ey),(ex,track)));shapes+=via(46,81,41,(ex,track))
            else:raise AssertionError(('unexpected signal layer',n))
            xs.append(ex)
        shapes.append(wire(81,(min(xs),track),(max(xs),track)))
        net.update(shapes=shapes,track_y_dbu=track)
    # All inherited routing is indexed too, so a new crossing cannot silently
    # short the existing1477 paths. Only named clock/reset joins are shared.
    paint=Paint();owners=[]
    for net in old['routes']:
        for l,b in net['shapes']:paint.add(l,tuple(b));owners.append(net['net'])
    conflicts=[]
    for net in routes:
        for l,b in net['shapes']:
            guard=460 if l==81 else 280 if l in [42,46] else 260
            q=(b[0]-guard,b[1]-guard,b[2]+guard,b[3]+guard)
            for hit in paint.hits(l,q):
                if owners[hit]!=net['net']:conflicts.append((net['net'],owners[hit],l,b,paint.shapes[hit][1]))
            adjacent=VIA.get(l,()) if l in VIA else [c for c,metals in VIA.items() if l in metals]
            for other in adjacent:
                for hit in paint.hits(other,b):
                    if owners[hit]!=net['net']:conflicts.append((net['net'],owners[hit],l,b,paint.shapes[hit][1]))
            paint.add(l,b);owners.append(net['net'])
    plan=dict(routes=routes,dispatcher_origin_dbu=origin,source_bounds_dbu=bounds,
              inherited_pair_bounds_dbu=oldbb,new_rectangles=sum(len(n['shapes']) for n in routes),
              conflicts=conflicts,inherited_routes_preserved=True,
              scope='1575 real ingress-to-dispatcher request/destination/tag/ready/completion signals plus2sharedclock/reset joins. Inherited1477route geometry remains unchanged. Native membrane output routing remains separate.')
    (OUT/'route_plan.json').write_text(json.dumps(plan,indent=2)+'\n');assert not conflicts,conflicts[:3]
    del paint
    pair_gds=ROOT/pair['gds'];prefix,cells=cells_read(pair_gds.read_bytes())
    dgds=next(ROOT/p for p in cm['sha256'] if p.endswith('.gds'));assert sha(dgds)==cm['sha256'][dgds.relative_to(ROOT).as_posix()]
    _,dc=cells_read(dgds.read_bytes())
    for name,blob in dc.items():
        new='DSP_'+name;assert new not in cells;cells[new]=renamed(blob,'DSP_')
    top='GF180_ACCUMULATION_DISPATCH_LINK_V2'
    body=reference(pair['top_cell'],0,0)+reference('DSP_'+cm['design'],*origin)
    body+=b''.join(rect(l,b) for net in routes for l,b in net['shapes'])
    body+=b''.join(label(net['net'],min(n['xy_dbu'][0] for n in net['nodes']),net['track_y_dbu']) for net in routes)
    cells[top]=begin(top)+body+rec(7,0)
    dest=OUT/'accumulation_dispatch_link_v2.gds'
    with dest.open('wb') as f:
        f.write(prefix)
        for blob in cells.values():f.write(blob)
        f.write(rec(4,0))
    report=dict(top_cell=top,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,
                ingress_dispatch_routes=1575,shared_clock_reset_joins=2,
                inherited_fabric_ingress_routes=1475,inherited_source_libraries_preserved=True,
                dispatcher_cell='DSP_'+cm['design'],native_membrane_outputs_bound=False,
                actual_gds_readback_pass=False,full_architecture_layout_complete=False,
                accumulation_5ms_accepted=False,scope=plan['scope'],elapsed_seconds=time.monotonic()-started,
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),pair_path,pair_proof,old_plan_path,pair_gds,cm_path,im_path,dgds,OUT/'route_plan.json',dest]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['gds','gds_bytes','ingress_dispatch_routes','elapsed_seconds']}),flush=True)


if __name__=='__main__':main()
