"""Independently read back class interfaces and all preserved reachable geometry."""
from pathlib import Path
import json,time
from assemble_gf180_external_bank_service_full25_v5 import elements
from gf180_fast_cells_v1 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import records,string
from assemble_gf180_full25_physical_candidate_v5 import rect,label
from assemble_gf180_full25_shared_page1024_v7 import labels
from prove_gf180_shared_page_parent_metal_v5 import Paint
from gf180_native_m5_corridor_v1 import Corridors
from gf180_v26_parent_index_v1 import build_index
from route_gf180_native_addresses_v23 import conflicts
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'assembly/full25_class_interfaces_v28'

def body(blob):return [b''.join(b for t,d,v,b in e) for e in elements(blob)]
def main():
    started=time.monotonic();dest=OUT/'independent_readback_v1.json';assert not dest.exists()
    mf=OUT/'physical_assembly.json';m=json.loads(mf.read_text())
    for p,d in m['sha256'].items():assert sha(ROOT/p)==d,p
    omf=BASE/'assembly/full25_control_supplies_v27/physical_assembly.json';om=json.loads(omf.read_text());_,old=cells_read((ROOT/om['gds']).read_bytes());_,cells=cells_read((ROOT/m['gds']).read_bytes())
    pp=OUT/'escape_plan.json';plan=json.loads(pp.read_text());assert plan['all_class_terminals_exposed'];changes=m['cloned_cells'];source=plan['source_cell'];reach=set()
    def visit(n):
        if n in reach:return
        reach.add(n)
        for t,d,v,b in records(old[n]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(om['top_cell'])
    for n in reach:
        actual_name=changes.get(n,n)
        if actual_name==n:
            assert cells[n]==old[n],('unchanged source bytes differ',n)
            continue
        if n==source:
            before=body(old[n]);actual=body(cells[actual_name]);assert actual[:len(before)]==before
            intended=[]
            for e in plan['escapes']:intended += [rect(81,e['rectangle_local_dbu']),label(e['escape_label'],*e['escaped_local_dbu'])]
            assert actual[len(before):]==intended
        else:
            expected=b''.join(string(6,actual_name) if t==6 and actual_name!=n else string(18,changes.get(v.rstrip(b'\0').decode(),v.rstrip(b'\0').decode())) if t==18 else b for t,d,v,b in records(old[n]))
            assert cells[actual_name]==expected,('unintended geometry change',n)
    original=Corridors(old);actual=Corridors(cells);newcell=changes[source];pins=labels(cells[newcell]);prior,_,paths=build_index()
    controlplan=BASE/'assembly/full25_control_supplies_v27/route_plan.json'
    for n in json.loads(controlplan.read_text())['routes']:
        for l,b in n['shapes']:prior.add(l,b,n['net'])
    prior.rebuild()
    for e in plan['escapes']:
        b=e['rectangle_local_dbu'];guard=(b[0]-460,b[1]-460,b[2]+460,b[3]+460);paint=Paint()
        for q in original.m5(source,guard):paint.add(81,q)
        sr=paint.at(81,*e['source_local_dbu']);assert all(paint.root(i)==sr for i in paint.hits(81,guard))
        paint=Paint()
        for q in actual.m5(newcell,b):paint.add(81,q)
        assert paint.at(81,*e['source_local_dbu'])==paint.at(81,*e['escaped_local_dbu'])
        pin=pins[e['escape_label']];assert pin[0]==81 and list(pin[1:])==e['escaped_local_dbu']
        owner=e['escape_label'];assert not conflicts(prior,[(81,e['rectangle_top_dbu'])],owner)
        prior.add(81,e['rectangle_top_dbu'],owner)
    report=dict(readback_pass=True,class_terminals_verified=118,reachable_source_cells_preserved=len(reach),new_escape_opens=0,new_escape_foreign_native_contacts=0,prior_parent_conflicts=0,class_supply_reference_joined=False,full_architecture_layout_complete=False,accumulation_5ms_accepted=False,elapsed_seconds=time.monotonic()-started,scope='Actual GDS class-interface geometry, labels, native460nm M5 guard/continuity, old parent conflicts and exact source hierarchy preservation. No loaded class cycle/global RC or accuracy claim.',sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_fast_cells_v1.py',mf,pp,omf,ROOT/m['gds'],controlplan,*paths]})
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='sha256'}),flush=True)
if __name__=='__main__':main()
