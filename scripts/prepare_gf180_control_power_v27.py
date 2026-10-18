"""Read actual native M4/M5 supply grids and prepare six safe source escapes."""
from pathlib import Path
import json,time,collections
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_accumulation_fabric_ingress_v1 import sha
from prove_gf180_shared_page_parent_metal_v5 import Paint,VIA
import gf180_service_metal_graph_v3 as graph
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/control_power_inputs_v27'

def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    ip=BASE/'assembly/native_address_route_inputs_v1/routing_inputs.json';inp=json.loads(ip.read_text())
    pp=BASE/'assembly/accumulation_fabric_ingress_v1/route_plan.json';pair=json.loads(pp.read_text())
    vp=BASE/'assembly/full25_accumulation_architecture_v17/route_plan.json';v17=json.loads(vp.read_text())
    ox,oy=v17['pair_origin_dbu']
    origins={side:[xy[0]+ox,xy[1]+oy] for side,xy in pair['origins_dbu'].items()}
    origins['DISPATCH']=inp['dispatcher_origin_top_dbu']
    grids=[];sources=[];hashes={};summary=[]
    class UpperPaint(Paint):
        def add(self,l,b):return super().add(l,b) if l in (46,81,41) else -1
        def vias(self,start=0):
            for i in range(start,len(self.shapes)):
                l,b=self.shapes[i]
                if l==41:
                    for metal in (46,81):
                        hits=self.hits(metal,b);assert hits,('unlanded native VIA4',b,metal)
                        for j in hits:self.join(i,j)
    for side,folder in [('FABRIC','full25_packet_fabric_v1'),('INGRESS','full25_actor_ingress_v2'),('DISPATCH','full25_accumulation_dispatch_v1')]:
        mp=BASE/f'assembly/{folder}/physical_macro.json';m=json.loads(mp.read_text())
        ng=next(ROOT/p for p in m['sha256'] if p.endswith('.gds'))
        assert sha(ng)==m['sha256'][ng.relative_to(ROOT).as_posix()]
        _,cells=cells_read(ng.read_bytes());previous=graph.Paint
        try:graph.Paint=UpperPaint;paint=graph.native_paint(cells,m['design'])
        finally:graph.Paint=previous
        owners=collections.defaultdict(set);powerroots={}
        for name,pin in m['ports'].items():
            for r in pin['rectangles']:
                layer={'Metal3':42,'Metal4':46,'Metal5':81}[r['layer']]
                if layer not in (46,81):continue
                x,y=[round(v*1000) for v in r['center_um']]
                if paint.hits(layer,(x,y,x,y)):owners[paint.at(layer,x,y)].add(name)
        for net in ('VDD','VSS'):
            rr=set()
            for r in m['ports'][net]['rectangles']:
                assert r['layer']=='Metal5';x,y=[round(v*1000) for v in r['center_um']]
                rr.add(paint.at(81,x,y))
            assert len(rr)==1,(side,net,'disconnected upper supply grid',len(rr))
            root=next(iter(rr));assert owners[root]=={net},(side,net,owners[root]);powerroots[net]=root
            r=min(m['ports'][net]['rectangles'],key=lambda r:(r['rect_um'][0],r['rect_um'][1]))
            x1,y1,x2,y2=[round(v*1000) for v in r['rect_um']];x=x1+100;y=(y1+y2)//2
            assert paint.at(81,x,y)==root
            gx,gy=origins[side];w,h=[round(v*1000) for v in m['size_um']]
            sources.append(dict(instance=side,net=net,layer=81,xy_top_dbu=[x+gx,y+gy],macro_bbox_dbu=[gx,gy,gx+w,gy+h],native_power_rectangle_dbu=[x1+gx,y1+gy,x2+gx,y2+gy]))
        assert powerroots['VDD']!=powerroots['VSS']
        gx,gy=origins[side]
        for i,(l,b) in enumerate(paint.shapes):
            root=paint.root(i);owner=next((net for net,r in powerroots.items() if r==root),side+'__unbound_component_'+str(root))
            grids.append([l,[b[0]+gx,b[1]+gy,b[2]+gx,b[3]+gy],owner])
        summary.append(dict(instance=side,actual_upper_shapes=len(paint.shapes),vdd_m5_port_rectangles=len(m['ports']['VDD']['rectangles']),vss_m5_port_rectangles=len(m['ports']['VSS']['rectangles']),each_upper_power_grid_connected=True))
        hashes.update({p.relative_to(ROOT).as_posix():sha(p) for p in (mp,ng)})
        print(json.dumps(summary[-1]),flush=True)
    geometry=OUT/'native_upper_geometry.json';geometry.write_text(json.dumps(grids)+'\n')
    result=dict(native_upper_power_grids_verified=True,sources=sources,macros=summary,elapsed_seconds=time.monotonic()-started,scope='Actual native M4/M5/VIA4 connectivity of all power-port rectangles, separate VDD/VSS components and no signal-port aliases. Lower native PG/device connectivity retains existing ORFS evidence; global wiring still absent.',sha256={**hashes,**{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ip,pp,vp,geometry]}})
    (OUT/'power_inputs.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
