"""Exact new-wire graph with qualified forest fields and actual actor intersections.

Actor root paint is retained in full. Native descendants are retained in full only
when their actual recursive geometry bbox intersects a new parent wire. Omitted
subtrees therefore cannot touch any addition; this is a conservative contact proof.
"""
from pathlib import Path
import argparse,collections,functools,hashlib,json,struct,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full25_shared_page1024_v7 import labels
from prove_gf180_shared_page_parent_metal_v5 import polygon_rectangles
import audit_gf180_page_forest_v2 as spatial
R=Path(__file__).resolve().parents[1];D=R/'artifacts/analog_asic/assembly/full25_class_current_service_v13';MET={34,36,42,46,75,81};VIA={35:(34,36),38:(36,42),40:(42,46),41:(46,81),141:(75,81)}
spatial.MET=MET;spatial.VIA=VIA
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--actor-index',type=int,required=True);args=ap.parse_args();start=time.monotonic();mf=D/'physical_assembly.json';m=json.loads(mf.read_text());g=D/'eventspikeseg140k_class_current_service_v13.gds';_,cells=cells_read(g.read_bytes());w=[m['class_current_service_wrapper']][args.actor_index];out=D/f'actor_{args.actor_index:02d}_boundary_wiring_v2.json';assert not out.exists()
 prior=R/'artifacts/analog_asic/assembly/full25_adaptation_service_v12/eventspikeseg140k_adaptation_service_v12.gds';_,old=cells_read(prior.read_bytes());unchanged=set()
 # Independently reconstruct the namespaced new native IO from its qualified
 # original GDS, and derive the three alias positions from the unchanged actor.
 from gf180_gds_library_stream_v1 import Library
 io='gf180_class_current_shared_io_v1';ip=R/'artifacts/analog_asic/layout'/io/(io+'.gds');qp=ip.parent/'qualification.json';iq=json.loads(qp.read_text());assert iq['source_and_GDS_exact_device_graphs_accepted'] and sha(ip)==iq['sha256'][ip.name];lib=Library();lib.load(ip)
 for blob in lib.cells:
  n=next(v.rstrip(b'\0').decode() for t,d,v,b in __import__('assemble_gf180_full_capacity_storage_gds_v2').records(blob) if t==6);old[n]=blob
 def compare(n):
  if n in unchanged:return
  assert cells[n]==old[n],('changed inherited cell',n);unchanged.add(n)
  for e in elements(cells[n]):
   for t,d,v,b in e:
    if t==18:compare(v.rstrip(b'\0').decode())
 for p in w['modules']:compare(p['cell'])
 @functools.lru_cache(None)
 def parse(n):
  rs=[];refs=[];boxes=[];caps=[];defs=[]
  for e in elements(cells[n]):
   if e[0][0]!=8:continue
   l=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
   if l in (75,117):
    xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16);(caps if l==75 else defs).extend(polygon_rectangles(xy))
  for e in elements(cells[n]):
   typ=e[0][0];xy=next((struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16),None)
   if xy is None:continue
   if typ==8:
    l=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13);boxes.append((min(xy[::2]),min(xy[1::2]),max(xy[::2]),max(xy[1::2])))
    if l not in MET|set(VIA):continue
    for b in polygon_rectangles(xy):
     ol=l
     if l==41:
      if any(c[0]<=b[0] and c[1]<=b[1] and c[2]>=b[2] and c[3]>=b[3] for c in caps):ol=141
      else:assert not any(spatial.hit(b,c) for c in caps+defs),('partialMIM',n,b)
     rs.append((ol,b))
   elif typ in (10,11):
    assert all(t not in (26,27,28) or(t==26 and v==bytes(2)) for t,d,v,b in e);ch=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18);nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1));dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0;refs.extend((ch,xy[0]+ix*dx,xy[1]+iy*dy) for iy in range(ny) for ix in range(nx))
   elif typ==9:raise AssertionError('PATH')
  return rs,refs,boxes
 @functools.lru_cache(None)
 def bbox(n):
  rs,refs,boxes=parse(n);bs=list(boxes)
  for ch,x,y in refs:
   b=bbox(ch);bs.append((b[0]+x,b[1]+y,b[2]+x,b[3]+y))
  assert bs,n
  return min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs)
 own,refs,_=parse(w['cell']);assert collections.Counter(refs)==collections.Counter((p['cell'],*p['origin_dbu']) for p in w['modules']);idx=spatial.Index(own,list(range(len(own))));base=[];anchors=[];skipped=0;expanded=0;forest_intrusions=[]
 def local(n,ox,oy,prune=False):
  nonlocal skipped,expanded
  bb=bbox(n);ab=(bb[0]+ox,bb[1]+oy,bb[2]+ox,bb[3]+oy)
  if prune and next(idx.query(ab),None) is None:skipped+=1;return
  expanded+=1;rs,children,_=parse(n)
  base.extend((l,(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)) for l,b in rs)
  for ch,x,y in children:local(ch,ox+x,oy+y,prune)
 for p in w['modules']:
  ox,oy=p['origin_dbu'];n=p['cell'];actual=labels(cells[n])
  if p['instance']=='FOREST':
   threshold=p['interface_y_dbu']-1000;fb=p['bbox_dbu'];forbidden=(fb[0],fb[1],fb[2],oy+threshold);forest_intrusions.extend((l,b) for l,b in own if spatial.positive(b,forbidden));assert not forest_intrusions
   rs,children,_=parse(n)
   for ch,x,y in children:assert y+bbox(ch)[3]<threshold
   base.extend((l,(b[0]+ox,max(b[1],threshold)+oy,b[2]+ox,b[3]+oy)) for l,b in rs if b[3]>=threshold)
  else:local(n,ox,oy,p['instance']=='RESIDENT')
  for pin,pd in p['ports'].items():
   l,x,y=actual[pd['pin']];assert [x,y]==pd['xy_dbu'] and l==pd['layer'];anchors.append((p['instance']+'.'+pin,p['mapping'][pin],l,x+ox,y+oy))
 graph=spatial.Graph(base+own);nb=len(base)
 for l,b in own:
  if l in VIA:
   for metal in VIA[l]:assert next(graph.idx[metal].query(b),None) is not None,('added via missing metal',l,b,metal)
 graph.connect(nb);known=collections.defaultdict(set);aa=[]
 for tag,net,l,x,y in anchors:
  rr=graph.at(l,x,y,nb);known[rr].add(net);aa.append((net,rr))
 aliases=[sorted(v) for v in known.values() if len(v)>1];baseline=[graph.root(i) for i in range(nb)];touched=set()
 for i,(l,b) in enumerate(own,nb):
  for lay in (l,)+VIA.get(l,())+tuple(k for k,vs in VIA.items() if l in vs):
   for j in graph.idx[lay].query(b):
    if j<nb:touched.add(baseline[j])
 unknown=touched-set(known);graph.connect();nr=collections.defaultdict(set);rn=collections.defaultdict(set)
 for net,rr in aa:nr[net].add(graph.root(rr));rn[graph.root(rr)].add(net)
 shorts=[sorted(v) for v in rn.values() if len(v)>1];opens={k:len(v) for k,v in nr.items() if len(v)>1};floating=sum(graph.root(i) not in rn for i in range(nb,len(graph.s)));pe=[]
 for pin,pd in w['ports'].items():
  l,x,y=labels(cells[w['cell']])[pin];assert l==pd['layer'] and [x,y]==pd['xy_dbu']
  if rn.get(graph.at(l,x,y))!={pin}:pe.append(pin)
 ok=not(aliases or unknown or shorts or opens or floating or pe)
 o={'actor_index':args.actor_index,'actor':w['actor'],'wrapper':w['cell'],'incremental_boundary_wiring_accepted':ok,'baseline_rectangles':nb,'added_rectangles':len(own),'anchors':len(anchors),'baseline_aliases':aliases,'unknown_child_components_touched':len(unknown),'shorts':shorts,'opens':opens,'floating_parent_rectangles':floating,'port_errors':pe,'forest_opaque_region_intrusions':len(forest_intrusions),'expanded_child_instances':expanded,'skipped_disjoint_subtrees':skipped,'elapsed_s':time.monotonic()-start,'full_native_parent_LVS_RC_or_transient_qualified':False,'full_chip_complete':False,'scope':'Exact class-current parent metal/contact graph: existing native six-class readout, native120MOS8R48MIMIO and forest terminal field, all child geometry byte verified. Added wire/via contacts, every endpoint/root port, short/open/floating and opaque-forest intrusion checked independently. No parentRC/loading/fullpopulation timing or modelaccuracy acceptance.','sha256':{p.relative_to(R).as_posix():sha(p) for p in (Path(__file__),mf,g)}}
 o['inherited_child_hierarchy_byte_identical_cells']=len(unchanged);o['sha256'][prior.relative_to(R).as_posix()]=sha(prior)
 out.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k not in ('sha256','scope')},indent=2));assert ok
if __name__=='__main__':main()
