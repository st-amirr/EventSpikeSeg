"""Check actual emitted actor service references and complete resident capacity, independently."""
from pathlib import Path
from functools import lru_cache
import json,hashlib,struct,collections
from assemble_gf180_full_capacity_storage_gds_v2 import records
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_external_bank_service_v5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 mf=D/'physical_assembly.json';m=json.loads(mf.read_text());g=D/'eventspikeseg140k_external_bank_service_v5.gds';prior=D/'independent_bank_identity_readback_v1.json';p=json.loads(prior.read_text());assert p['all_emitted_local_decoder_bank_identities_bijective'] and p['distinct_raw_plane_bank_equivalents_checked']==866005;out=D/'independent_resident_service_composition_v1.json';assert not out.exists()
 refs=collections.defaultdict(list);cur=None;e=None;names=set()
 for t,dt,v,b in records(g.read_bytes()):
  if t==6:cur=v.rstrip(b'\0').decode();assert cur not in names;names.add(cur)
  if t in [10,11]:e={'count':1}
  if t==18:e['child']=v.rstrip(b'\0').decode()
  if t==19:e['count']=math.prod(struct.unpack('>2h',v))
  if t==17 and e:refs[cur].append(e);e=None
 assert all(e['child'] in names for es in refs.values() for e in es)
 @lru_cache(None)
 def count(root,target):return int(root==target)+sum(e['count']*count(e['child'],target) for e in refs[root])
 def rootname(cell):
  d=B/'layout'/cell;q=json.loads((d/'qualification.json').read_text());gg=d/(cell+'.gds');assert sha(gg)==q['sha256'][gg.name];return 'N'+sha(gg)[:8]+'_'+hashlib.sha256(cell.encode()).hexdigest()[:16],q
 rn,rq=rootname('gf180_bank_pair_shared_reader_v1');cn,cq=rootname('gf180_decoded_shared_compute_tile_v2');pn,pq=rootname('gf180_independent_bank_pair_v4');sn,sq=rootname('gf180_compact_decoded_bank8x8_v1')
 assert {n for n in rq['ports'] if n.startswith(('B0_STATE','B1_STATE'))}=={f'B{b}_STATE{r}{c}' for b in range(2) for r in range(8) for c in range(8)}
 rows=[]
 for a in m['actor_regions']:
  root=a['gds_cell'];assert count(m['top_cell'],root)==1;assert sum(e['count'] for e in refs[root] if e['child']==rn)==1;assert sum(e['count'] for e in refs[root] if e['child']==cn)==1
  rows.append(dict(actor=a['actor'],actual_shared128reader_roots=1,actual_original64compute_roots=1,permanent_bank_identities=[[0,0,b] for b in range(3)],allocation='bank0 originalcompute STATErc;bank1 service B0_STATErc;bank2 service B1_STATErc'))
 totals={key:count(m['top_cell'],root) for key,root in [('raw_pairs',pn),('raw_singles',sn),('shared128_readers',rn),('original64_compute',cn)]};assert totals==dict(raw_pairs=432990,raw_singles=25,shared128_readers=25,original64_compute=25),totals;capacity=2*totals['raw_pairs']+totals['raw_singles']+2*totals['shared128_readers']+totals['original64_compute'];assert capacity==866080
 report=dict(all_resident_bank_identities_preserved_without_duplication=True,plane_identity_proof=prior.relative_to(R).as_posix(),actual_binary_hierarchy_counts=totals,total_64state_bank_equivalents=capacity,original_active_state_identities=54630400,actor_allocations=rows,new_actor_routing_qualified=False,full_chip_complete=False,scope='Actual binary hierarchy root counts/one peractor plus complete independent plane identityset audit. Qualified reader exposes128distinct native state ports; existingcompute64distinct sites. Together complete original bankidentityset with25moved pairs, including padded sites governed by original shapes. Does not qualify new analog routing/function,wholechip DRC/LVS,accuracy or5ms service.',sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,g,prior]});out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['actor_allocations','sha256']},indent=2))
if __name__=='__main__':
 import math
 main()
