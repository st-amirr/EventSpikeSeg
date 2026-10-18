"""Add physical AGE/AMP forest restore and row capture to15existing actors.

Actual analog connections, with categorical phases still external and parent RC
unqualified. Retain V10 module geometry and all resident state identity components.
"""
from pathlib import Path
import collections,hashlib,json,struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements,via
from assemble_gf180_full_capacity_storage_gds_v2 import begin,reference,rec
from assemble_gf180_full25_physical_candidate_v5 import pinlist,rect,label
from gf180_gds_library_stream_v1 import Library
from assemble_gf180_full25_shared_page1024_v7 import labels
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';S=B/'assembly/full25_membrane_service_v10';F=B/'assembly/full_population_page_forest_v2';D=B/'assembly/full25_adaptation_service_v12'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not D.exists();D.mkdir();mf=S/'physical_assembly.json';m=json.loads(mf.read_text());ff=F/'physical_forest.json';f=json.loads(ff.read_text());sg=S/'eventspikeseg140k_membrane_service_v10.gds';prefix,cells=cells_read(sg.read_bytes());io='gf180_adaptation_shared_state_io_v6';dd=B/'layout'/io;qf=dd/'qualification.json';q=json.loads(qf.read_text());assert q['source_and_GDS_exact_device_graphs_accepted'] and q['magic_drc_count']==q['gds_roundtrip_drc_count']==0;ig=dd/(io+'.gds');assert sha(ig)==q['sha256'][ig.name];simfile=B/'results'/(io+'_native_restore_capture.json');assert json.loads(simfile.read_text())['module_simulation_completed'];lib=Library();icell=lib.load(ig)[io];pins=pinlist(dd,io);iv={'cell':icell,'bbox_dbu':[round(v*1000) for v in q['bbox_um']],'ports':{p:{'pin':p,'layer':81,'xy_dbu':[round(pins[p][1]),round(pins[p][2])]} for p in q['ports']}};assert all(pins[p][0]=='metal5' for p in q['ports'])
 for blob in lib.cells:
  n=next(v.rstrip(b'\0').decode() for t,d,v,b in __import__('assemble_gf180_full_capacity_storage_gds_v2').records(blob) if t==6);assert n not in cells;cells[n]=blob
 wrappers=[];replace={};removeplanes=set()
 for ai,old in enumerate(m['membrane_service_wrappers']):
  ap=[p for p in f['planes'] if p['actor']==old['actor'] and p['state_kind']!='membrane']
  if not ap:continue
  assert {p['state_kind'] for p in ap}=={'adaptation_age','adaptation_amplitude'}
  actor=next(p for p in old['modules'] if p['instance']=='ACTOR');ax,ay=actor['origin_dbu'];al=labels(cells[actor['cell']]);aliases={}
  for p,nativepin in [('ADAPT_AGE','AGE'),('ADAPT_AMPLITUDE','AMPLITUDE'),('ADAPT_AMP_BUF','AMP_BUF')]:
   l,x,y=al['adaptation_characterization__'+nativepin];assert l==81;aliases[p]={'pin':p,'layer':l,'xy_dbu':[x+ax,y+ay]}
  alias=old['cell']+'_ADAPT_PORTS';cells[alias]=begin(alias)+b''.join(b''.join(b for t,d,v,b in e) for e in elements(cells[old['cell']]))+b''.join(label(n,*v['xy_dbu']) for n,v in aliases.items())+rec(7,0)
  rv={'cell':alias,'source_cell':old['cell'],'bbox_dbu':old['bbox_dbu'],'ports':{p:old['ports'][p] for p in ['VDD','VSS','STORAGE_REFERENCE']}|aliases}
  rm={'VDD':'VDD','VSS':'VSS','STORAGE_REFERENCE':'VCM','ADAPT_AGE':'AGE','ADAPT_AMPLITUDE':'AMPLITUDE','ADAPT_AMP_BUF':'AMP_BUFFERED'};entries=[]
  for kind in ('AGE','AMP'):
   p=next(p for p in ap if p['state_kind']==('adaptation_age' if kind=='AGE' else 'adaptation_amplitude'));view=f['templates'][p['root_cell']];mapping={n:kind+'__'+n for n in view['ports']};mapping.update(VCM='VCM',VDD='VDD',VSS='VSS',RECOV=kind+'_RECOV');mapping.update({f'DATA{k}':f'{kind}_DATA{k}' for k in range(8)});entries.append((kind+'_FOREST',view,mapping));removeplanes.add(p['plane_index'])
  entries.extend([('RESIDENT',rv,rm),('IO',iv,{n:n for n in iv['ports']})]);body=[];mods=[];groups=collections.OrderedDict();row_y=0;maxright=0;row_escapes=[]
  for tag,v,mapping in entries:
   bb=v['bbox_dbu'];left=500000+len(v['ports'])*2000;ox=left-bb[0];oy=row_y-bb[1];top=row_y+bb[3]-bb[1];right=left+bb[2]-bb[0];maxright=max(maxright,right);body.append(reference(v['cell'],ox,oy));mods.append({'instance':tag,'cell':v['cell'],'source_cell':v.get('source_cell'),'origin_dbu':[ox,oy],'bbox_dbu':[left,row_y,right,top],'ports':v['ports'],'mapping':mapping,'interface_y_dbu':v.get('interface_y_dbu')});eys=[]
   for pi,(pin,pd) in enumerate(v['ports'].items()):
    assert pd['layer']==81;x,y=pd['xy_dbu'];x+=ox;y+=oy;sx=left-2000-pi*6000;ey=top+10000+pi*6400;body.extend([rect(81,(min(x,sx)-220,y-220,max(x,sx)+220,y+220)),via(81,46,41,sx,y),rect(46,(sx-200,min(y,ey)-200,sx+200,max(y,ey)+200)),via(46,81,41,sx,ey)]);groups.setdefault(mapping[pin],[]).append((tag,pin,sx,ey));eys.append(ey)
   row_escapes.append((left,eys,row_y));row_y=top+10000+len(v['ports'])*6400+100000
  field=row_y+100000;ports={};nets=[];spines=[];ground=None
  for ni,(net,ends) in enumerate(groups.items()):
   x=-20000-ni*6000;ty=field+ni*6400;ys=[];spines.append(x)
   for tag,pin,sx,ey in ends:body.extend([rect(81,(min(x,sx)-220,ey-220,max(x,sx)+220,ey+220)),via(81,46,41,x,ey)]);ys.append(ey)
   body.extend([rect(46,(x-200,min(ys+[ty])-220,x+200,max(ys+[ty])+220)),via(46,81,41,x,ty),rect(81,(x-1200,ty-220,x+1200,ty+220)),label(net,x-1000,ty)]);ports[net]={'pin':net,'layer':81,'xy_dbu':[x-1000,ty]};nets.append({'net':net,'endpoints':[tag+'.'+pin for tag,pin,*_ in ends]})
   if net=='VSS':ground=(x,ty)
  gy=field+len(groups)*6400+10000;gx,gty=ground;hx=min(spines)-50000
  for x in [xx+3000 for xx in spines]:body.extend([rect(46,(x-200,0,x+200,gy+220)),via(46,81,41,x,gy)])
  for left,ys,start_y in row_escapes:
   for a,b in zip(ys,ys[1:]):
    y=(a+b)//2;body.extend([rect(81,(hx-220,y-220,left-500,y+220)),via(81,46,41,hx,y)])
   # Local M4 pin risers also need grounded separation; otherwise a new
   # parent would recreate the control/state coupling fixed in the IO child.
   tie_y=(ys[0]+ys[1])//2
   for pi in range(len(ys)-1):
    x=left-5000-pi*6000;body.extend([rect(46,(x-200,start_y,x+200,max(ys)+220)),via(46,81,41,x,tie_y)])
  body.extend([rect(46,(hx-200,0,hx+200,gy+220)),via(46,81,41,hx,gy),rect(46,(gx-200,gty-220,gx+200,gy+220)),via(46,81,41,gx,gy),rect(81,(hx-220,gy-220,max(spines)+3220,gy+220))]);root=f'ESS_ADAPT_SERVICE_{ai:02d}_V12';cells[root]=begin(root)+b''.join(body)+rec(7,0);w={'cell':root,'actor':old['actor'],'kind':'adaptation_service','bbox_dbu':[hx-220,0,maxright,gy+220],'ports':ports,'modules':mods,'nets':nets,'native_parent_wiring_qualified':False,'active_adaptation_states':sum(p['active_states'] for p in ap),'source_membrane_wrapper':old['cell']};wrappers.append(w);replace[old['cell']]=w
 assert len(wrappers)==15 and sum(w['active_adaptation_states'] for w in wrappers)==21964800
 views=[]
 for p in m['top_placements']:
  if p['plane_index'] in removeplanes:continue
  if p['cell'] in replace:views.append(replace[p['cell']]);continue
  ox,oy=p['origin_dbu'];bb=p['bbox_dbu'];views.append({'cell':p['cell'],'kind':p['kind'],'bbox_dbu':[bb[0]-ox,bb[1]-oy,bb[2]-ox,bb[3]-oy]})
 free=[(0,0,3000000000,3000000000)];body=[];placed=[]
 for v in sorted(views,key=lambda v:max(v['bbox_dbu'][2]-v['bbox_dbu'][0],v['bbox_dbu'][3]-v['bbox_dbu'][1]),reverse=True):
  bb=v['bbox_dbu'];w=bb[2]-bb[0];h=bb[3]-bb[1];uw=w+1000000;uh=h+1000000;opts=[(min(fw-uw,fh-uh),max(fw-uw,fh-uh),y,x) for x,y,fw,fh in free if fw>=uw and fh>=uh];assert opts,('packing',v['cell']);_,_,y,x=min(opts);nf=[]
  for fx,fy,fw,fh in free:
   rr=fx+fw;tt=fy+fh
   if x>=rr or x+uw<=fx or y>=tt or y+uh<=fy:nf.append((fx,fy,fw,fh));continue
   if x>fx:nf.append((fx,fy,x-fx,fh))
   if x+uw<rr:nf.append((x+uw,fy,rr-x-uw,fh))
   if y>fy:nf.append((fx,fy,fw,y-fy))
   if y+uh<tt:nf.append((fx,y+uh,fw,tt-y-uh))
  free=[q for q in sorted(set(nf)) if not any(q!=z and z[0]<=q[0] and z[1]<=q[1] and z[0]+z[2]>=q[0]+q[2] and z[1]+z[3]>=q[1]+q[3] for z in nf)];ox=x-bb[0]-1500000000;oy=y-bb[1]-1500000000;body.append(reference(v['cell'],ox,oy));placed.append({'cell':v['cell'],'kind':v['kind'],'origin_dbu':[ox,oy],'bbox_dbu':[x-1500000000,y-1500000000,x+w-1500000000,y+h-1500000000]})
 top='ESS140K_ADAPTATION_SERVICE_V12';cells[top]=begin(top)+b''.join(body)+rec(7,0);reach={}
 def visit(n):
  if n in reach:return
  reach[n]=cells[n]
  for e in elements(cells[n]):
   for t,d,v,b in e:
    if t==18:visit(v.rstrip(b'\0').decode())
 visit(top);dest=D/'eventspikeseg140k_adaptation_service_v12.gds';dest.write_bytes(prefix+b''.join(reach.values())+rec(4,0));o={'top_cell':top,'checkpoint_sha256':m['checkpoint_sha256'],'active_analog_state_identities':54630400,'active_membrane_state_physical_compute_paths_preserved':30976000,'active_adaptation_state_physical_compute_paths_built':21964800,'adaptation_service_wrappers':wrappers,'top_placements':placed,'adaptation_parent_wiring_qualified':False,'full_chip_functional_layout_complete':False,'full_chip_layout_complete':False,'full_5ms_population_service_accepted':False,'original_float_accuracy_accepted':False,'scope':'AGE/AMPforests connectnativeIOrestore toexistingresidentadaptationAGE/AMPLITUDE andAMP_BUF;16analogholdoutputs feed8DATAcolumnsperplane. FifteencopiesofrepairedV6IO,existingV10membraneconnections andallresidentstatecomponents preserved. No parentRC/transient/phase/calibratedage-step claim. Classcurrent/globalgraph/parameters/sequencing remainopen. Researchatlas,notcompactdie.','sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,ff,sg,qf,ig,simfile,dest]}};(D/'physical_assembly.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({'gds':str(dest),'bytes':dest.stat().st_size,'adaptation_wrappers':15,'active_adaptation_states_physically_bound':21964800,'parent_wiring_qualified':False}))
if __name__=='__main__':main()
