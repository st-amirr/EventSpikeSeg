"""Read back every new address escape and unchanged source hierarchy geometry."""
from pathlib import Path
import collections,json,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import records,string
from assemble_gf180_full25_shared_page1024_v7 import labels
from prove_gf180_shared_page_parent_metal_v5 import Paint
from gf180_native_m5_corridor_v1 import Corridors
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_membrane_address_breakouts_v18'


def body(blob):return [b''.join(b for t,d,v,b in e) for e in elements(blob)]


def main():
    started=time.monotonic();dest=OUT/'independent_readback_v1.json';assert not dest.exists()
    meta=OUT/'physical_assembly.json';m=json.loads(meta.read_text())
    for p,digest in m['sha256'].items():assert sha(ROOT/p)==digest,p
    old_meta=BASE/'assembly/full25_accumulation_architecture_v17/physical_assembly.json'
    oldm=json.loads(old_meta.read_text());_,old=cells_read((ROOT/oldm['gds']).read_bytes())
    gds=ROOT/m['gds'];_,cells=cells_read(gds.read_bytes())
    plan_path=OUT/'escape_plan.json';plan=json.loads(plan_path.read_text());changes=m['cloned_cells']
    wrappers={a['original_enclosing_cell']:a for a in m['actors']}
    reachable=set()
    def visit(n):
        if n in reachable:return
        reachable.add(n)
        for t,d,v,b in records(old[n]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(oldm['top_cell'])
    unchanged=0;cloned=0
    for name in reachable:
        actual_name=changes.get(name,name)
        assert actual_name in cells,name
        if name in wrappers:
            original=body(old[name]);actual=body(cells[actual_name])
            assert actual[:len(original)]==original,('source elements changed',name)
            added=actual[len(original):]
            expected_count=wrappers[name]['escaped_port_count']*2
            assert len(added)==expected_count,(name,len(added),expected_count)
            cloned+=1
        else:
            expected=b''.join(string(6,actual_name) if t==6 and actual_name!=name else
                              string(18,changes.get(v.rstrip(b'\0').decode(),v.rstrip(b'\0').decode())) if t==18 else b
                              for t,d,v,b in records(old[name]))
            assert cells[actual_name]==expected,('unintended geometry/reference edit',name)
            if actual_name==name:unchanged+=1
            else:cloned+=1
    del old
    corr=Corridors(cells);verified=[]
    for escape in plan['escapes']:
        a=m['actors'][escape['actor_index']];cell=a['breakout_cell']
        pin=labels(cells[cell])[escape['escape_label']]
        assert pin[0]==81 and list(pin[1:])==escape['escaped_local_dbu']
        box=escape['rectangle_local_dbu'];paint=Paint()
        for b in corr.m5(cell,box):paint.add(81,b)
        sr=paint.at(81,*escape['source_local_dbu']);tr=paint.at(81,*escape['escaped_local_dbu'])
        assert sr==tr,('new escape open',escape['actor_index'],escape['native_pin'])
        assert {paint.root(i) for i in paint.hits(81,box)}=={sr},('new escape alias',escape['native_pin'])
        verified.append((escape['actor_index'],escape['native_pin']))
    assert len(set(verified))==len(plan['escapes'])
    report=dict(readback_pass=True,actual_destination_escapes_verified=len(verified),
                physical_actors=25,unchanged_reachable_source_cells=unchanged,
                cloned_wrappers_and_ancestors_verified=cloned,
                native_state_geometry_preserved=True,existing_spike_and_ingress_routes_preserved=True,
                new_escape_opens=0,new_escape_same_layer_aliases=0,
                destination_controller_bound=False,full_architecture_layout_complete=False,
                accumulation_5ms_accepted=False,elapsed_seconds=time.monotonic()-started,
                scope='Actual GDS source-element preservation and conservative full enclosing native-hierarchy M5 corridor connectivity for every added address/select escape. Builder additionally screens460nm native/new-escape clearance. No full-style DRC, global native extraction/RC, controller binding or analog timing claim.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_native_m5_corridor_v1.py',meta,plan_path,old_meta,gds]})
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['scope','sha256']}),flush=True)


if __name__=='__main__':main()
