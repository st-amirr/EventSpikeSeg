"""Stream native GDS conductors with GF180 MIM-aware via classification."""
import struct
from assemble_gf180_full_capacity_storage_gds_v2 import real8
from assemble_gf180_external_bank_service_full25_v5 import elements
from prove_gf180_shared_page_parent_metal_v5 import Paint,LAYERS,VIA,polygon_rectangles

def native_paint(cells,root):
    cache={};paint=Paint()
    def compiled(name):
        if name in cache:return cache[name]
        shapes=[];children=[];caps=[];capdef=[]
        for e in elements(cells[name]):
            if e[0][0]!=8:continue
            layer=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
            if layer not in [75,117]:continue
            xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
            (caps if layer==75 else capdef).extend(polygon_rectangles(xy))
        for e in elements(cells[name]):
            typ=e[0][0]
            if typ==8:
                layer=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
                if layer not in LAYERS:continue
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                for box in polygon_rectangles(xy):
                    out=layer
                    if layer==41:
                        inside=lambda r:r[0]<=box[0] and r[1]<=box[1] and r[2]>=box[2] and r[3]>=box[3]
                        overlaps=lambda r:not(r[2]<box[0] or r[0]>box[2] or r[3]<box[1] or r[1]>box[3])
                        if any(inside(r) for r in caps):out=141
                        elif any(overlaps(r) for r in caps+capdef):raise AssertionError(('partial MIM via',name,box))
                    shapes.append((out,box))
            elif typ in [10,11]:
                flags=next((struct.unpack('>H',v)[0] for t,d,v,b in e if t==26),0)
                assert flags & 0x7fff == 0,('unsupported absolute transform',flags)
                magnitude=next((real8(v) for t,d,v,b in e if t==27),1.)
                angle=next((real8(v) for t,d,v,b in e if t==28),0.)
                assert abs(magnitude-1)<1e-12 and abs(angle/90-round(angle/90))<1e-10
                rotation=[(1,0,0,1),(0,-1,1,0),(-1,0,0,-1),(0,1,-1,0)][round(angle/90)%4]
                ca,cb,cc,cd=rotation
                if flags & 0x8000:cb=-cb;cd=-cd
                child=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1))
                dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0
                children.append((child,xy[0],xy[1],nx,ny,dx,dy,(ca,cb,cc,cd)))
            elif typ==9:raise AssertionError('unsupported PATH')
        cache[name]=(shapes,children);return cache[name]
    def visit(name,transform=(1,0,0,1,0,0)):
        a,b,c,d,ox,oy=transform;shapes,children=compiled(name)
        for layer,box in shapes:
            points=[(a*x+b*y+ox,c*x+d*y+oy) for x in [box[0],box[2]] for y in [box[1],box[3]]]
            paint.add(layer,(min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)))
        for child,cx,cy,nx,ny,dx,dy,matrix in children:
            ca,cb,cc,cd=matrix
            for iy in range(ny):
                for ix in range(nx):
                    x=cx+ix*dx;y=cy+iy*dy
                    visit(child,(a*ca+b*cc,a*cb+b*cd,c*ca+d*cc,c*cb+d*cd,a*x+b*y+ox,c*x+d*y+oy))
    visit(root);paint.vias();return paint

def touched(paint,layer,box):
    layers={layer}
    if layer in VIA:layers.update(VIA[layer])
    else:layers.update(cut for cut,metals in VIA.items() if layer in metals)
    return {paint.root(i) for lay in layers for i in paint.hits(lay,box)}

def add_connected(paint,shapes):
    first=len(paint.shapes)
    for layer,box in shapes:paint.add(layer,box)
    paint.vias(first)
    # A new conductor may also land on an existing via.
    for layer,box in shapes:
        for cut,metals in VIA.items():
            if layer not in metals:continue
            for ci in paint.hits(cut,box):
                for mi in paint.hits(layer,paint.shapes[ci][1]):paint.join(ci,mi)
