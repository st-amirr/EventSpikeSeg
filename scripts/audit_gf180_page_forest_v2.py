"""Independent binary hierarchy and interface-metal composition for the page forest.

Static bounding-volume trees avoid spatial-grid expansion on long research-atlas wires.
No transient simulation or full-model flattening is performed.
"""
from pathlib import Path
import collections, functools, hashlib, json, struct, time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full25_shared_page1024_v7 import labels
from prove_gf180_shared_page_parent_metal_v5 import polygon_rectangles
R=Path(__file__).resolve().parents[1]; D=R/'artifacts/analog_asic/assembly/full_population_page_forest_v2'
MET={34,36,42,46,81}; VIA={35:(34,36),38:(36,42),40:(42,46),41:(46,81)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hit(a,b):return not(a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])
def positive(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
class Index:
 def __init__(self,shapes,ids):
  self.s=shapes
  def build(ids):
   bb=(min(shapes[i][1][0] for i in ids),min(shapes[i][1][1] for i in ids),max(shapes[i][1][2] for i in ids),max(shapes[i][1][3] for i in ids))
   if len(ids)<=12:return (bb,ids,None)
   spans=[max(shapes[i][1][k]+shapes[i][1][k+2] for i in ids)-min(shapes[i][1][k]+shapes[i][1][k+2] for i in ids) for k in (0,1)]
   k=int(spans[1]>spans[0]);ids.sort(key=lambda i:shapes[i][1][k]+shapes[i][1][k+2]);mid=len(ids)//2
   return bb,build(ids[:mid]),build(ids[mid:])
  self.tree=build(ids) if ids else None
 def query(self,box):
  stack=[self.tree] if self.tree else []
  while stack:
   bb,a,b=stack.pop()
   if not hit(bb,box):continue
   if b is None:
    for i in a:
     if hit(self.s[i][1],box):yield i
   else:stack.extend((a,b))
class Graph:
 def __init__(self,shapes):
  self.s=shapes;self.p=list(range(len(shapes)));self.sz=[1]*len(shapes)
  self.idx={l:Index(shapes,[i for i,(lay,_) in enumerate(shapes) if lay==l]) for l in MET|set(VIA)}
 def root(self,i):
  while self.p[i]!=i:self.p[i]=self.p[self.p[i]];i=self.p[i]
  return i
 def join(self,i,j):
  i=self.root(i);j=self.root(j)
  if i==j:return
  if self.sz[i]<self.sz[j]:i,j=j,i
  self.p[j]=i;self.sz[i]+=self.sz[j]
 def connect(self,baseline=None):
  for i,(l,b) in enumerate(self.s):
   for lay in (l,)+VIA.get(l,()):
    for j in self.idx[lay].query(b):
     if baseline is not None and (i>=baseline or j>=baseline):continue
     if lay==l and j>=i:continue
     self.join(i,j)
 def at(self,l,x,y,limit=None):
  rr={self.root(i) for i in self.idx[l].query((x,y,x,y)) if limit is None or i<limit};assert len(rr)==1,('anchor',l,x,y,len(rr));return rr.pop()
def main():
 start=time.monotonic();mf=D/'physical_forest.json';g=D/'full_population_page_forest_v2.gds';m=json.loads(mf.read_text());_,cells=cells_read(g.read_bytes());templates=m['templates'];native={v['cell']:v for v in m['native_sources'].values()};meta=templates|native
 @functools.lru_cache(None)
 def parse(n):
  rs=[];refs=[]
  for e in elements(cells[n]):
   typ=e[0][0]
   if typ==8:
    l=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
    if l not in MET|set(VIA):continue
    xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
    rs.extend((l,b) for b in polygon_rectangles(xy))
   elif typ in (10,11):
    assert all(t not in (26,27,28) or (t==26 and v==bytes(2)) for t,d,v,b in e)
    child=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18);xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
    nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1))
    dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0
    refs.extend((child,xy[0]+ix*dx,xy[1]+iy*dy) for iy in range(ny) for ix in range(nx))
   elif typ==9:raise AssertionError('unsupported PATH')
  return rs,refs
 leaf=next(k for k,v in templates.items() if v['kind']=='native1024page')
 _,old=cells_read((R/'artifacts/analog_asic/assembly/full25_shared_page1024_v8/eventspikeseg140k_shared_page1024_v7.gds').read_bytes())
 visited=set()
 def exact(n):
  if n in visited:return
  assert cells[n]==old[n];visited.add(n)
  for ch,_,_ in parse(n)[1]:exact(ch)
 exact(leaf)
 @functools.lru_cache(None)
 def count(n):
  if n==leaf:return collections.Counter(page=1)
  if n in native:return collections.Counter({native[n]['source_cell']:1})
  c=collections.Counter()
  for ch,_,_ in parse(n)[1]:c.update(count(ch))
  return c
 expected=collections.Counter((p['root_cell'],*p['origin_dbu']) for p in m['planes']);assert collections.Counter(parse(m['top_cell'])[1])==expected
 totals=count(m['top_cell']);assert totals['page']==54105 and totals['gf180_shared_page_tree_selector8_v2']==7837
 assert totals['gf180_fixed_body_tg_quarter_shorttracks']==7837*64 and totals['gf180_dense_inverter_v1']==7837*8
 proofs=[]
 for name,v in sorted(templates.items(),key=lambda kv:kv[1]['level']):
  if v['kind']!='page_tree':continue
  own,refs=parse(name);assert collections.Counter(refs)==collections.Counter((p['cell'],*p['origin_dbu']) for p in v['modules'])
  base=[];anchors=[];intrusions=[]
  for p in v['modules']:
   ch=meta[p['cell']];ox,oy=p['origin_dbu'];threshold=ch.get('interface_y_dbu');rs,sub=parse(p['cell'])
   if threshold is None:assert not sub,('nonflat native',p['cell'])
   else:
    threshold-=1000
    # Child opaque region contains no parent route, on any conductor/contact layer.
    forbidden=(p['bbox_dbu'][0],p['bbox_dbu'][1],p['bbox_dbu'][2],oy+threshold)
    intrusions.extend((p['instance'],l,b) for l,b in own if positive(b,forbidden))
    if ch['kind']=='page_tree':assert all(q['bbox_dbu'][3]<threshold for q in ch['modules'])
   for l,b in rs:
    if threshold is not None:
     if b[3]<threshold:continue
     b=(b[0],max(b[1],threshold),b[2],b[3])
    base.append((l,(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)))
   actual=labels(cells[p['cell']])
   for port,pd in ch['ports'].items():
    lay,x,y=actual[pd['pin']];assert lay==pd['layer'] and [x,y]==pd['xy_dbu']
    anchors.append((p['instance']+'.'+port,p['mapping'][port],lay,x+ox,y+oy))
  assert not intrusions,('opaque_child_intrusions',name,intrusions[:3])
  graph=Graph(base+own);nb=len(base);graph.connect(nb);known=collections.defaultdict(set);aa=[]
  for tag,net,l,x,y in anchors:
   rr=graph.at(l,x,y,nb);known[rr].add(net);aa.append((net,rr))
  aliases=[sorted(vv) for vv in known.values() if len(vv)>1];assert not aliases,(name,'baseline alias',aliases)
  baseline=[graph.root(i) for i in range(nb)];touched=set()
  for i,(l,b) in enumerate(own,nb):
   compatible=(l,)+VIA.get(l,())+tuple(k for k,vs in VIA.items() if l in vs)
   for lay in compatible:
    for j in graph.idx[lay].query(b):
     if j<nb:touched.add(baseline[j])
  unknown=touched-set(known);graph.connect();nr=collections.defaultdict(set);rn=collections.defaultdict(set)
  for net,rr in aa:nr[net].add(graph.root(rr));rn[graph.root(rr)].add(net)
  shorts=[sorted(vv) for vv in rn.values() if len(vv)>1];opens={k:len(vv) for k,vv in nr.items() if len(vv)>1};floating=sum(graph.root(i) not in rn for i in range(nb,len(graph.s)))
  pe=[]
  for port,pd in v['ports'].items():
   l,x,y=labels(cells[name])[port];assert [x,y]==pd['xy_dbu'] and l==pd['layer']
   if rn.get(graph.at(l,x,y))!={port}:pe.append(port)
  ok=not(unknown or shorts or opens or floating or pe)
  proof={'cell':name,'accepted':ok,'baseline_rectangles':nb,'parent_rectangles':len(own),'anchors':len(anchors),'unknown_touched_components':len(unknown),'shorts':shorts,'opens':opens,'floating_parent_rectangles':floating,'port_errors':pe,'opaque_region_intrusions':len(intrusions)};proofs.append(proof)
  print(json.dumps(proof),flush=True)
  if not ok:break
 o={'actual_binary_hierarchy_inventory_verified':True,'native_leaf_hierarchy_byte_identical_cells':len(visited),'actual_instances':dict(totals),'interface_composition_accepted':len(proofs)==len(templates)-1 and all(p['accepted'] for p in proofs),'template_proofs':proofs,'elapsed_s':time.monotonic()-start,'full_native_forest_LVS_or_RC':False,'full_model_top_assembled':False,'full_chip_complete':False,'scope':'Binary SREF/AREF readback, unchanged native leaf hierarchy, and exact metal/via graph of each parent plus child interface fields. Opaque lower child regions excluded only when every added parent conductor avoids them. Native child transistor behavior/DRC and field-to-device paths inherited from prior evidence. Not whole-atlas DRC, loading, timing, native extraction or model accuracy.','sha256':{p.relative_to(R).as_posix():sha(p) for p in (Path(__file__),mf,g)}}
 (D/'independent_forest_audit_v2.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k not in ('template_proofs','scope','sha256')}));assert o['interface_composition_accepted']
if __name__=='__main__':main()
