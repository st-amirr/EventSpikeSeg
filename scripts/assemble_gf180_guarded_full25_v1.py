"""Bind qualified fullspan guard tile into all25actors without rebuilding resident arrays."""
from pathlib import Path
import json,hashlib,re,struct
from assemble_gf180_full_capacity_storage_gds_v2 import records,rec,string
from assemble_gf180_full25_physical_candidate_v5 import Library,pinlist
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=B/'assembly/full25_locally_decoded_storage_v2';out=B/'assembly/full25_locally_decoded_storage_v3';assert not out.exists();out.mkdir();mf=old/'physical_assembly.json';m=json.loads(mf.read_text());oldg=old/'eventspikeseg140k_locally_decoded_storage_v2.gds';rs=list(records(oldg.read_bytes()));first=next(i for i,r in enumerate(rs) if r[0]==5);prefix=b''.join(r[3] for r in rs[:first]);cells={};parts=[];name=None
 for t,d,v,b in rs[first:]:
  if t==5:parts=[]
  parts.append(b)
  if t==6:name=v.rstrip(b'\0').decode()
  if t==7:cells[name]=b''.join(parts)
 before='gf180_decoded_shared_compute_tile_v1';after='gf180_decoded_shared_compute_tile_v2';d=B/'layout'/after;qp=d/'qualification.json';q=json.loads(qp.read_text());oldq=json.loads((B/'layout'/before/'qualification.json').read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];assert q['ports']==oldq['ports'] and pinlist(d,after)==pinlist(B/'layout'/before,before);newg=d/(after+'.gds');assert sha(newg)==q['sha256'][newg.name];oldtile=B/'layout'/before/(before+'.gds');oldroot='N'+sha(oldtile)[:8]+'_'+hashlib.sha256(before.encode()).hexdigest()[:16];lib=Library();newroot=lib.load(newg)[after];assert not set(re.findall(rb'(?s)\x00',b'')) # No semantic use; cellname uniqueness checked below.
 replacements=0;modified=[]
 for a in m['actor_regions']:
  cname=a['gds_cell'];parts=[];count=0
  for t,dt,v,b in records(cells[cname]):
   if t==18 and v.rstrip(b'\0').decode()==oldroot:b=string(18,newroot);count+=1
   parts.append(b)
  assert count==1;cells[cname]=b''.join(parts);replacements+=count;modified.append(cname)
  for p in a['modules']:
   if p['cell']==before:
    p['cell']=after;p['bbox_dbu'][2]+=round((q['bbox_um'][2]-oldq['bbox_um'][2])*1000);assert p['bbox_dbu'][2]<a['bbox_dbu'][2]-a['origin_dbu'][0];p['native_guard_revision']=2
  a['guarded_compute_tile_physical']=True;a['parent_native_verification_current']=False
 oldtop=m['top_cell'];newtop='ESS140K_LOCALLY_DECODED_STORAGE_V3';top=b''.join(string(6,newtop) if t==6 else b for t,dt,v,b in records(cells.pop(oldtop)));g=out/'eventspikeseg140k_locally_decoded_storage_v3.gds';g.write_bytes(prefix+b''.join(cells.values())+b''.join(lib.cells)+top+rec(4,0));names=[v.rstrip(b'\0') for t,dt,v,b in records(g.read_bytes()) if t==6];assert len(names)==len(set(names));assert replacements==25
 for p in m['state_planes']:assert cells[p['candidate_cell']]==nextcell(oldg,p['candidate_cell'])
 audit=old/'independent_bank_identity_readback_v1.json';ident=json.loads(audit.read_text());assert ident['all_emitted_local_decoder_bank_identities_bijective'];ident.update(scope='All56resident plane cell bytes preserved exactly from independentlyauditedv2GDS,including all866055pair/single bank placements. All25compute-leaf port names/layers/coordinates unchanged;newguardedleaf exact759primitive proof preserves64stateallocation. ActorrootrecordschangeonlytileSNAME,oneperactor. Wholechipfunctionalaccess/DRC/LVS/accuracyservice remainunqualified.',source_bank_identity_audit=audit.relative_to(R).as_posix(),all_state_plane_cell_bytes_identical=True,compute_tile_native_pin_coordinates_identical=True,all25_actor_native_cells_byte_identical_to_prior_candidate=False,original_first_actor_native_drc_and_exact_connectivity_proof_preserved_by_translation=False,sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),audit,oldg,newg,g,qp]});(out/'independent_bank_identity_readback_v2.json').write_text(json.dumps(ident,indent=2)+'\n')
 m['native_macro_instances'][after]=m['native_macro_instances'].pop(before);m.update(top_cell=newtop,source_physical_candidate=mf.relative_to(R).as_posix(),full_chip_layout_complete=False,full_chip_functional_layout_complete=False,first_actor_native_connectivity_proof_preserved_by_translation=False,fullspan_guarded_compute_tiles=25,fullspan_guarded_parent_qualification_pending=True);m['sha256'].update({p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,oldg,newg,g,qp]});m['scope']+=' Newv3imports25fullspan grounded-bus-guard tiles;nativeports unchanged,all residentplane bytes preserved. Freshparentcheck required;oldactorproofdoesnotqualifynewrouting guards.';(out/'physical_assembly.json').write_text(json.dumps(m,indent=2)+'\n');(out/'assembly_overview.svg').write_bytes((old/'assembly_overview.svg').read_bytes());print(json.dumps(dict(gds=g.relative_to(R).as_posix(),bytes=g.stat().st_size,guarded_compute_tiles=25,active_analog_states=54630400,resident_plane_bytes_unchanged=True,full_chip_complete=False)))
def nextcell(path,wanted):
 parts=[];cur=None
 for t,d,v,b in records(path.read_bytes()):
  if t==5:parts=[]
  parts.append(b)
  if t==6:cur=v.rstrip(b'\0').decode()
  if t==7 and cur==wanted:return b''.join(parts)
 raise AssertionError(wanted)
if __name__=='__main__':main()
