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
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';S=B/'assembly/full25_adaptation_service_v12';F=B/'assembly/full_population_page_forest_v2';D=B/'assembly/full25_class_current_service_v13'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not D.exists();D.mkdir();mf=S/'physical_assembly.json';m=json.loads(mf.read_text());ff=F/'physical_forest.json';f=json.loads(ff.read_text());sg=S/'eventspikeseg140k_adaptation_service_v12.gds';prefix,cells=cells_read(sg.read_bytes());io='gf180_class_current_shared_io_v1';dd=B/'layout'/io;qf=dd/'qualification.json';q=json.loads(qf.read_text());assert q['source_and_GDS_exact_device_graphs_accepted'] and q['magic_drc_count']==q['gds_roundtrip_drc_count']==0;ig=dd/(io+'.gds');assert sha(ig)==q['sha256'][ig.name];lib=Library();icell=lib.load(ig)[io];pins=pinlist(dd,io);iv={'cell':icell,'bbox_dbu':[round(v*1000) for v in q['bbox_um']],'ports':{p:{'pin':p,'layer':81,'xy_dbu':[round(pins[p][1]),round(pins[p][2])]} for p in q['ports']}};assert all(pins[p][0]=='metal5' for p in q['ports'])
 readout='gf180_six_class_readout_v3';rd=B/'layout'/readout;rq=json.loads((rd/'qualification.json').read_text());rg=rd/(readout+'.gds');rcell=lib.load(rg)[readout];assert rcell in cells;rpins=pinlist(rd,readout);rv={'cell':rcell,'bbox_dbu':[round(v*1000) for v in rq['bbox_um']],'ports':{p:{'pin':p,'layer':81,'xy_dbu':[round(rpins[p][1]),round(rpins[p][2])]} for p in rq['ports']}};assert all(rpins[p][0]=='metal5' for p in rq['ports'])
 for blob in lib.cells:
  n=next(v.rstrip(b'\0').decode() for t,d,v,b in __import__('assemble_gf180_full_capacity_storage_gds_v2').records(blob) if t==6)
  if n in cells:assert cells[n]==blob
  else:cells[n]=blob
 plane=next(p for p in f['planes'] if p['state_kind']=='class_current');forest=f['templates'][plane['root_cell']];fm={p:'FOREST__'+p for p in forest['ports']};fm.update(VCM='STORAGE_REFERENCE',VDD='VDD',VSS='VSS',RECOV='RECOV');fm.update({f'DATA{k}':f'DATA{k}' for k in range(8)})
 rm={p:p for p in rv['ports']};rm['VRESET']='COMPUTE_REFERENCE'
 # Move the existing physical readout out of the auxiliary root exactly once.
 aux='ESS_PARAMETER_PROTOCOL_RETAINED_V10';ae=list(elements(cells[aux]));removed=[e for e in ae if any(t==18 and v.rstrip(b'\0').decode()==rcell for t,d,v,b in e)];assert len(removed)==1
 newaux='ESS_PARAMETER_PROTOCOL_RETAINED_V13';cells[newaux]=begin(newaux)+b''.join(b''.join(z for t,d,v,z in e) for e in ae if e not in removed)+rec(7,0)
 wrappers=[]
 for ai,unused in enumerate([0]):
  entries=[('FOREST',forest,fm),('READOUT',rv,rm),('IO',iv,{n:n for n in iv['ports']})];body=[];mods=[];groups=collections.OrderedDict();row_y=0;maxright=0;row_escapes=[]
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
  body.extend([rect(46,(hx-200,0,hx+200,gy+220)),via(46,81,41,hx,gy),rect(46,(gx-200,gty-220,gx+200,gy+220)),via(46,81,41,gx,gy),rect(81,(hx-220,gy-220,max(spines)+3220,gy+220))]);root='ESS_CLASS_CURRENT_SERVICE_V13';cells[root]=begin(root)+b''.join(body)+rec(7,0);w={'cell':root,'actor':'head.synapse','kind':'class_current_service','bbox_dbu':[hx-220,0,maxright,gy+220],'ports':ports,'modules':mods,'nets':nets,'native_parent_wiring_qualified':False,'active_class_current_states':1689600};wrappers.append(w)
 views=[]
 for p in m['top_placements']:
  if p['kind']=='class_current':assert p['cell']==plane['root_cell'];views.append(wrappers[0]);continue
  ox,oy=p['origin_dbu'];bb=p['bbox_dbu'];views.append({'cell':newaux if p['cell']==aux else p['cell'],'kind':p['kind'],'bbox_dbu':[bb[0]-ox,bb[1]-oy,bb[2]-ox,bb[3]-oy]})
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
 top='ESS140K_CLASS_CURRENT_SERVICE_V13';cells[top]=begin(top)+b''.join(body)+rec(7,0);reach={}
 def visit(n):
  if n in reach:return
  reach[n]=cells[n]
  for e in elements(cells[n]):
   for t,d,v,b in e:
    if t==18:visit(v.rstrip(b'\0').decode())
 visit(top);dest=D/'eventspikeseg140k_class_current_service_v13.gds';dest.write_bytes(prefix+b''.join(reach.values())+rec(4,0));o=dict(m);o.update(top_cell=top,top_placements=placed,class_current_service_wrapper=wrappers[0],active_class_current_physical_access_paths_built=1689600,all_numeric_state_access_paths_built=True,class_current_parent_wiring_qualified=False,full_chip_functional_layout_complete=False,full_chip_layout_complete=False,scope='Actual class forest RECOV joins shared native upshift/sixrestoreTGs to existing six-class workingstates; existing OUTPUTs join onehot sixTGmux/shared downshift/eightanalogholds back to forest DATA. Existing readout moved exactlyonce, allV12 membrane/adaptation geometry preserved. Native IO and readout independent module proofs; newparent wiring/RC/loading, trained synapses, globalgraph/operators/parameters/sequencer and modelaccuracy/5ms incomplete. Spacious research atlas, notcompactdie.');o['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,ff,sg,qf,ig,rg,dest]};(D/'physical_assembly.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({'gds':str(dest),'bytes':dest.stat().st_size,'class_current_states':1689600,'all_numeric_access_paths_built':True,'parent_wiring_qualified':False}))
if __name__=='__main__':main()
