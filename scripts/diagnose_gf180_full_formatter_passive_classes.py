"""Diagnose full formatter LVS using exact passive dimensions in comparison copies."""
from pathlib import Path
import re,json,hashlib
import probe_gf180_mos_gate_cap as f
from qualify_gf180_mim_dimension_classes import color
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=f.BASE/'layout/gf180_formatted_energy64_v3';out=f.BASE/'verification/full_formatter_passive_class_diagnosis_v1';assert not out.exists();out.mkdir(parents=True);f.OUT=out;files=[]
 for tag in ['source','reference']:
  p=d/(tag+'_compact.spice');text,counts=color(p.read_text());lines=[]
  for line in text.splitlines():
   if line.startswith('X') and 'ppolyf_u_1k' in line:
    dims=[re.search(r'\b'+v+r'=(\S+)',line)[1] for v in ['r_width','r_length']];line=line.replace('ppolyf_u_1k','res_exact_'+'_'.join(x.replace('.','p').replace('-','m').replace('+','p') for x in dims))
   lines.append(line)
  dest=out/(tag+'.spice');dest.write_text('\n'.join(lines)+'\n');files.append(dest)
 setup='/workspace/'+f.PDK.relative_to(ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';log=f.run(['netgen-lvs','-batch','lvs','source.spice gf180_formatted_energy64_v3','reference.spice reference',setup,'comparison.out']);(out/'comparison.log').write_text(log);passed='Circuits match uniquely' in log and 'property errors' not in log.lower();result={'comparison_pass':passed,'scope':'Diagnostic comparison-only exact MIM dimensions and exact native resistor segment dimensions; prevents PDK series/parallel resistor reduction from hiding segment identity. Original geometry and netlists untouched. This diagnostic does not qualify physical layout by itself.','sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}};(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));print(log[-2000:])
if __name__=='__main__':main()
