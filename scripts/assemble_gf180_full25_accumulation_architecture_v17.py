"""Integrate routed event/ingress pair into the full physical state architecture.

The inherited 25 spike routes are rebuilt with M1 vertical/M2 horizontal outer
channels, keeping their native M5 source/M3-or-M4 destination approaches.
This separates them from the new M3/M4/M5 event ingress parent wiring.
"""
from pathlib import Path
import json
import time
from assemble_gf180_one_neuron_page_link_v1 import gds_library_parts
from assemble_gf180_full_capacity_storage_gds_v2 import begin, rec, reference
from assemble_gf180_full25_physical_candidate_v5 import rect, label
from assemble_gf180_accumulation_fabric_ingress_v1 import sha, via

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'
OUT = BASE/'assembly/full25_accumulation_architecture_v17'


def wire(layer,a,b):
    assert a[0]==b[0] or a[1]==b[1]
    half = 220 if layer==81 else 140
    return layer,(min(a[0],b[0])-half,min(a[1],b[1])-half,
                  max(a[0],b[0])+half,max(a[1],b[1])+half)


def main():
    started=time.monotonic()
    pair_dir=BASE/'assembly/accumulation_fabric_ingress_v1'
    pair_meta=pair_dir/'physical_assembly.json'; pair=json.loads(pair_meta.read_text())
    pair_proof=pair_dir/'independent_readback_v1.json'
    assert json.loads(pair_proof.read_text())['readback_pass']
    pair_gds=ROOT/pair['gds']; assert sha(pair_gds)==pair['sha256'][pair['gds']]
    old_meta=BASE/'assembly/full25_spike_graph_v16/physical_assembly.json'
    old=json.loads(old_meta.read_text())
    old_proof=BASE/'assembly/full25_spike_graph_v16/gds_incremental_connectivity_v1.json'
    assert json.loads(old_proof.read_text())['actual_gds_incremental_spike_connectivity_pass']
    analog_meta=BASE/'assembly/full25_spike_breakouts_v15/physical_assembly.json'
    analog=json.loads(analog_meta.read_text()); analog_gds=ROOT/analog['gds']
    assert sha(analog_gds)==analog['sha256'][analog['gds']]
    assert not OUT.exists(); OUT.mkdir(parents=True)
    origin=old['fabric_origin_dbu']; body=reference(analog['top_cell'],0,0)+reference(pair['top_cell'],*origin)
    routes=[]; shapes=[]
    for old_route in old['routes']:
        points=[tuple(p) for p in old_route['points_dbu']]
        first=points[0]; last=points[-1]
        segments=[]; added=[]
        for index,(a,b) in enumerate(zip(points,points[1:])):
            if index==0: layer=81
            elif index==len(points)-2: layer=old_route['destination']['layer']
            else: layer=36 if a[1]==b[1] else 34
            shape=wire(layer,a,b); added.append(shape)
            segments.append(dict(layer=layer,start_dbu=a,end_dbu=b))
        for index in range(len(segments)-1):
            a,b=segments[index]['layer'],segments[index+1]['layer']; point=points[index+1]
            if a==b: continue
            chain=[34,36,42,46,81]; cuts=[35,38,40,41]
            ia,ib=sorted([chain.index(a),chain.index(b)])
            for j in range(ia,ib): added+=via(chain[j],chain[j+1],cuts[j],point)
        assert segments[0]['layer']==81
        assert segments[-1]['layer']==old_route['destination']['layer']
        name=f'ACTOR_{old_route["actor_index"]:02d}_SPIKE'
        body+=b''.join(rect(l,b) for l,b in added)+label(name,*first)
        shapes.extend((name,l,b) for l,b in added)
        routes.append(dict(net=name,actor_index=old_route['actor_index'],actor=old_route['actor'],
                           source=old_route['source'],destination=old_route['destination'],
                           points_dbu=points,segments=segments,shapes=added))
    # Cross-check every new spike rectangle against actual planned pair conductors.
    pair_plan_path=pair_dir/'route_plan.json'; pp=json.loads(pair_plan_path.read_text())
    conflicts=[]
    from prove_gf180_shared_page_parent_metal_v5 import VIA
    for owner,l,b in shapes:
        for net in pp['routes']:
            for other,c in net['shapes']:
                adjacent=(l==other or other in VIA.get(l,()) or l in VIA.get(other,()))
                if not adjacent: continue
                q=(c[0]+origin[0],c[1]+origin[1],c[2]+origin[0],c[3]+origin[1])
                guard=460 if l==other==81 else 280 if l==other and l in [34,36,42,46] else 260 if l==other else 0
                if not (b[2]+guard<q[0] or b[0]-guard>q[2] or b[3]+guard<q[1] or b[1]-guard>q[3]):
                    conflicts.append((owner,net['net'],l,b,other,q))
    plan=dict(routes=routes,new_rectangles=len(shapes),pair_origin_dbu=origin,
              pair_cross_contact_conflicts=conflicts,original_spike_connection_count_preserved=25,
              scope='Inherited outer route centerlines with M1/M2 channels and unchanged native source/destination approach layers. Incremental GDS connectivity/spacing check required.')
    (OUT/'route_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    assert not conflicts,conflicts[:3]
    ah,ac,an=gds_library_parts(analog_gds); ph,pc,pn=gds_library_parts(pair_gds)
    assert an.isdisjoint(pn),an&pn
    top='ESS140K_ACCUMULATION_ARCHITECTURE_V17'
    gds=OUT/'eventspikeseg140k_accumulation_architecture_v17.gds'
    with gds.open('wb') as stream:
        stream.write(ah);stream.write(ac);stream.write(pc)
        stream.write(begin(top)+body+rec(7,0)+rec(4,0))
    report=dict(top_cell=top,gds=gds.relative_to(ROOT).as_posix(),gds_bytes=gds.stat().st_size,
                physical_actor_count=25,analog_state_identities=54630400,resident_plif_membranes=30976000,
                inherited_spike_output_connections=25,fabric_to_ingress_event_routes=1475,
                shared_fabric_ingress_clock_reset_routes=2,
                source_state_geometry_preserved=True,full_architecture_layout_complete=False,
                actual_incremental_readback_pass=False,accumulation_5ms_accepted=False,
                stage='full_population_event_address_integration',
                remaining_required_boundaries=['Ingress destination address to native membrane access/injection',
                    'Externally driven analog contribution magnitude/sign and native phases',
                    'Global clock/reset/supply/reference distribution',
                    'Per-module loaded event accumulation and retention simulations'],
                excluded_completion_gates=['Trained-weight transfer','Output completion within 5ms','Hardware mIoU'],
                scope='Full physical state architecture with real routed fabric/ingress macro pair and retained25spike connections. A spacious research atlas, not a compact die. Native membrane injection addressing and global infrastructure remain incomplete; no autonomous inference or5ms claim.',
                elapsed_seconds=time.monotonic()-started,
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),pair_meta,pair_proof,pair_plan_path,pair_gds,old_meta,old_proof,analog_meta,analog_gds,OUT/'route_plan.json',gds]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['gds','gds_bytes','inherited_spike_output_connections','fabric_to_ingress_event_routes','elapsed_seconds']}),flush=True)


if __name__=='__main__': main()
