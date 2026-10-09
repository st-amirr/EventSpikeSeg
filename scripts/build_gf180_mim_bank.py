"""Route a physical parallel bank from audited native GF180 MIM geometry."""
import argparse,hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--size-um',type=int,choices=[7,22],default=7);p.add_argument('--count',type=int,choices=[8,9],default=9);a=p.parse_args();source=Path(__file__);size=a.size_um;cell=f'gf180_mim_bank_{size}x{size}_n{a.count}';out=flow.BASE/'layout'/cell;native=flow.BASE/'layout'/f'gf180_mim_{size}x{size}';qp=native/'qualification.json';q=json.loads(qp.read_text());inputs={qp,source}
 if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Native MIM qualification required')
 for name,sha in q['sha256'].items():
  f=native/name
  if digest(f)!=sha:raise ValueError('Native MIM provenance differs')
  inputs.add(f)
 layers0=rectangles(native/(q['cell']+'.mag'),0);layers={};pitch=(size+9)*200;half=size*100;bottom=-half-340;top=half+460;vss_y=bottom-500
 def rect(layer,box):layers.setdefault(layer,[]).append(box)
 for i in range(a.count):
  dx=i*pitch
  for layer,boxes in layers0.items():
   for x1,y1,x2,y2 in boxes:rect(layer,(x1+dx,y1,x2+dx,y2))
  # P exits vertically on M5, clear of the opposite M5 rim at the right.
  rect('metal5',(dx-180,0,dx-60,top+60))
  # M exits the left bottom-plate rim on M4; native substrate taps use M1.
  left=-half-200;tapx=half+640
  rect('metal4',(dx+left-60,bottom-60,dx+left+60,0))
  rect('metal1',(dx+tapx-40,vss_y-40,dx+tapx+40,0))
 end=(a.count-1)*pitch
 rect('metal5',(-400,top-60,end+200,top+60))
 rect('metal4',(-half-400,bottom-60,end+200,bottom+60))
 rect('metal1',(-half-400,vss_y-40,end+half+900,vss_y+40))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for layer,boxes in layers.items():
  lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(layer,y,net) in enumerate([('metal5',top,'P'),('metal4',bottom,'M'),('metal1',vss_y,'VSS')],1):lines+=[f'rlabel {layer} s -300 {y-20} -260 {y+20} 4 {net}',f'port {i} nsew']
 lines+=['<< end >>',''];out.mkdir(parents=True,exist_ok=True);flow.OUT=out;(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');snapshot=out/'build_source.py';snapshot.write_bytes(source.read_bytes())
 log=flow.magic(f'load {cell}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
 if not drc or int(drc.group(1)):raise RuntimeError(log[-4500:])
 ref='.subckt reference P M VSS\n'+''.join(f'Xcap{i} P M cap_mim_2f0_m4m5_noshield c_length={size}u c_width={size}u\n' for i in range(a.count))+'.ends\n';(out/'reference.spice').write_text(ref)
 lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference','/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(out/'netgen.log').write_text(lvs)
 if 'Circuits match uniquely' not in lvs:raise RuntimeError(lvs[-4500:])
 caplog=flow.magic(f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);captext=(out/(cell+'_cap.spice')).read_text()
 if 'VSUBS' in captext or re.search(r'FLOATING|floating',captext):raise ValueError('Bank substrate or route extraction contains unbound nodes')
 feedback=(out/'warnings.feedback').read_text()+(out/'capacitance_warnings.feedback').read_text()
 if feedback:raise ValueError('Extraction feedback requires resolution')
 generated=[out/(cell+x) for x in ['.mag','.spice','_cap.spice','.gds']]+[snapshot,out/'reference.spice',out/'extraction.log',out/'netgen.log',out/'capacitance_extraction.log',out/'warnings.feedback',out/'capacitance_warnings.feedback']
 result={'cell':cell,'native_cell':q['cell'],'native_capacitor_instance_count':a.count,'native_square_size_um':size,'magic_drc_count':0,'lvs_unique':True,'extraction_feedback':feedback,'bbox_um':[int(x)*.005 for x in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],'capacitance_count':len(re.findall(r'(?m)^C\S+',captext)),'physical_state_accepted':False,'combined_frontend_accepted':False,'full_chip_accepted':False,'scope':'Routed parallel native MIM bank with actual M5 P bus, M4 M bus and M1 explicit substrate bus; Magic DRC and Netgen LVS against the declared native-device count, plus capacitance extraction. No resistance extraction, sampled noise/retention or combined PLIF/service/chip acceptance. Bus capacitance must be included before interpreting existing individual-capacitor simulations.','sha256':{f.name:digest(f) for f in generated},'input_sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in inputs}}
 (out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
