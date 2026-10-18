"""Expand actual Magic hierarchy and sum signed capacitance corrections, never clip."""
from pathlib import Path
from decimal import Decimal
import argparse,hashlib,json,re
def expand(text,top):
 defs={}
 for m in re.finditer(r'(?ims)^\.subckt\s+(\S+)\s+([^\n]*)\n(.*?)^\.ends[^\n]*',text.replace('\n+',' ')):
  name,ports,body=m.groups();defs[name.lower()]=(ports.lower().split(),[l.lower().split() for l in body.splitlines() if l.strip() and not l.lstrip().startswith('*')])
 top=top.lower();instances={};parents={};primitive=[];caps=[];nodes=set();unresolved=[]
 def key(path,n):return ((),n) if n in ['0','vsubs'] else (path,n)
 def find(k):
  if k not in parents:parents[k]=k
  if parents[k]!=k:parents[k]=find(parents[k])
  return parents[k]
 def union(a,b):
  a=find(a);b=find(b)
  if a!=b:parents[max(a,b)]=min(a,b)
 def visit(name,path,ancestry):
  assert name not in ancestry,'Recursive hierarchy'
  ports,lines=defs[name];instances[path]={'ports':ports,'children':{},'tokens':set(ports)}
  for t in lines:
   if t[0].startswith('x'):
    idx=next((i for i,v in enumerate(t[1:],1) if '=' in v),len(t));model=t[idx-1];ns=t[1:idx-1];params=t[idx:]
    if model in defs:
     child=path+(t[0][1:],);instances[path]['children'][t[0][1:]]=child;visit(model,child,ancestry+(name,))
     assert len(ns)==len(defs[model][0])
     for a,b in zip(ns,defs[model][0]):union(key(path,a),key(child,b))
    else:primitive.append((path,ns,model,params))
    instances[path]['tokens'].update(ns)
   elif t[0].startswith('c'):
    assert len(t)==4,t;caps.append((path,t[1],t[2],t[3]));instances[path]['tokens'].update(t[1:3])
   else:assert t[0].startswith('.'),t
 visit(top,(),())
 def resolve(path,token):
  if '/' not in token:return key(path,token)
  prefix,rest=token.split('/',1)
  if prefix in instances[path]['children']:return resolve(instances[path]['children'][prefix],rest)
  unresolved.append((path,token));return key(path,token)
 for path,inst in instances.items():
  for n in inst['tokens']:
   k=key(path,n);nodes.add(k);union(k,resolve(path,n))
 ports=defs[top][0];names={find(key((),n)):n for n in ports}
 for g in ['0','vsubs']:names[find(key((),g))]=g
 def nname(k):
  k=find(k)
  if k not in names:names[k]='n'+str(len(names))
  return names[k]
 lines=[]
 for i,(path,ns,model,params) in enumerate(primitive):lines.append('X'+str(i)+' '+' '.join([nname(key(path,n)) for n in ns]+[model]+params))
 units={'':Decimal(1),'f':Decimal('1e-15'),'p':Decimal('1e-12'),'n':Decimal('1e-9'),'u':Decimal('1e-6'),'m':Decimal('1e-3')};aggregate={};shorted=0;negative_raw=0
 for path,a,b,value in caps:
  m=re.fullmatch(r'([-+0-9.e]+)([fpnum]?)',value);assert m,value;v=Decimal(m[1])*units[m[2]];negative_raw+=v<0
  a=nname(key(path,a));b=nname(key(path,b))
  if a==b:shorted+=1;continue
  pair=tuple(sorted([a,b]));aggregate[pair]=aggregate.get(pair,Decimal(0))+v
 negative={str(k):str(v) for k,v in aggregate.items() if v<0}
 for i,((a,b),v) in enumerate(sorted(aggregate.items())):lines.append(f'C{i} {a} {b} {v}')
 report=dict(electrical_hierarchy_expansion_completed=True,primitive_device_count=len(primitive),native_signed_cap_records=len(caps),negative_native_correction_records=negative_raw,physically_shorted_cap_records=shorted,aggregate_cap_branch_count=len(aggregate),negative_aggregate_branches=negative,unresolved_hierarchical_names=[{'path':'/'.join(p),'token':n} for p,n in sorted(set(unresolved))],passive_nonnegative_branch_network=not negative,geometry_flat_extraction_completed=False,
  scope='Algebraic expansion of existing native Magic hierarchical capacitance export. Original native device params retained; parent/child port and actual slash-qualified instance aliases resolved before signed correction summation. No clipping or replacement of negative capacitance. This is not a new geometric flat extraction. Unresolved hierarchy names or negative sums prohibit qualification; independent native flat baseline comparison remains required.')
 return '.subckt '+top+'_electrical '+' '.join(ports)+'\n'+'\n'.join(lines)+'\n.ends\n',report
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--top',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();p=Path(a.source);out=Path(a.output);assert not out.exists();text,r=expand(p.read_text(),a.top);out.write_text(text);r['source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();r['expanded_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['negative_aggregate_branches','unresolved_hierarchical_names']},indent=2));print('negative',len(r['negative_aggregate_branches']),'unresolved',len(r['unresolved_hierarchical_names']))
if __name__=='__main__':main()
