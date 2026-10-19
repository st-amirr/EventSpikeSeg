from pathlib import Path
import re,json,copy,xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfdoc import PDFStream,PDFDictionary,PDFName,PDFtrue,PDFfalse
R=Path(__file__).resolve().parents[1];F=R/'article/figures';W=R/'artifacts/article_work/interconnect_restore_20261019'
source=ET.parse(R/'artifacts/analog_asic/images/full_layout_overview.svg').getroot();crop=ET.parse(F/'old/gds_full_atlas_publication.svg').getroot();NS='{http://www.w3.org/2000/svg}';defs=source.find(NS+'defs');g=next(e for e in crop if e.tag==NS+'g')
num=r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
def nums(s):return [float(x) for x in re.findall(num,s)]
wire={'#4c91db','#d8e9fc','#52c2b0','#d4fff4','#e6bb4c','#fff5cf','#ab79d6','#f2d6ff','#ef9660'}
colors={'#28465a':'#abc5de','#47728a':'#263f79','#4c91db':'#2868a0','#d8e9fc':'#302b2b','#52c2b0':'#287a50','#d4fff4':'#302b2b','#e6bb4c':'#a46c00','#fff5cf':'#302b2b','#ab79d6':'#7d4f9f','#f2d6ff':'#302b2b','#ef9660':'#b73544'}
x0,y0,w,h=nums(crop.attrib['viewBox']);a,b,cc,d,ex,ey=nums(g.attrib['transform']);S=1e6;gs=abs(a)
pdfmetrics.registerFont(TTFont('OverviewSans','C:/Windows/Fonts/arial.ttf'));c=canvas.Canvas(str(F/'gds_full_atlas_indexed.pdf'),pagesize=(w,h),pageCompression=1,initialFontName='OverviewSans')
c.setTitle('EventSpikeSeg full layout overview');newdefs=ET.Element(NS+'defs')
def draw(e):
 tag=e.tag.split('}')[-1];at=e.attrib;c.saveState()
 if 'transform' in at:
  m=nums(at['transform']);c.transform(*m[:4],m[4]/S,m[5]/S)
 if tag=='use':c.doForm(at.get('href',at.get('{http://www.w3.org/1999/xlink}href')).lstrip('#'))
 elif tag in ('rect','path','polyline'):
  fill=at.get('fill','black');stroke=at.get('stroke','none')
  if fill!='none':c.setFillColor(HexColor(fill))
  if stroke!='none':c.setStrokeColor(HexColor(stroke));c.setLineWidth(float(at.get('stroke-width',1))/S/(gs if at.get('vector-effect')=='non-scaling-stroke' else 1))
  if tag=='rect':c.rect(*(float(at.get(k,0))/S for k in ['x','y','width','height']),stroke=int(stroke!='none'),fill=int(fill!='none'))
  else:
   p=c.beginPath()
   if tag=='polyline':
    xy=nums(at['points']);p.moveTo(xy[0]/S,xy[1]/S)
    for i in range(2,len(xy),2):p.lineTo(xy[i]/S,xy[i+1]/S)
   else:
    toks=re.findall(r'[MLHVZ]|'+num,at['d']);i=0;x=y=0
    while i<len(toks):
     op=toks[i];i+=1
     if op in ('M','L'):
      x=float(toks[i])/S;y=float(toks[i+1])/S;i+=2
      if op=='M':p.moveTo(x,y)
      else:p.lineTo(x,y)
     elif op=='H':x=float(toks[i])/S;i+=1;p.lineTo(x,y)
     elif op=='V':y=float(toks[i])/S;i+=1;p.lineTo(x,y)
     elif op=='Z':p.close()
     else:raise ValueError(op)
   c.drawPath(p,stroke=int(stroke!='none'),fill=int(fill!='none'))
 c.restoreState()
for e in defs:
 for iswire,suffix in [(False,'_d'),(True,'_w')]:
  out=ET.SubElement(newdefs,NS+'g',id=e.attrib['id']+suffix);c.beginForm(e.attrib['id']+suffix,-1e5,-1e5,1e5,1e5)
  for child in e:
   tag=child.tag.split('}')[-1];ch=copy.deepcopy(child)
   if tag=='use':
    for k in ['href','{http://www.w3.org/1999/xlink}href']:
     if k in ch.attrib:ch.attrib[k]+=suffix
   else:
    color=ch.attrib.get('fill',ch.attrib.get('stroke',''))
    if (color in wire)!=iswire:continue
    for k in ('fill','stroke'):
     if k in ch.attrib:ch.attrib[k]=colors.get(ch.attrib[k],ch.attrib[k])
   out.append(ch);draw(ch)
  c.endForm()
root=ET.Element(NS+'svg',{'width':str(w),'height':str(h),'viewBox':f'{x0} {y0} {w} {h}'})
ET.SubElement(root,NS+'title').text='EventSpikeSeg full layout overview'
ET.SubElement(root,NS+'desc').text='GDS-derived overview with original hierarchy proxies and native interconnect.'
root.append(newdefs);ET.SubElement(root,NS+'rect',x=str(x0),y=str(y0),width=str(w),height=str(h),fill='#ffffff')
c.setFillColor(HexColor('#ffffff'));c.rect(0,0,w,h,stroke=0,fill=1)
c.beginForm('overview_wire_overlay',0,0,w,h);c.translate(-x0,h+y0);c.scale(1,-1);c.transform(a*S,b*S,cc*S,d*S,ex,ey)
for ch in g:
 if ch.tag.endswith('use'):
  cp=copy.deepcopy(ch)
  for k in ('href','{http://www.w3.org/1999/xlink}href'):
   if k in cp.attrib:cp.attrib[k]+='_w'
  draw(cp)
c.endForm();overlay=c._doc.idToObject['FormXob.overview_wire_overlay'];overlay.Contents=PDFStream(PDFDictionary({'Group':PDFDictionary({'S':PDFName('Transparency'),'I':PDFtrue,'K':PDFfalse,'CS':PDFName('DeviceRGB')})}),overlay.stream)
c.saveState();c.translate(-x0,h+y0);c.scale(1,-1);c.transform(a*S,b*S,cc*S,d*S,ex,ey)
for ch in g:
 if ch.tag.endswith('use'):
  cp=copy.deepcopy(ch)
  for k in ('href','{http://www.w3.org/1999/xlink}href'):
   if k in cp.attrib:cp.attrib[k]+='_d'
  draw(cp)
c.restoreState();c.saveState();c.setFillAlpha(1.);c.doForm('overview_wire_overlay');c.restoreState()
for suffix in ('_d','_w'):
 gg=ET.SubElement(root,NS+'g',{'transform':g.attrib['transform'],**({})})
 for ch in g:
  cp=copy.deepcopy(ch)
  for k in ('href','{http://www.w3.org/1999/xlink}href'):
   if k in cp.attrib:cp.attrib[k]+=suffix
  gg.append(cp)
rows=json.loads((R/'article/supplementary_layout/manifest.json').read_text())['views']
for row in rows:
 box=row['bbox_dbu'];ox,oy=row['origin_top_dbu'];xx=ox+(box[0]+box[2])/2;yy=oy+(box[1]+box[3])/2;px=a*xx+cc*yy+ex;py=b*xx+d*yy+ey
 c.saveState();c.translate(px-x0,h+y0-py);c.setFillColor(HexColor('#ffffff'));c.setStrokeColor(HexColor('#302b2b'));c.setLineWidth(2);c.circle(0,0,37,stroke=1,fill=1);c.setFillColor(HexColor('#302b2b'));c.setFont('OverviewSans',48);c.drawCentredString(0,-16,str(row['actor_index']+1));c.restoreState()
 ET.SubElement(root,NS+'circle',cx=str(px),cy=str(py),r='37',fill='#ffffff',stroke='#302b2b',**{'stroke-width':'2'})
 ET.SubElement(root,NS+'text',x=str(px),y=str(py+16),fill='#302b2b',**{'font-family':'Arial','font-size':'48','text-anchor':'middle'}).text=str(row['actor_index']+1)
c.showPage();c.save();ET.register_namespace('',NS[1:-1]);ET.ElementTree(root).write(F/'gds_full_atlas_indexed.svg',encoding='unicode')
print('Overview PDF and SVG written.')

