"""Qualify an existing completed flat extraction using an exact factorized graph proof."""
from pathlib import Path
import argparse,json,re,hashlib
import probe_gf180_mos_gate_cap as f
from gf180_compact_lvs_v2 import compact
from resume_gf180_formatted64_completed_flat_v2 import branches_units
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);ap.add_argument('--graph-report',required=True);a=ap.parse_args();cell=a.cell;assert re.fullmatch(r'gf180_[A-Za-z0-9_]+',cell);d=f.BASE/'layout'/cell;flat=cell+'_flat';qp=d/'qualification.json';q=json.loads(qp.read_text());gp=ROOT/a.graph_report;g=json.loads(gp.read_text());assert g['all_subcircuits_compositionally_equivalent'];files={Path(__file__),qp,gp,ROOT/'scripts/gf180_compact_lvs_v2.py',ROOT/'scripts/resume_gf180_formatted64_completed_flat_v2.py'};cache_changes=[]
 for n,h in g['sha256'].items():
  p=ROOT/n[len('/workspace/'):] if n.startswith('/workspace/') else ROOT/n;assert sha(p)==h,n;files.add(p)
 for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
  for n,h in q.get(key,{}).items():
   p=d/n if key=='sha256' else ROOT/n
   if sha(p)!=h:assert p.suffix=='.ext',n;cache_changes.append(str(p.relative_to(ROOT)))
   files.add(p)
 device=d/(flat+'.spice');text,_=compact(device.read_text(),flat);expected=text.replace('.subckt '+flat+' ','.subckt '+cell+' ',1);copy=d/'flat_exact_graph_comparison.spice';assert expected==copy.read_text();source,_=compact((d/(cell+'.spice')).read_text(),cell);assert source==(d/'source_compact.spice').read_text();log=d/'flat_cap_extraction.log';assert re.search(r'Total DRC errors found:\s*0\b',log.read_text());feedback=d/'flat_extraction.feedback';assert not feedback.read_text();cap=d/(flat+'_cap.spice');cs=branches_units(cap,flat);neg={str(k):v for k,v in cs.items() if v< -1e-20};assert not neg,neg;files.update([device,copy,log,feedback,cap,d/'flat_single_pass.tcl']);r={'cell':cell,'flat_subcircuit':flat,'flat_extraction_completed':True,'full_flat_drc_count':0,'flat_lvs_unique':True,'lvs_basis':'Exact source/flat native primitive graph equivalence. Named external ports fixed; component factorization accelerates search, reconstructs full bijection and explicitly checks every original edge. Qualified source is independently equivalent to its original qualified-child reference and GDS readback. Native transistor W/L and passive dimensions exact; no relaxed topology/sizing. Historical failed Netgen or whole-graph timeouts remain preserved, not accepted as passing.','linear_branch_count':len(cs),'negative_aggregate_branches':neg,'generated_cache_changes':cache_changes,'scope':'Previously completed full flat DRC/capacitance extraction reused without restarting geometry or native extraction. Every linear branch retained unchanged, native f/p/n/u/m suffixes parsed numerically; nonnegative aggregate and exact device connectivity checked. No RPEX, noise/PVT, calibrated model accuracy,5ms population service or full-chip acceptance.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}};rp=d/'flat_cap_qualification.json';assert not rp.exists();rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),'branches':len(cs)}))
if __name__=='__main__':main()
