"""Conservative M5 corridor geometry with hierarchical bbox pruning.

For native orthogonal, untranslated-by-rotation analog hierarchies only.
Cells outside a corridor are pruned before expanding repeated storage pages.
"""
import struct
from assemble_gf180_external_bank_service_full25_v5 import elements
from prove_gf180_shared_page_parent_metal_v5 import polygon_rectangles


def overlap(a,b):return not(a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])


class Corridors:
    def __init__(self,cells):self.cells=cells;self.cache={};self.bounds={}

    def compiled(self,name):
        if name in self.cache:return self.cache[name]
        shapes=[];children=[]
        for e in elements(self.cells[name]):
            typ=e[0][0]
            if typ==8:
                layer=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                shapes.extend((layer,b) for b in polygon_rectangles(xy))
            elif typ in [10,11]:
                assert all((t==26 and v==bytes(2)) or t not in [26,27,28] for t,d,v,b in e),'unsupported native transform'
                child=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==18)
                xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
                nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1))
                dx=(xy[2]-xy[0])//nx if len(xy)>2 else 0;dy=(xy[5]-xy[1])//ny if len(xy)>2 else 0
                children.append((child,xy[0],xy[1],nx,ny,dx,dy))
            elif typ==9:raise AssertionError('Native corridor proof does not support PATH')
        self.cache[name]=(shapes,children);return shapes,children

    def bbox(self,name):
        if name in self.bounds:return self.bounds[name]
        shapes,children=self.compiled(name);bb=[b for l,b in shapes]
        for child,ox,oy,nx,ny,dx,dy in children:
            b=self.bbox(child)
            for ix,iy in [(0,0),(nx-1,0),(0,ny-1),(nx-1,ny-1)]:
                x,y=ox+ix*dx,oy+iy*dy;bb.append((b[0]+x,b[1]+y,b[2]+x,b[3]+y))
        assert bb,name
        result=(min(b[0] for b in bb),min(b[1] for b in bb),max(b[2] for b in bb),max(b[3] for b in bb))
        self.bounds[name]=result;return result

    def m5(self,name,region,ox=0,oy=0):
        bb=self.bbox(name);q=(bb[0]+ox,bb[1]+oy,bb[2]+ox,bb[3]+oy)
        if not overlap(q,region):return
        own,children=self.compiled(name)
        for layer,b in own:
            q=(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy)
            if layer==81 and overlap(q,region):yield q
        for child,cx,cy,nx,ny,dx,dy in children:
            for iy in range(ny):
                for ix in range(nx):yield from self.m5(child,region,ox+cx+ix*dx,oy+cy+iy*dy)
