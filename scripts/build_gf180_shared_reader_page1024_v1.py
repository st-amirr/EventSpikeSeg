"""Eight actual128-state pairs share one page-selected feedback reader."""
from pathlib import Path
import collections,hashlib,json
from assemble_gf180_full25_physical_candidate_v5 import Library,pinlist,rect,label
from assemble_gf180_full_capacity_storage_gds_v2 import begin,reference,rec
from build_gf180_fixed_body_tg import rectangles
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
D=B/'assembly/shared_reader_page1024_v1';ROOT='SHARED_READER_PAGE1024_V1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def via(a,b,c,x,y):
    pa=220 if a==81 else 200;pb=220 if b==81 else 200
    return rect(a,(x-pa,y-pa,x+pa,y+pa))+rect(b,(x-pb,y-pb,x+pb,y+pb))+rect(c,(x-140,y-140,x+140,y+140))

def main():
    assert not D.exists();D.mkdir();lib=Library();children={};mods=[];groups=collections.defaultdict(list);body=[];public={}
    def load(c):
        if c not in children:
            d=B/'layout'/c;q=json.loads((d/'qualification.json').read_text());g=d/(c+'.gds')
            assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and sha(g)==q['sha256'][g.name]
            children[c]=(lib.load(g)[c],q,pinlist(d,c))
        return children[c]
    def place(tag,c,left,bottom,mapping,small_slot=None):
        native,q,pins=load(c);bb=[round(v*1000) for v in q['bbox_um']]
        dx=left-bb[0];dy=bottom-bb[1];body.append(reference(native,dx,dy));assert set(mapping)==set(q['ports'])
        p={'instance':tag,'cell':c,'origin_dbu':[dx,dy],'bbox_dbu':[left,bottom,left+bb[2]-bb[0],bottom+bb[3]-bb[1]]};mods.append(p)
        for pi,pin in enumerate(q['ports']):
            layer,x,y=pins[pin];net=mapping[pin];x=round(x+dx);y=round(y+dy)
            if pin.startswith(('B0_STATE','B1_STATE')):
                body.append(label(net,x,y,{'metal3':42,'metal4':46,'metal5':81}[layer]));public[net]=True
            elif tag.startswith('P') and pin=='SELECTED_BIAS':
                # It remains connected through the native pair's bias-selection TGs.
                continue
            else:
                if tag.startswith('P') and pin in ['B0_BIAS','B1_BIAS']:
                    bx,by=(-25000,85240) if pin=='B0_BIAS' else (105000,85880)
                    paint=rectangles(B/'layout'/c/(c+'.mag'),0)
                    assert all(any(a<=bx<=z and b<=by<=w for a,b,z,w in paint[l]) for l in ['metal4','metal5','via4'])
                    layer='metal5';x=dx+bx*5;y=dy+by*5
                groups[net].append((p,pin,pi,layer,x,y,small_slot))
        return p
    pair='gf180_bank_pair_shared_readout_v3'
    for j in range(8):
        _,q,_=load(pair);mapping={pin:f'P{j}__{pin}' for pin in q['ports']}
        mapping.update({f'A{k}':f'LOW{k}' for k in range(3)});mapping.update(BANK_SELECT='LOW3',WRITE_CMD=f'W{j}',READ_CMD=f'R{j}',VDD='VDD',VSS='VSS',VCM='VCM',B0_BIAS='MASTER_NBIAS',B1_BIAS='MASTER_NBIAS')
        mapping.update({f'DATA{k}':f'DATA{k}' for k in range(8)});mapping.update({f'READOUT{k}':f'RAW{j}_{k}' for k in range(8)})
        place(f'P{j}',pair,1000000,j*600000,mapping)
    dec='gf180_bank_page_decoder8_v1';_,q,_=load(dec)
    mapping={f'A{k}':f'HIGH{k}' for k in range(3)};mapping.update(WRITE_CMD='WRITE_CMD',READ_CMD='READ_CMD',VDD='VDD',VSS='VSS')
    mapping.update({f'{mode}{j}':f'{short}{j}' for j in range(8) for mode,short in [('WRITE','W'),('READ','R')]})
    place('SELECT',dec,1000000,4800000,mapping)
    tg='gf180_fixed_body_tg_quarter_shorttracks';inv='gf180_dense_inverter_v1'
    for j in range(8):
        y=5100000+j*200000
        for k in range(8):
            place(f'G{j}_{k}',tg,1000000+k*100000,y,{'A':f'RAW{j}_{k}','B':f'COLUMN{k}','EN':f'R{j}','ENB':f'RB{j}','VDD':'VDD','VSS':'VSS'},k)
        place(f'INV{j}',inv,2000000,y,{'IN':f'R{j}','OUT':f'RB{j}','VDD':'VDD','VSS':'VSS'},8)
    mux='gf180_column_mux8_v2';_,q,_=load(mux);mapping={f'IN{k}':f'COLUMN{k}' for k in range(8)};mapping.update({f'SEL{k}':f'SEL{k}' for k in range(8)});mapping.update(OUT='RAW_MUX',VDD='VDD',VSS='VSS')
    place('COLUMN_MUX',mux,1000000,6900000,mapping)
    reader='gf180_replica_feedback_reader_v3'
    place('READER',reader,1000000,7300000,{'RAW':'RAW_MUX','RECOV':'RECOV','NBIAS':'MASTER_NBIAS','PBIAS':'PBIAS','READ_EN':'READ_ENABLE','VCM':'VCM','VDD':'VDD','VSS':'VSS'})
    public.update({p:True for p in [f'LOW{k}' for k in range(4)]+[f'HIGH{k}' for k in range(3)]+[f'DATA{k}' for k in range(8)]+[f'SEL{k}' for k in range(8)]+['WRITE_CMD','READ_CMD','READ_ENABLE','RECOV','MASTER_NBIAS','PBIAS','VCM','VDD','VSS']})
    endpoint_index=0;netrows=[];track0=7800000
    for ni,(net,ends) in enumerate(groups.items()):
        ytrack=track0+ni*3200;xs=[]
        for p,pin,pi,layer,x,y,slot in ends:
            ex=-20000-2000*endpoint_index;endpoint_index+=1;xs.append(ex)
            if layer=='metal3':
                assert slot is not None
                sx=p['bbox_dbu'][0]-2000-2000*pi
                ey=p['bbox_dbu'][1]+30000+(slot*6+pi)*2400
                body.extend([rect(42,(min(sx,x)-200,y-200,max(sx,x)+200,y+200)),via(42,46,40,sx,y),rect(46,(sx-200,min(y,ey)-200,sx+200,max(y,ey)+200)),via(46,81,41,sx,ey)])
                x,y=sx,ey
            else:assert layer=='metal5',(p['instance'],pin,layer)
            body.extend([rect(81,(min(ex,x)-220,y-220,max(ex,x)+220,y+220)),via(81,46,41,ex,y),rect(46,(ex-200,min(y,ytrack)-220,ex+200,max(y,ytrack)+220)),via(46,81,41,ex,ytrack)])
        body.append(rect(81,(min(xs)-1200,ytrack-220,max(xs)+1200,ytrack+220)))
        if net in public:body.append(label(net,min(xs)-1000,ytrack))
        netrows.append({'actor':'page1024','net':net,'endpoint_pins':[p['instance']+'.'+pin for p,pin,*_ in ends]})
    lib.cells.append(begin(ROOT)+b''.join(body)+rec(7,0));g=D/'shared_reader_page1024.gds';g.write_bytes(lib.prefix+b''.join(lib.cells)+rec(4,0))
    o={'actor_regions':[{'actor':'page1024','gds_cell':ROOT,'modules':mods}], 'local_pin_nets':netrows,'analog_state_count':1024,'native_mos_count':6818,'native_mim_count':1029,'expected_native_primitives':7847,'one_shared_feedback_reader':True,'reader_count':1,'page_select_bits':3,'within_pair_address_bits':4,'shared_write_columns':8,'shared_read_columns':8,'state_identity':'P[pair]__B[bank]_STATE[row][col]; 8pairs x2banks x8rows x8columns','reference_contract':'All16native bank reference diodes shareMASTER_NBIAS with16uA total fixture current (nominal1uA each); common feedbackreader NBIAS. PBIAS1uA sink. Sharing reference gates does not digitize numerical state. Commands off during address changes. READ_ENABLE off untilselected page/row/column settled.','qualified':False,'full_chip_complete':False,'scope':'Actual native hierarchy with1024unique state labels,one feedbackreader and page-gated8column read bus. Preserves qualified children. Fresh parentDRC/exactgraph,RC,nominal andfullmodel bindings required. Fixture geometry is deliberatelyspaced,not dense area.','sha256':{p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),g]}}
    (D/'physical_partition.json').write_text(json.dumps(o,indent=2)+'\n')
    print(json.dumps({k:o[k] for k in ['analog_state_count','native_mos_count','native_mim_count','reader_count','qualified']},indent=2))

if __name__=='__main__':main()
