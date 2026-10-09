"""Extracted sampler with switched precharged dual-buffer access; nominal diagnostic."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--membrane-window",action="store_true")
    parser.add_argument("--settled-acquisition",action="store_true")
    parser.add_argument("--max-step-ns",type=int,choices=[20,100],default=100)
    parser.add_argument("--early-only",action="store_true")
    args=parser.parse_args()
    if not args.settled_acquisition or not args.early_only:
        raise ValueError('Switched access diagnostic currently requires settled acquisition and early-only mode')
    sources=set()
    texts=[]
    for cell in ['gf180_compensated_bottom_sampler_shielded','gf180_shared_ota_core_pmos_input_fullroute']:
        directory=BASE/'layout'/cell
        qp=directory/'qualification.json'
        q=json.loads(qp.read_text())
        if q['magic_drc_count'] or q['gds_roundtrip_drc_count'] or not q['gds_roundtrip_lvs_unique']:
            raise ValueError('Physical view unqualified: '+cell)
        sources.add(qp)
        for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
            for name,expected in q[key].items():
                p=directory/name if key=='sha256' else ROOT/name
                if digest(p)!=expected: raise ValueError('Changed physical input: '+str(p))
                sources.add(p)
        texts.extend((directory/(cell+'_cap.spice')).read_text().splitlines())
    models=BASE/'pdk/gf180_primitive_source/models/ngspice'
    sources.update(models.rglob('*.spice'))
    prefix='/workspace/'+models.relative_to(ROOT).as_posix()
    stem='gf180_sampler_switched_read_window'+str(int(args.membrane_window))+'_acq'+str(int(args.settled_acquisition))+'_step'+str(args.max_step_ns)+'_early'+str(int(args.early_only))+'_src'+digest(Path(__file__))[:12]
    snapshot=BASE/'tools/source_snapshots'/(stem+'.py')
    if not snapshot.exists(): snapshot.write_bytes(Path(__file__).read_bytes())
    sources.add(snapshot)
    lines=['Extracted sampler and extracted dual unity read buffers',f'.include {prefix}/design.spice',
        '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice typical',
        f'.lib {prefix}/sm141064.spice mimcap_typical','.temp 27',
        '.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,
        'Vdd vdd 0 3.3','Ireference bias 0 1u',
        'Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
        'Ven en 0 PWL(0 0 10n 0 20n 3.3 990n 3.3 1u 0 5.002m 0)',
        'Venb enb 0 PWL(0 3.3 10n 3.3 20n 0 990n 0 1u 3.3 5.002m 3.3)',
        'Vben ben 0 PWL(0 0 10n 0 20n 3.3 970n 3.3 980n 0 5.002m 0)',
        'Vbenb benb 0 PWL(0 3.3 10n 3.3 20n 0 970n 0 980n 3.3 5.002m 3.3)',
        'Vcm vcm 0 PWL(0 0 30n 0 60n 1.65 5.002m 1.65)']
    targets={'low':.75,'mid':1.65,'high':2.55} if args.membrane_window else {'low':.3,'mid':1.65,'high':3.0}
    for name,target in targets.items():
        lines.extend([f'Vin_{name} input_{name} 0 PWL(0 0 30n 0 60n {target} 5.002m {target})',
            f'Xsample_{name} p_{name} m_{name} input_{name} vcm en enb ben benb 0 vdd gf180_compensated_bottom_sampler_shielded',
            f'.ic v(p_{name})=0 v(m_{name})=0'])
        for terminal in ['p','m']:
            lines.extend([f'Xaccess_{terminal}_{name} {terminal}_{name} rin_{terminal}_{name} read_en read_enb 0 vdd gf180_fixed_body_tg_fullroute',
                f'Xprecharge_{terminal}_{name} vcm rin_{terminal}_{name} pre_en pre_enb 0 vdd gf180_fixed_body_tg_fullroute',
                f'Xread_{terminal}_{name} rin_{terminal}_{name} out_{terminal}_{name} out_{terminal}_{name} vdd 0 bias cmp_{terminal}_{name} gf180_shared_ota_core_pmos_input_fullroute',
                f'Xcomp_{terminal}_{name} cmp_{terminal}_{name} out_{terminal}_{name} cap_mim_2f0_m4m5_noshield c_length=7u c_width=7u',
                f'Cload_{terminal}_{name} out_{terminal}_{name} 0 50f'])
    if args.settled_acquisition:
        lines=[line.replace('990n','19990n').replace('1u 0','20u 0').replace('1u 3.3','20u 3.3').replace('970n','19970n').replace('980n','19980n').replace('5.002m','5.021m') for line in lines]
    lines.extend(['Vread read_en 0 PWL(0 0 29.99u 0 30u 3.3 44.99u 3.3 45u 0 5.021m 0)',
        'Vreadb read_enb 0 PWL(0 3.3 29.99u 3.3 30u 0 44.99u 0 45u 3.3 5.021m 3.3)',
        'Vpre pre_en 0 PWL(0 3.3 29.97u 3.3 29.98u 0 5.021m 0)',
        'Vpreb pre_enb 0 PWL(0 0 29.97u 0 29.98u 3.3 5.021m 3.3)'])
    lines.extend(['.control','set numdgt=15',f'tran {args.max_step_ns}n {"5.021m" if args.settled_acquisition else "5.002m"} 0 {args.max_step_ns}n uic'])
    for name in targets:
        lines.extend([f'let stored_{name}=v(p_{name})-v(m_{name})',f'let read_{name}=v(out_p_{name})-v(out_m_{name})',f'let err_{name}=read_{name}-stored_{name}'])
        for phase,time in ([('on','19.96u'),('released','20.1u'),('settled','29u'),('before_read','29.9u'),('during_read','44u'),('after_read','45.1u'),('held','5.020m')] if args.settled_acquisition else [('on','960n'),('released','1.1u'),('settled','10u'),('held','5.001m')]):
            for signal in ['stored','read','err']:
                lines.append(f'meas tran {name}_{signal}_{phase} find {signal}_{name} at={time}')
    for name in targets:
        for node in ['p','m','out_p','out_m']:
            lines.append(f'meas tran node_{name}_{node} find v({node}_{name}) at={"5.020m" if args.settled_acquisition else "5.001m"}')
    lines.extend(['quit','.endc','.end'])
    if args.early_only:
        lines=[line.replace('5.021m','50u').replace('5.020m','49u').replace('5.002m','50u').replace('5.001m','49u') for line in lines]
    deck=BASE/'benches'/(stem+'.spice'); deck.write_text('\n'.join(lines)+'\n'); sources.add(deck)
    result=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=result.stdout+result.stderr
    lp=BASE/'results'/(stem+'.log'); lp.write_text(log); sources.add(lp)
    values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_(?:stored|read|err)_(?:on|released|settled|before_read|during_read|after_read|held))\s*=\s*([-+0-9.eE]+)',log)}
    nodes={k:float(v) for k,v in re.findall(r'(?m)^(node_(?:low|mid|high)_(?:p|m|out_p|out_m))\s*=\s*([-+0-9.eE]+)',log)}
    complete=result.returncode==0 and len(values)==63 and len(nodes)==12 and 'timestep too small' not in log.lower()
    cases=[]
    if complete:
        for name,target in targets.items():
            v={k.removeprefix(name+'_'):x for k,x in values.items() if k.startswith(name+'_')}
            cases.append({'target_v':target,'measurements_v':v,'release_step_mv':1000*(v['stored_released']-v['stored_on']),'hold_drift_mv':1000*(v['stored_held']-v['stored_released']),'late_read_error_mv':None,'during_access_read_error_mv':1000*v['err_during_read'],'access_disturbance_mv':1000*(v['stored_during_read']-v['stored_before_read']),'disconnect_disturbance_mv':1000*(v['stored_after_read']-v['stored_during_read'])})
    report={'simulation_completed':complete,'returncode':result.returncode,'settings':vars(args),'held_measurement_time_s':49e-6 if args.early_only else (5.020e-3 if args.settled_acquisition else 5.001e-3),'five_ms_hold_completed':complete and not args.early_only,'held_terminal_voltages_v':nodes,'cases':cases,'source_snapshot':snapshot.relative_to(ROOT).as_posix(),
        'scope':'Nominal typical27C cap-extracted sampler and two corrected OTA buffers wired schematically, connected to floating terminals through actual extracted TG access switches, with native TG precharge to1.65V. Access30-45us, precharge opens29.98us; measurement at44us is actual two-buffer differential output; after disconnect output error is not interpreted as state readout. Ideal reference/current/clock/input sources; schematic native diode bias and native7um compensation caps, ideal50fF output loads. Combined buffer-sampler/access physical routing, real clock drivers, RPEX, noise, mismatch/PVT, gate leakage qualification, nonlinear read/restore, PLIF and population5ms service not established. No ideal subtraction in the circuit: output remains two physical voltages; differential subtraction is a measurement only.',
        'physical_storage_accepted':False,'read_restore_accepted':False,'full_chip_accepted':False,
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    rp=BASE/'results'/(stem+'.json'); rp.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(rp),'simulation_completed':complete,'cases':cases},indent=2))
    if not complete: raise RuntimeError(log[-2000:])
if __name__=='__main__': main()
