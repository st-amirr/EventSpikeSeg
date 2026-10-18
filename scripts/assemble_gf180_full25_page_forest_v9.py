"""Replace unconnected raw planes by audited native shared-access forest.

Preserve compute, parameter capacity and protocol layout. Explicitly incomplete
compute/forest links remain exposed for the next assembly stage.
"""
from pathlib import Path
import collections,functools,hashlib,json,struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin,reference,rec
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic/assembly';S=B/'full25_shared_page1024_v8';F=B/'full_population_page_forest_v2';D=B/'full25_page_forest_v9'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not D.exists();D.mkdir();mf=S/'physical_assembly.json';m=json.loads(mf.read_text());ff=F/'physical_forest.json';f=json.loads(ff.read_text());af=F/'independent_forest_audit_v2.json';a=json.loads(af.read_text());assert a['interface_composition_accepted']
 sg=S/'eventspikeseg140k_shared_page1024_v7.gds';fg=F/'full_population_page_forest_v2.gds';prefix,cells=cells_read(sg.read_bytes());_,fc=cells_read(fg.read_bytes())
 for n,blob in fc.items():
  if n in cells:assert cells[n]==blob
  else:cells[n]=blob
 @functools.lru_cache(None)
 def bbox(n):
  boxes=[]
  for e in elements(cells[n]):
   xy=next((struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16),None)
   if xy is None:continue
   if e[0][0] in (10,11):
    assert all(t not in (26,27,28) or(t==26 and v==bytes(2)) for t,d,v,b in e)
    ch=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18);bb=bbox(ch);nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1));dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0
    for x,y in [(xy[0]+ix*dx,xy[1]+iy*dy) for ix in (0,nx-1) for iy in (0,ny-1)]:boxes.append((bb[0]+x,bb[1]+y,bb[2]+x,bb[3]+y))
   else:boxes.append((min(xy[::2]),min(xy[1::2]),max(xy[::2]),max(xy[1::2])))
  assert boxes,n
  return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
 # Independently verify the opaque native-page children end below the checked field.
 leaf=next(v for v in f['templates'].values() if v['kind']=='native1024page');threshold=leaf['interface_y_dbu']-1000;leaf_children=[]
 for e in elements(cells[leaf['cell']]):
  if e[0][0] not in (10,11):continue
  assert e[0][0]==10
  ch=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18);x,y=next(struct.unpack('>2i',v) for t,d,v,b in e if t==16);bb=bbox(ch);assert y+bb[3]<threshold,(ch,bb,threshold);leaf_children.append({'cell':ch,'actual_top_dbu':y+bb[3]})
 remove={p['candidate_cell'] for p in m['state_planes']};retained=[];removed=[];maxx=0
 for e in elements(cells[m['top_cell']]):
  ch=next((v.rstrip(b'\0').decode() for t,d,v,b in e if t==18),None)
  if ch in remove:removed.append(ch);continue
  retained.append(e)
  if ch:
   x,y=next(struct.unpack('>2i',v) for t,d,v,b in e if t==16);maxx=max(maxx,x+bbox(ch)[2])
  else:
   xy=next((struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16),())
   if xy:maxx=max(maxx,max(xy[::2]))
 assert collections.Counter(removed)==collections.Counter(remove) and len(removed)==56
 shift=-maxx-1000000;body=[]
 for e in retained:
  out=[]
  for t,d,v,b in e:
   if t==16:
    xy=list(struct.unpack('>'+str(len(v)//4)+'i',v))
    for k in range(0,len(xy),2):xy[k]+=shift
    b=rec(t,d,struct.pack('>'+str(len(xy))+'i',*xy))
   out.append(b)
  body.append(b''.join(out))
 body.append(reference(f['top_cell'],0,0));top='ESS140K_PAGE_FOREST_V9';cells[top]=begin(top)+b''.join(body)+rec(7,0)
 reachable={}
 def visit(n):
  if n in reachable:return
  reachable[n]=cells[n]
  for e in elements(cells[n]):
   for t,d,v,b in e:
    if t==18:visit(v.rstrip(b'\0').decode())
 visit(top);assert not remove.intersection(reachable)
 g=D/'eventspikeseg140k_page_forest_v9.gds';g.write_bytes(prefix+b''.join(reachable.values())+rec(4,0));bb=bbox(top);assert all(-2147483648<v<2147483647 for v in bb)
 o={'top_cell':top,'full_population_shared_access_layout_instantiated':True,'full_chip_layout_complete':False,'full_chip_functional_layout_complete':False,'forest_to_compute_links_complete':False,'global_operator_parameter_binding_complete':False,'full_5ms_population_service_accepted':False,'original_float_accuracy_accepted':False,'checkpoint_sha256':m['checkpoint_sha256'],'active_analog_state_identities':54630400,'forest_active_states':54600000,'preserved_actor_active_states':30400,'native_forest_leaf_pages':54105,'native_forest_selectors':7837,'physical_bank_capacity_instances':866155,'inactive_state_capacity':803520,'actor_count':25,'actor_and_parameter_protocol_translation_dbu':[shift,0],'atlas_bbox_dbu':bb,'spacious_research_atlas_not_dense_die':True,'removed_raw_plane_root_references':removed,'reachable_gds_cells':len(reachable),'native_leaf_opaque_child_bbox_guard':leaf_children,'actor_regions':[dict(p,origin_dbu=[p['origin_dbu'][0]+shift,p['origin_dbu'][1]],bbox_dbu=[p['bbox_dbu'][0]+shift,p['bbox_dbu'][1],p['bbox_dbu'][2]+shift,p['bbox_dbu'][3]]) for p in m['actor_regions']],'forest_planes':f['planes'],'scope':'Actual full-population native storage/access hierarchy and existing25compute clusters/parameter capacity/protocol geometry in one GDS. Old56unconnected raw-plane instances removed. Forest32..47publicports andactor service interfaces remain exposed,not joined. Researchatlas placement,not connected functionalASIC or compactdie. No new simulation or wholemodel accuracy/5ms claim.','sha256':{p.relative_to(R).as_posix():sha(p) for p in (Path(__file__),mf,ff,af,sg,fg,g)}}
 (D/'physical_assembly.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k not in ('sha256','actor_regions','forest_planes','removed_raw_plane_root_references','native_leaf_opaque_child_bbox_guard','scope')},indent=2))
if __name__=='__main__':main()
