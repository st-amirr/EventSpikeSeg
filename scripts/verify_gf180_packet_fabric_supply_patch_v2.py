"""OpenROAD Python: independently read back the incremental PG repair."""
from pathlib import Path
import hashlib,json
import odb

ROOT=Path('/workspace');BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_packet_fabric_v1/supply_repair_v2'

def main():
    out=OUT/'signal_preservation_readback.json';assert not out.exists()
    plan=json.loads((OUT/'repair_plan.json').read_text())
    db=odb.dbDatabase.create();odb.read_db(db,str(OUT/'repaired.odb'));b=db.getChip().getBlock()
    digest=hashlib.sha256();count=0
    for net in b.getNets():
        wire=net.getWire()
        if wire is None:continue
        itr=odb.dbWirePathItr();itr.begin(wire);path=odb.dbWirePath();shape=odb.dbWirePathShape()
        while itr.getNextPath(path):
            while itr.getNextShape(shape):
                s=shape.shape;box=(s.xMin(),s.yMin(),s.xMax(),s.yMax())
                digest.update(str((net.getName(),s.getType(),box)).encode());count+=1
    assert digest.hexdigest()==plan['signal_wire_shapes_fingerprint']
    assert count==plan['signal_wire_shapes']
    expected={name:[] for name in ['VDD','VSS']}
    for p in plan['plans']:expected[p['net']].append(tuple(p['route']))
    found={name:[] for name in expected}
    custom_vias=0
    for name in expected:
        for sw in b.findNet(name).getSWires():
            for box in sw.getWires():
                if box.isVia():
                    via=box.getBlockVia()
                    if via and via.getName()=='ESS_SUPPLY_PATCH_VIA45':custom_vias+=1
                elif box.getTechLayer().getName()=='Metal5':
                    rect=(box.xMin(),box.yMin(),box.xMax(),box.yMax())
                    if rect in expected[name]:found[name].append(rect)
        assert sorted(found[name])==sorted(expected[name]),name
    assert custom_vias==163
    result={'signal_wire_geometry_preserved':True,'signal_wire_shapes_checked':count,
            'new_pg_stubs_read_back':sum(len(v) for v in found.values()),'new_pg_vias_read_back':custom_vias,
            'full_chip_layout_complete':False,
            'scope':'Independent ODB readback proves all encoded signal wire shapes retain their original net/type/geometry fingerprint and all163 intended PG stubs/vias exist. Supply connectivity, spacing, IR/EM, timing and GDS are separate checks.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'repair_plan.json',OUT/'repaired.odb',Path(__file__)]}}
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='sha256'},indent=2))

if __name__=='__main__':main()
