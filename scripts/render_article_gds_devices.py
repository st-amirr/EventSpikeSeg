"""KLayout device-layer views. Hide interconnect for presentation; never write modified GDS."""
from pathlib import Path
import pya,json,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from article_gds_palette import apply_palette
R=Path(__file__).resolve().parents[1]; A=R/'artifacts/analog_asic'; O=R/'article/figures';rows=[]
def sections(path,cellname,regions,scope):
 v=pya.LayoutView();cv=v.load_layout(str(path),0);l=v.cellview(cv).layout();c=l.cell(cellname)
 if c is None:raise RuntimeError(cellname)
 v.select_cell(c.cell_index(),cv);v.max_hier();v.set_config('background-color','#ffffff');v.set_config('grid-visible','false');v.set_config('text-visible','false')
 apply_palette(v)
 hidden=[]
 it=v.begin_layers()
 while not it.at_end():
  lp=it.current()
  if lp.source_layer in [34,36,42,46,81,35,38,40,41]:
   hidden.append([lp.source_layer,lp.source_datatype]);lp.visible=False;v.set_layer_properties(it,lp)
  else:
   lp.width=6;v.set_layer_properties(it,lp)
  it.next()
 for name,title,b in regions:
  v.zoom_box(pya.DBox(*b));w=2200;h=round(w*(b[3]-b[1])/(b[2]-b[0]));out=O/(name.replace('_detail','_devices')+'.png');v.save_image(str(out),w,h)
  rows.append({'figure':out.relative_to(R).as_posix(),'title':title,'source_gds':path.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cell':cellname,'requested_window_um':b,'width_um':b[2]-b[0],'height_um':b[3]-b[1],'scope':scope,'renderer':'KLayout LayoutView zoom_box and save_image','modified_layout':False,'hidden_interconnect_layers':hidden,'view_type':'device layers; metal1-5 and via1-4 hidden'})
  print('Rendered',name,flush=True)
 v.destroy()
sections(A/'components/gf180_signed_event_injection_v1/gf180_signed_event_injection_v1.gds','gf180_signed_event_injection_v1',[
 ('gds_injector_sources_detail','PMOS source devices',[-1,-5,8,3]),
 ('gds_injector_switch_detail','Transmission-gate device region',[99,-5,129,3])], 'Native injector component GDS, selected device windows; remote buses outside the crop')
sections(A/'layout/EventSpikeSeg140k_GF180_Analog.gds','N4f23af30_1319a4e94a058629',[
 ('gds_plif_threshold_detail','State/threshold section',[12,-5,22,4]),
 ('gds_plif_reset_detail','Reset steering section',[1616,-5,1623,4]),
 ('gds_plif_decision_detail','Sampled-decision section',[2553,-5,2568,4])], 'Actual delivered PLIF cell in V31 GDS; selected windows at original coordinates; long parent wiring outside crops')
(O/'gds_device_manifest.json').write_text(json.dumps({'views':rows,'interpretation':'Interconnect is hidden by layer visibility for PLIF and injector figures; native 64-state bank image retains all wiring. Source GDS unchanged; this is not a connectivity view or physical optimization.'},indent=2)+'\n')
