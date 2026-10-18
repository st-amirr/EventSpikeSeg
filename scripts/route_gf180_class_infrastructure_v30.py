"""Connect the full class-current/readout wrapper to four existing research rails."""
from pathlib import Path
import json,time
from gf180_v26_parent_index_v1 import build_index
from route_gf180_native_addresses_v23 import wire,transition,conflicts,astar,occupied_astar
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from assemble_gf180_full25_physical_candidate_v5 import rect
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'assembly/full25_class_infrastructure_v30'

def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    sd=BASE/'assembly/full25_class_interfaces_v28';mf=sd/'physical_assembly.json';m=json.loads(mf.read_text());proof=sd/'independent_readback_v1.json';assert json.loads(proof.read_text())['readback_pass']
    source=ROOT/m['gds'];assert sha(source)==m['sha256'][m['gds']]
    ep=sd/'escape_plan.json';em=json.loads(ep.read_text());index,inp,paths=build_index()
    controlp=BASE/'assembly/full25_control_supplies_v27/route_plan.json'
    for n in json.loads(controlp.read_text())['routes']:
        for l,b in n['shapes']:index.add(l,b,n['net'])
    nets=['VDD','VSS','STORAGE_REFERENCE','COMPUTE_REFERENCE']
    for e in em['escapes']:index.add(81,e['rectangle_top_dbu'],e['native_pin'] if e['native_pin'] in nets else e['escape_label'])
    index.rebuild();railpaths=[BASE/'assembly/full25_analog_supplies_v25/route_plan.json',BASE/'assembly/full25_analog_references_v26/route_plan.json']
    rails={}
    for p in railpaths:
        plan=json.loads(p.read_text())
        for n in plan.get('external_supply_terminals',plan.get('external_reference_terminals',[])):rails[n['net']]=n
    bb=next(o['bbox_dbu'] for o in inp['obstacles'] if o.get('cell')==em['source_cell']);bb=list(bb);bb[0]=min(e['rectangle_top_dbu'][0] for e in em['escapes'])
    cb=json.loads((BASE/'assembly/full25_native_address_routes_v23/route_plan.json').read_text())['source_exit_envelope_dbu']
    obstacles=[bb if o.get('cell')==em['source_cell'] else cb if o['kind']=='categorical_control_and_parent_wiring' else o['bbox_dbu'] for o in inp['obstacles']]
    routes=[];failures=[]
    for ni,net in enumerate(nets):
        e=next(e for e in em['escapes'] if e['native_pin']==net);x,y=e['escaped_top_dbu'];base_bx=bb[0]-20000-ni*20000
        h,v=(42,46) if ni%2==0 else (36,34);start=tuple(rails[net]['xy_top_dbu']);attempts=[];selected=None
        for margin,bx in [(m,base_bx-trial*2000) for trial in range(64) for m in (50000,100000,250000,500000,750000,1000000,1500000,2000000,3000000,4000000)]:
            end=(bx,bb[3]+margin);p=(bx,y);tail=[wire(81,(x,y),p)]+transition(81,v,p)+[wire(v,p,end)]
            bad=conflicts(index,tail,net)
            if bad:attempts.append(dict(margin=margin,stage='branch',conflicts=bad));continue
            for occupied in (False,True):
                try:points=occupied_astar(start,end,obstacles,margin,index,net,h,v) if occupied else astar(start,end,obstacles,margin)
                except (RuntimeError,AssertionError) as error:attempts.append(dict(margin=margin,error=str(error)));continue
                shapes=[];previous=h
                for a,b in zip(points,points[1:]):
                    layer=h if a[1]==b[1] else v;shapes+=transition(previous,layer,a)+[wire(layer,a,b)];previous=layer
                shapes+=transition(previous,v,end)+tail;bad=conflicts(index,shapes,net)
                if bad:attempts.append(dict(margin=margin,conflicts=bad));continue
                selected=(points,shapes);break
            if selected:break
        if not selected:failures.append(dict(net=net,attempts=attempts));break
        points,shapes=selected;endpoint=dict(layer=81,xy_top_dbu=e['escaped_top_dbu'],pin=net)
        routes.append(dict(net=net,source=rails[net],endpoints=[endpoint],shapes=shapes,global_points_dbu=points))
        for l,b in shapes:index.add(l,b,net)
        index.rebuild();print('Class rail routed: '+net,flush=True)
    plan=dict(routes=routes,failures=failures,all_class_infrastructure_routes_built=len(routes)==4,scope='Four existing research supply/reference rails reach the native class-current/readout wrapper. Input events/contributions/address/phases remain explicit external module interfaces; no autonomous output or loaded global timing claim.')
    (OUT/'route_plan.json').write_text(json.dumps(plan,indent=2)+'\n');assert not failures,failures[:1]
    top='ESS140K_CLASS_INFRASTRUCTURE_V30';dest=OUT/'eventspikeseg140k_class_infrastructure_v30.gds'
    with source.open('rb') as a,dest.open('wb') as out:
        remaining=source.stat().st_size-4
        while remaining:
            chunk=a.read(min(1048576,remaining));out.write(chunk);remaining-=len(chunk)
        out.write(begin(top)+reference(m['top_cell'],0,0))
        for n in routes:
            for l,b in n['shapes']:out.write(rect(l,b))
        out.write(rec(7,0)+rec(4,0))
    report=dict(top_cell=top,gds=dest.relative_to(ROOT).as_posix(),gds_bytes=dest.stat().st_size,class_supply_reference_terminals_routed=4,actual_gds_readback_pass=False,full_architecture_layout_complete=False,accumulation_5ms_accepted=False,elapsed_seconds=time.monotonic()-started,sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_v26_parent_index_v1.py',mf,proof,source,ep,controlp,*paths,*railpaths,OUT/'route_plan.json',dest]})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
