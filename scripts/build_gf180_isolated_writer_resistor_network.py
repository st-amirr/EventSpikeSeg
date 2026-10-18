"""Route frozen native high-poly feedback network for the isolated-memory writer."""
import hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cell='gf180_isolated_writer_resistor_network';out=flow.BASE/'layout'/cell
    out.mkdir(parents=True,exist_ok=True)
    if (out/'qualification.json').exists():raise ValueError('Preserve qualified resistor network')
    flow.OUT=out
    inputs=set();children={};uses=[];layers={}
    nets=['FB','OUT','REF','GAIN1','GAIN2','VSS']
    tracks={net:16000+i*600 for i,net in enumerate(nets)}
    pairs=[('OUT','FB',2),('FB','GAIN1',64),('GAIN1','GAIN2',2),('GAIN2','REF',4)]
    shapes={}
    for length in [2,4,64]:
        name=f'gf180_writeback_resistor_{length}x1';directory=flow.BASE/'layout'/name
        qp=directory/'qualification.json';q=json.loads(qp.read_text());inputs.add(qp)
        if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Native resistor geometry unqualified')
        for filename,expected in q['sha256'].items():
            p=directory/filename
            if digest(p)!=expected:raise ValueError('Native resistor view changed')
            inputs.add(p)
        shapes[length]=rectangles(directory/(name+'.mag'),0)
    def rect(layer,box):layers.setdefault(layer,[]).append(tuple(box))
    def via(low,high,cut,x,y):
        for layer in [low,high]:
            pad=60 if layer=='metal5' else 40
            rect(layer,(x-pad,y-pad,x+pad,y+pad))
        half=26 if cut=='via1' else 28
        rect(cut,(x-half,y-half,x+half,y+half))
    for i,(a,b,length) in enumerate(pairs):
        shape=shapes[length]
        contacts=sorted(shape['polycontact'],key=lambda b:b[1])
        if len(contacts)!=2:raise ValueError('Expected two native end contacts')
        body=next(b for b in shape['psubdiffcont'] if b[0]<-200 and b[1]<0<b[3])
        dx=i*4000
        for layer,boxes in shape.items():
            for x1,y1,x2,y2 in boxes:rect(layer,(x1+dx,y1,x2+dx,y2))
        for j,(box,net) in enumerate(zip(contacts,[b,a])):
            x=dx+(box[0]+box[2])//2;y=(box[1]+box[3])//2;column=dx+(-700 if j==0 else 700)
            via('metal1','metal2','via1',x,y);rect('metal2',(min(x,column)-40,y-40,max(x,column)+40,y+40))
            rect('metal2',(column-40,y-40,column+40,tracks[net]+40));via('metal2','metal3','via2',column,tracks[net]);via('metal3','metal4','via3',column,tracks[net]);via('metal4','metal5','via4',column,tracks[net])
        x=dx+(body[0]+body[2])//2;column=dx-1100
        # Ground crosses the lower signal fanout: keep it on M3, not M2.
        via('metal1','metal2','via1',x,0);via('metal2','metal3','via2',x,0);rect('metal3',(column-40,-40,x+40,40));rect('metal3',(column-40,-40,column+40,tracks['VSS']+40))
        via('metal2','metal3','via2',column,tracks['VSS']);via('metal3','metal4','via3',column,tracks['VSS']);via('metal4','metal5','via4',column,tracks['VSS'])
    for y in tracks.values():rect('metal5',(-2500,y-60,18500,y+60))
    for i in range(len(nets)-1):
        y=16000+i*600+300;rect('metal5',(-2500,y-60,19060,y+60));via('metal4','metal5','via4',19000,y)
    rect('metal4',(18960,16300,19040,tracks['VSS']+40));rect('metal5',(18440,tracks['VSS']-60,19060,tracks['VSS']+60));via('metal4','metal5','via4',19000,tracks['VSS'])
    lines = ['magic','tech gf180mcuD','magscale 1 10','timestamp 0',*uses]
    for layer, boxes in layers.items():
        lines += ['<< '+layer+' >>']+['rect '+' '.join(map(str,b)) for b in boxes]
    lines += ['<< labels >>']
    for i,net in enumerate(nets,1):
        y = tracks[net]
        lines += [f'rlabel metal5 s -1750 {y-20} -1710 {y+20} 4 {net}',f'port {i} nsew']
    lines += ['<< end >>','']
    (out/(cell+'.mag')).write_text('\n'.join(lines),encoding='ascii')
    (out/'build_source.py').write_bytes(Path(__file__).read_bytes())
    preload = '\n'.join('load /workspace/'+(directory/name).relative_to(flow.ROOT).as_posix() for name,directory in children.items())+'\n'
    log = flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (out/'extraction.log').write_text(log)
    drc = re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc[1]) or (out/'gds_warnings.feedback').read_text() or re.search(r'\d+ problems occurred',log):
        raise RuntimeError(log[-5000:])
    ref='.subckt reference '+' '.join(nets)+'\n'
    for i,(a,b,length) in enumerate(pairs):ref+=f'Xr{i} {a} {b} VSS ppolyf_u_1k r_width=1u r_length={length}u\n'
    ref+='.ends\n'
    (out/'reference.spice').write_text(ref)
    setup = '/workspace/'+flow.PDK.relative_to(flow.ROOT).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
    lvs = flow.run(['netgen-lvs','-batch','lvs',cell+'.spice '+cell,'reference.spice reference',setup,'lvs.out'])
    (out/'netgen.log').write_text(lvs)
    if 'Circuits match uniquely' not in lvs:
        raise RuntimeError(lvs[-3500:])
    caplog = flow.magic(preload+f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance_warnings.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n')
    (out/'capacitance_extraction.log').write_text(caplog)
    if (out/'warnings.feedback').read_text() or (out/'capacitance_warnings.feedback').read_text():
        raise ValueError('Unresolved extraction feedback')
    rd = flow.BASE/'verification/gds_roundtrip'/cell
    rd.mkdir(parents=True,exist_ok=True)
    flow.OUT = rd
    readlog = flow.magic('gds read /workspace/'+(out/(cell+'.gds')).relative_to(flow.ROOT).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n')
    (rd/'readback.log').write_text(readlog)
    rdr = re.search(r'Total DRC errors found:\s*(\d+)',readlog)
    rlvs = flow.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(out/'reference.spice').relative_to(flow.ROOT).as_posix()+' reference',setup,'lvs.out'])
    (rd/'netgen.log').write_text(rlvs)
    if not rdr or int(rdr[1]) or 'Circuits match uniquely' not in rlvs or (rd/'roundtrip.feedback').read_text():
        raise RuntimeError('GDS roundtrip failed\n'+readlog[-1600:]+'\n'+rlvs[-1600:])
    files = [out/(cell+suffix) for suffix in ['.mag','.gds','.spice','_cap.spice']]+[out/n for n in ['build_source.py','extraction.log','reference.spice','netgen.log','capacitance_extraction.log','warnings.feedback','gds_warnings.feedback','capacitance_warnings.feedback']]
    q = {'cell':cell,'ports':nets,'magic_drc_count':0,'lvs_unique':True,'drc_style':'drc(full)',
         'gds_roundtrip_drc_count':0,'gds_roundtrip_lvs_unique':True,'extraction_feedback':'',
         'bbox_um':[int(v)*.005 for v in re.search(r'BBOX ([-0-9 ]+)',log)[1].split()],
         'native_resistor_count':4,'resistor_lengths_um':[2,64,2,4],'resistor_width_um':1,'feedback_ratio':'2/(64+2+4)',
         'grounded_global_route_guards':True,'ground_guard_count':5,
         'capacitance_count':len(re.findall(r'(?m)^C\S+',(out/(cell+'_cap.spice')).read_text())),
         'physical_storage_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,
         'scope':'Four native high-poly resistors forming OUT-to-FB2um and FB-to-REF64+2+4um series gain leg, all1um wide. Actual native geometry with substrate taps and M2-M5 routing; full DRC/LVS/GDS readback and cap extraction. Frozen nominal feedback ratio; no RPEX, noise, mismatch, combined writer simulation, model accuracy, storage or service acceptance.',
         'sha256':{p.name:digest(p) for p in files},
         'input_sha256':{p.relative_to(flow.ROOT).as_posix():digest(p) for p in sorted(inputs)},
         'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():digest(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
    (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n')
    print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'gds_roundtrip_lvs_unique':True},indent=2))


if __name__ == '__main__':
    main()
