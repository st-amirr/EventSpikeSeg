"""OpenROAD Python: extract real final I/O locations for full-chip binding."""
from pathlib import Path
import hashlib,json
import odb

ROOT=Path('/workspace');BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'assembly/full25_packet_fabric_v1'

def main():
    status=json.loads((OUT/'status.json').read_text())
    assert status['stage']=='physical_macro_completed', 'Collect the finished job first.'
    dest=OUT/'final_boundary_contract_v1.json';assert not dest.exists()
    source=BASE/'orfs/results/gf180'/status['design']/status['variant']/'6_final.odb'
    db=odb.dbDatabase.create();odb.read_db(db,str(source));block=db.getChip().getBlock();dbu=block.getDbUnitsPerMicron()
    macros=[]
    for inst in block.getInsts():
        if inst.getName()!='graph_macro' and not inst.getName().startswith('result_'):continue
        assert inst.getOrient()=='R0'
        supply={t.getMTerm().getName():t.getNet().getName() for t in inst.getITerms() if t.getMTerm().getName() in ['VDD','VSS']}
        assert supply=={'VDD':'VDD','VSS':'VSS'},inst.getName()
        macros.append({'instance':inst.getName(),'master':inst.getMaster().getName(),'origin_dbu':inst.getLocation(),'power_nets':supply})
    assert len(macros)==26
    ports={}
    for term in block.getBTerms():
        rectangles=[]
        for pin in term.getBPins():
            for g in pin.getBoxes():
                b=[g.xMin(),g.yMin(),g.xMax(),g.yMax()]
                rectangles.append({'layer':g.getTechLayer().getName(),'bbox_odb_dbu':b,
                                   'center_gds_nm':[round((b[0]+b[2])*500/dbu),round((b[1]+b[3])*500/dbu)]})
        assert rectangles,term.getName()
        ports[term.getName()]={'direction':term.getIoType(),'net':term.getNet().getName(),'rectangles':rectangles}
    spike=[]
    for i in range(25):
        name=f'result_spike_i[{i}]';assert name in ports
        assert ports[name]['direction']=='INPUT' and len(ports[name]['rectangles'])==1
        spike.append({'actor_index':i,'port':name,**ports[name]['rectangles'][0]})
    result={'actual_routed_boundary_extracted':True,'odb_units_per_um':dbu,'gds_units_per_um':1000,
            'macros':macros,'macro_count':26,'ports':ports,'spike_inputs':spike,
            'physical_supply_connectivity_scope':'Supply logical nets checked here; full physical connectivity is established by the final OpenROAD report.',
            'scope':'Actual final ODB I/O coordinates and macro placements. Supplies are logically associated. Provides destinations for the V15 analog spike-output routes; no full-chip analog binding or timing/accuracy acceptance.',
            'full_chip_layout_complete':False,'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,Path(__file__)]}}
    dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'macro_count':26,'ports':len(ports),'spike_inputs':25,'path':str(dest)},indent=2))

if __name__=='__main__':main()
