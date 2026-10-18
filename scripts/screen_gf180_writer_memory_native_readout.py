"""Actual writer-memory parent with native regulated current-matching readout transient."""
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
    parser.add_argument('--levels',default='1.2,1.65,2.1')
    parser.add_argument('--bus-mode',choices=['direct','isolated'],required=True)
    parser.add_argument('--capacitor', choices=['bank9','minimum'], required=True)
    parser.add_argument('--read-disabled', action='store_true')
    parser.add_argument('--read-clamp-v', type=float, choices=[0.01,1.65], default=0.01)
    args = parser.parse_args()
    source = Path(__file__)
    stem = 'gf180_writer_memory_native_readout_'+hashlib.sha256(json.dumps(vars(args),sort_keys=True).encode()).hexdigest()[:10]+'_src'+sha(source)[:12]
    report_path = BASE/'results'/(stem+'.json')
    assert not report_path.exists(), 'Preserve prior evidence'
    assert args.capacitor=='minimum' and args.bus_mode=='isolated'
    module='gf180_writer_memory_characterization_localpins'
    cap = 'gf180_mim_bank_7x7_n9' if args.capacitor=='bank9' else 'gf180_mim_5x5_ports_routed'
    prediction_path=BASE/'results/gf180_writer_memory_reference_prediction.json'
    prediction=json.loads(prediction_path.read_text(encoding='utf-8'))
    calibration=ROOT/prediction['calibration_report']
    assert sha(calibration)==prediction['calibration_sha256']
    write_reference=prediction['predicted_reference_v']
    files = {prediction_path,calibration}
    texts = []
    for cell in [module,'gf180_phase_inverter_fullroute','gf180_shared_ota_core_pmos_input_fullroute','gf180_source_pf05_l1_fullroute','gf180_nondestructive_sense_nf05_l1_fullroute','gf180_fixed_body_tg_fullroute_quarter']:
        directory = BASE/'layout'/cell
        path = directory/'qualification.json'
        q = json.loads(path.read_text(encoding='utf-8'))
        assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback']
        assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique']
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
           '.global VSUBS','Vsubstrate VSUBS 0 0','Vdd vdd 0 3.3','Vcm vcm 0 1.65','Vclamp clamp 0 .01',
           'Vwrite write_command 0 PWL(0 3.3 19.99u 3.3 20u 0 5080u 0)',
           'Vread read_command 0 '+('0' if args.read_disabled else 'PWL(0 0 5049.99u 0 5050u 3.3 5074.99u 3.3 5075u 0 5080u 0)'),
           'Vpark park_command 0 '+('3.3' if args.read_disabled else 'PWL(0 3.3 5049.97u 3.3 5049.98u 0 5075.01u 0 5075.02u 3.3 5080u 3.3)')]
    if args.bus_mode=='isolated':
        lines += ['Vouter outer_command 0 PWL(0 3.3 20.01u 3.3 20.02u 0 5080u 0)', 'Vmidclamp midclamp_command 0 PWL(0 0 20.03u 0 20.04u 3.3 5080u 3.3)']
    lines += ['Iprogram_bias program_bias 0 5u','Xprogram_ref program_bias program_bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',f'Vprogram_offset program_offset 0 {write_reference:.16g}']
    for phase in (['write','read','park']+(['outer','midclamp'] if args.bus_mode=='isolated' else [])):
        lines += [f'Xb_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',
                  f'Xc_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute']
    level_values=[float(x) for x in args.levels.split(',')];assert len(level_values)==3 and all(.75<=v<=2.55 for v in level_values)
    targets=dict(zip(['low','mid','high'],level_values))
    for name, voltage in targets.items():
        # Shared write bus is allowed to serve other states while this cell is off.
        bus=f'PWL(0 {voltage} 30u {voltage} 30.01u 1.65 99.99u 1.65 100u 0.75 199.99u 0.75 200u 2.55 499.99u 2.55 500u 0.75 999.99u 0.75 1000u 2.55 1999.99u 2.55 2000u 0.75 3999.99u 0.75 4000u 2.55 5029.99u 2.55 5030u 1.65 5080u 1.65)'
        lines += [f'Vbus_{name} bus_source_{name} 0 {bus}',
                  f'Vcolumn_{name} feedcol_{name} column_{name} 0',
                  f'Xmemory_{name} state_{name} vcm middle_{name} column_{name} drain_{name} write writeb outer outerb midclamp midclampb read readb park parkb 0 vdd program_out_{name} bus_source_{name} program_offset feedback_{name} program_bias program_cmp_{name} gain_mid_{name} gain_mid2_{name} {module}',
                  f'.ic v(state_{name})={voltage} v(drain_{name})=0']

        lines += [f'Xreadclamp_{name} column_{name} clamp mirror_gate_{name} vdd 0 program_bias readcmp1_{name} gf180_shared_ota_core_pmos_input_fullroute',f'Xreadfeed_{name} feedcol_{name} mirror_gate_{name} vdd vdd gf180_source_pf05_l1_fullroute',f'Xrepfeed_{name} refcol_{name} mirror_gate_{name} vdd vdd gf180_source_pf05_l1_fullroute',f'Xrepselect_{name} refdrain_{name} refcol_{name} read readb 0 vdd gf180_fixed_body_tg_fullroute_quarter',f'Xreplica_{name} refdrain_{name} decoded_{name} 0 0 gf180_nondestructive_sense_nf05_l1_fullroute',f'Xreadinverse_{name} refcol_{name} clamp decoded_{name} vdd 0 program_bias readcmp2_{name} gf180_shared_ota_core_pmos_input_fullroute',f'Xreadcomp1_{name} mirror_gate_{name} readcmp1_{name} cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u',f'Xreadcomp2_{name} decoded_{name} readcmp2_{name} cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u']

    lines += ['.control','set numdgt=15','tran 1u 5080u 0 1u uic']
    for name in targets:
        for phase,t in [('acquired',19.9),('released',25),('baseline',40),('held',5040),('reading',5074.5),('after',5078)]:
            lines.append(f'meas tran {name}_state_{phase} find v(state_{name}) at={t}u')
        lines += [f'meas tran {name}_program_acquired find v(program_out_{name}) at=19.9u',f'meas tran {name}_program_idle find v(program_out_{name}) at=40u']
        lines += [f'meas tran {name}_state_window_min min v(state_{name}) from=40u to=5040u',f'meas tran {name}_state_window_max max v(state_{name}) from=40u to=5040u']
        lines += [f'let release_{name}=v(state_{name})-{name}_state_acquired',f'meas tran {name}_release_error find release_{name} at=25u',
                  f'let hold_{name}=v(state_{name})-{name}_state_baseline',f'meas tran {name}_hold_error find hold_{name} at=5040u',
                  f'let read_{name}=v(state_{name})-{name}_state_held',f'meas tran {name}_read_error find read_{name} at=5078u',
                  f'meas tran {name}_read_current find i(Vcolumn_{name}) at=5074.5u',
                  f'meas tran {name}_read_drain find v(drain_{name}) at=5074.5u']
        for label,time in [('early',5050.5),('five',5055),('twenty',5070),('late',5074.5)]:
            lines.append(f'meas tran {name}_decoded_{label} find v(decoded_{name}) at={time}u')
        lines.append(f'meas tran {name}_column_v find v(column_{name}) at=5074.5u')
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
    values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_(?:state_(?:acquired|released|baseline|held|reading|after|window_min|window_max)|release_error|hold_error|read_error|read_current|read_drain|program_acquired|program_idle|decoded_(?:early|five|twenty|late)|column_v))\s*=\s*([-+0-9.eE]+)',log)}
    complete=run.returncode==0 and len(values)==60 and 'timestep too small' not in log.lower() and 'simulation(s) aborted' not in log.lower()
    report={'simulation_completed':complete,'simulator_returncode':run.returncode,'settings':vars(args),'measurements':values,
            'hold_interval_us':5000,'read_interval_us':25,'readout_layout_qualified':False,'target_levels_v':targets,'write_reference_v':write_reference,'reference_prediction':prediction_path.relative_to(ROOT).as_posix(),'nominal_feedback_ratio':'2/(64+2+4) native poly resistor lengths; actual resistor models determine gain','write_bias_ua':5,'writer_state_terminal':'A; matched baseline used B','physical_children_qualified':True,'memory_parent_layout_qualified':True,'writer_parent_layout_qualified':True,'combined_writer_memory_layout_qualified':True,
            'scope':'Cap-extracted qualified physical18MOS writer-memory parent with frozen corrected external reference. Ideal column clamp removed: two actual extracted native7MOS OTAs regulate sense/replica columns toward external10mV reference, matched extracted PF0.5/L1 feed transistors mirror current, native NF0.5/L1 replica and quarterTG select match resident read path. Native7um MIM compensation; readout wiring schematic, no qualified combined readout layout. Zero-voltage column probe is only series current metrology, not a voltage clamp. Global VSUBS tied to external substrate ground. Three actual held states;5ms hold followed by25us read with measured0.5/5/20/24.5us decode. External bias5uA, supply, reference and upstream timing; native clock inverters. No arithmetic decoded-voltage correction or forced held state after write. Nominal27C, mismatch/noise off; gate/dielectric leakage, retention, RPEX, decoder matching/noise and complete model/service/chip acceptance unqualified. Long read diagnostic is not population5ms service proof; no beta/reset/adaptation.',
            'physical_storage_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,
            'full_5ms_population_service_accepted':False,'full_chip_accepted':False,
            'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(report_path),'simulation_completed':complete,'measurements':values},indent=2))
    if not complete:
        raise RuntimeError(log[-1500:])

if __name__=='__main__':
    main()
