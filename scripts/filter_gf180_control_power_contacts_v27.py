"""Keep every native upper shape intersecting the six permitted M5 approaches."""
from pathlib import Path
import json,re,time
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/assembly/control_power_inputs_v27c'

def main():
    started=time.monotonic();mp=OUT/'power_inputs.json';m=json.loads(mp.read_text());src=OUT/'native_upper_geometry.json';assert sha(src)==m['sha256'][src.relative_to(ROOT).as_posix()]
    corridors=[]
    for s in m['sources']:
        x,y=s['xy_top_dbu'];bb=s['macro_bbox_dbu'];corridors.append([bb[0]-2000000,y-1000,x+1000,y+1000])
    pattern=re.compile(rb'\[(\d+), \[(-?\d+), (-?\d+), (-?\d+), (-?\d+)\], "([^"]+)"\]')
    count=0;kept=[];tail=b''
    with src.open('rb') as f:
        while True:
            chunk=f.read(1048576)
            if not chunk:break
            data=tail+chunk;end=0
            for match in pattern.finditer(data):
                count+=1;end=match.end();l,x1,y1,x2,y2,owner=match.groups();bb=tuple(int(v) for v in (x1,y1,x2,y2))
                if any(not(bb[2]<c[0] or bb[0]>c[2] or bb[3]<c[1] or bb[1]>c[3]) for c in corridors):kept.append([int(l),bb,owner.decode()])
            tail=data[end:];assert len(tail)<1000,('unexpected noncanonical geometry serialization',len(tail))
    assert count==sum(a['actual_upper_shapes'] for a in m['macros']),(count,m['macros'])
    gp=OUT/'native_contact_geometry.json';assert not gp.exists();gp.write_text(json.dumps(kept)+'\n')
    result=dict(m);result.update(native_approach_corridors_dbu=corridors,complete_native_shapes_scanned=count,corridor_shapes_retained=len(kept),contact_geometry=gp.relative_to(ROOT).as_posix(),elapsed_filter_seconds=time.monotonic()-started)
    result['sha256']={**m['sha256'],**{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),mp,gp]}}
    (OUT/'power_contact_inputs.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(scanned=count,retained=len(kept),elapsed_seconds=time.monotonic()-started)),flush=True)
if __name__=='__main__':main()
