"""Check generated actor constants against every frozen membrane-bank identity."""
from pathlib import Path
import hashlib,json,re
from map_gf180_full_population_page_access_v1 import encode_bank,decode_bank

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_decision_control_v2'

def main():
    dest=OUT/'all_actor_address_map_v1.json';assert not dest.exists()
    status_path=OUT/'status.json';status=json.loads(status_path.read_text())
    mapping=BASE/'assembly/full_population_page_access_v1/address_assembly_specification_v1.json'
    frozen=json.loads(mapping.read_text());planes={p['actor']:p for p in frozen['planes'] if p['state_kind']=='membrane'}
    rtl=ROOT/'asic/analog/gf180_analog_full25_decision_control_v2.sv'
    constants=re.findall(r'\.CHANNELS\((\d+)\),\.HEIGHT\((\d+)\),\.WIDTH\((\d+)\),\.LOCAL_BANKS\(380\x27h([0-9a-f]+)\)\) actor_(\d+)',rtl.read_text())
    assert len(constants)==25;rows=[];allbanks=allstates=0
    for c,h,w,literal,index in constants:
        i=int(index);c,h,w=map(int,[c,h,w]);actor=status['actors'][i];plane=planes[actor['actor']]
        assert [c,h,w]==actor['shape_chw']==plane['shape_chw']
        packed=int(literal,16);holes=[(packed>>(20*k))&((1<<20)-1) for k in range(19)]
        assert holes==plane['excluded_linear_banks'] and holes[:3]==[0,1,2]
        ny,nx=(h+7)//8,(w+7)//8;states=local=rank_expected=0;digest=hashlib.sha256()
        for bank in range(c*ny*nx):
            ch,tile=divmod(bank,ny*nx);by,bx=divmod(tile,nx)
            active=min(8,h-8*by)*min(8,w-8*bx);assert active>0;states+=active
            if bank in holes:
                slot=holes.index(bank);kind=0 if slot==0 else 1 if slot<3 else 2
                assert kind in [0,1,2]
                local+=active;digest.update(f'L{bank}:{slot};'.encode())
            else:
                candidate=bank-sum(bank>=v for v in holes)
                assert candidate==encode_bank(bank,holes)==rank_expected
                assert decode_bank(candidate,holes)==bank
                assert candidate*8+7 < (1<<plane['categorical_row_bank_address_bits'])
                digest.update(f'F{bank}:{candidate};'.encode());rank_expected+=1
        assert states==c*h*w and local==plane['existing_service_active_states']==1216
        assert rank_expected==plane['remaining_banks']
        rows.append({'actor_index':i,'actor':actor['actor'],'valid_neurons':states,'banks_checked':c*ny*nx,'native_local_states':local,'forest_banks':rank_expected,'noncontiguous_exceptions':holes!=list(range(19)),'map_digest':digest.hexdigest()})
        allbanks+=c*ny*nx;allstates+=states
    assert allstates==30976000
    result={'all25_generated_address_constants_pass':True,'bank_identities_checked':allbanks,
            'valid_membrane_identities_covered':allstates,'actors_with_noncontiguous_local_exceptions':sum(r['noncontiguous_exceptions'] for r in rows),'actors':rows,
            'scope':'Generated physical-controller parameters checked against frozen original-float actor shapes and every membrane-bank rank/inverse. Valid edge sites counted exactly. Arithmetic identity audit, not full-population RTL/analog simulation or5ms acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [rtl,mapping,Path(__file__)]}}
    dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['actors','sha256']},indent=2))

if __name__=='__main__':main()
