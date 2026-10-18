"""Read back every new address escape and unchanged source hierarchy geometry."""
from pathlib import Path
import collections,json,time
from assemble_gf180_external_bank_service_full25_v5 import elements
from gf180_fast_cells_v1 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import records,string
from assemble_gf180_full25_shared_page1024_v7 import labels
from prove_gf180_shared_page_parent_metal_v5 import Paint
from gf180_native_m5_corridor_v1 import Corridors
from assemble_gf180_full25_physical_candidate_v5 import rect,label
from route_gf180_native_addresses_v23 import conflicts
from gf180_v30_parent_index_v1 import build_index
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_native_controls_v31'


def body(blob):return [b''.join(b for t,d,v,b in e) for e in elements(blob)]


def main():
    started=time.monotonic();dest=OUT/'independent_readback_v1.json';assert not dest.exists()
    meta=OUT/'physical_assembly.json';m=json.loads(meta.read_text())
    for p,digest in m['sha256'].items():assert sha(ROOT/p)==digest,p
    old_meta=BASE/'assembly/full25_class_infrastructure_v30/physical_assembly.json'
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
        if actual_name==name:
            assert cells[name]==old[name],('unchanged native source bytes differ',name)
            unchanged+=1
            continue
        if name in wrappers:
            original=body(old[name]);actual=body(cells[actual_name])
            assert actual[:len(original)]==original,('source elements changed',name)
            added=actual[len(original):]
            expected_count=wrappers[name]['escaped_port_count']*2
            assert len(added)==expected_count,(name,len(added),expected_count)
            intended=[]
            for e in plan['escapes']:
                if e['actor_index']==wrappers[name]['actor_index']:
                    intended += [rect(81,e['rectangle_local_dbu']),label(e['escape_label'],*e['escaped_local_dbu'])]
            assert added==intended,('actual added geometry mismatch',name)
            cloned+=1
        else:
            expected=b''.join(string(6,actual_name) if t==6 and actual_name!=name else
                              string(18,changes.get(v.rstrip(b'\0').decode(),v.rstrip(b'\0').decode())) if t==18 else b
                              for t,d,v,b in records(old[name]))
            assert cells[actual_name]==expected,('unintended geometry/reference edit',name)
            if actual_name==name:unchanged+=1
            else:cloned+=1
    original_corr=Corridors(old);corr=Corridors(cells);verified=[]
    for escape in plan['escapes']:
        a=m['actors'][escape['actor_index']];cell=a['breakout_cell']
        pin=labels(cells[cell])[escape['escape_label']]
        assert pin[0]==81 and list(pin[1:])==escape['escaped_local_dbu']
        box=escape['rectangle_local_dbu'];guard=(box[0]-460,box[1]-460,box[2]+460,box[3]+460);baseline=Paint()
        for b in original_corr.m5(a['original_enclosing_cell'],guard):baseline.add(81,b)
        root=baseline.at(81,*escape['source_local_dbu'])
        assert all(baseline.root(i)==root for i in baseline.hits(81,guard))
        paint=Paint()
        for b in corr.m5(cell,box):paint.add(81,b)
        sr=paint.at(81,*escape['source_local_dbu']);tr=paint.at(81,*escape['escaped_local_dbu'])
        assert sr==tr,('new escape open',escape['actor_index'],escape['native_pin'])
        assert {paint.root(i) for i in paint.hits(81,box)}=={sr},('new escape alias',escape['native_pin'])
        verified.append((escape['actor_index'],escape['endpoint_kind'],escape['native_pin']))
    assert len(set(verified))==len(plan['escapes'])
    prior,inputs,prior_paths=build_index()
    for e in plan['escapes']:
        ox,oy=m['actors'][e['actor_index']]['origin_top_dbu'];b=e['rectangle_local_dbu']
        box=(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy);owner=f"external_{e['actor_index']}_{e['endpoint_kind']}_{e['native_pin']}"
        assert not conflicts(prior,[(81,box)],owner),owner
        prior.add(81,box,owner)
    report=dict(readback_pass=True,actual_native_control_escapes_verified=len(verified),
                physical_actors=25,unchanged_reachable_source_cells=unchanged,
                cloned_wrappers_and_ancestors_verified=cloned,
                native_state_geometry_preserved=True,existing_spike_and_ingress_routes_preserved=True,
                new_escape_opens=0,new_escape_same_layer_aliases=0,
                destination_controller_address_binding_preserved=True,full_architecture_layout_complete=False,
                accumulation_5ms_accepted=False,elapsed_seconds=time.monotonic()-started,
                scope='Actual GDS source-element preservation and conservative full enclosing native-hierarchy M5 corridor connectivity for every added native request/clock/reset/completion escape. Builder additionally screens460nm native/new-escape clearance. No full-style DRC, global native extraction/RC, global supply distribution or analog timing claim.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_native_m5_corridor_v1.py',ROOT/'scripts/gf180_fast_cells_v1.py',ROOT/'scripts/gf180_v30_parent_index_v1.py',meta,plan_path,old_meta,gds,*prior_paths]})
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['scope','sha256']}),flush=True)


if __name__=='__main__':main()
