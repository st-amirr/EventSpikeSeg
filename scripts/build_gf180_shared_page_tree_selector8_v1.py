"""Native eight-child read/write/enable selection and analog recovered-state mux."""
from pathlib import Path
import collections,hashlib,json,re
from assemble_gf180_full25_physical_candidate_v5 import Library,pinlist,rect,label
from assemble_gf180_external_bank_service_full25_v5 import via
from assemble_gf180_full_capacity_storage_gds_v2 import begin,reference,rec
import probe_gf180_mos_gate_cap as f
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';C='gf180_shared_page_tree_selector8_v1';D=B/'layout'/C
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not D.exists();D.mkdir();f.OUT=D;lib=Library();children={};groups=collections.defaultdict(list);body=[];mods=[];definitions=[];ports=[f'A{k}' for k in range(3)]+['WRITE_CMD','READ_CMD','READ_ENABLE','RECOV','VDD','VSS']+[f'{p}{j}' for j in range(8) for p in ['WRITE','READ','ENABLE','RECOV']];assert len(ports)==41
    for c in ['gf180_bank_page_decoder8_v1','gf180_reset_select_and_fullroute','gf180_fixed_body_tg_quarter_shorttracks']:
        d=B/'layout'/c;q=json.loads((d/'qualification.json').read_text());g=d/(c+'.gds');assert q['lvs_unique'] and q['magic_drc_count']==0 and sha(g)==q['sha256'][g.name];children[c]=(lib.load(g)[c],q,pinlist(d,c));definitions.append((d/(c+'.spice')).read_text())
    def place(tag,c,left,bottom,mapping):
        native,q,pins=children[c];bb=[round(v*1000) for v in q['bbox_um']];ox=left-bb[0];oy=bottom-bb[1];body.append(reference(native,ox,oy));assert set(mapping)==set(q['ports']);mods.append({'instance':tag,'cell':c,'origin_dbu':[ox,oy],'bbox_dbu':[left,bottom,left+bb[2]-bb[0],bottom+bb[3]-bb[1]],'mapping':mapping})
        for i,pin in enumerate(q['ports']):
            layer,x,y=pins[pin];x=round(x+ox);y=round(y+oy)
            if layer=='metal3':
                sx=left-2000-i*2000;ey=bottom+bb[3]-bb[1]+10000+i*3200
                body.extend([rect(42,(min(sx,x)-200,y-200,max(sx,x)+200,y+200)),via(42,46,40,sx,y),rect(46,(sx-200,min(y,ey)-200,sx+200,max(y,ey)+200)),via(46,81,41,sx,ey)]);x,y=sx,ey
            else:assert layer=='metal5'
            groups[mapping[pin]].append((tag,pin,x,y))
    mapping={f'A{k}':f'A{k}' for k in range(3)};mapping.update(WRITE_CMD='WRITE_CMD',READ_CMD='READ_CMD',VDD='VDD',VSS='VSS');mapping.update({f'{mode}{j}':f'{mode}{j}' for mode in ['WRITE','READ'] for j in range(8)})
    place('DEC','gf180_bank_page_decoder8_v1',500000,0,mapping)
    for j in range(8):
        y=250000+j*140000
        place(f'G{j}','gf180_reset_select_and_fullroute',500000,y,{'A':f'READ{j}','B':'READ_ENABLE','Y':f'ENABLE{j}','YB':f'ENABLEB{j}','VDD':'VDD','VSS':'VSS'})
        place(f'T{j}','gf180_fixed_body_tg_quarter_shorttracks',700000,y+60000,{'A':f'RECOV{j}','B':'RECOV','EN':f'ENABLE{j}','ENB':f'ENABLEB{j}','VDD':'VDD','VSS':'VSS'})
    endpoint=0;track=1400000;netrows=[]
    for ni,(net,ends) in enumerate(groups.items()):
        ty=track+ni*3200;xs=[]
        for tag,pin,x,y in ends:
            ex=-20000-endpoint*2000;endpoint+=1;xs.append(ex);body.extend([rect(81,(min(x,ex)-220,y-220,max(x,ex)+220,y+220)),via(81,46,41,ex,y),rect(46,(ex-200,min(y,ty)-220,ex+200,max(y,ty)+220)),via(46,81,41,ex,ty)])
        body.append(rect(81,(min(xs)-1200,ty-220,max(xs)+1200,ty+220)))
        if net in ports:body.append(label(net,min(xs)-1000,ty))
        netrows.append({'net':net,'endpoint_pins':[tag+'.'+pin for tag,pin,*_ in ends]})
    root=C+'_parent';source=D/'source_parent.gds';source.write_bytes(lib.prefix+b''.join(lib.cells)+begin(root)+b''.join(body)+rec(7,0)+rec(4,0));ref='\n'.join(definitions)+'\n.subckt reference '+' '.join(ports)+'\n'
    for p in mods:ref+='X'+p['instance']+' '+' '.join(p['mapping'][pin] for pin in children[p['cell']][1]['ports'])+' '+p['cell']+'\n'
    ref+='.ends\n';rp=D/'reference.spice';rp.write_text(ref)
    t='drc off\ngds read /workspace/'+source.relative_to(R).as_posix()+'\nload '+root+'\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\ndrc off\nflatten -dotoplabels '+C+'\nload '+C+'\nsave '+C+'\nextract no capacitance\nextract no coupling\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice hierarchy off\next2spice scale off\next2spice -o '+C+'.spice\ngds write '+C+'.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n';log=f.magic(t);(D/'extraction.log').write_text(log);dc=re.search(r'Total DRC errors found:\s*(\d+)',log);assert dc
    setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl';nl=f.run(['netgen-lvs','-batch','lvs',C+'.spice '+C,'reference.spice reference',setup,'lvs.out']);(D/'netgen.log').write_text(nl)
    paths=[Path(__file__),source,rp,D/'extraction.log',D/'netgen.log']+[D/(C+s) for s in ['.mag','.spice','.gds']]
    (D/'build_source.py').write_bytes(Path(__file__).read_bytes())
    q={'cell':C,'ports':ports,'bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],'mos_count':230,'native_mim_count':0,'magic_drc_count':int(dc[1]),'lvs_unique':'Circuits match uniquely' in nl,'source_layout_completed':True,'scope':'Native8way hierarchicalpage service stage:166MOSdecoder+8sixMOSread-enableAND+8twoMOSanalogTG. Separatechild READ/WRITE/ENABLE;one selected RECOV throughTG. Numericstate remainsanalog. Addressstablewhilecommandsactive;READ_ENABLE delayedafterselection. Recursivelyusableabovequalifiedpages,butglobalfanout/loadedhierarchy,writeDATA/lowaddress/biasrouting,scheduler,precision and5ms needintegration.','sha256':{p.relative_to(R).as_posix():sha(p) for p in paths}}
    (D/'initial_physical_result.json').write_text(json.dumps(q,indent=2)+'\n');(D/'placement_and_binding.json').write_text(json.dumps({'modules':mods,'nets':netrows},indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k not in ['ports','sha256']},indent=2));assert q['magic_drc_count']==0 and q['lvs_unique']
if __name__=='__main__':main()
