"""Direct native row/command decode beside the under-MIM bank; shared categorical buses."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bank_page_decoder8_v1';out=f.BASE/'layout'/cell;assert not out.exists();out.mkdir();f.OUT=out
 bank='gf180_underplate_biased_bank8x8_v1';gate='gf180_dense_and4_v1';inv='gf180_dense_inverter_v1';children={};files={Path(__file__)}
 for name in [gate,inv]:
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
 controls=['A0','AB0','A1','AB1','A2','AB2','WRITE_CMD','READ_CMD','VDD','VSS'];tracks={n:30400+200*i for i,n in enumerate(controls)};spines={n:-2400+160*i for i,n in enumerate(controls)}
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
 # Two terms per row: one WRITE and one READ, each shared by eight capacitors.
 for row in range(8):
  for mode,dx in [('WRITE',0),('READ',11000)]:
   dy=3600*row;mapping={n:('A'+str(i) if row&(1<<i) else 'AB'+str(i)) for i,n in enumerate(['A','B','C'])};mapping.update(EN=mode+'_CMD',Y=mode+str(row),YB=f'unused_{mode}{row}',VDD='VDD',VSS='VSS')
   ports=copy(gate,mode+str(row),dx,dy,mapping)
   for n in ['A','B','C','EN','VDD','VSS']:
    l,x,y=ports[n];net=mapping[n]
    if mode=='READ' and n=='EN':col=10400
    else:col=spines[net]
    h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,tracks[net]);via('metal4','metal5','via4',col,tracks[net])
   # Outputs use separate spines per row; they connect directly to bank wordlines.
   l,x,y=ports['Y'];col=(-4000+160*row) if mode=='WRITE' else (8200+160*row);dest=2240*row+(1340 if mode=='WRITE' else 1540)
   h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,dest);via('metal4','metal5','via4',col,dest);h('metal5',col,20600,dest,44)
 # Three compact polarity inverters, above the bank and below the control trunks.
 for bit in range(3):
  dx=23000+3000*bit;dy=20200;mapping={'IN':f'A{bit}','OUT':f'AB{bit}','VDD':'VDD','VSS':'VSS'};ports=copy(inv,'inv'+str(bit),dx,dy,mapping)
  for j,(n,(l,x,y)) in enumerate(ports.items()):
   col=dx-900-160*j;net=mapping[n];h('metal3',col,x,y);via('metal3','metal4','via3',col,y);v('metal4',col,y,tracks[net]);via('metal4','metal5','via4',col,tracks[net])
 for row in range(8):
  for mode,offset in [('WRITE',1340),('READ',1540)]:pin(mode+str(row),'metal5',20000,2240*row+offset)
 for net,y in tracks.items():h('metal5',-2600,33000,y,44)
 for n in ['A0','A1','A2','WRITE_CMD','READ_CMD','VDD','VSS']:pin(n,'metal5',-2500,tracks[n])

 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for l,boxes in layers.items():lines+=['<< '+l+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(n,(l,b)) in enumerate(pins.items(),1):lines +=[f'rlabel {l} s '+' '.join(map(str,b))+f' 4 {n}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines));(out/'build_source.py').write_bytes(Path(__file__).read_bytes());(out/'reference.spice').write_text('.subckt reference '+' '.join(pins)+'\n'+'\n'.join(refs)+'\n.ends\n')
 log=f.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 count=int(re.search(r'Total DRC errors found:\s*(\d+)',log)[1]);setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';nl=f.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(nl)
 files.update([out/(cell+s) for s in ['.mag','.spice','.gds']]+[out/'reference.spice',out/'extraction.log',out/'netgen.log'])
 q=dict(cell=cell,magic_drc_count=count,lvs_unique='Circuits match uniquely' in nl,source_layout_completed=True,mos_count=166,native_mim_count=0,bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],ports=list(pins),scope='Native166MOS three-address-bit page decoder with separate READ_CMD/WRITE_CMD. Sixteen real AND4 terms plus3polarity inverters; each output selects one of8physical memory-page children. Used recursively for higher bank selection,not numeric state/weight storage. Separate read/write enable,held-stable address while commands active. Children and address input drivers,global control fanout,analog data distribution and population5ms service need actual connected evidence. Native layout/reference qualification and loaded nominal command sequence required.',sha256={p.relative_to(R).as_posix():sha(p) for p in files})
 (out/'initial_physical_result.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k not in ['ports','sha256']},indent=2));assert count==0 and q['lvs_unique']
if __name__=='__main__':main()
