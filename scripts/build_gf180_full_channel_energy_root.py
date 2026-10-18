"""Connect resident age/amplitude, native triangle, amplitude buffer and native product."""
from pathlib import Path
import hashlib,json,re,argparse
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--channels',type=int,choices=[64,128],required=True);a=ap.parse_args();channels=a.channels;cell=f'gf180_energy_mean_root{channels}_v1';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);files={Path(__file__)};children={};geometry={};cache_changes=[]
 unit='gf180_two_channel_energy_root_v1';mim='gf180_mim_5x5_ports_routed';names=[unit]
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
 ports=[p+str(i) for i in range(channels) for p in ['IN_P','IN_N']]+['VBASE','ROOT','VDD','VSS'];instances=[]
 for i in range(channels//2):
  mapping={'A_P':'IN_P'+str(2*i),'A_N':'IN_N'+str(2*i),'B_P':'IN_P'+str(2*i+1),'B_N':'IN_N'+str(2*i+1),'VBASE':'VBASE','ROOT':'ROOT','VDD':'VDD','VSS':'VSS'};instances.append(('pair'+str(i),unit,280000*(i%8),60000*(i//8),mapping))
 nets=ports;tracks={n:(channels//16)*60000+20000+640*i for i,n in enumerate(nets)};layers={};uses=[]
 # Reserve bbox and routing escape envelopes before any geometry mutation.
 intervals=[]
 for inst,name,dx,dy,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];pin_count=len(children[name][1]['ports']);left=dx+bbox[0]-2000-400*(pin_count-1)-120-(dy//60000)*5000;right=dx+bbox[2];bottom=dy+bbox[1];top=dy+bbox[3]
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
   px=dx+(int(x1)+int(x2))//2;y=dy+(int(y1)+int(y2))//2;x=dx+bbox[0]-2000-400*i-(dy//60000)*5000;dest=tracks[mapping[pin]]
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
 caplog=flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');(out/'capacitance_extraction.log').write_text(caplog);assert not (out/'warnings.feedback').read_text() and not (out/'capacitance_warnings.feedback').read_text()
 rd=flow.BASE/'verification/gds_roundtrip'/cell;rd.mkdir(parents=True);flow.OUT=rd
 readlog=flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');(rd/'readback.log').write_text(readlog);rdr=re.search(r'Total DRC errors found:\s*(\d+)',readlog)
 rlvs=flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(rlvs);assert rdr and int(rdr[1])==0 and 'Circuits match uniquely' in rlvs and not (rd/'roundtrip.feedback').read_text(),readlog[-1000:]+'\n'+rlvs[-2000:]
 actual=re.search(r'(?m)^\.subckt[ \t]+'+cell+r'[ \t]*([^\n]*)',(rd/'roundtrip.spice').read_text().replace('\n+',' '));assert actual and actual[1].split()==ports,'GDS parent ports missing'
 outputs=[out/(cell+s) for s in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
 q={'cell':cell,'generated_cache_changes':cache_changes,'ports':ports,'magic_drc_count':0,'lvs_unique':True,'actual_source_ports_verified':True,'actual_gds_ports_verified':True,'drc_style':'drc(full)','gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'','bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':7*channels,'native_resistor_count':0,'native_mim_count':0,'target_float_channel':None,'channel_count':channels,'native_quadratic_kernel_count':channels,'native_root_receiver_count':channels,'scope':'Native full-channel energy mean/root reduction at actual model adaptation widths64 or128. Each logical channel has one6MOS differential energy kernel and one matched native PF diode receiver; all channel outputs and all receivers connect to common ROOT, preserving current-sum divided by receiver count before the native nonlinear root transfer. Reuses qualified two-channel root leaf, not an ideal behavioral reduction. Actual native topology and full parent interconnect require new DC/transient characterization; input differential formatter interfaces remain external and native nonideal RMS gain/offset/epsilon remain unaccepted. Geometry is a characterization reducer, not final optimized population replication area. No complete all-channel candidate formatter connection, full adaptation/model/5ms/full-chip acceptance','complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'sha256':{p.name:sha(p) for p in outputs},'input_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in sorted(files)},'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():sha(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
 (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'mos_count':7*channels,'native_resistor_count':0,'native_mim_count':0},indent=2))
if __name__=='__main__':main()
