"""Extracted current-divider compliance, cold startup and stationary current noise."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
CELL='gf180_encoder_current_reference_divider'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corner',choices=['typical','ff','ss'],default='typical')
    parser.add_argument('--temp-c',type=int,default=27)
    parser.add_argument('--mismatch-seed',type=int)
    parser.add_argument('--cal-filter-mim-count',type=int,choices=[0,1,4],default=0)
    args=parser.parse_args()
    source=Path(__file__);sha=digest(source)
    sources=[source]
    cells=[]
    for name in [CELL,'gf180_pmos_bias_reference_grounded']+(['gf180_mim_22x22'] if args.cal_filter_mim_count else []):
        folder=BASE/'layout'/name;qpath=folder/'qualification.json';q=json.loads(qpath.read_text())
        if q['magic_drc_count'] or not q['lvs_unique'] or q.get('extraction_feedback',q.get('feedback','')):
            raise ValueError('Physical reference qualification failed')
        for filename,expected in q['sha256'].items():
            p=folder/filename
            if digest(p)!=expected:raise ValueError('Layout provenance mismatch: '+str(p))
            sources.append(p)
        sources.append(qpath);cells.append(folder/(name+'_cap.spice'))
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    stem=f'gf180_encoder_current_reference_{args.corner}{args.temp_c}_src{sha[:12]}'
    if args.mismatch_seed is not None:stem+=f'_mismatchseed{args.mismatch_seed}'
    if args.cal_filter_mim_count:stem+=f'_filter{args.cal_filter_mim_count}mim22'
    dcpath=BASE/'results'/(stem+'_compliance.dat')
    startpath=BASE/'results'/(stem+'_startup.dat')
    lines=['GF180 extracted current divider diagnostics',f'.include {prefix}/design.spice',
           f'.param sw_stat_global=0 sw_stat_mismatch={int(args.mismatch_seed is not None)}',
           f'.lib {prefix}/sm141064.spice {args.corner}',f'.temp {args.temp_c}',
           '.options gmin=1e-18 reltol=1e-6 abstol=1e-18 vntol=1e-9']
    if args.cal_filter_mim_count:lines.append(f'.lib {prefix}/sm141064.spice mimcap_typical')
    for p in cells:lines+=p.read_text().splitlines()
    lines += [f'Xcalfilter{i} cal 0 0 gf180_mim_22x22' for i in range(args.cal_filter_mim_count)]
    lines+=['Vdd vdd 0 DC 3.3 AC 1 PWL(0 0 1u 3.3)',
            'Iref bias 0 DC 1u PWL(0 0 1u 0 1.1u 1u)',
            'Xbias bias vdd 0 gf180_pmos_bias_reference_grounded',
            f'Xdivider bias cal low vdd 0 {CELL}',
            'Vcal cal 0 DC 1.2 PWL(0 0 1u 1.2)',
            'Vlow low 0 DC 0.5 PWL(0 0 1u 0.5)',
            'Hcal calnoise 0 Vcal 1e9','Hlow lownoise 0 Vlow 1e6',
            '.control','set numdgt=15',f'setseed {args.mismatch_seed or 17}','reset','op',
            'print i(vcal) i(vlow) v(bias) i(vdd)',
            'noise v(calnoise) Vdd dec 80 10 100meg',
            'let cal_rms = onoise_total / 1e9','print cal_rms',
            'noise v(lownoise) Vdd dec 80 10 100meg',
            'let low_rms = onoise_total / 1e6','print low_rms',
            'dc Vcal 0.2 3.0 0.2','set wr_singlescale','set wr_vecnames',
            'wrdata /workspace/'+dcpath.relative_to(ROOT).as_posix()+' i(vcal) i(vlow) v(bias)',
            f'setseed {args.mismatch_seed or 17}','reset','tran 100n 100u uic',
            'set wr_singlescale','set wr_vecnames',
            'wrdata /workspace/'+startpath.relative_to(ROOT).as_posix()+' i(vcal) i(vlow) v(bias)',
            'meas tran cal_late find i(vcal) at=99u',
            'meas tran low_late find i(vlow) at=99u','quit','.endc','.end']
    deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n')
    snapshot=BASE/'tools/source_snapshots'/f'encoder_current_reference_{sha}.py'
    if not snapshot.exists():snapshot.write_bytes(source.read_bytes())
    sources+=[snapshot,deck,modeldir/'design.spice',modeldir/'sm141064.spice',modeldir/'sm141064_mim.spice']
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
        '--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout',
        'eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],
        capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/'results'/(stem+'.log');logpath.write_text(log);sources.append(logpath)
    values={k.lower():float(v) for k,v in re.findall(r'(?mi)^\s*(i\(vcal\)|i\(vlow\)|v\(bias\)|i\(vdd\)|cal_rms|low_rms|cal_late|low_late)\s*=\s*([-+0-9.eE]+)',log)}
    completed=proc.returncode==0 and len(values)==8 and dcpath.exists() and startpath.exists() and not re.search('simulation\(s\) aborted',log)
    data=[];startup={}
    if completed:
        for line in dcpath.read_text().splitlines()[1:]:
            row=list(map(float,line.split()));data.append({'cal_voltage_v':row[0],'cal_current_na':row[1]*1e9,'low_current_ua':row[2]*1e6,'bias_v':row[3]})
        sources += [dcpath,startpath]
        import numpy as np
        table=np.loadtxt(startpath,skiprows=1);target=values['i(vcal)'];bad=(table[:,0]>2e-6)&(abs(table[:,1]-target)>.01*abs(target))
        startup={'last_observed_outside_1percent_us':float(max(table[bad,0],default=2e-6)*1e6),'late_within_1percent':abs(values['cal_late']-target)<=.01*abs(target),'current_at10_50_99us_na':[float(np.interp(t*1e-6,table[:,0],table[:,1])*1e9) for t in [10,50,99]],'scope':'Finite100us diagnostic cold ramp, output externally clamped. Last outside1percent is not startup/service acceptance.'}
    report={'simulation_completed':completed,'simulator_returncode':proc.returncode,'command_arguments':vars(args),
            'values':values,'compliance_rows':data,'startup_analysis':startup,'source_snapshot':snapshot.relative_to(ROOT).as_posix(),
            'operating_point_solver_warning':bool(re.search('singular matrix|stepping failed|Transient op started',log,re.I)),
            'noise_band_hz':[10,1e8],'physical_current_reference_accepted':False,'full_chip_accepted':False,
            'scope':'Two separately extracted physical macros, root20/2um PF diode at ideal external1uA sink, divider and low mirror. Ideal outputs clamp CAL=1.2V/LOW=0.5V at noise point; compliance sweeps CAL only. Ideal CCCV transimpedance probes measure current noise without adding load/resistor noise. Supply/output ramps and root-current ramp are diagnostic sources; cold startup uses uic, not a fabricated enable circuit. Stationary current noise excludes root generator/supply noise, sampling/phase covariance and switched noise. No combined encoder/layout/RPEX/silicon gate leakage/model tolerance/service acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sources}}
    target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(target),'simulation_completed':completed,'values':values}))
    if not completed:raise RuntimeError(log[-2500:])

if __name__=='__main__':main()
