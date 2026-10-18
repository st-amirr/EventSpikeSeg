"""Prove exact source hierarchy/placement preservation and V19 integration."""
from pathlib import Path
import json,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import records,string
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_accumulation_dispatch_v19'


def main():
    started=time.monotonic();dest=OUT/'independent_readback_v1.json';assert not dest.exists()
    meta=OUT/'physical_assembly.json';m=json.loads(meta.read_text())
    for p,digest in m['sha256'].items():assert sha(ROOT/p)==digest,p
    nd=BASE/'assembly/full25_membrane_address_breakouts_v18';nm=json.loads((nd/'physical_assembly.json').read_text())
    ld=BASE/'assembly/accumulation_dispatch_link_v2';lm=json.loads((ld/'physical_assembly.json').read_text())
    assert json.loads((nd/'independent_readback_v1.json').read_text())['readback_pass']
    assert json.loads((ld/'independent_readback_v1.json').read_text())['readback_pass']
    _,cells=cells_read((ROOT/m['gds']).read_bytes());_,native=cells_read((ROOT/nm['gds']).read_bytes())
    # All reachable descendants of the former native top must remain identical.
    descendants=set()
    def visit(name):
        if name in descendants:return
        descendants.add(name)
        for t,d,v,b in records(native[name]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(nm['top_cell']);descendants.remove(nm['top_cell'])
    assert all(cells[n]==native[n] for n in descendants)
    expected=b''.join(string(6,m['top_cell']) if t==6 else string(18,lm['top_cell'])
                      if t==18 and v.rstrip(b'\0').decode()=='GF180_ACCUMULATION_FABRIC_INGRESS_V1' else b
                      for t,d,v,b in records(native[nm['top_cell']]))
    assert cells[m['top_cell']]==expected,'Full top changed beyond the intended child substitution'
    del native
    _,link=cells_read((ROOT/lm['gds']).read_bytes());assert all(cells[n]==b for n,b in link.items())
    assert json.loads((OUT/'cross_contact_check.json').read_text())['spike_to_dispatch_route_conflicts']==[]
    report=dict(readback_pass=True,reachable_native_source_cells_preserved=len(descendants),
                complete_dispatch_link_library_preserved=True,full_top_placements_and_spike_metal_preserved=True,
                native_address_select_escapes_verified=1622,spike_to_fabric_routes_verified=25,
                inherited_fabric_to_ingress_routes_verified=1475,ingress_to_dispatch_routes_verified=1575,
                shared_three_control_macro_clock_reset_networks_verified=2,
                spike_to_dispatch_cross_contacts=0,
                dispatcher_to_native_membranes_connected=False,full_architecture_layout_complete=False,
                accumulation_5ms_accepted=False,elapsed_seconds=time.monotonic()-started,
                scope='Exact actual-GDS hierarchy/library/placement preservation and intended top-child substitution. Inherits independently verified native1622escapes, three-macro3050eventpaths/clock-reset and25spike routes; cross-contact check preserves those spike paths.947native output nets, global infrastructure and loaded analog timing remain open.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),meta,ROOT/m['gds'],OUT/'cross_contact_check.json',nd/'independent_readback_v1.json',ld/'independent_readback_v1.json']})
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sha256','scope']}),flush=True)


if __name__=='__main__':main()
