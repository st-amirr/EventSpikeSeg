"""Physically bind independent128-state banks to shared selected analog readout."""
from pathlib import Path
import json,re,hashlib
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=f.ROOT;CELL='gf180_bank_pair_shared_readout_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=f.BASE/'layout'/CELL;assert not out.exists();out.mkdir();f.OUT=out
 layers={};pins={};refs=[];inputs={};placements=[]
 def rect(l,b):layers.setdefault(l,[]).append(tuple(b))
 def h(l,x,z,y,p=40):rect(l,(min(x,z)-p,y-p,max(x,z)+p,y+p))
 def v(l,x,y,z,p=40):rect(l,(x-p,min(y,z)-p,x+p,max(y,z)+p))
 def via(lo,hi,cut,x,y):
  for l in [lo,hi]:
   p=44 if l=='metal5' else 40;rect(l,(x-p,y-p,x+p,y+p))
  rect(cut,(x-28,y-28,x+28,y+28))
 def pin(n,l,x,y):pins[n]=(l,(x-20,y-20,x+20,y+20))
 def copy(name,tag,dx,dy,mapping):
  d=f.BASE/'layout'/name;q=json.loads((d/'qualification.json').read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
  for ext in ['.mag','.spice']:
   p=d/(name+ext);assert sha(p)==q['sha256'][p.name];inputs[p.relative_to(R).as_posix()]=sha(p)
  src=(d/(name+'.mag')).read_text();assert not re.search(r'(?m)^use ',src)
  for l,boxes in rectangles(d/(name+'.mag'),0).items():
   for a,b,c,e in boxes:rect(l,(a+dx,b+dy,c+dx,e+dy))
  pp={}
  for l,a,b,c,e,n in re.findall(r'(?m)^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)',src):pp[n]=(l,dx+(int(a)+int(c))//2,dy+(int(b)+int(e))//2)
  text=(d/(name+'.spice')).read_text().replace('\n+',' ');body=re.search(r'(?ms)^\.subckt\s+'+name+r'\s+[^\n]*\n(.*?)^\.ends',text)[1]
  for line in body.splitlines():
   if not line.startswith('X'):continue
   t=line.split();k=next((i for i,u in enumerate(t[1:],1) if '=' in u),len(t));nodes=[mapping.get(n,tag+'_'+n) for n in t[1:k-1]];refs.append('X'+tag+'_'+t[0][1:]+' '+' '.join(nodes+t[k-1:]))
  placements.append(dict(cell=name,instance=tag,origin_um=[dx*.005,dy*.005],bindings=mapping));return pp
 pair='gf180_independent_bank_pair_v4';pq=json.loads((f.BASE/'layout'/pair/'qualification.json').read_text());pp=copy(pair,'PAIR',0,0,{n:n for n in pq['ports']})
 nets=[f'B{b}_READOUT{c}' for b in range(2) for c in range(8)]+['B0_BIAS','B1_BIAS']+[f'READOUT{c}' for c in range(8)]+['SELECTED_BIAS','BANK_SELECT','BANK_SELECTB','VDD','VSS'];tracks={n:60000+640*i for i,n in enumerate(nets)};spinepoints={n:[] for n in nets}
 def totrack(net,x,y):v('metal4',x,y,tracks[net]);via('metal4','metal5','via4',x,tracks[net]);spinepoints[net].append(x)
 for n,(l,x,y) in pp.items():
  if 'READOUT' in n:
   b=int(n[1]);c=int(n[-1]);escape=19600+200*c;sx=-20000-400*c if b==0 else 100000+400*c
   assert l=='metal4';v('metal4',x,y,escape);via('metal4','metal5','via4',x,escape);h('metal5',x,sx,escape,44);via('metal4','metal5','via4',sx,escape);totrack(n,sx,escape)
  elif n in ['B0_BIAS','B1_BIAS']:
   b=int(n[1]);sx=-25000 if b==0 else 105000;assert l=='metal2';via('metal2','metal3','via2',x,y);h('metal3',x,sx,y);via('metal3','metal4','via3',sx,y);totrack(n,sx,y);pin(n,l,x,y)
  elif n in ['BANK_SELECT','VDD','VSS']:
   sx=-30000-400*['BANK_SELECT','VDD','VSS'].index(n);assert l=='metal5';h('metal5',sx,x,y,44);via('metal4','metal5','via4',sx,y);totrack(n,sx,y);pin(n,l,x,y)
  else:pin(n,l,x,y)
 tg='gf180_fixed_body_tg_quarter_shorttracks';inv='gf180_dense_inverter_v1'
 instances=[]
 for b in range(2):
  for c in range(8):instances.append((f'R{b}{c}',tg,120000+16000*(8*b+c),{'A':f'B{b}_READOUT{c}','B':f'READOUT{c}','EN':'BANK_SELECTB' if b==0 else 'BANK_SELECT','ENB':'BANK_SELECT' if b==0 else 'BANK_SELECTB','VDD':'VDD','VSS':'VSS'}))
  instances.append((f'BIAS{b}',tg,390000+16000*b,{'A':f'B{b}_BIAS','B':'SELECTED_BIAS','EN':'BANK_SELECTB' if b==0 else 'BANK_SELECT','ENB':'BANK_SELECT' if b==0 else 'BANK_SELECTB','VDD':'VDD','VSS':'VSS'}))
 instances.append(('INVERT',inv,430000,{'IN':'BANK_SELECT','OUT':'BANK_SELECTB','VDD':'VDD','VSS':'VSS'}))
 for tag,name,dx,mapping in instances:
  ports=copy(name,tag,dx,0,mapping)
  for i,(n,(l,x,y)) in enumerate(ports.items()):
   assert l=='metal3';sx=dx-3000-400*i;h('metal3',sx,x,y);via('metal3','metal4','via3',sx,y);totrack(mapping[n],sx,y)
 exposed=[f'READOUT{c}' for c in range(8)]+['SELECTED_BIAS']
 for n,xs in spinepoints.items():
  assert xs,n;y=tracks[n];h('metal5',min(xs+([-36000] if n in exposed else [])),max(xs),y,44)
  if n in exposed:pin(n,'metal5',-36000,y)
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for l,boxes in layers.items():lines+=['<< '+l+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(n,(l,b)) in enumerate(pins.items(),1):lines +=[f'rlabel {l} s '+' '.join(map(str,b))+f' 4 {n}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(CELL+'.mag')).write_text('\n'.join(lines));(out/'reference.spice').write_text('.subckt reference '+' '.join(pins)+'\n'+'\n'.join(refs)+'\n.ends\n');(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 (out/'placement_and_binding.json').write_text(json.dumps(dict(cell=CELL,placements=placements,inputs=inputs,state_count=128,mos_count=808,native_mim_count=128,shared_read_columns=8,shared_write_columns=8,scope='Actual physical bank-selected readout/replica-bias interface for independent128state pair. Shared8analog readout and8write trunks;4categorical row/bank address bits. Both master-current BIAS inputs remain exposed. Commands must be off while addresses change. Shared reader/compute,higherpage selection,population service still to bind. No numericdigitalstate.'),indent=2)+'\n')
 print('Native shared readout parent DRC/extraction',flush=True)
 log=f.magic(f'load {CELL}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 count=int(re.search(r'Total DRC errors found:\s*(\d+)',log)[1]);report=dict(cell=CELL,magic_drc_count=count,lvs_unique=False,mos_count=808,native_mim_count=128,bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],ports=list(pins),scope='128resident analog states with bank-selected shared8read columns and selected replica bias. External references and commands;new physical parent simulation required.')
 if count==0:
  setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';nl=f.run(['netgen-lvs','-batch','lvs',CELL+'.spice '+CELL,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(nl);report['lvs_unique']='Circuits match uniquely' in nl
 report['sha256']={p.name:sha(p) for p in [out/(CELL+s) for s in ['.mag','.spice','.gds']]+[out/'reference.spice',out/'build_source.py',out/'extraction.log']+([out/'netgen.log'] if (out/'netgen.log').exists() else [])};(out/'initial_physical_result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['ports','sha256']},indent=2))
if __name__=='__main__':main()
