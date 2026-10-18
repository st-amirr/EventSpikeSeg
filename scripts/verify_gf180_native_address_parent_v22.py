"""Read actual appended GDS and prove the incremental parent metal graph.

Native macro-edge contact qualification is a separate required check.
"""
from pathlib import Path
import collections,json,struct,time
from assemble_gf180_full_capacity_storage_gds_v2 import records
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
from gf180_rect_index_v1 import RectIndex,touch
from prove_gf180_shared_page_parent_metal_v5 import VIA
from route_gf180_native_addresses_v22 import initial_index,conflicts

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_native_address_routes_v22'


def main():
    started=time.monotonic();dest=OUT/'parent_graph_readback_v1.json'
    assert not dest.exists()
    meta=OUT/'physical_assembly.json';m=json.loads(meta.read_text())
    for p,d in m['sha256'].items():assert sha(ROOT/p)==d,p
    oldmeta=BASE/'assembly/full25_accumulation_dispatch_v19/physical_assembly.json'
    old=json.loads(oldmeta.read_text());source=ROOT/old['gds'];gds=ROOT/m['gds']
    with source.open('rb') as a,gds.open('rb') as b:
        remaining=source.stat().st_size-4
        while remaining:
            n=min(1048576,remaining);assert a.read(n)==b.read(n);remaining-=n
        suffix=b.read()
    actual=[];refs=[];kind=None;layer=None;xy=None;child=None
    for t,d,v,raw in records(suffix):
        if t in (8,10,12):kind=t;layer=None;xy=None;child=None
        elif t==13:layer=struct.unpack('>h',v)[0]
        elif t==16:xy=struct.unpack('>'+str(len(v)//4)+'i',v)
        elif t==18:child=v.rstrip(b'\0').decode()
        elif t==6:assert v.rstrip(b'\0').decode()==m['top_cell']
        elif t==17:
            if kind==8:
                assert len(xy)==10 and xy[:2]==xy[-2:]
                xs=xy[::2];ys=xy[1::2];box=(min(xs),min(ys),max(xs),max(ys))
                assert set(zip(xs,ys))=={(box[0],box[1]),(box[0],box[3]),(box[2],box[1]),(box[2],box[3])}
                actual.append((layer,box))
            elif kind==10:refs.append((child,xy))
            else:assert kind==12
            kind=None
        else:assert t in (4,5,7,14,22,25),('unsupported appended record',t)
    assert refs==[(old['top_cell'],(0,0))]
    plan=json.loads((OUT/'route_plan.json').read_text());assert plan['all947_routes_built']
    expected=collections.Counter((l,tuple(b)) for n in plan['routes'] for l,b in n['shapes'])
    assert collections.Counter(actual)==expected
    owners={}
    for n in plan['routes']:
        for l,b in n['shapes']:
            key=l,tuple(b);assert key not in owners or owners[key]==n['net'];owners[key]=n['net']
    idx=RectIndex()
    for l,b in actual:idx.add(l,b,owners[l,b])
    idx.rebuild();parent=list(range(len(actual)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def join(i,j):
        a,b=root(i),root(j)
        if a!=b:parent[b]=a
    for i,(l,b) in enumerate(actual):
        for j in idx.hits(l,b):join(i,j)
        if l in VIA:
            for metal in VIA[l]:
                hits=idx.hits(metal,b);assert hits,('unlanded via',i,metal)
                for j in hits:join(i,j)
    roots=collections.defaultdict(set)
    for i,owner in enumerate(idx.owners):roots[root(i)].add(owner)
    assert len(roots)==947 and all(len(v)==1 for v in roots.values()),'open, floating or aliased route'
    for n in plan['routes']:
        anchors=[n['source'],*n['endpoints']];rr=set()
        for a in anchors:
            x,y=a['xy_top_dbu'];hits=idx.hits(a['layer'],(x,y,x,y));assert hits,(n['net'],a)
            rr.update(root(i) for i in hits)
        assert len(rr)==1 and roots[next(iter(rr))]=={n['net']}
    inputs=json.loads((BASE/'assembly/native_address_route_inputs_v1/routing_inputs.json').read_text())
    prior,paths=initial_index(inputs)
    for n in plan['routes']:
        shapes=[(l,tuple(b)) for l,b in n['shapes']]
        assert not conflicts(prior,shapes,n['net']),n['net']
    # Independently check spacing between all actual new-net shapes too.
    for n in plan['routes']:
        assert not conflicts(idx,[(l,tuple(b)) for l,b in n['shapes']],n['net']),n['net']
    report=dict(parent_graph_readback_pass=True,source_library_byte_preserved=True,
                native_address_nets=947,sink_endpoints=1622,actual_parent_rectangles=len(actual),
                native_macro_edge_contact_readback_pass=False,full_architecture_layout_complete=False,
                accumulation_5ms_accepted=False,elapsed_seconds=time.monotonic()-started,
                scope='Actual appended GDS graph: source library preserved; all947 parent nets connected to1622 coordinate anchors; no parent aliases, floating pieces, unlanded cuts, new/new or retained-parent spacing/contact conflicts. Native macro edge and core collision checks remain separate and required. No DRC/RC or analog timing claim.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),meta,gds,OUT/'route_plan.json']})
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
