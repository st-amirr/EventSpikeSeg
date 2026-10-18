"""Render actual V31 GDS hierarchy with screen-size culling, without flattening arrays."""
from pathlib import Path
import mmap,struct,math,json,hashlib,time
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';O=B/'images'
SRC=B/'layout/EventSpikeSeg140k_GF180_Analog.gds';TOP='ESS140K_NATIVE_CONTROLS_V31'
PALETTE={22:'#866b4d',24:'#a58e69',30:'#e06666',31:'#d37090',32:'#a15aa2',33:'#e6ddd0',34:'#4c91db',35:'#d8e9fc',36:'#52c2b0',38:'#d4fff4',42:'#e6bb4c',40:'#fff5cf',46:'#ab79d6',41:'#f2d6ff',81:'#ef9660'}
def real8(b):return 0. if b==bytes(8) else (-1 if b[0]&128 else 1)*int.from_bytes(b[1:],'big')/(2**56)*16.**((b[0]&127)-64)
def union(a,b):
 if a is None:return b
 if b is None:return a
 return(min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3]))
def transformed(b,m):
 a,c,tx,d,e,ty=m;xs=[a*x+c*y+tx for x in (b[0],b[2]) for y in (b[1],b[3])];ys=[d*x+e*y+ty for x in (b[0],b[2]) for y in (b[1],b[3])];return min(xs),min(ys),max(xs),max(ys)
def compose(u,v):
 a,b,x,c,d,y=u;e,f,z,g,h,w=v;return(a*e+b*g,a*f+b*h,a*z+b*w+x,c*e+d*g,c*f+d*h,c*z+d*w+y)
def elem_iter(data,start,end):
 off=start;el=None
 while off<end:
  n,t,d=struct.unpack_from('>HBB',data,off);p=off+4
  if t in (8,9,10,11,12,45):el={'type':t,'start':off,'layer':0,'width':0,'flip':False,'angle':0.,'mag':1.,'cols':1,'rows':1}
  elif el is not None:
   if t==13:el['layer']=struct.unpack_from('>h',data,p)[0]
   elif t==15:el['width']=abs(struct.unpack_from('>i',data,p)[0])
   elif t==16:
    xy=struct.unpack_from('>'+str((n-4)//4)+'i',data,p);el['xy']=tuple(zip(xy[::2],xy[1::2]))
   elif t==18:el['child']=data[p:off+n].rstrip(b'\0').decode()
   elif t==19:el['cols'],el['rows']=struct.unpack_from('>hh',data,p)
   elif t==26:el['flip']=bool(struct.unpack_from('>H',data,p)[0]&0x8000)
   elif t==27:el['mag']=real8(data[p:off+n])
   elif t==28:el['angle']=real8(data[p:off+n])
   elif t==17:el['end']=off+n;yield el;el=None
  off+=n

def local_matrix(el,i=0,j=0):
 x,y=el['xy'][0]
 if el['type']==11:
  p,q=el['xy'][1:];x+=i*(p[0]-el['xy'][0][0])/el['cols']+j*(q[0]-el['xy'][0][0])/el['rows'];y+=i*(p[1]-el['xy'][0][1])/el['cols']+j*(q[1]-el['xy'][0][1])/el['rows']
 ang=math.radians(el['angle']);co=math.cos(ang)*el['mag'];si=math.sin(ang)*el['mag'];sg=-1 if el['flip'] else 1;return(co,-si*sg,x,si,co*sg,y)

def main():
 start=time.monotonic();O.mkdir(exist_ok=True);fh=SRC.open('rb');data=mmap.mmap(fh.fileno(),0,access=mmap.ACCESS_READ);cells={};off=0;name=None;begin=None;units=None
 while off<len(data):
  n,t,d=struct.unpack_from('>HBB',data,off);assert n>=4 and off+n<=len(data)
  if t==3:units=real8(data[off+12:off+20])*1e6
  elif t==5:begin=off
  elif t==6:name=data[off+4:off+n].rstrip(b'\0').decode()
  elif t==7:cells[name]={'start':begin,'end':off+n};name=None
  off+=n
 print(json.dumps({'indexed_cells':len(cells),'dbu_um':units,'seconds':time.monotonic()-start}),flush=True)
 assert TOP in cells and abs(units-.001)<1e-12
 def bbox(name):
  c=cells[name]
  if 'bbox' in c:return c['bbox']
  bb=None;refs=[];cnt=0
  for el in elem_iter(data,c['start'],c['end']):
   if el['type'] in (10,11):refs.append(el)
   elif el['type'] in (8,9,45) and el.get('xy'):
    xs,ys=zip(*el['xy']);w=el['width']/2 if el['type']==9 else 0;bb=union(bb,(min(xs)-w,min(ys)-w,max(xs)+w,max(ys)+w));cnt+=1
  for el in refs:
   child=bbox(el['child'])
   if child is not None:
    for i,j in {(0,0),(el['cols']-1,0),(0,el['rows']-1),(el['cols']-1,el['rows']-1)}:bb=union(bb,transformed(child,local_matrix(el,i,j)))
  c.update(bbox=bb,refs=refs,polygons=cnt);return bb
 full=bbox(TOP) if not (O/'full_layout_overview.png').exists() else None
 print(json.dumps({'top_bbox_dbu':full,'reusing_existing_overview':full is None,'seconds':time.monotonic()-start}),flush=True)
 fonts=Path('C:/Windows/Fonts');font=lambda s:ImageFont.truetype(str(fonts/'arial.ttf'),s)
 manifest={'source_gds':SRC.relative_to(R).as_posix(),'source_gds_sha256':hashlib.sha256(data).hexdigest(),'source_bytes':len(data),'top_cell':TOP,'dbu_um':units,'images':[],'method':'Actual GDS boundary/path polygons and exact hierarchical reference transforms. At overview scale small cell/array extents are approximated by hierarchy bounding rectangles; these are distinguished in the legend. No flattening or invented circuit geometry. Thin paths are enhanced to at least one display pixel. Native detail views use exact extracted GDS polygons. Research atlas extent is not compact die area.'}
 def render(name,title,subtitle,filename,W,H,threshold=2.):
  bb=bbox(name);padx=(bb[2]-bb[0])*.025;pady=(bb[3]-bb[1])*.025;bb=(bb[0]-padx,bb[1]-pady,bb[2]+padx,bb[3]+pady);im=Image.new('RGB',(W,H),'#0c1420');dr=ImageDraw.Draw(im);left,right,top,bottom=90,W-80,190,H-175;scale=min((right-left)/(bb[2]-bb[0]),(bottom-top)/(bb[3]-bb[1]));cx=(left+right)/2;cy=(top+bottom)/2;bx=(bb[0]+bb[2])/2;by=(bb[1]+bb[3])/2;stats={'polygons':0,'hierarchy_proxies':0,'references':0}
  def screen(x,y):return(cx+(x-bx)*scale,cy-(y-by)*scale)
  def screen_box(b):
   p=screen(b[0],b[3]);q=screen(b[2],b[1]);return(*p,*q)
  def visible(b):return not(b[2]<bb[0] or b[0]>bb[2] or b[3]<bb[1] or b[1]>bb[3])
  def proxy(b):
   q=screen_box(b);dr.rectangle((q[0],q[1],max(q[0]+.7,q[2]),max(q[1]+.7,q[3])),fill='#28465a',outline='#47728a');stats['hierarchy_proxies']+=1
  def visit(cell,m,depth=0):
   c=cells[cell];b=transformed(c['bbox'],m)
   if not visible(b):return
   if max(b[2]-b[0],b[3]-b[1])*scale<threshold:proxy(b);return
   stats['references']+=1;a,b1,x,d,e,y=m
   for el in elem_iter(data,c['start'],c['end']):
    if el['type'] not in (8,9,45) or not el.get('xy'):continue
    xs,ys=zip(*el['xy']);eb=transformed((min(xs),min(ys),max(xs),max(ys)),m)
    if not visible(eb):continue
    pts=[screen(a*u+b1*v+x,d*u+e*v+y) for u,v in el['xy']];color=PALETTE.get(el['layer'],'#52616e')
    if el['type']==9:dr.line(pts,fill=color,width=max(1,round(el['width']*scale*math.hypot(a,d))))
    else:dr.polygon(pts,fill=color)
    stats['polygons']+=1
   for el in c['refs']:
    child=cells[el['child']]['bbox']
    if child is None:continue
    array=None
    for i,j in {(0,0),(el['cols']-1,0),(0,el['rows']-1),(el['cols']-1,el['rows']-1)}:array=union(array,transformed(child,compose(m,local_matrix(el,i,j))))
    if not visible(array):continue
    extent=max(child[2]-child[0],child[3]-child[1])*el['mag']*math.hypot(a,d)*scale
    if extent<threshold:proxy(array);continue
    for j in range(el['rows']):
     for i in range(el['cols']):visit(el['child'],compose(m,local_matrix(el,i,j)),depth+1)
  visit(name,(1,0,0,0,1,0));dr.text((80,48),title,font=font(47),fill='#f4f7fa');dr.text((82,112),subtitle,font=font(23),fill='#a9bace')
  legend=[('M1','#4c91db'),('M2','#52c2b0'),('M3','#e6bb4c'),('M4','#ab79d6'),('M5','#ef9660'),('Hierarchy extents','#28465a')];lx=90
  for label,color in legend:dr.rectangle((lx,H-120,lx+25,H-95),fill=color);dr.text((lx+37,H-123),label,font=font(22),fill='#cbd7e3');lx+=90 if label.startswith('M') else 280
  target=(right-left)*.18/scale*units;ex=10**math.floor(math.log10(target));bar=max(v*ex for v in (1,2,5) if v*ex<=target);bw=bar/units*scale;xx=W-100-bw;yy=H-96;dr.line((xx,yy,xx+bw,yy),fill='#f4f7fa',width=5);dr.line((xx,yy-8,xx,yy+8),fill='#f4f7fa',width=3);dr.line((xx+bw,yy-8,xx+bw,yy+8),fill='#f4f7fa',width=3);label=f'{bar/1000:g} mm' if bar>=1000 else f'{bar:g} um';dr.text((xx,yy-38),label,font=font(22),fill='#f4f7fa');dr.text((90,H-61),'Actual GDS geometry  |  GF180  |  research implementation',font=font(20),fill='#8498ac');path=O/filename;im.save(path,dpi=(300,300));manifest['images'].append({'file':path.relative_to(R).as_posix(),'cell':name,'bbox_dbu':bbox(name),'pixel_size':[W,H],'render_stats':stats,'minimum_cell_size_pixels':threshold});print(json.dumps({'rendered':filename,'stats':stats,'seconds':time.monotonic()-start}),flush=True)
 if not (O/'full_layout_overview.png').exists():render(TOP,'EventSpikeSeg140k | full layout','V31 hierarchical research atlas - exact placement, with small hierarchy instances shown as extents','full_layout_overview.png',3200,2700,60.)
 for native,title,file in [('gf180_underplate_biased_bank8x8_v1','Membrane storage | one native 8 x 8 bank','membrane_bank_detail.png'),('gf180_neuron_five_module_parent_v6','PLIF | native update core','plif_core_detail.png')]:
  source=B/'components'/native/(native+'.gds');original=source.read_bytes();starts={};pos=0;st=None;nm=None
  while pos<len(original):
   size,typ,dt=struct.unpack_from('>HBB',original,pos)
   if typ==5:st=pos
   elif typ==6:nm=original[pos+4:pos+size].rstrip(b'\0').decode()
   elif typ==7:starts[nm]=(st,pos+size)
   pos+=size
  def signature(blob,lo,hi):
   h=hashlib.sha256();off=lo
   while off<hi:
    size,typ,dt=struct.unpack_from('>HBB',blob,off)
    if typ not in (5,6,7,18):h.update(blob[off:off+size])
    off+=size
   return h.hexdigest()
  lo,hi=starts[native];expected=signature(original,lo,hi);length=hi-lo;candidates=[n for n,c in cells.items() if length*.5<c['end']-c['start']<length*2 and signature(data,c['start'],c['end'])==expected]
  if candidates:
   chosen=candidates[0];bbox(chosen);render(chosen,title,'Native cell geometry matched directly inside the delivered V31 GDS',file,2800,1800 if 'bank' in native else 1050,.15)
  else:
   full_data,full_cells=data,cells;data=original;cells={n:{'start':a,'end':b} for n,(a,b) in starts.items()};bbox(native);render(native,title,'Qualified native component source GDS - local cell view',file,2800,1800 if 'bank' in native else 1050,.15);data,cells=full_data,full_cells
  manifest['images'][-1].update(native_source_cell=native,native_source_gds=source.relative_to(R).as_posix(),native_source_gds_sha256=hashlib.sha256(original).hexdigest(),geometry_signature=expected,matching_delivered_cells=candidates,source_scope='matched assembled GDS cell' if candidates else 'qualified native source component GDS; not an independently matched assembled-cell crop')
 if not any(x['file'].endswith('full_layout_overview.png') for x in manifest['images']):manifest['images'].insert(0,{'file':(O/'full_layout_overview.png').relative_to(R).as_posix(),'cell':TOP,'bbox_dbu':[-1507408450,-1507020230,-69180005,1421916180],'pixel_size':[3200,2700],'render_stats':{'polygons':9408979,'hierarchy_proxies':79180,'references':1049},'minimum_cell_size_pixels':60,'reused_from_completed_first_pass':True})
 manifest['elapsed_seconds']=time.monotonic()-start;(O/'render_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');data.close();fh.close()
if __name__=='__main__':main()
