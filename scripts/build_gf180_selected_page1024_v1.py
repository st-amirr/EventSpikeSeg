"""Connected native1024-state page: higher bank selection and shared analog data."""
from pathlib import Path
import json,re,hashlib
import probe_gf180_mos_gate_cap as f
from build_gf180_fixed_body_tg import rectangles
R=f.ROOT
CELL='gf180_selected_page1024_v1'
def main():
 out=f.BASE/'layout'/CELL;assert not out.exists();out.mkdir();f.OUT=out
 layers={};pins={};refs=[];placements=[];inputs={}
 def rect(l,b):layers.setdefault(l,[]).append(tuple(b))
 def h(x,z,y):rect('metal5',(min(x,z)-44,y-44,max(x,z)+44,y+44))
 def v(x,y,z):rect('metal4',(x-40,min(y,z)-40,x+40,max(y,z)+40))
 def via(x,y):
  for l in ['metal4','metal5']:rect(l,(x-52,y-52,x+52,y+52))
  rect('via4',(x-28,y-28,x+28,y+28))
 def pin(n,l,x,y):pins[n]=(l,(x-20,y-20,x+20,y+20))
 def copy(name,tag,dx,dy,mapping):
  d=f.BASE/'layout'/name;q=json.loads((d/'qualification.json').read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
  for suffix in ['.mag','.spice']:
   p=d/(name+suffix);assert hashlib.sha256(p.read_bytes()).hexdigest()==q['sha256'][p.name];inputs[str(p.relative_to(R))]=q['sha256'][p.name]
  src=(d/(name+'.mag')).read_text();assert not re.search(r'(?m)^use ',src)
  for l,boxes in rectangles(d/(name+'.mag'),0).items():
   for a,b,c,e in boxes:rect(l,(a+dx,b+dy,c+dx,e+dy))
  pp={}
  for l,a,b,c,e,n in re.findall(r'(?m)^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)',src):pp[n]=(l,dx+(int(a)+int(c))//2,dy+(int(b)+int(e))//2)
  text=(d/(name+'.spice')).read_text().replace('\n+',' ');body=re.search(r'(?ms)^\.subckt\s+'+name+r'\s+[^\n]*\n(.*?)^\.ends',text)[1]
  for line in body.splitlines():
   if not line.startswith('X'):continue
   t=line.split();k=next((i for i,u in enumerate(t[1:],1) if '=' in u),len(t));nodes=[mapping.get(n,tag+'_'+n) for n in t[1:k-1]];refs.append('X'+tag+'_'+t[0][1:]+' '+' '.join(nodes+t[k-1:]))
  placements.append(dict(cell=name,instance=tag,origin_um=[dx*.005,dy*.005],bindings=mapping));return pp,q
 common=['LOW0','LOW1','LOW2','LOW3','VDD','VSS','VCM'];spines={n:7000+400*j for j,n in enumerate(common)};spines.update({f'DATA{j}':11000+400*j for j in range(8)})
 ppairs=[]
 for i in range(8):
  mapping={f'A{j}':f'LOW{j}' for j in range(3)};mapping.update(BANK_SELECT='LOW3',WRITE_CMD=f'W{i}',READ_CMD=f'R{i}',VDD='VDD',VSS='VSS',VCM='VCM');mapping.update({f'DATA{j}':f'DATA{j}' for j in range(8)})
  pp,q=copy('gf180_independent_bank_pair_v4',f'P{i}',20044,36484*i+2440,mapping);ppairs.append(pp)
  for n,(l,x,y) in pp.items():
   net=mapping.get(n)
   if net in spines:
    assert l=='metal5';sx=spines[net];h(sx,x,y);via(sx,y)
   elif n not in ['WRITE_CMD','READ_CMD']:
    pin(f'P{i}_{n}',l,x,y)
 rootmap={f'A{j}':f'HIGH{j}' for j in range(3)};rootmap.update(WRITE_CMD='WRITE_CMD',READ_CMD='READ_CMD',VDD='VDD',VSS='VSS');rootmap.update({f'{mode}{j}':f'{short}{j}' for j in range(8) for mode,short in [('WRITE','W'),('READ','R')]})
 root,q=copy('gf180_bank_page_decoder8_v1','SELECT',20044,8*36484+4700,rootmap)
 for j in range(8):
  for mode,short,m in [('WRITE','W',0),('READ','R',1)]:
   l,x,y=root[f'{mode}{j}'];sx=1600+240*(2*j+m);_,tx,ty=ppairs[j][mode+'_CMD'];h(sx,x,y);via(sx,y);v(sx,ty,y);via(sx,ty);h(sx,tx,ty)
 for n in ['A0','A1','A2','WRITE_CMD','READ_CMD']:
  l,x,y=root[n];pin(rootmap[n],l,x,y)
 for n in ['VDD','VSS']:
  l,x,y=root[n];sx=spines[n];h(sx,x,y);via(sx,y)
 top=8*36484+4700+34000
 for j,(n,sx) in enumerate(spines.items()):
  ys=[(b[1]+b[3])//2 for b in layers.get('via4',[]) if (b[0]+b[2])//2==sx];dest=top+200*j;v(sx,min(ys),dest);via(sx,dest);h(sx,15000,dest);pin(n,'metal5',15000,dest)
 lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
 for l,boxes in layers.items():lines+=['<< '+l+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
 lines+=['<< labels >>']
 for i,(n,(l,b)) in enumerate(pins.items(),1):lines +=[f'rlabel {l} s '+' '.join(map(str,b))+f' 4 {n}',f'port {i} nsew']
 lines+=['<< end >>',''];(out/(CELL+'.mag')).write_text('\n'.join(lines));(out/'reference.spice').write_text('.subckt reference '+' '.join(pins)+'\n'+'\n'.join(refs)+'\n.ends\n');(out/'build_source.py').write_bytes(Path(__file__).read_bytes())
 (out/'placement_and_binding.json').write_text(json.dumps(dict(cell=CELL,placements=placements,inputs=inputs,state_count=1024,mos_count=6326,native_mim_count=1024,shared_data_columns=8,complete_chip=False,scope='Native selected1024-state page.7row-address bits select one8-state row;8shared analog DATA trunks. Readout/bias remain independently exposed;compute binding and native initialization not closed.'),indent=2)+'\n')
 print('Native page DRC/extraction starting',flush=True)
 log=f.magic(f'load {CELL}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n');(out/'extraction.log').write_text(log)
 count=int(re.search(r'Total DRC errors found:\s*(\d+)',log)[1]);report=dict(cell=CELL,magic_drc_count=count,lvs_unique=False,mos_count=6326,native_mim_count=1024,bbox_um=[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],ports=list(pins),scope='Connected native1024-state page; shared analog write data and categorical higher bank selector. Shared readout/compute,initialization,5ms service unqualified.')
 (out/'initial_physical_result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='ports'},indent=2),flush=True)
 if count:return
 setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';nl=f.run(['netgen-lvs','-batch','lvs',CELL+'.spice '+CELL,'reference.spice reference',setup,'lvs.out']);(out/'netgen.log').write_text(nl);report['lvs_unique']='Circuits match uniquely' in nl
 report['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/(CELL+s) for s in ['.mag','.spice','.gds']]+[out/'reference.spice',out/'build_source.py',out/'extraction.log',out/'netgen.log']};(out/'initial_physical_result.json').write_text(json.dumps(report,indent=2)+'\n');print('LVS unique:',report['lvs_unique'])
if __name__=='__main__':main()
