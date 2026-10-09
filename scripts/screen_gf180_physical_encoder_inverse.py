"""Extracted MOS inverse-current diagnostic, without ideal mathematical inversion."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dc-profile',required=True)
    parser.add_argument('--mismatch-seed',type=int,default=None)
    parser.add_argument('--buffer-reference-ua',type=float,default=None)
    args=parser.parse_args()
    source=Path(__file__);sha=digest(source)
    profile=ROOT/args.dc_profile;r=json.loads(profile.read_text());settings=r['command_arguments']
    if not r.get('simulation_completed') or r.get('operating_point_solver_warning') or settings.get('transient') or settings.get('noise') or not settings.get('source_lifted') or not settings.get('mirrored_feedback') or settings.get('physical_compensation_controller'):
        raise ValueError('Completed lifted mirrored DC profile without solver fallback required')
    if not r['analysis']['strictly_monotonic']:raise ValueError('Monotonic transfer required')
    sources=[source,profile]
    for name,expected in r['sha256'].items():
        if name=='scripts/screen_gf180_nonlinear_encoder.py':continue
        path=ROOT/name
        if digest(path)!=expected:raise ValueError('Profile input provenance mismatch: '+name)
        sources.append(path)
    original=next(ROOT/name for name in r['sha256'] if name.endswith('.spice') and '/benches/' in name)
    lines=original.read_text().split('.control')[0].splitlines()
    # The former encoder OTA now physically regulates the inverse mirror drain.
    # ENC is a diagnostic voltage command; it is not an implemented state buffer.
    remove=('Iinput ','Xinputfeedback','Xcompswitch ','Vcompen ','Vcompenb ')
    lines=[line for line in lines if not line.startswith(remove)]
    lines=[line.replace('Xota common sum enc ','Xota common sum sum ')               .replace('Xfeedback sum enc ','Xfeedback inverseout enc ')               .replace('Xcomp cmp enc ','Xcomp cmp sum ')               .replace('Xload enc ','Xload sum ') for line in lines]
    lines+=['Vprobe sum inverseout 0', 'Vencoded enc 0 1']
    if args.buffer_reference_ua is not None:
        if not .5<=args.buffer_reference_ua<=20:raise ValueError('Buffer bias0.5..20uA')
        lines=[line.replace(' 0 bias ', ' 0 inversebias ') if line.startswith('Xota ') else line for line in lines]
        lines+=[f'Iinversebias inversebias 0 {args.buffer_reference_ua:g}u','Xinversebias inversebias vdd 0 gf180_pmos_bias_reference_grounded']
    if args.mismatch_seed is not None:
        lines=[line.replace('sw_stat_mismatch=0','sw_stat_mismatch=1') for line in lines]
    lines+=['.control','set numdgt=15']
    if args.mismatch_seed is not None:lines.extend([f'setseed {args.mismatch_seed}','reset'])
    for i,row in enumerate(r['rows']):
        lines+=[f'echo POINT_{i}',f"alter Vencoded {row['v(enc)']:.15g}",'op','print i(vprobe) v(sum) v(enc) v(common) v(span) i(vdd)']
    lines+=['quit','.endc','.end']
    snapshot=BASE/'tools/source_snapshots'/f'physical_inverse_{sha}.py'
    if not snapshot.exists():snapshot.write_bytes(source.read_bytes())
    sources.append(snapshot)
    stem=f"gf180_physical_encoder_inverse_{settings['corner']}{settings['temp_c']:g}_src{sha[:12]}_profile{digest(profile)[:12]}"
    if args.mismatch_seed is not None:stem+=f'_mismatchseed{args.mismatch_seed}'
    if args.buffer_reference_ua is not None:stem+=f'_buffer{args.buffer_reference_ua:g}ua'
    deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=135)
    log=proc.stdout;logpath=BASE/'results'/(stem+'.log');logpath.write_text(log)
    rows=[]
    for index,block in re.findall(r'POINT_(\d+)\s*\n(.*?)(?=POINT_\d+\s*\n|\Z)',log,re.S):
        values={key.lower():float(value) for key,value in re.findall(r'(?mi)^\s*(i\(vprobe\)|v\(sum\)|v\(enc\)|v\(common\)|v\(span\)|i\(vdd\))\s*=\s*([-+0-9.eE]+)',block)}
        if len(values)==6:
            command=r['rows'][int(index)];decoded=-values['i(vprobe)']*1e9
            rows.append({'input_current_na':command['input_current_na'],'decoded_current_na':decoded,'current_error_na':decoded-command['input_current_na'],'sum_minus_reference_uv':(values['v(sum)']-values['v(common)'])*1e6,'point_solver_warning':bool(re.search(r'singular matrix|stepping failed|Transient op started',block,re.I)),**values})
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(rows)==len(r['rows'])
    analysis={}
    if complete:
        zero=next(row for row in rows if row['input_current_na']==0)
        for row in rows:row['zero_corrected_current_error_na']=row['current_error_na']-zero['current_error_na']
        analysis={'maximum_absolute_current_error_na':max(abs(x['current_error_na']) for x in rows),'zero_current_error_pa':zero['current_error_na']*1000,'maximum_zero_corrected_current_error_na':max(abs(x['zero_corrected_current_error_na']) for x in rows),'maximum_sum_minus_reference_uv':max(abs(x['sum_minus_reference_uv']) for x in rows),'strictly_monotonic':all(b['decoded_current_na']>a['decoded_current_na'] for a,b in zip(rows,rows[1:])),'zero_vdd_power_uw':-3.3*zero['i(vdd)']*1e6}
    sources+=[deck,logpath]
    report={'simulation_completed':complete,'simulator_returncode':proc.returncode,'command_arguments':vars(args),'encoder_settings':settings,'mismatch_seed_applied_via_reset':args.mismatch_seed is not None,'source_snapshot':snapshot.relative_to(ROOT).as_posix(),'rows':rows,'analysis':analysis,'operating_point_solver_warning':any(x['point_solver_warning'] for x in rows),'qualified_layout_components':r['qualified_layout_components'],'physical_state_accepted':False,'inverse_accepted':False,'full_chip_accepted':False,'scope':'Extracted six-MOS feedback reused as voltage-to-signed-current inverse, with physical seven-MOS OTA regulating mirror drain and physical span/common/low reference buffers. ENC is an ideal diagnostic voltage command from a prior measured DC curve; zero-volt current probe only observes current. Mismatch when enabled is official local statistical cards with setseed, still commanded from a nominal encoder profile; no paired encoder calibration. No mathematical inverse in circuit, stored-state sampler, gate loading/retention, input buffer, transient/noise/mismatch/RPEX, tiny-current generator, assembled layout, PLIF or model-accuracy acceptance. Zero correction is analysis only and not an implemented offset circuit.','sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in set(sources)}}
    target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(target),'simulation_completed':complete,'analysis':analysis,'solver_warning':report['operating_point_solver_warning']},indent=2))
    if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
