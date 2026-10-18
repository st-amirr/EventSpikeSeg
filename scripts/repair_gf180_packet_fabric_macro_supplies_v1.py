"""Run under OpenROAD Python. Add checked lateral macro supply connections.

Keep the routed signal database unchanged. Trim only foreign-net parent M5
power metal/vias where needed to give the new same-layer supply stub clearance.
The resulting database still requires power connectivity and geometry checks.
"""
from pathlib import Path
import collections,hashlib,json
import odb

ROOT=Path('/workspace')
BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/full25_packet_fabric_v1/supply_repair_v2'
SOURCE=BASE/'orfs/results/gf180/gf180_analog_full25_packet_fabric_v1/packet_fabric_repair1/5_route.odb'

def bbox(o):return (o.xMin(),o.yMin(),o.xMax(),o.yMax())
def overlap(a,b):return not(a[2]<=b[0] or a[0]>=b[2] or a[3]<=b[1] or a[1]>=b[3])
def expand(a,m):return (a[0]-m,a[1]-m,a[2]+m,a[3]+m)
def subtract(a,b):
    if not overlap(a,b):return [a]
    x1,y1,x2,y2=a;u1,v1,u2,v2=b;u1=max(x1,u1);u2=min(x2,u2);v1=max(y1,v1);v2=min(y2,v2)
    return [q for q in [(x1,y1,u1,y2),(u2,y1,x2,y2),(u1,y1,u2,v1),(u1,v2,u2,y2)] if q[2]-q[0]>=880 and q[3]-q[1]>=880]

def main():
    assert not (OUT/'repair_plan.json').exists()
    OUT.mkdir(parents=True,exist_ok=True)
    db=odb.dbDatabase.create();odb.read_db(db,str(SOURCE));block=db.getChip().getBlock();tech=db.getTech()
    assert block.getDbUnitsPerMicron()==2000
    pg={};via_cache={};pgvias=[]
    for name in ['VDD','VSS']:
        net=block.findNet(name);pg[name]=[]
        for sw in net.getSWires():
            for box in sw.getWires():
                if box.isVia():
                    via=box.getBlockVia() or box.getTechVia();key=via.getName()
                    if key not in via_cache:via_cache[key]={b.getTechLayer().getName() for b in via.getBoxes()}
                    if 'Metal5' in via_cache[key]:pgvias.append((name,bbox(box),box))
                elif box.getTechLayer().getName() in ['Metal4','Metal5']:
                    pg[name].append((box.getTechLayer().getName(),bbox(box),box,sw))
    signals=collections.defaultdict(list);signal_hash=hashlib.sha256();wire_count=0
    for net in block.getNets():
        wire=net.getWire()
        if wire is None:continue
        itr=odb.dbWirePathItr();itr.begin(wire);path=odb.dbWirePath();shape=odb.dbWirePathShape()
        while itr.getNextPath(path):
            while itr.getNextShape(shape):
                s=shape.shape;box=bbox(s);signal_hash.update(str((net.getName(),s.getType(),box)).encode());wire_count+=1
                if s.isVia():
                    via=s.getVia() or s.getTechVia();key=via.getName()
                    if key not in via_cache:via_cache[key]={b.getTechLayer().getName() for b in via.getBoxes()}
                    for layer in via_cache[key]&{'Metal4','Metal5'}:signals[layer].append((box,net.getName()))
                elif s.getTechLayer().getName() in ['Metal4','Metal5']:
                    signals[s.getTechLayer().getName()].append((box,net.getName()))
    macros=[];pins=[]
    for inst in block.getInsts():
        if inst.getName()!='graph_macro' and not inst.getName().startswith('result_'):continue
        assert inst.getOrient()=='R0'
        ox,oy=inst.getLocation();ib=bbox(inst.getBBox());macros.append((inst.getName(),ib))
        for term in inst.getITerms():
            name=term.getMTerm().getName()
            if name not in ['VDD','VSS']:continue
            for mp in term.getMTerm().getMPins():
                for g in mp.getGeometry():
                    assert g.getTechLayer().getName()=='Metal5'
                    b=bbox(g);pins.append((inst.getName(),name,(b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy),ib))
    assert len(macros)==26
    plans=[];failures=[]
    for inst,name,pin,ib in pins:
        foreign='VSS' if name=='VDD' else 'VDD';candidates=[]
        rails=[b for layer,b,_,_ in pg[name] if layer=='Metal4' and (b[2]<=ib[0]-1600 or b[0]>=ib[2]+1600)]
        for shift in [0,1120,-1120,2240,-2240,3360,-3360]:
            y=(pin[1]+pin[3])//2+shift
            if y-600<pin[1] or y+600>pin[3]:continue
            eligible=[b for b in rails if b[1]+600<=y<=b[3]-600]
            eligible.sort(key=lambda b:min(abs((b[0]+b[2])//2-pin[0]),abs((b[0]+b[2])//2-pin[2])))
            for rail in eligible[:12]:
                x=(rail[0]+rail[2])//2
                sx=pin[0]+600 if x<ib[0] else pin[2]-600
                route=(min(x,sx)-600,y-600,max(x,sx)+600,y+600);via=(x-600,y-600,x+600,y+600)
                if any(n!=inst and overlap(route,b) for n,b in macros):continue
                if any(overlap(expand(route,1000),b) for b,n in signals['Metal5']):continue
                if any(overlap(expand(via,1000),b) for b,n in signals['Metal4']):continue
                if any(layer=='Metal4' and overlap(expand(via,1000),b) for layer,b,_,_ in pg[foreign]):continue
                if any(other['net']!=name and (overlap(expand(route,1200),other['route']) or overlap(expand(via,1200),other['via'])) for other in plans):continue
                # Cut only parent PG on the opposite supply, never routed signals.
                clearance=expand(route,2000)
                cuts=[b for layer,b,_,_ in pg[foreign] if layer=='Metal5' and overlap(clearance,b)]
                candidates.append((len(cuts)*100000000+abs(x-sx),x,y,route,via,cuts))
        if not candidates:
            failures.append({'instance':inst,'net':name,'pin':pin});continue
        _,x,y,route,via,cuts=min(candidates)
        plans.append({'instance':inst,'net':name,'pin':pin,'route':route,'via':via,'via_center':[x,y],'foreign_pg_m5_intersections':len(cuts)})
    report={'planned_pins':len(plans),'total_macro_pg_shapes':len(pins),'failed_pins':failures,
            'signal_wire_shapes_fingerprint':signal_hash.hexdigest(),'signal_wire_shapes':wire_count,
            'signal_clearance_dbu':1000,'foreign_pg_clearance_dbu':2000,
            'plans':plans,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'scope':'Explicit lateral M5 PG stubs to existing same-net M4 rails, with M4/M5 signal clearance and opposite-supply contact rejection. Planned foreign parent M5/via trimming only. Requires final power and geometry checks.'}
    (OUT/'repair_plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'planned_pins':len(plans),'total_pg_shapes':len(pins),'failed_pins':failures[:8]},indent=2),flush=True)
    assert not failures, 'No database change made; inspect unrouteable pins.'
    # Construct a one-cut native-size via; all dimensions are database units.
    v45=odb.dbVia_create(block,'ESS_SUPPLY_PATCH_VIA45')
    for layer,b in [('Metal4',(-600,-600,600,600)),('Metal5',(-600,-600,600,600)),('Via4',(-280,-280,280,280))]:
        odb.dbBox_create(v45,tech.findLayer(layer),*b)
    trimmed=removed_vias=0
    for name in ['VDD','VSS']:
        cuts=[expand(p['route'],2000) for p in plans if p['net']!=name]
        for layer,b,obj,sw in pg[name]:
            if layer!='Metal5':continue
            relevant=[c for c in cuts if overlap(b,c)]
            if not relevant:continue
            fragments=[b]
            for cut in relevant:fragments=[part for f in fragments for part in subtract(f,cut)]
            odb.dbSBox_destroy(obj)
            for f in fragments:odb.dbSBox_create(sw,tech.findLayer('Metal5'),*f,'STRIPE')
            trimmed+=1
        for owner,b,obj in pgvias:
            if owner==name and any(overlap(b,c) for c in cuts):odb.dbSBox_destroy(obj);removed_vias+=1
    swires={n:odb.dbSWire_create(block.findNet(n),'ROUTED') for n in ['VDD','VSS']}
    for p in plans:
        sw=swires[p['net']];odb.dbSBox_create(sw,tech.findLayer('Metal5'),*p['route'],'STRIPE')
        odb.dbSBox_create(sw,v45,*p['via_center'],'STRIPE')
    repaired=OUT/'repaired.odb';odb.write_db(db,str(repaired))
    report.update(database_written=True,trimmed_foreign_pg_m5_shapes=trimmed,removed_foreign_pg_via45=removed_vias,
                  repaired_database_sha256=hashlib.sha256(repaired.read_bytes()).hexdigest(),power_connectivity_accepted=False)
    (OUT/'repair_plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'database_written':str(repaired),'trimmed_pg_shapes':trimmed,'removed_pg_vias':removed_vias},indent=2))

if __name__=='__main__':main()
