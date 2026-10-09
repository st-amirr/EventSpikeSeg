"""Build native PF0.5um/L1um primitive for the shared cascode source."""
import argparse,hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 nw,pw=.5,.5
 cell='gf180_source_pf05_l1_fullroute';out=flow.BASE/'layout'/cell;source=Path(__file__);out.mkdir(parents=True,exist_ok=True);flow.OUT=out
 if (out/'qualification.json').exists():raise ValueError('Preserve qualified view')
 genout=out/'source_generation_spaced';genout.mkdir(parents=True,exist_ok=True);flow.OUT=genout
 gen=flow.magic(f'dict set gf180mcu::ruleset gate_to_polycont 0.50\nload tg_raw\nmagic::gencell gf180mcu::pfet_03v3 p -spice w {nw}u l 1u nf 1 guard 0 botc 0 topc 1\nwriteall force\nquit -noprompt\n');(out/'generation.log').write_text(gen);layers={};pcells=[];tracks={'D':6000,'G':6480,'S':6240,'VDD':6960}
 def rect(layer,box):layers.setdefault(layer,[]).append(tuple(box))
 def via1(x,y):
  for layer in ['metal1','metal2']:rect(layer,(x-38,y-38,x+38,y+38))
  rect('via1',(x-26,y-26,x+26,y+26))
 def via2(x,y):
  for layer in ['metal2','metal3']:rect(layer,(x-40,y-40,x+40,y+40))
  rect('via2',(x-28,y-28,x+28,y+28))
 for family,w,dx,supply,tapx in [('pfet',pw,0,'VDD',1200)]:
  files=[p for p in genout.glob(family+'_03v3_*.mag') if f'string parameters w {float(w)} l 1.0 ' in p.read_text() and 'guard 0' in p.read_text() and 'botc 0' in p.read_text()]
  if not files:raise ValueError('Requested unguarded top-contact PCell absent')
  pc=max(files,key=lambda p:p.stat().st_mtime);pcells.append(pc);shape=rectangles(pc,0)
  for layer,boxes in shape.items():
   for x1,y1,x2,y2 in boxes:rect(layer,(x1+dx,y1,x2+dx,y2))
  gate='G'
  contacts=shape['polycontact'];gx=(contacts[0][0]+contacts[0][2])//2+dx;gy=(contacts[0][1]+contacts[0][3])//2;lift=(gy+100+1)//2*2
  rect('metal1',(gx-38,gy-38,gx+38,lift+38));via1(gx,lift);rect('metal2',(gx-38,lift-38,gx+38,tracks[gate]+40));via2(gx,tracks[gate])
  for side,column,net in [(1,dx+500,'D'),(-1,dx-500,'S')]:
   diffusion_contacts=shape['ndiffc' if family=='nfet' else 'pdiffc'];contact_box=sorted(diffusion_contacts,key=lambda b:b[0])[0 if side<0 else -1];x=(contact_box[0]+contact_box[2])//2+dx;cy=(contact_box[1]+contact_box[3])//2
   via1(x,cy);rect('metal2',(min(x,column)-38,cy-38,max(x,column)+38,cy+38));rect('metal2',(column-38,cy-38,column+38,tracks[net]+40));via2(column,tracks[net])
  tx=dx+tapx;ty=-600
  if family=='nfet':rect('pwell',(tx-180,ty-200,tx+180,ty+200));diff='psubdiff';contact='psubdiffcont'
  else:rect('nwell',(dx-300,-1000,dx+1400,500));diff='nsubdiff';contact='nsubdiffcont'
  rect(diff,(tx-36,ty-100,tx+36,ty+100));rect(contact,(tx-23,ty-87,tx+23,ty+87));rect('metal1',(tx-38,ty-98,tx+38,ty+98));via1(tx,ty);column=dx-1000;rect('metal2',(min(tx,column)-38,ty-38,max(tx,column)+38,ty+38));rect('metal2',(column-38,ty-38,column+38,tracks[supply]+40));via2(column,tracks[supply])
 for track in tracks.values():rect('metal3',(-1600,track-40,6000,track+40))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for layer,boxes in layers.items():lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(net,y) in enumerate(tracks.items(),1):lines+=[f'rlabel metal3 s -1560 {y-20} -1520 {y+20} 4 {net}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');(out/'build_source.py').write_bytes(source.read_bytes())
 flow.OUT=out
 log=flow.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
 if not drc or int(drc[1]) or (out/'gds_warnings.feedback').read_text() or re.search(r'\d+ problems occurred',log):raise RuntimeError(log[-5000:])
 ref='.subckt reference D G S VDD\nXp D G S VDD pfet_03v3 w=.5u l=1u\n.ends\n';(out/'reference.spice').write_text(ref)
 lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference','/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(out/'netgen.log').write_text(lvs)
 if 'Circuits match uniquely' not in lvs:raise RuntimeError(lvs[-3000:])
 caplog=flow.magic(f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog)
 if (out/'warnings.feedback').read_text() or (out/'capacitance_warnings.feedback').read_text():raise ValueError('Extraction feedback unresolved')
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True,exist_ok=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference','/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out']);(rd/'netgen.log').write_text(rlvs)
 if not rdr or int(rdr[1]) or 'Circuits match uniquely' not in rlvs or (rd/'roundtrip.feedback').read_text():raise RuntimeError('GDS readback failed\n'+readlog[-1800:]+'\n'+rlvs[-1800:])
 files=[out/(cell+x) for x in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','generation.log','extraction.log','netgen.log','reference.spice','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']];roundfiles=[rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]
 q={'cell':cell,'ports':list(tracks),'magic_drc_count':0,'drc_style':'drc(full)','full_cell_selected_and_catchup':True,'lvs_unique':True,'gds_export_feedback':'','gds_roundtrip_lvs_unique':True,'gds_roundtrip_drc_count':0,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],'capacitance_count':len(re.findall(r'(?m)^C\S+',(out/(cell+'_cap.spice')).read_text())),'original_views_preserved':True,'nf_width_um':0,'pf_width_um':pw,'length_um':1.0,'physical_state_accepted':False,'full_chip_accepted':False,'scope':f'PF{pw}um,L1um source transistor with official top-contact unguarded PCells, explicit supply-connected well tap, spaced M2 fanout and mask-exportable vias. Full-cell drc(full)/catchup, unique LVS, empty GDS export feedback, GDS reimport full DRC/LVS and capacitance extraction. New routing/body layout changes capacitance and requires new phase/module simulations; no old-performance/noise/5ms or chip acceptance.','sha256':{f.name:digest(f) for f in files},'input_sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in pcells},'gds_roundtrip_sha256':{f.relative_to(flow.ROOT).as_posix():digest(f) for f in roundfiles}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'gds_roundtrip_lvs_unique':True},indent=2))
if __name__=='__main__':main()
