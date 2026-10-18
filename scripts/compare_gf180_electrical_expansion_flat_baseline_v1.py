"""Compare expanded native hierarchy against independently completed geometric flat PEX."""
from pathlib import Path
from decimal import Decimal
import hashlib,json,re
from compare_gf180_exact_hierarchy_graph_v2 import parse,graph,component_compare
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(text):return '\n'.join(('X'+l[1:].lower()) if l.startswith(('X','x')) else l.lower() for l in text.splitlines())
def caps(text):
 out={};units={'':Decimal(1),'f':Decimal('1e-15'),'p':Decimal('1e-12'),'n':Decimal('1e-9'),'u':Decimal('1e-6'),'m':Decimal('1e-3')}
 for l in text.splitlines():
  if not l.lower().startswith('c'):continue
  t=l.lower().split();m=re.fullmatch(r'([-+0-9.e]+)([fpnum]?)',t[3]);assert m,t;v=Decimal(m[1])*units[m[2]];pair=tuple(sorted(t[1:3]));out[pair]=out.get(pair,Decimal(0))+v
 return out
def main():
 cell='gf180_formatted_energy64_v3';d=B/'layout'/cell;ep=d/'electrical_hierarchy_expanded_cap_v1.spice';fp=d/(cell+'_flat_cap.spice');et=normalize(ep.read_text());ft=normalize(fp.read_text())
 eg=graph(parse(et),cell+'_electrical');fg=graph(parse(ft),cell+'_flat');ok,mapping,stats=component_compare(eg,fg)
 r=dict(exact_primitive_graph_equivalent=ok,comparison_stats=stats,scope='Actual2304MOS full64 independent geometric-flat PEX baseline versus algebraically expanded native hierarchical PEX. Exact device graph establishes one net bijection; capacitance comparison follows that bijection. Symmetric device graph may permit multiple mappings; mismatch alone does not identify the physical source of an inequivalence.',sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),ep,fp,R/'scripts/expand_gf180_hierarchical_capacitance_v1.py']})
 if ok:
  ec=caps(et);fc=caps(ft);mc={}
  for pair,v in ec.items():
   p=tuple(sorted(mapping[('net',n)][1] for n in pair));mc[p]=mc.get(p,Decimal(0))+v
  keys=set(mc)|set(fc);errors=[(k,mc.get(k,Decimal(0))-fc.get(k,Decimal(0))) for k in keys];worst=sorted(errors,key=lambda kv:abs(kv[1]),reverse=True)
  # Native exports round each C record to1e-5fF. Use a conservative1e-3fF
  # branch bound for summed child/parent rounding; report actual error.
  tolerance=Decimal('1e-18');r.update(expanded_branches=len(ec),independent_flat_branches=len(fc),max_branch_error_f= float(abs(worst[0][1])),rounding_tolerance_f=float(tolerance),branches_exceeding_tolerance=sum(abs(v)>tolerance for k,v in errors),cap_matrix_matches_within_export_rounding=all(abs(v)<=tolerance for k,v in errors),worst20=[{'pair':k,'difference_f':str(v)} for k,v in worst[:20]])
 p=B/'results/gf180_hierarchical_cap_expansion_independent_flat_comparison_v1.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
