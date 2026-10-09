"""Stationary phase noise of the combined routed GF180 charge reader."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corner',choices=['typical','ff','ss'],default='typical')
    parser.add_argument('--temp-c',type=float,default=27)
    parser.add_argument('--phase',choices=['reset','read'],default='read')
    parser.add_argument('--frozen-read',action='store_true',help='Bias OUT and SUM to the completed transient zero-state read using AC-open auxiliary inductors')
    parser.add_argument('--load-mim-count',type=int,choices=[0,1,4,16],default=0)
    args=parser.parse_args()
    if args.frozen_read and args.phase!='read':
        raise ValueError('frozen read applies only to read phase')
    stem=f'gf180_combined_reader_stationary_noise_{args.corner}_temp{args.temp_c:g}_{args.phase}'
    if args.frozen_read:
        stem += '_frozenop'
    if args.load_mim_count:
        stem += f'_loadmim{args.load_mim_count}'
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    cell=BASE/'layout/gf180_gate_state_cell/gf180_gate_state_cell_cap.spice'
    frontend=BASE/'layout/gf180_charge_read_frontend/gf180_charge_read_frontend_cap.spice'
    load=BASE/'layout/gf180_mim_22x22/gf180_mim_22x22_cap.spice'
    deck=BASE/f'benches/{stem}.spice'
    spectrum=BASE/f'results/{stem}_spectrum.txt'
    reset=3.3 if args.phase=='reset' else 0
    lines=['Combined GF180 charge-reader stationary phase noise',f'.include {prefix}/design.spice',
           '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice {args.corner}',
           f'.lib {prefix}/sm141064.spice mimcap_typical',f'.temp {args.temp_c:g}',
           '.options gmin=1e-18 reltol=1e-6 abstol=1e-18 vntol=1e-11',
           *cell.read_text().splitlines(),*frontend.read_text().splitlines(),
           'Vdd vdd 0 3.3','Vcm vcm 0 1.65','Iref vdd bias 20u',
           f'Vreset reset 0 {reset:g}',f'Vresetb resetb 0 {3.3-reset:g}',
           'Ven en 0 3.3','Venb enb 0 0','Iprobe 0 sum DC 0 AC 1',
           'Xcell sum state en enb 0 vdd gf180_gate_state_cell',
           'Xreader vcm sum out vdd 0 bias reset resetb gf180_charge_read_frontend',
           'Cload out 0 100f','.control','set numdgt=15','op',
           'print v(out) v(sum) v(state) i(Vdd)',
           'noise v(out) Iprobe dec 80 10 100meg','print onoise_total inoise_total',
           'setplot noise1','set wr_singlescale','set wr_vecnames',
           'wrdata /workspace/'+spectrum.relative_to(ROOT).as_posix()+' onoise_spectrum',
           'quit','.endc','.end']
    read_report=None
    if args.load_mim_count:
        lines.remove('Cload out 0 100f')
        lines[lines.index('.control'):lines.index('.control')]=[
            *load.read_text().splitlines(),
            *[f'Xload_{i} out 0 0 gf180_mim_22x22' for i in range(args.load_mim_count)]]
    if args.frozen_read:
        load_suffix=f'_loadmim{args.load_mim_count}' if args.load_mim_count else ''
        read_report=BASE/f'results/gf180_active_charge_read_{args.corner}_temp{args.temp_c:g}_cf100ff_offset750mv_combinedfrontend{load_suffix}.json'
        transient=json.loads(read_report.read_text())
        if not transient['simulation_completed']:
            raise ValueError('completed transient required to freeze read operating point')
        zero=transient['rows']['zero']
        lines[lines.index('.control'):lines.index('.control')]=[
            f'Voutdc outdc 0 {zero["r900n"]:.15g}', 'Loutdc outdc out 1e18',
            f'Vsumdc sumdc 0 {zero["virtual"]:.15g}', 'Lsumdc sumdc sum 1e18']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
                         '--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout',
                         'eventspikeseg:analog-ngspice47','120','ngspice','-b',
                         '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/f'results/{stem}.log';logpath.write_text(log)
    values={k.lower():float(v) for k,v in re.findall(r'(?mi)^\s*(onoise_total|inoise_total|v\(out\)|v\(sum\)|v\(state\)|i\(vdd\))\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==6
    operating_point_in_range=complete and abs(values['v(sum)']-1.65)<0.02 and 0.9<values['v(out)']<2.4
    sources=[Path(__file__),cell,frontend,deck,logpath,modeldir/'design.spice',modeldir/'sm141064.spice',modeldir/'sm141064_mim.spice']
    if read_report is not None:
        sources.append(read_report)
    if args.load_mim_count:
        sources.append(load)
    filter_probes=[]
    if complete and operating_point_in_range and spectrum.exists():
        sources.append(spectrum)
        data=[]
        for line in spectrum.read_text().splitlines():
            try:
                parts=[float(x) for x in line.split()]
            except ValueError:
                continue
            if len(parts)==2:
                data.append((parts[0],parts[1]**2))
        for width_ns in [0,50,100,500,1000]:
            for delay_ns in [None,100,1000]:
                weighted=[]
                for f,psd in data:
                    x=math.pi*f*width_ns*1e-9
                    averaging=(math.sin(x)/x)**2 if x else 1
                    cds=4*math.sin(math.pi*f*delay_ns*1e-9)**2 if delay_ns is not None else 1
                    weighted.append((f,psd*averaging*cds))
                variance=sum((f2-f1)*(s1+s2)/2 for (f1,s1),(f2,s2) in zip(weighted,weighted[1:]))
                filter_probes.append({'ideal_boxcar_width_ns':width_ns,'same_stationary_process_difference_delay_ns':delay_ns,
                                      'nonoverlapping_windows':delay_ns is None or delay_ns>=width_ns,
                                      'output_noise_uv_rms':math.sqrt(variance)*1e6})
    report={'simulation_completed':complete,'operating_point_in_range':operating_point_in_range,
            'corner':args.corner,'temperature_c':args.temp_c,'mim_corner':'typical','stationary_phase':args.phase,
            'integration_band_hz':[10,1e8],'values':values,'onoise_unit':'V_RMS','inoise_unit':'A_RMS',
            'frozen_transient_bias_with_ideal_ac_open_inductors':args.frozen_read,
            'physical_output_load_mim_count':args.load_mim_count,
            'ideal_filter_probes_not_implemented_or_switched_noise':filter_probes,
            'physical_state_accepted':False,
            'scope':'Combined routed reader and separate extracted state cell, fixed read-on access. Stationary phase small-signal noise; DC read operating point may differ from transient held charge. Does not measure sampled noise, phase-transition noise, covariance, physical reference noise, restore/encoder, mismatch, resistance extraction, gate leakage or model/service acceptance. Ideal supply, VCM,20uA reference, controls and100fF load.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    if args.load_mim_count:
        report['scope']=report['scope'].replace('and100fF load','and separately extracted physical MIM output loads (no combined load routing)')
    if args.frozen_read:
        report['scope'] += ' OUT/SUM DC bias constrained to completed transient zero-state values through ideal1e18H AC-open inductors; auxiliary bench constraints, not fabricated components. Filter probes assume one stationary process; overlapping-window differences cannot represent separate pre/post acquisitions, and no probe includes switch sampling noise.'
    (BASE/f'results/{stem}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not complete:
        raise RuntimeError(log[-2500:])


if __name__=='__main__':
    main()
