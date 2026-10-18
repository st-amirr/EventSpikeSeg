"""Audit existing flat painted native source/GDS qualification and cap export."""
from pathlib import Path
import argparse,hashlib,json,re
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);a=ap.parse_args();d=B/'layout'/a.cell;qp=d/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
 for n,h in q['sha256'].items():assert sha(d/n)==h,n
 assert not re.search(r'(?m)^use ',(d/(a.cell+'.mag')).read_text())
 src=d/(a.cell+'.spice');cap=d/(a.cell+'_cap.spice');x=lambda p:[l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X')];assert x(src)==x(cap)
 branches=branches_units(cap,a.cell);neg={str(k):v for k,v in branches.items() if v< -1e-20};assert not neg
 out=d/'flat_cap_qualification.json';assert not out.exists();out.write_text(json.dumps(dict(cell=a.cell,flat_subcircuit=a.cell,flat_extraction_completed=True,flat_lvs_unique=True,full_flat_drc_count=0,linear_branch_count=len(branches),negative_aggregate_branches=neg,scope='Painted source with native source/GDS fullDRC0 and unique independent LVS. Native cap primitive tokens match source; all aggregate branches nonnegative. No interconnect resistance or functional claim.',sha256={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),qp,src,cap,d/(a.cell+'.mag'),d/(a.cell+'.gds')]}),indent=2)+'\n');print(json.dumps({'cell':a.cell,'native_cap_branches':len(branches)}))
if __name__=='__main__':main()
