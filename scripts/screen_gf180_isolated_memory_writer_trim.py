"""Frozen native writer resistor/reference trim for isolated memory."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bus-mode',choices=['direct','isolated'],required=True)
    parser.add_argument('--capacitor', choices=['bank9','minimum'], required=True)
    parser.add_argument('--read-disabled', action='store_true')
    parser.add_argument('--read-clamp-v', type=float, choices=[0.01,1.65], default=0.01)
    args = parser.parse_args()
    source = Path(__file__)
    stem = 'gf180_isolated_memory_writer_trim_'+hashlib.sha256(json.dumps(vars(args),sort_keys=True).encode()).hexdigest()[:10]+'_src'+sha(source)[:12]
    report_path = BASE/'results'/(stem+'.json')
    assert not report_path.exists(), 'Preserve prior evidence'
    assert args.capacitor=='minimum' and args.bus_mode=='isolated'
    module='gf180_isolated_memory_characterization_fullroute'
    cap = 'gf180_mim_bank_7x7_n9' if args.capacitor=='bank9' else 'gf180_mim_5x5_ports_routed'
    files = set()
    texts = []
    for cell in [module,'gf180_phase_inverter_fullroute','gf180_shared_ota_core_pmos_input_fullroute','gf180_writeback_resistor_2x1','gf180_writeback_resistor_64x1','gf180_writeback_resistor_4x1']:
        directory = BASE/'layout'/cell
        path = directory/'qualification.json'
        q = json.loads(path.read_text(encoding='utf-8'))
        assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback']
        files.add(path)
        for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
            for name, expected in q.get(key,{}).items():
                item = directory/name if key=='sha256' else ROOT/name
                assert sha(item)==expected, str(item)
                files.add(item)
        text = (directory/(cell+'_cap.spice')).read_text(encoding='utf-8')
        for child in re.findall(r'(?m)^\.subckt (\S+)',text):
            if child!=cell:
                text=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,text)
        texts.extend(text.splitlines())
    if args.capacitor=='minimum':
        audit_path=BASE/'results/gf180_minimum_mim_routed_gds_integrity.json'
        audit=json.loads(audit_path.read_text(encoding='utf-8'))
        assert audit['audit_completed'] and audit['cases'][0]['physical_layout_accepted']
        for name, expected in audit['sha256'].items():
            assert sha(ROOT/name)==expected,name
        files.add(audit_path)
    models=BASE/'pdk/gf180_primitive_source/models/ngspice'
    files.update(models.rglob('*.spice'))
    prefix='/workspace/'+models.relative_to(ROOT).as_posix()
    lines=['Native analog memory write-hold-read diagnostic',f'.include {prefix}/design.spice',
           f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical',
           '.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27',
           '.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,
           'Vdd vdd 0 3.3','Vcm vcm 0 1.65',
           'Vwrite write_command 0 PWL(0 3.3 19.99u 3.3 20u 0 5060u 0)',
           'Vread read_command 0 '+('0' if args.read_disabled else 'PWL(0 0 5049.99u 0 5050u 3.3 5050.99u 3.3 5051u 0 5060u 0)'),
           'Vpark park_command 0 '+('3.3' if args.read_disabled else 'PWL(0 3.3 5049.97u 3.3 5049.98u 0 5051.01u 0 5051.02u 3.3 5060u 3.3)')]
    if args.bus_mode=='isolated':
        lines += ['Vouter outer_command 0 PWL(0 3.3 20.01u 3.3 20.02u 0 5060u 0)', 'Vmidclamp midclamp_command 0 PWL(0 0 20.03u 0 20.04u 3.3 5060u 3.3)']
    lines += ['Iprogram_bias program_bias 0 5u','Xprogram_ref program_bias program_bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u','Vprogram_offset program_offset 0 1.510390449380059']
    for phase in (['write','read','park']+(['outer','midclamp'] if args.bus_mode=='isolated' else [])):
        lines += [f'Xb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',
                  f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute']
    targets={'low':0.75,'mid':1.65,'high':2.55}
    for name, voltage in targets.items():
        # Shared write bus is allowed to serve other states while this cell is off.
        bus=f'PWL(0 {voltage} 30u {voltage} 30.01u 1.65 99.99u 1.65 100u 0.75 199.99u 0.75 200u 2.55 499.99u 2.55 500u 0.75 999.99u 0.75 1000u 2.55 1999.99u 2.55 2000u 0.75 3999.99u 0.75 4000u 2.55 5029.99u 2.55 5030u 1.65 5060u 1.65)'
        lines += [f'Vbus_{name} bus_source_{name} 0 {bus}',f'Rbus_{name} program_out_{name} bus_{name} 1',
                  f'Vcolumn_{name} column_source_{name} 0 {args.read_clamp_v}',f'Rcolumn_{name} column_source_{name} column_{name} 1',
                  f'Xmemory_{name} state_{name} vcm middle_{name} column_{name} drain_{name} write writeb outer outerb midclamp midclampb read readb park parkb 0 vdd bus_{name} {module}',
                  f'.ic v(state_{name})={voltage} v(drain_{name})=0']
        lines += [f'Xprogram_{name} bus_source_{name} feedback_{name} program_out_{name} vdd 0 program_bias program_cmp_{name} gf180_shared_ota_core_pmos_input_fullroute',f'Xfeedback_{name} program_out_{name} feedback_{name} 0 gf180_writeback_resistor_2x1',f'Xgain64_{name} feedback_{name} gain_mid_{name} 0 gf180_writeback_resistor_64x1',f'Xgain2_{name} gain_mid_{name} gain_mid2_{name} 0 gf180_writeback_resistor_2x1',f'Xgain4_{name} gain_mid2_{name} program_offset 0 gf180_writeback_resistor_4x1',f'Xprogram_comp_{name} program_out_{name} program_cmp_{name} cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u']
    lines += ['.control','set numdgt=15','tran 1u 5060u 0 1u uic']
    for name in targets:
        for phase,t in [('acquired',19.9),('released',25),('baseline',40),('held',5040),('reading',5050.5),('after',5054)]:
            lines.append(f'meas tran {name}_state_{phase} find v(state_{name}) at={t}u')
        lines += [f'meas tran {name}_program_acquired find v(program_out_{name}) at=19.9u',f'meas tran {name}_program_idle find v(program_out_{name}) at=40u']
        lines += [f'meas tran {name}_state_window_min min v(state_{name}) from=40u to=5040u',f'meas tran {name}_state_window_max max v(state_{name}) from=40u to=5040u']
        lines += [f'let release_{name}=v(state_{name})-{name}_state_acquired',f'meas tran {name}_release_error find release_{name} at=25u',
                  f'let hold_{name}=v(state_{name})-{name}_state_baseline',f'meas tran {name}_hold_error find hold_{name} at=5040u',
                  f'let read_{name}=v(state_{name})-{name}_state_held',f'meas tran {name}_read_error find read_{name} at=5054u',
                  f'meas tran {name}_read_current find i(Vcolumn_{name}) at=5050.5u',
                  f'meas tran {name}_read_drain find v(drain_{name}) at=5050.5u']
    lines += ['quit','.endc','.end']
    deck=BASE/'benches'/(stem+'.spice')
    deck.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    snapshot=BASE/'tools/source_snapshots'/(stem+'.py')
    snapshot.write_bytes(source.read_bytes())
    files.update([deck,snapshot])
    run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace',
                        '--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b',
                        '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=run.stdout+run.stderr
    log_path=BASE/'results'/(stem+'.log')
    log_path.write_text(log,encoding='utf-8')
    files.add(log_path)
    values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_(?:state_(?:acquired|released|baseline|held|reading|after|window_min|window_max)|release_error|hold_error|read_error|read_current|read_drain|program_acquired|program_idle))\s*=\s*([-+0-9.eE]+)',log)}
    complete=run.returncode==0 and len(values)==45 and 'timestep too small' not in log.lower() and 'simulation(s) aborted' not in log.lower()
    report={'simulation_completed':complete,'simulator_returncode':run.returncode,'settings':vars(args),'measurements':values,
            'hold_interval_us':5000,'write_reference_v':1.5103904493800588,'nominal_feedback_ratio':'2/(64+2+4) native poly resistor lengths; actual resistor models determine gain','write_bias_ua':5,'writer_state_terminal':'A; matched baseline used B','physical_children_qualified':True,'combined_memory_layout_qualified':False,
            'scope':'Isolated mode adds real extracted quarterTG outer bus switch and middle-node VCM clamp, releasing outer20ns after inner writer and clamping20ns later. All five quarterTGs, sense transistor, MIM and their internal wiring are now in one full DRC/LVS/GDS-readback qualified cap-extracted module; external drivers/references remain schematic. Actual native seven-MOS OTA and native poly-resistor feedback drive the write bus; no corrected held voltage is forced and no numeric state subtraction. One native4um resistor added to gain leg; common ideal offset reference predicted from prior physical writer center and nominal66/70 gain-leg adjustment. No iterative pointwise correction. Ideal reference remains external; it is not an implemented reference generator. Added programmer/compensation/interconnect schematic, not combined physical qualification. Direct mode is matched control. Writer connects held state to extracted quarterTG A rather than B; transistor cards/layout capacitances unchanged and mapped to actual terminals. No arithmetic correction or forced held state. Entire physical eleven-MOS/5um MIM isolated memory characterization module imported with extracted internal routing; native external clock inverters. Three stored levels, shared write-bus activity while writer off, zero-parked drain and one1us read after5ms. Internal state/write/read/park/body/cap interconnect is physically qualified by full DRC/LVS/GDS readback and cap extraction. External clock/bus/column interface wiring remains schematic; RPEX absent. Spacious characterization macro is not a dense array cell or minimum footprint; actual dimensions are in its physical qualification. Ideal external write references, column voltage clamp and supply/VCM;1ohm bench source impedances. Column current is an observable, not implemented precision decode or range conversion. Sampling noise disabled; native gate leakage disabled/unqualified, MIM dielectric leakage and temperature/PVT/mismatch not qualified. Completed deterministic hold is not physical retention acceptance. The fixed-sense transistor is resident per state; its array area/current remains to be budgeted. No beta/reset/adaptation/weighted input, original-float accuracy, autonomous service or full-chip acceptance.',
            'physical_storage_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,
            'full_5ms_population_service_accepted':False,'full_chip_accepted':False,
            'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(report_path),'simulation_completed':complete,'measurements':values},indent=2))
    if not complete:
        raise RuntimeError(log[-1500:])

if __name__=='__main__':
    main()
