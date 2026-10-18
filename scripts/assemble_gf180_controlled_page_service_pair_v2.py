"""Connect both native analog page services to the routed access interlocks."""
from pathlib import Path
import hashlib,json
from assemble_gf180_external_bank_service_full25_v5 import cells_read
from assemble_gf180_full_capacity_storage_gds_v2 import begin,rec,reference
from assemble_gf180_full25_physical_candidate_v5 import rect,label

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'assembly/controlled_page_service_pair_v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wire(layer,a,b):
    assert a[0]==b[0] or a[1]==b[1]
    h=140 if layer==42 else 220
    return layer,(min(a[0],b[0])-h,min(a[1],b[1])-h,max(a[0],b[0])+h,max(a[1],b[1])+h)
def via(low,high,cut,p):
    x,y=p;return [(low,(x-300,y-300,x+300,y+300)),(high,(x-300,y-300,x+300,y+300)),(cut,(x-130,y-130,x+130,y+130))]

def main():
    assert not OUT.exists();OUT.mkdir()
    analog_dir=BASE/'assembly/page_service_control_breakouts_v2'
    ampath=analog_dir/'physical_breakouts.json';am=json.loads(ampath.read_text())
    proof=analog_dir/'independent_readback_v1.json';assert json.loads(proof.read_text())['readback_pass']
    analog=ROOT/am['gds'];prefix,cells=cells_read(analog.read_bytes())
    cd=BASE/'assembly/page_access_pair_control_v2';status_path=cd/'status.json';status=json.loads(status_path.read_text())
    assert status['stage']=='physical_macro_completed'
    contract=cd/'physical_macro.json';cm=json.loads(contract.read_text())
    digital=BASE/'orfs/results/gf180'/status['design']/status['variant']/'6_final.gds'
    assert cm['sha256'][digital.relative_to(ROOT).as_posix()]==sha(digital)
    _,dcells=cells_read(digital.read_bytes());assert set(cells).isdisjoint(dcells)
    bb=am['original_service_bbox_dbu']
    allboxes=[bb]+[s[1] for e in am['escapes'] for s in e['shapes']]
    abb=[min(b[0] for b in allboxes),min(b[1] for b in allboxes),max(b[2] for b in allboxes),max(b[3] for b in allboxes)]
    width,height=abb[2]-abb[0],abb[3]-abb[1]
    origins=[[-abb[0],-abb[1]],[width+1000000-abb[0],-abb[1]]]
    bounds=[(0,0,width,height),(width+1000000,0,2*width+1000000,height)]
    control_origin=(2*width+2000000,0)
    cw,ch=[round(v*1000) for v in cm['size_um']]
    bounds.append((*control_origin,control_origin[0]+cw,ch))
    escaped={e['port']:e['escaped'] for e in am['escapes']}
    nets={};records=[]
    def native(lane,port):
        l,x,y=escaped[port];ox,oy=origins[lane]
        return dict(block=lane,port='CONTROL__'+port,layer=l,xy=[x+ox,y+oy],original_xy=[x,y])
    def controller(port):
        r=cm['ports'][port]['rectangles'][0];l={'Metal3':42,'Metal4':46,'Metal5':81}[r['layer']]
        x,y=[round(v*1000) for v in r['center_um']]
        return dict(block=2,port=port,layer=l,xy=[x+control_origin[0],y],original_xy=[x,y])
    def connect(name,*nodes):
        nets.setdefault(name,[]).extend(nodes)
    bindings=[]
    for lane in range(2):
        mapping=[]
        for k in range(7):mapping.append((f'page_address_o[{lane*7+k}]',f'PAGE1024__LOW{k}' if k<4 else f'PAGE1024__HIGH{k-4}'))
        for k in range(8):mapping.append((f'page_select_o[{lane*8+k}]',f'PAGE1024__SEL{k}'))
        for port,pin in [('page_read_o','PAGE1024__READ_CMD'),('page_read_enable_o','PAGE1024__READ_ENABLE'),
                         ('page_write_o','PAGE1024__WRITE_CMD'),('page_restore_o','PAGE_RESTORE'),('page_restoreb_o','PAGE_RESTOREB'),
                         ('compute_init_o','compute__INIT'),('compute_initb_o','compute__INITB'),
                         ('compute_write_o','compute__C_WRITE'),('compute_writeb_o','compute__C_WRITEB'),
                         ('external_initialize_o','EXTERNAL_INITIALIZE'),('external_initializeb_o','EXTERNAL_INITIALIZEB')]:
            mapping.append((f'{port}[{lane}]',pin))
        for k in range(8):
            mapping.extend([(f'capture_o[{lane*8+k}]',f'compute__CAP{k}'),(f'captureb_o[{lane*8+k}]',f'compute__CAPB{k}')])
        assert len(mapping)==42
        for digital_port,native_port in mapping:
            name=f'L{lane}__{native_port}';connect(name,controller(digital_port),native(lane,native_port))
            bindings.append(dict(lane=lane,controller_port=digital_port,native_port=native_port,net=name))
        lows=['compute__WRITE_CMD','compute__READ_CMD','compute__READ_ENABLE','compute__RESTORE','EXTERNAL_RESTORE',
              'bank_service__WRITE_CMD','bank_service__READ_CMD','bank_service__READ_ENABLE','bank_service__BANK_SELECT']
        lows += [f'compute__SEL{k}' for k in range(8)]+[f'bank_service__SEL{k}' for k in range(8)]
        lows += [f'compute__A{k}' for k in range(3)]+[f'bank_service__A{k}' for k in range(3)]
        highs=['compute__RESTOREB','EXTERNAL_RESTOREB']
        for p in lows:connect('VSS',native(lane,p))
        for p in highs:connect('VDD',native(lane,p))
        connect('VDD',native(lane,'VDD'));connect('VSS',native(lane,'VSS'))
        connect('COMPUTE_REFERENCE',native(lane,'COMPUTE_REFERENCE'),native(lane,'EXTERNAL_INIT_DATA'))
    connect('VDD',controller('VDD'));connect('VSS',controller('VSS'))
    body=reference(am['service_cell'],*origins[0])+reference(am['service_cell'],*origins[1])+reference(status['design'],*control_origin)
    shapes=[];terminal_number=0;top_y=max(b[3] for b in bounds)+100000
    for ni,(name,nodes) in enumerate(nets.items()):
        track=top_y+ni*3200;xs=[];net_shapes=[]
        for node in nodes:
            l=node['layer'];x,y=node['xy'];b=bounds[node['block']];extra=20000+terminal_number*2000;terminal_number+=1
            if l==42:side='left' if x<(b[0]+b[2])/2 else 'right'
            elif node['block']<2:
                old=am['original_service_bbox_dbu'];local=node['original_xy']
                if local[0]<old[0]:side='left'
                elif local[0]>old[2]:side='right'
                elif local[1]>old[3]:side='top'
                elif local[1]<old[1]:side='bottom'
                else:raise AssertionError(('unescaped native pin',node))
            elif l==46:side='bottom' if y<(b[1]+b[3])/2 else 'top'
            else:side='left' if x<(b[0]+b[2])/2 else 'right'
            ex=b[0]-extra if side in ['left','top','bottom'] else b[2]+extra
            here=[]
            if side in ['left','right']:
                here.append(wire(l,(x,y),(ex,y)))
                here+=via(42,46,40,(ex,y)) if l==42 else via(46,81,41,(ex,y))
                here.append(wire(46,(ex,y),(ex,track)));here+=via(46,81,41,(ex,track))
            else:
                ey=b[1]-extra if side=='bottom' else b[3]+extra
                if l==81:here+=via(46,81,41,(x,y))
                here.append(wire(46,(x,y),(x,ey)));here+=via(46,81,41,(x,ey))
                here.append(wire(81,(x,ey),(ex,ey)));here+=via(46,81,41,(ex,ey))
                here.append(wire(46,(ex,ey),(ex,track)));here+=via(46,81,41,(ex,track))
            xs.append(ex);net_shapes.extend(here)
        net_shapes.append(wire(81,(min(xs),track),(max(xs),track)))
        for l,b in net_shapes:body+=rect(l,b);shapes.append((name,l,b))
        body+=label(name,min(xs),track)
        records.append(dict(net=name,nodes=nodes,track_y_dbu=track,shapes=net_shapes))
    # Signal shorts are never accepted as an article imperfection.
    conflicts=[]
    for i,(owner,l,b) in enumerate(shapes):
        for other,ol,c in shapes[:i]:
            if owner!=other and l==ol and min(b[2],c[2])>max(b[0],c[0]) and min(b[3],c[3])>max(b[1],c[1]):
                conflicts.append([owner,other,l,b,c])
    plan=dict(nets=records,bindings=bindings,new_rectangles=len(shapes),new_net_overlap_conflicts=conflicts,
              service_origins_dbu=origins,service_bbox_dbu=abb,control_origin_dbu=control_origin,block_bounds_dbu=bounds,
              scope='84real controller-to-native phase/address/capture paths; shared VDD/VSS with legacy access pins held off, physical EXTERNAL_INIT_DATA tied to compute zero reference. Parent RC/power loading, native phases/weight producer/5ms still unqualified.')
    (OUT/'route_plan.json').write_text(json.dumps(plan,indent=2)+'\n');assert not conflicts,conflicts[:3]
    cells.update(dcells);top='GF180_CONTROLLED_PAGE_SERVICE_PAIR_V2';cells[top]=begin(top)+body+rec(7,0)
    gds=OUT/'controlled_page_service_pair_v2.gds';gds.write_bytes(prefix+b''.join(cells.values())+rec(4,0))
    report=dict(top_cell=top,gds=gds.relative_to(ROOT).as_posix(),gds_bytes=gds.stat().st_size,
                native_service_cell=am['service_cell'],controller_cell=status['design'],service_lane_count=2,
                controller_native_connections_built=len(bindings),legacy_disabled_low_pins_per_lane=len(lows),
                legacy_disabled_high_pins_per_lane=len(highs),zero_initialization_reference_physically_tied=True,
                source_library_cells_preserved=True,full_chip_layout_complete=False,full_5ms_population_service_accepted=False,
                scope=plan['scope']+' Actual new GDS connectivity readback required before acceptance. This is a research module pair, not the full ASIC or selected parallelism.',
                sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ampath,proof,analog,status_path,contract,digital,gds,OUT/'route_plan.json']})
    (OUT/'physical_assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['gds','gds_bytes','controller_native_connections_built','legacy_disabled_low_pins_per_lane']},indent=2))

if __name__=='__main__':main()
