"""Finish controller metadata from completed physical passes without repeating extraction."""
from pathlib import Path
import json,re,hashlib,sys
import probe_gf180_mos_gate_cap as f
from gf180_compact_lvs_v2 import compact
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bin_commit_controller_v2';d=f.BASE/'layout'/cell;rd=f.BASE/'verification/gds_roundtrip'/cell;builder=ROOT/'scripts/build_gf180_bin_commit_controller_v2.py';assert not (d/'qualification.json').exists();assert sha(builder)==sha(d/'build_source.py');counts={}
 for name in ['gf180_control_dff_v1','gf180_nonoverlap_phase_pair_v2','gf180_reset_select_and_fullroute','gf180_phase_inverter_fullroute']:
  p=f.BASE/'layout'/name/(name+'.spice');txt,_=compact(p.read_text(),name);counts[name]=sum(1 for line in txt.splitlines() if line.startswith('X') and re.search(r'\b[ np]*fet_03v3\b',line));assert counts[name]>0
 native,_=compact((d/(cell+'.spice')).read_text(),cell);total=sum(1 for line in native.splitlines() if line.startswith('X') and re.search(r'\b[ np]*fet_03v3\b',line));rp=d/'native_device_count_recovery.json';assert rp.exists();prior=json.loads(rp.read_text());assert prior['native_MOS_count']==total;rp= d/'native_device_count_recovery_v2.json';assert not rp.exists();rp.write_text(json.dumps({'native_MOS_count':total,'child_native_MOS_counts':counts,'scope':'Completed source native transistor-instance count, metadata-only recovery after child qualification omitted mos_count; no circuit or physical rerun.'},indent=2)+'\n')
 src=builder.read_text().replace('assert not out.exists();out.mkdir(parents=True)','assert out.exists();out.mkdir(parents=True,exist_ok=True)',1).replace("children[n][1]['mos_count']","native_counts[n]").replace('rd.mkdir(parents=True)','rd.mkdir(parents=True,exist_ok=True)');ep=d/'metadata_recovery_execution_v2.py';assert not ep.exists();ep.write_text(src);oldmagic=f.magic;oldrun=f.run;oldwt=Path.write_text;oldwb=Path.write_bytes;calls=[0];protected={d/(cell+'.mag'),d/'build_source.py'}
 def wt(p,text,*a,**kw):
  if p in protected and p.exists():assert p.read_text()==text;return len(text)
  if p==d/'qualification.json':
   q=json.loads(text);assert q['mos_count']==total;q['input_sha256'].update({x.relative_to(ROOT).as_posix():sha(x) for x in [Path(__file__),ep,rp,ROOT/'scripts/gf180_compact_lvs_v2.py']});q['metadata_recovery']='Completed original source/GDS/native Netgen passes reused, only missing child-count metadata reconstructed from native transistor instances.';text=json.dumps(q,indent=2)+'\n'
  return oldwt(p,text,*a,**kw)
 def wb(p,b):
  if p in protected and p.exists():assert p.read_bytes()==b;return len(b)
  return oldwb(p,b)
 def magic(script):
  calls[0]+=1;p=[d/'extraction.log',d/'capacitance_extraction.log',rd/'readback.log'][calls[0]-1];log=p.read_text()
  if calls[0]!=2:assert re.search(r'Total DRC errors found:\s*0\b',log)
  return log
 def run(args,stdin=None):
  assert args[0]=='netgen-lvs';p=f.OUT/'netgen.log';log=p.read_text();assert 'Circuits match uniquely' in log;return log
 Path.write_text=wt;Path.write_bytes=wb;f.magic=magic;f.run=run
 try:
  ns={'__file__':str(builder),'__name__':'metadata_recovery','native_counts':counts};exec(compile(src,str(ep),'exec'),ns);ns['main']();assert calls[0]==3
 finally:Path.write_text=oldwt;Path.write_bytes=oldwb;f.magic=oldmagic;f.run=oldrun
if __name__=='__main__':main()
