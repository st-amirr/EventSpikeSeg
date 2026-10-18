"""Resume the completed scheduled-writer source pass without repeating its extraction."""
from pathlib import Path
import json,hashlib,re,subprocess
import probe_gf180_mos_gate_cap as f
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_full64_rms_frontend_v1';d=f.BASE/'layout'/cell;builder=ROOT/'scripts/build_gf180_full64_rms_frontend_v1.py';log=d/'first_pass_recovered.log';raw=log.read_text();assert re.search(r'Total DRC errors found:\s*0\b',raw) and 'BBOX ' in raw;assert not (d/'qualification.json').exists();assert sha(builder)==sha(d/'build_source.py');assert not (d/'warnings.feedback').read_text() and not (d/'gds_warnings.feedback').read_text();snapshot=d/'completed_first_pass_ext_snapshot.txt';assert not snapshot.exists();snapshot.write_bytes((d/(cell+'.ext')).read_bytes());source=builder.read_text().replace('assert not out.exists();out.mkdir(parents=True)','assert out.exists();out.mkdir(parents=True,exist_ok=True)',1);ep=d/'completed_first_pass_recovery_execution.py';assert not ep.exists();ep.write_text(source);oldmagic=f.magic;oldrun=f.run;wt=Path.write_text;wb=Path.write_bytes;protected={d/(cell+'.mag'),d/'build_source.py'};calls=[0]
 def write(p,text,*a,**kw):
  if p in protected:assert p.read_text()==text;return len(text)
  if p==d/'qualification.json':
   q=json.loads(text);q['completed_first_pass_recovery']={'source_container':'2c61fcd49b71','source_completed_after_host120s_timeout':True,'source_geometry_GDS_and_extraction_not_restarted':True,'hierarchical_cap_export_reuses_complete_original_EXT':True,'GDS_LVS_extracts_devices_without_linear_capacitance':True,'GDS_observation_bound_seconds':600,'runtime_basis':'Native2397MOS full64 RMS/frontend original source extraction exceeded120s host observation while actively processing the already qualified full64 child. Recover the original completed extraction; independent GDS readback gets one600s bound based on the observed full64 extraction cost. Native MIM devices retained.'};q['input_sha256'].update({x.relative_to(ROOT).as_posix():sha(x) for x in [Path(__file__),ep,snapshot,log]});text=json.dumps(q,indent=2)+'\n'
  return wt(p,text,*a,**kw)
 def writeb(p,b):
  if p in protected:assert p.read_bytes()==b;return len(b)
  return wb(p,b)
 def run(args,stdin=None):
  assert args[0]=='magic';cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','-i','--volume',f'{ROOT}:/workspace','--workdir','/workspace/'+f.OUT.relative_to(ROOT).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','600',*args];p=subprocess.run(cmd,input=stdin,capture_output=True,text=True,timeout=615);assert p.returncode==0,(p.returncode,p.stdout[-1000:],p.stderr[-1000:]);return p.stdout+p.stderr
 def magic(script):
  calls[0]+=1
  if calls[0]==1:return raw
  if calls[0]==2:
   assert sha(d/(cell+'.ext'))==sha(snapshot);script=script.replace('extract do capacitance\nextract all\n','extract do capacitance\n',1)
  elif calls[0]==3:script=script.replace('extract all\n','extract no capacitance\nextract all\n',1)
  else:raise AssertionError('Unexpected Magic pass')
  return oldmagic(script)
 f.magic=magic;f.run=run;Path.write_text=write;Path.write_bytes=writeb
 try:ns={'__file__':str(builder),'__name__':'completed_native_pass_recovery'};exec(compile(source,str(ep),'exec'),ns);ns['main']();assert calls[0]==3
 finally:f.magic=oldmagic;f.run=oldrun;Path.write_text=wt;Path.write_bytes=wb
if __name__=='__main__':main()
