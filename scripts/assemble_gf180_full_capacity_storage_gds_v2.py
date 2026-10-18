"""Place the full original-float analog state capacity using real qualified bank GDS.

This is a storage-only physical capacity assembly, not a connected full ASIC.
No third-party GDS writer is required: preserve native bank records and add
standard hierarchical GDS AREF/SREF records with independent readback checks.
"""
from pathlib import Path
import datetime,hashlib,json,math,struct
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(b):
 i=0
 while i<len(b):
  n,t,d=struct.unpack('>HBB',b[i:i+4]);assert n>=4 and n%2==0 and i+n<=len(b)
  yield t,d,b[i+4:i+n],b[i:i+n];i+=n
 assert i==len(b)
def rec(t,d,p=b''):
 if len(p)%2:p+=b'\0'
 return struct.pack('>HBB',len(p)+4,t,d)+p
def string(t,s):return rec(t,6,s.encode('ascii'))
def real8(b):
 if b==b'\0'*8:return 0.
 return (-1 if b[0]&128 else 1)*int.from_bytes(b[1:],'big')/(2**56)*16.**((b[0]&127)-64)
def begin(name):
 dt=datetime.datetime.now();v=[dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second]*2
 return rec(5,2,struct.pack('>12h',*v))+string(6,name)
def reference(name,x,y,nx=1,ny=1,pitchx=0,pitchy=0):
 if nx==ny==1:return rec(10,0)+string(18,name)+rec(16,3,struct.pack('>2i',x,y))+rec(17,0)
 assert 0<nx<=32767 and 0<ny<=32767
 return rec(11,0)+string(18,name)+rec(19,2,struct.pack('>2h',nx,ny))+rec(16,3,struct.pack('>6i',x,y,x+nx*pitchx,y,x,y+ny*pitchy))+rec(17,0)
def main():
 cell='gf180_underplate_biased_bank8x8_v1';d=B/'layout'/cell;native=d/(cell+'.gds');qpath=d/'qualification.json';q=json.loads(qpath.read_text());aq=d/'abstract_qualification.json'
 assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and sha(native)==q['sha256'][native.name]
 inp=B/'assembly/full25actor_permanent_analog_state_selectors_v1.json';selectors=json.loads(inp.read_text());assert selectors['logical_analog_nodes']==54630400
 raw=list(records(native.read_bytes()));units=next(v for t,dt,v,b in raw if t==3);dbum=real8(units[8:])*1e6;assert abs(dbum-.001)<1e-12
 first=next(i for i,(t,dt,v,b) in enumerate(raw) if t==5);last=max(i for i,(t,dt,v,b) in enumerate(raw) if t==7)
 body=b''.join(b for t,dt,v,b in raw[first:last+1]);prefix=b''.join(b for t,dt,v,b in raw[:first])
 # Qualified bbox100.28x99.9um plus2um horizontal/vertical interbank gaps.
 pitchx=102280;pitchy=101900;plane_gap=100000;atlas_width=140000000
 generated=[];planes=[];sx=sy=shelf_h=0;padded=active=banks=0
 for pi,p in enumerate(selectors['planes']):
  c,h,w=p['shape_chw'];nx=math.ceil(w/8);ny=math.ceil(h/8);n=nx*ny*c
  channel_w=nx*pitchx;channel_h=ny*pitchy;channel_cols=min(c,max(1,20000000//channel_w));channel_rows=math.ceil(c/channel_cols)
  width=channel_cols*(channel_w+plane_gap);height=channel_rows*(channel_h+plane_gap)
  if sx+width>atlas_width:sx=0;sy+=shelf_h+plane_gap;shelf_h=0
  name=f'STATE_PLANE_{pi:02d}';b=begin(name)
  # Offset moves the qualified bank bbox lower left to each tile origin.
  for ch in range(c):
   x=(ch%channel_cols)*(channel_w+plane_gap)+7220;y=(ch//channel_cols)*(channel_h+plane_gap)+12200
   b+=reference(cell,x,y,nx,ny,pitchx,pitchy)
  generated.append(b+rec(7,0));entry=dict(p,plane_index=pi,gds_cell=name,origin_dbu=[sx,sy],bbox_dbu=[sx,sy,sx+width,sy+height],bank_grid_yx=[ny,nx],bank_count=n,bank_slot_capacity=n*64,padded_inactive_slots=n*64-c*h*w,channel_grid_cols=channel_cols,channel_pitch_dbu=[channel_w+plane_gap,channel_h+plane_gap],bank_pitch_dbu=[pitchx,pitchy],dense_physical_cell=cell,
   physical_identity_expression=f'STORAGE_CAPACITY_TOP/{name}/channel[c]/tile[y//8,x//8]/STATE[y%8,x%8]',physical_state_coordinate_um_expression='plane_origin + channel_origin + tile_origin + native_local_STATE_pad; values remain analog charge',compute_lane_sharing_selected=False)
  planes.append(entry);active+=c*h*w;padded+=n*64;banks+=n;sx+=width+plane_gap;shelf_h=max(shelf_h,height)
 assert active==54630400 and len(planes)==56
 top=begin('STORAGE_CAPACITY_TOP')
 for p in planes:top+=reference(p['gds_cell'],*p['origin_dbu'])
 generated.append(top+rec(7,0));output=prefix+body+b''.join(generated)+rec(4,0)
 out=B/'assembly/full_capacity_storage_gds_v2';assert not out.exists();out.mkdir();gds=out/'full_capacity_storage_v2.gds';gds.write_bytes(output)
 # Parse every emitted record; independently count hierarchy references and ensure
 # all children resolve. This verifies GDS structure/capacity, not physical DRC.
 names=set();refs=[];current=None;last_ref=None
 for t,dt,v,b in records(output):
  if t==6:current=v.rstrip(b'\0').decode();assert current not in names;names.add(current)
  if t in [10,11]:last_ref={'parent':current,'kind':t,'nx':1,'ny':1}
  if t==18:last_ref['child']=v.rstrip(b'\0').decode()
  if t==19:last_ref['nx'],last_ref['ny']=struct.unpack('>2h',v)
  if t==17 and last_ref:refs.append(last_ref);last_ref=None
 assert all(r['child'] in names for r in refs)
 actual_bank_count=sum(r['nx']*r['ny'] for r in refs if r['child']==cell);assert actual_bank_count==banks
 assert sum(r['parent']=='STORAGE_CAPACITY_TOP' for r in refs)==56
 r=dict(storage_capacity_layout_written=True,gds_binary_record_readback_pass=True,logical_active_analog_nodes=active,physical_storage_slots=padded,inactive_boundary_padding_slots=padded-active,physical_bank_instances=banks,bank_area_um2=100.28*99.9,total_bank_geometry_area_mm2=banks*100.28*99.9/1e6,
  layout_atlas_bbox_um=[0,0,max(p['bbox_dbu'][2] for p in planes)*dbum,max(p['bbox_dbu'][3] for p in planes)*dbum],db_unit_um=dbum,checkpoint_sha256=selectors['checkpoint_sha256'],planes=planes,
  full_chip_layout_complete=False,top_level_routed=False,top_level_native_DRC_completed=False,top_level_native_LVS_completed=False,full_5ms_population_service_accepted=False,original_float_accuracy_accepted=False,
  scope='Storage-only physical capacity atlas with all56 original-float state planes and exact54,630,400 active identities. Native qualified8x8 bank polygons are preserved verbatim in GDS; hierarchical arrays instantiate actual padded capacity, independently counted from binary GDS. Native shared9MOS column-current mirror perbank is included. All interbank wiring, master-reference distribution, rowdecoder/write-drivers, trained beta/weights, complete PLIF/adaptation/inhibition, readout50ms hold qualification and global phase/network connectivity are absent. This very large atlas is not a reticle-sized manufacturable die or selected chiplet/stack architecture. Updated bank native checks and completed local5ms sequence do not qualify atlas DRC/LVS or whole-model behavior. Conditional1,215mm2 bare-plate estimate is not the physical bank area.',
  sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),native,qpath,aq,inp,gds]})
 rp=out/'capacity_assembly.json';rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['planes','sha256']},indent=2))
if __name__=='__main__':main()
