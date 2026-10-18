"""Publication views from retained SVG geometry and saved SPICE traces; no new simulation."""
from pathlib import Path
import json,re,hashlib,xml.etree.ElementTree as ET
import numpy as np
from reportlab.graphics.shapes import Drawing,Line,PolyLine,String,Rect
from reportlab.graphics import renderSVG
from reportlab.lib.colors import HexColor
R=Path(__file__).resolve().parents[1]; O=R/'article/figures'; I=R/'artifacts/analog_asic/images'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
colors={'#0c1420':'#ffffff','#f4f7fa':'#302b2b','#a9bace':'#625d5d','#cbd7e3':'#302b2b','#8498ac':'#625d5d','#28465a':'#abc5de','#47728a':'#263f79','#4c91db':'#2868a0','#52c2b0':'#287a50','#e6bb4c':'#a46c00','#ab79d6':'#7d4f9f','#ef9660':'#b73544','#d4fff4':'#566475'}
rows=[]
for name in ['full_layout_overview','membrane_bank_detail','plif_core_detail']:
 p=I/(name+'.svg'); s=p.read_text(encoding='utf-8'); before=ET.fromstring(s)
 original_shapes=[(e.tag,{k:v for k,v in e.attrib.items() if k in ['d','points','transform','x','y','width','height','href','{http://www.w3.org/1999/xlink}href']}) for e in before.find('{http://www.w3.org/2000/svg}defs').iter()]
 for a,b in colors.items():s=s.replace(a,b)
 out=I/(name+'_publication.svg');out.write_text(s,encoding='utf-8')
 after=ET.fromstring(s)
 shapes=[(e.tag,{k:v for k,v in e.attrib.items() if k in ['d','points','transform','x','y','width','height','href','{http://www.w3.org/1999/xlink}href']}) for e in after.find('{http://www.w3.org/2000/svg}defs').iter()]
 assert original_shapes==shapes
 rows.append({'source':p.relative_to(R).as_posix(),'output':out.relative_to(R).as_posix(),'source_sha256':sha(p),'output_sha256':sha(out),'geometry_definitions_unchanged':True})
 if name=='full_layout_overview':
  # A cropped paper view reuses the identical GDS-derived geometry and affine transform.
  defs=re.search(r'<defs>.*?</defs>',s,re.S)[0]
  group=re.search(r'</defs>\s*<rect[^>]*/>(<g transform=.*?</g>)',s,re.S)[1]
  crop='<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="2380" viewBox="1000 180 1200 2380"><rect x="1000" y="180" width="1200" height="2380" fill="white"/>'+defs+group+'<path d="M1100,2510H1479.62748461 M1100,2498V2522 M1479.62748461,2498V2522" stroke="#302b2b" stroke-width="5" fill="none"/><text x="1100" y="2486" font-family="Arial" font-size="34" fill="#302b2b">500 mm (atlas coordinates)</text></svg>'
  (O/'gds_full_atlas_publication.svg').write_text(crop,encoding='utf-8')
# Plot actual binary trace, preserving evidence/hash links.
p=R/'artifacts/analog_asic/evidence/module_results/selected_accumulation_retention_v2/waveforms.raw'
b=p.read_bytes();head,raw=b.split(b'Binary:\n',1);h=head.decode();nv=int(re.search(r'No. Variables:\s*(\d+)',h)[1]);names=[l.split()[1] for l in h.split('Variables:\n')[1].splitlines() if l.strip()];a=np.frombuffer(raw,dtype='<f8').reshape(-1,nv);t=a[:,0]
def v(n):return a[:,names.index('v('+n+')')]
state=v('state70');compute=v('c_state');start=230e-6;base=float(np.interp(start,t,state))
D=Drawing(1100,400); D.add(Rect(0,0,1100,400,fillColor=HexColor('#ffffff'),strokeColor=None)); ink='#302b2b';green='#287a50';purple='#7d4f9f';blue='#2868a0'
def text(x,y,s,size=13,color=ink,anchor='start'):D.add(String(x,y,s,fontName='Helvetica',fontSize=size,fillColor=HexColor(color),textAnchor=anchor))
def panel(x0,y0,w,hh,xlim,ylim,xticks,yticks,xlabel,ylabel,title):
 def xy(x,y):return x0+(x-xlim[0])*w/(xlim[1]-xlim[0]),y0+(y-ylim[0])*hh/(ylim[1]-ylim[0])
 for yy in yticks:
  y=xy(xlim[0],yy)[1];D.add(Line(x0,y,x0+w,y,strokeColor=HexColor('#dddddd'),strokeWidth=.6));text(x0-8,y-4,f'{yy:g}',12,anchor='end')
 for xx in xticks:
  x=xy(xx,ylim[0])[0];D.add(Line(x,y0,x,y0-4,strokeColor=HexColor(ink)));text(x,y0-22,f'{xx:g}',12,anchor='middle')
 D.add(Line(x0,y0,x0+w,y0,strokeColor=HexColor(ink)));D.add(Line(x0,y0,x0,y0+hh,strokeColor=HexColor(ink)))
 text(x0+w/2,y0-46,xlabel,14,anchor='middle');text(x0,y0+hh+18,ylabel,13);text(x0,y0+hh+49,title,16)
 return xy
xy=panel(65,70,450,240,(60,240),(0.9,2.0),[60,100,140,180,220],[1.0,1.2,1.4,1.6,1.8,2.0],'Time from transient start (us)','Voltage (V)','(a) Signed update and row commit')
for vals,col in [(compute,purple),(state,green)]:
 mask=(t>=60e-6)&(t<=240e-6);D.add(PolyLine([q for xx,yy in zip(t[mask]*1e6,vals[mask]) for q in xy(xx,yy)],strokeColor=HexColor(col),strokeWidth=1.8))
for xx,lab,col in [(97,'+5 us',blue),(110,'-3 us','#b73544')]:
 x=xy(xx,1.7)[0];D.add(Line(x,70,x,310,strokeColor=HexColor(col),strokeWidth=.7,strokeDashArray=[3,3]));text(x+3,320,lab,11,col)
text(295,297,'Compute state',12,purple);text(390,297,'Stored state',12,green)
xy2=panel(630,70,425,240,(0,5),(0,.6),[0,1,2,3,4,5],[0,.2,.4,.6],'Time after commit (ms)','Stored-state change (mV)','(b) Selected-state retention')
mask=t>=start;tx=np.r_[0,(t[mask]-start)*1000];vy=np.r_[0,(state[mask]-base)*1000]
D.add(PolyLine([q for xx,yy in zip(tx,vy) for q in xy2(xx,yy)],strokeColor=HexColor(green),strokeWidth=2))
text(820,120,'0.531 mV after 5 ms',14,green)
renderSVG.drawToFile(D,str(O/'selected_state_transient.svg'))
report={'layout_palette':colors,'svg_views':rows,'layout_policy':'Geometry retained; white background and darker layer colors. Full view retains fixed hierarchy proxies; article crop only removes canvas margins.','waveform':{'source':p.relative_to(R).as_posix(),'source_sha256':sha(p),'samples':len(t),'plot':'article/figures/selected_state_transient.svg','baseline_V':base,'end_hold_drift_mV':float((state[-1]-base)*1000),'conditions':'3.3 V, 27 C, typical GF180; extracted native capacitance; external pulse fixture; mismatch disabled; no global atlas RC','new_simulation':False}}
(O/'article_review_figure_manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'svg_views':len(rows),'trace_samples':len(t),'drift_mV':report['waveform']['end_hold_drift_mV']}))
