"""Independent exact metal/via graph for incremental parent wiring, with child boundaries.

Flatten conductor geometry, not SPICE. Reject unsupported transforms/polygons,
unanchored touched child components, unintended aliases, opens, and floating additions.
This proves incremental metal connectivity only; native circuit/RC evidence is separate.
"""
from pathlib import Path
import argparse,collections,hashlib,json,struct,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full25_shared_page1024_v7 import labels
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_shared_page1024_v8';S=B/'assembly/full25_shared_ROOT128_v6'
METAL={34,36,42,46,75,81};VIA={35:(34,36),38:(36,42),40:(42,46),41:(46,81),141:(75,81)};LAYERS=METAL|set(VIA)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def polygon_rectangles(xy):
    pts=list(zip(xy[::2],xy[1::2]));assert pts[0]==pts[-1]
    assert all(a[0]==b[0] or a[1]==b[1] for a,b in zip(pts,pts[1:])),pts
    ys=sorted({p[1] for p in pts});result=[]
    for lo,hi in zip(ys,ys[1:]):
        mid=lo+hi;xs=sorted(a[0] for a,b in zip(pts,pts[1:]) if a[0]==b[0] and 2*min(a[1],b[1])<mid<2*max(a[1],b[1]))
        assert len(xs)%2==0
        for left,right in zip(xs[::2],xs[1::2]):
            if left<right:result.append((left,lo,right,hi))
    return result
class Paint:
    def __init__(self):self.shapes=[];self.parent=[];self.size=[];self.grid=collections.defaultdict(list);self.contact_count=0
    def root(self,i):
        while self.parent[i]!=i:self.parent[i]=self.parent[self.parent[i]];i=self.parent[i]
        return i
    def join(self,a,b):
        a=self.root(a);b=self.root(b)
        if a==b:return
        if self.size[a]<self.size[b]:a,b=b,a
        self.parent[b]=a;self.size[a]+=self.size[b]
    def keys(self,layer,box):
        a,b,c,d=box
        for x in range(a//10000,c//10000+1):
            for y in range(b//10000,d//10000+1):yield layer,x,y
    def hits(self,layer,box):
        candidates=set()
        for key in self.keys(layer,box):candidates.update(self.grid.get(key,()))
        a,b,c,d=box
        return [i for i in candidates if not(self.shapes[i][1][2]<a or self.shapes[i][1][0]>c or self.shapes[i][1][3]<b or self.shapes[i][1][1]>d)]
    def add(self,layer,box):
        i=len(self.parent);self.parent.append(i);self.size.append(1);self.shapes.append((layer,box))
        for j in self.hits(layer,box):self.join(i,j)
        for key in self.keys(layer,box):self.grid[key].append(i)
        return i
    def vias(self,start=0):
        for i in range(start,len(self.shapes)):
            layer,box=self.shapes[i]
            if layer not in VIA:continue
            for metal in VIA[layer]:
                hits=self.hits(metal,box);assert hits,('via_without_metal',layer,box,metal)
                for j in hits:self.join(i,j);self.contact_count+=1
    def at(self,layer,x,y):
        hits=self.hits(layer,(x,y,x,y));assert hits,('anchor_without_paint',layer,x,y)
        roots={self.root(i) for i in hits};assert len(roots)==1;return next(iter(roots))
def main():
    global D
    ap=argparse.ArgumentParser();ap.add_argument('--revision',type=int,choices=[7,8],default=8);ap.add_argument('--actor-index',type=int,default=0);ap.add_argument('--known-bad-control',action='store_true');args=ap.parse_args();D=B/'assembly'/f'full25_shared_page1024_v{args.revision}'
    started=time.monotonic();mf=D/'physical_assembly.json';m=json.loads(mf.read_text());g=D/'eventspikeseg140k_shared_page1024_v7.gds';_,cells=cells_read(g.read_bytes());_,old=cells_read((S/'eventspikeseg140k_shared_ROOT128_v6.gds').read_bytes());a=m['actor_regions'][args.actor_index];root=a['gds_cell'];newbody=list(elements(cells[root]));oldbody=list(elements(old[root]));assert newbody[:len(oldbody)]==oldbody
    out=D/f'actor_{args.actor_index:02d}_complete_boundary_metal_proof_v5.json';assert not out.exists();paint=Paint();cache={}
    def compiled(n):
        if n in cache:return cache[n]
        rs=[];children=[];caps=[];capdef=[]
        for e in elements(cells[n]):
            if e[0][0]!=8:continue
            lay=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
            if lay not in [75,117]:continue
            xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
            (caps if lay==75 else capdef).extend(polygon_rectangles(xy))
        for e in elements(cells[n]):
            typ=e[0][0]
            if typ==8:
                layer=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
                if layer not in LAYERS:continue
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                for box in polygon_rectangles(xy):
                    outlayer=layer
                    if layer==41:
                        x1,y1,x2,y2=box
                        inside=lambda rr:rr[0]<=x1 and rr[1]<=y1 and rr[2]>=x2 and rr[3]>=y2
                        overlaps=lambda rr:not(rr[2]<x1 or rr[0]>x2 or rr[3]<y1 or rr[1]>y2)
                        if any(inside(rr) for rr in caps):outlayer=141
                        elif any(overlaps(rr) for rr in caps+capdef):raise AssertionError(('unsupported_partial_MIM_via',n,box))
                    rs.append((outlayer,box))
            elif typ in [10,11]:
                assert all((t==26 and v==bytes(2)) or t not in [26,27,28] for t,d,v,b in e),'unsupported_transform'
                child=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18);xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16);nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1));dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0
                children.append((child,xy[0],xy[1],nx,ny,dx,dy))
            elif typ in [9]:raise AssertionError('unsupported_PATH')
        cache[n]=(rs,children);return cache[n]
    def local(n,ox=0,oy=0):
        own,children=compiled(n)
        for layer,(x1,y1,x2,y2) in own:yield layer,(x1+ox,y1+oy,x2+ox,y2+oy)
        for child,cx,cy,nx,ny,dx,dy in children:
            for iy in range(ny):
                for ix in range(nx):yield from local(child,ox+cx+ix*dx,oy+cy+iy*dy)
    # Stream immutable child paint into the graph; do not retain expanded copies.

    added=[]
    for ix,e in enumerate(newbody):
        typ=e[0][0]
        if typ in [10,11]:
            assert typ==10 and all((t==26 and v==bytes(2)) or t not in [26,27,28] for t,d,v,b in e)
            child=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18);ox,oy=next(struct.unpack('>2i',v) for t,d,v,b in e if t==16)
            for layer,box in local(child,ox,oy):paint.add(layer,box)
        elif typ==8:
            layer=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
            if layer not in LAYERS:continue
            xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
            for box in polygon_rectangles(xy):
                if ix<len(oldbody):paint.add(layer,box)
                else:added.append((layer,box))
        elif typ==9:raise AssertionError('unsupported_PATH')
    paint.vias();baseline_count=len(paint.shapes);baseline_roots=[paint.root(i) for i in range(baseline_count)]
    # Expected boundary-net assignment is from independent original source composition.
    pm={(s.split('.',1)[0],s.split('.',1)[1]):n['net'] for n in m['local_pin_nets'] if n['actor']==a['actor'] for s in n['endpoint_pins']};anchors=[]
    for name,(layer,x,y) in labels(old[root]).items():anchors.append((name,name,layer,x,y))
    pagep=next(p for p in a['modules'] if p['instance']=='page_service');page_root=pagep['gds_native_cell'];ox,oy=pagep['origin_dbu']
    for name,(layer,x,y) in labels(cells[page_root]).items():
        net='page_service__'+name if '__B' in name and '_STATE' in name else pm['page_service',name];anchors.append(('page_service.'+name,net,layer,x+ox,y+oy))
    from assemble_gf180_full25_physical_candidate_v5 import pinlist
    for p in a['modules']:
        if p['instance'] not in ['page_up','page_restore']:continue
        ox,oy=p['origin_dbu']
        for name,(layer,x,y) in pinlist(B/'layout'/p['cell'],p['cell']).items():anchors.append((p['instance']+'.'+name,pm[p['instance'],name],{'metal1':34,'metal2':36,'metal3':42,'metal4':46,'metal5':81}[layer],round(x+ox),round(y+oy)))
    # Include every original native module terminal, not only public parent ports.
    # Match the source-reference rule used for original native parent qualification.
    old_public=set(labels(old[root]))
    for p in a['modules']:
        if p['instance'] in ['page_service','page_up','page_restore']:continue
        ox,oy=p['origin_dbu'];dd=B/'layout'/p['cell'];qq=json.loads((dd/'qualification.json').read_text());pins=pinlist(dd,p['cell'])
        for name in qq['ports']:
            layer,x,y=pins[name];public=p['instance']+'__'+name;net=pm.get((p['instance'],name),public if public in old_public else 'internal__'+p['instance']+'__'+name)
            anchors.append((p['instance']+'.'+name,net,{'metal1':34,'metal2':36,'metal3':42,'metal4':46,'metal5':81}[layer],round(x+ox),round(y+oy)))
    known=collections.defaultdict(set);anchor_ids=[]
    for name,net,layer,x,y in anchors:
        rr=paint.at(layer,x,y);known[rr].add(net);anchor_ids.append((name,net,rr))
    initial_aliases={str(k):sorted(v) for k,v in known.items() if len(v)>1}
    touched=set()
    for layer,box in added:
        for j in paint.hits(layer,box):
            if j<baseline_count:touched.add(baseline_roots[j])
        if layer in VIA:
            for met in VIA[layer]:
                for j in paint.hits(met,box):
                    if j<baseline_count:touched.add(baseline_roots[j])
        else:
            for cut,metals in VIA.items():
                if layer in metals:
                    for j in paint.hits(cut,box):
                        if j<baseline_count:touched.add(baseline_roots[j])
        paint.add(layer,box)
    paint.vias(baseline_count)
    # Added metal can also overlap existing cut layers; connect those to new metal.
    for i in range(baseline_count):
        layer,box=paint.shapes[i]
        if layer in VIA:
            for met in VIA[layer]:
                for j in paint.hits(met,box):
                    if j>=baseline_count:paint.join(i,j)
    unknown=sorted(touched-set(known));netroots=collections.defaultdict(set);rootnets=collections.defaultdict(set)
    for name,net,rr in anchor_ids:netroots[net].add(paint.root(rr));rootnets[paint.root(rr)].add(net)
    shorts=[sorted(v) for v in rootnets.values() if len(v)>1];opens={k:len(v) for k,v in netroots.items() if len(v)>1};floating=[i for i in range(baseline_count,len(paint.shapes)) if paint.root(i) not in rootnets]
    port_errors=[]
    for name,(layer,x,y) in labels(cells[root]).items():
        rr=paint.at(layer,x,y)
        if rootnets.get(rr)!={name}:port_errors.append({'port':name,'actual_nets':sorted(rootnets.get(rr,set()))})
    ok=not(initial_aliases or unknown or shorts or opens or floating or port_errors)
    o={'incremental_metal_connectivity_accepted':ok,'actor_index':args.actor_index,'revision':args.revision,'known_bad_control':args.known_bad_control,'full_native_parent_extraction_completed':False,'native_parent_RC_qualified':False,'full_chip_complete':False,'streamed_hierarchy_without_expanded_geometry_cache':True,'baseline_conductor_rectangles':baseline_count,'added_conductor_rectangles':len(added),'boundary_anchors':len(anchors),'baseline_boundary_aliases':initial_aliases,'unknown_baseline_components_touched':unknown,'unintended_shorts':shorts,'expected_net_opens':opens,'floating_added_rectangles':floating,'parent_port_errors':port_errors,'elapsed_s':time.monotonic()-started,'scope':'Exactrectilinear GDS metal1..5/CAPM graph. GF180 VIA4 insideCAPM connectsM5 toMIMtop75,notM4;regularVIA4 connectsM4/M5. Classification followsnativeMagictech CAPM/CAPDEF rules;partialmaskcuts rejected. Allnativechildpolygons included. Newparent additions musttouchonly declaredboundarycomponents;everyexpectednet mustconnect,eachaddedshape anchored,andallrootports verified. PriorV6geometry byteprefix preserved. This is independentincrementalmetalproof,not fullnative extraction,deviceparameters,active-layer/LVS orRC proof. Childnative exactgraphs/sourceDRC separatelyrequired.','sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,g]}}
    out.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:(len(v) if isinstance(v,(list,dict)) else v) for k,v in o.items() if k not in ['sha256','scope']},indent=2))
    if args.known_bad_control:
        expected={'PAGE_RESTORE','PAGE_RESTOREB','PAGE_SHIFTED','EXTERNAL_COMPUTE_DATA','VDD','VSS'}
        assert not ok and any(expected.issubset(set(group)) for group in shorts)
    else:assert ok
if __name__=='__main__':main()
