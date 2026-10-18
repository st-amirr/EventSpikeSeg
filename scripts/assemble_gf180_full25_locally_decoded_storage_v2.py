"""Replace all raw capacity banks by native locally addressable bank geometry."""
from pathlib import Path
from functools import lru_cache
import json,hashlib,math,struct,collections,html
from assemble_gf180_full_capacity_storage_gds_v2 import records,rec,string,begin,reference
from assemble_gf180_full25_physical_candidate_v5 import Library
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';SRC=B/'assembly/full25_physical_candidate_v8';OUT=B/'assembly/full25_locally_decoded_storage_v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();mf=SRC/'physical_assembly.json';m=json.loads(mf.read_text());oldgds=SRC/'eventspikeseg140k_physical_candidate_v8.gds';rs=list(records(oldgds.read_bytes()));start=next(i for i,r in enumerate(rs) if r[0]==5);prefix=b''.join(r[3] for r in rs[:start]);cells={};body=b'';name=None
 for t,d,v,b in rs[start:]:
  if t==5:body=b''
  body+=b
  if t==6:name=v.rstrip(b'\0').decode()
  if t==7:cells[name]=body
 lib=Library();pair='gf180_independent_bank_pair_v4';single='gf180_compact_decoded_bank8x8_v1';qualified={};inputs={Path(__file__),mf,oldgds}
 for c in [pair,single]:
  d=B/'layout'/c;qf=d/'qualification.json';q=json.loads(qf.read_text());g=d/(c+'.gds');assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and sha(g)==q['sha256'][g.name];mapping=lib.load(g);qualified[c]=(mapping[c],q);inputs.update([qf,g])
 pn,pq=qualified[pair];sn,sq=qualified[single];pbb=[round(v*1000) for v in pq['bbox_um']];sbb=[round(v*1000) for v in sq['bbox_um']];pw=pbb[2]-pbb[0];sw=sbb[2]-sbb[0];ph=pbb[3]-pbb[1];sh=sbb[3]-sbb[1];pp=pw+2000;sp=sw+2000;yp=max(ph,sh)+2000
 x=y=shelf=0;planes=[];old_to_new={};pair_total=single_total=0;removed=0;new_cells=[]
 for e in m['state_planes']:
  c,h,w=e['shape_chw'];ny,nx=e['bank_grid_yx'];replace=e['state_kind']=='membrane';cw=(nx//2)*pp+(sp if nx%2 else 0)+20000;ch=ny*yp+20000;cols=max(1,min(e['channel_grid_cols'],140000000//cw));width=cols*cw;height=math.ceil(c/cols)*ch
  if x+width>140000000:x=0;y+=shelf+200000;shelf=0
  origin=[x,y];body=b'';np=ns=0
  def rows(cx,cy,first_row,nrows,logical_first_x):
   nonlocal body,np,ns
   count=nx-logical_first_x;n=count//2
   if n:
    body+=reference(pn,cx-pbb[0],cy+first_row*yp-pbb[1],n,nrows,pp,yp);np+=n*nrows
   if count%2:
    body+=reference(sn,cx+n*pp-sbb[0],cy+first_row*yp-sbb[1],1,nrows,sp,yp);ns+=nrows
  for ci in range(c):
   cx=(ci%cols)*cw;cy=(ci//cols)*ch
   if ci==0 and replace:
    rows(cx,cy,0,1,1)
    if ny>1:rows(cx,cy,1,ny-1,0)
    removed+=1
   else:rows(cx,cy,0,ny,0)
  expected=c*ny*nx-int(replace);assert 2*np+ns==expected
  newname='ESS_DECODED_STATE_'+str(e['plane_index']).zfill(2);new_cells.append(begin(newname)+body+rec(7,0));old_to_new[e['candidate_cell']]=(newname,origin)
  plane=dict(e,candidate_cell=newname,origin_dbu=origin,bbox_dbu=[x,y,x+width,y+height],channel_grid_cols=cols,channel_pitch_dbu=[cw,ch],local_pair_pitch_dbu=[pp,yp],pair_instances=np,single_instances=ns,locally_decoded_bank_equivalents=2*np+ns,local_row_decode_physical=True,global_bank_selection_connected=False,storage_access_to_other_banks_connected=False,source_capacity_path_metadata_historical=True,identity_binding={'logical_bank_x':'floor(x/8)','logical_bank_y':'floor(y/8)','logical_row':'y%8','logical_column':'x%8','first_bank_exception':'If membrane,c==0,y<8,x<8:original actor compute tile bank; no duplicate in this plane.','logical_first_bank_x_by_row':'1 only for membrane,c==0,bank_y==0; otherwise0.','pair_index':'floor((bank_x-logical_first_bank_x)/2)','pair_bank_select':'(bank_x-logical_first_bank_x)%2','single_condition':'last bank of an odd remaining row uses single native decoder.','pair_native_state_port':'B[bank_select]_STATE[logical_row][logical_column]','single_native_state_port':'STATE[logical_row][logical_column]','global_compute_and_categorical_protocol_bound':False})
  planes.append(plane);pair_total+=np;single_total+=ns;x+=width+200000;shelf=max(shelf,height)
 storage_height=y+shelf;dy=max(0,storage_height+1000000-125000000);oldtop=m['top_cell'];newtop='ESS140K_LOCALLY_DECODED_STORAGE_V2';top=b'';target=None
 for t,d,v,b in records(cells[oldtop]):
  if t==6:b=string(6,newtop)
  if t==18:
   target=v.rstrip(b'\0').decode()
   if target in old_to_new:b=string(18,old_to_new[target][0])
  if t==16 and target:
   xx,yy=struct.unpack('>2i',v)
   if target in old_to_new:xx,yy=old_to_new[target][1]
   elif target.startswith('ESS_ACTOR_') or target=='ESS_PROTOCOL_CORRIDORS':yy+=dy
   b=rec(16,3,struct.pack('>2i',xx,yy))
  top+=b
  if t==17:target=None
 omitted=set(old_to_new)|{oldtop};output=prefix+b''.join(b for n,b in cells.items() if n not in omitted)+b''.join(lib.cells)+b''.join(new_cells)+top+rec(4,0);gds=OUT/'eventspikeseg140k_locally_decoded_storage_v2.gds';gds.write_bytes(output)
 # Read the emitted binary hierarchy independently; never flatten full-model SPICE.
 refs=collections.defaultdict(list);names=set();cur=None;item=None
 for t,d,v,b in records(output):
  if t==6:cur=v.rstrip(b'\0').decode();assert cur not in names;names.add(cur)
  if t in [10,11]:item={'count':1}
  if t==18:item['child']=v.rstrip(b'\0').decode()
  if t==19:item['count']=math.prod(struct.unpack('>2h',v))
  if t==17 and item:refs[cur].append(item);item=None
 assert all(e['child'] in names for v in refs.values() for e in v)
 @lru_cache(None)
 def count(root,target):return int(root==target)+sum(e['count']*count(e['child'],target) for e in refs[root])
 assert count(newtop,pn)==pair_total and count(newtop,sn)==single_total
 assert removed==25 and 2*pair_total+single_total+25==m['bank_capacity_instances']==866080
 for a in m['actor_regions']:
  a['origin_dbu'][1]+=dy;a['bbox_dbu'][1]+=dy;a['bbox_dbu'][3]+=dy
  a['remaining_membrane_banks_have_local_row_decoder']=True;a['remaining_membrane_banks_access_unconnected']=a['remaining_membrane_banks_access_unconnected'];a['global_bank_selection_and_compute_binding_complete']=False
 for e in m['protocol_edges']:
  for v in e['wires']:v['source_pad_dbu'][1]+=dy;v['destination_pad_dbu'][1]+=dy;v['track_y_dbu']+=dy
 active=sum(p['active_state_count'] for p in planes);assert active==54630400
 storage_area=(pair_total*pw*ph+single_total*sw*sh+25*10017.972*1e6)/1e12
 m.update(top_cell=newtop,state_planes=planes,source_physical_candidate=mf.relative_to(R).as_posix(),unaddressed_raw_storage_bank_instances=0,locally_decoded_storage_bank_equivalents=2*pair_total+single_total,local_bank_pair_instances=pair_total,local_single_bank_instances=single_total,compute_tile_bank_instances=25,all_analog_state_capacity_has_compute_access=False,global_bank_selection_complete=False,local_row_decode_capacity_complete_except_original25_compute_banks=False,local_row_decode_capacity_complete=True,local_row_decode_capacity_fraction=1.0,native_local_decoder_macro_footprint_mm2=storage_area,decoder_footprint_is_not_compact_die_area=True,atlas_bbox_um=[0,0,167968.1,m['atlas_bbox_um'][3]+dy*.001],actor_and_protocol_translation_y_um=dy*.001,storage_atlas_height_um=storage_height*.001,first_actor_native_connectivity_proof_preserved_by_translation=False,full_chip_layout_complete=False,full_chip_functional_layout_complete=False)
 m['native_macro_instances'].update({pair:pair_total,single:single_total});m['storage_only_bank_instances']=0
 m['missing_interfaces']=[s for s in m['missing_interfaces'] if not s.startswith('Storage banks beyond')];m['missing_interfaces'].insert(0,'All remaining banks now have actual local row decode and bank-pair isolation geometry; higher bank-address selection,shared readout mux/reader/write driver/compute routing and service allocation remain unbound. All25compute-tile banks now include native local rowdecode and sharedread/write/compute connections,nominal fullcycle remains incomplete.')
 m['scope']='Whole-model native physical candidate with all54,630,400original analog state identities preserved.866,055remaining bank equivalents use physically qualified native row-decode geometry,paired with independent bank enables and shared analog DATA where possible;25first membrane banks reside in newly qualified decoded shared-compute tiles. This is local access circuitry throughout capacity,not a connected full-population memory service or functional fullchip. Global bank selection,compute sharing,parameter programming and graph operator/endpoint binding remain missing. Macro footprint includes actual spacious native decode routing and is not compact die area. No fullmodel SPICE or numeric digital storage. New actorparent qualification is recorded separately;earlierfirstactor proofs do not qualify changedgeometry.Full assembly qualification remains incomplete.'
 m['sha256']={p.relative_to(R).as_posix():sha(p) for p in inputs|{gds}};(OUT/'physical_assembly.json').write_text(json.dumps(m,indent=2)+'\n')
 overview=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" viewBox="-20 -40 1720 '+str(m['atlas_bbox_um'][3]/100+100)+'"><rect x="-20" y="-40" width="1720" height="'+str(m['atlas_bbox_um'][3]/100+100)+'" fill="#101827"/><text fill="white" x="0" y="-15" font-size="18">EventSpikeSeg140k: locally decoded storage candidate</text>']
 for e in planes:
  x1,y1,x2,y2=[v/100000 for v in e['bbox_dbu']];overview.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" fill="#38bdf8" fill-opacity=".35" stroke="#38bdf8"><title>{html.escape(e["actor"]+" / "+e["state_kind"])}</title></rect>')
 for a in m['actor_regions']:
  x1,y1,x2,y2=[v/100000 for v in a['bbox_dbu']];overview.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" fill="#34d399" fill-opacity=".35" stroke="#34d399"/>')
 (OUT/'assembly_overview.svg').write_text(''.join(overview)+'</svg>');print(json.dumps({'gds':str(gds),'bytes':len(output),'native_pair_instances':pair_total,'native_single_instances':single_total,'all_bank_equivalents_including25_compute':2*pair_total+single_total+25,'active_analog_state_identities':active,'local_decoder_macro_footprint_mm2':storage_area,'global_bank_compute_binding_complete':False,'full_chip_functional_layout_complete':False},indent=2))
if __name__=='__main__':main()
