"""Physical3to8 categorical decoder and independent read/write commands joined to8x8 bank."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_addressed_memory_bank8x8_v2';out=f.BASE/'layout'/cell;assert not out.exists();out.mkdir();f.OUT=out
 bank='gf180_compact_memory_bank8x8_v1';andcell='gf180_reset_select_and_fullroute';inv='gf180_phase_inverter_fullroute';children={};inputs={Path(__file__)}
 for name in [bank,andcell,inv]:
  d=f.BASE/'layout'/name;qp=d/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
  for suffix in ['.mag','.spice','.gds']:
   p=d/(name+suffix);assert sha(p)==q['sha256'][p.name];inputs.add(p)
  inputs.add(qp);children[name]=(d,q)
 ports=['A0','A1','A2','WRITE_CMD','READ_CMD']+[f'DATA{c}' for c in range(8)]+[f'READOUT{c}' for c in range(8)]+['VDD','VSS','VCM']+[f'STATE{r}{c}' for r in range(8) for c in range(8)]
 instances=[]
 def gate(name,a,b,y,yb):instances.append((name,andcell,dict(A=a,B=b,Y=y,YB=yb,VDD='VDD',VSS='VSS')))
 for bit in range(3):instances.append((f'inv{bit}',inv,dict(IN=f'A{bit}',OUT=f'AB{bit}',VDD='VDD',VSS='VSS')))
 for pair in range(4):gate(f'pair{pair}','A0' if pair&1 else 'AB0','A1' if pair&2 else 'AB1',f'PAIR{pair}',f'PAIRB{pair}')
 for row in range(8):
  gate(f'select{row}',f'PAIR{row%4}','A2' if row&4 else 'AB2',f'SEL{row}',f'SELB{row}')
  gate(f'write{row}',f'SEL{row}','WRITE_CMD',f'WRITE{row}',f'WRITEB{row}')
  gate(f'read{row}',f'SEL{row}','READ_CMD',f'READ{row}',f'READB{row}')
 instances.append(('bank',bank,{p:p for p in children[bank][1]['ports']}))
 nets=[]
 for name,kind,mapping in instances:
  for n in mapping.values():
   if not n.startswith('STATE') and n not in nets:nets.append(n)
 tracks={n:32000+640*i for i,n in enumerate(nets)};layers={};labels={};refs=[];xmax=0
 def rect(l,b):layers.setdefault(l,[]).append(tuple(b))
 def h(l,x1,x2,y,p=40):rect(l,(min(x1,x2)-p,y-p,max(x1,x2)+p,y+p))
 def v(l,x,y1,y2,p=40):rect(l,(x-p,min(y1,y2)-p,x+p,max(y1,y2)+p))
 def via(lo,hi,cut,x,y,p5=60):
  for l in [lo,hi]:
   p=p5 if l=='metal5' else 38 if cut=='via1' else 40;rect(l,(x-p,y-p,x+p,y+p))
  c=26 if cut=='via1' else 28;rect(cut,(x-c,y-c,x+c,y+c))
 for index,(name,kind,mapping) in enumerate(instances):
  d,q=children[kind];dx=index*40000;dy=0;shape=rectangles(d/(kind+'.mag'),0);assert not re.search(r'(?m)^use ',(d/(kind+'.mag')).read_text())
  for l,boxes in shape.items():
   for a,b,c,e in boxes:rect(l,(a+dx,b,c+dx,e))
  native_labels=re.findall(r'(?m)^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)\nport (\d+)',(d/(kind+'.mag')).read_text());ordered=sorted(native_labels,key=lambda t:int(t[-1]));assert [p[-2] for p in ordered]==q['ports']
  for j,(l,a,b,c,e,p,number) in enumerate(ordered):
   net=mapping[p];x=dx+(int(a)+int(c))//2;y=(int(b)+int(e))//2
   if net.startswith('STATE'):labels[net]=(l,(x-20,y-20,x+20,y+20));continue
   column=dx-4000-640*j
   if kind!=bank:
    assert l=='metal3';h('metal3',column,x,y);via('metal3','metal4','via3',column,y)
   elif p.startswith(('DATA','READOUT')):
    # M2 vertical risers, separate M3 horizontal escapes above the bank.
    escape_y=22400+240*(int(p[4:]) if p.startswith('DATA') else 8+int(p[7:]))
    via('metal3','metal4','via3',x,y);via('metal2','metal3','via2',x,y);v('metal2',x,y,escape_y);via('metal2','metal3','via2',x,escape_y);h('metal3',column,x,escape_y);via('metal3','metal4','via3',column,escape_y);y=escape_y
   elif l=='metal5':h('metal5',column,x,y,44);via('metal4','metal5','via4',column,y,44)
   elif l=='metal2':via('metal2','metal3','via2',x,y);h('metal3',column,x,y);via('metal3','metal4','via3',column,y)
   else:raise AssertionError((p,l))
   v('metal4',column,y,tracks[net]);via('metal4','metal5','via4',column,tracks[net])
  xmax=max(xmax,dx+round(q['bbox_um'][2]/.005))
  text=(d/(kind+'.spice')).read_text().replace('\n+',' ');body=re.search(r'(?ms)^\.subckt\s+'+re.escape(kind)+r'\s+[^\n]*\n(.*?)^\.ends',text)[1]
  for line in body.splitlines():
   if not line.startswith('X'):continue
   t=line.split();k=next((i for i,vv in enumerate(t[1:],1) if '=' in vv),len(t));ns=[mapping.get(n,name+'_'+n) for n in t[1:k-1]];refs.append('X'+name+'_'+t[0][1:]+' '+' '.join(ns+t[k-1:]))
 for n,y in tracks.items():h('metal5',-12000,xmax+1000,y,60)
 for p in ports:
  if p.startswith('STATE'):continue
  y=tracks[p];labels[p]=('metal5',(-11900,y-20,-11860,y+20))
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for l,boxes in layers.items():lines+=['<< '+l+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,p in enumerate(ports,1):
  l,b=labels[p];lines +=[f'rlabel {l} s '+' '.join(map(str,b))+f' 4 {p}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(cell+'.mag')).write_text('\n'.join(lines));(out/'build_source.py').write_bytes(Path(__file__).read_bytes());(out/'reference.spice').write_text('.subckt reference '+' '.join(ports)+'\n'+'\n'.join(refs)+'\n.ends\n')
 log=f.magic(f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 count=int(re.search(r'Total DRC errors found:\s*(\d+)',log)[1]);setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';nl=f.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(nl)
 r=dict(cell=cell,magic_drc_count=count,lvs_unique='Circuits match uniquely' in nl,mos_count=430,native_mim_count=64,source_layout_completed=True,bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],ports=ports,dense_array_qualified=False,scope='Actual174 native decoder MOS:3 inverters and28 sixMOSAND cells, joined to256MOS64MIM real8x8 bank; total430MOS. Three categorical row address bits, independent read/write enables, decoded native WRITE/WRITEB/READ wordlines. All64 STATE diagnostic pads stay local; DATA/READOUT8column ports escape separately. This spacious routed integration fixture is not final dense decoder area or fullchip. External address/command/data/reference/current fixtures and uncalibrated readout remain; fresh native connected sequence required. No numerical state digitization, trained beta or compute path.',sha256={p.relative_to(R).as_posix():sha(p) for p in inputs|{out/(cell+'.mag'),out/(cell+'.spice'),out/(cell+'.gds'),out/'reference.spice',out/'netgen.log',out/'extraction.log'}})
 (out/'initial_physical_result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert count==0 and r['lvs_unique']
if __name__=='__main__':main()
