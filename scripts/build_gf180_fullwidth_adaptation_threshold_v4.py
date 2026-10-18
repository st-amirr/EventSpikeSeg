"""Connect resident age/amplitude, native triangle, amplitude buffer and native product."""
from pathlib import Path
import hashlib,json,re,argparse,subprocess
import probe_gf180_mos_gate_cap as flow

# Full128 has3099MOS versus measured full64v1 1563MOS/144s source export.
# First128 physical export bound360s (2x measured144s plus25percent margin),2CPU/2GB.
# No128 native transient runtime extension is implied.
# Bound subsequent physical commands180s,2CPU/2GB; reuse source EXT for cap export.
def run_bounded(args,stdin=None):
 cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2']+(['-i'] if stdin is not None else [])+['--volume',f'{flow.ROOT}:/workspace','--workdir','/workspace/'+flow.OUT.relative_to(flow.ROOT).as_posix(),'--entrypoint','timeout','eventspikeseg:analog-gf180-layout','360',*args]
 p=subprocess.run(cmd,input=stdin,capture_output=True,text=True,timeout=375);log=p.stdout+p.stderr
 if p.returncode:raise RuntimeError(log[-3000:])
 return log
flow.run=run_bounded

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--channels',type=int,choices=[128],required=True);channels=ap.parse_args().channels;cell=f'gf180_adaptation_sum{channels}_threshold_v2';out=flow.BASE/'layout'/cell;assert not out.exists() or not any(out.iterdir());out.mkdir(parents=True,exist_ok=True);files={Path(__file__)};children={};geometry={};cache_changes=[]
 raw='gf180_adaptation_sum8_v1';adder='gf180_buffered_centered_adder_v1';threshold='gf180_shared_adaptive_threshold_v1';mim='gf180_mim_5x5_ports_routed';names=[raw,threshold]+([adder] if channels==128 else [])
 for name in names:
  d=flow.BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback'];children[name]=(d,q)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    f=d/n if key=='sha256' else flow.ROOT/n;actual=sha(f)
    if actual!=h:
     assert f.suffix=='.ext',n
     cache_changes.append({'path':f.relative_to(flow.ROOT).as_posix(),'qualified_sha256':h,'current_sha256':actual,'reason':'Generated cache rewritten by parent extraction; source geometry and all consumed netlists remain checked.'})
    files.add(f)
    if f.suffix=='.mag':geometry.setdefault(f.stem,set()).add(f)
 ports=[f'PENALTY{i}' for i in range(channels)]+['BASE','VCOM','VMIN','VMAX','TOTAL','UNCLIPPED','EFFECTIVE_THRESHOLD','BIAS','VDD','VSS'];chunks=channels//8;cols=2 if channels==64 else 4
 nets=ports+[f'CHUNK{i}' for i in range(chunks)]+(['HALF0','HALF1'] if channels==128 else []);tracks={p:1000000+640*i for i,p in enumerate(nets)};layers={};uses=[];instances=[]
 for i in range(chunks):instances.append((f'chunk{i}',raw,4000000*(i%cols),180000*(i//cols),{**{f'PENALTY{j}':f'PENALTY{8*i+j}' for j in range(8)},'TOTAL':f'CHUNK{i}','VCOM':'VCOM','BIAS':'BIAS','VDD':'VDD','VSS':'VSS'}))
 if channels==64:instances.append(('sum64',raw,0,720000,{**{f'PENALTY{j}':f'CHUNK{j}' for j in range(8)},'TOTAL':'TOTAL','VCOM':'VCOM','BIAS':'BIAS','VDD':'VDD','VSS':'VSS'}))
 else:
  for h in range(2):instances.append((f'half{h}',raw,4000000*h,720000,{**{f'PENALTY{j}':f'CHUNK{8*h+j}' for j in range(8)},'TOTAL':f'HALF{h}','VCOM':'VCOM','BIAS':'BIAS','VDD':'VDD','VSS':'VSS'}))
  instances.append(('sum128',adder,8000000,720000,{'A':'HALF0','B':'HALF1','VCOM':'VCOM','SUM':'TOTAL','BIAS':'BIAS','VDD':'VDD','VSS':'VSS'}))
 instances.append(('threshold',threshold,4000000 if channels==64 else 12000000,720000,{p:('TOTAL' if p=='TOTAL_PENALTY' else p) for p in children[threshold][1]['ports']}))
 # Reserve bbox and routing escape envelopes before any geometry mutation.
 intervals=[]
 for inst,name,dx,dy,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];pin_count=len(children[name][1]['ports']);left=dx-60000-400*(pin_count-1)-120-(dy//180000)*16000;right=dx+bbox[2];bottom=dy+bbox[1];top=dy+bbox[3]
  assert all(right<lo or left>hi or top<bot or bottom>high for lo,hi,bot,high,_ in intervals),(inst,left,right,intervals)
  intervals.append((left,right,bottom,top,inst))
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:
   pad=120 if layer=='metal4' else 40;rect(layer,(x-pad,y-pad,x+pad,y+pad))
  rect(cut,(x-28,y-28,x+28,y+28))
 for inst,name,dx,dy,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 {dy}','box '+' '.join(map(str,bbox))]
  text=(children[name][0]/(name+'.mag')).read_text()
  labels=re.findall(r'^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',text,re.M)
  assert set(mapping)=={r[-1] for r in labels}
  for i,(layer,x1,y1,x2,y2,pin) in enumerate(labels):
   assert layer in ['metal3','metal4','metal5'] or (name==mim and pin=='VSS' and layer=='metal1'), (name,pin,layer)
   if mapping[pin] not in tracks:continue
   px=dx+(int(x1)+int(x2))//2;y=dy+(int(y1)+int(y2))//2;x=dx-60000-400*i-(dy//180000)*16000;dest=tracks[mapping[pin]]
   if name==mim:
    if pin=='P':
     x=px
     for lay in ['metal4','metal5']:rect(lay,(x-40,y-40,x+40,y+40))
     rect('via4',(x-28,y-28,x+28,y+28))
    elif pin=='M':
     x=dx-1400;rect('metal4',(x-40,y-40,px+40,y+40))
    else:
     assert pin=='VSS';x=dx-2000
     via('metal1','metal2','via1',px,y);via('metal2','metal3','via2',px,y);rect('metal3',(min(x,px)-40,y-40,max(x,px)+40,y+40));via('metal3','metal4','via3',x,y)
   else:
    if layer=='metal3':
     rect('metal3',(min(x,px)-40,y-40,max(x,px)+40,y+40));via('metal3','metal4','via3',x,y)
    else:
     assert layer=='metal5'
     rect('metal5',(min(x,px)-60,y-60,max(x,px)+60,y+60));via('metal4','metal5','via4',x,y)
   rect('metal4',(x-40,y-40,x+40,dest+40));via('metal4','metal5','via4',x,dest)
 for net,y in tracks.items():
  xs=[b[0] for b in layers.get('via4',[]) if abs((b[1]+b[3])//2-y)<1]+[b[2] for b in layers.get('via4',[]) if abs((b[1]+b[3])//2-y)<1]
  rect('metal5',(min(xs+([-18000] if net in ports else []))-60,y-60,max(xs+([-17900] if net in ports else []))+60,y+60))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 pins={}
 for net in ports:
  y=tracks[net];layer,b='metal5',(-17940,y-20,-17900,y+20);rect(layer,b);pins[net]=(layer,b)
 for layer,boxes in layers.items():lines+=['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,net in enumerate(ports,1):layer,b=pins[net];lines +=[f'rlabel {layer} s '+' '.join(map(str,b))+f' 4 {net}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii');(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 visited=set();views=[]
 def visit(name):
  if name in visited:return
  assert name in geometry and len(geometry[name])==1,name;p=next(iter(geometry[name]))
  for child in re.findall(r'^use\s+(\S+)\s+',p.read_text(),re.M):visit(child)
  visited.add(name);views.append(p)
 for name in names:visit(name)
 preload=''.join('load /workspace/'+p.with_suffix('').relative_to(flow.ROOT).as_posix()+'\n' for p in views);flow.OUT=out
 log=flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log);drc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert drc and int(drc[1])==0 and not (out/'gds_warnings.feedback').read_text() and not re.search(r'\d+ problems occurred',log),log[-5000:]
 actual=re.search(r'(?m)^\.subckt[ \t]+'+cell+r'[ \t]*([^\n]*)',(out/(cell+'.spice')).read_text().replace('\n+',' '));assert actual and actual[1].split()==ports,'Physical parent ports missing'
 ref='';orders={}
 for name,(d,q) in children.items():
  fqpath=d/'flat_cap_qualification.json'
  if fqpath.exists():
   fq=json.loads(fqpath.read_text());assert fq['flat_extraction_completed'] and fq['flat_lvs_unique'];files.add(fqpath);sub=fq['flat_subcircuit'];p=d/(sub+'.spice')
  else:sub=name;p=d/(name+'.spice')
  files.add(p);txt=p.read_text();orders[name]=re.search(r'(?m)^\.subckt\s+'+sub+r'\s+([^\n]+)',txt.replace('\n+',' '))[1].split();ref+=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(sub)+r'(?![A-Za-z0-9_])',name,txt)+'\n'
 ref+='.subckt reference '+' '.join(ports)+'\n'
 for inst,name,dx,dy,mapping in instances:ref+='X'+inst+' '+' '.join(mapping[p] for p in orders[name])+' '+name+'\n'
 ref+='.ends\n';(out/'reference.spice').write_text(ref)
 setup='/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';lvs=flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(lvs);assert 'Circuits match uniquely' in lvs,lvs[-3000:]
 caplog=flow.magic(preload+f'load {cell}\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'warnings.feedback').read_text() and not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1000:]+'\n'+rlvs[-2000:]
 actual=re.search(r'(?m)^\.subckt[ \t]+'+cell+r'[ \t]*([^\n]*)',(rd/'roundtrip.spice').read_text().replace('\n+',' '));assert actual and actual[1].split()==ports,'GDS parent ports missing'
 outputs=[out/(cell+s) for s in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
 q={'cell':cell,'generated_cache_changes':cache_changes,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'actual_source_ports_verified':True,'actual_gds_ports_verified':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':24*channels+27,'native_resistor_count':4*channels,'native_mim_count':12*channels,'target_float_channel':None,'feature_channels':channels,'scope':f'Revision2 uses fixed column-origin escape lanes with80um row stride independent of child bbox: v1 had four M4 spacing violations where threshold and reducer bbox differences shifted lanes toward each other. Source/GDS v1 retained,never accepted. Native full{channels}feature adaptation SUM followed by one buffered base addition and threshold clamp. Actual {channels-1} centered adders plus one51MOS final threshold path: {24*channels+27}MOS,{4*channels}R,{12*channels}MIM. Internal8way blocks are sum-only; no redundant per-chunk clipping or mean substitution. TOTAL=VCOM+sum of all{channels}per-feature deviations at one retinotopic pixel. Fixed channel ports preserve every feature contribution; grid placements are actual routed hierarchy. Final clipped threshold is intended for both decision and subtractive reset; native consumers,all resident product sources,RMS,autonomous control,trained voltage/range mapping and fullchip assembly remain unfinished. External master bias needs{3*(channels-1)+4}uA across actual references. Spaced research characterization grid is not compact per-pixel area. Fresh native source/flat/GDS and complete ground/coupling C qualification plus bounded module simulation required. No original-model accuracy or5ms population acceptance','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'mos_count':24*channels+27,'native_resistor_count':4*channels,'native_mim_count':12*channels},indent=2))
if __name__=='__main__':main()
