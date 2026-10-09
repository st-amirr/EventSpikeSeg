"""Extracted GF180 programming and destructive charge-sharing read probe."""
import hashlib
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dummy-factor',type=float,default=0)
    parser.add_argument('--nf-off-delay-ns',type=float,default=0)
    parser.add_argument('--offset-mv',type=float,default=750)
    parser.add_argument('--sample-ff',type=float,default=100)
    args=parser.parse_args()
    if not 0 <= args.dummy_factor <= 2:
        raise ValueError('dummy sizing factor outside bounded0..2 screen')
    if not -20 <= args.nf_off_delay_ns <= 20 or not 0 < args.offset_mv <= 750 or not 1 <= args.sample_ff <= 100:
        raise ValueError('phase delay, rail offset or sample capacitance outside bounded screen')
    cell = BASE/'layout/gf180_gate_state_cell/gf180_gate_state_cell_cap.spice'
    pdk = BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix = '/workspace/'+pdk.relative_to(ROOT).as_posix()
    stem = 'gf180_combined_state_program_read_ff85_sample100ff_slew10ns'
    if args.dummy_factor:
        stem += f'_dummy{args.dummy_factor:g}'
    if args.nf_off_delay_ns:
        stem += f'_nfoff{args.nf_off_delay_ns:g}ns'
    if args.offset_mv != 750:
        stem += f'_offset{args.offset_mv:g}mv'
    if args.sample_ff != 100:
        stem += f'_sample{args.sample_ff:g}ff'
    deck = BASE/f'benches/{stem}.spice'
    logfile = BASE/f'results/{stem}.log'
    lines = ['Physical GF180 state write and ideal100fF shared sample read',
             f'.include {prefix}/design.spice', '.param sw_stat_global=0 sw_stat_mismatch=0',
             f'.lib {prefix}/sm141064.spice ff', '.temp 85',
             '.options gmin=1e-18 reltol=1e-6 abstol=1e-18 vntol=1e-11',
             *cell.read_text().splitlines(), 'Vdd vdd 0 3.3', 'Vcm vcm 0 1.65',
             '.model ideal_phase SW(Ron=10 Roff=1e30 Vt=1.65 Vh=0.1)',
             'Vwrite write 0 PWL(0 3.3 0.899u 3.3 0.9u 0 5.01m 0)',
             'Vreset reset 0 PWL(0 3.3 1.099u 3.3 1.1u 0 5.01m 0)',
             'Vdrive drive 0 PWL(0 3.3 4.998999m 3.3 4.999m 0 5.01m 0)',
             'Vsample sample 0 PWL(0 0 4.999499m 0 4.9995m 3.3 5.01m 3.3)',
             'Vread read 0 PWL(0 0 4.999999m 0 5m 3.3 5.000999m 3.3 5.001m 0 5.01m 0)']
    kinds = ['low', 'high', 'zero', 'low_control', 'high_control']
    targets = {k:1.65+sign*args.offset_mv/1000 for k,sign in [('low',-1),('high',1),('zero',0),('low_control',-1),('high_control',1)]}
    for kind in kinds:
        target = targets[kind]
        if kind.endswith('control'):
            points = [(0,3.3),(0.89e-6,3.3),(0.9e-6,0),(5.01e-3,0)]
        else:
            points = [(0,3.3),(0.89e-6,3.3),(0.9e-6,0),(4.99999e-3,0),(5e-3,3.3),(5.00099e-3,3.3),(5.001e-3,0),(5.01e-3,0)]
        for gate, invert in [('en',False),('enb',True)]:
            gatepoints=list(points)
            if not invert and args.nf_off_delay_ns:
                for i in range(len(points)-1):
                    if points[i][1] == 3.3 and points[i+1][1] == 0:
                        gatepoints[i]=(points[i][0]+args.nf_off_delay_ns*1e-9,3.3)
                        gatepoints[i+1]=(points[i+1][0]+args.nf_off_delay_ns*1e-9,0)
            if any(gatepoints[i][0]>=gatepoints[i+1][0] for i in range(len(gatepoints)-1)):
                raise ValueError('nonmonotonic gate phase PWL')
            wave = ' '.join(f'{t:.12g} {3.3-v if invert else v:.12g}' for t,v in gatepoints)
            lines.append(f'V{gate}_{kind} {gate}_{kind} 0 PWL({wave})')
        lines += [f'Vsource_{kind} source_{kind} 0 PWL(0 {target:g} 1.1u {target:g} 1.2u 1.65 5.01m 1.65)',
                  f'Sdrive_{kind} source_{kind} bus_{kind} drive 0 ideal_phase',
                  f'Sreset_{kind} vcm bucket_{kind} reset 0 ideal_phase',
                  f'Ssample_{kind} bus_{kind} bucket_{kind} sample 0 ideal_phase',
                  f'Csample_{kind} bucket_{kind} 0 {args.sample_ff:g}f',
                  f'Xcell_{kind} bus_{kind} state_{kind} en_{kind} enb_{kind} 0 vdd gf180_gate_state_cell']
        if args.dummy_factor:
            # Opposite-phase shorted-D/S dummy pair: schematic sizing diagnostic.
            nwidth=0.5*args.dummy_factor
            pwidth=args.dummy_factor
            if nwidth < 0.22:
                raise ValueError('NF dummy narrower than official minimum')
            lines += [f'Xdummy_n_{kind} state_{kind} enb_{kind} state_{kind} 0 nfet_03v3 w={nwidth:g}u l=0.28u ad={nwidth*0.44:g}p as={nwidth*0.44:g}p pd={2*nwidth+0.88:g}u ps={2*nwidth+0.88:g}u',
                      f'Xdummy_p_{kind} state_{kind} en_{kind} state_{kind} vdd pfet_03v3 w={pwidth:g}u l=0.28u ad={pwidth*0.44:g}p as={pwidth*0.44:g}p pd={2*pwidth+0.88:g}u ps={2*pwidth+0.88:g}u']
    lines += ['.control','set numdgt=15','tran 500n 5.01m']
    measures=[('program','state','0.85u'),('isolated','state','1u'),('buschanged','state','2u'),('held','state','4.998m'),('readstate','state','5.0009m'),('readbucket','bucket','5.0009m'),('after','state','5.002m')]
    for kind in kinds:
        for name,node,time in measures:
            lines.append(f'meas tran {kind}_{name} find v({node}_{kind}) at={time}')
    lines += ['quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc = subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
                           '--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir',prefix,
                           '--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b',
                           '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log = proc.stdout+proc.stderr; logfile.write_text(log)
    values = {k:float(v) for k,v in re.findall(r'(?m)^\s*((?:low|high|zero)(?:_control)?_(?:program|isolated|buschanged|held|readstate|readbucket|after))\s*=\s*([-+0-9.eE]+)',log)}
    complete = proc.returncode==0 and 'ngspice-47 done' in log and len(values)==len(measures)*len(kinds)
    rows = {}
    if complete:
        for kind in kinds:
            row={name:values[f'{kind}_{name}'] for name,_,_ in measures}
            row['program_error_mv']=(row['program']-targets[kind])*1000
            row['switch_off_shift_mv']=(row['isolated']-row['program'])*1000
            row['bus_return_shift_mv']=(row['buschanged']-row['isolated'])*1000
            row['post_bus_hold_drift_mv']=(row['held']-row['buschanged'])*1000
            row['hold_total_error_mv']=(row['held']-targets[kind])*1000
            row['read_state_disturbance_mv']=(row['readstate']-row['held'])*1000
            row['sample_shift_mv']=(row['readbucket']-1.65)*1000
            rows[kind]=row
    report={'simulation_completed':complete,'rows':rows,'dummy_factor':args.dummy_factor,'nf_off_delay_ns':args.nf_off_delay_ns,'rail_offset_mv':args.offset_mv,'sample_capacitance_ff':args.sample_ff,'physical_state_accepted':False,
            'scope':'Physical extracted3.3V gate-state/TG, FF85. Optional opposite-phase dummy transistors are schematic with assumed diffusions. Physical TG does programming/read gating; driver, complementary phase controls, bus isolation, sampling/reset switches and100fF sample capacitor are ideal. No sense amplifier or restore path, gate leakage disabled in official models, resistance extraction/noise/mismatch/accuracy/service unqualified.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),cell,pdk/'design.spice',pdk/'sm141064.spice',deck,logfile]}}
    (BASE/f'results/{stem}.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
    if not complete:
        raise RuntimeError(log[-2000:])


if __name__=='__main__':
    main()
