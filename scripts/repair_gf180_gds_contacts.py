"""Preserve an original GF180 cell and repair GDS via export in a separate view."""
import argparse,hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cell',required=True);a=p.parse_args();native=flow.BASE/'layout'/a.cell;qp=native/'qualification.json';q=json.loads(qp.read_text());source=Path(__file__);cell=a.cell+'_gdsfix';out=flow.BASE/'layout'/cell
 if out.joinpath('qualification.json').exists():raise ValueError('Qualified repair already exists; preserve its immutable view')
 if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Audited original Magic layout required')
 inputs={qp,native/(a.cell+'.mag'),native/(a.cell+'.spice')};original={native/n:sha for n,sha in q['sha256'].items()}
 if any(digest(f)!=sha for f,sha in original.items()):raise ValueError('Original physical source differs')
 inputs.update(original);layers=rectangles(native/(a.cell+'.mag'),0);repairs=[]
 for layer in ['via2','via3','via4']:
  for i,box in enumerate(list(layers.get(layer,[]))):
   x1,y1,x2,y2=box
   if min(x2-x1,y2-y1)>56:continue
   new=(x1-4,y1-4,x2+4,y2+4);layers[layer][i]=new;number=int(layer[-1]);x=(x1+x2)//2;y=(y1+y2)//2
   # 0.30um painted via allows the mask exporter 10nm grid/border;
   # local0.44um metal pads preserve enclosure of the exported0.26um cut.
   for metal in ['metal'+str(number),'metal'+str(number+1)]:layers.setdefault(metal,[]).append((x-44,y-44,x+44,y+44))
   repairs.append({'layer':layer,'original_box':box,'repaired_box':new})
 if not repairs:raise ValueError('No small exported-via candidates found')
 raw=(native/(a.cell+'.mag')).read_text();labels=raw[raw.index('<< labels >>'):raw.index('<< end >>')];lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for layer,boxes in layers.items():lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines += [labels.rstrip(),'<< end >>',''];out.mkdir(parents=True,exist_ok=True);flow.OUT=out;(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');(out/'build_source.py').write_bytes(source.read_bytes())
 log=flow.magic(f'load {cell}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
 if not drc or int(drc.group(1)) or (out/'gds_warnings.feedback').read_text() or re.search(r'\d+ problems occurred',log):raise RuntimeError(log[-4500:])
 lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'/workspace/'+(native/(a.cell+'.spice')).relative_to(flow.ROOT).as_posix()+' '+a.cell,'/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(out/'netgen.log').write_text(lvs)
 if 'Circuits match uniquely' not in lvs:raise RuntimeError(lvs[-3000:])
 caplog=flow.magic(f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog)
 feedback=(out/'warnings.feedback').read_text()+(out/'capacitance_warnings.feedback').read_text()
 if feedback:raise ValueError('Extraction feedback unresolved')
 rounddir=flow.BASE/'verification/gds_roundtrip'/cell;rounddir.mkdir(parents=True,exist_ok=True);flow.OUT=rounddir
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc check\ndrc count\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rounddir/'readback.log').write_text(readlog)
 roundlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(native/(a.cell+'.spice')).relative_to(flow.ROOT).as_posix()+' '+a.cell,'/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(rounddir/'netgen.log').write_text(roundlvs);rdrc=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 if not rdrc or int(rdrc.group(1)) or 'Circuits match uniquely' not in roundlvs or (rounddir/'roundtrip.feedback').read_text():raise RuntimeError('GDS readback verification failed\n'+readlog[-1200:]+'\n'+roundlvs[-1800:])
 if any(digest(f)!=sha for f,sha in original.items()):raise ValueError('Original physical views changed during repair')
 files=[out/(cell+x) for x in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']];roundfiles=[rounddir/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]
 result={'cell':cell,'original_cell':a.cell,'magic_drc_count':0,'lvs_unique':True,'gds_export_feedback':'','gds_roundtrip_lvs_unique':True,'gds_roundtrip_drc_count':0,'extraction_feedback':'','bbox_um':[int(x)*.005 for x in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],'capacitance_count':len(re.findall(r'(?m)^C\S+',(out/(cell+'_cap.spice')).read_text())),'via_repairs':repairs,'original_physical_views_preserved':True,'physical_state_accepted':False,'full_chip_accepted':False,'scope':'Separate repaired metal/via view, MOS/resistor geometry preserved. Magic DRC/LVS against original intended circuit plus capacitance extraction, error-free GDS export and GDS reimport DRC/LVS against original intended circuit. Changed parasitics require new module simulations; no old-circuit performance, routing resistance extraction, model/5ms/chip acceptance.','sha256':{f.name:digest(f) for f in files},'input_sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in inputs},'gds_roundtrip_sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in roundfiles}}
 (out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'via_repairs':len(repairs),'gds_roundtrip_lvs_unique':True,'bbox_um':result['bbox_um']},indent=2))
if __name__=='__main__':main()
