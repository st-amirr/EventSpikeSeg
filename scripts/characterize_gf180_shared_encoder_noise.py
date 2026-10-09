"""Stationary encode-on noise from an audited physical-reference transient deck."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--transient',required=True)
    parser.add_argument('--input-current-na',type=float,default=0)
    args=parser.parse_args();source=Path(__file__);sha=digest(source)
    transient=ROOT/args.transient;r=json.loads(transient.read_text());settings=r['command_arguments']
    if not r['simulation_completed'] or not settings.get('physical_current_reference') or settings.get('mismatch_seed') is not None:
        raise ValueError('Completed nominal physical-reference transient required')
    if settings.get('feedback_release_advance_ns',0):raise ValueError('Simultaneous-switch baseline required')
    sources=[source,transient,ROOT/r['source_snapshot']]
    script='scripts/screen_gf180_shared_encoder_inverse.py'
    if digest(sources[-1])!=r['sha256'][script]:raise ValueError('Transient source snapshot mismatch')
    for name,expected in r['sha256'].items():
        if name==script:continue
        p=ROOT/name
        if digest(p)!=expected:raise ValueError('Transient input provenance mismatch: '+name)
        sources.append(p)
    rows=[x for x in r['rows'] if x['input_current_na']==args.input_current_na]
    if not rows:raise ValueError('Requested current absent from transient')
    row=rows[0]
    original=BASE/'benches'/transient.with_suffix('.spice').name
    if original.relative_to(ROOT).as_posix() not in r['sha256']:raise ValueError('Exact shared transient deck absent from provenance')
    lines=original.read_text().split('.control')[0].splitlines()
    levels={'Vencode':3.3,'Vencodeb':0,'Vdecode':0,'Vdecodeb':3.3,
            'Vrouteencode':3.3,'Vrouteencodeb':0,'Vbetaroute':0,'Vbetarouteb':3.3}
    frozen=[]
    for line in lines:
        name=line.split()[0] if line.split() else ''
        if name in levels:
            tokens=line.split();line=' '.join(tokens[:3])+f' DC {levels[name]:g}'
        elif name=='Iinput':line=f'Iinput sum 0 DC {args.input_current_na:g}n AC 1'
        frozen.append(line)
    stem=f'gf180_shared_encoder_noise_{r["encoder_settings"]["corner"]}{r["encoder_settings"]["temp_c"]}_i{args.input_current_na:g}na_src{sha[:12]}_from{digest(transient)[:12]}'
    snapshot=BASE/'tools/source_snapshots'/f'shared_encoder_noise_{sha}.py'
    if not snapshot.exists():snapshot.write_bytes(source.read_bytes())
    lines=frozen+['.control','set numdgt=15','setseed 17','reset','op',
        'print v(enc) v(common) v(span) v(low) v(compen) v(compenb) i(vcalprobe) i(vlowprobe) i(vdd)']
    for node in ['enc','common','span','low']:
        lines += [f'noise v({node}) Iinput dec 80 10 100meg',f'let {node}_rms = onoise_total',f'print {node}_rms']
    lines+=['quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n')
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
        '--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout','eventspikeseg:analog-ngspice47',
        '120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/'results'/(stem+'.log');logpath.write_text(log)
    values={key.lower():float(value) for key,value in re.findall(r'(?mi)^\s*(v\((?:enc|common|span|low|compen|compenb)\)|i\((?:vcalprobe|vlowprobe|vdd)\)|(?:enc|common|span|low)_rms)\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and len(values)==13 and 'ngspice-47 done' in log and not re.search('simulation\(s\) aborted',log)
    comparison={} if not complete else {'enc':(values['v(enc)']-row['encpre'])*1e6,
        'cal_reference_current_na':(values['i(vcalprobe)']-row['calcurrent'])*1e9,
        'low_reference_current_na':(values['i(vlowprobe)']-row['lowcurrent'])*1e9}
    sources += [snapshot,deck,logpath]
    report={'simulation_completed':complete,'simulator_returncode':proc.returncode,'command_arguments':vars(args),
        'source_snapshot':snapshot.relative_to(ROOT).as_posix(),'transient_evidence':args.transient,
        'values':values,'dc_minus_transient_comparison':comparison,
        'bias_matches_transient_within_100uv':complete and abs(comparison['enc'])<=100,
        'operating_point_solver_warning':bool(re.search('singular matrix|stepping failed|Transient op started',log,re.I)),
        'noise_band_hz':[10,1e8],'sampled_noise_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,
        'scope':'Full same extracted shared-module topology with physical current divider and all reference buffers/controller present, clocks frozen to encode-on state and ideal DC input current. No auxiliary node clamps. Stationary small-signal noise around resolved encode DC point; comparison to pre-capture transient ENC must pass before interpreting its relevance. Root1uA/integrator5uA sources, supply and clocks remain ideal/noiseless. Does not prove sampled/held/decode noise, inter-phase covariance, reference lifetime, physical startup/controller, full PLIF/model tolerance or5ms population service. Capacitance extraction only.',
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in set(sources)}}
    target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(target),'simulation_completed':complete,'values':values,'dc_minus_transient':comparison}))
    if not complete:raise RuntimeError(log[-2000:])

if __name__=='__main__':main()
