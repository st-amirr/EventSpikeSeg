"""Independent GDS/metal readback for native service control escapes."""
from pathlib import Path
import collections,hashlib,json,struct,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full25_shared_page1024_v7 import labels
from prove_gf180_shared_page_parent_metal_v5 import polygon_rectangles
from gf180_service_metal_graph import native_paint,touched

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/page_service_control_breakouts_v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def own_shapes(body):
    shapes=[]
    for e in body:
        if e[0][0]!=8:continue
        layer=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
        xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
        shapes.extend((layer,b) for b in polygon_rectangles(xy))
    return shapes

def main():
    started=time.monotonic();meta=OUT/'physical_breakouts.json';m=json.loads(meta.read_text())
    for name,digest in m['sha256'].items():assert sha(ROOT/name)==digest,name
    source=BASE/'assembly/parallel_page_service_pair_v1';sm=json.loads((source/'physical_pair.json').read_text())
    src=ROOT/sm['gds'];_,old=cells_read(src.read_bytes());gds=ROOT/m['gds'];_,new=cells_read(gds.read_bytes())
    old_body=list(elements(old[sm['service_cell']]));new_body=list(elements(new[m['service_cell']]))
    assert old_body==new_body[:len(old_body)]
    assert all(new[n]==blob for n,blob in old.items() if n in new and n!=m['service_cell'])
    added=own_shapes(new_body[len(old_body):]);expected=collections.Counter()
    owners={}
    for escape in m['escapes']:
        for layer,b in escape['shapes']:
            key=layer,tuple(b);expected[key]+=1;owners.setdefault(key,set()).add(escape['port'])
    assert collections.Counter(added)==expected and all(len(v)==1 for v in owners.values())
    oldpaint=native_paint(old,sm['service_cell']);oldpins=labels(old[sm['service_cell']])
    oldroots={n:oldpaint.at(*p) for n,p in oldpins.items()}
    for layer,b in added:
        owner=next(iter(owners[layer,b]));assert touched(oldpaint,layer,b)<={oldroots[owner]},(owner,'foreign native contact')
        if layer==41:assert not oldpaint.hits(75,b),(owner,'new Via4 overlaps native CAPM')
    final=native_paint(new,m['service_cell']);pins=labels(new[m['service_cell']])
    # Every original boundary equivalence class must stay distinct.
    components=collections.defaultdict(set)
    for n,p in oldpins.items():components[final.at(*p)].add(oldroots[n])
    assert all(len(v)==1 for v in components.values()),'native nets aliased'
    known=set(components)
    for escape in m['escapes']:
        n=escape['port'];assert pins['CONTROL__'+n]==tuple(escape['escaped'])
        assert final.at(*pins['CONTROL__'+n])==final.at(*pins[n]),(n,'open')
    for layer,b in added:
        x=(b[0]+b[2])//2;y=(b[1]+b[3])//2
        assert final.at(layer,x,y) in known,'floating new paint'
    report=dict(readback_pass=True,escaped_control_reference_supply_ports=len(m['escapes']),
                new_native_aliases=0,opens=0,floating_new_rectangles=0,
                new_via4_over_native_CAPM=0,original_analog_library_and_parent_elements_preserved=True,
                added_conductor_rectangles=len(added),elapsed_seconds=time.monotonic()-started,
                scope='Independent actual GDS and complete MIM-aware native metal graph: all79source-to-escaped-pad paths, no new aliases/opens/floating additions, no foreign native contacts and no new Via4 over native CAPM. Source child cells and parent element prefix unchanged. Thin-wire guards checked during routing; no new full-style Magic DRC/device extraction/loaded RC or5ms proof.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_service_metal_graph.py',meta,src,gds]})
    path=OUT/'independent_readback_v1.json';assert not path.exists();path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['sha256','scope']},indent=2))

if __name__=='__main__':main()
