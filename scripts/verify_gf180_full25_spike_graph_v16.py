"""Independently read V16 GDS and prove its incremental spike-wire graph."""
from pathlib import Path
import hashlib,json,struct
from assemble_gf180_full_capacity_storage_gds_v2 import records

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_spike_graph_v16'

def header_size(path):
    with path.open('rb') as f:
        while True:
            start=f.tell();h=f.read(4);n,t,d=struct.unpack('>HBB',h)
            if t==5:return start
            f.seek(n-4,1)

def same_bytes(a,b,n):
    while n:
        take=min(n,1048576);x=a.read(take);y=b.read(take)
        assert len(x)==len(y)==take and x==y,'Child library bytes changed'
        n-=take

def touch(a,b):return not(a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])

def main():
    dest=OUT/'gds_incremental_connectivity_v1.json';assert not dest.exists()
    metadata=OUT/'physical_assembly.json';m=json.loads(metadata.read_text())
    analog=BASE/'assembly/full25_spike_breakouts_v15/eventspikeseg140k_spike_breakouts_v15.gds'
    fabric=next(ROOT/p for p in m['sha256'] if '/orfs/results/' in p and p.endswith('/6_final.gds'))
    gds=ROOT/m['gds'];body_offset=analog.stat().st_size-4+fabric.stat().st_size-header_size(fabric)-4
    with gds.open('rb') as target,analog.open('rb') as source:
        same_bytes(source,target,analog.stat().st_size-4)
        with fabric.open('rb') as f:
            f.seek(header_size(fabric));same_bytes(f,target,fabric.stat().st_size-header_size(fabric)-4)
        tail=target.read()
    shapes=[];children=[];active=[]
    for t,d,v,raw in records(tail):
        if t==6:assert v.rstrip(b'\0').decode()==m['top_cell']
        if t in [8,10,12]:active=[]
        active.append((t,d,v))
        if t==17:
            kind=active[0][0]
            if kind==8:
                layer=next(struct.unpack('>h',v)[0] for t,d,v in active if t==13)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v in active if t==16)
                assert len(xy)==10 and xy[0:2]==xy[-2:]
                b=(min(xy[::2]),min(xy[1::2]),max(xy[::2]),max(xy[1::2]))
                assert set(zip(xy[::2],xy[1::2]))=={(b[0],b[1]),(b[0],b[3]),(b[2],b[1]),(b[2],b[3])}
                shapes.append((layer,b))
            elif kind==10:
                name=next(v.rstrip(b'\0').decode() for t,d,v in active if t==18)
                xy=next(struct.unpack('>2i',v) for t,d,v in active if t==16);children.append((name,list(xy)))
    assert len(shapes)==m['new_rectangles'] and len(children)==2
    assert children[0]==('ESS140K_SPIKE_BREAKOUTS_V15',[0,0])
    assert children[1]==('gf180_analog_full25_packet_fabric_v1',m['fabric_origin_dbu'])
    parents=list(range(len(shapes)))
    def root(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    def join(i,j):parents[root(j)]=root(i)
    metal={42,46,81};vias={40:(42,46),41:(46,81)}
    for i,(layer,b) in enumerate(shapes):
        if layer in metal:
            for j,(other,c) in enumerate(shapes[:i]):
                if layer==other and touch(b,c):join(i,j)
    for i,(layer,b) in enumerate(shapes):
        if layer not in vias:continue
        hits=[]
        for side in vias[layer]:
            found=[j for j,(other,c) in enumerate(shapes) if other==side and touch(b,c)]
            assert found,('Open via',i,side);hits.extend(found)
        for j in hits[1:]:join(hits[0],j)
    def anchor(layer,xy):
        hits={root(i) for i,(l,b) in enumerate(shapes) if l==layer and b[0]<=xy[0]<=b[2] and b[1]<=xy[1]<=b[3]}
        assert len(hits)==1,(layer,xy,hits)
        return next(iter(hits))
    owners={};proofs=[]
    for route in m['routes']:
        i=route['actor_index'];a=anchor(81,route['source']['xy_top_dbu'])
        b=anchor(route['destination']['layer'],route['destination']['xy_top_dbu'])
        assert a==b,('Spike wire open',i)
        assert a not in owners,('Spike nets shorted',i,owners.get(a))
        owners[a]=i;proofs.append({'actor_index':i,'source_and_destination_same_component':True})
    assert {root(i) for i,(l,b) in enumerate(shapes) if l in metal}==set(owners),'Floating new metal'
    spacing=[];minimum={42:280,46:280,81:460}
    for i,(layer,b) in enumerate(shapes):
        if layer not in metal:continue
        for j,(other,c) in enumerate(shapes[:i]):
            if layer!=other or root(i)==root(j):continue
            dx=max(b[0]-c[2],c[0]-b[2],0);dy=max(b[1]-c[3],c[1]-b[3],0)
            if dx*dx+dy*dy<minimum[layer]**2:spacing.append({'layer':layer,'actors':[owners[root(i)],owners[root(j)]],'boxes':[b,c]})
    result={'actual_gds_incremental_spike_connectivity_pass':True,'analog_child_library_byte_identical':True,
            'packet_fabric_child_library_byte_identical':True,'spike_connections_verified':25,
            'unintended_net_aliases':0,'opens':0,'floating_new_metal':0,'new_inter_net_metal_spacing_conflicts':spacing,
            'incremental_spacing_screen_pass':not spacing,'actors':proofs,'full_chip_layout_complete':False,
            'scope':'Actual streamed GDS child bytes, root references, all new rectangle/via contacts and25 distinct source/destination paths checked. Incremental M3/M4/M5 inter-net spacing screen only; no full-style DRC, loaded RC/timing, phase/control/synapse binding or model/service acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [metadata,gds,Path(__file__)]}}
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['actors','sha256','new_inter_net_metal_spacing_conflicts']},indent=2));print('spacing_conflicts',len(spacing))

if __name__=='__main__':main()
