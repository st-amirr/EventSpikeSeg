"""Connect the 25 actor/forest supply pairs to two external research rails.

This establishes connectivity only; global IR/EM/loading are not qualified.
"""
from pathlib import Path
import json,time
from route_gf180_native_addresses_v23 import initial_index,wire,transition,conflicts,astar,occupied_astar
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from assemble_gf180_full25_physical_candidate_v5 import rect,label

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_analog_supplies_v25'


def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    source_dir=BASE/'assembly/full25_analog_interfaces_v24'
    proof=source_dir/'independent_readback_v1.json';assert json.loads(proof.read_text())['readback_pass']
    meta=source_dir/'physical_assembly.json';m=json.loads(meta.read_text())
    source=ROOT/m['gds'];assert sha(source)==m['sha256'][m['gds']]
    escape_path=source_dir/'escape_plan.json';escape=json.loads(escape_path.read_text())
    input_path=BASE/'assembly/native_address_route_inputs_v1/routing_inputs.json';inputs=json.loads(input_path.read_text())
    index,prior_paths=initial_index(inputs)
    address_path=BASE/'assembly/full25_native_address_routes_v23/route_plan.json';ap=json.loads(address_path.read_text())
    for n in ap['routes']:
        for l,b in n['shapes']:index.add(l,b,n['net'])
    actorbounds={int(k):list(b) for k,b in inputs['actor_bounds_dbu'].items()}
    for e in escape['escapes']:
        ox,oy=m['actors'][e['actor_index']]['origin_top_dbu'];b=e['rectangle_local_dbu']
        box=(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)
        owner=e['native_pin'] if e['native_pin'] in ('VDD','VSS') else f"EXT_{e['actor_index']}_{e['endpoint_kind']}_{e['native_pin']}"
        index.add(81,box,owner);bb=actorbounds[e['actor_index']]
        bb[0]=min(bb[0],box[0]);bb[1]=min(bb[1],box[1]);bb[2]=max(bb[2],box[2]);bb[3]=max(bb[3],box[3])
    index.rebuild()
    obstacles=[actorbounds[o['actor_index']] if o['kind']=='native_actor' else ap['source_exit_envelope_dbu'] if o['kind']=='categorical_control_and_parent_wiring' else o['bbox_dbu'] for o in inputs['obstacles']]
    left=min(b[0] for b in obstacles)-5000000;bottom=min(b[1] for b in obstacles)-5000000
    routes=[];failures=[];external=[]
    for ni,net in enumerate(('VDD','VSS')):
        h,v=(42,46) if ni==0 else (36,34)
        start=(left-ni*20000,bottom-ni*20000);external.append(dict(net=net,layer=h,xy_top_dbu=start))
        for ai in range(25):
            ends=[e for e in escape['escapes'] if e['actor_index']==ai and e['native_pin']==net]
            assert len(ends)==2
            bb=actorbounds[ai];bx=bb[0]-20000-ni*20000
            selected=None;attempts=[]
            for margin in [50000,100000,250000,500000,750000,1000000,1500000,2000000,3000000,4000000]:
                end=(bx,bb[3]+margin)
                tail=[]
                for e in ends:
                    x,y=e['escaped_top_dbu'];p=(bx,y)
                    tail += [wire(81,(x,y),p)]+transition(81,v,p)+[wire(v,p,end)]
                if conflicts(index,tail,net):
                    attempts.append(dict(margin=margin,stage='branch',conflicts=conflicts(index,tail,net)));continue
                for occupied in (False,True):
                    try:points=occupied_astar(start,end,obstacles,margin,index,net,h,v) if occupied else astar(start,end,obstacles,margin)
                    except (RuntimeError,AssertionError) as error:
                        attempts.append(dict(margin=margin,occupied=occupied,error=str(error)));continue
                    shapes=[];previous=h
                    for a,b in zip(points,points[1:]):
                        layer=h if a[1]==b[1] else v
                        shapes+=transition(previous,layer,a)+[wire(layer,a,b)];previous=layer
                    shapes+=transition(previous,v,end)+tail
                    bad=conflicts(index,shapes,net)
                    if bad:attempts.append(dict(margin=margin,occupied=occupied,conflicts=bad));continue
                    selected=(points,shapes,margin);break
                if selected:break
            if not selected:
                failures.append(dict(net=net,actor_index=ai,attempts=attempts));break
            points,shapes,margin=selected
            routes.append(dict(net=net,actor_index=ai,source=external[-1],endpoints=ends,shapes=shapes,global_points_dbu=points,margin_nm=margin))
            for l,b in shapes:index.add(l,b,net)
            index.rebuild()
            print(json.dumps(dict(supply=net,actor=ai,routed=len(routes),elapsed_seconds=round(time.monotonic()-started,1))),flush=True)
        if failures:break
    plan=dict(routes=routes,failures=failures,external_supply_terminals=external,obstacles_dbu=obstacles,
              all_analog_actor_supply_pairs_routed=len(routes)==50,elapsed_seconds=time.monotonic()-started,
              scope='Physical analog actor/forest VDD/VSS joins only; categorical supplies and other native assemblies remain separate. Research thin-metal connections, not sized power delivery: IR/EM/global RC unqualified.')
    (OUT/'route_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    assert not failures,[(f['net'],f['actor_index']) for f in failures]
    top='ESS140K_ANALOG_SUPPLIES_V25';dest=OUT/'eventspikeseg140k_analog_supplies_v25.gds'
    with source.open('rb') as inp,dest.open('wb') as out:
        remaining=source.stat().st_size-4
        while remaining:
            chunk=inp.read(min(1048576,remaining));out.write(chunk);remaining-=len(chunk)
        out.write(begin(top)+reference(m['top_cell'],0,0))
        for n in routes:
            for l,b in n['shapes']:out.write(rect(l,b))
        for n in external:out.write(label('EXT_ANALOG_'+n['net'],*n['xy_top_dbu'],layer=n['layer']))
        out.write(rec(7,0)+rec(4,0))
    report=dict(top_cell=top,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,
                analog_actor_supply_endpoint_count=100,actual_gds_readback_pass=False,
                global_supply_distribution_complete=False,full_architecture_layout_complete=False,
                accumulation_5ms_accepted=False,scope=plan['scope'],
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),meta,proof,source,escape_path,input_path,address_path,OUT/'route_plan.json',dest]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
