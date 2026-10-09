"""Stationary selected-source-follower noise with the held state AC floating."""
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
    args=parser.parse_args()
    stem=f'gf180_gate_sensor_noise_{args.corner}_temp{args.temp_c:g}_physical_shortstate_rail'
    transient=BASE/f'results/gf180_gate_sensor_{args.corner}_temp{args.temp_c:g}_offset2mv_w1_read1ua_physicalsensor_shielded_smallload_physicalpark_cycles3.json'
    read=json.loads(transient.read_text())
    if not read['simulation_completed']:
        raise ValueError('completed transient required')
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    cells=[BASE/f'layout/{name}/{name}_cap.spice' for name in ['gf180_gate_state_cell','gf180_gate_sensor_shielded','gf180_fixed_body_tg','gf180_mim_7x7']]
    deck=BASE/f'benches/{stem}.spice'
    lines=['GF180 stationary gate sensor noise with AC-floating membrane',f'.include {prefix}/design.spice',
           '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice {args.corner}',
           f'.lib {prefix}/sm141064.spice mimcap_typical',f'.temp {args.temp_c:g}',
           '.options gmin=1e-18 reltol=1e-6 abstol=1e-18 vntol=1e-11']
    for cell in cells:
        lines += cell.read_text().splitlines()
    lines += ['Vdd vdd 0 3.3','Vcm vcm 0 1.65','Vpre pre 0 1',
              f'Vheld held 0 {read["rows"]["zero"]["during"]:.15g}','Lhold held state 1e18',
              'Iread bus 0 DC 1u AC 1',
              'Xcell vcm state 0 vdd 0 vdd gf180_gate_state_cell',
              'Xsensor state bus vdd 0 vdd 0 source gf180_gate_sensor_shielded',
              'Xpark pre bus 0 vdd 0 vdd gf180_fixed_body_tg',
              'Xload bus 0 0 gf180_mim_7x7',
              '.control','set numdgt=15','op','print v(state) v(bus) v(source) i(Vdd)',
              'noise v(bus) Iread dec 80 10 100meg','let bus_rms = onoise_total','print bus_rms',
              'noise v(state) Iread dec 80 10 100meg','let state_rms = onoise_total','print state_rms',
              'quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
                         '--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout',
                         'eventspikeseg:analog-ngspice47','120','ngspice','-b',
                         '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/f'results/{stem}.log';logpath.write_text(log)
    values={k.lower():float(v) for k,v in re.findall(r'(?mi)^\s*(bus_rms|state_rms|v\(state\)|v\(bus\)|v\(source\)|i\(vdd\))\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==6
    report={'simulation_completed':complete,'corner':args.corner,'temperature_c':args.temp_c,
            'mim_corner':'typical','integration_band_hz':[10,1e8],'values':values,'noise_unit':'V_RMS',
            'physical_state_accepted':False,
            'scope':'Separately extracted short-state-rail sensor, state/access, physical park TG and7um MIM bus load. Ideal1uA noiseless read current, supply/VCM/park references. State DC frozen to transient read via ideal AC-open1e18H bench inductor; AC state remains floating. Stationary phase only, no sampling or inter-phase covariance, local mismatch, physical reference noise, gate-leakage or model/service/restore acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),*cells,transient,deck,logpath,modeldir/'design.spice',modeldir/'sm141064.spice',modeldir/'sm141064_mim.spice']}}
    (BASE/f'results/{stem}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not complete:
        raise RuntimeError(log[-2200:])


if __name__=='__main__':
    main()
