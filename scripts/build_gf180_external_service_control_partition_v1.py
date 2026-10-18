"""Physical characterization partition; remove only two categorical controller SREFs."""
from pathlib import Path
import copy, hashlib, json
from assemble_gf180_external_bank_service_full25_v5 import cells_read, elements
from assemble_gf180_full_capacity_storage_gds_v2 import begin, rec, records

R=Path(__file__).resolve().parents[1]
B=R/'artifacts/analog_asic'
SRC=B/'assembly/full25_external_bank_service_v5'
D=B/'assembly/external_service_control_partition_v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not D.exists();D.mkdir()
    mf=SRC/'physical_assembly.json';g=SRC/'eventspikeseg140k_external_bank_service_v5.gds'
    m=json.loads(mf.read_text());a=copy.deepcopy(m['actor_regions'][0]);root=a['gds_cell']
    prefix,cells=cells_read(g.read_bytes());removed={}
    for p in a['modules']:
        if p['instance'] in ['commit','event']:
            child=B/'layout'/p['cell']/(p['cell']+'.gds')
            removed['N'+sha(child)[:8]+'_'+hashlib.sha256(p['cell'].encode()).hexdigest()[:16]]=p
    assert len(removed)==2
    kept=[];dropped_refs=[];dropped_labels=[]
    for e in elements(cells[root]):
        child=next((v.rstrip(b'\0').decode() for t,dt,v,b in e if t==18),None)
        label=next((v.rstrip(b'\0').decode() for t,dt,v,b in e if t==25),None)
        if child in removed:
            assert e[0][0]==10;dropped_refs.append(child)
        elif label and label.startswith(('commit__','event__')):
            dropped_labels.append(label)
        else:kept.append(b''.join(b for t,dt,v,b in e))
    assert set(dropped_refs)==set(removed) and len(dropped_refs)==2
    cells[root]=begin(root)+b''.join(kept)+rec(7,0)
    needed=set()
    def visit(n):
        if n in needed:return
        needed.add(n)
        for t,dt,v,b in records(cells[n]):
            if t==18:visit(v.rstrip(b'\0').decode())
    visit(root)
    a['modules']=[p for p in a['modules'] if p['instance'] not in ['commit','event']]
    out=D/'analog_partition.gds';out.write_bytes(prefix+b''.join(cells[n] for n in sorted(needed))+rec(4,0))
    report={'actor_regions':[a], 'local_pin_nets':[n for n in m['local_pin_nets'] if n['actor']==a['actor']],
            'source_parent':mf.relative_to(R).as_posix(),'removed_controller_instances':list(removed.values()),
            'removed_private_controller_labels':dropped_labels,'native_analog_geometry_unchanged':True,
            'parent_route_element_bytes_unchanged':True,'expected_remaining_native_primitives':1832,
            'full_chip_complete':False,
            'scope':'Physical characterization partition only. Exact two categorical-controller references removed:374MOS bin and156MOS event. All other native children/transforms and parent route polygon/via bytes preserved. Controller-private TEXT removed; shared analog control interfaces remain external. Full25ASIC physical controller layouts retained in V5. Requires fresh native DRC,exact1832 graph and complete routingC; not a full-native-controller cycle claim.',
            'sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,g,out]}}
    (D/'physical_partition.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'partition':str(out),'removed_native_controller_primitives':530,'expected_native_analog_primitives':1832},indent=2))

if __name__=='__main__':main()
