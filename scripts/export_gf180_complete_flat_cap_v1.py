"""Export complete native substrate/coupling C from an already qualified flat .ext view."""
from pathlib import Path
import argparse,hashlib,json,re,shlex
import probe_gf180_mos_gate_cap as f
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);a=ap.parse_args();assert re.fullmatch(r'[A-Za-z0-9_]+',a.cell)
 d=f.BASE/'layout'/a.cell;qp=d/'qualification.json';fp=d/'flat_cap_qualification.json';q=json.loads(qp.read_text());fq=json.loads(fp.read_text());assert q['magic_drc_count']==0 and fq['flat_lvs_unique']
 flat=fq['flat_subcircuit'];ext=d/(flat+'.ext');ref=d/(flat+'.spice');assert ext.exists() and ref.exists();dest=d/(flat+'_fullcap.spice');report=d/'flat_cap_full_qualification.json';assert not dest.exists() and not report.exists()
 # hierarchy off is essential even when the input .ext is geometrically flat.
 # Force the top wrapper; without an on-disk flat MAG, auto drops its .subckt.
 t=f'load {flat}\next2spice lvs\next2spice hierarchy off\next2spice subcircuit top on\next2spice cthresh 0\next2spice scale off\next2spice -o {flat}_fullcap.spice\nquit -noprompt\n';tp=d/'export_full_native_cap.tcl';tp.write_text(t);f.OUT=d;lp=d/'export_full_native_cap.log';lp.write_text(f.magic(t))
 x=lambda p:[l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X')];assert x(ref)==x(dest)
 text=dest.read_text().replace('\n+',' ');ports=re.search(r'(?m)^\.subckt\s+'+flat+r'\s+([^\n]+)',text)[1].split();assert ports==q['ports']
 cs=branches_units(dest,flat);assert not any(v<0 for v in cs.values());expected={t[1]:float(t[3])*1e-18 for line in ext.read_text().splitlines() if line.startswith('node ') for t in [shlex.split(line)]};errs={}
 for n,v in expected.items():
  actual=cs.get(tuple(sorted((n,'VSS'))),0)
  if abs(actual-v)>max(5e-18,abs(v)*5e-5):errs[n]=[v,actual]
 assert not errs,errs
 fq.update(export_hierarchy=False,linear_branch_count=len(cs),device_tokens_identical_to_qualified_flat=True,all_flat_extraction_node_ground_caps_verified=True,scope=fq['scope']+' Complete native flat substrate/coupling C export uses hierarchy off,top wrapper on. Every native device token/port unchanged and every .ext node ground cap checked; no manual cap fitting. Previous hierarchy-on substrate coverage is not assumed.')
 fq['sha256'].update({p.relative_to(R).as_posix():sha(p) for p in [qp,fp,ext,ref,dest,tp,lp,Path(__file__)]});report.write_text(json.dumps(fq,indent=2)+'\n');print(json.dumps({'cell':a.cell,'branches':len(cs),'native_device_count':len(x(dest)),'report':report.relative_to(R).as_posix()}))
if __name__=='__main__':main()
