"""Actual analog read/restore with simultaneous or reversed plate release."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--membrane-window",action="store_true")
    parser.add_argument("--settled-acquisition",action="store_true")
    parser.add_argument("--max-step-ns",type=int,choices=[10,20,100,1000],default=100)
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
    parser.add_argument("--long-hold",action="store_true")
    parser.add_argument("--physical-inverse-resistors",action="store_true")
    parser.add_argument("--combined-inverse",action="store_true")
    parser.add_argument("--zero-reference",action="store_true")
    parser.add_argument("--combined-zero-reference",action="store_true")
    parser.add_argument("--trim-inverse",action="store_true")
    parser.add_argument("--bottom-lead-ns",type=int,choices=[-20,0,20],default=20)
    args=parser.parse_args()
    inverse_cell="gf180_inverse_amplifier_rf126_guarded" if args.trim_inverse else "gf180_inverse_amplifier_guarded"
    if args.combined_zero_reference:args.zero_reference=True
    if not args.combined_inverse:raise ValueError("Zero-reference screen requires actual combined inverse amplifier")
    if args.combined_inverse:args.physical_inverse_resistors=True
    if args.input_series_ohm:raise ValueError("Restore mux diagnostic requires initialization source disconnected without a bypass series path")
    if not (args.inverse and args.physical_all_clocks and args.combined_capture and args.combined_buffer):raise ValueError('Identity restore requires inverse and actual clock/capture/buffer chain')
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
    if args.physical_inverse_resistors:cells.append('gf180_inverse_resistor_network_123x1')
    if args.combined_inverse:cells.append(inverse_cell)
    if args.combined_zero_reference:cells.append('gf180_zero_reference_buffer_guarded')
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
    stem='gf180_release_order_restore_inverse'+str(int(args.inverse))+'_step'+str(args.max_step_ns)+'_settings'+hashlib.sha256(json.dumps(vars(args),sort_keys=True).encode()).hexdigest()[:10]+'_src'+digest(Path(__file__))[:12]
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
    targets['cal']=1.65
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
    if args.physical_inverse_resistors:
        lines=[line for line in lines if not line.startswith(('Xrin_','Xrf_'))]
        for name in targets:
            lines.append(f'Xphysical_inverse_resistors_{name} buffered_{name} inverse_sum_{name} inverse_{name} r1_{name} r2_{name} r3_{name} 0 gf180_inverse_resistor_network_123x1')
    if args.combined_inverse:
        lines=[line for line in lines if not line.startswith(('Xinverse_','Xinv_comp_','Xphysical_inverse_resistors_'))]
        for name in targets:
            lines.append(f'Xphysical_inverse_{name} buffered_{name} vcm inverse_sum_{name} inverse_{name} vdd 0 bias inverse_cmp_{name} r1_{name} r2_{name} r3_{name} {inverse_cell}')
    if args.zero_reference:
        # With one unit from held-zero buffer to REF and four units from VCM
        # to REF, REF=(4*held_zero+VCM)/5. Gain-four inverse cancels read zero.
        # This is a native resistor circuit, not correction of measured data.
        lines.append('Xzero_divider buffered_cal zero_ref vcm zero_r1 zero_r2 zero_r3 0 gf180_inverse_resistor_network_123x1')
        for name in ['low','mid','high']:
            lines=[line.replace(f'Xphysical_inverse_{name} buffered_{name} vcm ',f'Xphysical_inverse_{name} buffered_{name} zero_ref ') for line in lines]
    if args.combined_buffer:
        lines=[line for line in lines if not line.startswith(('Xheld_buffer_','Xbuffer_comp_'))]
        for name in targets:lines.append(f'Xphysical_buffer_{name} captured_{name} buffered_{name} vdd 0 bias buffer_cmp_{name} gf180_held_output_buffer_guarded')
    if args.combined_zero_reference:
        lines=[line for line in lines if not line.startswith(('Xphysical_buffer_cal ','Xzero_divider '))]
        lines.append('Xzero_reference_macro captured_cal buffered_cal zero_ref vcm vdd 0 bias buffer_cmp_cal zero_r1 zero_r2 zero_r3 gf180_zero_reference_buffer_guarded')
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
    for name in targets:
        lines=[line.replace(f'Vin_{name} input_{name} 0',f'Vin_{name} initialize_{name} 0') for line in lines]
        lines.extend([f'Xinitialmux_{name} initialize_{name} input_{name} init_en init_enb 0 vdd {reader_cell}__gf180_fixed_body_tg_fullroute',f'Xrestoremux_{name} inverse_{name} input_{name} restore_en restore_enb 0 vdd {reader_cell}__gf180_fixed_body_tg_fullroute'])
    lines=[line.replace('20u 0 5.021m 0','20u 0 59.99u 0 60u 3.3 79.99u 3.3 80u 0 5.021m 0').replace('19980n 0 5.021m 0','19980n 0 59.99u 0 60u 3.3 79.97u 3.3 79.98u 0 5.021m 0') for line in lines]
    lines.extend(['Vinit init_command 0 PWL(0 3.3 24.99u 3.3 25u 0 90u 0)','Vrestore restore_command 0 PWL(0 0 57.99u 0 58u 3.3 80.09u 3.3 80.1u 0 90u 0)',
        'Xinit_b init_command init_enb vdd 0 gf180_phase_inverter_fullroute','Xinit init_enb init_en vdd 0 gf180_phase_inverter_fullroute',
        'Xrestore_b restore_command restore_enb vdd 0 gf180_phase_inverter_fullroute','Xrestore restore_enb restore_en vdd 0 gf180_phase_inverter_fullroute'])
    lines=[line.replace('19970n',f'{20000-args.bottom_lead_ns-10}n').replace('19980n',f'{20000-args.bottom_lead_ns}n').replace('79.97u',f'{80000-args.bottom_lead_ns-10}n').replace('79.98u',f'{80000-args.bottom_lead_ns}n') for line in lines]
    lines.extend(['.control','set numdgt=15',f'tran {args.max_step_ns}n {"5.021m" if args.settled_acquisition else "5.002m"} 0 {args.max_step_ns}n uic'])
    for name in targets:
        lines.extend([f'let stored_{name}=v(p_{name})-v(m_{name})',f'let read_{name}=v(out_{name})-v(vcm)',f'let err_{name}=v(sum_{name})-v(vcm)',f'let captured_{name}=v(captured_{name})-v(vcm)',f'let buffered_{name}=v(buffered_{name})-v(vcm)',f'let inverse_{name}=v(inverse_{name})-v(vcm)' if args.inverse else f'let inverse_{name}=buffered_{name}'])
        for phase,time in ([('on',f'{20000-max(args.bottom_lead_ns,0)-20}n'),('released','20.1u'),('settled','29u'),('before_read','29.9u'),('during_read','44u'),('before_capture_open','44.48u'),('after_capture_open','44.6u'),('after_read','45.1u'),('before_restore','59u'),('during_restore',f'{80000-max(args.bottom_lead_ns,0)-80}n'),('after_restore','80.2u'),('before_hold','89u'),('held','5.020m')] if args.settled_acquisition else [('on','960n'),('released','1.1u'),('settled','10u'),('held','5.001m')]):
            for signal in ['stored','read','err','captured','buffered','inverse']:
                lines.append(f'meas tran {name}_{signal}_{phase} find {signal}_{name} at={time}')
    for name in targets:
        for node in ['p','m','out','sum']:
            lines.append(f'meas tran node_{name}_{node} find v({node}_{name}) at={"5.020m" if args.settled_acquisition else "5.001m"}')
    if args.zero_reference:
        lines.extend(['let zero_reference=v(zero_ref)-v(vcm)','meas tran zero_reference_before_restore find zero_reference at=59u','meas tran zero_reference_held find zero_reference at=89u'])
    lines.extend(['quit','.endc','.end'])
    if args.early_only:
        lines=[line.replace('5.021m','90u').replace('5.020m','89u').replace('5.002m','90u').replace('5.001m','89u').replace('50u','90u') for line in lines]
    if args.long_hold:
        lines=[line.replace('90u','5.081m') if line.startswith(('tran ','V')) else line.replace('at=89u','at=5.080m') if ('_held ' in line or line.startswith('meas tran node_')) else line for line in lines]
    if args.operating_point:
        lines=[line.replace(' uic','') for line in lines]
    lines=[line.replace('method=gear','method='+args.integration) for line in lines]
    deck=BASE/'benches'/(stem+'.spice'); deck.write_text('\n'.join(lines)+'\n'); sources.add(deck)
    result=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=result.stdout+result.stderr
    lp=BASE/'results'/(stem+'.log'); lp.write_text(log); sources.add(lp)
    values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high|cal)_(?:stored|read|err|captured|buffered|inverse)_(?:on|released|settled|before_read|during_read|before_capture_open|after_capture_open|after_read|before_restore|during_restore|after_restore|before_hold|held))\s*=\s*([-+0-9.eE]+)',log)}
    nodes={k:float(v) for k,v in re.findall(r'(?m)^(node_(?:low|mid|high|cal)_(?:p|m|out|sum))\s*=\s*([-+0-9.eE]+)',log)}
    complete=result.returncode==0 and len(values)==312 and len(nodes)==16 and 'timestep too small' not in log.lower()
    cases=[]
    if complete:
        for name,target in targets.items():
            v={k.removeprefix(name+'_'):x for k,x in values.items() if k.startswith(name+'_')}
            cases.append({'target_v':target,'measurements_v':v,'release_step_mv':1000*(v['stored_released']-v['stored_on']),'hold_drift_mv':1000*(v['stored_held']-v['stored_released']),'late_read_error_mv':None,'virtual_sum_error_mv':1000*v['err_during_read'],'uncorrected_charge_read_gain':-v['read_during_read']/v['stored_before_read'] if abs(v['stored_before_read'])>.01 else None,'post_restore_hold_drift_uv':1e6*(v['stored_held']-v['stored_before_hold']),'restore_acquired_error_mv':1000*(v['stored_during_restore']-v['stored_before_read']),'restore_release_step_mv':1000*(v['stored_after_restore']-v['stored_during_restore']),'round_trip_error_mv':1000*(v['stored_held']-v['stored_before_read']),'round_trip_error_vs_initial_target_mv':1000*(v['stored_held']-(target-1.65)),'held_buffer_error_uv':1e6*(v['buffered_held']-v['captured_held']),'inverse_implemented':args.inverse,'inverse_gain_from_held_buffer':-v['inverse_held']/v['buffered_held'] if args.inverse and abs(v['buffered_held'])>.01 else None,'inverse_output_held_mv':1000*v['inverse_held'] if args.inverse else None,'capture_release_step_mv':1000*(v['captured_after_capture_open']-v['captured_before_capture_open']),'capture_immediate_error_mv':1000*(v['captured_after_capture_open']-v['read_before_capture_open']),'capture_post_release_drift_uv':1e6*(v['captured_held']-v['captured_after_capture_open']),'capture_preservation_error_mv':1000*(v['captured_held']-v['read_during_read']),'captured_output_held_mv':1000*v['captured_held'],'output_baseline_before_read_mv':1000*v['read_before_read'],'output_after_transfer_mv':1000*v['read_during_read'],'access_disturbance_mv':1000*(v['stored_during_read']-v['stored_before_read']),'disconnect_disturbance_mv':1000*(v['stored_after_read']-v['stored_during_read'])})
    zero_measurements={k:float(v) for k,v in re.findall(r'(?m)^(zero_reference_(?:before_restore|held))\s*=\s*([-+0-9.eE]+)',log)}
    if args.zero_reference and len(zero_measurements)!=2:complete=False
    report={'simulation_completed':complete,'returncode':result.returncode,'settings':vars(args),'post_restore_hold_completed':complete and args.long_hold,'held_measurement_time_s':5.080e-3 if args.long_hold else 89e-6 if args.early_only else (5.020e-3 if args.settled_acquisition else 5.001e-3),'five_ms_hold_completed':complete and not args.early_only,'held_terminal_voltages_v':nodes,'cases':cases[:3],'dedicated_zero_case':cases[3] if len(cases)==4 else None,'zero_reference_measurements_v':zero_measurements,'zero_reference_enabled':args.zero_reference,'source_snapshot':snapshot.relative_to(ROOT).as_posix(),
        'scope':'Typical27C actual combined-reader cap extraction connected schematically to qualified shielded sampler. Reader GDS full DRC/LVS qualified; includes3fullTG accesses/reset, halfTG reset dummy, corrected7MOS OTA,9feedback MIMs plus1compensation MIM and newly extracted routing. Sampler-reader interconnect and PF diode bias still schematic, with ideal input/reference/clock/current sources and ideal50fF output load. Destructive charge read requires physical analog inverse/restore. Output retained without ideal subtraction. Output capture uses two extracted fullTG primitives, optional physical halfTG opposite-clock dummy on held node, and an extracted9x7um bank connected schematically, sampling35-44.5us before read disconnect45us; Separate-primitive mode has no combined capture routing; optional combined-capture mode uses GDS-qualified gf180_reader_output_capture_guarded with every newly extracted routing capacitance. Reader-to-capture and driver interconnect remain schematic. Optional100ohm input-source series resistance is a schematic ideal-R bench driver assumption, not a qualified resistor or measured silicon driver. Isolation mode can remove either access switch or hold bank to locate the failing interaction; those circuits do not establish complete capture. Optional all-clock mode also drives acquisition, bottom-plate, reader access and reset through two extracted inverters per phase; no timing/driver acceptance inferred. Optional capture-clock driver is two qualified cap-extracted inverters driven by one ideal logical command, wired schematically; finite edge/load delay is simulated. Held output adds actual corrected extracted OTA follower; combined-buffer mode uses GDS-qualified gf180_held_output_buffer_guarded including native routed compensation and feedback, replacing separate schematic compensation. Separate-primitive buffer mode with native schematic7um compensation and ideal50fF load. Optional analog inverse is a second corrected extracted OTA with1input and4series feedback native model123umx1um poly resistors, res_typical27C; default resistors and compensation are schematic; optional physical-inverse-resistors replaces the five resistor models with the GDS-qualified native network including extracted capacitances. Its amplifier interconnect and compensation remain schematic, with no qualified combined inverse layout. Ideal ratio4 is a design target, not calibrated inverse of actual routed read gain or nonlinear encoding. Identity read/restore fixture now uses real extracted TG input muxes: external initialization disconnects25us; inverse output connects58us, actual sampler reacquires60-80us with bottom opens20ns earlier, restore mux disconnects80.1us; observation89us or optional5.080ms after restore80us. Long-hold native-card retention remains unqualified for actual gate leakage, noise and temperature. This is a linear storage interface fixture, not nonlinear companding/complete PLIF, and the uncalibrated resistor ratio4 cannot establish neural accuracy. No ideal waveform forces stored state after initialization. No ideal correction. No RPEX, sampled noise, mismatch/PVT, gate leakage qualification, calibrated inverse, restore/PLIF or population5ms acceptance.',
        'physical_inverse_resistor_network':args.physical_inverse_resistors,
        'combined_inverse_amplifier':args.combined_inverse,
        'inverse_resistor_scope':'GDS-qualified five-unit native network including extracted capacitances; amplifier interconnect schematic' if args.physical_inverse_resistors else 'Schematic native model resistors only',
        'physical_storage_accepted':False,'read_restore_accepted':False,'full_chip_accepted':False,
        'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    if args.combined_inverse:
        report['inverse_resistor_scope']='GDS-qualified combined seven-MOS inverse amplifier, five native resistors and native compensation; all internal routing capacitances included. Held-buffer and restore-mux interconnect remains schematic.'
        report['scope']+=' Combined-inverse mode replaces the separate OTA, compensation and resistor network with gf180_inverse_amplifier_guarded including all parent routing and contextual child extraction. Its nominal gain remains uncalibrated.'
    report['scope']+=' Dedicated fourth known-zero sampler/reader/capture/buffer path is independent of the three data cases and shares loaded clock drivers. Optional physical five-unit resistor divider delivers (4*held_zero+VCM)/5 to data inverse reference inputs. Reference and amplifier interconnect remain schematic. Calibration estimates common read/capture offset only; gain, reference-state acquisition error and signal-dependent restore release remain. No postprocessed state correction or neural accuracy acceptance.'
    report['commanded_release_order']='top_first_20ns' if args.bottom_lead_ns<0 else 'simultaneous' if args.bottom_lead_ns==0 else 'bottom_first_20ns'
    report['commanded_bottom_lead_ns']=args.bottom_lead_ns
    report['initial_acquired_measurement_time_ns']=20000-max(args.bottom_lead_ns,0)-20
    report['restore_acquired_measurement_time_ns']=80000-max(args.bottom_lead_ns,0)-80
    report['scope']+=' Bottom-plate logical falling command precedes top-plate command by signed configurable-20/0/+20ns (negative means top first) during initialization and restore. Actual extracted inverters and load determine electrical edges; no ideal nonoverlap or sequencer acceptance. Acquired samples precede the first plate command transition, so measurements are comparable phase-wise rather than at identical timestamps. Initial acquisition/read/zero-reference behavior may change as well as restore release.'
    report['native_gain_trim']=args.trim_inverse
    report['nominal_inverse_gain_magnitude']=495/123 if args.trim_inverse else 4
    if args.trim_inverse:report['scope']+=' Native gain trim uses implemented input123um and series feedback123+123+123+126um, ratio495/123=4.02439024. Zero divider retains its existing4/5 ratio. This fixed geometry is a nominal diagnostic, not per-die calibrated or nonlinear inverse acceptance.'
    report['combined_zero_reference_buffer']=args.combined_zero_reference
    if args.combined_zero_reference:
        report['scope']+=' Combined-zero-reference mode implements the zero-buffer unity feedback, five-resistor divider and native compensation in one GDS-qualified macro with all extracted internal routing/contextual capacitances; macro-to-macro connections remain schematic.'
    rp=BASE/'results'/(stem+'.json'); rp.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(rp),'simulation_completed':complete,'cases':cases},indent=2))
    if not complete: raise RuntimeError(log[-2000:])
if __name__=='__main__': main()
