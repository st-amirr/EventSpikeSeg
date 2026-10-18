"""Bounded format checks for exact GDS transforms/PATH and MIM separation."""
from pathlib import Path
import hashlib,json,struct
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference,real8,string
from assemble_gf180_full25_physical_candidate_v5 import rect
from gf180_service_metal_graph_v3 import native_paint

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/results/service_metal_graph_v3'
def real(value):
    from assemble_gf180_full_capacity_storage_gds_v2 import gds_real
    return gds_real(value)

def path(style,points,start=0,end=0):
    data=rec(9,0)+rec(13,2,struct.pack('>h',42))+rec(14,2,bytes(2))+rec(15,3,struct.pack('>i',280))+rec(33,2,struct.pack('>h',style))
    if style==4:data+=rec(48,3,struct.pack('>i',start))+rec(49,3,struct.pack('>i',end))
    data+=rec(16,3,struct.pack('>'+str(len(points)*2)+'i',*(v for p in points for v in p)))+rec(17,0)
    return data

def main():
    assert not OUT.exists();OUT.mkdir()
    # GDS base16 real encoder, independent of the reader under test.
    def encoded(value):
        if value==0:return bytes(8)
        exponent=64;v=float(value)
        while v>=1:v/=16;exponent+=1
        while v<1/16:v*=16;exponent-=1
        return bytes([exponent])+int(round(v*2**56)).to_bytes(7,'big')
    expected=[(0,0,(1,0,0,1)),(0,90,(0,-1,1,0)),(0,180,(-1,0,0,-1)),(0,270,(0,1,-1,0)),
              (0x8000,0,(1,0,0,-1)),(0x8000,90,(0,1,1,0)),(0x8000,180,(-1,0,0,1)),(0x8000,270,(0,-1,-1,0))]
    leaf=begin('LEAF')+rect(42,(0,0,1000,280))+path(2,[(1000,140),(2000,140)])+rec(7,0)
    for flags,angle,matrix in expected:
        ref=rec(10,0)+string(18,'LEAF')+rec(26,1,struct.pack('>H',flags))+rec(28,5,encoded(angle))+rec(16,3,struct.pack('>ii',5000,3000))+rec(17,0)
        paint=native_paint({'LEAF':leaf,'TOP':begin('TOP')+ref+rec(7,0)},'TOP')
        a,b,c,d=matrix
        transform=lambda x,y:(a*x+b*y+5000,c*x+d*y+3000)
        assert paint.at(42,*transform(100,140))==paint.at(42,*transform(2000,140))
    for style,start,end,xmin,xmax in [(0,0,0,1000,2000),(2,0,0,860,2140),(4,60,100,940,2100)]:
        paint=native_paint({'TOP':begin('TOP')+path(style,[(1000,140),(2000,140)],start,end)+rec(7,0)},'TOP')
        assert min(b[0] for l,b in paint.shapes)==xmin and max(b[2] for l,b in paint.shapes)==xmax
    paint=native_paint({'TOP':begin('TOP')+path(2,[(0,0),(1000,0),(1000,1000)])+rec(7,0)},'TOP')
    assert paint.hits(42,(1130,-130,1130,-130)),'miter outer corner missing'
    mim=begin('MIM')+rect(75,(5000,5000,10000,10000))+rect(81,(5600,5600,6600,6600))+rect(46,(5600,5600,6600,6600))+rect(41,(6000,6000,6260,6260))+rec(7,0)
    paint=native_paint({'MIM':mim},'MIM')
    assert paint.at(75,6100,6100)==paint.at(81,6100,6100)
    assert paint.at(46,6100,6100)!=paint.at(75,6100,6100)
    rejected=False
    try:native_paint({'TOP':begin('TOP')+path(1,[(0,0),(1000,0)])+rec(7,0)},'TOP')
    except AssertionError:rejected=True
    assert rejected
    helper=ROOT/'scripts/gf180_service_metal_graph_v3.py'
    report=dict(checks_pass=True,orthogonal_rotation_reflection_cases=8,path_end_styles_checked=[0,2,4],
                path_miter_corner_checked=True,mim_via_does_not_short_metal4=True,round_path_rejected=True,
                scope='Small synthetic binary GDS checks of the metal readback helper, not circuit/analog validation.',
                sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),helper]})
    (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
