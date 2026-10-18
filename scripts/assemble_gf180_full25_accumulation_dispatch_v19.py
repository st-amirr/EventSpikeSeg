"""Integrate the routed dispatcher link into the address-exposed full layout."""
from pathlib import Path
import json,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import rec,string,records
from prove_gf180_shared_page_parent_metal_v5 import VIA
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_accumulation_dispatch_v19'


def main():
    started=time.monotonic()
    nd=BASE/'assembly/full25_membrane_address_breakouts_v18'
    nm_path=nd/'physical_assembly.json';nm=json.loads(nm_path.read_text());ngds=ROOT/nm['gds']
    np=nd/'independent_readback_v1.json';assert json.loads(np.read_text())['readback_pass']
    ld=BASE/'assembly/accumulation_dispatch_link_v2'
    lm_path=ld/'physical_assembly.json';lm=json.loads(lm_path.read_text());lgds=ROOT/lm['gds']
    lp=ld/'independent_readback_v1.json';assert json.loads(lp.read_text())['readback_pass']
    for data,path in [(nm,ngds),(lm,lgds)]:assert sha(path)==data['sha256'][path.relative_to(ROOT).as_posix()]
    assert not OUT.exists();OUT.mkdir(parents=True)
    source_routes=BASE/'assembly/full25_accumulation_architecture_v17/route_plan.json'
    spikes=json.loads(source_routes.read_text());lplan_path=ld/'route_plan.json';lplan=json.loads(lplan_path.read_text())
    ox,oy=spikes['pair_origin_dbu'];conflicts=[]
    for route in spikes['routes']:
        for l,b in route['shapes']:
            for net in lplan['routes']:
                for other,c in net['shapes']:
                    if not(l==other or other in VIA.get(l,()) or l in VIA.get(other,())):continue
                    q=(c[0]+ox,c[1]+oy,c[2]+ox,c[3]+oy)
                    guard=460 if l==other==81 else 280 if l==other and l in [34,36,42,46] else 260 if l==other else 0
                    if not(b[2]+guard<q[0] or b[0]-guard>q[2] or b[3]+guard<q[1] or b[1]-guard>q[3]):
                        conflicts.append((route['net'],net['net'],l,b,other,q))
    (OUT/'cross_contact_check.json').write_text(json.dumps(dict(spike_to_dispatch_route_conflicts=conflicts),indent=2)+'\n')
    assert not conflicts,conflicts[:2]
    prefix,cells=cells_read(ngds.read_bytes());_,lc=cells_read(lgds.read_bytes())
    shared=0
    for name,blob in lc.items():
        if name in cells:assert cells[name]==blob,('source library name collision',name);shared+=1
        else:cells[name]=blob
    old_pair='GF180_ACCUMULATION_FABRIC_INGRESS_V1'
    top='ESS140K_ACCUMULATION_DISPATCH_V19';changed=0;body=[]
    for t,d,v,b in records(cells[nm['top_cell']]):
        if t==6:body.append(string(6,top))
        elif t==18 and v.rstrip(b'\0').decode()==old_pair:
            changed+=1;body.append(string(18,lm['top_cell']))
        else:body.append(b)
    assert changed==1
    cells[top]=b''.join(body)
    needed=set()
    def visit(name):
        if name in needed:return
        needed.add(name)
        for t,d,v,b in records(cells[name]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(top)
    dest=OUT/'eventspikeseg140k_accumulation_dispatch_v19.gds'
    with dest.open('wb') as f:
        f.write(prefix)
        for name in sorted(needed):f.write(cells[name])
        f.write(rec(4,0))
    report=dict(top_cell=top,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,
                native_state_identities_preserved=54630400,resident_plif_membranes=30976000,
                physical_actors=25,native_address_select_escapes=1622,
                spike_to_fabric_routes=25,fabric_to_ingress_routes=1475,ingress_to_dispatch_routes=1575,
                shared_three_control_macro_clock_reset_networks=2,
                unchanged_shared_source_cells=shared,native_state_geometry_preserved=True,
                dispatcher_native_output_nets_still_to_route=947,
                dispatcher_to_native_membranes_connected=False,
                full_architecture_layout_complete=False,accumulation_5ms_accepted=False,
                actual_gds_integration_readback_pass=False,elapsed_seconds=time.monotonic()-started,
                scope='Full population architecture now includes three physically connected categorical macros and readback-qualified native address/select escapes. Existing state geometry and25spike routes retained. The947dispatcher-to-native fanout nets, analog phase/external contribution interface and global infrastructure still need final integration. No loaded analog or5ms claim; no compact die claim.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),nm_path,np,ngds,lm_path,lp,lgds,source_routes,lplan_path,OUT/'cross_contact_check.json',dest]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['gds','gds_bytes','ingress_to_dispatch_routes','native_address_select_escapes','elapsed_seconds']}),flush=True)


if __name__=='__main__':main()
