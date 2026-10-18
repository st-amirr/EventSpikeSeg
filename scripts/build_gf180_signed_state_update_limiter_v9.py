"""Add physically routed phase-gated low/high rail switches to the qualified state-update parent."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_signed_state_update_limiter_v9';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);flow.OUT=out;files={Path(__file__)};children={};geometry={}
 specs=[('parent','gf180_signed_state_update_composed_v8',0,0),('clamp_lo','gf180_fixed_body_tg_quarter_shorttracks',720000,0),('clamp_hi','gf180_fixed_body_tg_quarter_shorttracks',730000,0)]
 for inst,name,dx,dy in specs:
  d=flow.BASE/'layout'/name;qpath=d/'qualification.json';q=json.loads(qpath.read_text());files.add(qpath);assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique'];children[name]=(d,q)
  for key in ('sha256','input_sha256','gds_roundtrip_sha256'):
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else flow.ROOT/n;assert sha(f)==h,n;files.add(f)
    if f.suffix=='.mag':geometry.setdefault(f.stem,set()).add(f)
 parent_ports=children['gf180_signed_state_update_composed_v8'][1]['ports']
 ports=parent_ports+['VRAIL_LO','VRAIL_HI','LIMIT_LO','LIMIT_LOB','LIMIT_HI','LIMIT_HIB']
 def pinmap(inst,name):
  if inst=='parent':return {p:p for p in parent_ports}
  return {'A':'STATE','B':'VRAIL_LO' if inst=='clamp_lo' else 'VRAIL_HI','EN':'LIMIT_LO' if inst=='clamp_lo' else 'LIMIT_HI','ENB':'LIMIT_LOB' if inst=='clamp_lo' else 'LIMIT_HIB','VSS':'VSS','VDD':'VDD'}
 tracks={net:300000+2500*i for i,net in enumerate(ports)};layers={};uses=[]
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via4(x,y):
  rect('metal4',(x-90,y-90,x+90,y+90));rect('metal5',(x-80,y-70,x+80,y+70));rect('via4',(x-28,y-28,x+28,y+28))
 def via3(x,y):
  rect('metal3',(x-90,y-90,x+90,y+90));rect('metal4',(x-80,y-70,x+80,y+70));rect('via3',(x-28,y-28,x+28,y+28));via4(x,y)
 pin_sources=[]
 for inst,name,dx,dy in specs:
  d,q=children[name];bbox=[round(v/.005) for v in q['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 {dy}','box '+' '.join(map(str,bbox))]
  txt=(d/(name+'.mag')).read_text(encoding='ascii');labs=re.findall(r'^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',txt,re.M)
  maps_i=pinmap(inst,name);expected=set(maps_i);assert {a[-1] for a in labs}==expected,(name,{a[-1] for a in labs},expected)
  for i,(layer,x1,y1,x2,y2,pin) in enumerate(labs):
   net=maps_i[pin];pin_sources.append((inst,name,dx,dy,layer,int(x1),int(y1),int(x2),int(y2),net,i))
 # One isolated M4 riser per child pin; M5 handles lateral access and top-level trunks.
 for idx,(inst,name,dx,dy,layer,x1,y1,x2,y2,net,local_i) in enumerate(pin_sources):
  px=dx+(x1+x2)//2;py=dy+(y1+y2)//2;rx=(-300000-idx*1700 if inst=='parent' else 750000+idx*2500);ty=tracks[net]
  if layer=='metal3':via3(px,py)
  elif layer in ('metal4','metal5'):via4(px,py)
  else:raise AssertionError((name,layer,net))
  rect('metal5',(min(px,rx)-50,py-50,max(px,rx)+50,py+50));via4(rx,py)
  rect('metal4',(rx-80,min(py,ty),rx+80,max(py,ty)+1));via4(rx,ty)
  rect('metal5',(min(-400000,rx),ty-60,max(-400000,rx),ty+60))
 # Top-level pads and continuous M5 net trunks.
 pin_boxes={}
 for i,net in enumerate(ports,1):
  ty=tracks[net];rect('metal5',(-400120,ty-60,900000,ty+60));b=(-400040,ty-20,-400000,ty+20);pin_boxes[net]=b
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
 # Compose an independent LVS reference from the existing parent and two TG children.
 ref='';orders={};included=set()
 for _,name,_,_ in specs:
  d,_=children[name];sub=name;sp=d/(name+'.spice');txt=sp.read_text(encoding='ascii');order=re.search(r'(?m)^\.subckt\s+'+re.escape(sub)+r'\s+([^\n]+)',txt.replace('\n+',' '));assert order,name;orders[name]=order.group(1).split()
  if name not in included:ref+=txt+'\n';included.add(name)
 ref+='.subckt reference '+' '.join(ports)+'\n'
 for inst,name,_,_ in specs:
  maps_i=pinmap(inst,name);ref+='X'+inst+' '+' '.join(maps_i[p] for p in orders[name])+' '+name+'\n'
 ref+='.ends reference\n';(out/'reference.spice').write_text(ref,encoding='ascii')
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-2500:]
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdrc=re.search(r'Total DRC errors found:\s*(\d+)',readlog);rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'roundtrip_lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdrc and int(rdrc[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1500:]+'\n'+rlvs[-2000:]
 q={'cell':cell,'ports':ports,'children':[n for _,n,_,_ in specs],'instances':['parent','clamp_lo','clamp_hi'],'range_limiter':{'low_rail_net':'VRAIL_LO','high_rail_net':'VRAIL_HI','low_enable_net':'LIMIT_LO','low_enable_bar_net':'LIMIT_LOB','high_enable_net':'LIMIT_HI','high_enable_bar_net':'LIMIT_HIB','control_is_external':True},'shared_state_node':'STATE','sign_logic_contract':'SIGN low selects positive; SIGN at VDD selects negative','magic_drc_count':0,'lvs_unique':True,'gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[round(int(v)*.005,4) for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'scope':'Physically placed/routed parent combining the qualified signed injector/state-update parent with two qualified quarter-size TG limiter switches. Rail values and complementary phase controls are external pins. Does not include physical range comparators, comparator sequencing, weight map, PLIF threshold/reset/adaptation, density, service or full-chip approval. Combined extracted transient qualification is required; child evidence alone is insufficient.','sha256':{p.name:sha(p) for p in [out/(cell+'.mag'),out/(cell+'.gds'),out/(cell+'.spice'),out/(cell+'_cap.spice'),out/'build_source.py',out/'extraction.log',out/'reference.spice',out/'netgen.log',out/'capacitance_extraction.log',out/'warnings.feedback',out/'gds_warnings.feedback',out/'capacitance_warnings.feedback']},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/'readback.log',rd/'netgen.log',rd/'roundtrip.spice',rd/'roundtrip.feedback']}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'lvs_unique':True},indent=2))

if __name__=='__main__':main()





