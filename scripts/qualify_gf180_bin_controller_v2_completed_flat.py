"""Qualify already completed controller flat extraction against its native reference."""
from pathlib import Path
import json,re,hashlib
import probe_gf180_mos_gate_cap as f
from extract_gf180_flat_compact_reference_cache_aware import branches
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bin_commit_controller_v2';flat=cell+'_flat';d=f.BASE/'layout'/cell;f.OUT=d;rp=d/'flat_cap_qualification.json';assert not rp.exists();log=d/'flat_cap_extraction.log';assert re.search(r'Total DRC errors found:\s*0\b',log.read_text());dest=d/(flat+'_cap.spice');cs=branches(dest,flat);neg={str(k):v for k,v in cs.items() if v< -1e-20};assert not neg;setup='/workspace/'+f.PDK.relative_to(ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=f.run(['netgen-lvs','-batch','lvs',flat+'.spice '+flat,'reference.spice reference',setup,'flat_lvs_native_reference.out']);lp=d/'flat_lvs_native_reference.log';lp.write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-1500:];files={Path(__file__),d/'qualification.json',log,dest,d/(flat+'.spice'),d/'reference.spice',d/'flat_extraction.feedback',lp};q=json.loads((d/'qualification.json').read_text())
 for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
  for n,h in q.get(key,{}).items():
   p=d/n if key=='sha256' else ROOT/n
   if p.suffix!='.ext':assert sha(p)==h,n
   files.add(p)
 r={'flat_extraction_completed':True,'cell':cell,'flat_subcircuit':flat,'full_flat_drc_count':0,'flat_lvs_unique':True,'lvs_basis':'Actual completed flat extraction against frozen native hierarchical reference; original helper failure was a missing compact-reference filename, not a failed connectivity comparison. No physical extraction repeated.','linear_branch_count':len(cs),'negative_aggregate_branches':neg,'scope':'Native controller flat capacitance, full DRC0, unique native-reference Netgen LVS, all routing branches retained and nonnegative aggregate checked. Source/GDS separately qualified. No connected analog/model/5ms/full-chip acceptance.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),'branches':len(cs)}))
if __name__=='__main__':main()
