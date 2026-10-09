"""Route and qualify the native resistor/reset TG/dummy as one physical macro."""
import hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=Path(__file__);cell='gf180_resistive_reset_gate_r2_dummy';out=flow.BASE/'layout'/cell;layers={};sources={source};qualified=[];pins=[];net_order=['LINEAR','RFEED','SUM','RESET','RESETB','VDD','VSS'];ports=['LINEAR','SUM','RESET','RESETB','VDD','VSS']
 def rect(layer,box):layers.setdefault(layer,[]).append(tuple(box))
 specs=[('gf180_writeback_resistor_2x1',0,{'B':'LINEAR','A':'RFEED','VSS':'VSS'},{'B':-600,'A':600,'VSS':-1000}),('gf180_fixed_body_tg',4000,{'A':'RFEED','B':'SUM','EN':'RESET','ENB':'RESETB','VSS':'VSS','VDD':'VDD'},{'A':-600,'B':600,'EN':1000,'ENB':1400,'VSS':-1000,'VDD':-1400}),('gf180_fixed_body_tg_nf0p5',8000,{'A':'SUM','B':'SUM','EN':'RESETB','ENB':'RESET','VSS':'VSS','VDD':'VDD'},{'A':-600,'B':600,'EN':1000,'ENB':1400,'VSS':-1000,'VDD':-1400})]
 reference=[]
 for native,dx,mapping,columns in specs:
  nd=flow.BASE/'layout'/native;qp=nd/'qualification.json';q=json.loads(qp.read_text());sources.add(qp);qualified.append(q)
  if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Qualified native input required')
  for name,sha in q['sha256'].items():
   f=nd/name
   if digest(f)!=sha:raise ValueError('Native input provenance differs')
   sources.add(f)
  mag=nd/(native+'.mag');txt=mag.read_text();reference.append((nd/(native+'.spice')).read_text())
  for layer,boxes in rectangles(mag,0).items():
   for x1,y1,x2,y2 in boxes:rect(layer,(x1+dx,y1,x2+dx,y2))
  labels=re.findall(r'(?m)^rlabel (\S+) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)',txt)
  if {row[-1] for row in labels}!=set(mapping):raise ValueError('Native port labels differ')
  for layer,x1,y1,x2,y2,pin in labels:
   x=(int(x1)+int(x2))//2+dx;y=(int(y1)+int(y2))//2;column=dx+columns[pin];net=mapping[pin];bus_y=4000+net_order.index(net)*400
   first=2 if layer=='metal2' else 1
   for number in range(first,4):rect('metal'+str(number),(x-40,y-40,x+40,y+40))
   for number in range(first,3):rect('via'+str(number),(x-26,y-26,x+26,y+26))
   rect('metal3',(min(x,column)-40,y-40,max(x,column)+40,y+40));rect('metal3',(column-40,y-40,column+40,y+40));rect('via3',(column-26,y-26,column+26,y+26));rect('metal4',(column-40,y-40,column+40,bus_y+40));rect('metal4',(column-40,bus_y-40,column+40,bus_y+40));rect('via4',(column-26,bus_y-26,column+26,bus_y+26));rect('metal5',(column-60,bus_y-60,column+60,bus_y+60));pins.append((native,pin,net,column,y))
 for net in net_order:
  y=4000+net_order.index(net)*400;rect('metal5',(-1800,y-60,9800,y+60))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for layer,boxes in layers.items():lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for net in net_order:
  y=4000+net_order.index(net)*400;lines.append(f'rlabel metal5 s -1780 {y-20} -1740 {y+20} 4 {net}')
  if net in ports:lines.append(f'port {ports.index(net)+1} nsew')
 lines+=['<< end >>',''];out.mkdir(parents=True,exist_ok=True);flow.OUT=out;(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');(out/'build_source.py').write_bytes(source.read_bytes())
 log=flow.magic(f'load {cell}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
 if not drc or int(drc.group(1)):raise RuntimeError(log[-4500:])
 reference+=['.subckt reference '+' '.join(ports),'Xr LINEAR RFEED VSS gf180_writeback_resistor_2x1','Xreset RFEED SUM RESET RESETB VSS VDD gf180_fixed_body_tg','Xdummy SUM SUM RESETB RESET VSS VDD gf180_fixed_body_tg_nf0p5','.ends'];(out/'reference.spice').write_text('\n'.join(reference)+'\n')
 lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference','/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(out/'netgen.log').write_text(lvs)
 if 'Circuits match uniquely' not in lvs:raise RuntimeError(lvs[-4500:])
 caplog=flow.magic(f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);ct=(out/(cell+'_cap.spice')).read_text();feedback=(out/'warnings.feedback').read_text()+(out/'capacitance_warnings.feedback').read_text()
 if feedback or re.search('FLOATING|VSUBS',ct):raise ValueError('Unresolved extraction feedback or substrate')
 files=[out/(cell+x) for x in ['.mag','.spice','_cap.spice','.gds']]+[out/n for n in ['build_source.py','reference.spice','extraction.log','netgen.log','capacitance_extraction.log','warnings.feedback','capacitance_warnings.feedback']]
 result={'cell':cell,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'extraction_feedback':feedback,'bbox_um':[int(x)*.005 for x in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],'capacitance_count':len(re.findall(r'(?m)^C\S+',ct)),'qualified_native_components':qualified,'pin_routes':pins,'combined_frontend_accepted':False,'physical_state_accepted':False,'full_chip_accepted':False,'scope':'One routed native2um poly resistor in series with fixed-body reset TG and half-size opposite-phase summing-node dummy. Real M3 access/M4 columns/M5 net buses and explicit rail/body connectivity. DRC/LVS and capacitance extraction only; no routing resistance extraction, reset settling/noise/PVT/full PLIF/service acceptance.','sha256':{f.name:digest(f) for f in files},'input_sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in sources}}
 (out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'magic_drc_count':0,'lvs_unique':True,'bbox_um':result['bbox_um'],'capacitance_count':result['capacitance_count']},indent=2))
if __name__=='__main__':main()
