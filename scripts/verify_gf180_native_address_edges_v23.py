"""Qualify added address-route contacts at the native dispatcher edge."""
from pathlib import Path
import collections,json,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
from prove_gf180_shared_page_parent_metal_v5 import Paint,VIA
from gf180_rect_index_v1 import touch,RectIndex
import gf180_service_metal_graph_v3 as graph

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_native_address_routes_v23'


def main():
    started=time.monotonic();dest=OUT/'native_edge_readback_v1.json';assert not dest.exists()
    proof=OUT/'parent_graph_readback_v1.json';p=json.loads(proof.read_text());assert p['parent_graph_readback_pass']
    for f,d in p['sha256'].items():assert sha(ROOT/f)==d,f
    plan=json.loads((OUT/'route_plan.json').read_text())
    inputs=json.loads((BASE/'assembly/native_address_route_inputs_v1/routing_inputs.json').read_text())
    cm_path=BASE/'assembly/full25_accumulation_dispatch_v1/physical_macro.json';cm=json.loads(cm_path.read_text())
    native=next(ROOT/f for f in cm['sha256'] if f.endswith('.gds'))
    assert sha(native)==cm['sha256'][native.relative_to(ROOT).as_posix()]
    _,cells=cells_read(native.read_bytes())
    sourcecell=inputs['nets'][0]['source']['cell'];assert sourcecell.startswith('DSP_');sourcecell=sourcecell[4:]
    bb=inputs['dispatcher_macro_bbox_dbu'];ox,oy=bb[:2]
    # Final macro bbox begins at zero; verify using actual port anchors below.
    bound={n['source']['pin']:n['net'] for n in inputs['nets']}
    for n in inputs['nets']:
        port=cm['ports'][n['source']['pin']]
        assert any([round(v*1000)+offset for v,offset in zip(r['center_um'],(ox,oy))]==n['source']['xy_top_dbu'] for r in port['rectangles'])
    x1,y1,x2,y2=bb;g=2000
    rings=[(x1-g,y1-g,x1+g,y2+g),(x2-g,y1-g,x2+g,y2+g),(x1-g,y1-g,x2+g,y1+g),(x1-g,y2-g,x2+g,y2+g)]
    class EdgePaint(Paint):
        def add(self,l,b):return super().add(l,b) if any(touch(b,r) for r in rings) else -1
        def vias(self,start=0):
            for i in range(start,len(self.shapes)):
                l,b=self.shapes[i]
                if l in VIA:
                    for metal in VIA[l]:
                        for j in self.hits(metal,b):self.join(i,j)
    top='NATIVE_ADDRESS_EDGE_BASELINE'
    cells[top]=begin(top)+reference(sourcecell,ox,oy)+rec(7,0)
    old=graph.Paint
    try:graph.Paint=EdgePaint;baseline=graph.native_paint(cells,top)
    finally:graph.Paint=old
    edge_index=RectIndex()
    for l,b in baseline.shapes:edge_index.add(l,b,None)
    edge_index.rebuild();baseline.hits=edge_index.hits
    print("Native perimeter parsed; checking contacts with sparse index",flush=True)
    owners=collections.defaultdict(set)
    for name,pin in cm['ports'].items():
        for r in pin['rectangles']:
            l={'Metal3':42,'Metal4':46,'Metal5':81}[r['layer']]
            x,y=[round(v*1000)+offset for v,offset in zip(r['center_um'],(ox,oy))]
            if baseline.hits(l,(x,y,x,y)):owners[baseline.at(l,x,y)].add(bound.get(name,'unbound__'+name))
    v15=json.loads((BASE/'assembly/full25_spike_breakouts_v15/physical_assembly.json').read_text())
    nativeboxes=[a['enclosing_top_bbox_dbu'] for a in v15['actors']]
    nativeboxes += [o['bbox_dbu'] for o in inputs['obstacles'] if o['kind'] not in ('categorical_control_and_parent_wiring',) and o['bbox_dbu'] not in list(inputs['actor_bounds_dbu'].values())]
    foreign=[];unknown=[];intrusions=[];contacts=set()
    core=(x1+g,y1+g,x2-g,y2-g)
    for n in plan['routes']:
        for l,b in n['shapes']:
            for root in (graph.touched(baseline,l,b) if any(touch(b,r) for r in rings) else ()):
                if root not in owners:unknown.append((n['net'],l,b))
                elif owners[root]!={n['net']}:foreign.append((n['net'],sorted(owners[root]),l,b))
                else:contacts.add(n['net'])
            if touch(b,core) or any(touch(b,o) for o in nativeboxes):intrusions.append((n['net'],l,b))
    report=dict(native_edge_readback_pass=not(foreign or unknown or intrusions) and len(contacts)==947,
                intended_dispatcher_contacts=len(contacts),foreign_contacts=foreign,unknown_contacts=unknown,core_intrusions=intrusions,
                elapsed_seconds=time.monotonic()-started,scope='Actual dispatcher2um perimeter contacts and native-wrapper core exclusion; parent graph and native1622M5escape corridor proofs separate. Not full DRC, global RC or analog timing.',
                sha256={f.relative_to(ROOT).as_posix():sha(f) for f in [Path(__file__),proof,cm_path,native,OUT/'route_plan.json']})
    dest.write_text(json.dumps(report,indent=2)+'\n')
    assert report['native_edge_readback_pass'],(len(foreign),len(unknown),len(intrusions),len(contacts))
    print(json.dumps({k:v for k,v in report.items() if k!='sha256'}),flush=True)


if __name__=='__main__':main()
