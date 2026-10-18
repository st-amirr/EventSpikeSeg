"""Single-pass flat capacitance extraction with exact primitive connectivity graph proof."""
from pathlib import Path
import json,re,hashlib,subprocess
import probe_gf180_mos_gate_cap as f
from resume_gf180_formatted64_completed_flat_v2 import branches_units as branches
from gf180_compact_lvs_v2 import compact
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def measured_runtime_magic(args,stdin=None):
 assert args[0]=='magic'
 # Previous actual2304MOS full64 flat extraction completed in approximately22minutes.
 # This2397MOS parent adds the already qualified93MOS frontend; one1800s native bound.
 cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','-i','--volume',f'{ROOT}:/workspace','--workdir','/workspace/'+f.OUT.relative_to(ROOT).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','120',*args]
 p=subprocess.run(cmd,input=stdin,capture_output=True,text=True,timeout=135)
 log=p.stdout+p.stderr
 (f.OUT/'flat_native_extraction_only_runtime.log').write_text(log)
 assert p.returncode==0,(p.returncode,log[-2500:])
 return log

def main():
 f.run=measured_runtime_magic
 cell='gf180_full64_rms_frontend_v1';flat=cell+'_flat';d=f.BASE/'layout'/cell;f.OUT=d;qp=d/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'];files={Path(__file__),qp,ROOT/'artifacts/analog_asic/results/gf180_full64_frontend_flat_runtime_stage_review_v1.json',d/'flat_native_runtime_observation.log',d/'flat_single_pass.tcl',d/'flat_initial_timeout_partial.ext',ROOT/'scripts/gf180_compact_lvs_v2.py',ROOT/'scripts/resume_gf180_formatted64_completed_flat_v2.py',ROOT/'scripts/compare_gf180_exact_hierarchy_graph_v2.py'};geometry={};changes=[]
 for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
  for n,h in q.get(key,{}).items():
   p=d/n if key=='sha256' else ROOT/n
   if sha(p)!=h:assert p.suffix=='.ext';changes.append(str(p.relative_to(ROOT)))
   files.add(p)
   if p.suffix=='.mag':geometry.setdefault(p.stem,set()).add(p)
 seen=set();views=[]
 def visit(name):
  if name in seen:return
  assert len(geometry[name])==1;p=next(iter(geometry[name]))
  for child in re.findall(r'^use\s+(\S+)\s+',p.read_text(),re.M):visit(child)
  seen.add(name);views.append(p)
 visit(cell);dest=d/(flat+'_cap.spice');assert not dest.exists();preload=''.join('load /workspace/'+p.with_suffix('').relative_to(ROOT).as_posix()+'\n' for p in views);tcl=preload+f'load {cell}\nflatten {flat}\nload {flat}\nselect top cell\ndrc off\nextract do capacitance\nextract all\nfeedback save flat_extraction.feedback\next2spice lvs\next2spice scale off\next2spice -o {flat}.spice\next2spice cthresh 0\next2spice -o {flat}_cap.spice\nquit -noprompt\n';tp=d/'flat_extraction_only_reuse_DRC.tcl';tp.write_text(tcl);log=f.magic(tcl);lp=d/'flat_cap_extraction_only_reuse_DRC.log';lp.write_text(log);assert re.search(r'Total DRC errors found:\s*0\b',(d/'flat_native_runtime_observation.log').read_text());cs=branches(dest,flat);neg={str(k):v for k,v in cs.items() if v< -1e-20};assert not neg,neg
 text,_=compact((d/(flat+'.spice')).read_text(),flat);copy=d/'flat_exact_graph_comparison.spice';copy.write_text(text.replace('.subckt '+flat+' ','.subckt '+cell+' ',1));gp=d/'flat_exact_graph_qualification.json';cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:torch2.2.2-cpu-verification-guarded','120','python','scripts/compare_gf180_exact_hierarchy_graph_v2.py','--source',(d/'source_compact.spice').relative_to(ROOT).as_posix(),'--other',copy.relative_to(ROOT).as_posix(),'--report',gp.relative_to(ROOT).as_posix()];run=subprocess.run(cmd,capture_output=True,text=True,timeout=135);gl=d/'flat_lvs_exact_graph.log';gl.write_text(run.stdout+run.stderr);assert run.returncode==0,(run.returncode,run.stdout[-1000:],run.stderr[-1000:]);assert json.loads(gp.read_text())['all_subcircuits_compositionally_equivalent'];files.update([tp,lp,dest,d/(flat+'.spice'),d/'flat_extraction.feedback',copy,gp,gl]);r={'flat_extraction_completed':True,'generated_cache_changes':changes,'cell':cell,'flat_subcircuit':flat,'full_flat_drc_count':0,'flat_lvs_unique':True,'lvs_basis':'Exact primitive graph comparison against compositionally qualified native source hierarchy; exact native transistor W/L, passive dimensions, port identity and every connection. Original reference independently checked through exact hierarchy bijection. Native Netgen failure is retained, not claimed passing.','linear_branch_count':len(cs),'negative_aggregate_branches':neg,'runtime_basis':'Original1800s native pass completed full flat DRC0 then was cut during EXT device output. Preserve truncated file. One120s extraction-only recovery on the exact same hash-checked source geometry; completed native flat DRC result is reused explicitly, not rerun or fabricated.','flat_DRC_reused_from_completed_original_pass':True,'scope':'Extraction-only recovery with completed original full flat DRC0 reused for identical source geometry. Full flat capacitance extraction, all routing branches retained and nonnegative aggregate checked; separate exact flat-device graph equivalence vs independently qualified source. Native source/GDS full DRC and connectivity qualified separately. No RPEX, noise, model/service/full-chip acceptance.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}};rp=d/'flat_cap_qualification.json';assert not rp.exists();rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),'branches':len(cs)}))
if __name__=='__main__':main()
