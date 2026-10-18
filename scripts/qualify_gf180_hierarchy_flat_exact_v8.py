"""Flatten a qualified native hierarchy and independently LVS-check capacitor export."""
from pathlib import Path
import argparse,json,re,hashlib,subprocess
from gf180_compact_lvs_v2 import compact
import probe_gf180_mos_gate_cap as f
# Source/GDS full DRC passed; avoid redundant flat DRC over spaced grid.
# Full128 first native flat extraction bound360s: two times measured144s full64 source export plus25percent margin;2CPU/2GB. Exact graph uses same120s bound and deterministic full-edge proof.
def bounded(args,stdin=None):
 cmd=["docker","run","--rm","--network","none","--memory","2g","--cpus","2"]+(["-i"] if stdin is not None else [])+["--volume",f"{f.ROOT}:/workspace","--workdir","/workspace/"+f.OUT.relative_to(f.ROOT).as_posix(),"--entrypoint","timeout","eventspikeseg:analog-gf180-layout","180",*args]
 p=subprocess.run(cmd,input=stdin,capture_output=True,text=True,timeout=375)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-3000:])
 return p.stdout+p.stderr
f.run=bounded
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);a=ap.parse_args();cell=a.cell;assert cell=='gf180_adaptation_sum128_threshold_v2';d=f.BASE/'layout'/cell;qpath=d/'qualification.json';q=json.loads(qpath.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];files={Path(__file__),qpath};geo={}
 for key in ['sha256','input_sha256']:
  for n,h in q.get(key,{}).items():
   p=d/n if key=='sha256' else R/n
   if p.suffix!='.ext':assert sha(p)==h,n
   files.add(p)
   if p.suffix=='.mag':geo.setdefault(p.stem,set()).add(p)
 views=[];seen=set()
 def visit(n):
  if n in seen:return
  assert len(geo[n])==1;p=next(iter(geo[n]))
  for c in re.findall(r'^use\s+(\S+)\s+',p.read_text(),re.M):visit(c)
  seen.add(n);views.append(p)
 visit(cell);flat=cell+'_flat';assert not (d/'flat_cap_qualification.json').exists();f.OUT=d
 preload=''.join('load /workspace/'+p.with_suffix('').relative_to(R).as_posix()+'\n' for p in views)
 tcl='drc off\n'+preload+f'load {cell}\nflatten {flat}\nload {flat}\nselect top cell\nextract do capacitance\nextract all\nfeedback save flat.feedback\next2spice lvs\next2spice scale off\next2spice -o {flat}.spice\next2spice cthresh 0\next2spice -o {flat}_cap.spice\nquit -noprompt\n'
 tp=d/'flat_extract_v8.tcl';lp=d/'flat_extract_v8.log'
 if tp.exists():
  assert tp.read_text()==tcl;log=lp.read_text()
 else:
  tp.write_text(tcl);log=f.magic(tcl);lp.write_text(log);assert not (d/'flat.feedback').read_text()
 for source,top,label in [(d/(flat+'.spice'),flat,'exact_source'),(d/'reference.spice','reference','exact_reference')]:
  txt,_=compact(source.read_text(),top);txt=txt.replace('.subckt '+top+' ','.subckt '+flat+' ',1);p=d/(label+'.spice');assert not p.exists() or p.read_text()==txt;
  if not p.exists():p.write_text(txt)
  files.add(p)
 gp=d/'flat_exact_graph_unique_net.json';np=d/'flat_exact_graph_unique_net.log';cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:torch2.2.2-cuda11.8','120','python','scripts/compare_gf180_exact_unique_net_bijection_v1.py','--source',(d/'exact_source.spice').relative_to(R).as_posix(),'--other',(d/'exact_reference.spice').relative_to(R).as_posix(),'--report',gp.relative_to(R).as_posix()];run=subprocess.run(cmd,capture_output=True,text=True,timeout=135);np.write_text(run.stdout+run.stderr);assert run.returncode==0 and json.loads(gp.read_text())['all_subcircuits_compositionally_equivalent'],np.read_text()[-2000:];files.update([gp,R/'scripts/compare_gf180_exact_unique_net_bijection_v1.py',R/'scripts/gf180_compact_lvs_v2.py'])
 device_lines=lambda p:[l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X')]
 assert device_lines(d/(flat+'.spice'))==device_lines(d/(flat+'_cap.spice')),'Cap export altered native device topology'
 cs=branches_units(d/(flat+'_cap.spice'),flat);neg={str(k):v for k,v in cs.items() if v< -1e-20};assert not neg
 files.update([tp,lp,np,d/'flat.feedback',d/'reference.spice',d/(flat+'.spice'),d/(flat+'_cap.spice')]);r=dict(cell=cell,flat_subcircuit=flat,flat_extraction_completed=True,flat_lvs_unique=True,native_flat_netgen_pass=None,lvs_basis="Exact unique-net proposed complete fixed-port primitive graph including native dimensions and every edge; native flat Netgen not run.",full_flat_drc_count=None,source_full_drc_count=0,gds_roundtrip_full_drc_count=0,flat_drc_scope='Redundant fresh flat DRC not run following full64 method review; source hierarchy and independently reimported GDS fullDRC both0. Native flat extraction and exact primitive connectivity separately checked.',linear_branch_count=len(cs),negative_aggregate_branches=neg,scope='Actual fully flattened painted geometry; source/GDS fullDRC0, fresh flat DRC incomplete, exact primitive-graph equivalence of device export and token-identical device records in capacitor export against separately qualified reference. All aggregate routing C signs checked and every branch retained; no RPEX/noise/population/full-chip claim.',sha256={p.relative_to(R).as_posix():sha(p) for p in files});(d/'flat_cap_qualification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'flat_branches':len(cs),'exact_graph':True,'native_flat_Netgen_run':False}))
if __name__=='__main__':main()
