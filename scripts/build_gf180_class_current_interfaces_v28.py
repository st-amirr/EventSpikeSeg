"""Expose the existing full class-current/readout wrapper without altering devices."""
from pathlib import Path
import json,time
from assemble_gf180_external_bank_service_full25_v5 import elements
from gf180_fast_cells_v1 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,string,records
from assemble_gf180_full25_physical_candidate_v5 import rect,label
from gf180_native_m5_corridor_v1 import Corridors
from prove_gf180_shared_page_parent_metal_v5 import Paint
from gf180_v26_parent_index_v1 import build_index
from route_gf180_native_addresses_v23 import conflicts
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'assembly/full25_class_interfaces_v28'

def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    sd=BASE/'assembly/full25_control_supplies_v27';mf=sd/'physical_assembly.json';m=json.loads(mf.read_text())
    proof=sd/'parent_graph_readback_v1.json';assert json.loads(proof.read_text())['parent_graph_readback_pass']
    gds=ROOT/m['gds'];assert sha(gds)==m['sha256'][m['gds']]
    oldmf=BASE/'assembly/full25_class_current_service_v13/physical_assembly.json';old=json.loads(oldmf.read_text());wrapper=old['class_current_service_wrapper'];cell=wrapper['cell'];placement=next(p for p in old['top_placements'] if p['cell']==cell);ox,oy=placement['origin_dbu'];bb=placement['bbox_dbu']
    prefix,cells=cells_read(gds.read_bytes());corr=Corridors(cells);index,inp,paths=build_index()
    for n in json.loads((sd/'route_plan.json').read_text())['routes']:
        for l,b in n['shapes']:index.add(l,b,n['net'])
    index.rebuild();escapes=[];failures=[];added=[]
    for i,(name,p) in enumerate(wrapper['ports'].items()):
        assert p['layer']==81;x,y=p['xy_dbu'];ex=bb[0]-250000-i*2000-ox;box=(min(x,ex)-220,y-220,max(x,ex)+220,y+220);guard=(box[0]-460,box[1]-460,box[2]+460,box[3]+460)
        paint=Paint()
        for b in corr.m5(cell,guard):paint.add(81,b)
        root=paint.at(81,x,y);foreign=[paint.shapes[j][1] for j in paint.hits(81,guard) if paint.root(j)!=root]
        topbox=(box[0]+ox,box[1]+oy,box[2]+ox,box[3]+oy);owner='CLASS__'+name;bad=conflicts(index,[(81,topbox)],owner)
        if foreign or bad:failures.append(dict(pin=name,native_foreign_m5=foreign[:5],prior_route_contacts=bad));break
        added += [rect(81,box),label(owner,ex,y)];index.add(81,topbox,owner)
        escapes.append(dict(native_pin=name,escape_label=owner,layer=81,source_local_dbu=[x,y],escaped_local_dbu=[ex,y],source_top_dbu=[x+ox,y+oy],escaped_top_dbu=[ex+ox,y+oy],rectangle_local_dbu=box,rectangle_top_dbu=topbox))
    plan=dict(escapes=escapes,failures=failures,all_class_terminals_exposed=len(escapes)==118,source_cell=cell,origin_top_dbu=[ox,oy],scope='Physical M5 access escapes for118 existing class-current/readout terminals. Class input/address/phase interfaces remain external under article scope. Supply/reference joins and actual readback required.')
    (OUT/'escape_plan.json').write_text(json.dumps(plan,indent=2)+'\n');assert not failures,failures[:1]
    replacements={cell:'ESS_CLASS_INTERFACE_V28'}
    body=b''.join(b for e in elements(cells[cell]) for t,d,v,b in e);cells[replacements[cell]]=begin(replacements[cell])+body+b''.join(added)+rec(7,0)
    def clone(name):
        if name in replacements:return replacements[name]
        children={v.rstrip(b'\0').decode() for t,d,v,b in records(cells[name]) if t==18};changes={n:clone(n) for n in children}
        if all(k==v for k,v in changes.items()):return name
        new='ESS140K_CLASS_INTERFACES_V28' if name==m['top_cell'] else name+'_CI28';assert len(new)<=64 and new not in cells
        cells[new]=b''.join(string(6,new) if t==6 else string(18,changes[v.rstrip(b'\0').decode()]) if t==18 else b for t,d,v,b in records(cells[name]));replacements[name]=new;return new
    top=clone(m['top_cell']);needed=set()
    def visit(n):
        if n in needed:return
        needed.add(n)
        for t,d,v,b in records(cells[n]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(top);dest=OUT/'eventspikeseg140k_class_interfaces_v28.gds'
    with dest.open('wb') as stream:
        stream.write(prefix)
        for n in sorted(needed):stream.write(cells[n])
        stream.write(rec(4,0))
    report=dict(top_cell=top,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,escaped_class_terminals=118,cloned_cells=replacements,actual_gds_readback_pass=False,full_architecture_layout_complete=False,accumulation_5ms_accepted=False,elapsed_seconds=time.monotonic()-started,sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_fast_cells_v1.py',mf,proof,oldmf,gds,*paths,OUT/'escape_plan.json',dest]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n');print('Class current boundary GDS emitted',flush=True)
if __name__=='__main__':main()
