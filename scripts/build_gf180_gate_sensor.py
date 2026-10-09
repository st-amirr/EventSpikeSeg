"""Route a permanently attached GF180 source follower and output-select TG."""
import hashlib
import argparse
import json
import re
import probe_gf180_mos_gate_cap as flow
from build_gf180_fixed_body_tg import rectangles

CELL='gf180_gate_sensor'
OUT=flow.BASE/'layout'/CELL
DEVICES=[('sense','nfet',1,1,['VDD','STATE','source','VSS']),
         ('selectn','nfet',1,1,['source','READ','BUS','VSS']),
         ('selectp','pfet',2,1,['source','READB','BUS','VDD'])]
PORTS=['STATE','BUS','READ','READB','VDD','VSS']


def main():
    global CELL,OUT,PORTS,DEVICES
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--encoder-feedback-module',action='store_true')
    parser.add_argument('--encoder-mirrored-feedback',action='store_true')
    parser.add_argument('--pmos-bias-reference',action='store_true')
    parser.add_argument('--encoder-grounded',action='store_true')
    parser.add_argument('--encoder-source-lifted',action='store_true')
    parser.add_argument('--encoder-width-scale',type=int,choices=[1,10,50],default=1)
    parser.add_argument('--encoder-isolate-mirror-drains',action='store_true')
    parser.add_argument('--encoder-isolate-held-gate',action='store_true')
    parser.add_argument('--encoder-export-mirror-nodes',action='store_true')
    parser.add_argument('--encoder-peak-detector',type=int,choices=[10,50])
    parser.add_argument('--encoder-peak-threshold-scale',type=float,choices=[.25,.5,1],default=1)
    parser.add_argument('--encoder-peak-hysteresis',action='store_true')
    parser.add_argument('--shielded',action='store_true',help='Short isolated state rail and expose source diagnostic port')
    parser.add_argument('--offset-module',action='store_true')
    parser.add_argument('--offset-switch-width-scale',type=float,choices=[.5,1],default=1)
    parser.add_argument('--offset-short-split',action='store_true',help='Four MIM offset bank with0.28um TGs and separate bottom-plate use controls')
    parser.add_argument('--offset-isolate-routes',action='store_true')
    parser.add_argument('--offset-reverse-cap-plates',action='store_true')
    parser.add_argument('--offset-dummy-bottom',action='store_true')
    parser.add_argument('--offset-split-sample',action='store_true')
    parser.add_argument('--offset-sample-dummy-bottom',action='store_true')
    parser.add_argument('--offset-sample-dummy-nwidth-um',type=float,choices=[.25,.33,.5],default=.5)
    parser.add_argument('--offset-sample-clock-trim-um',type=float,choices=[0,1,2,4],default=0)
    parser.add_argument('--offset-sample-clock-trim-net',choices=['SAMPLEB','SAMPLE'],default='SAMPLEB')
    args=parser.parse_args()
    if args.encoder_grounded and not (args.encoder_feedback_module or args.encoder_mirrored_feedback or args.pmos_bias_reference or args.encoder_peak_detector):
        raise ValueError('grounded encoder variant requires encoder or bias module')
    if args.encoder_source_lifted and not (args.encoder_grounded and (args.encoder_feedback_module or args.encoder_mirrored_feedback)):
        raise ValueError('Lifted NF source requires grounded encoder feedback variant')
    if args.encoder_width_scale!=1 and not args.encoder_source_lifted:
        raise ValueError('Encoder width scale requires lifted source variant')
    if args.encoder_export_mirror_nodes and not args.encoder_mirrored_feedback:
        raise ValueError('Mirror observer ports require mirrored feedback')
    if args.encoder_peak_detector and (not args.encoder_grounded or args.encoder_mirrored_feedback or args.encoder_feedback_module or args.pmos_bias_reference or args.offset_module or args.shielded):
        raise ValueError('Peak detector is a separate grounded macro')
    if args.encoder_peak_threshold_scale!=1 and not args.encoder_peak_detector:
        raise ValueError('Threshold scale requires separate peak detector')
    if args.encoder_peak_hysteresis and not args.encoder_peak_detector:
        raise ValueError('Hysteresis requires separate peak detector')
    if args.offset_switch_width_scale!=1 and (not args.offset_reverse_cap_plates or args.offset_sample_dummy_bottom or args.offset_dummy_bottom or args.offset_split_sample):
        raise ValueError('scaled switches require reversed isolated macro without experimental dummy/sample controls')
    if args.offset_sample_clock_trim_net!='SAMPLEB' and not args.offset_sample_clock_trim_um:
        raise ValueError('trim polarity requires nonzero trim length')
    if args.offset_sample_clock_trim_um and (not args.offset_sample_dummy_bottom or args.offset_sample_dummy_nwidth_um!=.5):
        raise ValueError('clock trim requires default-width calibration dummy')
    if args.offset_sample_dummy_nwidth_um!=.5 and not args.offset_sample_dummy_bottom:
        raise ValueError('sample dummy width requires calibration dummy')
    if args.offset_sample_dummy_bottom and (not args.offset_reverse_cap_plates or args.offset_dummy_bottom or args.offset_split_sample):
        raise ValueError('sample dummy requires reversed unsplit macro without use dummy')
    if args.offset_split_sample and (not args.offset_reverse_cap_plates or args.offset_dummy_bottom):
        raise ValueError('split sample requires reversed offset without dummy')
    if args.offset_short_split and not args.offset_module:
        raise ValueError('short split variant requires offset module')
    if args.offset_isolate_routes and not args.offset_short_split:
        raise ValueError('isolated routing requires short split module')
    if args.offset_reverse_cap_plates and not args.offset_isolate_routes:
        raise ValueError('reversed plates require isolated offset routing')
    if args.offset_dummy_bottom and not args.offset_reverse_cap_plates:
        raise ValueError('bottom dummy requires reversed isolated offset macro')
    if args.offset_module:
        if args.shielded:
            raise ValueError('offset module is a separate cell')
        CELL='gf180_offset_subtractor';OUT=flow.BASE/'layout'/CELL
        PORTS=['CAL_IN','REF_IN','HELD_IN','OUT','VDD','VSS','SAMPLE','SAMPLEB','USE','USEB','TOP','BOTTOM']
        if args.offset_short_split:
            CELL='gf180_offset_subtractor_short_split4';OUT=flow.BASE/'layout'/CELL
            if args.offset_isolate_routes:
                CELL+='_isolated';OUT=flow.BASE/'layout'/CELL
            if args.offset_reverse_cap_plates:
                CELL+='_reversed';OUT=flow.BASE/'layout'/CELL
            if args.offset_dummy_bottom:
                CELL+='_dummybottom';OUT=flow.BASE/'layout'/CELL
            if args.offset_sample_dummy_bottom:
                CELL+='_sampledummybottom';OUT=flow.BASE/'layout'/CELL
                if args.offset_sample_dummy_nwidth_um!=.5:
                    CELL+='_nf'+f'{args.offset_sample_dummy_nwidth_um:g}'.replace('.','p');OUT=flow.BASE/'layout'/CELL
            if args.offset_sample_clock_trim_um:
                CELL+='_clocktrim'+f'{args.offset_sample_clock_trim_um:g}'+('_sample' if args.offset_sample_clock_trim_net=='SAMPLE' else '');OUT=flow.BASE/'layout'/CELL
            if args.offset_switch_width_scale!=1:
                CELL+='_halfswitch';OUT=flow.BASE/'layout'/CELL
            PORTS+=['USEBOTTOM','USEBOTTOMB']
            if args.offset_split_sample:
                CELL+='_splitsample';OUT=flow.BASE/'layout'/CELL
                PORTS+=['SAMPLEBOTTOM','SAMPLEBOTTOMB']
        DEVICES=[]
        for name,left,right,en,enb in [('sampletop','TOP','CAL_IN','SAMPLE','SAMPLEB'),
                                     ('samplebottom','BOTTOM','REF_IN','SAMPLE','SAMPLEB'),
                                     ('usetop','TOP','HELD_IN','USE','USEB'),
                                     ('usebottom','BOTTOM','OUT','USE','USEB')]:
            if args.offset_short_split and name=='usebottom':
                en,enb='USEBOTTOM','USEBOTTOMB'
            if args.offset_split_sample and name=='samplebottom':
                en,enb='SAMPLEBOTTOM','SAMPLEBOTTOMB'
            length=.28 if args.offset_short_split else 1
            DEVICES += [(name+'n','nfet',args.offset_switch_width_scale,length,[left,en,right,'VSS']),
                        (name+'p','pfet',2*args.offset_switch_width_scale,length,[left,enb,right,'VDD'])]
        if args.offset_dummy_bottom:
            DEVICES += [('dummyn','nfet',.5,.28,['BOTTOM','USEBOTTOMB','BOTTOM','VSS']),
                        ('dummyp','pfet',1,.28,['BOTTOM','USEBOTTOM','BOTTOM','VDD'])]
        if args.offset_sample_dummy_bottom:
            DEVICES += [('dummyn','nfet',args.offset_sample_dummy_nwidth_um,.28,['BOTTOM','SAMPLEB','BOTTOM','VSS']),
                        ('dummyp','pfet',2*args.offset_sample_dummy_nwidth_um,.28,['BOTTOM','SAMPLE','BOTTOM','VDD'])]
    if args.encoder_feedback_module:
        if args.offset_module or args.shielded:
            raise ValueError('encoder feedback is a separate macro')
        CELL='gf180_complementary_encoder_feedback';OUT=flow.BASE/'layout'/CELL
        PORTS=['SUM','ENC','VSPAN','VSS']
        DEVICES=[('feedbackn','nfet',1,1,['SUM','ENC','VSS','VSS']),
                 ('feedbackp','pfet',2,1,['SUM','ENC','VSPAN','VSPAN'])]
    if args.encoder_mirrored_feedback:
        if args.offset_module or args.shielded or args.encoder_feedback_module or args.pmos_bias_reference:
            raise ValueError('mirrored feedback is a separate macro')
        CELL='gf180_mirrored_encoder_feedback';OUT=flow.BASE/'layout'/CELL
        PORTS=['SUM','ENC','VSPAN','VSS','VDD']
        DEVICES=[('feedbackn','nfet',1,1,['PMIR','ENC','VSS','VSS']),
                 ('pdiode','pfet',2,1,['PMIR','PMIR','VDD','VDD']),
                 ('pmirror','pfet',2,1,['SUM','PMIR','VDD','VDD']),
                 ('feedbackp','pfet',2,1,['NMIR','ENC','VSPAN','VSPAN']),
                 ('ndiode','nfet',1,1,['NMIR','NMIR','VSS','VSS']),
                 ('nmirror','nfet',1,1,['SUM','NMIR','VSS','VSS'])]
    if args.pmos_bias_reference:
        if args.offset_module or args.shielded or args.encoder_feedback_module:
            raise ValueError('PMOS bias reference is a separate macro')
        CELL='gf180_pmos_bias_reference';OUT=flow.BASE/'layout'/CELL
        PORTS=['BIAS','VDD']
        DEVICES=[('biasref','pfet',20,2,['BIAS','BIAS','VDD','VDD'])]
    if args.encoder_grounded:
        CELL+='_grounded';OUT=flow.BASE/'layout'/CELL
        if 'VSS' not in PORTS:PORTS.append('VSS')
    if args.encoder_source_lifted:
        CELL+='_source_lifted';OUT=flow.BASE/'layout'/CELL
        PORTS.append('VLOW')
        DEVICES=[(name,f,w,l,[nodes[0],nodes[1],'VLOW',nodes[3]] if name=='feedbackn' else nodes)
                 for name,f,w,l,nodes in DEVICES]
    if args.encoder_width_scale!=1:
        CELL+=f'_w{args.encoder_width_scale}';OUT=flow.BASE/'layout'/CELL
        DEVICES=[(name,f,w*args.encoder_width_scale if name in ('feedbackn','feedbackp') else w,l,nodes)
                 for name,f,w,l,nodes in DEVICES]
    if args.encoder_isolate_held_gate and not args.encoder_mirrored_feedback:
        raise ValueError('Held-gate route isolation requires mirrored encoder')
    if args.encoder_isolate_held_gate:
        CELL+='_isolated_enc';OUT=flow.BASE/'layout'/CELL
    if args.encoder_isolate_mirror_drains:
        if not args.encoder_isolate_held_gate:raise ValueError('Mirror-drain isolation requires isolated held gate')
        CELL=f'gf180_encoder_w{args.encoder_width_scale}_isolated_enc_sum';OUT=flow.BASE/'layout'/CELL
    if args.encoder_export_mirror_nodes:
        CELL+='_observer_ports';OUT=flow.BASE/'layout'/CELL
        PORTS+=['PMIR','NMIR']
    if args.encoder_peak_detector:
        CELL=f'gf180_encoder_peak_detector_scale{args.encoder_peak_detector}';OUT=flow.BASE/'layout'/CELL
        if args.encoder_peak_threshold_scale!=1:
            CELL+='_threshold'+f'{args.encoder_peak_threshold_scale:g}'.replace('.','p');OUT=flow.BASE/'layout'/CELL
        if args.encoder_peak_hysteresis:
            CELL+='_hysteresis';OUT=flow.BASE/'layout'/CELL
        PORTS=['PMIR','NMIR','BIAS','EN','ENB','VDD','VSS']
        DEVICES=[('pdetect','pfet',2,1,['ndetect','PMIR','VDD','VDD']),
                 ('ndiag','nfet',1,1,['ndetect','ndetect','VSS','VSS']),
                 ('ncopy','nfet',1,1,['peak','ndetect','VSS','VSS']),
                 ('ndetect','nfet',1,1,['peak','NMIR','VSS','VSS']),
                 ('pref','pfet',.2*args.encoder_peak_detector*args.encoder_peak_threshold_scale,1,['peak','BIAS','VDD','VDD']),
                 ('ninv','nfet',1,1,['EN','peak','VSS','VSS']),
                 ('pinv','pfet',2,1,['EN','peak','VDD','VDD']),
                 ('ninvb','nfet',1,1,['ENB','EN','VSS','VSS']),
                 ('pinvb','pfet',2,1,['ENB','EN','VDD','VDD'])]
        if args.encoder_peak_hysteresis:
            DEVICES += [('phystref','pfet',.2*args.encoder_peak_detector*args.encoder_peak_threshold_scale,1,['hystmid','BIAS','VDD','VDD']),
                        ('phystswitch','pfet',2,1,['peak','EN','hystmid','VDD'])]
    if args.shielded:
        CELL += '_shielded';OUT=flow.BASE/'layout'/CELL
        PORTS=PORTS+['source']
    OUT.mkdir(parents=True,exist_ok=True);flow.OUT=OUT
    tcl=['load gf180_sensor_raw']+[f'magic::gencell gf180mcu::{f}_03v3 {n} -spice w {w}u l {l}u nf 1' for n,f,w,l,_ in DEVICES]+['writeall force','quit -noprompt','']
    (OUT/'generation.log').write_text(flow.magic('\n'.join(tcl)))
    nets=PORTS if args.offset_module or args.encoder_grounded else (PORTS if args.shielded else PORTS+['source'])
    if args.encoder_mirrored_feedback:nets=PORTS+[net for net in ['PMIR','NMIR'] if net not in PORTS]
    if args.encoder_peak_detector:nets=PORTS+['ndetect','peak']
    if args.encoder_peak_hysteresis:nets.append('hystmid')
    tracks={n:(5000 if args.offset_module else 2200)+160*i for i,n in enumerate(nets)};layers={}
    if args.encoder_isolate_held_gate:
        tracks['ENC']=5200
    if args.encoder_isolate_mirror_drains:
        tracks['SUM']=-4000
    if args.offset_isolate_routes:
        tracks['TOP']=9000;tracks['BOTTOM']=9600
    if args.shielded:
        tracks['STATE']=800
    for i,(_,family,w,l,connections) in enumerate(DEVICES):
        candidates=[p for p in OUT.glob(f'{family}_03v3_*.mag') if f'string parameters w {float(w)} l {float(l)} ' in p.read_text()]
        if not candidates:
            raise RuntimeError('sensor PCell missing')
        p=max(candidates,key=lambda p:p.stat().st_mtime);dx=2000*i
        for layer,rs in rectangles(p,0).items():
            layers.setdefault(layer,[]).extend((x1+dx,y1,x2+dx,y2) for x1,y1,x2,y2 in rs)
        half_l=int(l*100)
        for (x,y),net in zip([(half_l+52,0),(-half_l-52,0),(0,int(w*100)),(-half_l-190,0)],
                              [connections[0],connections[2],connections[1],connections[3]]):
            x+=dx;track=tracks[net];top=y+79 if y else y+38
            layers.setdefault('metal1',[]).append((x-38,y-38,x+38,top))
            layers.setdefault('via1',[]).append((x-26,y-26,x+26,y+26))
            layers.setdefault('metal2',[]).append((x-38,min(y-38,track-38),x+38,max(top,track+38)))
            layers.setdefault('via2',[]).append((x-26,track-26,x+26,track+26))
    for net,track in tracks.items():
        xmax=(42600 if args.offset_short_split else 24600) if args.offset_module else (400 if args.shielded and net=='STATE' else 4600)
        if args.offset_isolate_routes and net not in ['TOP','BOTTOM','VSS']:
            xmax=20200 if args.offset_dummy_bottom or args.offset_sample_dummy_bottom else 16200
        if args.encoder_mirrored_feedback:xmax=12200
        if args.encoder_peak_detector:xmax=(len(DEVICES)-1)*2000+600
        layers.setdefault('metal3',[]).append((-600,track-38,xmax,track+38))
    if args.encoder_grounded:
        tapx=2000*len(DEVICES)+2000
        layers.setdefault('pwell',[]).append((tapx-180,-200,tapx+180,200))
        layers.setdefault('psubdiff',[]).append((tapx-36,-100,tapx+36,100))
        layers.setdefault('psubdiffcont',[]).append((tapx-23,-87,tapx+23,87))
        layers.setdefault('metal1',[]).append((tapx-38,-98,tapx+38,98))
        layers.setdefault('via1',[]).append((tapx-26,-26,tapx+26,26))
        y=tracks['VSS']
        layers.setdefault('metal2',[]).append((tapx-38,-38,tapx+38,y+38))
        layers.setdefault('via2',[]).append((tapx-26,y-26,tapx+26,y+26))
        layers.setdefault('metal3',[]).append((-600,y-38,tapx+38,y+38))
    if args.encoder_isolate_held_gate:
        # Separate held ENC rail from switched SUM; connect a VSS guard below ENC.
        guard_y=5000;x=-500
        layers.setdefault('metal2',[]).append((x-38,tracks['VSS']-38,x+38,guard_y+38))
        for y in [tracks['VSS'],guard_y]:
            layers.setdefault('via2',[]).append((x-26,y-26,x+26,y+26))
        layers.setdefault('metal3',[]).append((-600,guard_y-38,12200,guard_y+38))
    if args.encoder_isolate_mirror_drains:
        guard_y=-3800;x=-500
        layers.setdefault('metal2',[]).append((x-38,guard_y-38,x+38,tracks['VSS']+38))
        for y in [tracks['VSS'],guard_y]:layers.setdefault('via2',[]).append((x-26,y-26,x+26,y+26))
        layers.setdefault('metal3',[]).append((-600,guard_y-38,12200,guard_y+38))
    if args.offset_isolate_routes:
        layers.setdefault('metal2',[]).append((-538,tracks['VSS']-38,-462,9798))
        for y in [tracks['VSS'],8840,9760]:
            layers.setdefault('via2',[]).append((-526,y-26,-474,y+26))
        for y in [8840,9760]:
            layers.setdefault('metal3',[]).append((-600,y-38,42600,y+38))
    if args.offset_sample_clock_trim_um:
        # Connected complementary-clock fringe finger; native grid 0.005um.
        x=-100;y=9440;clock_y=tracks[args.offset_sample_clock_trim_net]
        layers.setdefault('metal2',[]).append((x-38,clock_y-38,x+38,y+38))
        for cy in [clock_y,y]:
            layers.setdefault('via2',[]).append((x-26,cy-26,x+26,cy+26))
        layers.setdefault('metal3',[]).append((x-38,y-38,x+round(args.offset_sample_clock_trim_um*200),y+38))
    if args.offset_module:
        cap=flow.BASE/'layout/gf180_mim_22x22/gf180_mim_22x22.mag'
        local=rectangles(cap,0)
        count=4 if args.offset_short_split else 1
        for j in range(count):
            dx=20000+6000*j
            for layer,rs in local.items():
                layers.setdefault(layer,[]).extend((x1+dx,y1,x2+dx,y2) for x1,y1,x2,y2 in rs)
            tap=max(r[2] for r in local['metal1'])-38+dx
            layers.setdefault('via1',[]).append((tap-26,-26,tap+26,26))
            layers.setdefault('metal2',[]).append((tap-38,-38,tap+38,tracks['VSS']+38))
            layers.setdefault('via2',[]).append((tap-26,tracks['VSS']-26,tap+26,tracks['VSS']+26))
        bottom_x=24000+6000*(count-1)
        top_net='BOTTOM' if args.offset_reverse_cap_plates else 'TOP'
        bottom_net='TOP' if args.offset_reverse_cap_plates else 'BOTTOM'
        # A straight M5 bus through the row shorts native bottom-plate via4 stripes.
        # Route the top plate outside the row, with one branch in each inter-cap gap.
        layers.setdefault('metal5',[]).append((16940,-60,19940,60))
        if count>1:
            layers.setdefault('metal5',[]).extend([(16940,-3060,35060,-2940),(16940,-3060,17060,60)])
            for j in range(1,count):
                x=17000+6000*j
                layers.setdefault('metal5',[]).extend([(x-60,-3060,x+60,60),(x-60,-60,x+2940,60)])
        layers.setdefault('via4',[]).append((16956,-44,17044,44))
        layers.setdefault('metal4',[]).extend([(16940,-60,17060,60),(16962,-38,17038,tracks[top_net]+38),
                                              (22280,-38,bottom_x+38,38),(bottom_x-38,-38,bottom_x+38,tracks[bottom_net]+38)])
        for x,net in [(17000,top_net),(bottom_x,bottom_net)]:
            y=tracks[net];layers.setdefault('via3',[]).append((x-26,y-26,x+26,y+26))
            layers.setdefault('metal4',[]).append((x-38,y-38,x+38,y+38))
    lines=['magic','tech gf180mcuD','magscale 1 10','timestamp 0']
    for layer,rs in layers.items():
        lines += [f'<< {layer} >>']+['rect '+' '.join(map(str,r)) for r in rs]
    lines += ['<< labels >>']
    for i,net in enumerate(PORTS,1):
        y=tracks[net];lines += [f'rlabel metal3 s -600 {y-20} -540 {y+20} 4 {net}',f'port {i} nsew']
    lines += ['<< end >>',''];(OUT/f'{CELL}.mag').write_text('\n'.join(lines),encoding='ascii')
    log=flow.magic(f'load {CELL}\ndrc check\ndrc count\ndrc listall why\nextract all\nfeedback save warnings.feedback\next2spice lvs\next2spice scale off\next2spice -o {CELL}.spice\ngds write {CELL}.gds\nselect top cell\nputs "BBOX [box values]"\nquit -noprompt\n')
    (OUT/'extraction.log').write_text(log)
    drc=re.search(r'Total DRC errors found:\s*(\d+)',log)
    if not drc or int(drc.group(1)):
        raise RuntimeError(log[-4000:])
    ref=['.subckt reference '+' '.join(PORTS)]
    ref += [f'X{n} '+' '.join(connections)+f' {f}_03v3 w={w}u l={l}u' for n,f,w,l,connections in DEVICES]
    if args.offset_module:
        plates='BOTTOM TOP' if args.offset_reverse_cap_plates else 'TOP BOTTOM'
        ref += [f'Xcap{i} {plates} cap_mim_2f0_m4m5_noshield c_width=22u c_length=22u' for i in range(4 if args.offset_short_split else 1)]
    ref += ['.ends',''];(OUT/'reference.spice').write_text('\n'.join(ref))
    lvs=flow.run(['netgen-lvs','-batch','lvs',f'{CELL}.spice {CELL}','reference.spice reference',f'/workspace/{flow.PDK.relative_to(flow.ROOT).as_posix()}/libs.tech/netgen/gf180mcuD_setup.tcl','lvs.out'])
    (OUT/'netgen.log').write_text(lvs)
    if 'Circuits match uniquely' not in lvs:
        raise RuntimeError(lvs[-3000:])
    caplog=flow.magic(f'load {CELL}\nextract do capacitance\nextract all\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {CELL}_cap.spice\nquit -noprompt\n')
    (OUT/'capacitance_extraction.log').write_text(caplog)
    capnet=(OUT/f'{CELL}_cap.spice').read_text()
    feedback=(OUT/'warnings.feedback').read_text()
    if args.encoder_grounded and ('VSUBS' in capnet or '**FLOATING' in capnet):
        raise RuntimeError('Grounded encoder must have no floating substrate/conductor')
    expected_dummy_feedback=False
    if args.offset_dummy_bottom or args.offset_sample_dummy_bottom:
        nw=args.offset_sample_dummy_nwidth_um if args.offset_sample_dummy_bottom else .5
        pw=2*nw
        expected=(f'box 17972 {-round(pw*100)} 18028 {round(pw*100)}\nfeedback add "device missing 1 terminal;\n connecting remainder to node BOTTOM" pale\n'
                  f'box 15972 {-round(nw*100)} 16028 {round(nw*100)}\nfeedback add "device missing 1 terminal;\n connecting remainder to node BOTTOM" pale\n')
        clock='SAMPLE' if args.offset_sample_dummy_bottom else 'USEBOTTOM'
        shorted=[line for line in capnet.splitlines() if re.match(r'^X\S+ BOTTOM '+clock+r'B? BOTTOM (?:VSS|VDD) ',line)]
        expected_dummy_feedback=(feedback==expected and len(shorted)==2 and
            any('nfet_03v3' in line and f'w={nw:g}u l=0.28u' in line for line in shorted) and
            any('pfet_03v3' in line and f'w={pw:g}u l=0.28u' in line for line in shorted))
        if not expected_dummy_feedback:
            raise RuntimeError('dummy terminal/feedback audit failed')
    report={'cell':CELL,'magic_drc_count':0,'lvs_unique':True,'ports':PORTS,
            'bbox_um':[int(v)*0.005 for v in re.search(r'BBOX ([-0-9 ]+)',log).group(1).split()],
            'capacitance_entries':len(re.findall(r'(?m)^C\S+',capnet)),
            'extraction_feedback':feedback,'physical_state_accepted':False,
            'intentional_dummy_terminal_merge_verified':expected_dummy_feedback,
            'offset_switch_width_scale':args.offset_switch_width_scale,
            'offset_split_sample_controls':args.offset_split_sample,
            'offset_sample_dummy_bottom':args.offset_sample_dummy_bottom,
            'offset_sample_clock_trim_um':args.offset_sample_clock_trim_um,
            'offset_sample_clock_trim_net':args.offset_sample_clock_trim_net,
            'calibration_dummy_nf_width_um':args.offset_sample_dummy_nwidth_um if args.offset_sample_dummy_bottom else None,
            'scope':'Routed1/1um permanent source follower and1/1um NF,2/1um PF output selection, separate from stored gate cell. No resistance extraction, read current/park controls, noise, mismatch, qualified gate leakage, restore/encode or model/service acceptance.',
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/f'{CELL}.mag',OUT/f'{CELL}.gds',OUT/f'{CELL}.spice',OUT/f'{CELL}_cap.spice']}}
    if args.offset_module:
        report['scope']='Combined routed four1um TGs and grounded-substrate22um MIM floating offset storage/plate-switch subtraction. External calibration/reference/held-sample signals, control drivers, output load, resistance extraction, switched noise/mismatch, restore accuracy and complete model/service unqualified.'
        if args.offset_short_split:
            report['scope']='Combined routed four0.28um TGs and four grounded-substrate22um MIM caps in parallel with separate bottom-plate use controls. Prototype layout, not array density. External signal/reference/control drivers, RPEX, sampled noise, restore accuracy and complete model/service unqualified.'
        if args.offset_isolate_routes:
            report['scope']+=' Shortened clock rails, separated TOP/BOTTOM routes and connected VSS guard rails; parasitic reduction and functional effect require extracted simulation.'
        if args.offset_reverse_cap_plates:
            report['scope']+=' Native MIM bottom plate connects logical driven TOP; low substrate-coupling native top plate connects floating reference BOTTOM. Functional effect requires simulation; no accuracy acceptance.'
        if args.offset_split_sample:
            report['scope']+=' Separately routed calibration-bottom sample controls allow measured switch-order experiments; same four MIMs/eight MOS, no software offset or charge correction. Timing/charge injection/noise require qualification.'
        if args.offset_dummy_bottom or args.offset_sample_dummy_bottom:
            phase='calibration-sample' if args.offset_sample_dummy_bottom else 'bottom-use'
            report['scope']+=f' {nw:g}/0.28um NF and{pw:g}/0.28um PF dummy switches have D/S shorted to floating BOTTOM and complementary{phase} gates. Physical charge compensation candidate, not demonstrated accuracy.'
            report['scope']+=' Two exact missing-terminal boxes correspond to intentional dummy D/S merges; extracted connectivity/dimensions and unique LVS verified. Warnings retained; diffusion parameters unchanged.'
    if args.encoder_feedback_module:
        report['scope']='Routed complementary nonlinear feedback pair, NF1/1um to VSS and PF2/1um with source/body tied to VSPAN. Common gates ENC and common drains SUM. Independent regulated VSPAN source, OTA feedback, compensation, encoder transfer/noise/PVT/mismatch and complete SNN update unqualified; capacitance extraction only.'
        report['device_count']=2
    if args.encoder_mirrored_feedback:
        report['scope']='Six-MOS nonlinear feedback with PF mirror injecting NF-encoded current into SUM and NF mirror sinking PF-encoded current. ENC gates the fixed-source NF/PF encoder pair; current mirrors isolate its drains from SUM. VDD/VSPAN references, amplifier polarity, loop compensation, transfer/noise/PVT and full model service unqualified; capacitance extraction only.'
        report['device_count']=6
    if args.pmos_bias_reference:
        report['scope']='Routed diode-connected PF20/2um bias reference, source/body VDD, drain/gate BIAS. External reference-current source, source noise, PVT/mismatch and assembled encoder unqualified; capacitance extraction only.'
        report['device_count']=1
    if args.encoder_grounded:
        report['scope']+=' Explicit routed PSUB tap to VSS; unused internal source rail omitted. No VSUBS or FLOATING capacitance nodes allowed.'
    if args.encoder_source_lifted:
        report['scope']+=' Encoded NF source moves to external VLOW, with body still VSS; other NF mirror sources stay VSS. Physical source elevation intended to preserve output swing at smaller reference current, not qualified companding/precision. VLOW generator/body effect/noise/settling require simulation.'
    report['encoder_isolate_mirror_drains']=args.encoder_isolate_mirror_drains
    if args.encoder_isolate_mirror_drains:report['scope']+=' SUM M3 rail at-20um with connected VSS guard at-19um separates switched output drains from held ENC/mirror-reference rails; extracted capacitance and functional effect require measurement.'
    report['encoder_isolate_held_gate']=args.encoder_isolate_held_gate
    if args.encoder_isolate_held_gate:
        report['scope']+=' ENC M3 rail separated to26um with connected VSS guard at25um; actual capacitance and transfer/mode disturbance require extraction and simulation, not inferred shielding acceptance.'
    report['encoder_width_scale']=args.encoder_width_scale
    if args.encoder_export_mirror_nodes:
        report['scope']+=' PMIR/NMIR rails exposed as actual macro ports for a physical observer; observer loading/control require assembled simulation.'
    if args.encoder_peak_detector:
        report['scope']=f'{len(DEVICES)} physical MOS: PF replica observes PMIR and NF diode/mirror sinks its magnitude; NF replica observes NMIR and adds the opposite magnitude. Physical PF threshold source driven by BIAS competes at peak node, followed by two complementary inverters EN/ENB. No ideal current threshold or command-derived control source. Approximate threshold uses same PF bias family; switching threshold, chatter/settling/load/noise/mismatch/PVT and assembled controller unqualified; capacitance extraction only.'
        report['device_count']=len(DEVICES)
        report['threshold_nominal_na_at_1ua_bias']=20*args.encoder_peak_detector*args.encoder_peak_threshold_scale
        if args.encoder_peak_hysteresis:
            report['scope']+=' Additional matched PF reference and EN-controlled PF switch add threshold current while EN is low. Nominal turn-on threshold doubles, turn-off retains base threshold; actual levels/hysteresis/chatter require measurement.'
    if args.encoder_width_scale!=1:
        report['scope']+=f' Encoded NF/PF widths scaled{args.encoder_width_scale}x; reference diode pair shares scaled geometry. Four feedback mirror devices retain original1/2um widths. Matching current/reference scaling, MOS model-bin changes, capacitance/noise/power/loop stability require measurement.'
    if args.offset_switch_width_scale!=1:
        report['scope']+=' All four plate TG widths halved to0.5um NF/1um PF, L0.28um; extracted settling, charge transfer and noise require qualification.'
    if args.offset_sample_clock_trim_um:
        report['scope']+=f' Connected{args.offset_sample_clock_trim_net} M3 fringe finger of{args.offset_sample_clock_trim_um:g}um near BOTTOM; compensation/noise/PVT effect unqualified.'
    (OUT/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if feedback and not expected_dummy_feedback:
        raise RuntimeError('sensor extraction feedback requires review')


if __name__=='__main__':
    main()
