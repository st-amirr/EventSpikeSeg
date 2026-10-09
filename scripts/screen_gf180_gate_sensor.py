"""Bound a permanently attached MOS gate sensor with extracted state/access and output TG."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corner',choices=['typical','ff','ss'],default='typical')
    parser.add_argument('--temp-c',type=float,default=27)
    parser.add_argument('--offset-mv',type=float,default=750)
    parser.add_argument('--sensor-w-um',type=float,choices=[0.5,1,2],default=1)
    parser.add_argument('--read-ua',type=float,choices=[0.1,1,5],default=1)
    parser.add_argument('--no-read',action='store_true')
    parser.add_argument('--physical-sensor',action='store_true')
    parser.add_argument('--small-load',action='store_true',help='Use extracted7x7um MIM rather than22x22um')
    parser.add_argument('--read-cycles',type=int,choices=[1,3],default=1)
    parser.add_argument('--shielded-sensor',action='store_true')
    parser.add_argument('--physical-park',action='store_true')
    parser.add_argument('--cycle-gap-us',type=float,choices=[4,5000],default=4)
    args=parser.parse_args()
    if not 0<args.offset_mv<=750:
        raise ValueError('offset outside range')
    stem=f'gf180_gate_sensor_{args.corner}_temp{args.temp_c:g}_offset{args.offset_mv:g}mv_w{args.sensor_w_um:g}_read{args.read_ua:g}ua'
    if args.no_read:
        stem += '_control'
    if args.physical_sensor:
        if args.sensor_w_um != 1:
            raise ValueError('physical sensor width is1um')
        stem += '_physicalsensor'
    if args.shielded_sensor:
        if not args.physical_sensor:
            raise ValueError('shielded sensor requires physical sensor')
        stem += '_shielded'
    if args.small_load:
        stem += '_smallload'
    if args.physical_park:
        stem += '_physicalpark'
    if args.read_cycles != 1:
        stem += f'_cycles{args.read_cycles}'
        if args.cycle_gap_us != 4:
            stem += f'_gap{args.cycle_gap_us:g}us'
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    cell=BASE/'layout/gf180_gate_state_cell/gf180_gate_state_cell_cap.spice'
    switch=BASE/'layout/gf180_fixed_body_tg/gf180_fixed_body_tg_cap.spice'
    capcell='gf180_mim_7x7' if args.small_load else 'gf180_mim_22x22'
    cap=BASE/f'layout/{capcell}/{capcell}_cap.spice'
    sensorcell='gf180_gate_sensor_shielded' if args.shielded_sensor else 'gf180_gate_sensor'
    sensor=BASE/f'layout/{sensorcell}/{sensorcell}_cap.spice'
    deck=BASE/f'benches/{stem}.spice'
    lines=['GF180 permanent gate source-follower sensing screen',f'.include {prefix}/design.spice',
           '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice {args.corner}',
           f'.lib {prefix}/sm141064.spice mimcap_typical',f'.temp {args.temp_c:g}',
           '.options gmin=1e-18 reltol=1e-6 abstol=1e-16 vntol=1e-10',
           *cell.read_text().splitlines(),*switch.read_text().splitlines(),*cap.read_text().splitlines(),
           'Vdd vdd 0 3.3','Vcm vcm 0 1.65','Vpre pre 0 1',
           '.model ideal_phase SW(Ron=10 Roff=1e30 Vt=1.65 Vh=0.1)',
           'Vinit init 0 PWL(0 3.3 0.99u 3.3 1u 0 5.01m 0)']
    if args.no_read:
        lines += ['Vread read 0 0','Vreadb readb 0 3.3','Vpark park 0 3.3']
    else:
        lines += ['Vread read 0 PWL(0 0 4.99999m 0 5m 3.3 5.00199m 3.3 5.002m 0 5.01m 0)',
                  'Vreadb readb 0 PWL(0 3.3 4.99999m 3.3 5m 0 5.00199m 0 5.002m 3.3 5.01m 3.3)',
                  'Vpark park 0 PWL(0 3.3 4.99949m 3.3 4.9995m 0 5.00249m 0 5.0025m 3.3 5.01m 3.3)']
    if args.physical_sensor:
        lines += sensor.read_text().splitlines()
    for kind,sign in [('low',-1),('high',1),('zero',0)]:
        target=1.65+sign*args.offset_mv/1000
        width=args.sensor_w_um
        lines += [f'Vtarget_{kind} target_{kind} 0 {target:.12g}',
                  f'Sinit_{kind} target_{kind} state_{kind} init 0 ideal_phase',
                  f'Xcell_{kind} vcm state_{kind} 0 vdd 0 vdd gf180_gate_state_cell',
                  f'Xsensor_{kind} vdd state_{kind} source_{kind} 0 nfet_03v3 w={width:g}u l=1u as={0.44*width:g}p ad={0.44*width:g}p ps={2*width+0.88:g}u pd={2*width+0.88:g}u',
                  f'Xselect_{kind} source_{kind} bus_{kind} read readb 0 vdd gf180_fixed_body_tg',
                  f'Xload_{kind} bus_{kind} 0 0 {capcell}',
                  f'Spark_{kind} pre bus_{kind} park 0 ideal_phase']
        if args.physical_sensor:
            lines=[line for line in lines if not line.startswith(f'Xsensor_{kind} ') and not line.startswith(f'Xselect_{kind} ')]
            source_port=f' source_{kind}' if args.shielded_sensor else ''
            lines.append(f'Xsensor_{kind} state_{kind} bus_{kind} read readb vdd 0{source_port} {sensorcell}')
        if args.no_read:
            lines.append(f'Iread_{kind} bus_{kind} 0 0')
        else:
            lines.append(f'Iread_{kind} bus_{kind} 0 PWL(0 0 4.99999m 0 5m {args.read_ua:g}u 5.00199m {args.read_ua:g}u 5.002m 0 5.01m 0)')
    measure=[('initial','state','2u'),('held','state','4.998m'),('during','state','5.0019m'),
             ('after','state','5.003m'),('bus100n','bus','5.0001m'),('bus500n','bus','5.0005m'),
             ('bus1900n','bus','5.0019m'),('sourceheld','source','4.998m')]
    if args.physical_sensor and not args.shielded_sensor:
        measure=[item for item in measure if item[0]!='sourceheld']
    if args.read_cycles>1 and not args.no_read:
        def waveform(name,node,initial,events):
            return f'{name} {node} 0 PWL(0 {initial:g} '+' '.join(f'{t:.12g} {v:.12g}' for t,v in events)+')'
        reads=[];parks=[];currents=[]
        for cycle in range(args.read_cycles):
            t=0.005+cycle*args.cycle_gap_us*1e-6
            reads += [(t-1e-8,0),(t,3.3),(t+1.99e-6,3.3),(t+2e-6,0)]
            parks += [(t-0.51e-6,3.3),(t-0.5e-6,0),(t+2.49e-6,0),(t+2.5e-6,3.3)]
            currents += [(t-1e-8,0),(t,args.read_ua*1e-6),(t+1.99e-6,args.read_ua*1e-6),(t+2e-6,0)]
        lines=[line for line in lines if not line.startswith(('Vread ','Vreadb ','Vpark ','Iread_'))]
        lines += [waveform('Vread','read',0,reads),waveform('Vreadb','readb',3.3,[(t,3.3-v) for t,v in reads]),
                  waveform('Vpark','park',3.3,parks)]
        lines += [waveform(f'Iread_{kind}',f'bus_{kind}',0,currents) for kind in ['low','high','zero']]
        measure += [('final','state',f'{0.005+(args.read_cycles-1)*args.cycle_gap_us*1e-6+3e-6:.12g}')]
    if args.physical_park:
        parkline=next(line for line in lines if line.startswith('Vpark '))
        if args.no_read:
            lines.append('Vparkb parkb 0 0')
        else:
            numeric=parkline.split('PWL(')[1].rstrip(')').split()
            inverse=' '.join(value if i%2==0 else f'{3.3-float(value):.12g}' for i,value in enumerate(numeric))
            lines.append('Vparkb parkb 0 PWL('+inverse+')')
        for kind in ['low','high','zero']:
            lines.remove(f'Spark_{kind} pre bus_{kind} park 0 ideal_phase')
            lines.append(f'Xpark_{kind} pre bus_{kind} park parkb 0 vdd gf180_fixed_body_tg')
    stop=max(0.005015,0.005+(args.read_cycles-1)*args.cycle_gap_us*1e-6+4e-6)
    lines += ['.control','set numdgt=15',f'tran 500n {stop:.12g}']
    for kind in ['low','high','zero']:
        for name,node,time in measure:
            lines.append(f'meas tran {kind}_{name} find v({node}_{kind}) at={time}')
    lines += ['quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
                         '--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir',prefix,
                         '--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b',
                         '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/f'results/{stem}.log';logpath.write_text(log)
    values={k:float(v) for k,v in re.findall(r'(?m)^\s*((?:low|high|zero)_\w+)\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==3*len(measure)
    rows={kind:{name:values[f'{kind}_{name}'] for name,_,_ in measure} for kind in ['low','high','zero']} if complete else {}
    for row in rows.values():
        row['during_read_disturbance_mv']=(row['during']-row['held'])*1000
        row['post_read_disturbance_mv']=(row['after']-row['held'])*1000
        row['hold_drift_mv']=(row['held']-row['initial'])*1000
        row['bus_500ns_vs1900ns_uv']=(row['bus500n']-row['bus1900n'])*1e6
        if 'final' in row:
            row['final_after_repeated_reads_disturbance_mv']=(row['final']-row['held'])*1000
    report={'simulation_completed':complete,'corner':args.corner,'temperature_c':args.temp_c,
            'sensor_w_um':width,'sensor_l_um':1,'offset_mv':args.offset_mv,'ideal_read_current_ua':0 if args.no_read else args.read_ua,
            'read_disabled_control':args.no_read,'rows':rows,'physical_state_accepted':False,
            'physical_sensor':args.physical_sensor,'load_mim_cell':capcell,'read_cycles':args.read_cycles,
            'sensor_cell':sensorcell if args.physical_sensor else None,
            'physical_park_switch':args.physical_park,
            'cycle_gap_us':args.cycle_gap_us,
            'scope':'Extracted storage/access, output-select TG and MIM load. Permanently attached schematic source-follower uses official NF model and assumed diffusion geometry; no sensor layout or combined routing. Ideal current/supply/park/program/phase sources. Deterministic gate/source feedthrough screen, no noise/mismatch/gate leakage, nonlinear encoding, full PLIF or5ms population service qualification.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),cell,switch,cap,deck,logpath,modeldir/'design.spice',modeldir/'sm141064.spice',modeldir/'sm141064_mim.spice']}}
    if args.physical_sensor:
        report['sha256'][sensor.relative_to(ROOT).as_posix()]=hashlib.sha256(sensor.read_bytes()).hexdigest()
        report['scope']='Separately extracted storage/access, permanently attached source-follower/output-select macro and grounded MIM bus load. No combined sensor/storage routing or resistance extraction. Ideal read current/supply/park/program/phase sources. Deterministic gate feedthrough only; no sampled noise, mismatch, gate-leakage coverage, encode/restore, full PLIF/model/service acceptance.'
    if args.physical_park:
        report['scope'] += ' Bus park uses a separately extracted fixed-body TG; park voltage/control remain ideal.'
    (BASE/f'results/{stem}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not complete:
        raise RuntimeError(log[-2200:])


if __name__=='__main__':
    main()
