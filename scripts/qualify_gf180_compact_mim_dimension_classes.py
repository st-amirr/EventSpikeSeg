"""Check MIM dimensions structurally to avoid old Netgen mixed-size symmetry ambiguity."""
from pathlib import Path
from decimal import Decimal
import re,json,hashlib,argparse,collections
import probe_gf180_mos_gate_cap as flow
from gf180_compact_lvs_v2 import compact

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(s):
 m=re.fullmatch(r'([0-9.eE+-]+)([unp]?)',s);assert m,s
 return Decimal(m[1])*{'':Decimal(1),'u':Decimal('1e-6'),'n':Decimal('1e-9'),'p':Decimal('1e-12')}[m[2]]
def color(text):
 text=text.replace('\n+',' ');counts=collections.Counter();out=[]
 for line in text.splitlines():
  if line.startswith('X') and 'cap_mim_2f0_m4m5_noshield' in line:
   dims=[number(re.search(r'\b'+p+r'=(\S+)',line)[1]) for p in ['c_width','c_length']];nm='mim_size_'+str(int(dims[0]*Decimal('1e9')))+'n_'+str(int(dims[1]*Decimal('1e9')))+'n';line=line.replace('cap_mim_2f0_m4m5_noshield',nm);counts[nm]+=1
  out.append(line)
 return '\n'.join(out)+'\n',dict(counts)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cell',required=True);a=ap.parse_args();cell=a.cell;assert re.fullmatch(r'[A-Za-z0-9_]+',cell);d=flow.BASE/'layout'/cell;out=flow.BASE/'verification/dimension_class_mim'/cell;assert not out.exists();out.mkdir(parents=True);flow.OUT=out;ref=d/'reference.spice';setup=flow.PDK/'libs.tech/netgen/gf180mcuD_setup.tcl';files={Path(__file__),ref,setup,Path(__file__).with_name('gf180_compact_lvs_v2.py')};ct,ci=compact(ref.read_text(),'reference');txt,counts=color(ct);rp=out/'reference_size_classes.spice';rp.write_text(txt);files.add(rp);checks=[]
 for tag,p,sub in [('source',d/(cell+'.spice'),cell),('flat',d/(cell+'_flat.spice'),cell+'_flat'),('gds',flow.BASE/'verification/gds_roundtrip'/cell/'roundtrip.spice',cell)]:
  files.add(p);ct,ci=compact(p.read_text(),sub);txt,c=color(ct);copy=out/(tag+'_size_classes.spice');copy.write_text(txt);files.add(copy);log=flow.run(['netgen-lvs','-batch','lvs',copy.name+' '+sub,rp.name+' reference','/workspace/'+setup.relative_to(flow.ROOT).as_posix(),tag+'.out']);lp=out/(tag+'.log');lp.write_text(log);files.add(lp);passed=('Circuits match uniquely' in log or 'Circuits match correctly' in log) and not re.search(r'(?:There were property errors|Property errors were found|The following cells had property errors)',log);checks.append({'view':tag,'connectivity_and_dimensions_match':passed,'definition_size_counts':c});print(tag,passed)
 result={'cell':cell,'all_views_connectivity_and_dimensions_match':all(x['connectivity_and_dimensions_match'] for x in checks),'checks':checks,'scope':'Graph-preserving recursive flattening into comparison-only short-name copies precedes dimension classification to avoid old Netgen hierarchy overflow. Exact external port order and primitive topology/parameters retained. Supplemental LVS preserves all nodes, instances, numeric parameters and device topology; in comparison-only copies, each native MIM model token is classified by its exact parsed physical width and length (normalized in integer nanometers). Unequal dimensions become different structural device classes, preventing old Netgen from arbitrarily pairing parallel5um and22um devices. Original source/GDS/extracted simulation netlists unchanged. All remaining PDK setup rules retained; no deleted devices, ignored properties or relaxed tolerance. Frozen reference vs source, full flat and GDS readback checked independently.','sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)}};(out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');assert result['all_views_connectivity_and_dimensions_match']
if __name__=='__main__':main()
