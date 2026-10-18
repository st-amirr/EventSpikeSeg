"""Exact rectangle lookup without a grid proportional to atlas wire length."""
from collections import defaultdict


def touch(a,b):return not(a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])


class RectIndex:
    def __init__(self):
        self.shapes=[];self.owners=[];self.layers=defaultdict(list)
        self.trees={};self.pending=defaultdict(list)

    def add(self,layer,box,owner):
        i=len(self.shapes);self.shapes.append((layer,tuple(box)));self.owners.append(owner)
        self.layers[layer].append(i);self.pending[layer].append(i);return i

    def rebuild(self):
        def build(ids):
            boxes=[self.shapes[i][1] for i in ids]
            bb=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
            if len(ids)<=12:return bb,ids,None
            xs=[b[0]+b[2] for b in boxes];ys=[b[1]+b[3] for b in boxes]
            axis=0 if max(xs)-min(xs)>=max(ys)-min(ys) else 1
            ordered=sorted(ids,key=lambda i:self.shapes[i][1][axis]+self.shapes[i][1][axis+2])
            mid=len(ids)//2;return bb,build(ordered[:mid]),build(ordered[mid:])
        self.trees={l:build(ids) for l,ids in self.layers.items() if ids}
        self.pending=defaultdict(list)

    def hits(self,layer,box):
        result=[]
        def visit(node):
            bb,left,right=node
            if not touch(bb,box):return
            if right is None:
                result.extend(i for i in left if touch(self.shapes[i][1],box))
            else:visit(left);visit(right)
        if layer in self.trees:visit(self.trees[layer])
        result.extend(i for i in self.pending[layer] if touch(self.shapes[i][1],box))
        return result
