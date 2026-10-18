"""Read actual V10 top references, native hierarchy, bbox and retained identities."""
from pathlib import Path
import collections,functools,hashlib,json,struct,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
R=Path(__file__).resolve().parents[1];D=R/'artifacts/analog_asic/assembly/full25_adaptation_service_v12'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 start=time.monotonic();mf=D/'physical_assembly.json';m=json.loads(mf.read_text());g=D/'eventspikeseg140k_adaptation_service_v12.gds';_,cells=cells_read(g.read_bytes());ff=R/'artifacts/analog_asic/assembly/full_population_page_forest_v2/physical_forest.json';f=json.loads(ff.read_text());forestcells={p['root_cell'] for p in f['planes']};pmf=R/'artifacts/analog_asic/assembly/full25_membrane_service_v10/physical_assembly.json';prior=json.loads(pmf.read_text());actors={p['cell'] for w in prior['membrane_service_wrappers'] for p in w['modules'] if p['instance']=='ACTOR'};leaf=next(k for k,v in f['templates'].items() if v['kind']=='native1024page')
 for w in m['adaptation_service_wrappers']:
  orig=next(p for p in prior['membrane_service_wrappers'] if p['actor']==w['actor']);res=next(p for p in w['modules'] if p['instance']=='RESIDENT');assert res['source_cell']==orig['cell']
  assert res['mapping']=={'VDD':'VDD','VSS':'VSS','STORAGE_REFERENCE':'VCM','ADAPT_AGE':'AGE','ADAPT_AMPLITUDE':'AMPLITUDE','ADAPT_AMP_BUF':'AMP_BUFFERED'}
  for kind,sk in [('AGE','adaptation_age'),('AMP','adaptation_amplitude')]:
   p=next(p for p in w['modules'] if p['instance']==kind+'_FOREST');expected=next(p for p in f['planes'] if p['actor']==w['actor'] and p['state_kind']==sk);assert p['cell']==expected['root_cell'];mapping={n:kind+'__'+n for n in p['ports']};mapping.update(VCM='VCM',VDD='VDD',VSS='VSS',RECOV=kind+'_RECOV');mapping.update({f'DATA{k}':f'{kind}_DATA{k}' for k in range(8)});assert p['mapping']==mapping
  io=next(p for p in w['modules'] if p['instance']=='IO');assert io['mapping']=={n:n for n in io['ports']}
 @functools.lru_cache(None)
 def parse(n):
  refs=[];boxes=[]
  for e in elements(cells[n]):
   typ=e[0][0];xy=next((struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16),None)
   if xy is None:continue
   if typ in (10,11):
    assert all(t not in (26,27,28) or(t==26 and v==bytes(2)) for t,d,v,b in e);ch=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18);nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1));dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0;refs.append((ch,xy[0],xy[1],nx,ny,dx,dy))
   else:
    assert typ!=9,'PATH unsupported';boxes.append((min(xy[::2]),min(xy[1::2]),max(xy[::2]),max(xy[1::2])))
  return refs,boxes
 @functools.lru_cache(None)
 def bbox(n):
  refs,boxes=parse(n);bs=list(boxes)
  for ch,x,y,nx,ny,dx,dy in refs:
   b=bbox(ch)
   for ix in (0,nx-1):
    for iy in (0,ny-1):bs.append((b[0]+x+ix*dx,b[1]+y+iy*dy,b[2]+x+ix*dx,b[3]+y+iy*dy))
  assert bs
  return min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs)
 @functools.lru_cache(None)
 def census(n):
  if n in forestcells or n in actors:return collections.Counter({n:1})
  c=collections.Counter()
  for ch,x,y,nx,ny,dx,dy in parse(n)[0]:
   for k,v in census(ch).items():c[k]+=v*nx*ny
  return c
 expected=collections.Counter(p['root_cell'] for p in f['planes']);expected.update({n:1 for n in actors});actual=census(m['top_cell']);assert actual==expected,('root census',actual-expected,expected-actual)
 @functools.lru_cache(None)
 def pages(n):return int(n==leaf) if n==leaf else sum(pages(ch)*nx*ny for ch,x,y,nx,ny,dx,dy in parse(n)[0])
 assert pages(m['top_cell'])==54130
 rr=collections.Counter((ch,x,y) for ch,x,y,nx,ny,dx,dy in parse(m['top_cell'])[0] if nx==ny==1);assert rr==collections.Counter((p['cell'],*p['origin_dbu']) for p in m['top_placements'])
 bbox_errors=[];placement_boxes=[]
 for p in m['top_placements']:
  b=bbox(p['cell']);x,y=p['origin_dbu'];actualbb=[b[0]+x,b[1]+y,b[2]+x,b[3]+y];decl=p['bbox_dbu']
  if not(decl[0]<=actualbb[0] and decl[1]<=actualbb[1] and decl[2]>=actualbb[2] and decl[3]>=actualbb[3]):bbox_errors.append({'cell':p['cell'],'actual':actualbb,'declared':decl})
  placement_boxes.append((p['cell'],actualbb))
 overlap=[]
 for i,(n,a) in enumerate(placement_boxes):
  for nn,b in placement_boxes[:i]:
   if min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1]):overlap.append([n,nn])
 proofs=[json.loads((D/f'actor_{i:02d}_boundary_wiring_v2.json').read_text()) for i in range(15)];wiring=all(p['incremental_boundary_wiring_accepted'] and p['sha256'][g.relative_to(R).as_posix()]==sha(g) and p['sha256'][mf.relative_to(R).as_posix()]==sha(mf) for p in proofs);bb=bbox(m['top_cell']);ok=not(bbox_errors or overlap) and wiring and all(-2147483648<v<2147483647 for v in bb)
 o={'actual_top_inventory_accepted':True,'actual_native1024page_instances_including_actor_pages':54130,'forest_root_instances':56,'actor_instances':25,'active_states_inherited_identity_contract':54630400,'active_membranes_with_verified_boundary_compute_link':30976000 if wiring else 0,'all25_boundary_wiring_proofs_accepted':wiring,'top_placement_bounds_and_disjointness_accepted':ok,'actual_bbox_dbu':bb,'bbox_errors':bbox_errors,'overlapping_top_region_bboxes':overlap,'elapsed_s':time.monotonic()-start,'full_chip_complete':False,'full_5ms_population_service_accepted':False,'scope':'Actualbinaryhierarchy hasexactoriginal56forestrootoccurrences and25actorinstances;all54130native1024pagesincl25localactorpages counted. No duplication/removalofselectedrootcomponents;nativechildbyteidentities checkedseparatelyinall25wiringproofs. Activeidentityrank/holecontracts inheritedfrompriorV8andglobaladdressspec;notnewfullstateaddressvoltageverification. Placementbounds includeallgeometry/TEXT andnativearrayextents. Exactparentwiringproofs donotestablishRC/loading/timing ororiginalfloataccuracy.','sha256':{p.relative_to(R).as_posix():sha(p) for p in (Path(__file__),mf,g,ff)}}
 o.pop('all25_boundary_wiring_proofs_accepted');o.update(all15_adaptation_boundary_wiring_proofs_accepted=wiring,adaptation_forest_to_existing_resident_port_contracts_verified=True,active_adaptation_states_with_verified_boundary_compute_link=21964800 if wiring else 0,active_membrane_states_with_inherited_V10_verified_boundary_compute_link=30976000,parent_RC_or_loaded_nominal_qualified=False)
 o['scope']='Actualbinarytopcensus preservesall56forestrootoccurrences/25originalactors/54130native1024pages. Every15AGE/AMP mapping derivedfromindependentoriginalactor/planecontract:RECOV torestore,8DATA tosame-kindholdoutputs,existingresidentAGE/AMPLITUDE/AMP_BUF tocorrespondingIOports. All15newparentmetalgraphs/aliases/unchangednativechildrenverified. OriginalV10membranepaths inheritedunchanged. Actualgeometry/TEXT/AREFbounds fitdisjointtopregions. Activeidentityrank/holecontracts inherited,notnewper-statevoltageverification. ParentRC,loadedage-step/capture/fullforestservice andaccuracy/5ms unqualified.'
 o['sha256'][pmf.relative_to(R).as_posix()]=sha(pmf)
 (D/'independent_top_inventory_v1.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k not in ('sha256','scope')},indent=2));assert ok
if __name__=='__main__':main()
