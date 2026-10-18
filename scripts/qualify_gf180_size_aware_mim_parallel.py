"""Supplement existing checks with size-aware parallel native MIM comparison."""
from pathlib import Path
import argparse,json,hashlib,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);a=ap.parse_args();cell=a.cell;assert re.fullmatch(r'[A-Za-z0-9_]+',cell);d=flow.BASE/'layout'/cell;out=flow.BASE/'verification/size_aware_mim'/cell;assert not out.exists();out.mkdir(parents=True);flow.OUT=out
 setup=flow.PDK/'libs.tech/netgen/gf180mcuD_setup.tcl';wrapper=out/'setup.tcl';wrapper.write_text('source /workspace/'+setup.relative_to(flow.ROOT).as_posix()+'\nforeach circuit {1 2} {\nproperty "-circuit$circuit cap_mim_2f0_m4m5_noshield" parallel {c_length critical}\nproperty "-circuit$circuit cap_mim_2f0_m4m5_noshield" parallel {c_width critical}\n}\n')
 ref=d/'reference.spice';rd=flow.BASE/'verification/gds_roundtrip'/cell;files={Path(__file__),setup,wrapper,ref};checks=[]
 for tag,p,sub in [('source',d/(cell+'.spice'),cell),('flat',d/(cell+'_flat.spice'),cell+'_flat'),('gds',rd/'roundtrip.spice',cell)]:
  assert p.exists();files.add(p);log=flow.run(['netgen-lvs','-batch','lvs','/workspace/'+p.relative_to(flow.ROOT).as_posix()+' '+sub,'/workspace/'+ref.relative_to(flow.ROOT).as_posix()+' reference','/workspace/'+wrapper.relative_to(flow.ROOT).as_posix(),tag+'.out']);lp=out/(tag+'.log');lp.write_text(log);files.add(lp);passed='Circuits match uniquely' in log and not re.search(r'(?:There were property errors|Property errors were found|The following cells had property errors)',log);checks.append({'view':tag,'connectivity_and_properties_match':passed});print(tag,passed)
 report={'cell':cell,'checks':checks,'all_views_connectivity_and_properties_match':all(c['connectivity_and_properties_match'] for c in checks),'scope':'Supplemental native MIM dimension-aware LVS. Original PDK setup preserved and sourced unchanged, then both capacitor width and length made critical for parallel grouping so unequal5um/22um devices cannot be ambiguously merged. Original device values and geometry unchanged; source, flat and GDS readback independently compared against frozen reference. No tolerance relaxation or property suppression.','sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)}};(out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');assert report['all_views_connectivity_and_properties_match']
if __name__=='__main__':main()
