"""Expose actual actor spike conductors while preserving the V13 state layout.

Conservative independent check: a new M5 escape may touch only the pre-existing
M5 component containing SPIKE. No new via or device is introduced. Lower-layer
connections are not used to excuse additional M5 contacts.
"""
from pathlib import Path
import collections
import hashlib
import json
import math
import struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,string,records
from assemble_gf180_full25_physical_candidate_v5 import rect,label
from prove_gf180_shared_page_parent_metal_v5 import polygon_rectangles,Paint

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_spike_breakouts_v14'

def main():
    assert not OUT.exists(), 'Preserve earlier attempts.'
    OUT.mkdir()
    source=BASE/'assembly/full25_class_current_service_v13'
    source_gds=source/'eventspikeseg140k_class_current_service_v13.gds'
    metadata=json.loads((source/'physical_assembly.json').read_text())
    terminals=BASE/'assembly/full25_layout_integration_v14/actor_boundary_ports_v1.json'
    ports=json.loads(terminals.read_text())
    assert ports['sha256'][source_gds.relative_to(ROOT).as_posix()]==hashlib.sha256(source_gds.read_bytes()).hexdigest()
    prefix,cells=cells_read(source_gds.read_bytes())
    cache={};bounds={}
    def compile_cell(n):
        if n in cache:return cache[n]
        shapes=[];children=[]
        for e in elements(cells[n]):
            if e[0][0]==8:
                layer=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                # Actual rectangular geometry contributes to bounds; M5 alone
                # enters this deliberately conservative same-layer contact proof.
                boxes=polygon_rectangles(xy)
                for box in boxes:shapes.append((layer,box))
            elif e[0][0] in [10,11]:
                assert all((t==26 and v==bytes(2)) or t not in [26,27,28] for t,d,v,b in e),'unsupported transform'
                child=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1))
                dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0
                dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0
                children.append((child,xy[0],xy[1],nx,ny,dx,dy))
            elif e[0][0]==9:raise AssertionError('unsupported PATH')
        cache[n]=(shapes,children);return cache[n]
    def bbox(n):
        if n in bounds:return bounds[n]
        shapes,children=compile_cell(n);bb=[b for layer,b in shapes]
        for child,ox,oy,nx,ny,dx,dy in children:
            x1,y1,x2,y2=bbox(child)
            for ix,iy in [(0,0),(nx-1,0),(0,ny-1),(nx-1,ny-1)]:
                x=ox+ix*dx;y=oy+iy*dy;bb.append((x+x1,y+y1,x+x2,y+y2))
        assert bb,n
        bounds[n]=(min(b[0] for b in bb),min(b[1] for b in bb),max(b[2] for b in bb),max(b[3] for b in bb))
        return bounds[n]
    overlap=lambda a,b:not(a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])
    def m5(n,ox=0,oy=0,region=None):
        bb=bbox(n)
        if region and not overlap((bb[0]+ox,bb[1]+oy,bb[2]+ox,bb[3]+oy),region):return
        own,children=compile_cell(n)
        for layer,b in own:
            if layer==81:
                q=(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)
                # Retain full rectangles touching the corridor, so the source
                # conductor is never fragmented by clipping.
                if not region or overlap(q,region):yield q
        for child,cx,cy,nx,ny,dx,dy in children:
            for iy in range(ny):
                for ix in range(nx):yield from m5(child,ox+cx+ix*dx,oy+cy+iy*dy,region)
    proofs=[];replacements={};failed=False
    for actor in ports['actors']:
        ai=actor['actor_index'];native=actor['native_actor'];name=native['cell']
        source_name='OWN_SPIKE' if 'OWN_SPIKE' in native['ports'] else 'compute__C_SPIKE'
        entries=native['ports'][source_name];assert len(entries)==1 and entries[0]['layer']==81
        x,y=entries[0]['xy_local_dbu'];bb=bbox(name);target=bb[0]-10000
        route=(target-220,y-220,x+220,y+220)
        paint=Paint()
        for box in m5(name,region=route):paint.add(81,box)
        source_component=paint.at(81,x,y)
        hits=paint.hits(81,route)
        foreign=[i for i in hits if paint.root(i)!=source_component]
        proof={'actor_index':ai,'actor':actor['actor'],'source_cell':name,
               'source_terminal':source_name,'source_xy_dbu':[x,y],
               'output_terminal':'SPIKE_RESULT','output_xy_dbu':[target,y],
               'baseline_m5_rectangles_in_corridor':len(paint.shapes),
               'foreign_m5_components_touched':len({paint.root(i) for i in foreign}),
               'foreign_rectangles':[paint.shapes[i][1] for i in foreign[:12]],
               'accepted':not foreign,'route_rect_dbu':route}
        proofs.append(proof)
        if foreign:failed=True;continue
        newname=f'ESS_ACTOR_{ai:02d}_SPIKE_V14'
        # Preserve every old element, including all child references, unchanged.
        body=b''.join(b for e in elements(cells[name]) for t,d,v,b in e)
        cells[newname]=begin(newname)+body+rect(81,route)+label('SPIKE_RESULT',target,y)+rec(7,0)
        replacements[name]=newname
    report={'all25_spike_escape_contacts_accepted':not failed,'actors':proofs,
            'scope':'Conservative M5 contact proof for native SPIKE output escapes. No new vias/devices. Does not qualify DRC spacing, parent-wrapper routes, graph binding, analog loading or full-chip service.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [source_gds,terminals,Path(__file__)]}}
    (OUT/'spike_escape_contact_proof_v1.json').write_text(json.dumps(report,indent=2)+'\n')
    if failed:
        print(json.dumps({'accepted':False,'failed_actors':[p['actor_index'] for p in proofs if not p['accepted']],'evidence':str(OUT/'spike_escape_contact_proof_v1.json')},indent=2))
        raise SystemExit(2)
    def clone(n):
        if n in replacements:return replacements[n]
        own,children=compile_cell(n)
        changed={ch:clone(ch) for ch,*_ in children}
        if not any(k!=v for k,v in changed.items()):return n
        newname=('ESS140K_SPIKE_BREAKOUTS_V14' if n==metadata['top_cell'] else n+'_SPIKE14')
        assert len(newname)<=64 and newname not in cells
        body=[]
        for t,d,v,b in records(cells[n]):
            if t==6:body.append(string(6,newname))
            elif t==18:body.append(string(18,changed[v.rstrip(b'\0').decode()]))
            else:body.append(b)
        cells[newname]=b''.join(body);replacements[n]=newname;return newname
    top=clone(metadata['top_cell']);reachable={}
    def visit(n):
        if n in reachable:return
        reachable[n]=cells[n]
        for e in elements(cells[n]):
            for t,d,v,b in e:
                if t==18:visit(v.rstrip(b'\0').decode())
    visit(top)
    dest=OUT/'eventspikeseg140k_spike_breakouts_v14.gds'
    dest.write_bytes(prefix+b''.join(reachable.values())+rec(4,0))
    report.update(gds=dest.relative_to(ROOT).as_posix(),top_cell=top,
                  cloned_cells=replacements,source_state_layout_preserved=True,
                  full_chip_layout_complete=False)
    report['sha256'][dest.relative_to(ROOT).as_posix()]=hashlib.sha256(dest.read_bytes()).hexdigest()
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'accepted':True,'actors':25,'top_cell':top,'gds':str(dest),'bytes':dest.stat().st_size,'full_chip_layout_complete':False},indent=2))

if __name__=='__main__':main()
