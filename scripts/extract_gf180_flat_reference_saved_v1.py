"""Flatten a checked module in memory and qualify its passive capacitance view."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow
import argparse,collections

def branches(path,root):
 cs=collections.defaultdict(float)
 for line in path.read_text().splitlines():
  t=line.split()
  if t and t[0].startswith("C"):
   m=re.fullmatch(r"([0-9.eE+\-]+)([fp]?)",t[3]);assert m,t
   cs[tuple(sorted(t[1:3]))]+=float(m[1])*{"":1,"f":1e-15,"p":1e-12}[m[2]]
 return cs

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cell',required=True);args=parser.parse_args();cell=args.cell;assert re.fullmatch(r'[A-Za-z0-9_]+',cell);flat=cell+'_flat';out=flow.BASE/'layout'/cell;flow.OUT=out
 qpath=out/'qualification.json';q=json.loads(qpath.read_text());cache_changes=[];paths={Path(__file__),qpath,out/'reference.spice'};geometry={}
 for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
  for n,h in q.get(key,{}).items():
   p=out/n if key=='sha256' else flow.ROOT/n;current=sha(p)
   if current!=h:
    assert p.suffix=='.ext',n
    cache_changes.append({'path':p.relative_to(flow.ROOT).as_posix(),'qualified_sha256':h,'current_sha256':current,'reason':'Generated extraction cache rewritten by another qualified parent; all source geometry/netlists remain hash-checked.'})
   paths.add(p)
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
 log=flow.magic(preload+f'load {cell}\nflatten {flat}\nload {flat}\nsave {flat}\nselect top cell\ndrc on\ndrc style drc(full)\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save flat_extraction.feedback\next2spice lvs\next2spice scale off\next2spice -o {flat}.spice\nextract do capacitance\nextract all\next2spice cthresh 0\next2spice -o {flat}_cap.spice\nquit -noprompt\n')
 lp=out/'flat_cap_extraction.log';lp.write_text(log);paths.add(lp)
 drc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert drc and int(drc[1])==0,log[-2000:]
 cs=branches(dest,flat);negative={str(k):v for k,v in cs.items() if v < -1e-20};assert not negative,negative
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
 lvs=flow.run(['netgen-lvs','-batch','lvs',flat+'.spice '+flat,'reference.spice reference',setup,'flat_lvs_reference.out'])
 lpath=out/'flat_lvs.log';lpath.write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-2500:]
 paths.update([dest,out/(flat+'.spice'),out/'flat_extraction.feedback',lpath])
 report={'flat_extraction_completed':True,'generated_cache_changes':cache_changes,'cell':cell,'flat_subcircuit':flat,'full_flat_drc_count':0,'flat_lvs_unique':True,'lvs_basis':'Flat extracted physical geometry vs frozen flat-child reference; original qualification separately checks flat source and flat GDS reimport against same reference.','linear_branch_count':len(cs),'negative_aggregate_branches':negative,'scope':'Same checked source geometry flattened in memory before extraction; no geometry edits, no deleted capacitor corrections. Separate flat LVS against frozen reference netlist; parent source and GDS readback are independently checked against that reference. Use this flat capacitive view for native module simulation; hierarchical view is preserved separately; use flat view to avoid nested correction artifacts. Native device capacitance/noise/accuracy/service acceptance separate.','sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(paths)}}
 rp=out/'flat_cap_qualification.json';rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),'branches':len(cs)},indent=2))
if __name__=='__main__':main()
