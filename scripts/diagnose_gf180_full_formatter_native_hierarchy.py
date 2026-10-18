"""Compare the full formatter against independently qualified native child hierarchies."""
from pathlib import Path
import re,json,hashlib
import probe_gf180_mos_gate_cap as f
from gf180_compact_lvs_v2 import compact
from qualify_gf180_mim_dimension_classes import color
ROOT=Path(__file__).resolve().parents[1]
def main():
 cell='gf180_formatted_energy64_v3';d=f.BASE/'layout'/cell;out=f.BASE/'verification/full_formatter_native_hierarchy_diagnosis_v1';assert not out.exists();out.mkdir(parents=True);f.OUT=out
 old=(d/'reference.spice').read_text();top=re.search(r'(?ms)^\.subckt reference .*?^\.ends[^\n]*',old)[0];parts=[];files=[d/'reference.spice',d/(cell+'.spice')]
 for child in ['gf180_product_gate_formatter_v3','gf180_energy_mean_root64_v1']:
  folder=f.BASE/'layout'/child;q=json.loads((folder/'qualification.json').read_text());p=folder/(child+'.spice');assert hashlib.sha256(p.read_bytes()).hexdigest()==q['sha256'][p.name];parts.append(p.read_text());files.append(p)
 ref=out/'reference_native_hierarchy.spice';ref.write_text('\n'.join(parts+[top])+'\n')
 for tag,p,sub in [('source',d/(cell+'.spice'),cell),('reference',ref,'reference')]:
  txt,_=compact(p.read_text(),sub);txt,_=color(txt);(out/(tag+'.spice')).write_text(txt)
 setup='/workspace/'+f.PDK.relative_to(ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';log=f.run(['netgen-lvs','-batch','lvs','source.spice '+cell,'reference.spice reference',setup,'comparison.out']);(out/'comparison.log').write_text(log);ok='Circuits match uniquely' in log and 'property errors' not in log.lower();r={'comparison_pass':ok,'scope':'Parent routing independently checked against qualified original native child extraction hierarchies rather than an alternative flat-child resistor segmentation. Exact MIM dimensions retained. No geometry edits or tolerance relaxation. GDS and flat RC qualification remain separate.','sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}};(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));print(log[-1200:])
if __name__=='__main__':main()
