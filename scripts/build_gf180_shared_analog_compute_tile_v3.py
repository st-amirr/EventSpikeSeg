"""Build physical matched-replica feedback membrane read interface."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as flow

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_shared_analog_compute_tile_v3';out=flow.BASE/'layout'/cell;assert not out.exists();out.mkdir(parents=True);files={Path(__file__)};children={};geometry={};cache_changes=[]
 bank='gf180_row_staged_writeback_v2';reader='gf180_replica_feedback_reader_v3';mux='gf180_column_mux8_v2';compute='gf180_neuron_five_module_parent_v6';shift='gf180_candidate_penalty_subtractor_v2';reference='gf180_pmos_bias_reference_fullroute_v2';tg='gf180_fixed_body_tg_fullroute_quarter';nf='gf180_fixed_body_nf025_shorttracks';mim='gf180_mim_5x5_ports_routed';bigmim=None;names=[bank,reader,mux,compute,shift,reference,tg,nf,mim]
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
 bm={p:({'COMPUTE_OUT':'C_STATE','VCM':'SREF'}.get(p,p)) for p in children[bank][1]['ports']}
 cp={p:('COMPUTE_DATA' if p=='DATA' else 'CREF' if p=='VCM' else 'PARK_BIAS' if p=='PARK_BIAS' else p if p in ['VDD','VSS'] else 'C_'+p) for p in children[compute][1]['ports']}
 ports=[bm[p] for p in children[bank][1]['ports'] if p not in ['COMPUTE_OUT','BUFFERED','COMMIT_DATA']]+['CREF','INIT_DATA','INIT','INITB','RESTORE','RESTOREB','READ_ENABLE','READER_BIAS','UP_BIAS','DOWN_BIAS','PARK_BIAS']+[f'SEL{i}' for i in range(8)]+[cp[p] for p in children[compute][1]['ports'] if p not in ['DATA','VDD','VSS','VCM','PARK_BIAS']]
 assert len(set(ports))==len(ports)
 nets=[f'READOUT{i}' for i in range(8)]+['RAW_MUX','RECOV','BIAS','SREF','CREF','VDD','VSS','C_STATE','BUFFERED','COMMIT_DATA','IO_BIAS','COMPUTE_DATA','UP','PARK_BIAS','C_SENSE_REF','C_SENSE_OUT','C_SENSE_COMP','C_PARK_AZ','C_PARK_AZB'];tracks={n:160000+640*i for i,n in enumerate(nets)};layers={};uses=[];bankpins={}
 instances=[('bank',bank,0,bm),('mux',mux,1800000,{**{f'IN{i}':f'READOUT{i}' for i in range(8)},**{f'SEL{i}':f'SEL{i}' for i in range(8)},'OUT':'RAW_MUX','VDD':'VDD','VSS':'VSS'}),('reader',reader,2000000,{'RAW':'RAW_MUX','RECOV':'RECOV','NBIAS':'BIAS','PBIAS':'READER_BIAS','READ_EN':'READ_ENABLE','VCM':'SREF','VDD':'VDD','VSS':'VSS'}),('up',shift,2200000,{'CANDIDATE':'RECOV','PENALTY':'SREF','VCOM':'CREF','ADJUSTED':'UP','BIAS':'UP_BIAS','VDD':'VDD','VSS':'VSS'}),('compute',compute,2400000,cp),('down',shift,3200000,{'CANDIDATE':'BUFFERED','PENALTY':'CREF','VCOM':'SREF','ADJUSTED':'COMMIT_DATA','BIAS':'DOWN_BIAS','VDD':'VDD','VSS':'VSS'}),('restore',tg,3500000,{'A':'UP','B':'COMPUTE_DATA','EN':'RESTORE','ENB':'RESTOREB','VDD':'VDD','VSS':'VSS'}),('initialize',tg,3520000,{'A':'INIT_DATA','B':'COMPUTE_DATA','EN':'INIT','ENB':'INITB','VDD':'VDD','VSS':'VSS'}),('parkref',reference,3540000,{'BIAS':'PARK_BIAS','VDD':'VDD','VSS':'VSS'}),('autozero',tg,3560000,{'A':'C_SENSE_OUT','B':'C_SENSE_REF','EN':'C_PARK_AZ','ENB':'C_PARK_AZB','VDD':'VDD','VSS':'VSS'}),('dummy',nf,3580000,{'A':'C_SENSE_REF','B':'C_SENSE_REF','EN':'C_PARK_AZB','VSS':'VSS'})]
 for j in range(9):instances.append((f'refhold{j}',mim,3600000+6000*j,{'P':'C_SENSE_REF','M':'CREF','VSS':'VSS'}))
 instances.append(('sensecomp',mim,3660000,{'P':'C_SENSE_OUT','M':'C_SENSE_COMP','VSS':'VSS'}))

 # Reserve bbox and routing escape envelopes before any geometry mutation.
 intervals=[]
 for inst,name,dx,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];pin_count=len(children[name][1]['ports']);left=dx+bbox[0]-2000-400*(pin_count-1)-120;right=dx+bbox[2]
  right+=0
  assert all(right<lo or left>hi for lo,hi,_ in intervals),(inst,left,right,intervals)
  intervals.append((left,right,inst))
 def rect(layer,b):layers.setdefault(layer,[]).append(tuple(b))
 def via(lo,hi,cut,x,y):
  for layer in [lo,hi]:
   pad=120 if layer=='metal4' else 40;rect(layer,(x-pad,y-pad,x+pad,y+pad))
  rect(cut,(x-28,y-28,x+28,y+28))
 for inst,name,dx,mapping in instances:
  bbox=[round(v/.005) for v in children[name][1]['bbox_um']];uses +=[f'use {name} {inst}',f'transform 1 0 {dx} 0 1 0','box '+' '.join(map(str,bbox))]
  text=(children[name][0]/(name+'.mag')).read_text()
  labels=re.findall(r'^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)$',text,re.M)
  assert set(mapping)=={r[-1] for r in labels}
  for i,(layer,x1,y1,x2,y2,pin) in enumerate(labels):
   assert layer in ['metal1','metal2','metal3','metal4','metal5'], (name,pin,layer)
   px=dx+(int(x1)+int(x2))//2;y=(int(y1)+int(y2))//2;x=dx+bbox[0]-2000-400*i
   if name==bank:
    if mapping[pin] in ports:bankpins[mapping[pin]]=(layer,(dx+int(x1),int(y1),dx+int(x2),int(y2)))
    if not pin.startswith('READOUT') and pin not in ['BIAS','COMPUTE_OUT','BUFFERED','COMMIT_DATA','IO_BIAS','VCM','VDD','VSS']:continue
    dest=tracks[mapping[pin]]
    if pin.startswith('READOUT'):
     col=int(pin[-1]);low=-10000-640*col;x=-60000-640*col;rect('metal4',(px-40,low-40,px+40,y+40));via('metal4','metal5','via4',px,low);rect('metal5',(x-60,low-60,px+60,low+60));via('metal4','metal5','via4',x,low);y=low
    elif pin=='BIAS':
     x=22000;via('metal2','metal3','via2',px,y);rect('metal3',(px-40,y-40,x+40,y+40));via('metal3','metal4','via3',x,y)
    elif layer=='metal5':
     x=-30000-640*['COMPUTE_OUT','BUFFERED','COMMIT_DATA','IO_BIAS'].index(pin);rect('metal5',(x-60,y-60,px+60,y+60));via('metal4','metal5','via4',x,y)
    else:
     x={'VDD':-3000,'VSS':-3400,'VCM':-3800}[pin];via('metal2','metal3','via2',px,y);rect('metal3',(x-40,y-40,px+40,y+40));via('metal3','metal4','via3',x,y)
    rect('metal4',(x-40,y-40,x+40,dest+40));via('metal4','metal5','via4',x,dest);continue
   if mapping[pin] in ports:bankpins[mapping[pin]]=(layer,(dx+int(x1),int(y1),dx+int(x2),int(y2)))
   if mapping[pin] not in tracks:continue
   dest=tracks[mapping[pin]]
   if name in [mim,bigmim]:
    if pin=='P':
     x=px
     for lay in ['metal4','metal5']:rect(lay,(x-40,y-40,x+40,y+40))
     rect('via4',(x-28,y-28,x+28,y+28))
    elif pin=='M':
     x=dx-1400 if name==mim else dx+bbox[0]-1400;rect('metal4',(x-40,y-40,px+40,y+40))
    else:
     assert pin=='VSS';x=dx-2000 if name==mim else dx+bbox[0]-2400
     via('metal1','metal2','via1',px,y);via('metal2','metal3','via2',px,y);rect('metal3',(min(x,px)-40,y-40,max(x,px)+40,y+40));via('metal3','metal4','via3',x,y)
   else:
    if layer=='metal1':
     via('metal1','metal2','via1',px,y);via('metal2','metal3','via2',px,y);rect('metal3',(min(x,px)-40,y-40,max(x,px)+40,y+40));via('metal3','metal4','via3',x,y)
    elif layer=='metal4':
     assert name==mem and pin=='VCM';x=dx-1200;rect('metal4',(x-40,y-40,px+40,y+40))
    elif layer=='metal3':
     rect('metal3',(min(x,px)-40,y-40,max(x,px)+40,y+40));via('metal3','metal4','via3',x,y)
    else:
     assert layer=='metal5'
     rect('metal5',(min(x,px)-60,y-60,max(x,px)+60,y+60));via('metal4','metal5','via4',x,y)
   rect('metal4',(x-40,y-40,x+40,dest+40));via('metal4','metal5','via4',x,dest)
 for net,y in tracks.items():
  xs=[b[0] for b in layers.get('via4',[]) if abs((b[1]+b[3])//2-y)<1]+[b[2] for b in layers.get('via4',[]) if abs((b[1]+b[3])//2-y)<1]
  rect('metal5',(min(xs+([-18000] if net in ports else []))-60,y-60,max(xs+([-17900] if net in ports else []))+60,y+60))
 # One focused repair: ground shield between membrane and its following buffer output.
 # Child geometry, phases, native devices and all trained-reference values unchanged.
 sy=(tracks['C_STATE']+tracks['BUFFERED'])//2;gx=3700000
 rect('metal5',(-34000,sy-44,gx+60,sy+44))
 via('metal4','metal5','via4',gx,sy)
 rect('metal4',(gx-40,tracks['VSS']-40,gx+40,sy+40))
 via('metal4','metal5','via4',gx,tracks['VSS'])
 rect('metal5',(3200000,tracks['VSS']-60,gx+60,tracks['VSS']+60))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
 pins=bankpins
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
 for inst,name,dx,mapping in instances:ref+='X'+inst+' '+' '.join(mapping[p] for p in orders[name])+' '+name+'\n'
 ref+='.ends\n';(out/'reference.spice').write_text(ref)
 print(json.dumps({'cell':cell,'source_DRC':0,'next':'Exact source/flat/GDS graph qualification; no native Netgen pass claimed.'}))
if __name__=='__main__':main()
