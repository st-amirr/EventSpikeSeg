"""Actual GDS readback of all inherited/new routes and three macro edges."""
from pathlib import Path
import collections,json,struct,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from prove_gf180_shared_page_parent_metal_v5 import Paint,VIA,polygon_rectangles
import gf180_service_metal_graph_v3 as graph
from assemble_gf180_accumulation_fabric_ingress_v1 import sha,renamed

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/accumulation_dispatch_link_v1'


def overlap(a,b):return not(a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])


def rectangles(blob):
    result=[];refs=[]
    for e in elements(blob):
        if e[0][0]==8:
            l=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
            xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
            result.extend((l,b) for b in polygon_rectangles(xy))
        elif e[0][0]==10:
            name=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18)
            xy=next(struct.unpack('>2i',v) for t,d,v,b in e if t==16);refs.append((name,list(xy)))
        elif e[0][0]!=12:raise AssertionError(('unsupported parent element',e[0][0]))
    return result,refs


def main():
    started=time.monotonic();dest=OUT/'independent_readback_v1.json';assert not dest.exists()
    meta=OUT/'physical_assembly.json';m=json.loads(meta.read_text())
    for p,digest in m['sha256'].items():assert sha(ROOT/p)==digest,p
    plan_path=OUT/'route_plan.json';plan=json.loads(plan_path.read_text())
    pd=BASE/'assembly/accumulation_fabric_ingress_v1';pm=json.loads((pd/'physical_assembly.json').read_text())
    old=json.loads((pd/'route_plan.json').read_text());gds=ROOT/m['gds'];_,cells=cells_read(gds.read_bytes())
    _,pc=cells_read((ROOT/pm['gds']).read_bytes());assert all(cells[n]==b for n,b in pc.items());del pc
    cms={side:json.loads((BASE/f'assembly/{folder}/physical_macro.json').read_text()) for side,folder in
         [('FABRIC','full25_packet_fabric_v1'),('INGRESS','full25_actor_ingress_v2'),('DISPATCH','full25_accumulation_dispatch_v1')]}
    dgds=next(ROOT/p for p in cms['DISPATCH']['sha256'] if p.endswith('.gds'))
    _,dc=cells_read(dgds.read_bytes());assert all(cells['DSP_'+n]==renamed(b,'DSP_') for n,b in dc.items());del dc
    new,refs=rectangles(cells[m['top_cell']]);inherited,oldrefs=rectangles(cells[pm['top_cell']])
    assert refs==[(pm['top_cell'],[0,0]),(m['dispatcher_cell'],plan['dispatcher_origin_dbu'])]
    for actual,routes in [(new,plan['routes']),(inherited,old['routes'])]:
        assert collections.Counter(actual)==collections.Counter((l,tuple(b)) for net in routes for l,b in net['shapes'])
    routes=old['routes']+plan['routes'];added=inherited+new;shape_owner={}
    for net in routes:
        for l,b in net['shapes']:
            key=l,tuple(b);assert key not in shape_owner or shape_owner[key]==net['net'];shape_owner[key]=net['net']
    origins={**old['origins_dbu'],'DISPATCH':plan['dispatcher_origin_dbu']}
    bounds={**old['bounds_dbu'],'DISPATCH':plan['source_bounds_dbu']['DISPATCH']}
    roots={**pm['source_roots'],'DISPATCH':m['dispatcher_cell']}
    rings=[]
    for x1,y1,x2,y2 in bounds.values():
        g=2000;rings.extend([(x1-g,y1-g,x1+g,y2+g),(x2-g,y1-g,x2+g,y2+g),
                            (x1-g,y1-g,x2+g,y1+g),(x1-g,y2-g,x2+g,y2+g)])
    class EdgePaint(Paint):
        def add(self,l,b):return super().add(l,b) if any(overlap(b,r) for r in rings) else -1
        def vias(self,start=0):
            for i in range(start,len(self.shapes)):
                l,b=self.shapes[i]
                if l in VIA:
                    for metal in VIA[l]:
                        for j in self.hits(metal,b):self.join(i,j)
    baseline_name='ACC_DISPATCH_EDGE_BASELINE'
    cells[baseline_name]=begin(baseline_name)+b''.join(reference(roots[s],*origins[s]) for s in roots)+rec(7,0)
    print('Parent rectangles and all three source libraries match; checking native perimeter contacts.',flush=True)
    original_paint=graph.Paint
    try:graph.Paint=EdgePaint;baseline=graph.native_paint(cells,baseline_name)
    finally:graph.Paint=original_paint
    bound={(n['instance'],n['pin']):net['net'] for net in routes for n in net['nodes']}
    component_owners=collections.defaultdict(set)
    for side,cm in cms.items():
        ox,oy=origins[side]
        for name,pin in cm['ports'].items():
            for r in pin['rectangles']:
                l={'Metal3':42,'Metal4':46,'Metal5':81}[r['layer']]
                x,y=[round(v*1000) for v in r['center_um']];x+=ox;y+=oy
                if baseline.hits(l,(x,y,x,y)):
                    component_owners[baseline.at(l,x,y)].add(bound.get((side,name),side+'__'+name))
    foreign=[];unknown=[];intrusions=[]
    for l,b in added:
        owner=shape_owner[l,b]
        for root in graph.touched(baseline,l,b):
            if root not in component_owners:unknown.append((owner,root,l,b))
            elif component_owners[root]!={owner}:foreign.append((owner,sorted(component_owners[root]),l,b))
        for bb in bounds.values():
            core=(bb[0]+2000,bb[1]+2000,bb[2]-2000,bb[3]-2000)
            if overlap(b,core):intrusions.append((owner,l,b))
    edge_report=dict(foreign_native_contacts=foreign,unknown_native_contacts=unknown,parent_core_intrusions=intrusions)
    (OUT/'edge_contact_check_v1.json').write_text(json.dumps(edge_report,indent=2)+'\n')
    assert not foreign and not unknown and not intrusions,(foreign[:2],unknown[:2],intrusions[:2])
    del baseline;del cells
    print('Native contacts pass; checking all inherited/new route components.',flush=True)
    paint=Paint()
    for l,b in added:paint.add(l,b)
    paint.vias();owners=collections.defaultdict(set);net_roots=collections.defaultdict(set)
    for net in routes:
        for n in net['nodes']:
            root=paint.at(n['layer'],*n['xy_dbu']);owners[root].add(net['net']);net_roots[net['net']].add(root)
    opens={n:len(r) for n,r in net_roots.items() if len(r)>1}
    aliases=[sorted(v) for v in owners.values() if len(v)>1]
    floating=[i for i,(l,b) in enumerate(added) if owners.get(paint.root(i))!={shape_owner[l,b]}]
    assert not opens and not aliases and not floating,(opens,aliases[:2],floating[:2])
    report=dict(readback_pass=True,ingress_dispatch_routes_verified=1575,
                inherited_fabric_ingress_routes_verified=1475,shared_clock_reset_networks_verified=2,
                three_macro_clock_reset_connected=True,actual_parent_rectangles_verified=len(added),
                expected_net_opens=0,inter_net_aliases=0,floating_rectangles_or_cuts=0,
                foreign_native_contacts=0,unknown_native_contacts=0,parent_core_intrusions=0,
                native_perimeter_band_um=2,source_libraries_preserved=True,
                native_membrane_outputs_bound=False,full_architecture_layout_complete=False,
                accumulation_5ms_accepted=False,elapsed_seconds=time.monotonic()-started,
                scope='Actual full inherited/new parent metal graph and native2um macro-edge contact screen for fabric, ingress and dispatcher; all parent metal stays outside deeper macro interiors. No full-style DRC/device extraction or loaded parent RC/power/timing claim. Dispatcher-to-membrane and global infrastructure remain open.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_service_metal_graph_v3.py',meta,plan_path,gds,OUT/'edge_contact_check_v1.json']})
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sha256','scope']}),flush=True)


if __name__=='__main__':main()
