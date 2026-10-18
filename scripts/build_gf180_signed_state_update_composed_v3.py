"""Place and route the extracted signed injector and native state/update cell as one parent."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_signed_state_update_composed_v3';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);flow.OUT=out;files={Path(__file__)};children={};geometry={}
 specs=[('inject','gf180_signed_weight_charge_parent_v2',0,0),('state','gf180_nf_state_update_aux_overlap',800000,0)]
 for inst,name,dx,dy in specs:
  d=flow.BASE/'layout'/name;qpath=d/'qualification.json';q=json.loads(qpath.read_text());files.add(qpath);assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'];children[name]=(d,q)
  for key in ('sha256','input_sha256','gds_roundtrip_sha256'):
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else flow.ROOT/n;assert sha(f)==h,n;files.add(f)
    if f.suffix=='.mag':geometry.setdefault(f.stem,set()).add(f)
 signed_ports=['MAG_DATA','WRITE','WRITEB','ARM','ARMB','BIAS','VRESET','RAMP_BIAS','RAMP_CAS','VDD','VSS','SIGN','STATE','PARK','PPROGRAM','NPROGRAM','PCAS','NCAS','PULSE','PULSEB','POS','NEG']
 state_ports=['STATE','AUX','DATA','WRITE','WRITEB','AUXRESET','BETA','AUXREF','VCM','VSS','VDD']
 maps={'gf180_signed_weight_charge_parent_v2':{p:('VCM' if p=='PARK' else p) for p in signed_ports},'gf180_nf_state_update_aux_overlap':{p:p for p in state_ports}}
 ports=['MAG_DATA','WRITE','WRITEB','ARM','ARMB','BIAS','VRESET','RAMP_BIAS','RAMP_CAS','VDD','VSS','SIGN','STATE','PPROGRAM','NPROGRAM','PCAS','NCAS','PULSE','PULSEB','POS','NEG','DATA','AUX','AUXRESET','BETA','AUXREF','VCM']
 tracks={net:220000+10000*i for i,net in enumerate(ports)};layers={};uses=[]
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via4(x,y):
  rect('metal4',(x-120,y-120,x+120,y+120));rect('metal5',(x-40,y-40,x+40,y+40));rect('via4',(x-28,y-28,x+28,y+28))
 pin_sources=[]
 for inst,name,dx,dy in specs:
  d,q=children[name];bbox=[round(v/.005) for v in q['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 {dy}','box '+' '.join(map(str,bbox))]
  txt=(d/(name+'.mag')).read_text(encoding='ascii');labs=re.findall(r'^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',txt,re.M)
  expected=set(maps[name]);assert {a[-1] for a in labs}==expected,(name,{a[-1] for a in labs},expected)
  for i,(layer,x1,y1,x2,y2,pin) in enumerate(labs):
   net=maps[name][pin];pin_sources.append((inst,name,dx,dy,layer,int(x1),int(y1),int(x2),int(y2),net,i))
 # One isolated M4 riser per child pin; M5 handles lateral access and top-level trunks.
 for idx,(inst,name,dx,dy,layer,x1,y1,x2,y2,net,local_i) in enumerate(pin_sources):
  px=dx+(x1+x2)//2;py=dy+(y1+y2)//2;rx=(-100000-idx*1600 if name=='gf180_signed_weight_charge_parent_v2' else 780000-idx*1600);ty=tracks[net]
  if layer=='metal4':via4(px,py)
  elif layer=='metal5':via4(px,py)
  else:raise AssertionError((name,layer,net))
  rect('metal5',(min(px,rx)-40,py-40,max(px,rx)+40,py+40));via4(rx,py)
  rect('metal4',(rx-80,min(py,ty),rx+80,max(py,ty)+1));via4(rx,ty)
  rect('metal5',(min(-200000,rx),ty-60,max(-200000,rx),ty+60))
 # Top-level pads and continuous M5 net trunks.
 pin_boxes={}
 for i,net in enumerate(ports,1):
  ty=tracks[net];rect('metal5',(-200120,ty-60,1000000,ty+60));b=(-200040,ty-20,-200000,ty+20);pin_boxes[net]=b
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 for layer,boxes in layers.items():lines +=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines +=['<< labels >>']
 for i,net in enumerate(ports,1):lines +=[f'rlabel metal5 s '+' '.join(map(str,pin_boxes[net]))+f' 4 {net}',f'port {i} nsew']
 lines +=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 visited=set();views=[]
 def visit(name):
  if name in visited:return
  assert name in geometry and len(geometry[name])==1,name;p=next(iter(geometry[name]))
  for child in re.findall(r'^use\s+(\S+)\s+',p.read_text(),re.M):visit(child)
  visited.add(name);views.append(p)
 for _,name,_,_ in specs:visit(name)
 preload=''.join('load /workspace/'+p.with_suffix('').relative_to(flow.ROOT).as_posix()+'\n' for p in views)
 log=flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert drc and int(drc[1])==0 and not (out/'warnings.feedback').read_text() and not (out/'gds_warnings.feedback').read_text(),log[-3000:]
 # Compose a hierarchy-aware independent LVS reference from the two qualified child netlists.
 ref='';orders={}
 for _,name,_,_ in specs:
  d,_=children[name];sub=name;sp=d/(name+'.spice');txt=sp.read_text(encoding='ascii');order=re.search(r'(?m)^\.subckt\s+'+re.escape(sub)+r'\s+([^\n]+)',txt.replace('\n+',' '));assert order,name;orders[name]=order.group(1).split();ref+=txt+'\n'
 ref+='.subckt reference '+' '.join(ports)+'\n'
 for inst,name,_,_ in specs:
  ref+='X'+inst+' '+' '.join(maps[name][p] for p in orders[name])+' '+name+'\n'
 ref+='.ends reference\n';(out/'reference.spice').write_text(ref,encoding='ascii')
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-2500:]
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdrc=re.search(r'Total DRC errors found:\s*(\d+)',readlog);rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'roundtrip_lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdrc and int(rdrc[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1500:]+'\n'+rlvs[-2000:]
 q={'cell':cell,'ports':ports,'children':[n for _,n,_,_ in specs],'shared_state_node':'STATE','sign_logic_contract':'SIGN low selects positive; SIGN at VDD selects negative','magic_drc_count':0,'lvs_unique':True,'gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[round(int(v)*.005,4) for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'scope':'Physically placed/routed parent combining the qualified signed injector and state/update cell. Analog controls remain top-level pins. Does not include the per-bank scale-source cell, weight map, PLIF threshold/reset/adaptation, density, service or full-chip approval.','sha256':{p.name:sha(p) for p in [out/(cell+'.mag'),out/(cell+'.gds'),out/(cell+'.spice'),out/(cell+'_cap.spice'),out/'build_source.py',out/'extraction.log',out/'reference.spice',out/'netgen.log',out/'capacitance_extraction.log',out/'warnings.feedback',out/'gds_warnings.feedback',out/'capacitance_warnings.feedback']},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/'readback.log',rd/'netgen.log',rd/'roundtrip.spice',rd/'roundtrip.feedback']}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'lvs_unique':True},indent=2))

if __name__=='__main__':main()


