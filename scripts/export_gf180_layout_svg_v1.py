"""True vector SVG exports from GDS; preserve hierarchy with reusable SVG definitions."""
from pathlib import Path
import mmap,struct,math,json,hashlib,html,time
import render_gf180_delivered_gds_v1 as g
from resolve_asic_artifact_path import resolve_artifact
R=g.R;O=g.O;meta=json.loads((O/'render_manifest.json').read_text())
def f(x):return format(x,'.12g')
def index(data):
 cells={};off=0;start=None;name=None
 while off<len(data):
  n,t,d=struct.unpack_from('>HBB',data,off)
  if t==5:start=off
  elif t==6:name=data[off+4:off+n].rstrip(b'\0').decode()
  elif t==7:cells[name]={'start':start,'end':off+n}
  off+=n
 return cells

def export(data,cells,item):
 top=item['cell'];W,H=item['pixel_size'];threshold=item['minimum_cell_size_pixels'];title='EventSpikeSeg140k | full layout' if top==meta['top_cell'] else 'Membrane storage | one native 8 x 8 bank' if 'bank' in top else 'PLIF | native update core'
 subtitle='V31 hierarchical research atlas - vector hierarchy overview' if top==meta['top_cell'] else 'Qualified native component source GDS - vector cell view' if not item.get('matching_delivered_cells') else 'Native geometry matched inside delivered V31 GDS - vector cell view'
 def bbox(name):
  c=cells[name]
  if 'bbox' in c:return c['bbox']
  b=None;refs=[]
  for e in g.elem_iter(data,c['start'],c['end']):
   if e['type'] in (10,11):refs.append(e)
   elif e['type'] in (8,9,45) and e.get('xy'):
    xs,ys=zip(*e['xy']);w=e['width']/2 if e['type']==9 else 0;b=g.union(b,(min(xs)-w,min(ys)-w,max(xs)+w,max(ys)+w))
  for e in refs:
   child=bbox(e['child'])
   if child is not None:
    for i,j in {(0,0),(e['cols']-1,0),(0,e['rows']-1),(e['cols']-1,e['rows']-1)}:b=g.union(b,g.transformed(child,g.local_matrix(e,i,j)))
  c.update(bbox=b,refs=refs);return b
 bb=bbox(top);assert all(abs(a-b)<1e-6 for a,b in zip(bb,item['bbox_dbu']));dx=(bb[2]-bb[0])*.025;dy=(bb[3]-bb[1])*.025;vb=(bb[0]-dx,bb[1]-dy,bb[2]+dx,bb[3]+dy);left,right,up,down=90,W-80,190,H-175;scale=min((right-left)/(vb[2]-vb[0]),(down-up)/(vb[3]-vb[1]));tx=(left+right)/2-(vb[0]+vb[2])*scale/2;ty=(up+down)/2+(vb[1]+vb[3])*scale/2
 ids={n:'c'+str(i) for i,n in enumerate(cells)};done=set();stats={'cell_definitions':0,'unique_polygons':0,'reference_uses':0,'proxy_rectangles':0}
 def small(name):
  b=bbox(name);return max(b[2]-b[0],b[3]-b[1])*scale<threshold
 def proxy(b):
  stats['proxy_rectangles']+=1;return f'<rect x="{f(b[0])}" y="{f(b[1])}" width="{f(b[2]-b[0])}" height="{f(b[3]-b[1])}" fill="#28465a" stroke="#47728a" stroke-width="0.8" vector-effect="non-scaling-stroke"/>'
 def matrix(m):a,b,x,c,d,y=m;return 'matrix('+','.join(f(v) for v in (a,c,b,d,x,y))+')'
 dest=resolve_artifact(item['file']);dest=dest.with_suffix('.svg');assert not dest.exists();started=time.monotonic()
 with dest.open('w',encoding='utf-8',newline='\n') as out:
  out.write(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">\n<title id="title">{html.escape(title)}</title><desc id="desc">True vector GDS export. '+html.escape(subtitle)+'. Hierarchy boxes remain simplified at all zoom levels; no bitmap is embedded.</desc>\n')
  out.write('<metadata>'+html.escape(json.dumps({'source_gds':item.get('native_source_gds') if not item.get('matching_delivered_cells') and item.get('native_source_gds') else meta['source_gds'],'assembled_gds_sha256':meta['source_gds_sha256'],'cell':top,'minimum_hierarchy_size_at_overview_pixels':threshold,'raster_embedded':False,'scope':item.get('source_scope','assembled GDS hierarchical overview; atlas is not a compact die')}))+'</metadata>\n<defs>\n')
  def emit(name):
   if name in done:return
   done.add(name);c=cells[name];stats['cell_definitions']+=1
   if small(name):out.write(f'<g id="{ids[name]}">'+proxy(c['bbox'])+'</g>\n');return
   for e in c['refs']:
    if bbox(e['child']) is not None and not(e['type']==11 and small(e['child'])):emit(e['child'])
   out.write(f'<g id="{ids[name]}">\n');paths={};lines=[]
   for e in g.elem_iter(data,c['start'],c['end']):
    if e['type'] not in (8,9,45) or not e.get('xy'):continue
    pts=e['xy'];color=g.PALETTE.get(e['layer'],'#52616e');stats['unique_polygons']+=1
    if e['type']==9:
     lines.append('<polyline points="'+' '.join(f(x)+','+f(y) for x,y in pts)+'" fill="none" stroke="'+color+'" stroke-width="'+f(max(e['width'],1/scale))+'"/>');continue
    xs={x for x,y in pts};ys={y for x,y in pts}
    if len(pts)==5 and len(xs)==len(ys)==2:
     x1,x2=sorted(xs);y1,y2=sorted(ys);path='M'+f(x1)+','+f(y1)+'H'+f(x2)+'V'+f(y2)+'H'+f(x1)+'Z'
    else:path='M'+'L'.join(f(x)+','+f(y) for x,y in pts)+'Z'
    paths.setdefault(color,[]).append(path)
   for color,p in paths.items():out.write('<path fill="'+color+'" d="'+''.join(p)+'"/>\n')
   out.write('\n'.join(lines))
   for e in c['refs']:
    b=bbox(e['child'])
    if b is None:continue
    if e['type']==11 and small(e['child']):
     a=None
     for i,j in {(0,0),(e['cols']-1,0),(0,e['rows']-1),(e['cols']-1,e['rows']-1)}:a=g.union(a,g.transformed(b,g.local_matrix(e,i,j)))
     out.write(proxy(a)+'\n');continue
    for j in range(e['rows']):
     for i in range(e['cols']):out.write(f'<use href="#{ids[e["child"]]}" xlink:href="#{ids[e["child"]]}" transform="{matrix(g.local_matrix(e,i,j))}"/>\n');stats['reference_uses']+=1
   out.write('</g>\n')
  emit(top);out.write('</defs>\n');out.write(f'<rect width="{W}" height="{H}" fill="#0c1420"/><g transform="matrix({f(scale)},0,0,{f(-scale)},{f(tx)},{f(ty)})"><use href="#{ids[top]}" xlink:href="#{ids[top]}"/></g>\n')
  def text(x,y,value,size,color='#cbd7e3'):out.write(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, sans-serif" font-size="{size}">{html.escape(value)}</text>\n')
  text(80,91,title,47,'#f4f7fa');text(82,134,subtitle,23,'#a9bace');lx=90
  for label,color in [('M1','#4c91db'),('M2','#52c2b0'),('M3','#e6bb4c'),('M4','#ab79d6'),('M5','#ef9660'),('Hierarchy extents','#28465a')]:out.write(f'<rect x="{lx}" y="{H-120}" width="25" height="25" fill="{color}"/>');text(lx+37,H-101,label,22);lx+=90 if label.startswith('M') else 280
  target=(right-left)*.18/scale*.001;ex=10**math.floor(math.log10(target));bar=max(v*ex for v in (1,2,5) if v*ex<=target);bw=bar/.001*scale;xx=W-100-bw;yy=H-96;out.write(f'<path d="M{f(xx)},{yy}H{W-100} M{f(xx)},{yy-8}V{yy+8} M{W-100},{yy-8}V{yy+8}" fill="none" stroke="#f4f7fa" stroke-width="4"/>');text(f(xx),yy-15,f'{bar/1000:g} mm' if bar>=1000 else f'{bar:g} um',22,'#f4f7fa');text(90,H-42,'Vector GDS geometry | GF180 | research atlas, not compact die' if top==meta['top_cell'] else 'Vector GDS geometry | GF180 | native component',20,'#8498ac');out.write('</svg>\n')
 print(json.dumps({'svg':dest.name,'bytes':dest.stat().st_size,'stats':stats,'seconds':time.monotonic()-started}),flush=True);return dict(file=dest.relative_to(R).as_posix(),bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),stats=stats,source_scope=item.get('source_scope','assembled GDS overview'),embedded_raster=False)

def main():
 start=time.monotonic();results=[];source=resolve_artifact(meta['source_gds'])
 with source.open('rb') as fh:
  data=mmap.mmap(fh.fileno(),0,access=mmap.ACCESS_READ);assert hashlib.sha256(data).hexdigest()==meta['source_gds_sha256'];cells=index(data);print(json.dumps({'indexed_cells':len(cells),'seconds':time.monotonic()-start}),flush=True)
  for item in meta['images']:
   if item.get('native_source_gds') and not item.get('matching_delivered_cells'):
    original=resolve_artifact(item['native_source_gds']).read_bytes();assert hashlib.sha256(original).hexdigest()==item['native_source_gds_sha256'];results.append(export(original,index(original),item))
   else:results.append(export(data,cells,item))
  data.close()
 import xml.etree.ElementTree as ET
 for r in results:
  root=ET.parse(R/r['file']).getroot();assert not any(e.tag.rsplit('}',1)[-1]=='image' for e in root.iter());r['xml_parsed_and_no_raster_image_elements']=True
 (O/'svg_manifest.json').write_text(json.dumps({'source_gds_sha256':meta['source_gds_sha256'],'exports':results,'scope':'True vector counterparts of the PNG views. The full-layout hierarchy simplification remains fixed; zoom does not reveal omitted transistor geometry. Native component close-ups preserve drawn polygon geometry.','elapsed_s':time.monotonic()-start},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
