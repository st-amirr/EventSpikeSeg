"""Read exact GDS cell byte slices without allocating all record tuples."""
import struct

def cells_read(blob):
    cells={};offset=0;start=None;first=None;name=None
    while offset<len(blob):
        assert offset+4<=len(blob)
        n,t,d=struct.unpack_from('>HBB',blob,offset)
        assert n>=4 and n%2==0 and offset+n<=len(blob)
        if t==5:
            assert start is None;start=offset
            if first is None:first=offset
        elif t==6:
            assert start is not None and name is None;name=blob[offset+4:offset+n].rstrip(b'\0').decode()
            assert name not in cells
        elif t==7:
            assert start is not None and name is not None;cells[name]=blob[start:offset+n];start=None;name=None
        offset+=n
    assert offset==len(blob) and start is None and first is not None
    return blob[:first],cells
