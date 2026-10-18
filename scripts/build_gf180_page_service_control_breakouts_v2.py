"""Find real pin escapes without contacting unrelated native conductors."""
from pathlib import Path
import hashlib,json,time
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec
from assemble_gf180_full25_physical_candidate_v5 import rect,label
from assemble_gf180_full25_shared_page1024_v7 import labels
from gf180_service_metal_graph import native_paint,touched,add_connected

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/page_service_control_breakouts_v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wire(layer,a,b):
    assert a[0]==b[0] or a[1]==b[1]
    h=140 if layer==42 else 220
    return layer,(min(a[0],b[0])-h,min(a[1],b[1])-h,max(a[0],b[0])+h,max(a[1],b[1])+h)
def via(low,high,cut,p):
    x,y=p;return [(low,(x-300,y-300,x+300,y+300)),(high,(x-300,y-300,x+300,y+300)),(cut,(x-130,y-130,x+130,y+130))]

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    src=BASE/'assembly/parallel_page_service_pair_v1';meta=src/'physical_pair.json';m=json.loads(meta.read_text())
    original=ROOT/m['gds'];prefix,cells=cells_read(original.read_bytes());root=m['service_cell']
    pin=labels(cells[root]);paint=native_paint(cells,root);baseline=len(paint.shapes)
    all_roots={name:paint.at(*value) for name,value in pin.items()}
    names=[f'PAGE1024__LOW{k}' for k in range(4)]+[f'PAGE1024__HIGH{k}' for k in range(3)]
    names += [f'PAGE1024__SEL{k}' for k in range(8)]
    names += ['PAGE1024__READ_CMD','PAGE1024__READ_ENABLE','PAGE1024__WRITE_CMD','PAGE_RESTORE','PAGE_RESTOREB',
              'compute__INIT','compute__INITB','compute__C_WRITE','compute__C_WRITEB','EXTERNAL_INITIALIZE','EXTERNAL_INITIALIZEB']
    names += [f'compute__CAP{k}' for k in range(8)]+[f'compute__CAPB{k}' for k in range(8)]
    names += ['VDD','VSS','COMPUTE_REFERENCE','EXTERNAL_INIT_DATA',
              'compute__WRITE_CMD','compute__READ_CMD','compute__READ_ENABLE','compute__RESTORE','compute__RESTOREB',
              'EXTERNAL_RESTORE','EXTERNAL_RESTOREB','bank_service__WRITE_CMD','bank_service__READ_CMD','bank_service__READ_ENABLE']
    names += [f'compute__SEL{k}' for k in range(8)]+[f'bank_service__SEL{k}' for k in range(8)]
    names += [f'compute__A{k}' for k in range(3)]+[f'bank_service__A{k}' for k in range(3)]+['bank_service__BANK_SELECT']
    assert len(names)==len(set(names)) and all(n in pin for n in names)
    body=[];escapes=[];failures=[];bb=m['service_bbox_dbu']
    def allowed(shapes,owner):
        expected=paint.root(all_roots[owner])
        for layer,b in shapes:
            # Thin-wire GF180D spacing: M3/M4 .28um, M5 .46um; via cuts .26um.
            guard=460 if layer==81 else 280 if layer in [42,46] else 260
            q=(b[0]-guard,b[1]-guard,b[2]+guard,b[3]+guard)
            if touched(paint,layer,q)-{expected}:return False
        return True
    for index,name in enumerate(names):
        layer,x,y=pin[name];start=(x,y);margin=20000+index*2000;candidates=[]
        # Try horizontal M5 first; the native parent already exposes many M5 pads.
        if layer==81:
            for ex in [bb[0]-margin,bb[2]+margin]:
                candidates.append(([(81,(min(x,ex)-220,y-220,max(x,ex)+220,y+220))],(ex,y),81))
        # Escape on M4 above/below the macro. M3/M5 pin stubs offset the riser
        # to avoid shared-x terminal shorts; each candidate checks actual paint.
        offsets=[0]+[sign*step for step in range(2000,100001,2000) for sign in [-1,1]]
        for dx in offsets:
            ex=x+dx
            for ey in [bb[3]+margin,bb[1]-margin]:
                shapes=[]
                if layer==42:
                    shapes.append(wire(42,start,(ex,y)));shapes+=via(42,46,40,(ex,y))
                elif layer==81:
                    shapes.append(wire(81,start,(ex,y)));shapes+=via(46,81,41,(ex,y))
                elif layer==46:
                    if dx:continue
                else:raise AssertionError((name,layer))
                shapes.append(wire(46,(ex,y),(ex,ey)));shapes+=via(46,81,41,(ex,ey))
                candidates.append((shapes,(ex,ey),81))
        selected=next((v for v in candidates if allowed(v[0],name)),None)
        if selected is None:
            failures.append(dict(port=name,source=pin[name],candidate_count=len(candidates)));break
        shapes,endpoint,outlayer=selected;add_connected(paint,shapes)
        assert paint.at(outlayer,*endpoint)==paint.root(all_roots[name])
        body.extend(rect(l,b) for l,b in shapes);body.append(label('CONTROL__'+name,*endpoint,outlayer))
        escapes.append(dict(port=name,source=pin[name],escaped=[outlayer,*endpoint],shapes=shapes))
    plan=dict(success=not failures,baseline_conductor_rectangles=baseline,escapes=escapes,failures=failures,
              elapsed_seconds=time.monotonic()-started,scope='Ray escapes screened against the complete MIM-aware native conductor graph and previously added escapes, with GF180D thin-wire .28um M3/M4, .46um M5 and .26um cut guards. No unrelated native component may be contacted. Final GDS readback is still required.')
    (OUT/'route_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    assert not failures,failures
    new='GF180_PAGE_SERVICE_CONTROLS_V2'
    old_body=b''.join(b''.join(b for t,d,v,b in e) for e in elements(cells[root]))
    cells[new]=begin(new)+old_body+b''.join(body)+rec(7,0)
    # Keep only the new root and its existing analog child hierarchy.
    from assemble_gf180_full_capacity_storage_gds_v2 import records
    needed=set()
    def visit(n):
        if n in needed:return
        needed.add(n)
        for t,d,v,b in records(cells[n]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(new)
    gds=OUT/'page_service_control_breakouts_v2.gds';gds.write_bytes(prefix+b''.join(cells[n] for n in sorted(needed))+rec(4,0))
    report=dict(service_cell=new,gds=gds.relative_to(ROOT).as_posix(),escaped_port_count=len(escapes),
                native_service_cell=root,original_service_bbox_dbu=bb,escapes=escapes,
                source_analog_geometry_preserved=True,full_chip_layout_complete=False,
                scope='Independent native page/compute service with safe external control/initialization/power pads. No controller connection, global operation, analog loaded timing or5ms proof yet.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/gf180_service_metal_graph.py',meta,original,gds,OUT/'route_plan.json']})
    (OUT/'physical_breakouts.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(gds=str(gds),escaped_ports=len(escapes),elapsed_seconds=time.monotonic()-started),indent=2))

if __name__=='__main__':main()
