"""Official local-mismatch screen of the routed permanent gate sensor."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=17)
    parser.add_argument('--samples',type=int,choices=[8,32],default=32)
    parser.add_argument('--mismatch',type=int,choices=[0,1],default=1)
    args=parser.parse_args()
    stem=f'gf180_gate_sensor_mismatch_typical27_seed{args.seed}_n{args.samples}_mm{args.mismatch}'
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    sensor=BASE/'layout/gf180_gate_sensor_shielded/gf180_gate_sensor_shielded_cap.spice'
    deck=BASE/f'benches/{stem}.spice'
    lines=['GF180 routed gate sensor official mismatch DC screen',f'.include {prefix}/design.spice',
           f'.param sw_stat_global=0 sw_stat_mismatch={args.mismatch}',f'.lib {prefix}/sm141064.spice typical',
           '.temp 27','.options gmin=1e-18 reltol=1e-7 abstol=1e-18 vntol=1e-11',
           *sensor.read_text().splitlines(),'Vdd vdd 0 3.3','Vstate state 0 1.65']
    for i in range(args.samples):
        lines += [f'Xsensor{i} state bus{i} vdd 0 vdd 0 source{i} gf180_gate_sensor_shielded',
                  f'Iread{i} bus{i} 0 1u']
    lines += ['.control','set numdgt=15',f'setseed {args.seed}','reset']
    for name,voltage in [('zero',1.65),('low',1.648),('high',1.652)]:
        lines += [f'alter Vstate={voltage:g}','op']
        for i in range(args.samples):
            lines += [f'let {name}_{i} = v(bus{i})',f'print {name}_{i}']
    lines += ['quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
                         '--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout',
                         'eventspikeseg:analog-ngspice47','120','ngspice','-b',
                         '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/f'results/{stem}.log';logpath.write_text(log)
    values={k:float(v) for k,v in re.findall(r'(?m)^\s*((?:zero|low|high)_\d+)\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==3*args.samples
    rows=[];stats={}
    if complete:
        for i in range(args.samples):
            zero,low,high=[values[f'{k}_{i}'] for k in ['zero','low','high']]
            rows.append({'sample':i,'zero_bus_v':zero,'low_bus_v':low,'high_bus_v':high,
                         'gain_over4mv':(high-low)/0.004,'high_minus_own_zero_mv':(high-zero)*1000,
                         'low_minus_own_zero_mv':(low-zero)*1000})
        stats={'zero_bus_mean_v':statistics.mean(r['zero_bus_v'] for r in rows),
               'zero_bus_std_mv':statistics.stdev(r['zero_bus_v'] for r in rows)*1000,
               'zero_bus_min_max_v':[min(r['zero_bus_v'] for r in rows),max(r['zero_bus_v'] for r in rows)],
               'gain_mean':statistics.mean(r['gain_over4mv'] for r in rows),
               'gain_std':statistics.stdev(r['gain_over4mv'] for r in rows)}
    report={'simulation_completed':complete,'seed':args.seed,'samples':args.samples,'local_mismatch_enabled':bool(args.mismatch),
            'global_variation_enabled':False,'corner':'typical','temperature_c':27,'rows':rows,'statistics':stats,
            'physical_state_accepted':False,
            'scope':'Official fets_mm per-instance mismatch enabled without model edits. Routed short-state-rail sensor at ideal DC gate voltage,1uA noiseless sink and ideal control/supply. setseed then reset reloads circuit before OP; seed reproducibility requires comparison. Own-zero subtraction is a software calibration oracle, no physical self-reference or stored offset. Excludes state/storage switching, noise, layout-dependent mismatch correlation and complete model/service/area acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),sensor,deck,logpath,modeldir/'design.spice',modeldir/'sm141064.spice']}}
    (BASE/f'results/{stem}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'simulation_completed':complete,'statistics':stats},indent=2))
    if not complete:
        raise RuntimeError(log[-2200:])


if __name__=='__main__':
    main()
