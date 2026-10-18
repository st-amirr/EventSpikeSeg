"""Read back independent page references and verify bank identity/spacing."""
from pathlib import Path
import bisect,collections,hashlib,json,struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/parallel_storage_roots_v4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    report_path=OUT/'physical_partition.json';report=json.loads(report_path.read_text())
    for name,digest in report['sha256'].items():assert sha(ROOT/name)==digest,name
    map_path=OUT/'root_instance_map.json';mapping=json.loads(map_path.read_text())
    source_path=BASE/'assembly/full_population_page_forest_v2/physical_forest.json'
    source=json.loads(source_path.read_text());leaf=next(v for v in source['templates'].values() if v['kind']=='native1024page')
    original=BASE/'assembly/full_population_page_forest_v2/full_population_page_forest_v2.gds'
    gds=ROOT/report['gds'];_,cells=cells_read(gds.read_bytes());_,old=cells_read(original.read_bytes())
    assert all(cells[k]==v for k,v in old.items())
    actual=[]
    for element in elements(cells[report['top_cell']]):
        if element[0][0]!=10:continue
        child=next(v.rstrip(b'\0').decode() for t,d,v,b in element if t==18)
        xy=next(struct.unpack('>ii',v) for t,d,v,b in element if t==16)
        assert child==leaf['cell'];actual.append(xy)
    roots=mapping['roots'];assert actual==[tuple(r['origin_dbu']) for r in roots]
    bb=leaf['bbox_dbu'];pitch=max(bb[2]-bb[0],bb[3]-bb[1])+1
    grid=collections.defaultdict(list);overlaps=[]
    for i,(x,y) in enumerate(actual):
        b=(x+bb[0],y+bb[1],x+bb[2],y+bb[3])
        keys=[(gx,gy) for gx in range(b[0]//pitch,b[2]//pitch+1) for gy in range(b[1]//pitch,b[3]//pitch+1)]
        candidates={j for key in keys for j in grid[key]}
        for j in candidates:
            ox,oy=actual[j];c=(ox+bb[0],oy+bb[1],ox+bb[2],oy+bb[3])
            if min(b[2],c[2])>max(b[0],c[0]) and min(b[3],c[3])>max(b[1],c[1]):overlaps.append([i,j])
        for key in keys:grid[key].append(i)
    assert not overlaps,overlaps[:4]
    verified_banks=0;states=0
    for plane in mapping['planes']:
        selected=roots[plane['first_root_index']:plane['first_root_index']+plane['root_count']]
        assert [r['page_rank'] for r in selected]==list(range(len(selected)))
        channels,height,width=plane['shape_chw'];ny=(height+7)//8;nx=(width+7)//8
        holes=plane['excluded_linear_banks'];active_by_page=collections.Counter();rank=0
        for canonical in range(channels*ny*nx):
            if canonical in holes:continue
            assert rank==canonical-bisect.bisect_left(holes,canonical)
            page,within=divmod(rank,16);assert page<len(selected)
            assert selected[page]['forest_ranked_bank_first']+within==rank
            _,spatial=divmod(canonical,ny*nx);by,bx=divmod(spatial,nx)
            active_by_page[page]+=min(8,height-by*8)*min(8,width-bx*8)
            rank+=1
        assert rank<=len(selected)*16
        assert all(r['ranked_active_slots']==active_by_page[r['page_rank']] for r in selected)
        assert sum(active_by_page.values())==plane['active_state_identities']
        verified_banks+=rank;states+=sum(active_by_page.values())
    output=OUT/'independent_readback_v1.json';assert not output.exists()
    result=dict(readback_pass=True,independent_roots=len(actual),leaf_bbox_overlap_pairs=overlaps,
                all_native_library_cells_byte_identical=True,canonical_banks_verified=verified_banks,
                active_state_identities_verified=states,logical_bank_page_row_column_aliases=0,
                scope='Actual GDS page references, native cell bytes, separate page bounding boxes and every canonical bank-to-page mapping. No new metal was added. Global wiring, native parallel compute/injection, simultaneous loading and5ms remain incomplete.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),report_path,map_path,source_path,original,gds]})
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['sha256','scope']},indent=2))

if __name__=='__main__':main()
