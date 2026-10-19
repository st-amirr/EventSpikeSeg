from pathlib import Path
import pya,json,sys,math
R=Path('/workspace');sys.path.insert(0,str(R/'scripts'));from article_gds_palette import PALETTE
l=pya.Layout();l.read(str(R/'artifacts/analog_asic/layout/EventSpikeSeg140k_GF180_Analog.gds'))
rows=json.loads((R/'article/supplementary_layout/manifest.json').read_text())['views'];S=1e6;out=R/'artifacts/article_work/layout_vectors';geoms={};reports=[];out.mkdir(parents=True,exist_ok=True)
def boxvals(b):return [b.left/S,b.bottom/S,b.right/S,b.top/S]
def matrix(t):
 a=math.radians(t.angle);cs=math.cos(a)*t.mag;sn=math.sin(a)*t.mag
 return [cs,sn,sn if t.is_mirror() else -sn,-cs if t.is_mirror() else cs,t.disp.x/S,t.disp.y/S]
def geometry(c,cut):
 key=(c.cell_index(),round(cut,9))
 if key in geoms:return geoms[key]
 shapes=[]
 for li in l.layer_indexes():
  wire=l.get_info(li).layer in [34,36,42,46,81,35,38,40,41]
  opacity=1.0
  color='#%06x'%PALETTE.get(l.get_info(li).layer,0x263F79)
  for sh in c.shapes(li).each():
   if sh.is_text():continue
   b=sh.bbox()
   if max(b.width(),b.height())/S<cut/25:continue
   if not wire and sh.is_box() and min(b.width(),b.height())/S<cut/25:continue
   if sh.is_box():
    opacity=.3 if wire and min(b.width(),b.height())/S<cut/25 else 1.0
    shapes.append([color,'r',boxvals(b),opacity])
   elif sh.is_polygon() or sh.is_simple_polygon() or sh.is_path():
    poly=sh.path.polygon() if sh.is_path() else sh.polygon
    if not wire and abs(poly.area())/S/S/max(max(b.width(),b.height())/S,1e-12)<cut/25:continue
    opacity=.3 if wire and abs(poly.area())/S/S/max(max(b.width(),b.height())/S,1e-12)<cut/25 else 1.0
    rings=[[[p.x/S,p.y/S] for p in poly.each_point_hull()]]
    for hole in range(poly.holes()):rings.append([[p.x/S,p.y/S] for p in poly.each_point_hole(hole)])
    shapes.append([color,'p',rings,opacity])
 name='g'+str(len(geoms));geoms[key]=(name,shapes);return name,shapes
for row in rows:
 c=l.cell(row['breakout_cell']);b=c.bbox();extent=max(b.width(),b.height())/S;cut=row['cutoff_mm']
 for attempt in range(1):
  calls=[];proxy=0;cost=0;overflow=False
  def walk(ci,t,depth):
   global proxy,cost,overflow
   if overflow:return
   cc=l.cell(ci);bb=cc.bbox()
   if depth==8 or max(bb.width(),bb.height())/S*t.mag<=cut:
    calls.append(['r',matrix(t),boxvals(bb)]);proxy+=1;cost+=1
   else:
    name,shape=geometry(cc,cut/max(t.mag,1e-12))
    children=list(cc.each_inst())
    if shape:calls.append(['g',matrix(t),name]);cost+=len(shape)
    if not any(sh[3]>=1 for sh in shape) and not children and not bb.empty():
     calls.append(['r',matrix(t),boxvals(bb)]);proxy+=1;cost+=1
    for inst in children:
     for tr in inst.cell_inst.each_cplx_trans():walk(inst.cell_index,t*tr,depth+1)
     if overflow:break
   if cost>100000000:overflow=True
  walk(c.cell_index(),pya.ICplxTrans(),0)
  if not overflow:break
  cut*=2
 if overflow:raise RuntimeError('Vector budget exceeded')
 report={'region':row['actor_index']+1,'actor':row['actor'],'cell':row['breakout_cell'],'bbox_mm':boxvals(b),'calls':calls,'cutoff_mm':cut,'minimum_shape_extent_mm':cut/25,'vector_primitives':cost,'macro_outlines':proxy,'maximum_depth':8}
 reports.append(report);print('Region',report['region'],'primitives',cost,'cutoff mm',cut,flush=True)
(out/'geometry.json').write_text(json.dumps({'definitions':{name:shape for name,shape in geoms.values()},'regions':reports,'source_gds':'artifacts/analog_asic/layout/EventSpikeSeg140k_GF180_Analog.gds','source_sha256':'fb28eeb6bbc8901ad8594dcd4b5cc14450b7cae438bd5f239096c587f96d1d92'},separators=(',',':')))
