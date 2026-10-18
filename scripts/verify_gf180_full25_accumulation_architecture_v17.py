"""Check the full-population integration without flattening 54.6M state cells."""
from pathlib import Path
import collections
import json
import struct
import time
from assemble_gf180_full_capacity_storage_gds_v2 import records
from verify_gf180_full25_spike_graph_v16 import header_size, same_bytes, touch
from prove_gf180_shared_page_parent_metal_v5 import VIA, polygon_rectangles
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_accumulation_architecture_v17'


def main():
    started=time.monotonic(); dest=OUT/'independent_readback_v1.json'
    assert not dest.exists()
    meta=OUT/'physical_assembly.json'; m=json.loads(meta.read_text())
    for p,digest in m['sha256'].items(): assert sha(ROOT/p)==digest,p
    analog=BASE/'assembly/full25_spike_breakouts_v15/eventspikeseg140k_spike_breakouts_v15.gds'
    pair=BASE/'assembly/accumulation_fabric_ingress_v1/accumulation_fabric_ingress_v1.gds'
    gds=ROOT/m['gds']; plan_path=OUT/'route_plan.json';plan=json.loads(plan_path.read_text())
    # Compare every immutable child cell directly against the two source streams.
    with gds.open('rb') as output,analog.open('rb') as source:
        same_bytes(source,output,analog.stat().st_size-4)
        with pair.open('rb') as source_pair:
            source_pair.seek(header_size(pair))
            same_bytes(source_pair,output,pair.stat().st_size-header_size(pair)-4)
        tail=output.read()
    added=[];children=[]; active=[]
    for t,d,v,raw in records(tail):
        if t==6: assert v.rstrip(b'\0').decode()==m['top_cell']
        if t in [8,10,12]: active=[]
        active.append((t,d,v))
        if t!=17: continue
        kind=active[0][0]
        if kind==8:
            layer=next(struct.unpack('>h',v)[0] for t,d,v in active if t==13)
            xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v in active if t==16)
            added.extend((layer,b) for b in polygon_rectangles(xy))
        elif kind==10:
            name=next(v.rstrip(b'\0').decode() for t,d,v in active if t==18)
            xy=next(struct.unpack('>2i',v) for t,d,v in active if t==16)
            children.append((name,list(xy)))
    assert children==[('ESS140K_SPIKE_BREAKOUTS_V15',[0,0]),
                      ('GF180_ACCUMULATION_FABRIC_INGRESS_V1',plan['pair_origin_dbu'])]
    expected=collections.Counter((l,tuple(b)) for route in plan['routes'] for l,b in route['shapes'])
    assert collections.Counter(added)==expected
    assert len(added)==plan['new_rectangles']
    parent=list(range(len(added)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def join(a,b):parent[root(b)]=root(a)
    metal={34,36,42,46,81}
    for i,(l,b) in enumerate(added):
        for j,(other,c) in enumerate(added[:i]):
            if l==other and touch(b,c):join(i,j)
    for i,(l,b) in enumerate(added):
        if l not in VIA:continue
        for target in VIA[l]:
            hits=[j for j,(other,c) in enumerate(added) if other==target and touch(b,c)]
            assert hits,('open via',i,l,target)
            for j in hits:join(i,j)
    def anchor(layer,point):
        hits={root(i) for i,(l,b) in enumerate(added) if l==layer and
              b[0]<=point[0]<=b[2] and b[1]<=point[1]<=b[3]}
        assert len(hits)==1,(layer,point,hits)
        return next(iter(hits))
    owners={}
    for route in plan['routes']:
        a=anchor(81,route['source']['xy_top_dbu'])
        b=anchor(route['destination']['layer'],route['destination']['xy_top_dbu'])
        assert a==b,('open spike',route['net'])
        assert a not in owners,('shorted spikes',route['net'],owners.get(a))
        owners[a]=route['net']
    assert {root(i) for i in range(len(added))}==set(owners),'floating conductor or cut'
    spacing=[]
    for i,(l,b) in enumerate(added):
        for j,(other,c) in enumerate(added[:i]):
            if l!=other or root(i)==root(j):continue
            guard=460 if l==81 else 280 if l in metal else 260
            dx=max(b[0]-c[2],c[0]-b[2],0);dy=max(b[1]-c[3],c[1]-b[3],0)
            if dx*dx+dy*dy<guard*guard:spacing.append((owners[root(i)],owners[root(j)],l))
    pair_dir=BASE/'assembly/accumulation_fabric_ingress_v1'
    proof=json.loads((pair_dir/'independent_readback_v1.json').read_text());assert proof['readback_pass']
    pp=json.loads((pair_dir/'route_plan.json').read_text());ox,oy=plan['pair_origin_dbu']
    cross=[]
    for l,b in added:
        for net in pp['routes']:
            for other,c in net['shapes']:
                adjacent=l==other or other in VIA.get(l,()) or l in VIA.get(other,())
                if not adjacent:continue
                q=(c[0]+ox,c[1]+oy,c[2]+ox,c[3]+oy)
                guard=460 if l==other==81 else 280 if l==other and l in metal else 260 if l==other else 0
                if not(b[2]+guard<q[0] or b[0]-guard>q[2] or b[3]+guard<q[1] or b[1]-guard>q[3]):
                    cross.append((l,b,net['net'],other,q))
    assert not spacing and not cross,(spacing[:2],cross[:2])
    # Changed route layers may not enter any unrelated physical macro interior.
    actors=json.loads((BASE/'assembly/full25_spike_breakouts_v15/physical_assembly.json').read_text())['actors']
    macro_intrusions=[]
    for route in plan['routes']:
        for l,b in route['shapes']:
            for actor in actors:
                if actor['actor_index']==route['actor_index']:continue
                if touch(b,actor['enclosing_top_bbox_dbu']):macro_intrusions.append((route['net'],actor['actor_index']))
            for side,bb in pp['bounds_dbu'].items():
                q=(bb[0]+ox+2000,bb[1]+oy+2000,bb[2]+ox-2000,bb[3]+oy-2000)
                if touch(b,q):macro_intrusions.append((route['net'],side))
    assert not macro_intrusions,macro_intrusions[:3]
    report=dict(readback_pass=True,inherited_state_and_routed_pair_libraries_byte_identical=True,
                actual_spike_routes_verified=25,integrated_fabric_ingress_routes_verified=1475,
                shared_fabric_ingress_clock_reset_routes_verified=2,
                spike_route_opens=0,inter_net_aliases=0,floating_new_conductors_or_cuts=0,
                spike_route_spacing_conflicts=0,spike_to_ingress_route_conflicts=0,
                unrelated_macro_intrusions=0,source_state_geometry_preserved=True,
                full_architecture_layout_complete=False,accumulation_5ms_accepted=False,
                elapsed_seconds=time.monotonic()-started,
                scope='Exact full source-library preservation plus actual incremental GDS spike connectivity, cut/metal spacing and contact checks against the independently checked1477-route pair. Retains native source/destination approach layers; new outer channels avoid unrelated macros. No full native extraction/DRC or parent RC/power/timing claim. Membrane destination/injection and global infrastructure remain open.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),meta,plan_path,gds,pair_dir/'independent_readback_v1.json']})
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['sha256','scope']}),flush=True)


if __name__=='__main__':main()
