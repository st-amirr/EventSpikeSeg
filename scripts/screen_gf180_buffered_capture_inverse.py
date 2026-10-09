"""Extracted buffered capture and native-resistor analog inverse bringup."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--membrane-window",action="store_true")
    parser.add_argument("--settled-acquisition",action="store_true")
    parser.add_argument("--max-step-ns",type=int,choices=[10,20,100],default=100)
    parser.add_argument("--early-only",action="store_true")
    parser.add_argument("--reset-dummy",action="store_true")
    parser.add_argument("--shielded-reader",action="store_true")
    parser.add_argument("--vertical-guards",action="store_true")
    parser.add_argument("--input-series-ohm",type=int,choices=[0,100],default=0)
    parser.add_argument("--operating-point",action="store_true")
    parser.add_argument("--integration",choices=["gear","trap"],default="gear")
    parser.add_argument("--physical-capture-clocks",action="store_true")
    parser.add_argument("--isolate",choices=["full","switch_only","hold_only"],default="full")
    parser.add_argument("--physical-all-clocks",action="store_true")
    parser.add_argument("--capture-dummy",action="store_true")
    parser.add_argument("--combined-capture",action="store_true")
    parser.add_argument("--inverse",action="store_true")
    parser.add_argument("--combined-buffer",action="store_true")
    args=parser.parse_args()
    if args.combined_capture:
        if args.isolate!="full":raise ValueError("Combined capture requires full circuit")
        args.capture_dummy=True
    if args.physical_all_clocks:args.physical_capture_clocks=True
    if not args.reset_dummy:raise ValueError('Physical reader includes reset dummy')
    if not args.settled_acquisition or not args.early_only:
        raise ValueError('Switched access diagnostic currently requires settled acquisition and early-only mode')
    reader_cell='gf180_active_charge_reader_fullroute'+('_guarded' if args.vertical_guards else ('_shielded' if args.shielded_reader else ''))
    sources=set()
    texts=[]
    cells=['gf180_compensated_bottom_sampler_shielded',reader_cell,'gf180_shared_ota_core_pmos_input_fullroute']
    if args.combined_buffer:cells.append('gf180_held_output_buffer_guarded')
    if args.combined_capture:cells.append('gf180_reader_output_capture_guarded')
    if args.physical_capture_clocks:cells.append('gf180_phase_inverter_fullroute')
    for cell in cells:
        directory=BASE/'layout'/cell
        qp=directory/'qualification.json'
        q=json.loads(qp.read_text())
        if q['magic_drc_count'] or q.get('gds_roundtrip_drc_count',0) or not q.get('gds_roundtrip_lvs_unique',q.get('lvs_unique',False)):
            raise ValueError('Physical view unqualified: '+cell)
        sources.add(qp)
        for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
            for name,expected in q.get(key,{}).items():
                p=directory/name if key=='sha256' else ROOT/name
                if digest(p)!=expected: raise ValueError('Changed physical input: '+str(p))
                sources.add(p)
        local=(directory/(cell+'_cap.spice')).read_text()
        for child in re.findall(r'(?m)^\.subckt (\S+)',local):
            if child!=cell:
                local=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,local)
        texts.extend(local.splitlines())
    models=BASE/'pdk/gf180_primitive_source/models/ngspice'
    sources.update(models.rglob('*.spice'))
    prefix='/workspace/'+models.relative_to(ROOT).as_posix()
    stem='gf180_buffered_capture_inverse'+str(int(args.inverse))+'_step'+str(args.max_step_ns)+'_settings'+hashlib.sha256(json.dumps(vars(args),sort_keys=True).encode()).hexdigest()[:10]+'_src'+digest(Path(__file__))[:12]
    snapshot=BASE/'tools/source_snapshots'/(stem+'.py')
    if not snapshot.exists(): snapshot.write_bytes(Path(__file__).read_bytes())
    sources.add(snapshot)
    lines=['Extracted sampler and extracted dual unity read buffers',f'.include {prefix}/design.spice',
        '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice typical',
        f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.temp 27',
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
        lines.extend([f'Xphysical_reader_{name} p_{name} m_{name} vcm out_{name} vdd 0 bias read_en read_enb pre_en pre_enb sum_{name} cmp_{name} gf180_active_charge_reader_fullroute{"_guarded" if args.vertical_guards else ("_shielded" if args.shielded_reader else "")}',
            f'Cload_{name} out_{name} 0 50f',f'.ic v(captured_{name})=0',
            f'Xcapture_{name} out_{name} captured_{name} capture_en capture_enb 0 vdd {reader_cell}__gf180_fixed_body_tg_fullroute',
            f'Xcapinit_{name} vcm captured_{name} pre_en pre_enb 0 vdd {reader_cell}__gf180_fixed_body_tg_fullroute',
            f'Xcapturehold_{name} captured_{name} vcm 0 {reader_cell}__gf180_mim_bank_7x7_n9'])
    for name in targets:
        lines.extend([f'Xheld_buffer_{name} captured_{name} buffered_{name} buffered_{name} vdd 0 bias buffer_cmp_{name} gf180_shared_ota_core_pmos_input_fullroute',
            f'Xbuffer_comp_{name} buffer_cmp_{name} buffered_{name} cap_mim_2f0_m4m5_noshield c_length=7u c_width=7u',f'Cbuffer_load_{name} buffered_{name} 0 50f'])
        if args.inverse:
            lines.extend([f'Xinverse_{name} vcm inverse_sum_{name} inverse_{name} vdd 0 bias inverse_cmp_{name} gf180_shared_ota_core_pmos_input_fullroute',
                f'Xinv_comp_{name} inverse_cmp_{name} inverse_{name} cap_mim_2f0_m4m5_noshield c_length=7u c_width=7u',f'Cinv_load_{name} inverse_{name} 0 50f',
                f'Xrin_{name} buffered_{name} inverse_sum_{name} 0 ppolyf_u_1k r_width=1u r_length=123u'])
            chain=[f'inverse_{name}',f'r1_{name}',f'r2_{name}',f'r3_{name}',f'inverse_sum_{name}']
            for i in range(4):lines.append(f'Xrf_{name}_{i} {chain[i]} {chain[i+1]} 0 ppolyf_u_1k r_width=1u r_length=123u')
    if args.combined_buffer:
        lines=[line for line in lines if not line.startswith(('Xheld_buffer_','Xbuffer_comp_'))]
        for name in targets:lines.append(f'Xphysical_buffer_{name} captured_{name} buffered_{name} vdd 0 bias buffer_cmp_{name} gf180_held_output_buffer_guarded')
    if args.combined_capture:
        lines=[line for line in lines if not line.startswith(('Xcapture_','Xcapinit_','Xcapturehold_'))]
        for name in targets:lines.append(f'Xcapturemacro_{name} out_{name} vcm captured_{name} vdd 0 capture_en capture_enb pre_en pre_enb gf180_reader_output_capture_guarded')
    if args.capture_dummy and not args.combined_capture:
        for name in targets:lines.append(f'Xcapture_dummy_{name} captured_{name} captured_{name} capture_enb capture_en 0 vdd {reader_cell}__gf180_fixed_body_tg_fullroute_half')
    if args.isolate=='switch_only':
        lines=[line for line in lines if not line.startswith('Xcapturehold_')]
    elif args.isolate=='hold_only':
        lines=[line for line in lines if not line.startswith('Xcapture_')]
    if args.input_series_ohm:
        for name in targets:
            lines=[line.replace(f'Vin_{name} input_{name} 0',f'Vin_{name} drive_{name} 0') for line in lines]
            lines.append(f'Rbench_input_{name} drive_{name} input_{name} {args.input_series_ohm}')
    if args.settled_acquisition:
        lines=[line.replace('990n','19990n').replace('1u 0','20u 0').replace('1u 3.3','20u 3.3').replace('970n','19970n').replace('980n','19980n').replace('5.002m','5.021m') for line in lines]
    lines.extend(['Vread read_en 0 PWL(0 0 29.99u 0 30u 3.3 44.99u 3.3 45u 0 5.021m 0)',
        'Vreadb read_enb 0 PWL(0 3.3 29.99u 3.3 30u 0 44.99u 0 45u 3.3 5.021m 3.3)',
        'Vpre pre_en 0 PWL(0 3.3 29.97u 3.3 29.98u 0 5.021m 0)',
        'Vpreb pre_enb 0 PWL(0 0 29.97u 0 29.98u 3.3 5.021m 3.3)'])
    lines.extend(['Vcapture capture_en 0 PWL(0 0 34.99u 0 35u 3.3 44.49u 3.3 44.5u 0 50u 0)',
        'Vcaptureb capture_enb 0 PWL(0 3.3 34.99u 3.3 35u 0 44.49u 0 44.5u 3.3 50u 3.3)'])
    if args.physical_capture_clocks:
        lines=[line.replace('Vcapture capture_en 0','Vcapture capture_command 0') for line in lines if not line.startswith('Vcaptureb ')]
        lines.extend(['Xcapture_clock_b capture_command capture_enb vdd 0 gf180_phase_inverter_fullroute','Xcapture_clock capture_enb capture_en vdd 0 gf180_phase_inverter_fullroute'])
    if args.physical_all_clocks:
        for source,node,complement,complement_source in [('Ven','en','enb','Venb'),('Vben','ben','benb','Vbenb'),('Vread','read_en','read_enb','Vreadb'),('Vpre','pre_en','pre_enb','Vpreb')]:
            lines=[line.replace(f'{source} {node} 0',f'{source} {node}_command 0') for line in lines if not line.startswith(complement_source+' ')]
            lines.extend([f'Xclock_b_{node} {node}_command {complement} vdd 0 gf180_phase_inverter_fullroute',f'Xclock_{node} {complement} {node} vdd 0 gf180_phase_inverter_fullroute'])
    lines.extend(['.control','set numdgt=15',f'tran {args.max_step_ns}n {"5.021m" if args.settled_acquisition else "5.002m"} 0 {args.max_step_ns}n uic'])
    for name in targets:
        lines.extend([f'let stored_{name}=v(p_{name})-v(m_{name})',f'let read_{name}=v(out_{name})-v(vcm)',f'let err_{name}=v(sum_{name})-v(vcm)',f'let captured_{name}=v(captured_{name})-v(vcm)',f'let buffered_{name}=v(buffered_{name})-v(vcm)',f'let inverse_{name}=v(inverse_{name})-v(vcm)' if args.inverse else f'let inverse_{name}=buffered_{name}'])
        for phase,time in ([('on','19.96u'),('released','20.1u'),('settled','29u'),('before_read','29.9u'),('during_read','44u'),('before_capture_open','44.48u'),('after_capture_open','44.6u'),('after_read','45.1u'),('held','5.020m')] if args.settled_acquisition else [('on','960n'),('released','1.1u'),('settled','10u'),('held','5.001m')]):
            for signal in ['stored','read','err','captured','buffered','inverse']:
                lines.append(f'meas tran {name}_{signal}_{phase} find {signal}_{name} at={time}')
    for name in targets:
        for node in ['p','m','out','sum']:
            lines.append(f'meas tran node_{name}_{node} find v({node}_{name}) at={"5.020m" if args.settled_acquisition else "5.001m"}')
    lines.extend(['quit','.endc','.end'])
    if args.early_only:
        lines=[line.replace('5.021m','50u').replace('5.020m','49u').replace('5.002m','50u').replace('5.001m','49u') for line in lines]
    if args.operating_point:
        lines=[line.replace(' uic','') for line in lines]
    lines=[line.replace('method=gear','method='+args.integration) for line in lines]
    deck=BASE/'benches'/(stem+'.spice'); deck.write_text('\n'.join(lines)+'\n'); sources.add(deck)
    result=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=result.stdout+result.stderr
    lp=BASE/'results'/(stem+'.log'); lp.write_text(log); sources.add(lp)
    values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_(?:stored|read|err|captured|buffered|inverse)_(?:on|released|settled|before_read|during_read|before_capture_open|after_capture_open|after_read|held))\s*=\s*([-+0-9.eE]+)',log)}
    nodes={k:float(v) for k,v in re.findall(r'(?m)^(node_(?:low|mid|high)_(?:p|m|out|sum))\s*=\s*([-+0-9.eE]+)',log)}
    complete=result.returncode==0 and len(values)==162 and len(nodes)==12 and 'timestep too small' not in log.lower()
    cases=[]
    if complete:
        for name,target in targets.items():
            v={k.removeprefix(name+'_'):x for k,x in values.items() if k.startswith(name+'_')}
            cases.append({'target_v':target,'measurements_v':v,'release_step_mv':1000*(v['stored_released']-v['stored_on']),'hold_drift_mv':1000*(v['stored_held']-v['stored_released']),'late_read_error_mv':None,'virtual_sum_error_mv':1000*v['err_during_read'],'uncorrected_charge_read_gain':-v['read_during_read']/v['stored_before_read'] if abs(v['stored_before_read'])>.01 else None,'held_buffer_error_uv':1e6*(v['buffered_held']-v['captured_held']),'inverse_implemented':args.inverse,'inverse_gain_from_held_buffer':-v['inverse_held']/v['buffered_held'] if args.inverse and abs(v['buffered_held'])>.01 else None,'inverse_output_held_mv':1000*v['inverse_held'] if args.inverse else None,'capture_release_step_mv':1000*(v['captured_after_capture_open']-v['captured_before_capture_open']),'capture_immediate_error_mv':1000*(v['captured_after_capture_open']-v['read_before_capture_open']),'capture_post_release_drift_uv':1e6*(v['captured_held']-v['captured_after_capture_open']),'capture_preservation_error_mv':1000*(v['captured_held']-v['read_during_read']),'captured_output_held_mv':1000*v['captured_held'],'output_baseline_before_read_mv':1000*v['read_before_read'],'output_after_transfer_mv':1000*v['read_during_read'],'access_disturbance_mv':1000*(v['stored_during_read']-v['stored_before_read']),'disconnect_disturbance_mv':1000*(v['stored_after_read']-v['stored_during_read'])})
    report={'simulation_completed':complete,'returncode':result.returncode,'settings':vars(args),'held_measurement_time_s':49e-6 if args.early_only else (5.020e-3 if args.settled_acquisition else 5.001e-3),'five_ms_hold_completed':complete and not args.early_only,'held_terminal_voltages_v':nodes,'cases':cases,'source_snapshot':snapshot.relative_to(ROOT).as_posix(),
        'scope':'Typical27C actual combined-reader cap extraction connected schematically to qualified shielded sampler. Reader GDS full DRC/LVS qualified; includes3fullTG accesses/reset, halfTG reset dummy, corrected7MOS OTA,9feedback MIMs plus1compensation MIM and newly extracted routing. Sampler-reader interconnect and PF diode bias still schematic, with ideal input/reference/clock/current sources and ideal50fF output load. Destructive charge read requires physical analog inverse/restore. Output retained without ideal subtraction. Output capture uses two extracted fullTG primitives, optional physical halfTG opposite-clock dummy on held node, and an extracted9x7um bank connected schematically, sampling35-44.5us before read disconnect45us; Separate-primitive mode has no combined capture routing; optional combined-capture mode uses GDS-qualified gf180_reader_output_capture_guarded with every newly extracted routing capacitance. Reader-to-capture and driver interconnect remain schematic. Optional100ohm input-source series resistance is a schematic ideal-R bench driver assumption, not a qualified resistor or measured silicon driver. Isolation mode can remove either access switch or hold bank to locate the failing interaction; those circuits do not establish complete capture. Optional all-clock mode also drives acquisition, bottom-plate, reader access and reset through two extracted inverters per phase; no timing/driver acceptance inferred. Optional capture-clock driver is two qualified cap-extracted inverters driven by one ideal logical command, wired schematically; finite edge/load delay is simulated. Held output adds actual corrected extracted OTA follower; combined-buffer mode uses GDS-qualified gf180_held_output_buffer_guarded including native routed compensation and feedback, replacing separate schematic compensation. Separate-primitive buffer mode with native schematic7um compensation and ideal50fF load. Optional analog inverse is a second corrected extracted OTA with1input and4series feedback native model123umx1um poly resistors, res_typical27C; these resistors and compensation are schematic and not a qualified combined inverse layout. Ideal ratio4 is a design target, not calibrated inverse of actual routed read gain or nonlinear encoding. No restore connection/phase yet. No ideal correction. No RPEX, sampled noise, mismatch/PVT, gate leakage qualification, calibrated inverse, restore/PLIF or population5ms acceptance.',
        'physical_storage_accepted':False,'read_restore_accepted':False,'full_chip_accepted':False,
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    rp=BASE/'results'/(stem+'.json'); rp.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(rp),'simulation_completed':complete,'cases':cases},indent=2))
    if not complete: raise RuntimeError(log[-2000:])
if __name__=='__main__': main()
