"""Byte-equivalent namespace import without quadratic per-cell concatenation."""
from pathlib import Path
import hashlib
from assemble_gf180_full25_physical_candidate_v5 import Library as Original
from assemble_gf180_full_capacity_storage_gds_v2 import records,real8,string
class Library(Original):
 def load(self,p):
  if p in self.maps:return self.maps[p]
  blob=p.read_bytes();units=next(v for t,d,v,b in records(blob) if t==3);assert abs(real8(units[8:])*1e6-.001)<1e-12
  names=[v.rstrip(b'\0').decode() for t,d,v,b in records(blob) if t==6];assert len(names)==len(set(names));tag=hashlib.sha256(blob).hexdigest()[:8];mapping={n:'N'+tag+'_'+hashlib.sha256(n.encode()).hexdigest()[:16] for n in names};head=[];body=None
  for t,d,v,b in records(blob):
   if t==5:body=[]
   if body is None:
    if t!=4:head.append(b)
   else:body.append(string(t,mapping[v.rstrip(b'\0').decode()]) if t in (6,18) else b)
   if t==7:self.cells.append(b''.join(body));body=None
  if self.prefix is None:
   # Prefix ends at the first BGNSTR, not at later inter-structure records.
   parts=[]
   for t,d,v,b in records(blob):
    if t==5:break
    parts.append(b)
   self.prefix=b''.join(parts)
  self.maps[p]=mapping;self.inputs.add(p);return mapping
