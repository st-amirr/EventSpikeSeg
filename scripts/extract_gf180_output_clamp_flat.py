"""Flatten checked clamp-parent geometry for a correction-free capacitance view."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow
from summarize_gf180_combined_parent_coupling_v5 import branches

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_state_threshold_output_clamp_v2';flat=cell+'_flat';out=flow.BASE/'layout'/cell;flow.OUT=out
 qpath=out/'qualification.json';q=json.loads(qpath.read_text());paths={Path(__file__),qpath};geometry={}
 for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
  for n,h in q.get(key,{}).items():
   p=out/n if key=='sha256' else flow.ROOT/n;assert sha(p)==h,n;paths.add(p)
   if p.suffix=='.mag':geometry.setdefault(p.stem,set()).add(p)
 views=[];visited=set()
 def visit(name):
  if name in visited:return
  assert len(geometry[name])==1;p=next(iter(geometry[name]))
  for child in re.findall(r'^use\s+(\S+)\s+',p.read_text(),re.M):visit(child)
  visited.add(name);views.append(p)
 visit(cell)
 dest=out/(flat+'_cap.spice');assert not dest.exists()
 preload=''.join('load /workspace/'+p.with_suffix('').relative_to(flow.ROOT).as_posix()+'\n' for p in views)
 log=flow.magic(preload+f'load {cell}\nflatten {flat}\nload {flat}\nselect top cell\ndrc on\ndrc style drc(full)\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save flat_extraction.feedback\next2spice lvs\next2spice scale off\next2spice -o {flat}.spice\nextract do capacitance\nextract all\next2spice cthresh 0\next2spice -o {flat}_cap.spice\nquit -noprompt\n')
 lp=out/'flat_cap_extraction.log';lp.write_text(log);paths.add(lp)
 drc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert drc and int(drc[1])==0,log[-2000:]
 cs=branches(dest,flat);negative={str(k):v for k,v in cs.items() if v < -1e-20};assert not negative,negative
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
 lvs=flow.run(['netgen-lvs','-batch','lvs',flat+'.spice '+flat,cell+'.spice '+cell,setup,'flat_lvs.out'])
 lpath=out/'flat_lvs.log';lpath.write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-2500:]
 paths.update([dest,out/(flat+'.spice'),out/'flat_extraction.feedback',lpath])
 report={'flat_extraction_completed':True,'cell':cell,'flat_subcircuit':flat,'full_flat_drc_count':0,'flat_lvs_unique':True,'linear_branch_count':len(cs),'negative_aggregate_branches':negative,'scope':'Same checked source geometry flattened in memory before extraction; no geometry edits, no deleted capacitor corrections. Separate flat LVS against qualified hierarchical device netlist. Use this flat capacitive view for native module simulation; original hierarchical view retains a negative aggregate AUXREF-ground correction and is not a valid passive branch model. Native device capacitance/noise/accuracy/service acceptance separate.','sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(paths)}}
 rp=out/'flat_cap_qualification.json';rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),'branches':len(cs)},indent=2))
if __name__=='__main__':main()
