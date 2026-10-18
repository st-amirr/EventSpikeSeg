"""Resume qualification after the original flat Magic process completes; never re-extract."""
from pathlib import Path
import json,hashlib,re,collections
import probe_gf180_mos_gate_cap as f
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def branches_units(path,root):
 cs=collections.defaultdict(float)
 for line in path.read_text().splitlines():
  t=line.split()
  if t and t[0].startswith('C'):
   m=re.fullmatch(r'([0-9.eE+\-]+)([fpunm]?)',t[3]);assert m,t
   cs[tuple(sorted(t[1:3]))]+=float(m[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3}[m[2]]
 return cs

def main():
 cell='gf180_formatted_energy64_v3';d=f.BASE/'layout'/cell;log=d/'flat_recovered_extraction.log';raw=log.read_text();assert re.search(r'Total DRC errors found:\s*0\b',raw);assert raw.count('exttospice finished.')>=2;assert (d/(cell+'_flat_cap.spice')).stat().st_size>10000;assert not (d/'flat_cap_qualification.json').exists();builder=ROOT/'scripts/extract_gf180_formatted64_flat_exact_graph.py';source=builder.read_text().replace('assert not dest.exists()','assert dest.exists()',1);ep=d/'flat_qualification_recovery_execution_v2.py';assert not ep.exists();ep.write_text(source);oldmagic=f.magic;wt=Path.write_text;protected={d/'flat_single_pass.tcl'};calls=[0]
 def magic(script):calls[0]+=1;assert calls[0]==1;assert script==(d/'flat_single_pass.tcl').read_text();return raw
 def write(p,text,*a,**kw):
  if p in protected:assert p.read_text()==text;return len(text)
  if p==d/'flat_cap_qualification.json':
   r=json.loads(text);r['original_flat_process_recovery']={'container':'7f79ed9c3247','host_observation_timeout_seconds':120,'same_native_process_completed_without_restart':True,'parser_fix':'Accept native nanofarad/unit suffixes for large full-width routing capacitance; numeric values and every branch retained unchanged'};r['sha256'].update({x.relative_to(ROOT).as_posix():sha(x) for x in [Path(__file__),ep,log]});text=json.dumps(r,indent=2)+'\n'
  return wt(p,text,*a,**kw)
 f.magic=magic;Path.write_text=write
 try:ns={'__file__':str(builder),'__name__':'completed_process_recovery'};exec(compile(source,str(ep),'exec'),ns);ns['branches']=branches_units;ns['main']();assert calls[0]==1
 finally:f.magic=oldmagic;Path.write_text=wt
if __name__=='__main__':main()
