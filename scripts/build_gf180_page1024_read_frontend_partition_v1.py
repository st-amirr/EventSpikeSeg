"""Cut verified storage children at RAW ports; preserve new page-selection/reader geometry."""
from pathlib import Path
import copy,hashlib,json
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,records
from assemble_gf180_full25_physical_candidate_v5 import pinlist,label
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
SRC=B/'assembly/shared_reader_page1024_v1';D=B/'assembly/page1024_read_frontend_partition_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not D.exists();D.mkdir();mf=SRC/'physical_partition.json';m=json.loads(mf.read_text());a=copy.deepcopy(m['actor_regions'][0]);root=a['gds_cell'];g=SRC/'shared_reader_page1024.gds';prefix,cells=cells_read(g.read_bytes());gone={};ports=[]
    for p in a['modules']:
        if p['instance'].startswith('P'):
            d=B/'layout'/p['cell'];cg=d/(p['cell']+'.gds');native='N'+sha(cg)[:8]+'_'+hashlib.sha256(p['cell'].encode()).hexdigest()[:16];gone[native]=True
            j=int(p['instance'][1:]);dx,dy=p['origin_dbu']
            for k in range(8):
                layer,x,y=pinlist(d,p['cell'])[f'READOUT{k}'];assert layer=='metal5';ports.append(label(f'RAW{j}_{k}',round(dx+x),round(dy+y)))
    assert len(gone)==1 and len(ports)==64
    body=[];removed_refs=0;removed_state_labels=0
    for e in elements(cells[root]):
        child=next((v.rstrip(b'\0').decode() for t,dt,v,b in e if t==18),None);text=next((v.rstrip(b'\0').decode() for t,dt,v,b in e if t==25),None)
        if child in gone:removed_refs+=1
        elif text and '__B' in text and '_STATE' in text:removed_state_labels+=1
        else:body.append(b''.join(b for t,dt,v,b in e))
    assert removed_refs==8 and removed_state_labels==1024
    cells[root]=begin(root)+b''.join(body+ports)+rec(7,0);needed=set()
    def visit(n):
        if n in needed:return
        needed.add(n)
        for t,dt,v,b in records(cells[n]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(root);out=D/'frontend_partition.gds';out.write_bytes(prefix+b''.join(cells[n] for n in sorted(needed))+rec(4,0))
    a['modules']=[p for p in a['modules'] if not p['instance'].startswith('P')]
    nets=[]
    for n in m['local_pin_nets']:
        nn=copy.deepcopy(n);nn['endpoint_pins']=[p for p in n['endpoint_pins'] if not p.split('.',1)[0].startswith('P')]
        if nn['endpoint_pins']:nets.append(nn)
    # RAW labels fix the external boundary for the remaining TG input pins.
    o={'actor_regions':[a],'local_pin_nets':nets,'native_mos_count':354,'native_mim_count':5,'expected_native_primitives':359,'source_parent':mf.relative_to(R).as_posix(),'physical_storage_removed_only_in_characterization':True,'parent_route_polygon_and_via_bytes_unchanged':True,'full_chip_complete':False,'scope':'New page decoder,64readTG,8enableinverters,columnmux andonefeedbackreader physical partition. Remove only8qualified808MOS128MIM storage/readout SREFs and1024STATE labels;allnewfrontend modules andparentroute bytes retained. Add64RAWport labels at actual formerbankoutput landings. Fresh parentDRC/exact359graph/nativeC required. External RAW fixtures from completed native128bank trace;does not prove connected1024storage transient,source impedance,initialization or5msservice. Full1024physicalparent remains preserved withDRC0/exact7847 and71802C,failed120s transient retained.','sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,g,out]}}
    (D/'physical_partition.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({'removed_storage_references':removed_refs,'native_frontend_primitives':359,'RAW_ports':64},indent=2))

if __name__=='__main__':main()
