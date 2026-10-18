"""Physical recursive READ/WRITE/analogDATA hierarchy for all remaining state banks.

Native1024state pages and374MOS selection/isolation nodes. Geometry is a spacious
research atlas. Identity,incremental wiring,DRC/loading and actor links need audit.
"""
from pathlib import Path
import collections,hashlib,json,math,struct
from functools import lru_cache
from assemble_gf180_external_bank_service_full25_v5 import cells_read,elements,via
from assemble_gf180_full25_physical_candidate_v5 import Library,pinlist,rect,label
from assemble_gf180_full_capacity_storage_gds_v2 import begin,reference,rec
from assemble_gf180_full25_shared_page1024_v7 import labels
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';S=B/'assembly/full25_shared_page1024_v8';D=B/'assembly/full_population_page_forest_v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def public(level):return [f'ADDR{k}' for k in range(7+3*level)]+[f'DATA{k}' for k in range(8)]+[f'SEL{k}' for k in range(8)]+['WRITE_CMD','READ_CMD','READ_ENABLE','RECOV','MASTER_NBIAS','PBIAS','VCM','VDD','VSS']
class Factory:
    def __init__(self):
        source=S/'eventspikeseg140k_shared_page1024_v7.gds';self.prefix,allcells=cells_read(source.read_bytes());self.cells={};self.meta={};self.cache={};self.inputs={source};m=json.loads((S/'physical_assembly.json').read_text());p=next(p for p in m['actor_regions'][0]['modules'] if p['instance']=='page_service');leaf=p['gds_native_cell']
        def visit(n):
            if n in self.cells:return
            self.cells[n]=allcells[n]
            for e in elements(allcells[n]):
                for t,d,v,b in e:
                    if t==18:visit(v.rstrip(b'\0').decode())
        visit(leaf);pins=labels(self.cells[leaf]);ports={}
        for name in public(0):
            actual=('LOW'+name[4:] if int(name[4:])<4 else 'HIGH'+str(int(name[4:])-4)) if name.startswith('ADDR') else name
            lay,x,y=pins[actual];ports[name]={'pin':actual,'layer':lay,'xy_dbu':[x,y]}
        self.leaf={'cell':leaf,'kind':'native1024page','level':0,'leaf_pages':1,'bbox_dbu':[-1383200,0,2087220,8209820],'ports':ports,'interface_y_dbu':min(p['xy_dbu'][1] for p in ports.values()),'native_state_slots':1024,'qualified_child_source':'artifacts/analog_asic/assembly/shared_reader_page1024_v1/article_delivery_v1.json'};self.meta[leaf]=self.leaf;lib=Library();self.native={}
        for c in ['gf180_shared_page_tree_selector8_v2','gf180_fixed_body_tg_quarter_shorttracks','gf180_dense_inverter_v1']:
            d=B/'layout'/c;qf=d/'qualification.json';q=json.loads(qf.read_text());g=d/(c+'.gds');assert q['lvs_unique'] and q['magic_drc_count']==0 and sha(g)==q['sha256'][g.name];native=lib.load(g)[c];bb=[round(v*1000) for v in q['bbox_um']];pins=pinlist(d,c);pm={p:{'pin':p,'layer':{'metal1':34,'metal2':36,'metal3':42,'metal4':46,'metal5':81}[pins[p][0]],'xy_dbu':[round(pins[p][1]),round(pins[p][2])]} for p in q['ports']};self.native[c]={'cell':native,'kind':'qualified_native','source_cell':c,'bbox_dbu':bb,'ports':pm};self.inputs.update([qf,g])
        for blob in lib.cells:
            name=next(v.rstrip(b'\0').decode() for t,dt,v,b in __import__('assemble_gf180_full_capacity_storage_gds_v2').records(blob) if t==6)
            if name in self.cells:assert self.cells[name]==blob
            else:self.cells[name]=blob
    def tree(self,n,level):
        assert 1<=n<=8**level
        if level==0:return self.leaf
        if (n,level) in self.cache:return self.cache[n,level]
        name=f'GF180_PAGE_TREE_L{level}_N{n}';assert name not in self.cells;cap=8**(level-1);children=[self.tree(min(cap,n-j*cap),level-1) for j in range(math.ceil(n/cap))];pub=public(level);groups=collections.OrderedDict((p,[]) for p in pub);body=[];modules=[];row_y=0;maxright=0;row_index=0
        def row(entries):
            nonlocal row_y,maxright,row_index
            cursor=400000;ends=[];height=max(v['bbox_dbu'][3]-v['bbox_dbu'][1] for tag,v,mapping in entries)
            for tag,v,mapping in entries:
                bb=v['bbox_dbu'];left=cursor+4000+len(v['ports'])*2000;ox=left-bb[0];oy=row_y-bb[1];assert set(mapping)==set(v['ports']);body.append(reference(v['cell'],ox,oy));right=left+bb[2]-bb[0];maxright=max(maxright,right);modules.append({'instance':tag,'cell':v['cell'],'kind':v['kind'],'source_cell':v.get('source_cell'),'origin_dbu':[ox,oy],'bbox_dbu':[left,row_y,right,row_y+bb[3]-bb[1]],'mapping':mapping,'child_interface_y_dbu':v.get('interface_y_dbu'),'row':row_index})
                for pi,(pin,pd) in enumerate(v['ports'].items()):
                    x,y=pd['xy_dbu'];x+=ox;y+=oy;sx=left-2000-pi*2000;lay=pd['layer'];net=mapping[pin]
                    if lay==42:body.extend([rect(42,(min(x,sx)-200,y-200,max(x,sx)+200,y+200)),via(42,46,40,sx,y)])
                    else:
                        assert lay==81;(body.extend([rect(81,(min(x,sx)-220,y-220,max(x,sx)+220,y+220)),via(81,46,41,sx,y)]))
                    ends.append((tag,pin,net,sx,y))
                cursor=right+50000
            channel=row_y+height+10000
            for ei,(tag,pin,net,sx,y) in enumerate(ends):
                ey=channel+ei*3200;body.extend([rect(46,(sx-200,min(y,ey)-200,sx+200,max(y,ey)+200)),via(46,81,41,sx,ey)]);groups.setdefault(net,[]).append({'instance':tag,'pin':pin,'local_escape_dbu':[sx,ey]})
            row_y=channel+len(ends)*3200+50000;row_index+=1
        cols=4 if level%2 else 2
        for first in range(0,len(children),cols):
            entries=[]
            for j in range(first,min(first+cols,len(children))):
                ch=children[j];mapping={p:p for p in ch['ports']};mapping.update({f'DATA{k}':f'CH{j}_DATA{k}' for k in range(8)});mapping.update(WRITE_CMD=f'CH{j}_WRITE',READ_CMD=f'CH{j}_READ',READ_ENABLE=f'CH{j}_ENABLE',RECOV=f'CH{j}_RECOV');entries.append((f'C{j}',ch,mapping))
            row(entries)
        tg=self.native['gf180_fixed_body_tg_quarter_shorttracks'];inv=self.native['gf180_dense_inverter_v1'];sel=self.native['gf180_shared_page_tree_selector8_v2']
        for j in range(8):
            entries=[(f'D{j}_{k}',tg,{'A':f'DATA{k}','B':f'CH{j}_DATA{k}','EN':f'CH{j}_WRITE','ENB':f'CH{j}_WRITEB','VDD':'VDD','VSS':'VSS'}) for k in range(8)]
            entries.append((f'I{j}',inv,{'IN':f'CH{j}_WRITE','OUT':f'CH{j}_WRITEB','VDD':'VDD','VSS':'VSS'}));row(entries)
        mapping={p:p for p in sel['ports']}
        for k in range(3):mapping[f'A{k}']=f'ADDR{7+3*(level-1)+k}'
        for j in range(8):
            for kind in ['WRITE','READ','ENABLE']:mapping[f'{kind}{j}']=f'CH{j}_{kind}'
            mapping[f'RECOV{j}']=f'CH{j}_RECOV' if j<len(children) else 'VCM'
        row([('SELECT',sel,mapping)]);field=row_y+100000;netrows=[];minx=0
        for ni,(net,ends) in enumerate(groups.items()):
            assert ends,net;ex=-20000-ni*2000;ty=field+ni*3200;ys=[];minx=min(minx,ex-1200)
            for e in ends:
                sx,ey=e['local_escape_dbu'];body.extend([rect(81,(min(ex,sx)-220,ey-220,max(ex,sx)+220,ey+220)),via(81,46,41,ex,ey)]);ys.append(ey)
            body.extend([rect(46,(ex-200,min(ys+[ty])-220,ex+200,max(ys+[ty])+220)),via(46,81,41,ex,ty)])
            if net in pub:body.extend([rect(81,(ex-1200,ty-220,ex+1200,ty+220)),label(net,ex-1000,ty)])
            netrows.append({'net':net,'endpoints':[e['instance']+'.'+e['pin'] for e in ends],'spine_dbu':[ex,ty]})
        bb=[minx,0,maxright,field+(len(groups)-1)*3200+220];ports={net:{'pin':net,'layer':81,'xy_dbu':[netrows[ni]['spine_dbu'][0]-1000,netrows[ni]['spine_dbu'][1]]} for ni,net in enumerate(groups) if net in pub};assert list(ports)==pub
        self.cells[name]=begin(name)+b''.join(body)+rec(7,0);meta={'cell':name,'kind':'page_tree','level':level,'leaf_pages':n,'bbox_dbu':bb,'ports':ports,'interface_y_dbu':field,'modules':modules,'nets':netrows,'selector_instances_here':1,'DATA_TG_instances_here':64,'DATA_inverter_instances_here':8,'added_native_MOS_here':374,'child_page_capacity':cap,'populated_children':len(children),'layout_and_wiring_qualified':False};self.meta[name]=meta;self.cache[n,level]=meta;return meta
def main():
    assert not D.exists();D.mkdir();ap=B/'assembly/full_population_page_access_v1/address_assembly_specification_v1.json';a=json.loads(ap.read_text());assert a['global_bank_address_mapping_verified'];f=Factory();planes=[]
    for p in a['planes']:
        view=f.tree(p['native1024_leaf_pages'],p['higher_selector_levels']);planes.append({'plane_index':p['plane_index'],'actor':p['actor'],'state_kind':p['state_kind'],'root_cell':view['cell'],'leaf_pages':p['native1024_leaf_pages'],'active_states':p['remaining_active_states']})
    top='GF180_FULL_POPULATION_PAGE_FOREST_V2';body=[];placements={};free=[(0,0,2100000000,2100000000)];maxx=maxy=0
    for p in sorted(planes,key=lambda p:max(f.meta[p['root_cell']]['bbox_dbu'][2]-f.meta[p['root_cell']]['bbox_dbu'][0],f.meta[p['root_cell']]['bbox_dbu'][3]),reverse=True):
        view=f.meta[p['root_cell']];bb=view['bbox_dbu'];w=bb[2]-bb[0];h=bb[3]-bb[1];pad=1000000;uw=w+pad;uh=h+pad
        options=[(min(fw-uw,fh-uh),max(fw-uw,fh-uh),fy,fx) for fx,fy,fw,fh in free if fw>=uw and fh>=uh];assert options,('atlas_packing_failed',p['plane_index'],w,h)
        _,_,y,x=min(options);nextfree=[]
        for fx,fy,fw,fh in free:
            right=fx+fw;topedge=fy+fh
            if x>=right or x+uw<=fx or y>=topedge or y+uh<=fy:nextfree.append((fx,fy,fw,fh));continue
            if x>fx:nextfree.append((fx,fy,x-fx,fh))
            if x+uw<right:nextfree.append((x+uw,fy,right-x-uw,fh))
            if y>fy:nextfree.append((fx,fy,fw,y-fy))
            if y+uh<topedge:nextfree.append((fx,y+uh,fw,topedge-y-uh))
        free=[]
        for rr in sorted(set(nextfree)):
            rx,ry,rw,rh=rr
            if any(oo!=rr and oo[0]<=rx and oo[1]<=ry and oo[0]+oo[2]>=rx+rw and oo[1]+oo[3]>=ry+rh for oo in nextfree):continue
            free.append(rr)
        ox=x-bb[0];oy=y;body.append(reference(view['cell'],ox,oy));p['origin_dbu']=[ox,oy];p['bbox_dbu']=[x,y,x+w,y+h]
        for name,pd in view['ports'].items():px,py=pd['xy_dbu'];body.append(label(f'F{p["plane_index"]}__{name}',ox+px,oy+py,pd['layer']))
        placements[p['plane_index']]=p;maxx=max(maxx,x+w);maxy=max(maxy,y+h)
    f.cells[top]=begin(top)+b''.join(body)+rec(7,0);g=D/'full_population_page_forest_v2.gds';g.write_bytes(f.prefix+b''.join(f.cells.values())+rec(4,0));names=list(f.cells);assert len(names)==len(set(names));assert sum(p['leaf_pages'] for p in planes)==54105
    o={'top_cell':top,'global_tree_layout_built':True,'global_tree_wiring_qualified':False,'full_model_top_assembled':False,'full_chip_complete':False,'active_states_in_this_forest':54600000,'remaining_active_states_preserved_in_V8_actors':30400,'native1024_leaf_page_instances':54105,'higher_selector_instances':a['higher_selector_instances_required'],'extra_inactive_bank_slots':75,'bbox_dbu':[0,0,maxx,maxy],'geometry_scope':'Spacious characterizationatlas;not compactdie,manufacturingfloorplan or5ms claim. Power/bias/addr fanout andanalogDATA/RECOV loading unqualified.','address_specification':ap.relative_to(R).as_posix(),'planes':[placements[p['plane_index']] for p in planes],'templates':f.meta,'native_sources':f.native,'sha256':{p.relative_to(R).as_posix():sha(p) for p in f.inputs|{Path(__file__),ap,g}}}
    (D/'physical_forest.json').write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({'gds':str(g),'bytes':g.stat().st_size,'active_forest_states':54600000,'leaf_pages':54105,'selector_instances':a['higher_selector_instances_required'],'unique_tree_templates':len(f.cache),'atlas_bbox_mm':[v/1e6 for v in o['bbox_dbu']],'wiring_qualified':False},indent=2))
if __name__=='__main__':main()
