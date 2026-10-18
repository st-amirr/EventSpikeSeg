"""Canonical full-population analog address mapping and exhaustive bank bijection audit.

This emits the address specification for physical tree assembly, not a layout pass.
"""
from pathlib import Path
import bisect,hashlib,json,math,struct
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';S=B/'assembly/full25_shared_page1024_v8';D=B/'assembly/full_population_page_access_v1'
def encode_bank(linear,holes):
    assert linear not in holes
    return linear-bisect.bisect_right(holes,linear)
def decode_bank(rank,holes):
    linear=rank
    while True:
        candidate=rank+bisect.bisect_right(holes,linear)
        if candidate==linear:return linear
        linear=candidate
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not D.exists();D.mkdir();mf=S/'physical_assembly.json';m=json.loads(mf.read_text());identity=S/'independent_bank_identity_readback_v1.json';assert json.loads(identity.read_text())['all_emitted_bank_identities_bijective'];selector=B/'layout/gf180_shared_page_tree_selector8_v2/qualification.json';sq=json.loads(selector.read_text());assert sq['lvs_unique'];sim=B/'results/gf180_shared_page_tree_selector8_v2_native_A_B_A.json';sr=json.loads(sim.read_text());assert sr['module_simulation_completed'] and sr['hierarchical_page_selection_observed'];planes=[];raw=active=service=pages=nodes=0;digest=hashlib.sha256()
    for p in m['state_planes']:
        c,h,w=p['shape_chw'];ny,nx=p['bank_grid_yx'];holes=[];exceptions=[]
        if p['state_kind']=='membrane':
            exceptions=[{'channel':0,'bank_y':0,'bank_x':0,'native_instance':'compute','state_port':'STATE[row][column]'}]+p['external_compute_service_bank_exceptions']
            holes=sorted(e['channel']*ny*nx+e['bank_y']*nx+e['bank_x'] for e in exceptions);assert len(holes)==19 and len(set(holes))==19
        n=c*ny*nx-len(holes);assert n==p['locally_decoded_bank_equivalents'];npages=math.ceil(n/16);level=math.ceil(math.log(npages,8));nselectors=sum(math.ceil(npages/(8**k)) for k in range(1,level+1));seen=0;pa=0;ps=0
        for linear in range(c*ny*nx):
            channel,site=divmod(linear,ny*nx);by,bx=divmod(site,nx);valid=min(8,h-8*by)*min(8,w-8*bx);assert valid>0
            if linear in holes:ps+=valid;continue
            rank=encode_bank(linear,holes);assert rank==seen and decode_bank(rank,holes)==linear;leaf,bank=divmod(rank,16);assert leaf<npages;digits=[(leaf//(8**k))%8 for k in range(level)];assert sum(v*8**k for k,v in enumerate(digits))==leaf;pair,bankselect=divmod(bank,2);assert 0<=pair<8 and bankselect in [0,1]
            digest.update(struct.pack('>5I',p['plane_index'],linear,rank,leaf,bank));pa+=valid;seen+=1
        assert seen==n and pa+ps==p['active_state_count'];raw+=n;active+=pa;service+=ps;pages+=npages;nodes+=nselectors
        planes.append({'plane_index':p['plane_index'],'actor':p['actor'],'state_kind':p['state_kind'],'shape_chw':[c,h,w],'bank_grid_yx':[ny,nx],'bank_linear_expression':'channel*(ny*nx)+bank_y*nx+bank_x','excluded_linear_banks':holes,'existing_service_exceptions':exceptions,'remaining_banks':n,'remaining_active_states':pa,'existing_service_active_states':ps,'native1024_leaf_pages':npages,'additional_inactive_bank_slots':npages*16-n,'higher_selector_levels':level,'higher_selector_instances':nselectors,'categorical_row_bank_address_bits':7+3*level,'column_select':'SEL0..7 onehot selects x%8;row address=y%8','bank_rank_expression':'linear_bank - count(excluded_linear_banks <= linear_bank),valid only outside exceptions','global_leaf_page_expression':'bank_rank//16','leaf_pair_expression':'(bank_rank%16)//2','leaf_BANK_SELECT_expression':'bank_rank%2','address_bits':'ADDR0..2=row;ADDR3=bankselect;ADDR4..6=leafpair;ADDR[7+3*k:9+3*k]=base8 page digit k;SEL[column]=1','uniform_depth_required':True,'unused_child_policy':'No storage assigned. MissingREAD inputs tieVCM;native address decoder still tests all level bits,preventing tail aliases.','bank_address_bijection_verified':True})
    assert raw==865605 and active+service==54630400 and service==30400 and pages==54105
    o={'global_bank_address_mapping_verified':True,'physical_global_service_tree_built':False,'global_bank_compute_binding_complete':False,'full_population_5ms_accepted':False,'full_chip_complete':False,'checkpoint_sha256':m['checkpoint_sha256'],'analog_numeric_state':'NativeMIM charge;no ADC/digital numericalstate','original_active_analog_states':active+service,'existing_routed_service_states':service,'remaining_active_states':active,'remaining_bank_equivalents':raw,'native1024_leaf_pages_required':pages,'higher_selector_instances_required':nodes,'extra_inactive_bank_slots':pages*16-raw,'total_physical_bank_capacity_after_replacement':pages*16+475,'selector_native_MOS':230,'proposed_write_DATA_isolation_per_selector':'64nativeTG+8nativeinverters =144MOS;notyet assembled/qualified asparent','planned_read_write_node_MOS':374,'scope':'Exhaustive865605remaining-bank rank/inverse/base8 path audit and active-site count,using independently verifiedV8identity exceptions. Logicaladdress specification forphysicaltreeassembly;not evidence thattreewires orglobalcompute service exist. SamecolumnDATA8write bus requires per-childTG isolation;READselection uses qualified230MOSstage. Full5ms,fanout,parameter/scheduler/AGE/AMP/classcompute bindings remainopen.','planes':planes,'bank_mapping_SHA256':digest.hexdigest(),'sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,identity,selector,sim]}}
    (D/'address_assembly_specification_v1.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k not in ['planes','sha256','scope']},indent=2))
if __name__=='__main__':main()
