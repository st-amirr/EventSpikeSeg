"""Direct native row/command decode beside the under-MIM bank; shared categorical buses."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_independent_bank_pair_v3';out=f.BASE/'layout'/cell;assert not out.exists();out.mkdir();f.OUT=out
 bank='gf180_underplate_biased_bank8x8_v1';gate='gf180_dense_and4_v1';inv='gf180_dense_inverter_v1';children={};files={Path(__file__)}
 for name in [bank,gate,inv]:
  d=f.BASE/'layout'/name;q=json.loads((d/'qualification.json').read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];files.add(d/'qualification.json')
  for n in [name+'.mag',name+'.spice',name+'.gds']:assert sha(d/n)==q['sha256'][n];files.add(d/n)
  children[name]=(d,q)
 layers={};pins={};refs=[]
 def rect(l,b):layers.setdefault(l,[]).append(tuple(b))
 def h(l,a,b,y,p=40):rect(l,(min(a,b)-p,y-p,max(a,b)+p,y+p))
 def v(l,x,a,b,p=40):rect(l,(x-p,min(a,b)-p,x+p,max(a,b)+p))
 def via(lo,hi,cut,x,y):
  p,c=(38,26) if cut=='via1' else (40,28)
  for l in [lo,hi]:
   a=44 if l=='metal5' else p;rect(l,(x-a,y-a,x+a,y+a))
  rect(cut,(x-c,y-c,x+c,y+c))
 def pin(n,l,x,y):pins[n]=(l,(x-20,y-20,x+20,y+20))
 controls=['A0','AB0','A1','AB1','A2','AB2','WRITE_CMD','READ_CMD','BANK_SELECT','BANK_SELECTB','B0_WRITE','B0_READ','B1_WRITE','B1_READ','VDD','VSS','VCM'];tracks={n:30400+200*i for i,n in enumerate(controls)};spines={n:-2400+160*i for i,n in enumerate(controls)}
 def copy(name,label,dx,dy,mapping):
  d,q=children[name];src=d/(name+'.mag');assert not re.search(r'(?m)^use ',src.read_text())
  for l,boxes in rectangles(src,0).items():
   for a,b,c,e in boxes:rect(l,(a+dx,b+dy,c+dx,e+dy))
  ports={}
  for l,a,b,c,e,n in re.findall(r'(?m)^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)',src.read_text()):ports[n]=(l,dx+(int(a)+int(c))//2,dy+(int(b)+int(e))//2)
  text=(d/(name+'.spice')).read_text().replace('\n+',' ');body=re.search(r'(?ms)^\.subckt\s+'+name+r'\s+[^\n]*\n(.*?)^\.ends',text)[1]
  for line in body.splitlines():
   if not line.startswith('X'):continue
   t=line.split();k=next((i for i,u in enumerate(t[1:],1) if '=' in u),len(t));nodes=[mapping.get(n,label+'_'+n) for n in t[1:k-1]];refs.append('X'+label+'_'+t[0][1:]+' '+' '.join(nodes+t[k-1:]))
  return ports
 # Share address polarity and global write-data drive, but independently gate
 # each bank's command BEFORE its row decode. Both banks must not write together.
 for bi in range(2):
  shift=44000*bi
  for row in range(8):
   for mode,local_dx in [('WRITE',0),('READ',11000)]:
    dx=shift+local_dx;dy=3600*row;mapping={n:('A'+str(i) if row&(1<<i) else 'AB'+str(i)) for i,n in enumerate(['A','B','C'])};mapping.update(EN=f'B{bi}_{mode}',Y=f'B{bi}_{mode}{row}',YB=f'unused_B{bi}_{mode}{row}',VDD='VDD',VSS='VSS')
    ports=copy(gate,f'B{bi}_{mode}{row}',dx,dy,mapping)
    for n in ['A','B','C','EN','VDD','VSS']:
     l,x,y=ports[n];net=mapping[n];col=shift+(10400 if mode=='READ' and n=='EN' else spines[net])
     h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,tracks[net]);via('metal4','metal5','via4',col,tracks[net])
    l,x,y=ports['Y'];col=shift+((-4000+160*row) if mode=='WRITE' else (8200+160*row));dest=2240*row+(1340 if mode=='WRITE' else 1540)
    h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,dest);via('metal4','metal5','via4',col,dest);h('metal5',col,shift+20600,dest,44)
 # Four native command gates use the qualified dense AND4 (unused inputs high).
 for bi in range(2):
  for mode,local_dx in [('WRITE',0),('READ',11000)]:
   dx=44000*bi+local_dx;dy=36000;mapping=dict(A='BANK_SELECTB' if bi==0 else 'BANK_SELECT',B=mode+'_CMD',C='VDD',EN='VDD',Y=f'B{bi}_{mode}',YB=f'unused_enable_{bi}_{mode}',VDD='VDD',VSS='VSS');ports=copy(gate,f'enable_{bi}_{mode}',dx,dy,mapping)
   for j,(n,(l,x,y)) in enumerate(ports.items()):
    if n=='YB':continue
    # Separate escape columns: read/write gates have distinct commands/outputs.
    # Horizontal read stubs must not cross corresponding write-gate pins.
    net=mapping[n];col=44000*bi+((10000-160*j) if mode=='READ' else (-6000-160*j))
    h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,tracks[net]);via('metal4','metal5','via4',col,tracks[net])
 # Three row-address polarity inverters shared by the two banks.
 for bit in range(3):
  dx=23000+3000*bit;dy=20200;mapping={'IN':f'A{bit}','OUT':f'AB{bit}','VDD':'VDD','VSS':'VSS'};ports=copy(inv,'inv'+str(bit),dx,dy,mapping)
  for j,(n,(l,x,y)) in enumerate(ports.items()):
   col=dx-900-160*j;net=mapping[n];h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,tracks[net]);via('metal4','metal5','via4',col,tracks[net])
 # One additional inverter produces bank0 enable from the categorical bank bit.
 mapping=dict(IN='BANK_SELECT',OUT='BANK_SELECTB',VDD='VDD',VSS='VSS');ports=copy(inv,'bank_inverse',23000,23800,mapping)
 for j,(n,(l,x,y)) in enumerate(ports.items()):
  col=18000-160*j;net=mapping[n];h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,tracks[net]);via('metal4','metal5','via4',col,tracks[net])
 data_points={col:[] for col in range(8)}
 for bank_index in range(2):
  shift=44000*bank_index;prefix=f'B{bank_index}_'
  mapping={n:(prefix+n if n.startswith(('STATE','BIAS','READOUT','WRITE','READ')) else n) for n in children[bank][1]['ports']}
  bp=copy(bank,'bank'+str(bank_index),22000+shift,0,mapping)
  for n,(l,x,y) in bp.items():
   if n.startswith(('WRITE','READ')) and not n.startswith('READOUT'):continue
   if n.startswith('DATA'):
    col=int(n[4:]);dest=18000+200*col;v('metal4',x,y,dest);via('metal4','metal5','via4',x,dest);data_points[col].append(x)
   elif n in ['VDD','VSS','VCM']:
    col={'VDD':19800,'VSS':19600,'VCM':19400}[n]+shift;via('metal2','metal3','via2',x,y);h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,tracks[n]);via('metal4','metal5','via4',col,tracks[n])
   else:pin(mapping[n],l,x,y)
 for col,xs in data_points.items():
  dest=18000+200*col;h('metal5',20000,max(xs),dest,44);pin(f'DATA{col}','metal5',20000,dest)
 for net,y in tracks.items():
  xs=[(x1+x2)//2 for x1,y1,x2,y2 in layers['via4'] if (y1+y2)//2==y]
  assert xs,net
  h('metal5',min(xs+[-2600])-200,max(xs+[90000])+200,y,44)
 for n in ['A0','A1','A2','BANK_SELECT','WRITE_CMD','READ_CMD','VDD','VSS']:pin(n,'metal5',-2500,tracks[n])
 # VCM is exposed on its shared supply trunk; BIAS remains an analog master-current port.
 pin('VCM','metal5',-2500,tracks['VCM'])
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for l,boxes in layers.items():lines+=['<< '+l+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(n,(l,b)) in enumerate(pins.items(),1):lines +=[f'rlabel {l} s '+' '.join(map(str,b))+f' 4 {n}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines));(out/'build_source.py').write_bytes(Path(__file__).read_bytes());(out/'reference.spice').write_text('.subckt reference '+' '.join(pins)+'\n'+'\n'.join(refs)+'\n.ends\n')
 print('Native parent DRC/extraction starting',flush=True)
 log=f.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 count=int(re.search(r'Total DRC errors found:\s*(\d+)',log)[1]);setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';nl=f.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(nl)
 files.update([out/(cell+s) for s in ['.mag','.spice','.gds']]+[out/'reference.spice',out/'extraction.log',out/'netgen.log'])
 q=dict(cell=cell,magic_drc_count=count,lvs_unique='Circuits match uniquely' in nl,source_layout_completed=True,mos_count=770,native_mim_count=128,bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],ports=list(pins),scope='Independent native128-state bank pair:2x201MOS64MIM banks,2x160MOS row terms,shared6MOS row-address polarity,4x10MOS perbank command gates and2MOS bank polarity (770MOS128MIM total). BANK_SELECT chooses one bank for shared3bit row address/read/write commands. Shared eight physical analog DATA trunks drive both banks, while only selected bank wordline can write; both banks have independent READOUT/BIAS and all128state identities. Command/address changes must occur with READ_CMD/WRITE_CMD low. This closes destructive simultaneous-write behavior of the earlier shared-row pair; all old artifacts preserved. Higher-level bank address decoder,readout mux/reader,compute/scheduler and full-population5ms service remain unbound. No numerical-state digitization. New native isolation sequence and layout qualification required; parent precision/noise/retention not inferred from child results.',sha256={p.relative_to(R).as_posix():sha(p) for p in files})
 (out/'initial_physical_result.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k not in ['ports','sha256']},indent=2));assert count==0 and q['lvs_unique']
if __name__=='__main__':main()
