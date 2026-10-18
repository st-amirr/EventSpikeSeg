"""Join native current-summing ROOT nodes of two64-channel RMS halves in actual GDS."""
from pathlib import Path
import copy,hashlib,json,struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements,via
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec
from assemble_gf180_full25_physical_candidate_v5 import rect,label,pinlist
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
SRC=B/'assembly/full25_external_bank_service_v5';D=B/'assembly/full25_shared_ROOT128_v6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not D.exists();D.mkdir()
    proof=B/'verification/shared_ROOT128_composition_v2/composition_review.json'
    assert json.loads(proof.read_text())['two64_shared_ROOT_equals_native128_primitive_graph']
    mf=SRC/'physical_assembly.json';src=SRC/'eventspikeseg140k_external_bank_service_v5.gds'
    m=json.loads(mf.read_text());prefix,cells=cells_read(src.read_bytes());joins=[]
    for a in m['actor_regions']:
        halves=[p for p in a['modules'] if p['instance'].startswith('energy64_')]
        if len(halves)<2:continue
        assert len(halves)==2 and {p['instance'] for p in halves}=={'energy64_0','energy64_1'}
        root=a['gds_cell'];body=[];removed=[]
        for e in elements(cells[root]):
            text=next((v.rstrip(b'\0').decode() for t,dt,v,b in e if t==25),None)
            if text in ['energy64_0__ROOT','energy64_1__ROOT']:removed.append(text)
            else:body.append(b''.join(b for t,dt,v,b in e))
        assert len(removed)==2
        ex=-a['external_service_spine_gutter_dbu']+5000;ys=[];ends=[]
        for p in halves:
            folder=B/'layout'/p['cell'];q=json.loads((folder/'qualification.json').read_text())
            g=folder/(p['cell']+'.gds');assert sha(g)==q['sha256'][g.name]
            layer,x,y=pinlist(folder,p['cell'])['ROOT'];assert layer=='metal5'
            dx,dy=p['origin_dbu'];px=round(dx+x);py=round(dy+y)
            body +=[rect(81,(min(ex,px)-220,py-220,max(ex,px)+220,py+220)),via(81,46,41,ex,py)]
            ys.append(py);ends.append({'instance':p['instance'],'native_ROOT_pad_dbu':[px,py]})
        body +=[rect(46,(ex-200,min(ys)-220,ex+200,max(ys)+220)),label('RMS128_ROOT',ex,min(ys))]
        cells[root]=begin(root)+b''.join(body)+rec(7,0)
        entry={'actor':a['actor'],'net':'RMS128_ROOT','endpoint_pins':['energy64_0.ROOT','energy64_1.ROOT'],'externally_supplied_or_unconsumed':True,'native_current_sum_root_feedback_join':True}
        assert not any(n['actor']==a['actor'] and n['net']=='RMS128_ROOT' for n in m['local_pin_nets'])
        m['local_pin_nets'].append(entry);a['native128_ROOT_current_sum_physically_joined']=True
        a['native128_ROOT_current_sum_parent_qualified']=False
        joins.append(dict(actor=a['actor'],root_cell=root,escape_x_dbu=ex,endpoints=ends))
    assert len(joins)==9
    old=m['top_cell'];new='ESS140K_SHARED_ROOT128_V6';oldbody=b''.join(b for e in elements(cells[old]) for t,dt,v,b in e)
    cells[new]=begin(new)+oldbody+rec(7,0);del cells[old];m['top_cell']=new
    dest=D/'eventspikeseg140k_shared_ROOT128_v6.gds';dest.write_bytes(prefix+b''.join(cells.values())+rec(4,0))
    m.update(source_physical_candidate=mf.relative_to(R).as_posix(),full_chip_layout_complete=False,
             full_chip_functional_layout_complete=False,native128_ROOT_joins=joins,
             shared_ROOT128_composition_proof=proof.relative_to(R).as_posix(),
             root_join_parent_DRC_and_connectivity_complete=False)
    m['scope']='V6 adds one physical shared current-summing ROOT wire between existing64channel RMS halves in each of9actual128channel actors. Exact896primitive composition matches existing native128 reducer. Native macro transforms,allstate plane and parameter references unchanged;no added active circuit. New parent route DRС/connectivity and128nominal remain unqualified;globalbankservice/operator/parameter bindings and fullASIC incomplete.'
    m['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),proof,mf,src,dest]}
    (D/'physical_assembly.json').write_text(json.dumps(m,indent=2)+'\n')
    print(json.dumps({'gds':str(dest),'actual128_actor_ROOT_joins':len(joins),'added_native_devices':0,'full_chip_complete':False},indent=2))

if __name__=='__main__':main()
