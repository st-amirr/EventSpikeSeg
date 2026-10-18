"""Join the three categorical macros to the existing V26 research supply rails."""
from pathlib import Path
import json,time
from gf180_v26_parent_index_v1 import build_index
from route_gf180_native_addresses_v23 import wire,transition,conflicts,astar,occupied_astar
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from assemble_gf180_full25_physical_candidate_v5 import rect,label
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'assembly/full25_control_supplies_v27'

def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    pp=BASE/'assembly/control_power_inputs_v27c/power_contact_inputs.json';power=json.loads(pp.read_text());assert power['native_upper_power_grids_verified']
    for p,d in power['sha256'].items():assert sha(ROOT/p)==d,p
    source_meta=BASE/'assembly/full25_analog_references_v26/physical_assembly.json';m=json.loads(source_meta.read_text());source=ROOT/m['gds'];assert sha(source)==m['sha256'][m['gds']]
    index,inp,paths=build_index();ng=pp.parent/'native_contact_geometry.json'
    for l,b,owner in json.loads(ng.read_text()):index.add(l,b,owner)
    index.rebuild()
    ap=json.loads((BASE/'assembly/full25_native_address_routes_v23/route_plan.json').read_text());cb=ap['source_exit_envelope_dbu']
    obstacles=[o['bbox_dbu'] if o['kind']!='categorical_control_and_parent_wiring' else cb for o in inp['obstacles']]
    rails=json.loads((BASE/'assembly/full25_analog_supplies_v25/route_plan.json').read_text())['external_supply_terminals'];rails={n['net']:n for n in rails}
    routes=[];failures=[]
    for si,s in enumerate(power['sources']):
        net=s['net'];h,v=(42,46) if net=='VDD' else (36,34);start=tuple(rails[net]['xy_top_dbu']);x,y=s['xy_top_dbu'];bb=s['macro_bbox_dbu'];selected=None;attempts=[]
        for trial in range(12):
            ex=bb[0]-900000-trial*40000-si*10000;bottom=cb[1]-2000000-si*20000-trial*1000;end=(cb[0]-3000000-si*20000,bottom)
            initial=[wire(81,(x,y),(ex,y))]+transition(81,34,(ex,y))+[wire(34,(ex,y),(ex,bottom))]+transition(34,36,(ex,bottom))+[wire(36,(ex,bottom),end)]+transition(36,v,end)
            bad=conflicts(index,initial,net)
            if bad:attempts.append(dict(trial=trial,stage='source_exit',conflicts=bad));continue
            for margin in (50000,100000,250000,500000,1000000,2000000):
                for occupied in (False,True):
                    try:points=occupied_astar(start,end,obstacles,margin,index,net,h,v) if occupied else astar(start,end,obstacles,margin)
                    except (RuntimeError,AssertionError) as error:attempts.append(dict(trial=trial,margin=margin,error=str(error)));continue
                    shapes=[];previous=h
                    for a,b in zip(points,points[1:]):
                        layer=h if a[1]==b[1] else v;shapes+=transition(previous,layer,a)+[wire(layer,a,b)];previous=layer
                    shapes+=transition(previous,v,end)+initial
                    bad=conflicts(index,shapes,net)
                    if bad:attempts.append(dict(trial=trial,margin=margin,conflicts=bad));continue
                    selected=(points,shapes,initial);break
                if selected:break
            if selected:break
        if not selected:failures.append(dict(source=s,attempts=attempts));break
        points,shapes,initial=selected
        routes.append(dict(net=net,source=rails[net],endpoints=[s],shapes=shapes,source_exit_shapes=initial,global_points_dbu=points))
        for l,b in shapes:index.add(l,b,net)
        index.rebuild();print(json.dumps(dict(instance=s['instance'],supply=net,routed=len(routes),elapsed_seconds=round(time.monotonic()-started,1))),flush=True)
    plan=dict(routes=routes,failures=failures,all_control_supply_routes_built=len(routes)==6,scope='Joins six native upper power-grid components to existing research analog rails. Native grids are independently read back. Thin-wire topology only, with no global IR/EM/loading/timing qualification.',elapsed_seconds=time.monotonic()-started)
    (OUT/'route_plan.json').write_text(json.dumps(plan,indent=2)+'\n');assert not failures,[(f['source']['instance'],f['source']['net']) for f in failures]
    top='ESS140K_CONTROL_SUPPLIES_V27';dest=OUT/'eventspikeseg140k_control_supplies_v27.gds'
    with source.open('rb') as a,dest.open('wb') as out:
        remaining=source.stat().st_size-4
        while remaining:
            chunk=a.read(min(1048576,remaining));out.write(chunk);remaining-=len(chunk)
        out.write(begin(top)+reference(m['top_cell'],0,0))
        for n in routes:
            for l,b in n['shapes']:out.write(rect(l,b))
        out.write(rec(7,0)+rec(4,0))
    report=dict(top_cell=top,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,categorical_supply_terminals_routed=6,actual_gds_readback_pass=False,full_architecture_layout_complete=False,accumulation_5ms_accepted=False,scope=plan['scope'],sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_v26_parent_index_v1.py',pp,ng,source_meta,source,*paths,OUT/'route_plan.json',dest]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
