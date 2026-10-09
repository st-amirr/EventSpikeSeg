"""Qualify a native GF180 high-resistance poly conversion primitive."""
import argparse,hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles
CELL='gf180_writeback_resistor_123x1'
def main():
 global CELL
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--length-um',type=int,choices=[2,4,8,16,32,60,64,123,128],default=123);a=parser.parse_args();length=a.length_um;CELL=f'gf180_writeback_resistor_{length}x1'
 out=flow.BASE/'layout'/CELL;out.mkdir(parents=True,exist_ok=True);flow.OUT=out
 log=flow.magic(f'load resistor_raw\nmagic::gencell gf180mcu::ppolyf_u_1k r -spice w 1u l {length}u\nwriteall force\nquit -noprompt\n');(out/'generation.log').write_text(log)
 files=[p for p in out.glob('ppolyf_u_1k_*.mag') if f'string parameters w 1.0 l {float(length)} ' in p.read_text()]
 if not files:raise RuntimeError('Native resistor PCell unavailable')
 raw=max(files,key=lambda p:p.stat().st_mtime);text=raw.read_text();rs=rectangles(raw,0)
 contacts=sorted(rs['polycontact'],key=lambda r:r[1]);labels=['<< labels >>']
 for i,(net,box) in enumerate(zip(['B','A'],contacts),1):
  x=(box[0]+box[2])//2;y=(box[1]+box[3])//2
  labels += [f'rlabel polycontact s {x-15} {y-15} {x+15} {y+15} 4 {net}',f'port {i} nsew']
 guard=next(r for r in rs['psubdiffcont'] if r[0]<-200 and r[1]<0<r[3]);x=(guard[0]+guard[2])//2
 labels += [f'rlabel psubdiffcont s {x-10} -20 {x+10} 20 4 VSS','port 3 nsew']
 (out/f'{CELL}.mag').write_text(text.replace('<< end >>','\n'.join(labels)+'\n<< end >>'),encoding='ascii')
 log=flow.magic(f'load {CELL}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 match=re.search(r'Total DRC errors found:\s*(\d+)',log)
 if not match or int(match.group(1)):raise RuntimeError(log[-3000:])
 (out/'reference.spice').write_text(f'.subckt reference B A VSS\nXr B A VSS ppolyf_u_1k r_width=1u r_length={length}u\n.ends\n')
 lvs=flow.run(['netgen-lvs','-batch','lvs',f'{CELL}.spice {CELL}','reference.spice reference',f'/workspace/{flow.PDK.relative_to(flow.ROOT).as_posix()}/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(out/'netgen.log').write_text(lvs)
 if 'Circuits match uniquely' not in lvs:raise RuntimeError(lvs[-3000:])
 caplog=flow.magic(f'load {CELL}\nextract do capacitance\nextract all\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {CELL}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog)
 cap=(out/f'{CELL}_cap.spice').read_text()
 if f'.subckt {CELL} B A VSS' not in cap or 'VSUBS' in cap:raise RuntimeError('Explicit resistor/substrate ports required')
 feedback=(out/'warnings.feedback').read_text()
 if feedback:raise RuntimeError('Extraction feedback requires qualification: '+feedback)
 snapshot=out/'build_source.py';snapshot.write_bytes(Path(__file__).read_bytes())
 report={'cell':CELL,'resistor_width_um':1,'resistor_length_um':length,'ports':['B','A','VSS'],'magic_drc_count':0,'lvs_unique':True,'bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],'extraction_feedback':feedback,'capacitance_count':len(re.findall(r'(?m)^C\S+',cap)),'physical_state_accepted':False,'scope':'Native three-terminal high-resistance poly device with grounded substrate, actual geometry/GDS/DRC/LVS/capacitance extraction. Device resistance is official primitive model, not routing RPEX. R/C writeback calibration, loading, noise/PVT/mismatch, combined routing, PLIF and chip acceptance remain unqualified.','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/f'{CELL}.mag',out/f'{CELL}.gds',out/f'{CELL}.spice',out/f'{CELL}_cap.spice',snapshot]}}
 (out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
