"""Expose the existing page access circuits as independent physical roots.

This candidate replaces the shared forest ancestor references with references
to the very same native1024 pages at their original coordinates. It preserves
state geometry and page ordering; compute, dispatch and global wiring remain.
"""
from pathlib import Path
import bisect,hashlib,json,struct
from assemble_gf180_one_neuron_page_link_v1 import gds_library_parts
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from assemble_gf180_full25_physical_candidate_v5 import label
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/parallel_storage_roots_v4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not OUT.exists();OUT.mkdir()
    source=BASE/'assembly/full_population_page_forest_v2'
    meta=source/'physical_forest.json';m=json.loads(meta.read_text())
    original=source/'full_population_page_forest_v2.gds'
    assert m['sha256'][original.relative_to(ROOT).as_posix()]==sha(original)
    templates=m['templates'];leaves=[t for t in templates.values() if t['kind']=='native1024page']
    assert len(leaves)==1;leaf=leaves[0]
    mapping_path=BASE/'assembly/full_population_page_access_v1/address_assembly_specification_v1.json'
    mapping=json.loads(mapping_path.read_text());planes_by_id={p['plane_index']:p for p in mapping['planes']}
    roots=[];parts=[];planes=[]
    def walk(cell,origin,path):
        t=templates[cell]
        if t['kind']=='native1024page':
            yield origin,path
            return
        children=[v for v in t['modules'] if v['kind'] in ['native1024page','page_tree']]
        assert len(children)==t['populated_children']
        for i,child in enumerate(children):
            assert child['instance']==f'C{i}'
            xy=child['origin_dbu']
            yield from walk(child['cell'],(origin[0]+xy[0],origin[1]+xy[1]),path+'/'+child['instance'])
    for plane in m['planes']:
        plane_map=planes_by_id[plane['plane_index']]
        assert plane_map['actor']==plane['actor'] and plane_map['state_kind']==plane['state_kind']
        placements=list(walk(plane['root_cell'],tuple(plane['origin_dbu']),plane['root_cell']))
        assert len(placements)==plane['leaf_pages']
        first=len(roots)
        for rank,(xy,path) in enumerate(placements):
            identity=f"P{plane['plane_index']:02d}_PAGE{rank:05d}"
            # Forest addressing is sequential groups of16banks,8rows,8columns.
            channels,height,width=plane_map['shape_chw']
            ny,nx=plane_map['bank_grid_yx'];holes=plane_map['excluded_linear_banks']
            bank_count=channels*ny*nx-len(holes)
            active=0
            for bank_rank in range(rank*16,min(rank*16+16,bank_count)):
                canonical=bank_rank
                while True:
                    adjusted=bank_rank+bisect.bisect_right(holes,canonical)
                    if adjusted==canonical:break
                    canonical=adjusted
                assert canonical not in holes
                channel,spatial=divmod(canonical,ny*nx);by,bx=divmod(spatial,nx)
                assert channel<channels
                active+=min(8,height-by*8)*min(8,width-bx*8)
            root=dict(root_index=len(roots),root_id=identity,plane_index=plane['plane_index'],
                      page_rank=rank,forest_ranked_bank_first=rank*16,
                      row_address_bits=7,origin_dbu=xy,source_hierarchy_path=path,
                      ranked_active_slots=active)
            roots.append(root);parts.append(reference(leaf['cell'],*xy))
            anchor=leaf['ports']['RECOV']['xy_dbu']
            parts.append(label(identity,xy[0]+anchor[0],xy[1]+anchor[1]))
        planes.append(dict(plane_index=plane['plane_index'],actor=plane['actor'],state_kind=plane['state_kind'],
                           first_root_index=first,root_count=len(placements),active_state_identities=plane['active_states'],
                           shape_chw=plane_map['shape_chw'],excluded_linear_banks=plane_map['excluded_linear_banks'],
                           identity_mapping='canonical bank minus preceding excluded banks -> page=floor(rank/16); page address=(rank%16)*8+row; column selector=x%8. Edge padding is inactive.'))
    assert len(roots)==m['native1024_leaf_page_instances']==54105
    head,library,_=gds_library_parts(original)
    top='GF180_PARALLEL_STORAGE_ROOTS_V4'
    top_blob=begin(top)+b''.join(parts)+rec(7,0)
    gds=OUT/'parallel_storage_roots_v4.gds';gds.write_bytes(head+library+top_blob+rec(4,0))
    _,old_cells=cells_read(original.read_bytes());_,new_cells=cells_read(gds.read_bytes())
    assert all(new_cells[n]==blob for n,blob in old_cells.items())
    actual=[]
    for e in elements(new_cells[top]):
        if e[0][0]!=10:continue
        cell=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18)
        xy=next(struct.unpack('>ii',v) for t,d,v,b in e if t==16)
        assert cell==leaf['cell'];actual.append(xy)
    assert actual==[tuple(r['origin_dbu']) for r in roots]
    assert len(set(actual))==len(actual)
    for plane in planes:
        assert sum(r['ranked_active_slots'] for r in roots if r['plane_index']==plane['plane_index'])==plane['active_state_identities']
    (OUT/'root_instance_map.json').write_text(json.dumps(dict(planes=planes,roots=roots),separators=(',',':'))+'\n')
    report=dict(top_cell=top,gds=gds.relative_to(ROOT).as_posix(),gds_bytes=gds.stat().st_size,
                physical_independent_page_roots_built=len(roots),state_identities=sum(p['active_state_identities'] for p in planes),
                prior_local_state_identities_retained_in_actor_modules=m['remaining_active_states_preserved_in_V8_actors'],
                original_leaf_cells_byte_identical=True,all_original_page_origins_and_order_read_back=True,
                all_valid_state_counts_checked_against_edge_padding_and_local_exclusions=True,
                root_data_recov_write_read_address_buses_independent=True,
                native_page_ports=leaf['ports'],root_instance_map='root_instance_map.json',
                scope='Standalone physical parallel-storage candidate. Removes shared ancestor selectors from active hierarchy, exposes each existing native1024 page independently, preserves actual leaf storage/access geometry and placement. Original ancestor cells remain unreferenced library definitions. No new compute/service, global power/address wiring, timing/DRC closure or replacement of V16 full assembly is claimed. Parallel reads are physically possible through independent root ports; loaded simultaneous operation remains untested. No5ms acceptance. Peripheral forest page slots retain frozen logical map; padding is inactive.',
                supersedes='parallel_storage_roots_v3: page active-count metadata treated edge padding as contiguous; GDS page geometry unchanged. V4 counts every valid canonical bank/row/column and excluded local bank.',
                full_chip_layout_complete=False,full_5ms_population_service_accepted=False,
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),meta,original,mapping_path,gds,OUT/'root_instance_map.json']})
    assert report['state_identities']==54600000
    (OUT/'physical_partition.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['gds','gds_bytes','physical_independent_page_roots_built','state_identities','original_leaf_cells_byte_identical','all_original_page_origins_and_order_read_back']},indent=2))

if __name__=='__main__':main()
