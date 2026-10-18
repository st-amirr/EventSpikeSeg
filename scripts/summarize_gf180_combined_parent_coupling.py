"""Audit combined-parent extracted linear capacitance after hierarchical corrections."""
from pathlib import Path
import json,re,hashlib,collections
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def branches(p,root):
 text=re.sub(r'\n\+\s*',' ',p.read_text());subs={}
 for m in re.finditer(r'(?ims)^\.subckt\s+(\S+)\s+([^\n]+)\n(.*?)^\.ends[^\n]*',text):subs[m[1]]=(m[2].split(),m[3].splitlines())
 cs=collections.defaultdict(float)
 def visit(name,ports,path):
  labels,body=subs[name];assert len(labels)==len(ports);alias=dict(zip(labels,ports));node=lambda n:alias.get(n,n if n in ['0','VSUBS'] else path+'/'+n)
  for line in body:
   t=line.split()
   if not t:continue
   if t[0][0]=='C':
    value=float(t[3][:-1])*1e-15 if t[3].lower().endswith('f') else float(t[3]);cs[tuple(sorted([node(t[1]),node(t[2])]))]+=value
   if t[0][0]=='X':
    found=[i for i,v in enumerate(t) if v in subs]
    if found:
     i=found[0];visit(t[i],[node(n) for n in t[1:i]],path+'/'+t[0])
 visit(root,subs[root][0],root);return cs

def main():
 files={Path(__file__)};rows=[]
 for cell in ['gf180_loaded_state_threshold_parent_v2','gf180_loaded_state_threshold_shielded_v4']:
  d=BASE/'layout'/cell;qpath=d/'qualification.json';q=json.loads(qpath.read_text());files.add(qpath);assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    p=d/n if key=='sha256' else ROOT/n;assert sha(p)==h,n;files.add(p)
  cs=branches(d/(cell+'_cap.spice'),cell);neg={str(k):v for k,v in cs.items() if v< -1e-20};assert not neg,neg
  c=lambda a,b:cs.get(tuple(sorted([a,b])),0)
  rows.append({'cell':cell,'linear_branch_count':len(cs),'minimum_aggregated_branch_f':min(cs.values()),'negative_individual_hierarchical_corrections_are_not_negative_total_branches':True,'sense_out_to_sense_ref_f':c('SENSE_OUT','SENSE_REF'),'state_to_sense_out_f':c('STATE','SENSE_OUT'),'state_to_sense_ref_f':c('STATE','SENSE_REF'),'state_to_vss_f':c('STATE','VSS')})
 out=BASE/'results/gf180_combined_parent_coupling_boundary.json';assert not out.exists();r={'audit_completed':True,'cases':rows,'scope':'Same resized state/detector child geometry and STATE path; grounded parent escape/port guards added in v4. Full qualified hierarchy linear layout capacitors aggregated by actual node aliases, with negative hierarchical correction terms included. Every total linear branch nonnegative; native MOS/MIM nonlinear intrinsic capacitance is outside this linear audit. Coupling comparison does not qualify reference retention/trip accuracy, stability, beta/reset, sampled noise, full physical PLIF or population/chip acceptance.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}};out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(out),'cases':rows},indent=2))
if __name__=='__main__':main()
