"""Move eight existing resident pairs per actor into a connected1024state shared page."""
from pathlib import Path
import collections,hashlib,json,struct
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements,via
from assemble_gf180_full_capacity_storage_gds_v2 import begin,reference,rec,string
from assemble_gf180_full25_physical_candidate_v5 import Library,pinlist,rect,label
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
S=B/'assembly/full25_shared_ROOT128_v6';P=B/'assembly/shared_reader_page1024_v1';D=B/'assembly/full25_shared_page1024_v7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def labels(blob):
    out={}
    for e in elements(blob):
        if e[0][0]!=12:continue
        name=next(v.rstrip(b'\0').decode() for t,d,v,b in e if t==25)
        lay=next(struct.unpack('>h',v)[0] for t,d,v,b in e if t==13)
        xy=next(struct.unpack('>2i',v) for t,d,v,b in e if t==16)
        assert name not in out;out[name]=(lay,*xy)
    return out
def main():
    assert not D.exists();D.mkdir();mf=S/'physical_assembly.json';g=S/'eventspikeseg140k_shared_ROOT128_v6.gds';m=json.loads(mf.read_text());prefix,cells=cells_read(g.read_bytes());lib=Library()
    pg=P/'shared_reader_page1024.gds';_,pc=cells_read(pg.read_bytes());page='SHARED_READER_PAGE1024_V1';ppins=labels(pc[page]);pn=lib.load(pg)[page]
    assert len(ppins)==1056
    assert json.loads((P/'verification/native_parent_v1/parent_exact_connectivity_attempt.json').read_text())['independent_connectivity_accepted']
    pair='gf180_independent_bank_pair_v4';pairg=B/'layout'/pair/(pair+'.gds');pairname='N'+sha(pairg)[:8]+'_'+hashlib.sha256(pair.encode()).hexdigest()[:16]
    pairbb=[round(v*1000) for v in json.loads((B/'layout'/pair/'qualification.json').read_text())['bbox_um']]
    moves=[]
    for p in m['state_planes']:
        if p['state_kind']!='membrane':continue
        remaining=8;body=[];taken=[];pitch,yp=p['local_pair_pitch_dbu'];cw,ch=p['channel_pitch_dbu'];cols=p['channel_grid_cols']
        for e in elements(cells[p['candidate_cell']]):
            child=next((v.rstrip(b'\0').decode() for t,d,v,b in e if t==18),None)
            if child!=pairname or not remaining:body.append(b''.join(b for t,d,v,b in e));continue
            xy=next(struct.unpack('>'+str(len(v)//4)+'i',v) for t,d,v,b in e if t==16)
            nx,ny=next((struct.unpack('>2h',v) for t,d,v,b in e if t==19),(1,1));dx=pitch if nx==1 else (xy[2]-xy[0])//nx;dy=yp if ny==1 else (xy[5]-xy[1])//ny
            assert dx==pitch and dy==yp
            for row in range(ny):
                n=min(remaining,nx);remaining-=n
                for col in range(n):
                    x=xy[0]+col*dx;y=xy[1]+row*dy;left=x+pairbb[0];bottom=y+pairbb[1]
                    channel=(bottom//ch)*cols+left//cw;by=(bottom%ch)//yp;pi=(left%cw)//pitch;start=int(channel==0 and by==0)
                    assert bottom%ch%yp==0 and left%cw%pitch==0
                    taken.append({'page_pair':len(taken),'channel':channel,'bank_y':by,'bank_x_pair':[start+2*pi,start+2*pi+1],'removed_origin_dbu':[x,y]})
                if n<nx:body.append(reference(pairname,xy[0]+n*dx,xy[1]+row*dy,nx-n,1,dx,dy))
                if not remaining and row+1<ny:
                    body.append(reference(pairname,xy[0],xy[1]+(row+1)*dy,nx,ny-row-1,dx,dy));break
        assert remaining==0 and len(taken)==8
        cells[p['candidate_cell']]=begin(p['candidate_cell'])+b''.join(body)+rec(7,0);p['pair_instances']-=8;p['locally_decoded_bank_equivalents']-=16
        for t in taken:
            for bank,bx in enumerate(t['bank_x_pair']):p['external_compute_service_bank_exceptions'].append({'channel':t['channel'],'bank_y':t['bank_y'],'bank_x':bx,'native_instance':'page_service','page_pair':t['page_pair'],'state_port':f'P{t["page_pair"]}__B{bank}_STATE[row][column]'})
        moves.append({'actor':p['actor'],'plane_index':p['plane_index'],'pairs':taken})
    assert len(moves)==25
    shift='gf180_candidate_penalty_subtractor_v2';tg='gf180_fixed_body_tg_quarter_shorttracks';native={}
    for c in [shift,tg]:
        d=B/'layout'/c;q=json.loads((d/'qualification.json').read_text());cg=d/(c+'.gds');assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and sha(cg)==q['sha256'][cg.name];native[c]=(lib.load(cg)[c],q,pinlist(d,c))
    sizes={};newnets=[]
    for a in m['actor_regions']:
        root=a['gds_cell'];oldlabels=labels(cells[root]);body=[b''.join(b for t,d,v,b in e) for e in elements(cells[root])];groups=collections.defaultdict(list)
        # Leave native V6 controllers/compute and prior128state service intact. New page
        # has its own level shift and gated restore into the same compute numerical input.
        localtop=a['bbox_dbu'][3]-a['bbox_dbu'][1];px=1931200;py=localtop+300000
        body.append(reference(pn,px,py));pageplace={'instance':'page_service','cell':'shared_reader_page1024_v1','gds_native_cell':pn,'assembly_source':(P/'physical_partition.json').relative_to(R).as_posix(),'origin_dbu':[px,py],'bbox_dbu':[px-1383200,py,px+2087220,py+8209820]}
        placements=[pageplace];end=pageplace['bbox_dbu'][3]+100000
        for tag,c in [('page_up',shift),('page_restore',tg)]:
            name,q,pins=native[c];bb=[round(v*1000) for v in q['bbox_um']];ox=548000-bb[0];oy=end-bb[1];body.append(reference(name,ox,oy));placements.append({'instance':tag,'cell':c,'origin_dbu':[ox,oy],'bbox_dbu':[548000,end,548000+bb[2]-bb[0],end+bb[3]-bb[1]]});end=placements[-1]['bbox_dbu'][3]+100000
        def endpoint(net,tag,pin,lay,x,y):groups[net].append((tag,pin,lay,round(x),round(y)))
        pmap={'RECOV':'PAGE_RECOVERED','VCM':'STORAGE_REFERENCE','VDD':'VDD','VSS':'VSS'}
        pmap.update({f'DATA{k}':f'SHARED_WRITE_DATA{k}' for k in range(8)})
        for pin,(lay,x,y) in ppins.items():
            if '__B' in pin and '_STATE' in pin:body.append(label('page_service__'+pin,px+x,py+y,lay));continue
            endpoint(pmap.get(pin,'PAGE1024__'+pin),'page_service',pin,lay,px+x,py+y)
        maps={'page_up':{'CANDIDATE':'PAGE_RECOVERED','PENALTY':'STORAGE_REFERENCE','VCOM':'COMPUTE_REFERENCE','ADJUSTED':'PAGE_SHIFTED','VDD':'VDD','VSS':'VSS'},'page_restore':{'A':'PAGE_SHIFTED','B':'EXTERNAL_COMPUTE_DATA','EN':'PAGE_RESTORE','ENB':'PAGE_RESTOREB','VDD':'VDD','VSS':'VSS'}}
        for p in placements[1:]:
            _,q,pins=native[p['cell']];ox,oy=p['origin_dbu']
            for i,(pin,(layer,x,y)) in enumerate(pins.items()):
                net=maps[p['instance']].get(pin,p['instance']+'__'+pin);lay={'metal1':34,'metal2':36,'metal3':42,'metal4':46,'metal5':81}[layer];x=round(ox+x);y=round(oy+y)
                if lay!=81:
                    ey=p['bbox_dbu'][3]+10000+i*3200
                    if lay==34:body.extend([via(34,36,35,x,y),via(36,42,38,x,y)])
                    if lay in [34,42]:body.append(via(42,46,40,x,y))
                    assert lay in [34,42,46]
                    body.extend([rect(46,(x-200,min(y,ey)-200,x+200,max(y,ey)+200)),via(46,81,41,x,ey)]);y=ey
                endpoint(net,p['instance'],pin,81,x,y)
        # Attach to existing public service nets at parent M5 pads outside native leaves.
        oldattach=['VDD','VSS','STORAGE_REFERENCE','COMPUTE_REFERENCE','EXTERNAL_COMPUTE_DATA']+[f'SHARED_WRITE_DATA{k}' for k in range(8)]
        for net in oldattach:
            lay,x,y=oldlabels[net];assert lay==81;endpoint(net,'V6_PARENT',net,lay,x,y)
        track=end+100000
        for ni,(net,ends) in enumerate(groups.items()):
            ty=track+ni*3200;xs=[]
            for ei,(tag,pin,lay,x,y) in enumerate(ends):
                ex=-a['external_service_spine_gutter_dbu']-10000-2000*(ni*6+ei);xs.append(ex);assert lay==81
                body.extend([rect(81,(min(x,ex)-220,y-220,max(x,ex)+220,y+220)),via(81,46,41,ex,y),rect(46,(ex-200,min(y,ty)-220,ex+200,max(y,ty)+220)),via(46,81,41,ex,ty)])
            body.append(rect(81,(min(xs)-1200,ty-220,max(xs)+1200,ty+220)))
            if net not in oldattach:body.append(label(net,min(xs)-1000,ty))
            newnets.append({'actor':a['actor'],'net':net,'endpoint_pins':[tag+'.'+pin for tag,pin,*_ in ends],'existing_parent_net_attachment':net in oldattach,'externally_supplied_or_unconsumed':len(ends)==1})
        cells[root]=begin(root)+b''.join(body)+rec(7,0);a['modules']+=placements;a['representative_compute_tile_resident_membranes']=1216;a['remaining_membrane_banks_access_unconnected']-=16;a['shared1024page_compute_service_physical']=True;a['shared1024page_parent_qualified']=False
        gutter=a['external_service_spine_gutter_dbu']+10000+2000*(len(groups)*6+6)+10000
        sizes[root]=(a['bbox_dbu'][2]-a['bbox_dbu'][0]-a['external_service_spine_gutter_dbu'],track+len(groups)*3200+100000,gutter)
    # Repack enlarged characterization actors; state atlas geometry/coordinates remain.
    x=0;y=round(m['storage_atlas_height_um']*1000)+1000000;shelf=0;origins={}
    for a in m['actor_regions']:
        w,h,gutter=sizes[a['gds_cell']]
        if x+gutter+w>140000000:x=0;y+=shelf+200000;shelf=0
        origins[a['gds_cell']]=[x+gutter,y];a['origin_dbu']=origins[a['gds_cell']];a['bbox_dbu']=[x,y,x+gutter+w,y+h];a['external_service_spine_gutter_dbu']=gutter;x+=gutter+w+200000;shelf=max(shelf,h)
    top=[];oldtop=m['top_cell'];newtop='ESS140K_SHARED_PAGE1024_V7';delta=y+shelf+300000-min(w['source_pad_dbu'][1] for e in m['protocol_edges'] for w in e['wires'])
    for e in elements(cells.pop(oldtop)):
        child=next((v.rstrip(b'\0').decode() for t,d,v,b in e if t==18),None);new=[]
        for t,d,v,b in e:
            if t==16 and child in origins:b=rec(16,3,struct.pack('>2i',*origins[child]))
            elif t==16 and child=='ESS_PROTOCOL_CORRIDORS':xx,yy=struct.unpack('>2i',v);b=rec(16,3,struct.pack('>2i',xx,yy+delta))
            new.append(b)
        top.append(b''.join(new))
    cells[newtop]=begin(newtop)+b''.join(top)+rec(7,0)
    for e in m['protocol_edges']:
        for w in e['wires']:w['source_pad_dbu'][1]+=delta;w['destination_pad_dbu'][1]+=delta;w['track_y_dbu']+=delta
    for blob in lib.cells:
        name=next(v.rstrip(b'\0').decode() for t,d,v,b in __import__('assemble_gf180_full_capacity_storage_gds_v2').records(blob) if t==6)
        if name in cells:assert cells[name]==blob
        else:cells[name]=blob
    dest=D/'eventspikeseg140k_shared_page1024_v7.gds';dest.write_bytes(prefix+b''.join(cells.values())+rec(4,0))
    m.update(top_cell=newtop,source_physical_candidate=mf.relative_to(R).as_posix(),local_bank_pair_instances=m['local_bank_pair_instances']-200,locally_decoded_storage_bank_equivalents=865605,representative_compute_resident_states=30400,shared1024page_instances=25,shared1024page_identity_bindings=moves,full_chip_layout_complete=False,full_chip_functional_layout_complete=False)
    m['local_pin_nets']+=newnets;m['native_macro_instances'][pair]-=200;m['native_macro_instances']['shared_reader_page1024_v1']=25
    for c,n in [(shift,25),(tg,25)]:m['native_macro_instances'][c]=m['native_macro_instances'].get(c,0)+n
    m['scope']='V7 moves200actual resident pairs into25physical1024state pages. Shared8writecolumns connect existingcompute;onefeedbackreader/page connects throughnativelevelshift andgatedrestore to existingcompute numericalinput. Original64+128state service peractor retained. Commands/restore/bias remain external categorical/analogprogramminginterfaces;higherglobalservice,graphoperators/parameterdistribution and5ms remain incomplete. NewparentDRC/exactgraph required. Spacious characterization placement is notcompactdie.'
    m['atlas_bbox_um'][3]+=delta*.001;m['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),mf,g,pg,dest]}
    (D/'physical_assembly.json').write_text(json.dumps(m,indent=2)+'\n')
    (D/'resident_page_move_inventory_v1.json').write_text(json.dumps({'removed_native_pairs':200,'new1024pages':25,'total_state_capacity_unchanged':True,'moves':moves,'new_parent_qualified':False},indent=2)+'\n')
    print(json.dumps({'gds':str(dest),'moved_pairs':200,'shared_pages':25,'physically_bound_sites':30400,'new_parent_qualified':False},indent=2))
if __name__=='__main__':main()
