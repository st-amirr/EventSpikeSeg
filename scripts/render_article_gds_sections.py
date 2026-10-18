"""KLayout section views; crops preserve all native geometry and do not reroute the design."""
from pathlib import Path
import pya,json,hashlib
R=Path(__file__).resolve().parents[1]; A=R/'artifacts/analog_asic'; O=R/'article/figures';rows=[]
def sections(path,cellname,regions,scope):
 v=pya.LayoutView();cv=v.load_layout(str(path),0);l=v.cellview(cv).layout();c=l.cell(cellname)
 if c is None:raise RuntimeError(cellname)
 v.select_cell(c.cell_index(),cv);v.max_hier();v.set_config('background-color','#ffffff');v.set_config('grid-visible','false');v.set_config('text-visible','false')
 for name,title,b in regions:
  v.zoom_box(pya.DBox(*b));w=2200;h=round(w*(b[3]-b[1])/(b[2]-b[0]));out=O/(name+'.png');v.save_image(str(out),w,h)
  rows.append({'figure':out.relative_to(R).as_posix(),'title':title,'source_gds':path.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cell':cellname,'requested_window_um':b,'width_um':b[2]-b[0],'height_um':b[3]-b[1],'scope':scope,'renderer':'KLayout LayoutView zoom_box and save_image','modified_layout':False})
  print('Rendered',name,flush=True)
 v.destroy()
sections(A/'components/gf180_signed_event_injection_v1/gf180_signed_event_injection_v1.gds','gf180_signed_event_injection_v1',[
 ('gds_injector_sources_detail','PMOS source devices',[-3,-6,28,5]),
 ('gds_injector_switch_detail','Transmission-gate device region',[98,-6,132,5])], 'Native injector component GDS, selected device windows; remote buses outside the crop')
sections(A/'layout/EventSpikeSeg140k_GF180_Analog.gds','N4f23af30_1319a4e94a058629',[
 ('gds_plif_threshold_detail','State/threshold section',[0,-6,42,40]),
 ('gds_plif_reset_detail','Reset steering section',[1595,-6,1660,5]),
 ('gds_plif_decision_detail','Sampled-decision section',[2490,-6,2570,5])], 'Actual delivered PLIF cell in V31 GDS; selected windows at original coordinates; long parent wiring outside crops')
(O/'gds_section_manifest.json').write_text(json.dumps({'views':rows,'interpretation':'Section views improve figure readability; no compaction, rerouting or physical optimization is claimed.'},indent=2)+'\n')
