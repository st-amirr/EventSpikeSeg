"""Assemble routed writer and isolated-memory modules with physical bus and reference routing."""
import argparse,hashlib,json,re
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--shielded',action='store_true');parser.add_argument('--vertical-guards',action='store_true');args=parser.parse_args()
    if args.vertical_guards:args.shielded=True
    cell='gf180_writer_memory_characterization_preloaded'+('_guarded' if args.vertical_guards else ('_shielded' if args.shielded else ''))
    out=flow.BASE/'layout'/cell
    out.mkdir(parents=True,exist_ok=True)
    if (out/'qualification.json').exists():raise ValueError('Preserve qualified reader')
    flow.OUT=out
    inputs=set();children={};qualifications={}
    writer='gf180_isolated_memory_writer';memory='gf180_isolated_memory_characterization_fullroute'
    for name in [writer,memory]:
        directory=flow.BASE/'layout'/name;qp=directory/'qualification.json';q=json.loads(qp.read_text())
        if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Native input unqualified')
        if (q['gds_roundtrip_drc_count'] or not q['gds_roundtrip_lvs_unique']):raise ValueError('Corrected GDS required')
        inputs.add(qp)
        for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
            for filename,expected in q.get(key,{}).items():
                p=directory/filename if key=='sha256' else flow.ROOT/filename
                if digest(p)!=expected:raise ValueError('Changed child evidence: '+str(p))
                inputs.add(p)
        children[name]=directory;qualifications[name]=q
    nets=['STATE','VCM','MIDDLE','COL','DRAIN','WRITE','WRITEB','OUTER','OUTERB','MIDCLAMP','MIDCLAMPB','READ','READB','PARK','PARKB','VSS','VDD','BUS','IP','REF','FB','BIAS','CMP','GAIN1','GAIN2']
    pitch=600 if args.shielded else 480
    tracks={net:80000+i*pitch for i,net in enumerate(nets)}
    layers={}
    def rect(layer,box):layers.setdefault(layer,[]).append(tuple(box))
    def via(low,high,cut,x,y,pad=40):
        for layer in [low,high]:
            enclosure=max(pad,60) if layer=='metal5' else pad
            rect(layer,(x-enclosure,y-enclosure,x+enclosure,y+enclosure))
        rect(cut,(x-28,y-28,x+28,y+28))
    configurations=[('writer',writer,0,0,['IP','REF','FB','BUS','VDD','VSS','BIAS','CMP','GAIN1','GAIN2']),('memory',memory,160000,0,['STATE','VCM','MIDDLE','COL','DRAIN','WRITE','WRITEB','OUTER','OUTERB','MIDCLAMP','MIDCLAMPB','READ','READB','PARK','PARKB','VSS','VDD','BUS'])]
    uses=[]
    for instance,name,dx,dy,mapping in configurations:
        bbox=[round(v/.005) for v in qualifications[name]['bbox_um']]
        uses.extend([f'use {name} {instance}',f'transform 1 0 {dx} 0 1 {dy}','box '+' '.join(map(str,bbox))])
        labels=re.findall(r'(?m)^rlabel (metal[1-5]) s (-?\d+) (-?\d+) (-?\d+) (-?\d+) 4 (\S+)\nport (\d+)',(children[name]/(name+'.mag')).read_text())
        ordered=sorted(labels,key=lambda x:int(x[-1]))
        if len(ordered)!=len(mapping):raise ValueError('Port inventory mismatch')
        fanout_pitch=(720 if name==memory else 600) if args.vertical_guards else (480 if name==memory else 240)
        for i,(label,net) in enumerate(zip(ordered,mapping)):
            layer,x1,y1,x2,y2,port,number=label
            x=dx+(int(x1)+int(x2))//2;y=dy+(int(y1)+int(y2))//2
            column=dx+bbox[0]-600-i*fanout_pitch
            half_width=60 if layer=='metal5' else 40
            rect(layer,(min(x,column)-half_width,y-half_width,max(x,column)+half_width,y+half_width))
            if layer=='metal1':
                via('metal1','metal2','via1',column,y);via('metal2','metal3','via2',column,y);via('metal3','metal4','via3',column,y)
            elif layer=='metal3':via('metal3','metal4','via3',column,y)
            elif layer=='metal5':via('metal4','metal5','via4',column,y)
            elif layer!='metal4':raise ValueError('Unexpected pin layer')
            rect('metal4',(column-40,y-40,column+40,tracks[net]+40))
            via('metal4','metal5','via4',column,tracks[net],108 if name==memory and layer=='metal4' else 40)
        if args.vertical_guards:
            start=dy+max((int(label[2])+int(label[4]))//2 for label in ordered)+400
            for i in range(len(mapping)-1):
                column=dx+bbox[0]-600-i*fanout_pitch-fanout_pitch//2
                rect('metal4',(column-40,start,column+40,max(tracks.values())+400))
                via('metal4','metal5','via4',column,tracks['VSS'])
    left_edge=-11000 if args.vertical_guards else -9000
    for y in tracks.values():rect('metal5',(left_edge,y-60,210000,y+60))
    if args.shielded:
        guards=[80000+i*pitch+pitch//2 for i in range(len(nets)-1)]
        for y in guards:
            rect('metal5',(left_edge,y-60,210560,y+60));via('metal4','metal5','via4',210500,y)
        rect('metal4',(210460,min(guards)-40,210540,max(guards)+40))
        rect('metal5',(209940,tracks['VSS']-60,210560,tracks['VSS']+60));via('metal4','metal5','via4',210500,tracks['VSS'])
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
    # Preload the complete qualified hierarchy in dependency order; Magic otherwise
    # resolves grandchildren relative to their parent directory and loses cells.
    geometry={p.stem:p for p in inputs if p.suffix=='.mag'}
    for name,directory in children.items():geometry[name]=directory/(name+'.mag')
    loaded=set();ordered=[]
    def visit(name):
        if name in loaded:return
        p=geometry[name]
        for child in re.findall(r'(?m)^use (\S+) ',p.read_text()):
            if child not in geometry:raise ValueError('Missing qualified descendant '+child)
            visit(child)
        ordered.append(p);loaded.add(name)
    for name in children:visit(name)
    preload=''.join('load /workspace/'+p.with_suffix('').relative_to(flow.ROOT).as_posix()+'\n' for p in ordered)
    log = flow.magic(preload+f'load {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nputs [drc listall why]\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {cell}.spice\ngds write {cell}.gds\nfeedback save gds_warnings.feedback\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (out/'extraction.log').write_text(log)
    drc = re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc[1]) or (out/'gds_warnings.feedback').read_text() or re.search(r'\d+ problems occurred|Failure to read|I/O error',log):
        raise RuntimeError(log[-5000:])
    ref = ''.join((directory/(name+'.spice')).read_text()+'\n' for name,directory in children.items())
    ref += '.subckt reference '+ ' '.join(nets)+'\n'
    for instance,name,dx,dy,mapping in configurations:
        ref += 'X'+instance+' '+' '.join(mapping)+' '+name+'\n'
    ref += '.ends\n'
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
         'native_mim_count':2,'native_resistor_count':4,'mos_count':18,'dummy_junction_geometry_preserved_hierarchically':True,
         'vertical_fanout_ground_guards':args.vertical_guards,'grounded_global_route_guards':args.shielded,'ground_guard_count':len(nets)-1 if args.shielded else 0,
         'capacitance_count':len(re.findall(r'(?m)^C\S+',(out/(cell+'_cap.spice')).read_text())),
         'physical_storage_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,
         'scope':'Physical hierarchical assembly of native7MOS/four-resistor/compensation-MIM writer and11MOS/minimum-MIM isolated analog memory, including real BUS, feedback, external-reference, clock/control, column, supply and state diagnostic routes. Full DRC/LVS/GDS readback and cap extraction. Frozen writer settings; references, bias diode, clocks and column frontend external. Spacious characterization assembly, not compact array or full neuron. New parent routing requires connected simulation. No RPEX/noise/mismatch/PVT, qualified leakage/retention, original-model accuracy,5ms population service or full-chip acceptance.',
         'sha256':{p.name:digest(p) for p in files},
         'input_sha256':{p.relative_to(flow.ROOT).as_posix():digest(p) for p in sorted(inputs)},
         'gds_roundtrip_sha256':{p.relative_to(flow.ROOT).as_posix():digest(p) for p in [rd/n for n in ['readback.log','netgen.log','roundtrip.spice','roundtrip.feedback']]}}
    (out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n')
    print(json.dumps({'report':str(out/'qualification.json'),'bbox_um':q['bbox_um'],'gds_roundtrip_lvs_unique':True},indent=2))


if __name__ == '__main__':
    main()
