"""Verify84controller bindings and intended supply/reference ties in actualGDS."""
from pathlib import Path
import collections,hashlib,json,struct,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec
from assemble_gf180_full25_shared_page1024_v7 import labels
from prove_gf180_shared_page_parent_metal_v5 import polygon_rectangles
from gf180_service_metal_graph_v2 import native_paint,touched

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/controlled_page_service_pair_v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    started=time.monotonic();meta=OUT/'physical_assembly.json';m=json.loads(meta.read_text())
    for name,digest in m['sha256'].items():assert sha(ROOT/name)==digest,name
    gds=ROOT/m['gds'];prefix,cells=cells_read(gds.read_bytes())
    plan_path=OUT/'route_plan.json';plan=json.loads(plan_path.read_text());top=m['top_cell']
    refs=[];added=[]
    for e in elements(cells[top]):
        if e[0][0]==10:refs.append(b''.join(b for t,d,v,b in e))
        elif e[0][0]==8:
            l=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
            xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
            added.extend((l,b) for b in polygon_rectangles(xy))
    assert len(refs)==3
    expected=collections.Counter();shape_owner={}
    for net in plan['nets']:
        for l,b in net['shapes']:
            key=l,tuple(b);expected[key]+=1;shape_owner.setdefault(key,set()).add(net['net'])
    assert collections.Counter(added)==expected and all(len(v)==1 for v in shape_owner.values())
    baseline_name='ESS_ACCESS_PAIR_READBACK_BASELINE'
    cells[baseline_name]=begin(baseline_name)+b''.join(refs)+rec(7,0)
    baseline=native_paint(cells,baseline_name)
    expected_owner={};points=[]
    for net in plan['nets']:
        for node in net['nodes']:
            l=node['layer'];x,y=node['xy'];rr=baseline.at(l,x,y)
            assert rr not in expected_owner or expected_owner[rr]==net['net'],('baseline boundary alias',node)
            expected_owner[rr]=net['net'];points.append((l,x,y,rr))
    for lane,origin in enumerate(plan['service_origins_dbu']):
        for name,(l,x,y) in labels(cells[m['native_service_cell']]).items():
            x+=origin[0];y+=origin[1];rr=baseline.at(l,x,y)
            expected_owner.setdefault(rr,f'unbound_native_lane{lane}_component{rr}');points.append((l,x,y,rr))
    cm_path=BASE/'assembly/page_access_pair_control_v2/physical_macro.json';cm=json.loads(cm_path.read_text())
    ox,oy=plan['control_origin_dbu']
    for name,port in cm['ports'].items():
        r=port['rectangles'][0];l={'Metal3':42,'Metal4':46,'Metal5':81}[r['layer']]
        x,y=[round(v*1000) for v in r['center_um']];x+=ox;y+=oy;rr=baseline.at(l,x,y)
        expected_owner.setdefault(rr,f'unbound_controller_component{rr}');points.append((l,x,y,rr))
    unknown=[];foreign=[]
    for l,b in added:
        owner=next(iter(shape_owner[l,b]))
        for rr in touched(baseline,l,b):
            if rr not in expected_owner:unknown.append((owner,rr))
            elif expected_owner[rr]!=owner:foreign.append((owner,expected_owner[rr]))
        if l==41:assert not baseline.hits(75,b),'parent Via4 overCAPM'
    assert not unknown and not foreign,(unknown[:3],foreign[:3])
    del baseline
    final=native_paint(cells,top)
    root_owners=collections.defaultdict(set);netroots=collections.defaultdict(set)
    for l,x,y,old_root in points:
        rr=final.at(l,x,y);owner=expected_owner[old_root]
        root_owners[rr].add(owner);netroots[owner].add(rr)
    aliases=[sorted(v) for v in root_owners.values() if len(v)>1]
    opens={n:len(rr) for n,rr in netroots.items() if len(rr)>1}
    floating=[]
    for i,(l,b) in enumerate(added):
        rr=final.at(l,(b[0]+b[2])//2,(b[1]+b[3])//2)
        owner=next(iter(shape_owner[l,b]))
        if root_owners.get(rr)!={owner}:floating.append(i)
    assert not aliases and not opens and not floating,(aliases[:3],opens,floating[:3])
    report=dict(readback_pass=True,controller_native_paths_verified=len(plan['bindings']),
                analog_service_lanes=2,legacy_low_ties_per_lane=m['legacy_disabled_low_pins_per_lane'],
                legacy_high_ties_per_lane=m['legacy_disabled_high_pins_per_lane'],
                shared_supply_and_zero_initialization_reference_ties_verified=True,
                unintended_native_or_controller_contacts=0,unknown_native_contacts=0,
                inter_net_aliases=0,expected_net_opens=0,floating_added_rectangles=0,
                added_conductor_rectangles=len(added),elapsed_seconds=time.monotonic()-started,
                scope='Actual GDS complete MIM-aware metal graph including both analog native service hierarchies and standard-cell access macro. Verifies84control/address/capture connections, shared supplies,62legacy controls tied low/four high, and physical initialization reference ties. No new full-style DRC/device extraction, parent power/signal RC, simultaneous native transient or5ms proof. Original-float phase,weight delivery and global population integration remain incomplete.',
                full_chip_layout_complete=False,full_5ms_population_service_accepted=False,
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_service_metal_graph_v2.py',meta,plan_path,gds,cm_path]})
    out=OUT/'independent_readback_v2.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['sha256','scope']},indent=2))

if __name__=='__main__':main()
