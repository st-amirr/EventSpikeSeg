"""Move128 real resident states per actor into a physically connected shared compute service."""
from pathlib import Path
from build_gf180_fixed_body_tg import rectangles
import json,re,struct,hashlib,collections,math
from assemble_gf180_full_capacity_storage_gds_v2 import records,rec,string,begin,reference
from assemble_gf180_full25_physical_candidate_v5 import Library,pinlist,rect,label,via as original_via
def via(a,b,c,x,y):
 if {a,b}=={46,81}:return rect(a,(x-220,y-220,x+220,y+220))+rect(b,(x-220,y-220,x+220,y+220))+rect(c,(x-140,y-140,x+140,y+140))
 return original_via(a,b,c,x,y)
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';SRC=B/'assembly/full25_locally_decoded_storage_v3';OUT=B/'assembly/full25_external_bank_service_v5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cells_read(blob):
 cells={};parts=[];name=None;rs=list(records(blob));first=next(i for i,r in enumerate(rs) if r[0]==5)
 for t,d,v,b in rs[first:]:
  if t==5:parts=[]
  parts.append(b)
  if t==6:name=v.rstrip(b'\0').decode()
  if t==7:cells[name]=b''.join(parts)
 return b''.join(r[3] for r in rs[:first]),cells
def elements(blob):
 parts=[];active=False
 for t,d,v,b in records(blob):
  if t in [8,9,10,11,12]:active=True;parts=[]
  if active:parts.append((t,d,v,b))
  if t==17 and active:yield parts;active=False
def main():
 assert not OUT.exists();OUT.mkdir();mf=SRC/'physical_assembly.json';m=json.loads(mf.read_text());oldg=SRC/'eventspikeseg140k_locally_decoded_storage_v3.gds';prefix,cells=cells_read(oldg.read_bytes());lib=Library();inputs={Path(__file__),mf,oldg};selected={}
 def load(c):
  d=B/'layout'/c;qf=d/'qualification.json';q=json.loads(qf.read_text());g=d/(c+'.gds');assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and sha(g)==q['sha256'][g.name];selected[c]=(lib.load(g)[c],q,pinlist(d,c));inputs.update([qf,g,d/(c+'.mag')]);return selected[c]
 reader='gf180_bank_pair_shared_reader_v1';shift='gf180_candidate_penalty_subtractor_v2';tg='gf180_fixed_body_tg_quarter_shorttracks'
 for c in [reader,shift,tg]:load(c)
 pair='gf180_independent_bank_pair_v4';pg=B/'layout'/pair/(pair+'.gds');pn='N'+sha(pg)[:8]+'_'+hashlib.sha256(pair.encode()).hexdigest()[:16];pq=json.loads((B/'layout'/pair/'qualification.json').read_text());pbb=[round(v*1000) for v in pq['bbox_um']];moved=[]
 for p in m['state_planes']:
  if p['state_kind']!='membrane':continue
  old=cells[p['candidate_cell']];wanted=(-pbb[0],-pbb[1]);changed=False;replacement=b'';parts=[]
  for e in elements(old):
   child=next((v.rstrip(b'\0').decode() for t,d,v,b in e if t==18),None);xy=next((struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16),None)
   if child==pn and xy[:2]==wanted:
    assert not changed;nx,ny=next(struct.unpack('>2h',v) for t,d,v,b in e if t==19);assert ny==1 and nx>=1;pp,yp=p['local_pair_pitch_dbu'];assert xy[2]-xy[0]==nx*pp
    if nx>1:parts.append(reference(pn,xy[0]+pp,xy[1],nx-1,1,pp,yp))
    changed=True
   else:parts.append(b''.join(r[3] for r in e))
  assert changed,p['actor'];cells[p['candidate_cell']]=begin(p['candidate_cell'])+b''.join(parts)+rec(7,0);p['pair_instances']-=1;p['locally_decoded_bank_equivalents']-=2;p['external_compute_service_bank_exceptions']=[dict(channel=0,bank_y=0,bank_x=1,native_instance='bank_service',state_port='B0_STATE[row][column]'),dict(channel=0,bank_y=0,bank_x=2,native_instance='bank_service',state_port='B1_STATE[row][column]')];moved.append(dict(actor=p['actor'],plane=p['plane_index'],native_pair_removed=True,logical_banks=[[0,0,1],[0,0,2]],state_port_map={'bank_x1':'B0_STATE[row][column]','bank_x2':'B1_STATE[row][column]'},active_shape_chw=p['shape_chw']))
 assert len(moved)==25
 actor_sizes={};newnets=[]
 for a in m['actor_regions']:
  owner=a['actor'];root=a['gds_cell'];old=cells[root];compute=next(p for p in a['modules'] if p['instance']=='compute');cd=B/'layout'/compute['cell'];cq=json.loads((cd/'qualification.json').read_text());cpins=pinlist(cd,compute['cell']);oldheight=a['bbox_dbu'][3]-a['bbox_dbu'][1];width=a['bbox_dbu'][2]-a['bbox_dbu'][0];body=[];connected={'compute__DATA'+str(c) for c in range(8)}|{'compute__INIT_DATA','compute__SREF','compute__CREF'}
  for e in elements(old):
   text=next((v.rstrip(b'\0').decode() for t,d,v,b in e if t==25),None)
   if text not in connected:body.append(b''.join(r[3] for r in e))
  placements=[];sy=oldheight+100000;pinbase=sum(len(json.loads((B/'layout'/p['cell']/'qualification.json').read_text())['ports']) for p in a['modules'])
  for tag,c in [('bank_service',reader),('external_up',shift),('external_restore',tg),('external_initialize',tg)]:
   native,q,pins=selected[c];bb=[round(v*1000) for v in q['bbox_um']];dx=548000-bb[0];dy=sy-bb[1];body.append(reference(native,dx,dy));p=dict(instance=tag,cell=c,origin_dbu=[dx,dy],bbox_dbu=[548000,sy,548000+bb[2]-bb[0],sy+bb[3]-bb[1]],escape_start_index=pinbase);placements.append(p);pinbase+=len(pins);sy=p['bbox_dbu'][3]+100000
  bindings={};groups=collections.defaultdict(list)
  def bind(net,*ends):
   for tag,pin in ends:assert (tag,pin) not in bindings;bindings[tag,pin]=net
  for c in range(8):bind('SHARED_WRITE_DATA'+str(c),('compute','DATA'+str(c)),('bank_service','DATA'+str(c)))
  bind('STORAGE_REFERENCE',('compute','SREF'),('bank_service','VCM'),('external_up','PENALTY'))
  bind('COMPUTE_REFERENCE',('compute','CREF'),('external_up','VCOM'))
  bind('EXTERNAL_RECOVERED',('bank_service','RECOV'),('external_up','CANDIDATE'))
  bind('EXTERNAL_SHIFTED',('external_up','ADJUSTED'),('external_restore','A'))
  bind('EXTERNAL_COMPUTE_DATA',('compute','INIT_DATA'),('external_restore','B'),('external_initialize','B'))
  bind('EXTERNAL_RESTORE',('external_restore','EN'));bind('EXTERNAL_RESTOREB',('external_restore','ENB'))
  bind('EXTERNAL_INITIALIZE',('external_initialize','EN'));bind('EXTERNAL_INITIALIZEB',('external_initialize','ENB'));bind('EXTERNAL_INIT_DATA',('external_initialize','A'))
  allmods=[compute]+placements
  for p in allmods:
   pins=cpins if p['instance']=='compute' else selected[p['cell']][2]
   for pi,(pin,(layer,lx,ly)) in enumerate(pins.items()):
    net=bindings.get((p['instance'],pin));net=pin if pin in ['VDD','VSS'] and p['instance']!='compute' else net
    if net:groups[net].append((p,pin,pi,layer,lx,ly))
    elif p['instance']!='compute':
     dx,dy=p['origin_dbu'];body.append(label(p['instance']+'__'+pin,dx+lx,dy+ly,{'metal1':34,'metal2':36,'metal3':42,'metal4':46,'metal5':81}[layer]))
  # Existing actor power pads are already qualified; attach there without touching leaf supply escapes.
  oldlabels={};pos=None;lay=None
  for e in elements(old):
   if e[0][0]!=12:continue
   for t,dt,v,b in e:
    if t==13:lay=struct.unpack('>h',v)[0]
    if t==16:pos=struct.unpack('>2i',v)
    if t==25:oldlabels[v.rstrip(b'\0').decode()]=(lay,pos)
  track0=sy+100000
  for ni,(net,ends) in enumerate(groups.items()):
   ty=track0+ni*3200;xs=[];endnames=[]
   for p,pin,pi,layer,lx,ly in ends:
    dx,dy=p['origin_dbu'];px=round(dx+lx);py=round(dy+ly);ex=-100000-2000*(p['escape_start_index']+pi);xs.append(ex);endnames.append(p['instance']+'.'+pin)
    if p['instance']=='compute':
     if pin.startswith('DATA'):
      col=int(pin[4:]);sx=-100000-640*col;sy_data=120000+640*col
      service_mag=B/'layout/gf180_decoded_read_write_service_v2/gf180_decoded_read_write_service_v2.mag';inputs.add(service_mag);paint=rectangles(service_mag,0)
      assert all(any(x1<=sx<=x2 and y1<=sy_data<=y2 for x1,y1,x2,y2 in paint[l]) for l in ['metal4','metal5','via4'])
      px=round(dx+sx*5);py=round(dy+sy_data*5);layer='metal4' # Existing native via4 already joins this landing to DATA M5.
     # Native pin rises only through its own leaf; escape in100um empty gap above it.
     ey=compute['bbox_dbu'][3]+10000+3200*len([n for n in endnames if n.startswith('compute.')]);ey+=3200*ni
     assert ey<compute['bbox_dbu'][3]+100000
     if layer=='metal3':body.append(via(42,46,40,px,py))
     elif layer=='metal5':body.append(via(81,46,41,px,py))
     else:assert layer=='metal4',(pin,layer)
     body.extend([rect(46,(px-200,min(py,ey)-200,px+200,max(py,ey)+200)),via(46,81,41,px,ey),rect(81,(min(ex,px)-220,ey-220,max(ex,px)+220,ey+220)),via(81,46,41,ex,ey)]);py=ey
    else:
     if layer=='metal1':body.extend([via(34,36,35,px,py),via(36,42,38,px,py)])
     if layer in ['metal1','metal3']:body.append(via(42,46,40,px,py))
     if layer in ['metal1','metal3','metal4']:body.append(via(46,81,41,px,py))
     assert layer in ['metal1','metal3','metal4','metal5'];body.extend([rect(81,(min(ex,px)-220,py-220,max(ex,px)+220,py+220)),via(81,46,41,ex,py)])
    body.extend([rect(46,(ex-200,min(py,ty)-200,ex+200,max(py,ty)+200)),via(46,81,41,ex,ty)])
   if net in ['VDD','VSS']:
    lay,(px,py)=oldlabels[net];assert lay==81;ex=-50000-(2000 if net=='VSS' else 0);body.extend([rect(81,(min(ex,px)-220,py-220,max(ex,px)+220,py+220)),via(81,46,41,ex,py),rect(46,(ex-200,min(py,ty)-200,ex+200,max(py,ty)+200)),via(46,81,41,ex,ty)]);xs.append(ex)
   body.append(rect(81,(min(xs)-1000,ty-220,max(xs)+1000,ty+220)))
   if net not in ['VDD','VSS']:body.append(label(net,min(xs)-900,ty))
   newnets.append(dict(actor=owner,net=net,endpoint_pins=endnames,externally_supplied_or_unconsumed=len(ends)==1))
  cells[root]=begin(root)+b''.join(body)+rec(7,0);a['modules']+=placements;a['representative_compute_tile_resident_membranes']=192;a['external_resident_pair_compute_service_physical']=True;a['external_resident_pair_service_nominal_simulation_completed']=False;a['remaining_membrane_banks_access_unconnected']-=2;actor_sizes[root]=[width,track0+len(groups)*3200+100000,max(1200000,110000+2000*pinbase)]
 # Repack actor shelves above storage; preserve all state-plane origins and internal module transforms.
 x=0;y=round(m['storage_atlas_height_um']*1000)+1000000;shelf=0;actor_origins={}
 for a in m['actor_regions']:
  w,h,left_gutter=actor_sizes[a['gds_cell']]
  if x+left_gutter+w>140000000:x=0;y+=shelf+200000;shelf=0
  actor_origins[a['gds_cell']]=[x+left_gutter,y];a['origin_dbu']=[x+left_gutter,y];a['bbox_dbu']=[x,y,x+left_gutter+w,y+h];a['external_service_spine_gutter_dbu']=left_gutter;x+=left_gutter+w+200000;shelf=max(shelf,h)
 protocol_old=next(v for t,dt,v,b in records(cells[m['top_cell']]) if t==18 and v.rstrip(b'\0').decode()=='ESS_PROTOCOL_CORRIDORS');protocol_old_y=min(w['source_pad_dbu'][1] for e in m['protocol_edges'] for w in e['wires']);protocol_delta=y+shelf+300000-protocol_old_y
 top=[];target=None;newtop='ESS140K_EXTERNAL_BANK_SERVICE_V5'
 for t,dt,v,b in records(cells.pop(m['top_cell'])):
  if t==6:b=string(6,newtop)
  if t==18:target=v.rstrip(b'\0').decode()
  if t==16 and target in actor_origins:b=rec(16,3,struct.pack('>2i',*actor_origins[target]))
  elif t==16 and target=='ESS_PROTOCOL_CORRIDORS':xx,yy=struct.unpack('>2i',v);b=rec(16,3,struct.pack('>2i',xx,yy+protocol_delta))
  top.append(b)
  if t==17:target=None
 for e in m['protocol_edges']:
  for w in e['wires']:
   w['source_pad_dbu'][1]+=protocol_delta;w['destination_pad_dbu'][1]+=protocol_delta;w['track_y_dbu']+=protocol_delta
 g=OUT/'eventspikeseg140k_external_bank_service_v4.gds';g.write_bytes(prefix+b''.join(cells.values())+b''.join(lib.cells)+b''.join(top)+rec(4,0));names=[v.rstrip(b'\0') for t,dt,v,b in records(g.read_bytes()) if t==6];assert len(names)==len(set(names))
 m.update(top_cell=newtop,local_bank_pair_instances=m['local_bank_pair_instances']-25,external_bank_service_pair_instances=25,representative_compute_resident_states=4800,external_service_bank_identity_bindings=moved,full_chip_layout_complete=False,full_chip_functional_layout_complete=False,fullspan_guarded_parent_qualification_pending=False,external_service_parent_qualification_pending=True);m['local_pin_nets']+=newnets;m['native_macro_instances'][pair]-=25;m['native_macro_instances'].update({reader:25,shift:m['native_macro_instances'].get(shift,0)+25,tg:m['native_macro_instances'].get(tg,0)+50});m['scope']+=' Externalservicev1moves25existing128state pairs(logicalmembrane channel0 bankrow0 banks1/2)fromplanes into sharedfeedbackreader parents;8actualanalogwritecolumns,selectednativeupshift andtwoTGstartup/restoreselectorconnecteachpairtoexistingcompute. First192membranesperactor nowhavephysicalservicebindings;remainingbank/globalgraph/scheduler unbound. NewparentDRC/LVS/nominal required;childproofdoesnotqualifynewparent.';m['atlas_bbox_um'][3]+=protocol_delta*.001;m['locally_decoded_storage_bank_equivalents']=866005;m['sha256'].update({p.relative_to(R).as_posix():sha(p) for p in inputs|{g}});(OUT/'physical_assembly.json').write_text(json.dumps(m,indent=2)+'\n');(OUT/'resident_pair_move_inventory_v1.json').write_text(json.dumps(dict(active_state_identities=54630400,moved_pairs=moved,removed_plane_pairs=25,new_resident_service_pairs=25,source_identity_audit='artifacts/analog_asic/assembly/full25_locally_decoded_storage_v3/independent_bank_identity_readback_v2.json',full_chip_complete=False),indent=2)+'\n');print(json.dumps(dict(gds=g.relative_to(R).as_posix(),bytes=g.stat().st_size,moved_existing_resident_pairs=25,physically_bound_states_peractor=192,active_original_states=54630400,new_parent_qualified=False),indent=2))
if __name__=='__main__':main()
