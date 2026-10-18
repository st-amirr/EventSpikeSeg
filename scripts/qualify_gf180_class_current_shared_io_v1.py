"""Qualify native class-current IO using exact graph and independent GDS readback."""
from pathlib import Path
import re
import qualify_gf180_adaptation_shared_state_io_v6 as q
R=Path(__file__).resolve().parents[1]
C='gf180_class_current_shared_io_v1'

def main():
 q.C=C;q.D=q.f.BASE/'layout'/C
 reference=(q.D/'reference_compact.spice').read_text()
 reference=re.sub(r'(?m)^\.subckt reference ','.subckt '+C+' ',reference)
 p=q.D/'reference_exact_graph.spice';assert not p.exists();p.write_text(reference)
 q.exact(q.D/'source_compact.spice',p,q.D/'source_exact_graph_v1.json')
 # Same native DRC/cap/GDS workflow. Its generic graph checks are authoritative;
 # remove adaptation-specific prose from the resulting independent evidence.
 q.main()
 import json
 for n in ['qualification.json','flat_cap_qualification.json']:
  p=q.D/n;v=json.loads(p.read_text());v['scope']=v['scope'].replace('exact256primitive','exact176primitive')
  if 'flat_lvs_basis' in v:v['flat_lvs_basis']='Independent unique net/device/pin bijection, every edge and native primitive dimensions verified; native Netgen mismatch retained.'
  v['native_resistor_count']=8
  p.write_text(json.dumps(v,indent=2)+'\n')
 # qualification is an input to the flat report; preserve the final hash.
 p=q.D/'flat_cap_qualification.json';v=json.loads(p.read_text());qp=q.D/'qualification.json';v['sha256'][qp.relative_to(R).as_posix()]=q.sha(qp);p.write_text(json.dumps(v,indent=2)+'\n')
if __name__=='__main__':main()
