"""Read back V14 and check escapes against enclosing V13 parent wiring."""
from pathlib import Path
import hashlib,json,struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import records
from prove_gf180_shared_page_parent_metal_v5 import Paint,polygon_rectangles

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_spike_breakouts_v14'

class Geometry:
    def __init__(self,cells):self.cells=cells;self.index={};self.boxes={}
    def parse(self,n):
        if n in self.index:return self.index[n]
        shapes=[];children=[]
        for e in elements(self.cells[n]):
            if e[0][0]==8:
                layer=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                shapes.extend((layer,b) for b in polygon_rectangles(xy))
            elif e[0][0] in [10,11]:
                assert all((t==26 and v==bytes(2)) or t not in [26,27,28] for t,d,v,b in e),'unsupported transform'
                child=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1))
                dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0
                children.append((child,xy[0],xy[1],nx,ny,dx,dy))
            elif e[0][0]==9:raise AssertionError('unsupported PATH')
        self.index[n]=(shapes,children);return self.index[n]
    def bbox(self,n):
        if n in self.boxes:return self.boxes[n]
        shapes,children=self.parse(n);bb=[b for layer,b in shapes]
        for child,ox,oy,nx,ny,dx,dy in children:
            b=self.bbox(child)
            for ix,iy in [(0,0),(nx-1,0),(0,ny-1),(nx-1,ny-1)]:
                x=ox+ix*dx;y=oy+iy*dy;bb.append((x+b[0],y+b[1],x+b[2],y+b[3]))
        assert bb,n
        result=(min(b[0] for b in bb),min(b[1] for b in bb),max(b[2] for b in bb),max(b[3] for b in bb))
        self.boxes[n]=result;return result
    def m5(self,n,region,ox=0,oy=0):
        overlaps=lambda b:not(b[2]<region[0] or b[0]>region[2] or b[3]<region[1] or b[1]>region[3])
        b=self.bbox(n)
        if not overlaps((b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)):return
        own,children=self.parse(n)
        for layer,b in own:
            q=(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)
            if layer==81 and overlaps(q):yield q
        for ch,x,y,nx,ny,dx,dy in children:
            for iy in range(ny):
                for ix in range(nx):yield from self.m5(ch,region,ox+x+ix*dx,oy+y+iy*dy)

def main():
    dest=OUT/'full_parent_readback_v1.json';assert not dest.exists()
    assembly=OUT/'physical_assembly.json';m=json.loads(assembly.read_text())
    oldg=BASE/'assembly/full25_class_current_service_v13/eventspikeseg140k_class_current_service_v13.gds'
    newg=ROOT/m['gds'];ports=BASE/'assembly/full25_layout_integration_v14/actor_boundary_ports_v1.json'
    p=json.loads(ports.read_text());_,old=cells_read(oldg.read_bytes());_,new=cells_read(newg.read_bytes())
    # Strong preservation check: all source geometry/AREF multiplicities and
    # native children are byte-identical; only known SREF names and 25 additions differ.
    mapping=m['cloned_cells'];actors={a['source_cell']:a for a in m['actors']}
    retained=0;cloned=0
    for name,blob in old.items():
        if name not in mapping:
            assert name in new and new[name]==blob,name;retained+=1;continue
        target=mapping[name]
        if name in actors:
            old_elements=list(elements(blob));new_elements=list(elements(new[target]))
            assert new_elements[:len(old_elements)]==old_elements,name
            assert len(new_elements)==len(old_elements)+2,name
        else:
            a=list(records(blob));b=list(records(new[target]));assert len(a)==len(b)
            for (t,d,v,raw),(nt,nd,nv,nraw) in zip(a,b):
                assert t==nt and d==nd
                if t==6:assert nv.rstrip(b'\0').decode()==target
                elif t==18:
                    child=v.rstrip(b'\0').decode();assert nv.rstrip(b'\0').decode()==mapping.get(child,child)
                else:assert raw==nraw,(name,t)
        cloned+=1
    geom=Geometry(old);proofs=[]
    for actor,route in zip(p['actors'],m['actors']):
        assert actor['actor_index']==route['actor_index']
        ox,oy=actor['native_actor']['origin_top_dbu']
        x,y=route['source_xy_dbu'];x+=ox;y+=oy
        b=route['route_rect_dbu'];region=(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)
        paint=Paint()
        for box in geom.m5(p['source_top'],region):paint.add(81,box)
        source=paint.at(81,x,y);hits=paint.hits(81,region)
        foreign=[i for i in hits if paint.root(i)!=source]
        proofs.append({'actor_index':actor['actor_index'],'baseline_m5_rectangles':len(paint.shapes),
                       'foreign_parent_m5_components':len({paint.root(i) for i in foreign}),
                       'foreign_rectangles':[paint.shapes[i][1] for i in foreign[:8]],'accepted':not foreign,
                       'output_top_dbu':[route['output_xy_dbu'][0]+ox,route['output_xy_dbu'][1]+oy]})
    passed=all(p['accepted'] for p in proofs)
    report={'full_parent_escape_contacts_accepted':passed,'actors':proofs,
            'source_native_cells_byte_verified':retained,'cloned_source_cells_verified':cloned,
            'existing_state_geometry_and_array_multiplicities_preserved':True,
            'full_chip_layout_complete':False,
            'scope':'Read back actual V14 GDS; every unchanged source cell and every cloned ancestor checked bytewise apart from intended cell-reference renames and25 escape rectangles/labels. Full V13 enclosing-parent M5 contact check detects additional contacts. No spacing DRC, RC/loading, outer port or graph binding acceptance.',
            'sha256':{q.relative_to(ROOT).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in [assembly,oldg,newg,ports,Path(__file__)]}}
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['actors','sha256']},indent=2))
    if not passed:raise SystemExit(2)

if __name__=='__main__':main()
