"""Qualify source/GDS full formatter by exact compositional connectivity proofs."""
from pathlib import Path
import json,re,hashlib
import probe_gf180_mos_gate_cap as f
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_formatted_energy64_v3';d=f.BASE/'layout'/cell;rd=f.BASE/'verification/gds_roundtrip'/cell;qp=d/'qualification.json';assert not qp.exists();proof=f.BASE/'results/gf180_formatted_energy64_v3_exact_hierarchy_connectivity.json';gp=f.BASE/'results/gf180_formatted64_source_GDS_exact_graph.json';assert json.loads(proof.read_text())['exact_parent_connectivity_pass'];assert json.loads(gp.read_text())['all_subcircuits_compositionally_equivalent'];files={Path(__file__),proof,gp,ROOT/'scripts/compare_gf180_exact_hierarchy_graph.py',ROOT/'scripts/screen_gf180_formatted64_exact_hierarchy_dc.py'};geometry={}
 for name in ['gf180_product_gate_formatter_v3','gf180_energy_mean_root64_v1']:
  folder=f.BASE/'layout'/name;cp=folder/'qualification.json';q=json.loads(cp.read_text());files.add(cp)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    p=folder/n if key=='sha256' else ROOT/n
    if p.suffix!='.ext':assert sha(p)==h,n
    files.add(p)
    if p.suffix=='.mag':geometry.setdefault(p.stem,set()).add(p)
 for p in [d/'first_pass_recovered.log',rd/'recovered_readback.log']:
  log=p.read_text();assert re.search(r'Total DRC errors found:\s*0\b',log);files.add(p)
 for p in [d/'warnings.feedback',d/'gds_warnings.feedback',rd/'roundtrip.feedback']:assert not p.read_text();files.add(p)
 visited=set();views=[]
 def visit(name):
  if name in visited:return
  assert len(geometry[name])==1;v=next(iter(geometry[name]))
  for child in re.findall(r'^use\s+(\S+)\s+',v.read_text(),re.M):visit(child)
  visited.add(name);views.append(v)
 for name in ['gf180_product_gate_formatter_v3','gf180_energy_mean_root64_v1']:visit(name)
 f.OUT=d;preload=''.join('load /workspace/'+p.with_suffix('').relative_to(ROOT).as_posix()+'\n' for p in views);log=f.magic(preload+f'load {cell}\nextract do capacitance\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');lp=d/'capacitance_export_existing_ext.log';lp.write_text(log);outputs=[d/(cell+s) for s in ['.mag','.spice','_cap.spice','.gds']]+[lp,d/'build_source.py',d/'reference.spice',d/'reference_compact.spice',d/'source_compact.spice',d/'first_pass_extraction_snapshot.txt'];ports=re.search(r'(?m)^\.subckt '+cell+r' ([^\n]+)',(d/(cell+'.spice')).read_text().replace('\n+',' '))[1].split();gports=re.search(r'(?m)^\.subckt '+cell+r' ([^\n]+)',(rd/'roundtrip.spice').read_text().replace('\n+',' '))[1].split();assert set(ports)==set(gports)
 q={'cell':cell,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'lvs_method':'Deterministic exact source-reference parent net bijection with identical independently qualified child definitions; exact graph isomorphism at every GDS/source subcircuit. Full flattened Netgen attempt failed symmetry resolution and is explicitly not treated as passing.','full_flat_netgen_pass':False,'actual_source_ports_verified':True,'actual_gds_ports_verified':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',(d/'first_pass_recovered.log').read_text())[1].split()],'mos_count':2304,'native_resistor_count':2816,'native_mim_count':1024,'channel_count':64,'scope':'Actual64 native candidate-minus-penalty formatters,64 quadratic kernels and64 mean/root receivers; source full DRC0/GDS readback DRC0, source connectivity exact compositionally proven vs independent qualified-child reference, every source/GDS subcircuit graph exactly equivalent. All original failed Netgen logs retained; native device dimensions and connectivity not relaxed. Existing completed first-pass EXT supplies hierarchical capacitance export without repeating extraction. Separate flat RC/device graph qualification and transient required. Spacious characterization footprint is not dense population area. No calibrated RMS, epsilon, model accuracy,5ms/full-chip acceptance.','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files},'gds_roundtrip_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [rd/'roundtrip.spice',rd/'roundtrip.feedback',rd/'recovered_readback.log']}};qp.write_text(json.dumps(q,indent=2)+'\n');print(qp)
if __name__=='__main__':main()
