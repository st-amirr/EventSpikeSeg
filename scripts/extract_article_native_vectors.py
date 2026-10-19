from pathlib import Path
import pya,json,sys
R=Path('/workspace');sys.path.insert(0,str(R/'scripts'));from article_gds_palette import PALETTE
S=1e6;w=R/'artifacts/article_work/layout_vectors';device=json.loads((R/'article/figures/gds_device_manifest.json').read_text())['views'];rows=[];definitions={};layouts={}
for row in device:
 rows.append({'name':Path(row['figure']).stem,'source_gds':row['source_gds'],'cell':row['cell'],'window_um':row['requested_window_um']})
bank=json.loads((R/'article/figures/gds_figure_manifest.json').read_text())['figures'][0]
rows.append({'name':'gds_membrane_bank','source_gds':bank['source_gds'],'cell':bank['cell'],'window_um':[v*.001 for v in bank['bbox_dbu']]})
w.mkdir(parents=True,exist_ok=True)
reports=[]
for row in rows:
 key=row['source_gds']
 if key not in layouts:
  ll=pya.Layout();ll.read(str(R/key));layouts[key]=ll
 ll=layouts[key];cc=ll.cell(row['cell']);box=pya.Box(*[round(v/ll.dbu) for v in row['window_um']]);shapes=[];wirecount=0
 for li in ll.layer_indexes():
  wire=ll.get_info(li).layer in [34,36,42,46,81,35,38,40,41];alpha=.3 if wire and row['name']!='gds_membrane_bank' else 1.;color='#%06x'%PALETTE.get(ll.get_info(li).layer,0x263F79)
  it=cc.begin_shapes_rec_overlapping(li,box)
  while not it.at_end():
   sh=it.shape()
   if sh.is_box() or sh.is_polygon() or sh.is_simple_polygon() or sh.is_path():
    poly=(pya.Polygon(sh.box) if sh.is_box() else sh.path.polygon() if sh.is_path() else sh.polygon).transformed(it.trans())
    rings=[[[pt.x/S,pt.y/S] for pt in poly.each_point_hull()]]
    for hole in range(poly.holes()):rings.append([[pt.x/S,pt.y/S] for pt in poly.each_point_hole(hole)])
    shapes.append([color,'p',rings,alpha]);wirecount+=int(wire)
   it.next()
 name='native'+str(len(reports));definitions[name]=shapes;coords=[v*.001 for v in row['window_um']];reports.append(dict(row,region=len(reports)+1,actor=row['name'],bbox_mm=coords,calls=[['g',[1,0,0,1,0,0],name]],cutoff_mm=0,vector_primitives=len(shapes),interconnect_primitives=wirecount));print(row['name'],len(shapes),'wire',wirecount,flush=True)
(w/'native_geometry.json').write_text(json.dumps({'definitions':definitions,'regions':reports},separators=(',',':')))
