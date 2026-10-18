"""Recover an existing flat extraction via exact primitive graphs; retain failed native LVS."""
from pathlib import Path
import argparse,json,hashlib,re,subprocess
import probe_gf180_mos_gate_cap as f
from gf180_compact_lvs_v2 import compact
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);a=ap.parse_args();c=a.cell;d=f.BASE/'layout'/c;flat=c+'_flat';qpath=d/'qualification.json';q=json.loads(qpath.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];assert not (d/'flat_cap_qualification.json').exists();files={qpath,Path(__file__),R/'scripts/compare_gf180_exact_hierarchy_graph.py',R/'scripts/gf180_compact_lvs_v2.py'}
 for key in ['sha256','input_sha256']:
  for n,h in q.get(key,{}).items():
   p=d/n if key=='sha256' else R/n
   if p.suffix!='.ext':assert sha(p)==h,p
   files.add(p)
 log=d/'flat_extract.log';assert re.search(r'Total DRC errors found:\s*0\b',log.read_text()) and not (d/'flat.feedback').read_text();src=d/(flat+'.spice');cap=d/(flat+'_cap.spice');ref=d/'reference.spice'
 for p,top,name in [(src,flat,'flat_exact_source'),(ref,'reference','flat_exact_reference')]:
  txt,stats=compact(p.read_text(),top);txt=txt.replace('.subckt '+top+' ','.subckt '+flat+' ',1);dest=d/(name+'.spice');assert not dest.exists();dest.write_text(txt);files.update([p,dest])
 gp=d/'flat_exact_graph_recovery.json';lp=d/'flat_exact_graph_recovery.log';cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:torch2.2.2-cuda11.8','120','python','scripts/compare_gf180_exact_hierarchy_graph.py','--source',(d/'flat_exact_source.spice').relative_to(R).as_posix(),'--other',(d/'flat_exact_reference.spice').relative_to(R).as_posix(),'--report',gp.relative_to(R).as_posix()];p=subprocess.run(cmd,capture_output=True,text=True,timeout=135);lp.write_text(p.stdout+p.stderr);assert p.returncode==0 and json.loads(gp.read_text())['all_subcircuits_compositionally_equivalent'],lp.read_text()[-2000:]
 x=lambda p:[l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X')];assert x(src)==x(cap);cs=branches_units(cap,flat);assert not any(v<0 for v in cs.values());files.update([gp,lp,log,d/'flat_extract.tcl',d/'flat.feedback',d/'flat_lvs_v2.log',d/'flat_lvs_v2.out',cap]);out=dict(cell=c,flat_subcircuit=flat,flat_extraction_completed=True,flat_lvs_unique=True,native_flat_netgen_pass=False,lvs_basis='Exact complete primitive graph bijection against independent qualified-child reference,all ports/W/L/passive dimensions/every edge; failed flat native Netgen retained. Source/GDS native Netgen passed separately.',full_flat_drc_count=0,linear_branch_count=len(cs),negative_aggregate_branches={},scope='Existing geometrically flat painted extraction recovered without re-extraction. Native flat Netgen fails on symmetric repeated hierarchy; no false passing claim. Exact fixed-port primitive graph proves equivalence; all native capacitor-export device tokens identical. Complete substrate export still required with hierarchy off/top on before native simulation.',sha256={p.relative_to(R).as_posix():sha(p) for p in files});(d/'flat_cap_qualification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'flat_exact_graph':True,'native_flat_netgen':False,'branches':len(cs)}))
if __name__=='__main__':main()
