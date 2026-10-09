"""Stationary small-signal noise of the extracted GF180 write-on path."""
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
    parser.add_argument('--state-v',type=float,default=1.65)
    args=parser.parse_args()
    if not 0.9 <= args.state_v <= 2.4:
        raise ValueError('state outside bounded voltage range')
    stem=f'gf180_extracted_write_on_noise_ff85_state{args.state_v:g}v'
    cell=BASE/'layout/gf180_gate_state_cell/gf180_gate_state_cell_cap.spice'
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    deck=BASE/f'benches/{stem}.spice'
    lines=['Extracted GF180 write-on stationary noise',f'.include {prefix}/design.spice',
           '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice ff',
           '.temp 85','.options gmin=1e-18 reltol=1e-6 abstol=1e-18 vntol=1e-11',
           *cell.read_text().splitlines(),f'Vbus bus 0 DC {args.state_v:g} AC 1',
           'Vdd vdd 0 3.3','Ven en 0 3.3','Venb enb 0 0',
           'Xcell bus state en enb 0 vdd gf180_gate_state_cell',
           '.control','set numdgt=15','noise v(state) Vbus dec 80 1 1e12',
           'print onoise_total inoise_total','quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
                         '--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout',
                         'eventspikeseg:analog-ngspice47','120','ngspice','-b',
                         '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr; logpath=BASE/f'results/{stem}.log';logpath.write_text(log)
    values={k:float(v) for k,v in re.findall(r'(?m)^\s*(onoise_total|inoise_total)\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==2
    report={'simulation_completed':complete,'state_v':args.state_v,'temperature_c':85,
            'corner':'ff','integration_band_hz':[1,1e12],'noise_v_rms':values,
            'physical_state_accepted':False,
            'limitations':'Stationary small-signal write-on noise only, not time-varying sampled reset noise or correlated differential cancellation. Ideal bus/control supplies. No sensor/restore, mismatch, gate-leakage coverage, task accuracy or service acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),cell,modeldir/'design.spice',modeldir/'sm141064.spice',deck,logpath]}}
    (BASE/f'results/{stem}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not complete:
        raise RuntimeError(log[-2500:])


if __name__=='__main__':
    main()
