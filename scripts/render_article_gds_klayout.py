"""Run with KLayout -b -r; render actual GDS polygons for article figures."""
from pathlib import Path
import pya,json,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from article_gds_palette import apply_palette
R=Path(__file__).resolve().parents[1]
O=R/'article/figures'; O.mkdir(exist_ok=True)
A=R/'artifacts/analog_asic'
reports=[]
def render(path,cellname,name,scope):
 print('Loading',str(path),flush=True)
 view=pya.LayoutView()
 cv=view.load_layout(str(path),0)
 layout=view.cellview(cv).layout()
 cell=layout.cell(cellname)
 if cell is None:raise RuntimeError('Missing cell '+cellname)
 view.select_cell(cell.cell_index(),cv)
 view.max_hier()
 view.set_config('background-color','#ffffff')
 view.set_config('grid-visible','false')
 view.set_config('text-visible','false')
 apply_palette(view)
 view.zoom_fit()
 out=O/(name+'.png')
 box=cell.bbox()
 width=3200
 height=max(800,min(3200,round(width*box.height()/box.width())))
 view.save_image(str(out),width,height)
 box=cell.bbox()
 reports.append({'figure':out.relative_to(R).as_posix(),'source_gds':path.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cell':cellname,'dbu_um':layout.dbu,'bbox_dbu':[box.left,box.bottom,box.right,box.top],'width_um':box.width()*layout.dbu,'height_um':box.height()*layout.dbu,'renderer':'KLayout LayoutView.save_image','pixel_size':[width,height],'scope':scope,'geometry':'actual native GDS polygons; all cell hierarchy levels rendered'})
 print('Rendered',name,box.to_s(),flush=True)
 view.destroy()
render(A/'components/gf180_underplate_biased_bank8x8_v1/gf180_underplate_biased_bank8x8_v1.gds','gf180_underplate_biased_bank8x8_v1','gds_membrane_bank','Qualified native source-component layout, not independently matched to an assembled-cell crop')
render(A/'components/gf180_signed_event_injection_v1/gf180_signed_event_injection_v1.gds','gf180_signed_event_injection_v1','gds_signed_injector','Qualified native source-component layout')
render(A/'layout/EventSpikeSeg140k_GF180_Analog.gds','N4f23af30_1319a4e94a058629','gds_plif_core','Cell selected directly inside the delivered V31 GDS; native cell geometry matched in prior render manifest')
(O/'gds_figure_manifest.json').write_text(json.dumps({'figures':reports},indent=2)+'\n')
