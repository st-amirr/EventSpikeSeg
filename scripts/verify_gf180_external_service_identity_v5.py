"""Independently bind emitted GDS placement to every original logical bank identity."""
from pathlib import Path
import json,hashlib,struct,re
from assemble_gf180_full_capacity_storage_gds_v2 import records
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_external_bank_service_v5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 cells={};refs={};body=[];cur=None;item=None;children=[]
 for t,d,v,b in records(p.read_bytes()):
  if t==5:body=[];children=[]
  body.append(b)
  if t==6:cur=v.rstrip(b'\0').decode()
  if t in [10,11]:item={'nx':1,'ny':1}
  if t==18:item['child']=v.rstrip(b'\0').decode()
  if t==19:item['nx'],item['ny']=struct.unpack('>2h',v)
  if t==16 and item:item['xy']=struct.unpack('>'+str(len(v)//4)+'i',v)
  if t==17 and item:children.append(item);item=None
  if t==7:assert cur not in cells;cells[cur]=b''.join(body);refs[cur]=children
 return cells,refs
def main():
 mf=D/'physical_assembly.json';m=json.loads(mf.read_text());gds=D/'eventspikeseg140k_external_bank_service_v5.gds';oldgds=B/'assembly/full25_physical_candidate_v8/eventspikeseg140k_physical_candidate_v8.gds';cells,refs=read(gds);old,_=read(oldgds);out=D/'independent_bank_identity_readback_v1.json';assert not out.exists();inputs={Path(__file__),mf,gds,oldgds};q={}
 for cell in ['gf180_independent_bank_pair_v5','gf180_compact_decoded_bank8x8_v1']:
  qp=B/'layout'/cell/'qualification.json';g=B/'layout'/cell/(cell+'.gds');q[cell]=json.loads(qp.read_text());q[cell]['gds_name']='N'+sha(g)[:8]+'_'+hashlib.sha256(cell.encode()).hexdigest()[:16];inputs.update([qp,g])
 pair=q['gf180_independent_bank_pair_v5'];single=q['gf180_compact_decoded_bank8x8_v1'];assert {n for n in pair['ports'] if re.fullmatch('B[01]_STATE[0-7][0-7]',n)}=={f'B{b}_STATE{r}{c}' for b in range(2) for r in range(8) for c in range(8)};checked=0;rows=[]
 for p in m['state_planes']:
  c,h,w=p['shape_chw'];ny,nx=p['bank_grid_yx'];cw,ch=p['channel_pitch_dbu'];pp,yp=p['local_pair_pitch_dbu'];cols=p['channel_grid_cols'];seen=set();boxcount=0
  for a in refs[p['candidate_cell']]:
   ispair=a['child']==pair['gds_name'];qual=pair if ispair else single;assert a['child']==qual['gds_name'];bb=[round(v*1000) for v in qual['bbox_um']];xy=a['xy'];dx=(xy[2]-xy[0])//a['nx'] if len(xy)>2 else 0;dy=(xy[5]-xy[1])//a['ny'] if len(xy)>2 else 0
   for ay in range(a['ny']):
    for ax in range(a['nx']):
     left=xy[0]+ax*dx+bb[0];bottom=xy[1]+ay*dy+bb[1];cc=left//cw;cr=bottom//ch;channel=cr*cols+cc;assert channel<c;lx=left-cc*cw;ly=bottom-cr*ch;assert ly%yp==0;by=ly//yp;assert 0<=by<ny;assert lx%pp==0;pi=lx//pp;start=int(p['state_kind']=='membrane' and channel==0 and by==0);first=start+2*pi
     for bankoffset in range(2 if ispair else 1):
      bx=first+bankoffset;assert 0<=bx<nx;key=(channel,by,bx);assert key not in seen,(p['actor'],key);seen.add(key)
     assert ispair or first==nx-1
     boxcount+=1
  hole={(0,0,bx) for bx in range(3)} if p['state_kind']=='membrane' else set();expected={(ci,by,bx) for ci in range(c) for by in range(ny) for bx in range(nx)};assert seen==expected-hole;checked+=len(seen);rows.append(dict(plane=p['plane_index'],actor=p['actor'],state_kind=p['state_kind'],native_macro_placements=boxcount,distinct_logical_bank_identities=len(seen),omitted_first_compute_bank=len(hole),placement_identity_bijection=True))
 assert len(m['external_service_bank_identity_bindings'])==25
 for a in m['actor_regions']:
  assert sum(p['cell']=='gf180_bank_pair_shared_reader_v1' for p in a['modules'])==1
  assert a['representative_compute_tile_resident_membranes']==192
 assert checked==866005 and sum(p['active_state_count'] for p in m['state_planes'])==54630400
 report=dict(all_emitted_local_decoder_bank_identities_bijective=True,distinct_raw_plane_bank_equivalents_checked=checked,compute_tile_exception_banks=25,external_reader_exception_banks=50,total_bank_equivalents=866080,active_analog_state_identities=54630400,all25_actor_native_cells_byte_identical_to_prior_candidate=False,original_first_actor_native_drc_and_exact_connectivity_proof_preserved_by_translation=False,full_chip_native_DRC_completed=False,full_chip_native_LVS_completed=False,global_bank_and_compute_access_complete=False,scope='Independent emitted binary GDS AREF/SREF coordinates,not builder counters. Each actual native pair/single placement decoded back to original(channel,bank_y,bank_x); complete perplane set equality and duplicate rejection. Source bank pair qualified128unique STATE ports. Eachactor nowcontainsoriginal64state compute andone128state physical sharedreader;plane holes map to logicalbanks0,1,2. Additional128states require separately qualified actorparent bindings;no identity duplication bycapacity count. Does not qualify global routing,whole-chip DRC/LVS,capacitance,accuracy or service.',planes=rows,sha256={p.relative_to(R).as_posix():sha(p) for p in inputs});out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['planes','sha256']},indent=2))
if __name__=='__main__':main()
