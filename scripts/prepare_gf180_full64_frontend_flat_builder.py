"""Prepare one full-cap extraction with measured full64 runtime and exact v2 graph proof."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'scripts/extract_gf180_scheduled_writer_flat_exact_graph.py'
q=R/'scripts/extract_gf180_full64_frontend_flat_exact_graph_v1.py'
assert not q.exists()
s=p.read_text().replace('gf180_scheduled_rms_resident_write_v1','gf180_full64_rms_frontend_v1')
s=s.replace('compare_gf180_exact_hierarchy_graph.py','compare_gf180_exact_hierarchy_graph_v2.py')
s=s.replace("def main():\n",'''def measured_runtime_magic(args,stdin=None):
 assert args[0]=='magic'
 # Previous actual2304MOS full64 flat extraction completed in approximately22minutes.
 # This2397MOS parent adds the already qualified93MOS frontend; one1800s native bound.
 cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','-i','--volume',f'{ROOT}:/workspace','--workdir','/workspace/'+f.OUT.relative_to(ROOT).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','1800',*args]
 p=subprocess.run(cmd,input=stdin,capture_output=True,text=True,timeout=1815)
 log=p.stdout+p.stderr
 (f.OUT/'flat_native_runtime_observation.log').write_text(log)
 assert p.returncode==0,(p.returncode,log[-2500:])
 return log

def main():
 f.run=measured_runtime_magic
''',1)
s=s.replace("'scope':'Single full flat", "'runtime_basis':'Previous actual2304MOS full64 flat extraction completed in approximately22minutes; this2397MOS parent adds93MOS frontend. One1800s native bound, same2CPU/2GB, single extraction, no geometry/solver sweep.','scope':'Single full flat")
q.write_text(s);print(q)
