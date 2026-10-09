"""Native3.3V GF180 two-stage shared OTA: closed-loop settling and noise."""
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
    parser.add_argument('--bias-v',type=float,default=0.8)
    parser.add_argument('--comp-pf',type=float,default=1)
    parser.add_argument('--reference-ua',type=float,default=None)
    args=parser.parse_args()
    if not 0.65 <= args.bias_v <= 1.0 or not 0.2 <= args.comp_pf <= 5:
        raise ValueError('bias/compensation outside bounded screen')
    if args.reference_ua is not None and not 5 <= args.reference_ua <= 50:
        raise ValueError('reference current outside5..50uA screen')
    stem=f'gf180_shared_ota_{args.corner}_temp{args.temp_c:g}_bias{args.bias_v:g}_comp{args.comp_pf:g}pf'
    if args.reference_ua is not None:
        stem += f'_mirrorref{args.reference_ua:g}ua'
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    deck=BASE/f'benches/{stem}.spice'
    lines=['GF180 shared OTA unity feedback benchmark',f'.include {prefix}/design.spice',
           '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice {args.corner}',
           f'.temp {args.temp_c:g}', '.options gmin=1e-18 reltol=1e-6 abstol=1e-16 vntol=1e-10',
           'Vdd vdd 0 3.3',f'Vbias bias 0 {args.bias_v:g}',
           'Vref inp 0 DC 1.65 AC 1 PWL(0 1.65 0.999u 1.65 1u 1.651 4u 1.651 4.001u 1.65 6u 1.65 6.001u 1.75 10u 1.75)',
           'Xn1 mirror out tail 0 nfet_03v3 w=10u l=1u as=4.4p ad=4.4p ps=20.88u pd=20.88u',
           'Xn2 first inp tail 0 nfet_03v3 w=10u l=1u as=4.4p ad=4.4p ps=20.88u pd=20.88u',
           'Xt tail bias 0 0 nfet_03v3 w=10u l=2u as=4.4p ad=4.4p ps=20.88u pd=20.88u',
           'Xp1 mirror mirror vdd vdd pfet_03v3 w=20u l=1u as=8.8p ad=8.8p ps=40.88u pd=40.88u',
           'Xp2 first mirror vdd vdd pfet_03v3 w=20u l=1u as=8.8p ad=8.8p ps=40.88u pd=40.88u',
           'Xpout out first vdd vdd pfet_03v3 w=40u l=1u as=17.6p ad=17.6p ps=80.88u pd=80.88u',
           'Xnsink out bias 0 0 nfet_03v3 w=20u l=1u as=8.8p ad=8.8p ps=40.88u pd=40.88u',
           f'Ccomp first comp {args.comp_pf:g}p','Rcomp comp out 100','Cload out 0 100f',
           '.control','set numdgt=15','op','print v(out) v(first) v(tail) i(Vdd)',
           'noise v(out) Vref dec 60 10 100meg','print onoise_total inoise_total',
           'tran 2n 10u']
    for name,time in [('before','0.9u'),('s100n','1.1u'),('s500n','1.5u'),('s1u','2u'),('s2u','3u'),('large100n','6.101u'),('large500n','6.501u'),('large1u','7.001u'),('large3u','9.001u')]:
        lines.append(f'meas tran out_{name} find v(out) at={time}')
    lines+=['quit','.endc','.end']
    if args.reference_ua is not None:
        lines.remove(f'Vbias bias 0 {args.bias_v:g}')
        lines[lines.index('.control'):lines.index('.control')]=[
            f'Iref vdd bias {args.reference_ua:g}u',
            'Xref bias bias 0 0 nfet_03v3 w=10u l=2u as=4.4p ad=4.4p ps=20.88u pd=20.88u']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','3g','--cpus','2',
                         '--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir',prefix,
                         '--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b',
                         '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/f'results/{stem}.log';logpath.write_text(log)
    patterns=r'(?m)^\s*(onoise_total|inoise_total|out_\w+|v\(out\)|v\(first\)|v\(tail\)|i\(vdd\))\s*=\s*([-+0-9.eE]+)'
    values={k.lower():float(v) for k,v in re.findall(patterns,log,re.I)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==15
    result={'simulation_completed':complete,'corner':args.corner,'temperature_c':args.temp_c,
            'bias_v':args.bias_v,'compensation_pf':args.comp_pf,'values':values,
            'ideal_reference_current_ua':args.reference_ua,
            'physical_state_accepted':False,'scope':'Schematic shared OTA only: assumed diffusion areas, ideal bias/supply/compensation/load and unity-feedback input.10Hz..100MHz stationary noise. No input state loading, autozero, switched read/restore, resistor/capacitor layout, mismatch or full-float/service acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),deck,logpath,modeldir/'design.spice',modeldir/'sm141064.spice']}}
    (BASE/f'results/{stem}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if not complete:
        raise RuntimeError(log[-2500:])


if __name__=='__main__':
    main()
