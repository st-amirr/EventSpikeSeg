"""Flatten a qualified native hierarchy and independently LVS-check capacitor export."""
from pathlib import Path
import argparse,json,re,hashlib
import probe_gf180_mos_gate_cap as f
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);a=ap.parse_args();cell=a.cell;d=f.BASE/'layout'/cell;qpath=d/'qualification.json';q=json.loads(qpath.read_text());assert q['magic_drc_count']==0 and q['lvs_unique'];files={Path(__file__),qpath};geo={}
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
 tcl=preload+f'load {cell}\nflatten {flat}\nload {flat}\nselect top cell\ndrc on\ndrc style drc(full)\ndrc check\ndrc catchup\ndrc count total\nextract do capacitance\nextract all\nfeedback save flat.feedback\next2spice lvs\next2spice scale off\next2spice -o {flat}.spice\next2spice cthresh 0\next2spice -o {flat}_cap.spice\nquit -noprompt\n'
 tp=d/'flat_extract.tcl';lp=d/'flat_extract.log'
 if tp.exists():
  assert tp.read_text()==tcl;log=lp.read_text()
 else:
  tp.write_text(tcl);log=f.magic(tcl);lp.write_text(log);assert re.search(r'Total DRC errors found:\s*0\b',log) and not (d/'flat.feedback').read_text()
 setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
 log=f.run(['netgen-lvs','-batch','lvs',flat+'.spice '+flat,'reference.spice reference',setup,'flat_lvs_v2.out']);np=d/'flat_lvs_v2.log';np.write_text(log);assert 'Circuits match uniquely' in log,log[-3000:]
 device_lines=lambda p:[l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X')]
 assert device_lines(d/(flat+'.spice'))==device_lines(d/(flat+'_cap.spice')),'Cap export altered native device topology'
 cs=branches_units(d/(flat+'_cap.spice'),flat);neg={str(k):v for k,v in cs.items() if v< -1e-20};assert not neg
 files.update([tp,lp,np,d/'flat.feedback',d/'reference.spice',d/(flat+'.spice'),d/(flat+'_cap.spice')]);r=dict(cell=cell,flat_subcircuit=flat,flat_extraction_completed=True,flat_lvs_unique=True,full_flat_drc_count=0,linear_branch_count=len(cs),negative_aggregate_branches=neg,scope='Actual fully flattened painted geometry, full DRC0, independent native Netgen LVS of device export and token-identical device records in capacitor export against separately qualified reference. All aggregate routing C signs checked and every branch retained; no RPEX/noise/population/full-chip claim.',sha256={p.relative_to(R).as_posix():sha(p) for p in files});(d/'flat_cap_qualification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'flat_branches':len(cs),'LVS_unique':True}))
if __name__=='__main__':main()
