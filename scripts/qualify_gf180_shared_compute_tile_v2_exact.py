"""Qualify shared tile using exact primitive graphs where hierarchical Netgen fails."""
from pathlib import Path
import json,re,hashlib,subprocess,collections
import probe_gf180_mos_gate_cap as f
from gf180_compact_lvs_v2 import compact
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_shared_analog_compute_tile_v2';d=f.BASE/'layout'/cell;assert not (d/'qualification.json').exists();files={Path(__file__),R/'scripts/gf180_compact_lvs_v2.py',R/'scripts/compare_gf180_exact_hierarchy_graph.py'};geo={};changes=[]
 def include(p):
  files.add(p)
  if p.suffix=='.mag':geo.setdefault(p.stem,set()).add(p)
 include(d/(cell+'.mag'))
 for n in re.findall(r'^use\s+(\S+)\s+', (d/(cell+'.mag')).read_text(),re.M):
  cd=f.BASE/'layout'/n;qp=cd/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'];include(qp)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for name,h in q.get(key,{}).items():
    p=cd/name if key=='sha256' else R/name
    if sha(p)!=h:assert p.suffix=='.ext',p;changes.append(p.relative_to(R).as_posix())
    include(p)
 visited=set();views=[]
 def visit(n):
  if n in visited:return
  assert len(geo[n])==1;p=next(iter(geo[n]))
  for child in re.findall(r'^use\s+(\S+)\s+',p.read_text(),re.M):visit(child)
  visited.add(n);views.append(p)
 visit(cell);preload=''.join('load /workspace/'+p.with_suffix('').relative_to(R).as_posix()+'\n' for p in views);log=(d/'extraction.log').read_text();assert re.search(r'Total DRC errors found:\s*0\b',log) and not (d/'warnings.feedback').read_text();proof=d/'compact_exact_graph_diagnosis.json';assert json.loads(proof.read_text())['all_subcircuits_compositionally_equivalent'];files.add(proof)
 ref=d/'compact_reference_named.spice';assert ref.exists();files.add(ref)
 def prove(src,top,label,folder):
  txt,stats=compact(src.read_text(),top);txt=txt.replace('.subckt '+top+' ','.subckt '+cell+' ',1);cp=folder/(label+'_primitive_comparison.spice');assert not cp.exists();cp.write_text(txt);gp=folder/(label+'_exact_graph.json');lp=folder/(label+'_exact_graph.log')
  args=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:torch2.2.2-cuda11.8','120','python','scripts/compare_gf180_exact_hierarchy_graph.py','--source',cp.relative_to(R).as_posix(),'--other',ref.relative_to(R).as_posix(),'--report',gp.relative_to(R).as_posix()]
  p=subprocess.run(args,capture_output=True,text=True,timeout=135);lp.write_text(p.stdout+p.stderr);assert p.returncode==0 and json.loads(gp.read_text())['all_subcircuits_compositionally_equivalent'],lp.read_text()[-1500:];files.update([src,cp,gp,lp]);return stats
 flat=cell+'_flat';f.OUT=d;dest=d/(flat+'_cap.spice');assert not dest.exists();tcl=preload+f'load {cell}\nflatten {flat}\nload {flat}\nselect top cell\ndrc on\ndrc style drc(full)\ndrc check\ndrc catchup\ndrc count total\nextract do capacitance\nextract all\nfeedback save flat.feedback\next2spice lvs\next2spice scale off\next2spice -o {flat}.spice\next2spice cthresh 0\next2spice -o {flat}_cap.spice\nquit -noprompt\n';tp=d/'flat_extract.tcl';tp.write_text(tcl);fl=f.magic(tcl);lp=d/'flat_extract.log';lp.write_text(fl);assert re.search(r'Total DRC errors found:\s*0\b',fl) and not (d/'flat.feedback').read_text();files.update([tp,lp,d/'flat.feedback',dest])
 stats=prove(d/(flat+'.spice'),flat,'flat',d);device_lines=lambda p:[l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X')];assert device_lines(d/(flat+'.spice'))==device_lines(dest);cs=branches_units(dest,flat);neg={str(k):v for k,v in cs.items() if v< -1e-20};assert not neg
 rd=f.BASE/'verification/gds_roundtrip'/cell;assert not rd.exists();rd.mkdir(parents=True);f.OUT=rd;gl=f.magic('gds read /workspace/'+(d/(cell+'.gds')).relative_to(R).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');gp=rd/'readback.log';gp.write_text(gl);assert re.search(r'Total DRC errors found:\s*0\b',gl) and not (rd/'roundtrip.feedback').read_text();gstats=prove(rd/'roundtrip.spice',cell,'gds',rd);files.update([gp,rd/'roundtrip.feedback']);assert stats['primitive_devices']==gstats['primitive_devices']==593
 original=[d/(cell+x) for x in ['.mag','.gds','.spice']]+[d/n for n in ['build_source.py','reference.spice','netgen.log','extraction.log','warnings.feedback','gds_warnings.feedback','compact_netgen.log','compact_lvs.out','compact_exact_graph_diagnosis.log']];files.update(original)
 qp=d/'qualification.json';scope='Actual413MOS8R172MIM joined shared64state analog compute/read/staged-writeback tile. Fresh source and GDS reimport full DRC0. Native hierarchical and compact Netgen failures retained; exact primitive graph bijections against independent qualified-child reference prove source,geometrically flat and GDS device connectivity with fixed named ports,exact W/L and passive dimensions,every graph edge. No fake native-Netgen pass. Flat C retains every nonnegative branch. Native init/read/voltage shift/compute/output hold/row commit are physically connected; native closed-loop cycle still to simulate. Known beta/injection/hold/reset errors preserved. External scheduler,current/analog references and programming remain; full adaptation/RMS/inhibition,learned mapping,PVT,model precision,5ms service,dense placement and fullchip remain unfinished. Spaced characterization fixture is not dense area.'
 q=dict(cell=cell,ports=stats['port_order'],bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],mos_count=413,native_resistor_count=8,native_mim_count=172,magic_drc_count=0,gds_roundtrip_drc_count=0,lvs_unique=True,gds_roundtrip_lvs_unique=True,native_netgen_lvs_pass=False,lvs_basis='Exact complete primitive-device graph bijection, fixed named interfaces, native model dimensions; source/flat/GDS vs independent reference. Native Netgen failures retained.',actual_source_ports_verified=True,actual_gds_ports_verified=True,extraction_feedback='',drc_style='drc(full)',scope=scope,generated_cache_changes=changes,complete_PLIF_accepted=False,original_float_accuracy_accepted=False,full_chip_accepted=False,sha256={p.name:sha(p) for p in original},input_sha256={p.relative_to(R).as_posix():sha(p) for p in files if p not in original},gds_roundtrip_sha256={p.relative_to(R).as_posix():sha(p) for p in files if p.parent==rd});qp.write_text(json.dumps(q,indent=2)+'\n');files.add(qp)
 fq=dict(cell=cell,flat_subcircuit=flat,flat_extraction_completed=True,full_flat_drc_count=0,flat_lvs_unique=True,native_netgen_lvs_pass=False,lvs_basis=q['lvs_basis'],linear_branch_count=len(cs),negative_aggregate_branches=neg,scope=scope,sha256={p.relative_to(R).as_posix():sha(p) for p in files});(d/'flat_cap_qualification.json').write_text(json.dumps(fq,indent=2)+'\n');print(json.dumps({'source_flat_GDS_full_DRC':0,'exact_source_flat_GDS_graphs':True,'native_Netgen_pass':False,'native_MOS':413,'native_MIM':172,'native_R':8,'flat_C_branches':len(cs)}))
if __name__=='__main__':main()
