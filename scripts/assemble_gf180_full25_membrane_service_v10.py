"""Connect every membrane forest to its existing compute actor via native restore.

Categorical phase/address controls stay exposed. Other numerical planes and graph
operators remain pending. This emits physical wiring, not functional signoff.
"""
from pathlib import Path
import collections,hashlib,json,struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements,via
from assemble_gf180_full_capacity_storage_gds_v2 import begin,reference,rec
from assemble_gf180_full25_physical_candidate_v5 import Library,pinlist,rect,label
from assemble_gf180_full25_shared_page1024_v7 import labels
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';S=B/'assembly/full25_page_forest_v9';F=B/'assembly/full_population_page_forest_v2';D=B/'assembly/full25_membrane_service_v10'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not D.exists();D.mkdir();mf=S/'physical_assembly.json';m=json.loads(mf.read_text());ff=F/'physical_forest.json';f=json.loads(ff.read_text());g=S/'eventspikeseg140k_page_forest_v9.gds';prefix,cells=cells_read(g.read_bytes());lib=Library();native={}
 for c in ['gf180_candidate_penalty_subtractor_v2','gf180_fixed_body_tg_quarter_shorttracks']:
  dd=B/'layout'/c;q=json.loads((dd/'qualification.json').read_text());cg=dd/(c+'.gds');assert q['magic_drc_count']==0 and sha(cg)==q['sha256'][cg.name];name=lib.load(cg)[c];pins=pinlist(dd,c);native[c]={'cell':name,'bbox_dbu':[round(v*1000) for v in q['bbox_um']],'ports':{p:{'pin':p,'layer':{'metal3':42,'metal5':81}[pins[p][0]],'xy_dbu':[round(pins[p][1]),round(pins[p][2])]} for p in q['ports']}}
 for blob in lib.cells:
  name=next(v.rstrip(b'\0').decode() for t,d,v,b in __import__('assemble_gf180_full_capacity_storage_gds_v2').records(blob) if t==6)
  if name in cells:assert cells[name]==blob
  else:cells[name]=blob
 wrappers=[];placements=[];attach=['VDD','VSS','STORAGE_REFERENCE','COMPUTE_REFERENCE','EXTERNAL_COMPUTE_DATA']+[f'SHARED_WRITE_DATA{k}' for k in range(8)]
 for ai,a in enumerate(m['actor_regions']):
  plane=next(p for p in f['planes'] if p['actor']==a['actor'] and p['state_kind']=='membrane');forest=f['templates'][plane['root_cell']];ap=labels(cells[a['gds_cell']]);ox,oy=a['origin_dbu'];abb=a['bbox_dbu'];actor={'cell':a['gds_cell'],'bbox_dbu':[abb[0]-ox,abb[1]-oy,abb[2]-ox,abb[3]-oy],'ports':{p:{'pin':p,'layer':ap[p][0],'xy_dbu':list(ap[p][1:])} for p in attach}}
  fm={p:'FOREST__'+p for p in forest['ports']};fm.update(VCM='STORAGE_REFERENCE',VDD='VDD',VSS='VSS',RECOV='FOREST_RECOVERED');fm.update({f'DATA{k}':f'SHARED_WRITE_DATA{k}' for k in range(8)})
  shift=native['gf180_candidate_penalty_subtractor_v2'];sm={'CANDIDATE':'FOREST_RECOVERED','PENALTY':'STORAGE_REFERENCE','VCOM':'COMPUTE_REFERENCE','ADJUSTED':'FOREST_SHIFTED','VDD':'VDD','VSS':'VSS','BIAS':'FOREST_UP_BIAS'};assert set(sm)==set(shift['ports'])
  tg=native['gf180_fixed_body_tg_quarter_shorttracks'];tm={'A':'FOREST_SHIFTED','B':'EXTERNAL_COMPUTE_DATA','EN':'FOREST_RESTORE','ENB':'FOREST_RESTOREB','VDD':'VDD','VSS':'VSS'}
  entries=[('FOREST',forest,fm),('ACTOR',actor,{p:p for p in actor['ports']}),('UP',shift,sm),('RESTORE',tg,tm)];body=[];mods=[];groups=collections.OrderedDict();row_y=0;maxright=0
  for tag,v,mapping in entries:
   bb=v['bbox_dbu'];left=400000+4000+len(v['ports'])*2000;px=left-bb[0];py=row_y-bb[1];right=left+bb[2]-bb[0];top=row_y+bb[3]-bb[1];maxright=max(maxright,right);body.append(reference(v['cell'],px,py));mods.append({'instance':tag,'cell':v['cell'],'origin_dbu':[px,py],'bbox_dbu':[left,row_y,right,top],'ports':v['ports'],'mapping':mapping,'interface_y_dbu':v.get('interface_y_dbu')})
   for pi,(pin,pd) in enumerate(v['ports'].items()):
    x,y=pd['xy_dbu'];x+=px;y+=py;sx=left-2000-pi*2000;lay=pd['layer'];ey=top+10000+pi*3200
    if lay==42:body.extend([rect(42,(min(x,sx)-200,y-200,max(x,sx)+200,y+200)),via(42,46,40,sx,y)])
    else:assert lay==81;body.extend([rect(81,(min(x,sx)-220,y-220,max(x,sx)+220,y+220)),via(81,46,41,sx,y)])
    body.extend([rect(46,(sx-200,min(y,ey)-200,sx+200,max(y,ey)+200)),via(46,81,41,sx,ey)]);groups.setdefault(mapping[pin],[]).append({'instance':tag,'pin':pin,'escape_dbu':[sx,ey]})
   row_y=top+10000+len(v['ports'])*3200+100000
  field=row_y+100000;ports={};nets=[];minx=0
  for ni,(net,ends) in enumerate(groups.items()):
   ex=-20000-ni*2000;ty=field+ni*3200;ys=[];minx=min(minx,ex-1200)
   for e in ends:
    sx,ey=e['escape_dbu'];body.extend([rect(81,(min(sx,ex)-220,ey-220,max(sx,ex)+220,ey+220)),via(81,46,41,ex,ey)]);ys.append(ey)
   body.extend([rect(46,(ex-200,min(ys+[ty])-220,ex+200,max(ys+[ty])+220)),via(46,81,41,ex,ty),rect(81,(ex-1200,ty-220,ex+1200,ty+220)),label(net,ex-1000,ty)]);ports[net]={'pin':net,'layer':81,'xy_dbu':[ex-1000,ty]};nets.append({'net':net,'endpoints':[e['instance']+'.'+e['pin'] for e in ends]})
  root=f'ESS_MEMBRANE_SERVICE_{ai:02d}_V10';cells[root]=begin(root)+b''.join(body)+rec(7,0);view={'cell':root,'actor':a['actor'],'plane_index':plane['plane_index'],'kind':'membrane_compute_wrapper','bbox_dbu':[minx,0,maxright,field+(len(groups)-1)*3200+220],'ports':ports,'modules':mods,'nets':nets,'native_parent_wiring_qualified':False,'active_membrane_states':plane['active_states']+1216};wrappers.append(view);placements.append(view)
 # Keep all non-membrane state forests. Preserve auxiliary parameter/protocol geometry.
 for p in f['planes']:
  if p['state_kind']=='membrane':continue
  placements.append({'cell':p['root_cell'],'kind':p['state_kind'],'plane_index':p['plane_index'],'bbox_dbu':f['templates'][p['root_cell']]['bbox_dbu']})
 actorcells={a['gds_cell'] for a in m['actor_regions']};aux=[]
 for e in elements(cells[m['top_cell']]):
  ch=next((v.rstrip(b'\0').decode() for t,d,v,b in e if t==18),None)
  if ch in actorcells or ch==f['top_cell']:continue
  aux.append(b''.join(b for t,d,v,b in e))
 auxname='ESS_PARAMETER_PROTOCOL_RETAINED_V10';cells[auxname]=begin(auxname)+b''.join(aux)+rec(7,0)
 # Aux bounding region conservatively retains the original actor/protocol atlas extent.
 placements.append({'cell':auxname,'kind':'parameter_protocol','bbox_dbu':[m['atlas_bbox_dbu'][0],0,-1000000,900000000]})
 free=[(0,0,3000000000,3000000000)];topbody=[];placed=[]
 for v in sorted(placements,key=lambda v:max(v['bbox_dbu'][2]-v['bbox_dbu'][0],v['bbox_dbu'][3]-v['bbox_dbu'][1]),reverse=True):
  bb=v['bbox_dbu'];w=bb[2]-bb[0];h=bb[3]-bb[1];uw=w+1000000;uh=h+1000000;opts=[(min(fw-uw,fh-uh),max(fw-uw,fh-uh),y,x) for x,y,fw,fh in free if fw>=uw and fh>=uh];assert opts,('packing',v['cell']);_,_,y,x=min(opts);nf=[]
  for fx,fy,fw,fh in free:
   rr=fx+fw;tt=fy+fh
   if x>=rr or x+uw<=fx or y>=tt or y+uh<=fy:nf.append((fx,fy,fw,fh));continue
   if x>fx:nf.append((fx,fy,x-fx,fh))
   if x+uw<rr:nf.append((x+uw,fy,rr-x-uw,fh))
   if y>fy:nf.append((fx,fy,fw,y-fy))
   if y+uh<tt:nf.append((fx,y+uh,fw,tt-y-uh))
  free=[q for q in sorted(set(nf)) if not any(q!=z and z[0]<=q[0] and z[1]<=q[1] and z[0]+z[2]>=q[0]+q[2] and z[1]+z[3]>=q[1]+q[3] for z in nf)];px=x-bb[0]-1500000000;py=y-bb[1]-1500000000;topbody.append(reference(v['cell'],px,py));placed.append({'cell':v['cell'],'kind':v['kind'],'plane_index':v.get('plane_index'),'origin_dbu':[px,py],'bbox_dbu':[x-1500000000,y-1500000000,x+w-1500000000,y+h-1500000000]})
 top='ESS140K_MEMBRANE_SERVICE_V10';cells[top]=begin(top)+b''.join(topbody)+rec(7,0);reachable={}
 def visit(n):
  if n in reachable:return
  reachable[n]=cells[n]
  for e in elements(cells[n]):
   for t,d,v,b in e:
    if t==18:visit(v.rstrip(b'\0').decode())
 visit(top);dest=D/'eventspikeseg140k_membrane_service_v10.gds';dest.write_bytes(prefix+b''.join(reachable.values())+rec(4,0))
 contract={'restore_path':'selectedforest.RECOV -> native16MOS levelshift -> native2MOS gatedrestore -> existingactor.EXTERNAL_COMPUTE_DATA/compute.INIT_DATA','write_path':'existingactor.SHARED_WRITE_DATA0..7 -> selectedforest.DATA0..7','mutual_exclusion':'FOREST_RESTORE, actorPAGE_RESTORE, actorRESTORE/INITIALIZE must not overlap;only one destination page WRITE_CMD may assert during row commit','categorical_interface':'FOREST__ADDR,SEL,READ/WRITE/READ_ENABLE andFOREST_RESTORE/B externally driven until sequencer bound','bias_interface':'FOREST__MASTER_NBIAS/PBIAS andFOREST_UP_BIAS externally programmed','global_recovery_storage_center_V':1.2,'compute_center_V':1.65,'full_population_service_timing_accepted':False,'long_wire_fanout_loading_qualified':False}
 o={'top_cell':top,'source_assembly':mf.relative_to(R).as_posix(),'checkpoint_sha256':m['checkpoint_sha256'],'active_analog_state_identities':54630400,'active_membranes_with_physical_compute_link':sum(w['active_membrane_states'] for w in wrappers),'actor_count':25,'membrane_service_wrappers':wrappers,'top_placements':placed,'interface_contract':contract,'membrane_forest_compute_wiring_built':True,'membrane_forest_compute_wiring_qualified':False,'adaptation_and_class_plane_compute_links_complete':False,'full_chip_functional_layout_complete':False,'full_chip_layout_complete':False,'full_5ms_population_service_accepted':False,'original_float_accuracy_accepted':False,'scope':'Actual25membrane forests connectexistingcompute via separate nativelevelshift/gatedrestore and8sharedanalog writecolumns. Nativeactor geometry/stateidentity unchanged;wrapperboundarywiring needsindependentproof. Address/phase/bias/protocol/parameter andAGE/AMP/classlinks remainexternal oropen. Spaciousresearchatlas,not compactdie or5ms proof.','sha256':{p.relative_to(R).as_posix():sha(p) for p in (Path(__file__),mf,ff,g,dest)}}
 (D/'physical_assembly.json').write_text(json.dumps(o,indent=2)+'\n');(D/'interface_contract_v1.json').write_text(json.dumps(contract,indent=2)+'\n');print(json.dumps({'top':top,'membrane_states_connected':o['active_membranes_with_physical_compute_link'],'wrappers':len(wrappers),'gds_bytes':dest.stat().st_size,'wiring_qualified':False}))
if __name__=='__main__':main()
