"""Route all categorical membrane address nets across the retained atlas.

Native numerical state is unchanged. Source exits use M1/M2; long routes use
two independent directional layer pairs. All candidates are checked against
retained parent wiring and accepted routes before being committed.
"""
from pathlib import Path
import json,time,collections,random
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
from assemble_gf180_full25_spike_graph_v16 import astar,compress
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from assemble_gf180_full25_physical_candidate_v5 import rect,label
from verify_gf180_full25_spike_graph_v16 import header_size
from prove_gf180_shared_page_parent_metal_v5 import VIA
from gf180_rect_index_v1 import RectIndex,touch

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_native_address_routes_v21'
METALS=[34,36,42,46,81];CUTS=[35,38,40,41]


def wire(l,a,b):
    assert a[0]==b[0] or a[1]==b[1]
    h=220 if l==81 else 140
    return l,(min(a[0],b[0])-h,min(a[1],b[1])-h,max(a[0],b[0])+h,max(a[1],b[1])+h)


def transition(a,b,p):
    x,y=p;lo,hi=sorted([METALS.index(a),METALS.index(b)]);shapes=[]
    for j in range(lo,hi):
        shapes.extend([(METALS[j],(x-230,y-230,x+230,y+230)),
                       (METALS[j+1],(x-230,y-230,x+230,y+230)),
                       (CUTS[j],(x-130,y-130,x+130,y+130))])
    return shapes


def initial_index(inputs):
    index=RectIndex();sources=[]
    p=BASE/'assembly/full25_accumulation_architecture_v17/route_plan.json';v17=json.loads(p.read_text());sources.append(p)
    for net in v17['routes']:
        for l,b in net['shapes']:index.add(l,b,'prior_spike__'+net['net'])
    ox,oy=v17['pair_origin_dbu']
    for folder in ['accumulation_fabric_ingress_v1','accumulation_dispatch_link_v2']:
        p=BASE/f'assembly/{folder}/route_plan.json';m=json.loads(p.read_text());sources.append(p)
        for net in m['routes']:
            for l,b in net['shapes']:index.add(l,(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy),'prior_control__'+net['net'])
    p=BASE/'assembly/full25_membrane_address_breakouts_v18/escape_plan.json';m=json.loads(p.read_text());sources.append(p)
    owner={(e['actor_index'],e['native_pin']):n['net'] for n in inputs['nets'] for e in n['endpoints']}
    origins={a['actor_index']:a['origin_top_dbu'] for a in m['actors']}
    for e in m['escapes']:
        ox,oy=origins[e['actor_index']];b=e['rectangle_local_dbu']
        index.add(81,(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy),owner[e['actor_index'],e['native_pin']])
    index.rebuild()
    # Compare spatial indexing with exhaustive lookup on actual prior geometry.
    rng=random.Random(9471622)
    for _ in range(48):
        l,b=index.shapes[rng.randrange(len(index.shapes))]
        q=(b[0]-460,b[1]-460,b[2]+460,b[3]+460)
        expected={i for i,(other,c) in enumerate(index.shapes) if other==l and touch(c,q)}
        assert set(index.hits(l,q))==expected,'Rectangle index missed actual geometry'
    return index,sources


def conflicts(index,shapes,owner,limit=5):
    result=[]
    for l,b in shapes:
        guard=460 if l==81 else 280 if l in METALS else 260
        q=(b[0]-guard,b[1]-guard,b[2]+guard,b[3]+guard)
        for i in index.hits(l,q):
            if index.owners[i]!=owner:result.append((owner,index.owners[i],l,b,index.shapes[i]))
            if len(result)>=limit:return result
        adjacent=VIA.get(l,()) if l in VIA else [c for c,metals in VIA.items() if l in metals]
        for other in adjacent:
            for i in index.hits(other,b):
                if index.owners[i]!=owner:result.append((owner,index.owners[i],l,b,index.shapes[i]))
                if len(result)>=limit:return result
    return result


def source_escape(n,i,macro,block,max_extra,horizontal):
    l=n['source']['layer'];x,y=n['source']['xy_top_dbu'];extra=20000+i*750
    bottom=block[1]-extra;inner_x=block[0]-max_extra-extra
    shapes=[]
    if l==42:
        ex=macro[0]-extra if x<(macro[0]+macro[2])/2 else macro[2]+extra
        shapes.append(wire(42,(x,y),(ex,y)));shapes+=transition(42,34,(ex,y))
        shapes.append(wire(34,(ex,y),(ex,bottom)));shapes+=transition(34,36,(ex,bottom))
    else:
        assert l==46
        ey=macro[1]-extra if y<(macro[1]+macro[3])/2 else macro[3]+extra;ex=macro[0]-extra
        shapes.append(wire(46,(x,y),(x,ey)));shapes+=transition(46,36,(x,ey))
        shapes.append(wire(36,(x,ey),(ex,ey)));shapes+=transition(36,34,(ex,ey))
        shapes.append(wire(34,(ex,ey),(ex,bottom)));shapes+=transition(34,36,(ex,bottom))
    shapes.append(wire(36,(ex,bottom),(inner_x,bottom)))
    shapes+=transition(36,horizontal,(inner_x,bottom))
    return shapes,(inner_x,bottom)


def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    input_path=BASE/'assembly/native_address_route_inputs_v1/routing_inputs.json';m=json.loads(input_path.read_text())
    for p,digest in m['sha256'].items():assert sha(ROOT/p)==digest,p
    meta=BASE/'assembly/full25_accumulation_dispatch_v19/physical_assembly.json';source_meta=json.loads(meta.read_text())
    source=ROOT/source_meta['gds'];assert sha(source)==source_meta['sha256'][source_meta['gds']]
    index,prior_paths=initial_index(m);prior_count=len(index.shapes)
    max_extra=20000+len(m['nets'])*750
    cb=m['categorical_block_bbox_dbu'];macro=m['dispatcher_macro_bbox_dbu']
    # Keep long routes outside the complete source-exit channel too.
    control_box=[cb[0]-2*max_extra-1000,cb[1]-max_extra-1000,cb[2],cb[3]]
    obstacles=[b['bbox_dbu'] if b['kind']!='categorical_control_and_parent_wiring' else control_box for b in m['obstacles']]
    actor_counts=collections.Counter();used=[set(),set()];routes=[];failures=[]
    for i,n in enumerate(m['nets']):
        ai=n['endpoints'][0]['actor_index'];assert all(e['actor_index']==ai for e in n['endpoints'])
        local_rank=actor_counts[ai];actor_counts[ai]+=1
        bb=m['actor_bounds_dbu'][str(ai)];branch_x=bb[0]-20000-local_rank*2000
        family=i%2;h,v=(36,34) if family==0 else (42,46)
        initial,inner=source_escape(n,i,macro,cb,max_extra,h)
        fixed_conflicts=conflicts(index,initial,n['net'])
        if fixed_conflicts:
            failures.append(dict(net=n['net'],stage='source_exit',conflicts=fixed_conflicts));break
        selected=None;attempts=[]
        candidates=[150000+(i//2)*750]+list(range(150000,700001,750))
        seen=set()
        for margin in candidates:
            if margin in seen or margin in used[family]:continue
            seen.add(margin)
            start=(control_box[0]-margin,inner[1]);end=(branch_x,bb[3]+margin)
            try:points=astar(start,end,obstacles,margin)
            except (AssertionError,RuntimeError) as error:
                attempts.append(dict(margin=margin,error=str(error)));continue
            shapes=initial+[wire(h,inner,start)];previous=h
            for a,b in zip(points,points[1:]):
                layer=h if a[1]==b[1] else v
                shapes+=transition(previous,layer,a);shapes.append(wire(layer,a,b));previous=layer
            shapes+=transition(previous,v,end)
            for e in n['endpoints']:
                x,y=e['xy_top_dbu'];p=(branch_x,y)
                shapes.append(wire(81,(x,y),p));shapes+=transition(81,v,p)
                shapes.append(wire(v,p,end))
            bad=conflicts(index,shapes,n['net'])
            if not bad:selected=(margin,points,shapes);break
            attempts.append(dict(margin=margin,conflicts=bad))
        if selected is None:
            failures.append(dict(net=n['net'],stage='global_route',attempts=attempts));break
        margin,points,shapes=selected;used[family].add(margin)
        for l,b in shapes:index.add(l,b,n['net'])
        routes.append(dict(net=n['net'],source=n['source'],endpoints=n['endpoints'],actor_index=ai,
                           family=family,margin_nm=margin,branch_x_dbu=branch_x,
                           source_exit_point_dbu=inner,global_points_dbu=points,shapes=shapes))
        if (i+1)%16==0:index.rebuild()
        if (i+1)%25==0:
            print(json.dumps(dict(routed=i+1,total=947,elapsed_seconds=round(time.monotonic()-started,1))),flush=True)
            (OUT/'progress.json').write_text(json.dumps(dict(routed=i+1,total=947,stage='routing',elapsed_seconds=time.monotonic()-started))+'\n')
    plan=dict(routes=routes,failures=failures,all947_routes_built=len(routes)==947,
              source_exit_envelope_dbu=control_box,obstacles_dbu=obstacles,
              retained_parent_rectangles=prior_count,new_rectangles=sum(len(n['shapes']) for n in routes),
              elapsed_seconds=time.monotonic()-started,
              scope='Candidate routes screened against retained parent/escape geometry and accepted nets, using exact sparse rectangle lookup and conservative spacing guards. Actual GDS connectivity/native endpoint readback and global loading remain required.')
    (OUT/'route_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    assert not failures,[(f["net"],f["stage"],len(f.get("attempts",[]))) for f in failures]
    top='ESS140K_NATIVE_ADDRESS_ROUTES_V21';dest=OUT/'eventspikeseg140k_native_address_routes_v21.gds'
    with source.open('rb') as inp,dest.open('wb') as out:
        remaining=source.stat().st_size-4
        while remaining:
            chunk=inp.read(min(1048576,remaining));assert chunk;out.write(chunk);remaining-=len(chunk)
        out.write(begin(top)+reference(source_meta['top_cell'],0,0))
        for net in routes:
            for l,b in net['shapes']:out.write(rect(l,b))
            out.write(label('MEM_ADDRESS__'+net['net'],*net['source']['xy_top_dbu']))
        out.write(rec(7,0)+rec(4,0))
    report=dict(top_cell=top,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,
                native_address_nets_routed=947,native_sink_endpoints=1622,
                source_child_library_byte_preserved=True,actual_gds_readback_pass=False,
                full_architecture_layout_complete=False,accumulation_5ms_accepted=False,
                scope=plan['scope'],elapsed_seconds=time.monotonic()-started,
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_rect_index_v1.py',input_path,meta,source,*prior_paths,OUT/'route_plan.json',dest]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['gds','native_address_nets_routed','new_rectangles'] if k in report}),flush=True)


if __name__=='__main__':main()
