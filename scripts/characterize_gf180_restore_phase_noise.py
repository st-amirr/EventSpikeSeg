"""Stationary restore-phase noise at a completed physical transient bias point."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    source_sha_at_start=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-ua',type=float,default=2)
    parser.add_argument('--writer-input-width-um',type=float,choices=[2.5,5,10],default=10)
    parser.add_argument('--offset-extra-mim-count',type=int,choices=[0,4,12],default=0)
    parser.add_argument('--continuous-offset-startup-clamp',action='store_true')
    parser.add_argument('--sample-switch-nwidth-um',type=float,choices=[.5,1],default=1)
    parser.add_argument('--physical-acquisition-buffer',action='store_true')
    parser.add_argument('--probe-charge-fc',type=int,choices=[-1,1],default=1)
    args=parser.parse_args()
    matches=[]
    for path in (BASE/'results').glob('gf180_sensor_zero_servo_*sampledrestore*.json'):
        r=json.loads(path.read_text())
        if (r.get('simulation_completed') and r.get('physical_sample_buffer') and
            r.get('offset_reversed_plates') and r.get('offset_refresh_each_slot') and
            not r.get('offset_dummy_bottom') and not r.get('local_mismatch_enabled') and
            not r.get('offset_split_sample') and
            bool(r.get('physical_acquisition_buffer'))==args.physical_acquisition_buffer and
            bool(r.get('offset_continuous_use'))==args.continuous_offset_startup_clamp and
            (not args.continuous_offset_startup_clamp or r.get('offset_continuous_clamp_startup_only')) and
            not r.get('offset_sample_dummy_bottom') and
            r.get('offset_switch_width_scale',1)==1 and
            r.get('corner')=='typical' and r.get('temperature_c')==27 and
            r.get('diagnostic_ideal_charge_fc')==args.probe_charge_fc and
            r.get('writer_input_pair_width_um',10)==args.writer_input_width_um and
            r.get('offset_extra_mim_count',0)==args.offset_extra_mim_count and
            r.get('sample_switch_nf_width_um',1)==args.sample_switch_nwidth_um and
            r.get('hold_mim_count')==4 and r.get('offset_mim_count')==4 and
            r.get('combined_routed_offset_short_split') and
            r.get('writer_reference_current_ua',20)==args.reference_ua):
            matches.append((path,r))
    if not matches:
        raise ValueError('completed matching typical signed-charge transient required')
    source,r=max(matches,key=lambda pair:pair[0].stat().st_mtime)
    row=r['rows'][-1]
    names=['gf180_gate_state_cell','gf180_gate_sensor_shielded','gf180_fixed_body_tg',
           'gf180_mim_7x7','gf180_mim_22x22','gf180_sensor_servo_writer',
           'gf180_offset_subtractor_short_split4_isolated_reversed']
    writer_cell='gf180_sensor_servo_writer'
    if args.writer_input_width_um!=10:
        width_token=f'{args.writer_input_width_um:g}'.replace('.','p')
        writer_cell+=f'_input{width_token}um'
        names.append(writer_cell)
    sample_cell='gf180_fixed_body_tg'
    if args.sample_switch_nwidth_um!=1:
        sample_cell+='_nf'+f'{args.sample_switch_nwidth_um:g}'.replace('.','p');names.append(sample_cell)
    cells=[BASE/'layout'/name/(name+'_cap.spice') for name in names]
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    stem=f'gf180_restore_phase_noise_typical27_reference{args.reference_ua:g}ua'
    if args.writer_input_width_um!=10:
        stem+=f'_input{width_token}um'
    if args.offset_extra_mim_count:
        stem+=f'_extraoffsetmim{args.offset_extra_mim_count}'
    if args.sample_switch_nwidth_um!=1:
        stem+='_sampleswitchnf'+f'{args.sample_switch_nwidth_um:g}'.replace('.','p')
    if args.continuous_offset_startup_clamp:
        stem+='_continuousstartupclamp'
    if args.physical_acquisition_buffer:
        stem+='_acquisitionbuffer'
    if args.probe_charge_fc!=1:
        stem+='_probecharge'+str(args.probe_charge_fc)+'fc'
    stem+=f'_src{source_sha_at_start[:12]}_tran{hashlib.sha256(source.read_bytes()).hexdigest()[:12]}'
    source_snapshot=BASE/'tools/source_snapshots'/f'restore_phase_noise_{source_sha_at_start}.py'
    source_snapshot.parent.mkdir(parents=True,exist_ok=True)
    if not source_snapshot.exists():
        source_snapshot.write_bytes(Path(__file__).read_bytes())
    deck=BASE/'benches'/(stem+'.spice')
    lines=['GF180 stationary physical buffered restore noise',f'.include {prefix}/design.spice',
           '.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice typical',
           f'.lib {prefix}/sm141064.spice mimcap_typical','.temp 27',
           '.options gmin=1e-18 reltol=1e-6 abstol=1e-18 vntol=1e-11']
    for cell in cells:
        lines+=cell.read_text().splitlines()
    lines+=['Vdd vdd 0 3.3','Vset setpoint 0 1.2',
            f'Iref vdd bias {args.reference_ua:g}u',f'Ibufferref vdd bufferbias {args.reference_ua:g}u',
            f'Vhelddc helddc 0 {row["heldafteruse"]:.15g}','Lhelddc helddc heldref 1e18',
            f'Voffsetdc offsetdc 0 {row["bottomduringuse"]:.15g}','Loffsetdc offsetdc calbottom 1e18',
            f'Vrefstatedc refstatedc 0 {row["referencegate"]:.15g}','Lrefstatedc refstatedc stateref 1e18',
            'Iread readbus 0 DC 1u AC 1',
            f'Xwriter reference readbus writer vdd 0 bias vdd 0 {writer_cell}',
            'Xbuffer bufferinput readbus bufferedref vdd 0 bufferbias 0 vdd gf180_sensor_servo_writer',
            'Xbuffer_input_cal readbus bufferinput 0 vdd 0 vdd gf180_fixed_body_tg',
            'Xbuffer_input_hold heldref bufferinput vdd 0 0 vdd gf180_fixed_body_tg',
            'Xcell writer state vdd 0 0 vdd gf180_gate_state_cell',
            'Xsensor state readbus vdd 0 vdd 0 source gf180_gate_sensor_shielded',
            'Xcellref writer stateref 0 vdd 0 vdd gf180_gate_state_cell',
            'Xsensorref stateref readbus 0 vdd vdd 0 sourceref gf180_gate_sensor_shielded',
            'Xpark setpoint readbus 0 vdd 0 vdd gf180_fixed_body_tg',
            f'Xsample readbus heldref 0 vdd 0 vdd {sample_cell}',
            'Xholdinit setpoint heldref 0 vdd 0 vdd gf180_fixed_body_tg',
            'Xreference_set setpoint reference 0 vdd 0 vdd gf180_fixed_body_tg',
            'Xoffsetmodule bufferedref setpoint bufferedref reference vdd 0 0 vdd vdd 0 caltop calbottom vdd 0 gf180_offset_subtractor_short_split4_isolated_reversed',
            'Xload readbus 0 0 gf180_mim_7x7']
    if args.physical_acquisition_buffer:
        lines=[line.replace(f'Xsample readbus heldref 0 vdd 0 vdd {sample_cell}',
                            f'Xsample acquisitionout heldref 0 vdd 0 vdd {sample_cell}')
                   .replace('Xbuffer_input_cal readbus bufferinput ',
                            'Xbuffer_input_cal acquisitionout bufferinput ') for line in lines]
        lines += [f'Iacquisitionref vdd acquisitionbias {args.reference_ua:g}u',
                  'Xacquisitionbuffer readbus readbus acquisitionout vdd 0 acquisitionbias 0 vdd gf180_sensor_servo_writer']
    lines += [f'Xholdcap{i} heldref 0 0 gf180_mim_22x22' for i in range(4)]
    lines += [f'Xextraoffsetcap{i} calbottom caltop 0 gf180_mim_22x22' for i in range(args.offset_extra_mim_count)]
    lines+=['.control','set numdgt=15','op',
            'print v(state) v(readbus) v(bufferedref) v(reference) v(heldref) i(Vdd)']
    for key,node in [('state','state'),('readbus','readbus'),('buffer','bufferedref'),('reference','reference'),('held','heldref')]:
        lines += [f'noise v({node}) Iread dec 80 10 100meg',f'let {key}_rms = onoise_total',f'print {key}_rms']
    lines+=['quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
        '--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout',
        'eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],
        capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr
    logpath=BASE/'results'/(stem+'.log');logpath.write_text(log)
    values={key.lower():float(value) for key,value in re.findall(
        r'(?mi)^\s*(state_rms|readbus_rms|buffer_rms|reference_rms|held_rms|v\(state\)|v\(readbus\)|v\(bufferedref\)|v\(reference\)|v\(heldref\)|i\(vdd\))\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==11
    result={'simulation_completed':complete,'writer_reference_current_ua':args.reference_ua,
        'writer_input_pair_width_um':args.writer_input_width_um,
        'sample_switch_nf_width_um':args.sample_switch_nwidth_um,
        'physical_acquisition_buffer':args.physical_acquisition_buffer,
        'diagnostic_ideal_charge_fc':args.probe_charge_fc,
        'offset_extra_mim_count':args.offset_extra_mim_count,
        'offset_continuous_use':args.continuous_offset_startup_clamp,
        'offset_continuous_clamp_startup_only':args.continuous_offset_startup_clamp,
        'source_snapshot':source_snapshot.relative_to(ROOT).as_posix(),
        'transient_source':source.relative_to(ROOT).as_posix(),'values':values,
        'integration_band_hz':[10,1e8],'physical_state_accepted':False,
        'scope':'Stationary selected restore phase of separately extracted physical state/sensor, two routed writers, reversed offset module and physical sample/reference/park/input TGs. One unselected physical reference cell included; other unselected logical slots omitted. Held sample, floating offset and reference-state DC frozen via ideal1e18H AC-open benchmark inductors to transient values, all remain AC floating. Ideal noiseless supplies/read/bias currents and static controls. DC noise is not sampled noise, clock noise, inter-phase covariance, reference lifetime or complete float/model/service/power acceptance.'}
    if complete:
        result['dc_minus_transient_mv']={
            'readbus':(values['v(readbus)']-row['restoreprogram'])*1000,
            'buffer':(values['v(bufferedref)']-row['topduringuse'])*1000,
            'reference':(values['v(reference)']-row['restoreref'])*1000}
        result['bias_matches_transient_within_100uv']=max(abs(v) for v in result['dc_minus_transient_mv'].values())<=.1
    sources=[Path(__file__),source_snapshot,source,*cells,deck,logpath,modeldir/'design.spice',modeldir/'sm141064.spice',modeldir/'sm141064_mim.spice']
    result['sha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    result['sha256'][Path(__file__).relative_to(ROOT).as_posix()]=source_sha_at_start
    if args.continuous_offset_startup_clamp:
        result['scope']+=' Matched continuous-use/startup-clamp transient selected; frozen restore-on switches have the same DC topology as the strobed variant at this phase. This does not qualify calibration/sampling transitions or sampled noise.'
    if args.physical_acquisition_buffer:
        result['scope']=result['scope'].replace('two routed writers','three routed writers')
    if args.physical_acquisition_buffer:
        result['scope']+=' Additional routed acquisition buffer and its bias included; physical OFF sample and calibration TG endpoints match its output. Third buffer bias is resolved by DC feedback, not independently frozen to a transient measurement. Sampling/calibration noise remains unqualified.'
    target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not complete:
        raise RuntimeError(log[-2000:])


if __name__=='__main__':
    main()
