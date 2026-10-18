"""Expose native destination-address pins beyond all25 enclosing wrappers.

Every new straight M5 escape must contact only its original same-layer
component, checked through the complete native enclosing hierarchy corridor.
"""
from pathlib import Path
import json,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,string,records
from assemble_gf180_full25_physical_candidate_v5 import rect,label
from prove_gf180_shared_page_parent_metal_v5 import Paint
from gf180_native_m5_corridor_v1 import Corridors,overlap
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_membrane_address_breakouts_v18'


def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    v17=BASE/'assembly/full25_accumulation_architecture_v17'
    meta=v17/'physical_assembly.json';m=json.loads(meta.read_text());gds=ROOT/m['gds']
    proof=v17/'independent_readback_v1.json';assert json.loads(proof.read_text())['readback_pass']
    assert sha(gds)==m['sha256'][m['gds']]
    boundary_path=BASE/'assembly/full25_layout_integration_v14/actor_boundary_ports_v1.json'
    boundaries=json.loads(boundary_path.read_text())
    v15_path=BASE/'assembly/full25_spike_breakouts_v15/physical_assembly.json';v15=json.loads(v15_path.read_text())
    prefix,cells=cells_read(gds.read_bytes());corr=Corridors(cells)
    escapes=[];failures=[];replacements={};actors=[]
    for a in boundaries['actors']:
        ai=a['actor_index'];native=a['native_actor'];forest=a['membrane_service']
        outer_original=native['path'][0]['child'];outer=v15['cloned_cells'].get(outer_original,outer_original)
        ox,oy=native['path'][0]['origin_dbu'];bb=v15['actors'][ai]['enclosing_top_bbox_dbu']
        pins=[]
        for pin in sorted(forest['ports']):
            if pin.startswith('FOREST__ADDR'):
                k=int(pin.removeprefix('FOREST__ADDR'));pins.append(('forest_address_o',k,'forest',pin,forest['ports'][pin]))
            elif pin.startswith('FOREST__SEL'):
                k=int(pin.removeprefix('FOREST__SEL'));pins.append(('column_select_o',k,'forest',pin,forest['ports'][pin]))
        for k in range(3):
            for part in ['compute','bank_service']:
                pin=f'{part}__A{k}';pins.append(('local_row_o',k,'actor',pin,native['ports'][pin]))
        for k in range(7):
            pin=f'PAGE1024__LOW{k}' if k<4 else f'PAGE1024__HIGH{k-4}'
            pins.append(('local_page_address_o',k,'actor',pin,native['ports'][pin]))
        pin='bank_service__BANK_SELECT';pins.append(('local_bank_select_o',0,'actor',pin,native['ports'][pin]))
        for k in range(8):
            for part in ['compute','bank_service','PAGE1024']:
                pin=f'{part}__SEL{k}';pins.append(('column_select_o',k,'actor',pin,native['ports'][pin]))
        additions=[];accepted_shapes=[];actor_escapes=[]
        for index,(port,bit,kind,pin,entries) in enumerate(pins):
            assert len(entries)==1 and entries[0]['layer']==81,(ai,pin,entries)
            sx,sy=entries[0]['xy_top_dbu'];x,y=sx-ox,sy-oy
            ex=bb[0]-20000-index*2000-ox
            box=(min(x,ex)-220,y-220,max(x,ex)+220,y+220)
            guarded=(box[0]-460,box[1]-460,box[2]+460,box[3]+460)
            paint=Paint()
            for b in corr.m5(outer,guarded):paint.add(81,b)
            source=paint.at(81,x,y)
            foreign=[paint.shapes[i][1] for i in paint.hits(81,guarded) if paint.root(i)!=source]
            conflicts=[oldpin for oldpin,oldbox in accepted_shapes if overlap(guarded,oldbox)]
            # Even same eventual logical-net endpoints remain separate until
            # explicit controller fanout routing joins them; do not hide aliases.
            if foreign or conflicts:
                failures.append(dict(actor_index=ai,pin=pin,foreign_m5=foreign[:8],new_escape_contacts=conflicts));break
            name='ACC_DEST__'+pin;additions.extend([rect(81,box),label(name,ex,y)])
            accepted_shapes.append((pin,box))
            entry=dict(actor_index=ai,actor=a['actor'],dispatcher_port=port,dispatcher_bit=bit,
                       endpoint_kind=kind,native_pin=pin,enclosing_cell=outer,
                       source_local_dbu=[x,y],source_top_dbu=[sx,sy],
                       escape_label=name,escaped_local_dbu=[ex,y],escaped_top_dbu=[ex+ox,y+oy],
                       rectangle_local_dbu=box,source_m5_component_only=True,
                       native_spacing_guard_nm=460)
            escapes.append(entry);actor_escapes.append(entry)
        if failures:break
        new=f'ESS_ACCUMULATION_ADDRESS_{ai:02d}_V18'
        body=b''.join(b for e in elements(cells[outer]) for t,d,v,b in e)
        cells[new]=begin(new)+body+b''.join(additions)+rec(7,0);replacements[outer]=new
        actors.append(dict(actor_index=ai,actor=a['actor'],original_enclosing_cell=outer,
                           breakout_cell=new,origin_top_dbu=[ox,oy],escaped_port_count=len(actor_escapes)))
    plan=dict(escapes=escapes,actors=actors,failures=failures,all_address_escapes_accepted=not failures,
              scope='M5-only conservative hierarchical corridor proof with460nm guard. No full lower-layer/native transistor/RC qualification; controller joins and actual GDS readback remain required.')
    (OUT/'escape_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    assert not failures,failures[:2]
    def clone(name):
        if name in replacements:return replacements[name]
        children={v.rstrip(b'\0').decode() for t,d,v,b in records(cells[name]) if t==18}
        changes={child:clone(child) for child in children}
        if all(k==v for k,v in changes.items()):return name
        new='ESS140K_MEMBRANE_ADDRESS_BREAKOUTS_V18' if name==m['top_cell'] else name+'_ADDR18'
        assert new not in cells and len(new)<=64
        cells[new]=b''.join(string(6,new) if t==6 else string(18,changes[v.rstrip(b'\0').decode()]) if t==18 else b for t,d,v,b in records(cells[name]))
        replacements[name]=new;return new
    top=clone(m['top_cell']);needed=set()
    def visit(name):
        if name in needed:return
        needed.add(name)
        for t,d,v,b in records(cells[name]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(top)
    dest=OUT/'eventspikeseg140k_membrane_address_breakouts_v18.gds'
    with dest.open('wb') as stream:
        stream.write(prefix)
        for name in sorted(needed):stream.write(cells[name])
        stream.write(rec(4,0))
    report=dict(top_cell=top,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,
                escaped_destination_terminals=len(escapes),actors=actors,cloned_cells=replacements,
                native_state_geometry_preserved=True,existing_25_spike_and1477_event_routes_preserved=True,
                actual_new_gds_readback_pass=False,destination_controller_bound=False,
                full_architecture_layout_complete=False,accumulation_5ms_accepted=False,
                elapsed_seconds=time.monotonic()-started,
                scope=plan['scope'],
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_native_m5_corridor_v1.py',meta,proof,gds,boundary_path,v15_path,OUT/'escape_plan.json',dest]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['gds','gds_bytes','escaped_destination_terminals','elapsed_seconds']}),flush=True)


if __name__=='__main__':main()
