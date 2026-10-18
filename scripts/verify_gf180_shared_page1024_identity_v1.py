"""Read emitted arrays independently and prove exact logical-bank set preservation."""
from pathlib import Path
import hashlib,json,struct
from verify_gf180_shared_ROOT128_identity_v1 import read,sha
from assemble_gf180_full_capacity_storage_gds_v2 import records,string
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_shared_page1024_v7'
def main():
    mf=D/'physical_assembly.json';g=D/'eventspikeseg140k_shared_page1024_v7.gds';m=json.loads(mf.read_text());cells,refs=read(g);out=D/'independent_bank_identity_readback_v1.json';assert not out.exists()
    quals={}
    for c in ['gf180_independent_bank_pair_v4','gf180_compact_decoded_bank8x8_v1']:
        gg=B/'layout'/c/(c+'.gds');q=json.loads((B/'layout'/c/'qualification.json').read_text());q['name']='N'+sha(gg)[:8]+'_'+hashlib.sha256(c.encode()).hexdigest()[:16];quals[c]=q
    pair,single=quals.values();pageg=B/'assembly/shared_reader_page1024_v1/shared_reader_page1024.gds';source,_=read(pageg);tag=sha(pageg)[:8];names={n:'N'+tag+'_'+hashlib.sha256(n.encode()).hexdigest()[:16] for n in source}
    for name,blob in source.items():
        expected=b''.join(string(t,names[v.rstrip(b'\0').decode()]) if t in [6,18] else b for t,d,v,b in records(blob));assert cells[names[name]]==expected
    # Verify page state names, count, and fixed high/low categorical addressing from
    # qualified fullpage graph, not merely its capacity counter.
    nativepage=names['SHARED_READER_PAGE1024_V1'];pageproof=B/'assembly/shared_reader_page1024_v1/verification/native_parent_v1/parent_exact_connectivity_attempt.json';assert json.loads(pageproof.read_text())['native_primitives']==7847 and json.loads(pageproof.read_text())['independent_connectivity_accepted']
    rows=[];total=0;movemap={r['actor']:r for r in m['shared1024page_identity_bindings']}
    for p in m['state_planes']:
        c,h,w=p['shape_chw'];ny,nx=p['bank_grid_yx'];cw,ch=p['channel_pitch_dbu'];pp,yp=p['local_pair_pitch_dbu'];cols=p['channel_grid_cols'];seen=set()
        for a in refs[p['candidate_cell']]:
            isp=a['child']==pair['name'];q=pair if isp else single;assert a['child']==q['name'];bb=[round(v*1000) for v in q['bbox_um']];xy=a['xy'];dx=(xy[2]-xy[0])//a['nx'] if len(xy)>2 else 0;dy=(xy[5]-xy[1])//a['ny'] if len(xy)>2 else 0
            for ay in range(a['ny']):
                for ax in range(a['nx']):
                    left=xy[0]+ax*dx+bb[0];bottom=xy[1]+ay*dy+bb[1];cc=left//cw;cr=bottom//ch;channel=cr*cols+cc;assert channel<c;lx=left-cc*cw;ly=bottom-cr*ch;assert ly%yp==0;by=ly//yp;assert 0<=by<ny and lx%pp==0;pi=lx//pp;first=int(p['state_kind']=='membrane' and channel==0 and by==0)+2*pi
                    for off in range(2 if isp else 1):
                        key=(channel,by,first+off);assert key not in seen and 0<=first+off<nx;seen.add(key)
        holes=set()
        if p['state_kind']=='membrane':
            holes={(0,0,i) for i in range(3)};move=movemap[p['actor']];assert len(move['pairs'])==8
            for j,t in enumerate(move['pairs']):
                assert t['page_pair']==j
                for bx in t['bank_x_pair']:
                    key=(t['channel'],t['bank_y'],bx);assert key not in holes;holes.add(key)
            a=next(a for a in m['actor_regions'] if a['actor']==p['actor']);ps=[r for r in refs[a['gds_cell']] if r['child']==nativepage];assert len(ps)==1 and ps[0]['nx']==ps[0]['ny']==1
            assert ps[0]['xy']==tuple(next(k['origin_dbu'] for k in a['modules'] if k['instance']=='page_service'))
            assert len(holes)==19
        expected={(ci,by,bx) for ci in range(c) for by in range(ny) for bx in range(nx)};assert seen.isdisjoint(holes) and seen|holes==expected
        total+=len(seen);rows.append({'plane':p['plane_index'],'actor':p['actor'],'raw_bank_identities':len(seen),'serviced_bank_exceptions':len(holes),'identity_bijection':True})
    assert total==865605 and sum(p['active_state_count'] for p in m['state_planes'])==54630400
    o={'all_emitted_bank_identities_bijective':True,'raw_plane_bank_equivalents':total,'original_compute_banks':25,'original128_service_banks':50,'new1024page_banks':400,'total_bank_equivalents':866080,'active_original_analog_states':54630400,'native_page_hierarchy_byte_verified':True,'new_parent_wiring_qualified':False,'full_chip_complete':False,'scope':'Independent binary GDS array/SREF coordinates decoded back to exact logicalbank sets.25qualified native1024page hierarchies byteverified after namespace mapping. Each assigned pagebank fills a distinct emitted rawplane hole;original64+128actorbank exceptions preserved. Does not prove newparent net connections,address scheduler,accuracy or5ms.','planes':rows,'sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,g,pageg,pageproof]}}
    out.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k not in ['planes','sha256']},indent=2))
if __name__=='__main__':main()
