from pathlib import Path
import json,html
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfdoc import PDFStream,PDFDictionary,PDFName,PDFtrue,PDFfalse
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1];W=R/'artifacts/article_work/layout_vectors';F=R/'article/figures';pdfmetrics.registerFont(TTFont('LayoutSans','C:/Windows/Fonts/arial.ttf'))
def svgshape(sh):
 color,kind,pts,alpha=sh;style=f'fill="{color}" fill-opacity="1"'
 if kind=='r':
  x0,y0,x1,y1=pts;return f'<rect x="{x0:.9f}" y="{y0:.9f}" width="{x1-x0:.9f}" height="{y1-y0:.9f}" {style}/>'
 d=' '.join('M'+' L'.join(f'{x:.9f},{y:.9f}' for x,y in ring)+' Z' for ring in pts)
 return f'<path d="{d}" {style} fill-rule="evenodd"/>'
def pdfshape(c,sh):
 color,kind,pts,alpha=sh;c.setFillColor(HexColor(color))
 if kind=='r':
  x0,y0,x1,y1=pts;c.rect(x0,y0,x1-x0,y1-y0,stroke=0,fill=1)
 else:
  p=c.beginPath()
  for ring in pts:
   if not ring:continue
   p.moveTo(*ring[0])
   for pt in ring[1:]:p.lineTo(*pt)
   p.close()
  c.drawPath(p,stroke=0,fill=1,fillMode=0)
def render(data,native=False):
 reports=[];out=F if native else R/'article/supplementary_layout'
 for row in data['regions']:
  name=row['name'] if native else 'actor_%02d'%row['region'];x0,y0,x1,y1=row['bbox_mm'];pad=0 if native else max(x1-x0,y1-y0)*.012;x0-=pad;y0-=pad;x1+=pad;y1+=pad;ww=x1-x0;hh=y1-y0;k=1000/hh
  c=canvas.Canvas(str(out/(name+'.pdf')),pagesize=(ww*k,1000),pageCompression=1,initialFontName='LayoutSans');c.setTitle('EventSpikeSeg '+name);c.setFillColor(HexColor('#FFFFFF'));c.rect(0,0,ww*k,1000,stroke=0,fill=1)
  used={call[2] for call in row['calls'] if call[0]=='g'};defs=[];available=set()
  for key in sorted(used):
   for wire,suffix in [(False,'_d'),(True,'_w')]:
    shapes=[sh for sh in data['definitions'][key] if (sh[3]<1)==wire]
    if not shapes:continue
    form=key+suffix;available.add(form);defs.append('<g id="'+form+'">'+''.join(svgshape(sh) for sh in shapes)+'</g>');c.beginForm(form,-10000,-10000,10000,10000)
    for sh in shapes:pdfshape(c,sh)
    c.endForm()
  wireparts=[]
  c.beginForm('wire_overlay',x0,y0,x1,y1)
  for typ,m,payload in row['calls']:
   if typ!='g' or payload+'_w' not in available:continue
   c.saveState();c.transform(*m);c.doForm(payload+'_w');c.restoreState();tr='matrix('+','.join(f'{v:.12f}' for v in m)+')';wireparts.append(f'<use href="#{payload}_w" transform="{tr}"/>')
  c.endForm()
  overlay=c._doc.idToObject['FormXob.wire_overlay'];overlay.Contents=PDFStream(PDFDictionary({'Group':PDFDictionary({'S':PDFName('Transparency'),'I':PDFtrue,'K':PDFfalse,'CS':PDFName('DeviceRGB')})}),overlay.stream)
  c.scale(k,k);c.translate(-x0,-y0);parts=[]
  for typ,m,payload in row['calls']:
   c.saveState();c.transform(*m);tr='matrix('+','.join(f'{v:.12f}' for v in m)+')'
   if typ=='g':
    form=payload+'_d'
    if form in available:c.doForm(form);parts.append(f'<use href="#{form}" transform="{tr}"/>')
   else:
    bx0,by0,bx1,by1=payload;c.setFillColor(HexColor('#ABC5DE'));c.setStrokeColor(HexColor('#263F79'));c.setLineWidth(.12/k);c.rect(bx0,by0,bx1-bx0,by1-by0,stroke=1,fill=1);parts.append(f'<rect x="{bx0:.9f}" y="{by0:.9f}" width="{bx1-bx0:.9f}" height="{by1-by0:.9f}" fill="#ABC5DE" stroke="#263F79" stroke-width="{.12/k:.9f}" transform="{tr}"/>')
   c.restoreState()
  c.saveState();c.setFillAlpha(.3);c.doForm('wire_overlay');c.restoreState();parts.append('<g opacity="0.3">'+''.join(wireparts)+'</g>')
  c.showPage();c.save();svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{ww*k:.3f}" height="1000" viewBox="{x0:.9f} {-y1:.9f} {ww:.9f} {hh:.9f}"><title>{html.escape(name)}</title><desc>GDS-derived vector view; previously visible geometry retained; restored routes included. Small regional cells use hierarchy bounds.</desc><defs>'+''.join(defs)+'</defs><g transform="scale(1,-1)">'+''.join(parts)+'</g></svg>';(out/(name+'.svg')).write_text(svg);reports.append({key:value for key,value in row.items() if key!='calls'});print(name,(out/(name+'.pdf')).stat().st_size,flush=True)
  if not native:
   pass
 return reports
regions=render(json.loads((W/'geometry.json').read_text()));native=render(json.loads((W/'native_geometry.json').read_text()),True)
(R/'article/supplementary_layout/vector_manifest.json').write_text(json.dumps({'source_gds':'artifacts/analog_asic/layout/EventSpikeSeg140k_GF180_Analog.gds','source_sha256':'fb28eeb6bbc8901ad8594dcd4b5cc14450b7cae438bd5f239096c587f96d1d92','renderer':'KLayout GDS extraction and SVG/PDF vector paths; no raster image objects','scope':'Original regional hierarchy cutoffs retained. Interconnect is restored above the spatial extent cutoff, without thickness-based removal; internal geometry of collapsed cells remains summarized.','interconnect_layers':[34,36,42,46,81,35,38,40,41],'regions':regions},indent=2)+'\n')
(F/'native_interconnect_manifest.json').write_text(json.dumps({'method':'All-layer spatial GDS extraction; native geometry in exact requested windows, with interconnect composited after devices. No GDS changes.','views':native},indent=2)+'\n')

# Add captions to freshly rendered supplementary PDF artwork.
import runpy
runpy.run_path(str(R/'scripts/caption_article_layout_sections.py'),run_name='__main__')
