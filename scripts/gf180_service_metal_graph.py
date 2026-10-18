"""Stream native GDS conductors with GF180 MIM-aware via classification."""
import struct
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
                assert all((t==26 and v==bytes(2)) or t not in [26,27,28] for t,d,v,b in e)
                child=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1))
                dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0
                children.append((child,xy[0],xy[1],nx,ny,dx,dy))
            elif typ==9:raise AssertionError('unsupported PATH')
        cache[name]=(shapes,children);return cache[name]
    def visit(name,x=0,y=0):
        shapes,children=compiled(name)
        for layer,b in shapes:paint.add(layer,(b[0]+x,b[1]+y,b[2]+x,b[3]+y))
        for child,cx,cy,nx,ny,dx,dy in children:
            for iy in range(ny):
                for ix in range(nx):visit(child,x+cx+ix*dx,y+cy+iy*dy)
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
