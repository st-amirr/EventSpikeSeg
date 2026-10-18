"""Reuse the connected V8 page/compute path as two independent analog services.

Remove the two existing categorical controller drivers so later service control
can drive the shared phase ports without conflicting outputs. Preserve every
analog child transform and all parent route bytes. This is a two-lane physical
building block, not a selected full-population lane count or timing claim.
"""
from pathlib import Path
import hashlib,json
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference,records
from assemble_gf180_full25_shared_page1024_v7 import labels

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/parallel_page_service_pair_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not OUT.exists();OUT.mkdir()
    source=BASE/'assembly/full25_shared_page1024_v8'
    mp=source/'physical_assembly.json';m=json.loads(mp.read_text());actor=m['actor_regions'][0]
    g=source/'eventspikeseg140k_shared_page1024_v7.gds'
    assert m['sha256'][g.relative_to(ROOT).as_posix()]==sha(g)
    proof_path=source/'actor_00_complete_boundary_metal_proof_v5.json'
    proof=json.loads(proof_path.read_text());assert proof['incremental_metal_connectivity_accepted']
    composition_path=source/'actor_compositional_wiring_qualification_v1.json'
    composition=json.loads(composition_path.read_text());assert composition['all25_actor_native_child_and_boundary_composition_accepted']
    prefix,cells=cells_read(g.read_bytes());original_cell=actor['gds_cell']
    removed={}
    for module in actor['modules']:
        if module['instance'] not in ['commit','event']:continue
        path=BASE/'layout'/module['cell']/(module['cell']+'.gds')
        name='N'+sha(path)[:8]+'_'+hashlib.sha256(module['cell'].encode()).hexdigest()[:16]
        removed[name]=module['instance']
    kept=[];dropped=[];private=[]
    for e in elements(cells[original_cell]):
        child=next((v.rstrip(b'\0').decode() for t,d,v,b in e if t==18),None)
        text=next((v.rstrip(b'\0').decode() for t,d,v,b in e if t==25),None)
        if child in removed:
            assert e[0][0]==10;dropped.append(child)
        elif text and text.startswith(('commit__','event__')):private.append(text)
        else:kept.append(b''.join(b for t,d,v,b in e))
    assert len(dropped)==2 and set(dropped)==set(removed)
    service='GF180_ANALOG_PAGE_SERVICE_V1'
    cells[service]=begin(service)+b''.join(kept)+rec(7,0)
    needed=set()
    def visit(cell):
        if cell in needed:return
        needed.add(cell)
        for t,d,v,b in records(cells[cell]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(service)
    assert original_cell not in needed and not (set(removed)&needed)
    ports=labels(cells[service])
    required=['PAGE_RESTORE','PAGE_RESTOREB','PAGE_RECOVERED','PAGE_SHIFTED','EXTERNAL_COMPUTE_DATA',
              'STORAGE_REFERENCE','COMPUTE_REFERENCE','BETA_PHASE','DETECT_PHASE','SUBTRACTIVE_RESET_PHASE',
              'WEIGHT_SAMPLE','WEIGHT_ARM','WEIGHT_SIGN','WEIGHT_PULSE','compute__C_SPIKE','duration__MAG_DATA',
              'PAGE1024__LOW0','PAGE1024__HIGH0','PAGE1024__WRITE_CMD','PAGE1024__READ_CMD','PAGE1024__READ_ENABLE']
    assert all(p in ports for p in required),[p for p in required if p not in ports]
    bb=actor['bbox_dbu'];ox,oy=actor['origin_dbu']
    local=[bb[0]-ox,bb[1]-oy,bb[2]-ox,bb[3]-oy]
    width,height=local[2]-local[0],local[3]-local[1]
    origins=[[-local[0],-local[1]],[width+1000000-local[0],-local[1]]]
    top='GF180_PARALLEL_PAGE_SERVICE_PAIR_V1'
    body=b''.join(reference(service,*xy) for xy in origins)
    topblob=begin(top)+body+rec(7,0)
    dest=OUT/'parallel_page_service_pair_v1.gds'
    dest.write_bytes(prefix+b''.join(cells[n] for n in sorted(needed))+topblob+rec(4,0))
    public={p:v for p,v in ports.items() if '_STATE' not in p and not p.startswith('compute__STATE')}
    native_page=next(p for p in actor['modules'] if p['instance']=='page_service')
    remaining=[p for p in actor['modules'] if p['instance'] not in ['commit','event']]
    report=dict(top_cell=top,service_cell=service,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,
                lane_count=2,service_origins_dbu=origins,service_bbox_dbu=local,
                child_modules=remaining,removed_controller_instances=removed,removed_private_labels=private,
                service_ports=public,resident_page_slots_per_lane=1024,
                working_and_legacy_local_slots_per_lane=192,
                resident_pages_have_distinct_physical_instances=True,
                inherited_page_restore_compute_and_eight_column_writeback_paths=True,
                source_incremental_boundary_proof=proof_path.relative_to(ROOT).as_posix(),
                controller_driver_conflicts_removed=True,new_parent_signal_or_supply_metal_added=False,
                full_chip_layout_complete=False,full_5ms_population_service_accepted=False,
                scope='Two independent instances of the existing connected V8 native1024page, feedback reader, level shift, gated restore, scalar analog compute, signed weight-duration injector and eight analog writeback holders. Existing analog geometry/routes preserved exactly. Commit/event drivers removed to expose external categorical phases; no ideal numeric state/weight inserted. The64working+128legacy local cells remain, are separate from the1024resident page, and are not extra model identities. This candidate is not mapped into V4/V16, does not choose54105compute lanes, and has no new global supply/phase/parameter delivery, fullpage loaded transient or5ms evidence. Other adaptation/RMS/inhibition functions remain actor-level requirements.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),mp,g,proof_path,composition_path,dest]})
    (OUT/'physical_pair.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['gds','gds_bytes','lane_count','resident_page_slots_per_lane','working_and_legacy_local_slots_per_lane','controller_driver_conflicts_removed']},indent=2))

if __name__=='__main__':main()
