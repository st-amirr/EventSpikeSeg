"""Build the seven-MOS PMOS-input OTA with verified exported connectivity."""
import hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

PORTS=['IP','IN','OUT','VDD','VSS','BIAS','CMP']
DEVICES=[('n1','nfet',.25,.28,['mirror','IN','tail','VSS']),
 ('n2','nfet',.25,.28,['CMP','IP','tail','VSS']),
 ('tail','nfet',.25,.56,['tail','BIAS','VSS','VSS']),
 ('p1','pfet',.5,.28,['mirror','mirror','VDD','VDD']),
 ('p2','pfet',.5,.28,['CMP','mirror','VDD','VDD']),
 ('pout','pfet',1,.28,['OUT','CMP','VDD','VDD']),
 ('sink','nfet',.5,.28,['OUT','BIAS','VSS','VSS'])]


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_compact_nf_threshold_shielded';out=flow.BASE/'layout'/cell;out.mkdir(parents=True,exist_ok=True);source=Path(__file__)
 if (out/'qualification.json').exists():raise ValueError('Preserve qualified OTA')
 genout=out/'source_generation_spaced';genout.mkdir(parents=True,exist_ok=True);flow.OUT=genout
 tcl=['dict set gf180mcu::ruleset gate_to_polycont 0.50','load ota_raw']
 for name,family,w,length,nets in DEVICES:tcl.append(f'magic::gencell gf180mcu::{family}_03v3 {name} -spice w {w}u l {length}u nf 1 guard 0 botc 0 topc 1')
 tcl+=['writeall force','quit -noprompt',''];gen=flow.magic('\n'.join(tcl));(out/'generation.log').write_text(gen)
 layers={};pcells=[];tracks={net:3000+i*1200 for i,net in enumerate(PORTS+['mirror','tail'])}
 def rect(layer,box):layers.setdefault(layer,[]).append(tuple(box))
 def via1(x,y):
  for layer in ['metal1','metal2']:rect(layer,(x-38,y-38,x+38,y+38))
  rect('via1',(x-26,y-26,x+26,y+26))
 def via2(x,y):
  for layer in ['metal2','metal3']:rect(layer,(x-40,y-40,x+40,y+40))
  rect('via2',(x-28,y-28,x+28,y+28))
 for index,(name,family,w,length,nets) in enumerate(DEVICES):
  dx=index*3200
  files=[p for p in genout.glob(family+'_03v3_*.mag') if f'string parameters w {float(w)} l {float(length)} ' in p.read_text() and 'guard 0' in p.read_text() and 'botc 0' in p.read_text()]
  if not files:raise ValueError('Requested unguarded top-contact PCell absent')
  pc=max(files,key=lambda p:p.stat().st_mtime);pcells.append(pc);shape=rectangles(pc,0)
  for layer,boxes in shape.items():
   for x1,y1,x2,y2 in boxes:rect(layer,(x1+dx,y1,x2+dx,y2))
  contact=shape['polycontact'][0];gx=(contact[0]+contact[2])//2+dx;gy=(contact[1]+contact[3])//2;lift=(gy+100+1)//2*2
  rect('metal1',(gx-38,gy-38,gx+38,lift+38));via1(gx,lift);rect('metal2',(gx-38,lift-38,gx+38,tracks[nets[1]]+40));via2(gx,tracks[nets[1]])
  contacts=shape['ndiffc' if family=='nfet' else 'pdiffc']
  for sign,net in [(1,nets[0]),(-1,nets[2])]:
   boxes=[b for b in contacts if sign*(b[0]+b[2])>0];box=max(boxes,key=lambda b:(b[2]-b[0])*(b[3]-b[1]));x=(box[0]+box[2])//2+dx;cy=(box[1]+box[3])//2;column=dx+sign*700
   via1(x,cy);rect('metal2',(min(x,column)-38,cy-38,max(x,column)+38,cy+38));rect('metal2',(column-38,cy-38,column+38,tracks[net]+40));via2(column,tracks[net])
  tx=dx+(-1200 if family=='nfet' else 1200);ty=-600
  if family=='nfet':rect('pwell',(tx-180,ty-200,tx+180,ty+200));diff='psubdiff';contact='psubdiffcont'
  else:
   well=shape['nwell'];rect('nwell',(dx+min(b[0] for b in well),min(-1000,min(b[1] for b in well)),dx+max(1400,max(b[2] for b in well)),max(500,max(b[3] for b in well))));diff='nsubdiff';contact='nsubdiffcont'
  rect(diff,(tx-36,ty-100,tx+36,ty+100));rect(contact,(tx-23,ty-87,tx+23,ty+87));rect('metal1',(tx-38,ty-98,tx+38,ty+98));via1(tx,ty);column=dx+1500;rect('metal2',(min(tx,column)-38,ty-38,max(tx,column)+38,ty+38));rect('metal2',(column-38,ty-38,column+38,tracks[nets[3]]+40));via2(column,tracks[nets[3]])
 for track in tracks.values():rect('metal3',(-1600,track-40,22000,track+40))
 # Grounded M3 shields between long signal accesses, connected through M4.
 for y in [3600+1200*i for i in range(8)]+[tracks['VSS']]:
  rect('metal3',(-1880,y-40,22000,y+40));rect('metal4',(-1840,y-40,-1760,y+40));rect('via3',(-1828,y-28,-1772,y+28))
 rect('metal4',(-1840,3560,-1760,12040))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for layer,boxes in layers.items():lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,net in enumerate(PORTS,1):y=tracks[net];lines+=[f'rlabel metal3 s -1560 {y-20} -1520 {y+20} 4 {net}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');(out/'build_source.py').write_bytes(source.read_bytes())
 flow.OUT=out
 log=flow.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
 if not drc or int(drc[1]) or (out/'gds_warnings.feedback').read_text() or re.search(r'\d+ problems occurred',log):raise RuntimeError(log[-5000:])
 ref='.subckt reference '+' '.join(PORTS)+'\n'+''.join(f'X{name} '+' '.join(nets)+f' {family}_03v3 w={w}u l={length}u\n' for name,family,w,length,nets in DEVICES)+'.ends\n';(out/'reference.spice').write_text(ref)
 lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference','/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(out/'netgen.log').write_text(lvs)
 if 'Circuits match uniquely' not in lvs:raise RuntimeError(lvs[-3000:])
 caplog=flow.magic(f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog)
 if (out/'warnings.feedback').read_text() or (out/'capacitance_warnings.feedback').read_text():raise ValueError('Extraction feedback unresolved')
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True,exist_ok=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference','/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(rd/'netgen.log').write_text(rlvs)
 if not rdr or int(rdr[1]) or 'Circuits match uniquely' not in rlvs or (rd/'roundtrip.feedback').read_text():raise RuntimeError('GDS readback failed\n'+readlog[-1800:]+'\n'+rlvs[-1800:])
 files=[out/(cell+x) for x in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','generation.log','extraction.log','netgen.log','reference.spice','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']];roundfiles=[rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]
 q={'cell':cell,'ports':PORTS,'magic_drc_count':0,'drc_style':'drc(full)','full_cell_selected_and_catchup':True,'lvs_unique':True,'gds_export_feedback':'','gds_roundtrip_lvs_unique':True,'gds_roundtrip_drc_count':0,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],'capacitance_count':len(re.findall(r'(?m)^C\S+',(out/(cell+'_cap.spice')).read_text())),'original_views_preserved':True,'mos_count':7,'compact_comparator_devices':True,'physical_state_accepted':False,'full_chip_accepted':False,'scope':'Seven-MOS small NF-input differential preamplifier/threshold candidate; native minimum input dimensions, separate rail/body taps. Ground shields separate long signal routes; same transistor topology/dimensions. Input loading, trip offset, bias switching/kickback and mismatch remain unqualified. Explicit body taps, spaced real contacts/vias, full-cell DRC and exported-GDS readback DRC/LVS. Capacitance extraction only, no interconnect resistance, compensated stability, bias generator, noise, full read/restore, PLIF or chip/service acceptance.','sha256':{f.name:digest(f) for f in files},'input_sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in pcells},'gds_roundtrip_sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in roundfiles}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'gds_roundtrip_lvs_unique':True},indent=2))
if __name__=='__main__':main()
