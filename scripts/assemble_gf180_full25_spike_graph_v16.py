"""Route actual V15 scalar SPIKE outputs into the completed packet fabric.

Preserve the research atlas and both child GDS libraries. Only 25 categorical
spike wires are added; sample/address/control and numerical synapse bindings
remain required. This is neither a compact die nor a loaded timing claim.
"""
from pathlib import Path
import hashlib,heapq,json,math,struct
from assemble_gf180_one_neuron_page_link_v1 import gds_library_parts,text_pins
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference,real8,records
from assemble_gf180_full25_physical_candidate_v5 import rect,label

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_spike_graph_v16'

def overlap(a,b):return not(a[2]<=b[0] or a[0]>=b[2] or a[3]<=b[1] or a[1]>=b[3])
def box(a,b,half):return (min(a[0],b[0])-half,min(a[1],b[1])-half,max(a[0],b[0])+half,max(a[1],b[1])+half)
def compress(points):
    result=[]
    for p in points:
        if result and p==result[-1]:continue
        if len(result)>1 and ((result[-2][0]==result[-1][0]==p[0]) or (result[-2][1]==result[-1][1]==p[1])):result[-1]=p
        else:result.append(p)
    return result

def astar(start,end,obstacles,margin):
    xs=sorted({start[0],end[0]}|{v for b in obstacles for v in [b[0]-margin,b[2]+margin]})
    ys=sorted({start[1],end[1]}|{v for b in obstacles for v in [b[1]-margin,b[3]+margin]})
    sx,sy=xs.index(start[0]),ys.index(start[1]);ex,ey=xs.index(end[0]),ys.index(end[1])
    valid={};edge_cache={}
    def point_ok(i,j):
        key=i,j
        if key not in valid:valid[key]=not any(b[0]-1000<xs[i]<b[2]+1000 and b[1]-1000<ys[j]<b[3]+1000 for b in obstacles)
        return valid[key]
    def edge_ok(a,b):
        key=tuple(sorted((a,b)))
        if key not in edge_cache:
            q=box((xs[a[0]],ys[a[1]]),(xs[b[0]],ys[b[1]]),500)
            edge_cache[key]=not any(overlap(q,o) for o in obstacles)
        return edge_cache[key]
    assert point_ok(sx,sy) and point_ok(ex,ey)
    queue=[(0,0,(sx,sy),None)];best={(sx,sy):0};parents={};target=(ex,ey)
    while queue:
        _,cost,here,previous=heapq.heappop(queue)
        if cost!=best[here]:continue
        if here==target:
            path=[here]
            while path[-1]!=(sx,sy):path.append(parents[path[-1]])
            return compress([(xs[i],ys[j]) for i,j in path[::-1]])
        i,j=here
        for next_node in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
            u,v=next_node
            if not(0<=u<len(xs) and 0<=v<len(ys)) or not point_ok(u,v) or not edge_ok(here,next_node):continue
            new=cost+abs(xs[u]-xs[i])+abs(ys[v]-ys[j])
            if new>=best.get(next_node,10**30):continue
            best[next_node]=new;parents[next_node]=here
            h=abs(xs[u]-end[0])+abs(ys[v]-end[1]);heapq.heappush(queue,(new+h,new,next_node,here))
    raise RuntimeError(('No outside-macro path',start,end))

def main():
    assert not OUT.exists();OUT.mkdir()
    analog_dir=BASE/'assembly/full25_spike_breakouts_v15'
    analog_meta=analog_dir/'physical_assembly.json';am=json.loads(analog_meta.read_text())
    analog_gds=ROOT/am['gds'];proof_path=analog_dir/'full_parent_readback_v1.json';proof=json.loads(proof_path.read_text())
    assert proof['full_parent_escape_contacts_accepted'] and proof['existing_state_geometry_and_array_multiplicities_preserved']
    original_meta=BASE/'assembly/full25_class_current_service_v13/physical_assembly.json';original=json.loads(original_meta.read_text())
    fabric_dir=BASE/'assembly/full25_packet_fabric_v1';status=json.loads((fabric_dir/'status.json').read_text());assert status['stage']=='physical_macro_completed'
    macro=fabric_dir/'physical_macro.json';fm=json.loads(macro.read_text());contract=fabric_dir/'final_boundary_contract_v1.json';boundary=json.loads(contract.read_text())
    fabric_gds=BASE/'orfs/results/gf180'/status['design']/status['variant']/'6_final.gds'
    assert fm['sha256'][fabric_gds.relative_to(ROOT).as_posix()]==hashlib.sha256(fabric_gds.read_bytes()).hexdigest()
    placements=original['top_placements'];obstacles=[tuple(p['bbox_dbu']) for p in placements]
    maxx=max(b[2] for b in obstacles);miny=min(b[1] for b in obstacles)
    origin=(maxx+10000000,miny+10000000);width,height=[round(v*1000) for v in fm['size_um']]
    hub_box=(origin[0],origin[1],origin[0]+width,origin[1]+height);obstacles.append(hub_box)
    assert max(abs(v) for b in obstacles for v in b)<2100000000
    # Independently compare actual GDS TEXT pin anchors with the ODB contract.
    gds_pins=text_pins(fabric_gds,status['design'])
    routes=[];shapes=[];body=reference(am['top_cell'],0,0)+reference(status['design'],*origin)
    def paint(layer,b,owner):
        nonlocal body
        body+=rect(layer,b);shapes.append((owner,layer,tuple(map(round,b))))
    def contact(low,high,cut,point,owner):
        x,y=point
        for layer,h in [(low,220),(high,220),(cut,130)]:paint(layer,(x-h,y-h,x+h,y+h),owner)
    for i,(source,destination) in enumerate(zip(proof['actors'],boundary['spike_inputs'])):
        assert source['actor_index']==destination['actor_index']==i
        s=tuple(source['output_top_dbu']);tx,ty=destination['center_gds_nm'];target=(tx+origin[0],ty+origin[1])
        gds_layer,gx,gy=gds_pins[destination['port']]
        expected={'Metal3':42,'Metal4':46}[destination['layer']]
        b=destination['bbox_odb_dbu'];assert gds_layer==expected
        assert b[0]/2-1<=gx<=b[2]/2+1 and b[1]/2-1<=gy<=b[3]/2+1
        owner=am['actors'][i];native_box=owner['enclosing_top_bbox_dbu']
        margin=100000+i*2000
        escape_x=native_box[0]-margin
        escape_y=(native_box[3]+margin if abs(s[1]-native_box[3])<abs(s[1]-native_box[1]) else native_box[1]-margin)
        start=(escape_x,escape_y)
        if expected==42:
            side_left=tx<width/2;ex=hub_box[0]-margin if side_left else hub_box[2]+margin
            ey=hub_box[1]-margin if abs(ty)<abs(ty-height) else hub_box[3]+margin
            end=(ex,ey);tail=[(ex,target[1]),target]
        else:
            ey=hub_box[1]-margin if ty<height/2 else hub_box[3]+margin
            end=(target[0],ey);tail=[target]
        middle=astar(start,end,obstacles,margin)
        points=compress([s,(escape_x,s[1]),*middle,*tail])
        segments=[]
        for j,(a,b) in enumerate(zip(points,points[1:])):
            assert a[0]==b[0] or a[1]==b[1]
            layer=81 if a[1]==b[1] else 46
            if expected==42 and j==len(points)-2:layer=42
            half={81:220,46:200,42:140}[layer];q=box(a,b,half)
            # Only the final input-pin approach may enter the hub boundary.
            for oi,o in enumerate(obstacles):
                if oi==len(obstacles)-1 and j==len(points)-2:continue
                assert not overlap(q,o),(i,'macro intrusion',j,oi)
            paint(layer,q,i);segments.append({'layer':layer,'from':a,'to':b,'box_dbu':q})
        for j in range(len(segments)-1):
            low,high=sorted([segments[j]['layer'],segments[j+1]['layer']])
            if low==high:continue
            if {low,high}=={46,81}:contact(46,81,41,points[j+1],i)
            elif {low,high}=={42,46}:contact(42,46,40,points[j+1],i)
            else:raise AssertionError(('Unsupported layer junction',i,low,high))
        body+=label(f'ACTOR_{i:02d}_SPIKE_TO_FABRIC',s[0],s[1])
        routes.append({'actor_index':i,'actor':owner['actor'],'source':{'cell':owner['source_cell'],'pin':'SPIKE_RESULT','xy_top_dbu':s},
                       'destination':{'instance':'PACKET_FABRIC','pin':destination['port'],'layer':expected,'xy_top_dbu':target},
                       'points_dbu':points,'segments':segments,'length_um':sum(abs(a[0]-b[0])+abs(a[1]-b[1]) for a,b in zip(points,points[1:]))/1000})
    # Reject shorts between newly added nets on every conductor/cut layer.
    conflicts=[]
    for j,(owner,layer,b) in enumerate(shapes):
        for other,other_layer,c in shapes[:j]:
            if owner!=other and layer==other_layer and overlap(b,c):conflicts.append((owner,other,layer,b,c))
    report={'routes_built':len(routes),'routes':routes,'new_rectangles':len(shapes),'new_net_overlap_conflicts':conflicts,
            'all_paths_avoid_unrelated_macro_bounds':True,'actual_gds_input_pin_anchors_checked':25,
            'fabric_origin_dbu':origin,'fabric_bbox_dbu':hub_box,'full_chip_layout_complete':False,
            'scope':'25 actual SPIKE conductors connect to matching scalar result inputs through outside-macro M4/M5 tracks and M3/M4 input approaches. No new-net overlap. Native child cells preserved. This retains the spacious research atlas, not a compact die. New routing spacing/RC/loading, shared supplies and clock/reset/sample/address/last/parameter controls, analog synapses, accuracy and5ms service remain unqualified.'}
    (OUT/'route_plan.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not conflicts, conflicts[:3]
    ah,ac,an=gds_library_parts(analog_gds);fh,fc,fn=gds_library_parts(fabric_gds)
    assert an.isdisjoint(fn),(an&fn)
    for head in [ah,fh]:
        units=next(v for t,d,v,b in records(head) if t==3);assert abs(real8(units[8:])-1e-9)<1e-18
    top='ESS140K_SPIKE_GRAPH_V16';topblob=begin(top)+body+rec(7,0)
    out=OUT/'eventspikeseg140k_spike_graph_v16.gds';out.write_bytes(ah+ac+fc+topblob+rec(4,0))
    report.update(top_cell=top,gds=out.relative_to(ROOT).as_posix(),gds_bytes=out.stat().st_size,
                  all_existing_analog_state_geometry_retained=True,analog_output_graph_pin_connections_built=25,
                  remaining_required_bindings=['shared supplies/clock/reset','settled sample-valid','per-neuron canonical address/bin tag','full-population last-result marker','graph ingress to analog synapse/weight service','trained analog parameter delivery','phase/address producers'])
    inputs=[Path(__file__),analog_gds,analog_meta,proof_path,original_meta,macro,contract,fabric_gds,out]
    report['sha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'gds':str(out),'bytes':out.stat().st_size,'actual_spike_connections':25,'new_wire_rectangles':len(shapes),'new_net_conflicts':len(conflicts),'full_chip_layout_complete':False},indent=2))

if __name__=='__main__':main()
