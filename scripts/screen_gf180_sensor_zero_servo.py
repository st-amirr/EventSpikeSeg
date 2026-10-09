"""Shared physical OTA zero-programming through each resident gate sensor."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    source_sha_at_start=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=17)
    parser.add_argument('--mismatch',type=int,choices=[0,1],default=0)
    parser.add_argument('--slots',type=int,choices=[4,8],default=4)
    parser.add_argument('--combined-writer',action='store_true')
    parser.add_argument('--writer-input-width-um',type=float,choices=[2.5,5,10],default=10)
    parser.add_argument('--corner',choices=['typical','ff','ss'],default='typical')
    parser.add_argument('--temp-c',type=float,default=27)
    parser.add_argument('--setpoint-v',type=float,default=1.2)
    parser.add_argument('--measure-energy',action='store_true')
    parser.add_argument('--sampled-restore',action='store_true')
    parser.add_argument('--sample-switch-nwidth-um',type=float,choices=[.5,1],default=1)
    parser.add_argument('--hold-mim-count',type=int,choices=[1,4],default=1)
    parser.add_argument('--physical-offset',action='store_true')
    parser.add_argument('--offset-switch-width-scale',type=float,choices=[.5,1],default=1)
    parser.add_argument('--offset-mim-count',type=int,choices=[1,4],default=1)
    parser.add_argument('--offset-extra-mim-count',type=int,choices=[0,4,12],default=0,help='Separately extracted parallel offset capacitors; complete assembly routing remains absent')
    parser.add_argument('--combined-offset-module',action='store_true')
    parser.add_argument('--bottom-plate-stagger-ns',type=float,default=0)
    parser.add_argument('--offset-acquire-us',type=float,default=.5)
    parser.add_argument('--offset-refresh-on-read',action='store_true')
    parser.add_argument('--offset-dedicated-read',action='store_true')
    parser.add_argument('--combined-offset-short-split',action='store_true')
    parser.add_argument('--offset-isolated-routes',action='store_true')
    parser.add_argument('--integration-method',choices=['trap','gear'],default='trap')
    parser.add_argument('--probe-charge-fc',type=float,default=0,help='Ideal diagnostic charge onto nonreference slots; not injector qualification')
    parser.add_argument('--max-step-ns',type=float,default=500)
    parser.add_argument('--simulation-timeout-s',type=int,choices=[120,240],default=120)
    parser.add_argument('--sample-extra-us',type=float,default=0)
    parser.add_argument('--restore-extra-us',type=float,default=0,help='Extend physical write/feedback and plate-use phase together')
    parser.add_argument('--reference-extra-us',type=float,default=0,help='Start reference read/capture earlier; include extra time in service')
    parser.add_argument('--physical-sample-buffer',action='store_true')
    parser.add_argument('--physical-acquisition-buffer',action='store_true',help='Additional routed unity writer ahead of sampler; calibration traverses both buffers')
    parser.add_argument('--offset-reversed-plates',action='store_true')
    parser.add_argument('--offset-dummy-bottom',action='store_true')
    parser.add_argument('--offset-split-sample',action='store_true')
    parser.add_argument('--offset-sample-dummy-bottom',action='store_true')
    parser.add_argument('--offset-sample-dummy-nwidth-um',type=float,choices=[.25,.33,.5],default=.5)
    parser.add_argument('--offset-sample-clock-trim-um',type=float,choices=[0,1,2,4],default=0)
    parser.add_argument('--offset-sample-clock-trim-net',choices=['SAMPLEB','SAMPLE'],default='SAMPLEB')
    parser.add_argument('--offset-sample-bottom-advance-ns',type=float,default=0)
    parser.add_argument('--offset-refresh-each-slot',action='store_true')
    parser.add_argument('--offset-continuous-use',action='store_true',help='Keep physical offset use TGs on; explicit calibration/startup reference clamp')
    parser.add_argument('--offset-continuous-clamp-startup-only',action='store_true',help='After startup, physical bank sample-bottom alone clamps reference during calibration')
    parser.add_argument('--reference-ua',type=float,default=20,help='Ideal reference current for each physical writer bias diode')
    parser.add_argument('--verify-next-read',action='store_true')
    parser.add_argument('--follow-delay-us',type=float,default=30,help='Follow read delay from last signal-slot start, not end of restore')
    args=parser.parse_args()
    if args.physical_acquisition_buffer and (not args.physical_sample_buffer or not args.offset_refresh_each_slot or not args.sampled_restore):
        raise ValueError('acquisition buffer requires refreshed physically buffered sampled restore')
    if args.sample_switch_nwidth_um!=1 and not args.sampled_restore:
        raise ValueError('sample switch variant requires sampled restore')
    if args.offset_continuous_clamp_startup_only and not args.offset_continuous_use:
        raise ValueError('startup-only reference clamp requires continuous offset use')
    if args.offset_continuous_use and (not args.offset_refresh_each_slot or not args.physical_sample_buffer or not args.offset_reversed_plates or args.bottom_plate_stagger_ns):
        raise ValueError('continuous offset use requires refreshed buffered reversed macro and zero stagger')
    if args.offset_switch_width_scale!=1 and (not args.offset_reversed_plates or args.offset_sample_dummy_bottom or args.offset_dummy_bottom or args.offset_split_sample):
        raise ValueError('scaled switches require reversed isolated macro without dummy/sample experiments')
    if args.offset_sample_clock_trim_net!='SAMPLEB' and not args.offset_sample_clock_trim_um:
        raise ValueError('trim polarity requires nonzero trim length')
    if args.offset_sample_clock_trim_um and (not args.offset_sample_dummy_bottom or args.offset_sample_dummy_nwidth_um!=.5):
        raise ValueError('clock trim requires default-width calibration dummy')
    if args.offset_sample_dummy_nwidth_um!=.5 and not args.offset_sample_dummy_bottom:
        raise ValueError('calibration dummy width requires sample dummy')
    if args.offset_sample_dummy_bottom and (not args.offset_reversed_plates or args.offset_dummy_bottom or args.offset_split_sample):
        raise ValueError('sample dummy requires reversed unsplit offset without use dummy')
    if not 0<=args.reference_extra_us<=3 or (args.reference_extra_us and not args.offset_refresh_each_slot):
        raise ValueError('reference extension requires per-slot reference refresh and0..3us')
    slot_us=12+args.sample_extra_us+args.restore_extra_us+args.reference_extra_us
    if args.offset_split_sample and (not args.offset_reversed_plates or args.offset_dummy_bottom):
        raise ValueError('split calibration sample requires reversed macro without dummy')
    if not -200<=args.offset_sample_bottom_advance_ns<=200 or (args.offset_sample_bottom_advance_ns and not args.offset_split_sample):
        raise ValueError('sample bottom advance requires split sample and-200..200ns')
    if not 0<=args.restore_extra_us<=4 or (args.restore_extra_us and not args.sampled_restore):
        raise ValueError('restore extension requires sampled restore and0..4us')
    if args.writer_input_width_um!=10 and not args.combined_writer:
        raise ValueError('writer input variant requires combined writer')
    if args.offset_extra_mim_count and not (args.combined_offset_short_split and args.offset_reversed_plates):
        raise ValueError('extra offset MIM requires reversed short-split physical offset macro')
    if not 30<=args.follow_delay_us<=5020 or (args.follow_delay_us!=30 and not args.verify_next_read):
        raise ValueError('follow delay requires next-read screen and30..5020us')
    if not .5<=args.reference_ua<=20:
        raise ValueError('writer reference current must be0.5..20uA')
    if not 10<=args.max_step_ns<=500:
        raise ValueError('max step must be10..500ns')
    if not 0<=args.sample_extra_us<=3 or (args.sample_extra_us and not args.sampled_restore):
        raise ValueError('sample extension requires sampled restore and0..3us')
    if not 0<=args.bottom_plate_stagger_ns<=200 or (args.bottom_plate_stagger_ns and not args.physical_offset):
        raise ValueError('bottom plate stagger requires physical offset and0..200ns')
    if not .5<=args.offset_acquire_us<=2 or (args.offset_acquire_us!=.5 and not args.physical_offset):
        raise ValueError('offset acquisition requires physical offset and0.5..2us')
    if not 1.05<=args.setpoint_v<=1.5:
        raise ValueError('setpoint outside bounded1.05..1.5V servo screen')
    stem=f'gf180_sensor_zero_servo_{args.corner}{args.temp_c:g}_seed{args.seed}_slots{args.slots}_mm{args.mismatch}'
    if args.setpoint_v!=1.2:
        stem += f'_set{args.setpoint_v:g}v'
    if args.combined_writer:
        stem += '_combinedwriter'
        if args.writer_input_width_um!=10:
            stem += f'_writerinput{args.writer_input_width_um:g}um'
    if args.measure_energy:
        stem += '_energy'
    if args.sampled_restore:
        if not args.combined_writer:
            raise ValueError('sampled restore requires routed writer')
        stem += f'_sampledrestore_hold{args.hold_mim_count}'
    if args.physical_offset:
        if not args.sampled_restore:
            raise ValueError('physical offset requires sampled restore')
        stem += f'_physicaloffset{args.offset_mim_count}'
    if args.combined_offset_module:
        if not args.physical_offset or args.offset_mim_count!=1:
            raise ValueError('combined offset macro requires physical-offset and one internal MIM')
        stem += '_combinedoffset'
    if args.combined_offset_short_split:
        if not args.physical_offset or args.offset_mim_count!=4 or args.combined_offset_module:
            raise ValueError('short split macro requires physical offset and four internal MIMs')
        stem += '_combinedshortsplit4'
    if args.offset_isolated_routes:
        if not args.combined_offset_short_split:
            raise ValueError('isolated routing requires combined short split macro')
        stem += '_isolatedroutes'
    if args.bottom_plate_stagger_ns:
        stem += f'_bottomstagger{args.bottom_plate_stagger_ns:g}ns'
    if args.offset_acquire_us!=.5:
        stem += f'_offsetacquire{args.offset_acquire_us:g}us'
    if args.offset_refresh_on_read:
        if not args.physical_offset or args.offset_acquire_us!=.5:
            raise ValueError('read-phase capture requires physical offset and default acquisition')
        stem += '_readphaseoffset'
    if args.offset_dedicated_read:
        if not args.physical_offset or args.offset_refresh_on_read or args.offset_acquire_us!=.5:
            raise ValueError('dedicated calibration requires physical offset and default capture settings')
        stem += '_dedicatedoffsetread'
    if args.integration_method!='trap':
        stem += '_gear'
    if args.probe_charge_fc:
        if not args.offset_dedicated_read or not -10<=args.probe_charge_fc<=10:
            raise ValueError('charge diagnostic requires dedicated zero-reference slot and at most10fC')
        stem += f'_probecharge{args.probe_charge_fc:g}fc'
    if args.max_step_ns!=500:
        stem += f'_step{args.max_step_ns:g}ns'
    if args.sample_extra_us:
        stem += f'_sampleextra{args.sample_extra_us:g}us'
    if args.restore_extra_us:
        stem += f'_restoreextra{args.restore_extra_us:g}us'
    if args.reference_extra_us:
        stem += f'_referenceextra{args.reference_extra_us:g}us'
    if args.physical_sample_buffer:
        if not args.combined_offset_short_split or not args.offset_dedicated_read:
            raise ValueError('physical buffer requires combined offset and dedicated calibration')
        stem += '_physicalsamplebuffer'
    if args.offset_reversed_plates:
        if not args.offset_isolated_routes:
            raise ValueError('reversed capacitor plates require isolated macro')
        stem += '_reversedplates'
    if args.offset_extra_mim_count:
        stem += f'_extraoffsetmim{args.offset_extra_mim_count}'
    if args.offset_dummy_bottom:
        if not args.offset_reversed_plates:
            raise ValueError('bottom dummy requires reversed isolated macro')
        stem += '_dummybottom'
    if args.offset_sample_dummy_bottom:
        stem += '_sampledummybottom'
        if args.offset_sample_dummy_nwidth_um!=.5:
            stem+=f'_nf{args.offset_sample_dummy_nwidth_um:g}'
    if args.offset_sample_clock_trim_um:
        stem+=f'_clocktrim{args.offset_sample_clock_trim_um:g}'+('_sample' if args.offset_sample_clock_trim_net=='SAMPLE' else '')
    if args.offset_switch_width_scale!=1:
        stem+='_halfswitch'
    if args.offset_split_sample:
        stem+=f'_splitsample_bottomadvance{args.offset_sample_bottom_advance_ns:g}ns'
    if args.offset_continuous_use:
        stem+='_continuousoffsetuse'
        if args.offset_continuous_clamp_startup_only:
            stem+='_startupclamponly'
    if args.offset_refresh_each_slot:
        if not args.offset_dedicated_read:
            raise ValueError('physical refresh requires dedicated offset calibration')
        stem += '_refreshreference'
    if args.reference_ua!=20:
        stem += f'_reference{args.reference_ua:g}ua'
    if args.verify_next_read:
        if not args.sampled_restore:
            raise ValueError('next-read screen requires sampled restore')
        stem += '_verifyread'
        if args.follow_delay_us!=30:
            stem += f'_followdelay{args.follow_delay_us:g}us'
    if args.simulation_timeout_s!=120:
        stem+=f'_timeout{args.simulation_timeout_s}s'
    if args.physical_acquisition_buffer:
        stem+='_physicalacquisitionbuffer'
    if args.sample_switch_nwidth_um!=1:
        stem+='_sampleswitchnf'+f'{args.sample_switch_nwidth_um:g}'.replace('.','p')
    stem+=f'_src{source_sha_at_start[:12]}'
    source_snapshot=BASE/'tools/source_snapshots'/f'sensor_zero_servo_{source_sha_at_start}.py'
    source_snapshot.parent.mkdir(parents=True,exist_ok=True)
    if not source_snapshot.exists():
        source_snapshot.write_bytes(Path(__file__).read_bytes())
    descriptive_run_name=stem
    # Windows components are limited to255 characters; retain complete settings in the report.
    if len(stem)>220:
        token=hashlib.sha256(stem.encode('ascii')).hexdigest()[:20]
        stem=f'gf180_sensor_zero_servo_{args.corner}{args.temp_c:g}_sampledrestore_{token}'
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    cells=[BASE/f'layout/{name}/{name}_cap.spice' for name in ['gf180_gate_state_cell','gf180_gate_sensor_shielded','gf180_fixed_body_tg','gf180_shared_ota_core','gf180_mim_7x7','gf180_mim_22x22']]
    sample_cell='gf180_fixed_body_tg'
    if args.sample_switch_nwidth_um!=1:
        sample_cell+='_nf'+f'{args.sample_switch_nwidth_um:g}'.replace('.','p')
        cells.append(BASE/f'layout/{sample_cell}/{sample_cell}_cap.spice')
    deck=BASE/f'benches/{stem}.spice'
    writer=BASE/'layout/gf180_sensor_servo_writer/gf180_sensor_servo_writer_cap.spice'
    writer_cell='gf180_sensor_servo_writer'
    if args.writer_input_width_um!=10:
        width_token=f'{args.writer_input_width_um:g}'.replace('.','p')
        writer_cell+=f'_input{width_token}um'
        writer=BASE/f'layout/{writer_cell}/{writer_cell}_cap.spice'
        if args.physical_sample_buffer:
            cells.append(BASE/'layout/gf180_sensor_servo_writer/gf180_sensor_servo_writer_cap.spice')
    offset_module=BASE/'layout/gf180_offset_subtractor/gf180_offset_subtractor_cap.spice'
    if args.combined_offset_short_split:
        offset_module=BASE/'layout/gf180_offset_subtractor_short_split4/gf180_offset_subtractor_short_split4_cap.spice'
        if args.offset_isolated_routes:
            offset_module=BASE/'layout/gf180_offset_subtractor_short_split4_isolated/gf180_offset_subtractor_short_split4_isolated_cap.spice'
            if args.offset_reversed_plates:
                offset_module=BASE/'layout/gf180_offset_subtractor_short_split4_isolated_reversed/gf180_offset_subtractor_short_split4_isolated_reversed_cap.spice'
                if args.offset_dummy_bottom:
                    offset_module=BASE/'layout/gf180_offset_subtractor_short_split4_isolated_reversed_dummybottom/gf180_offset_subtractor_short_split4_isolated_reversed_dummybottom_cap.spice'
    if args.offset_split_sample:
        name='gf180_offset_subtractor_short_split4_isolated_reversed_splitsample'
        offset_module=BASE/f'layout/{name}/{name}_cap.spice'
    if args.offset_sample_dummy_bottom:
        name='gf180_offset_subtractor_short_split4_isolated_reversed_sampledummybottom'
        if args.offset_sample_dummy_nwidth_um!=.5:
            name+='_nf'+f'{args.offset_sample_dummy_nwidth_um:g}'.replace('.','p')
        if args.offset_sample_clock_trim_um:
            name+=f'_clocktrim{args.offset_sample_clock_trim_um:g}'+('_sample' if args.offset_sample_clock_trim_net=='SAMPLE' else '')
        offset_module=BASE/f'layout/{name}/{name}_cap.spice'
    if args.offset_switch_width_scale!=1:
        name='gf180_offset_subtractor_short_split4_isolated_reversed_halfswitch'
        offset_module=BASE/f'layout/{name}/{name}_cap.spice'
    def phase_time(at):
        # Extend acquisition, then extend write-on settling before shifting end phases.
        for _,r in times:
            if r+1.68e-6<=at<=r+9e-6:
                restore_shift=args.restore_extra_us*1e-6 if at>=r+4.89e-6 else 0
                return at+args.sample_extra_us*1e-6+restore_shift
        return at
    def wave(name,node,initial,points):
        return f'{name} {node} 0 PWL(0 {initial:g} '+' '.join(f'{phase_time(t):.12g} {v:.12g}' for t,v in points)+')'
    def inverse(points):
        return [(t,3.3-v) for t,v in points]
    lines=['GF180 shared OTA sensor-referenced zero setting',f'.include {prefix}/design.spice',
           f'.param sw_stat_global=0 sw_stat_mismatch={args.mismatch}',f'.lib {prefix}/sm141064.spice {args.corner}',
           f'.lib {prefix}/sm141064.spice mimcap_typical',f'.temp {args.temp_c:g}',
           f'.options method={args.integration_method} gmin=1e-18 reltol=1e-6 abstol=1e-16 vntol=1e-10']
    for cell in cells:
        lines += cell.read_text().splitlines()
    lines += ['Vdd vdd 0 3.3',f'Vset setpoint 0 {args.setpoint_v:g}','Vinitref initref 0 1.65',
              f'Iref vdd bias {args.reference_ua:g}u','Xref bias bias 0 0 nfet_03v3 w=10u l=2u as=4.4p ad=4.4p ps=20.88u pd=20.88u',
              'Xota setpoint input writer vdd 0 bias cmp gf180_shared_ota_core',
              'Xcomp cmp writer 0 gf180_mim_22x22','Xload readbus 0 0 gf180_mim_7x7',
              'Xmuxread input readbus cal calb 0 vdd gf180_fixed_body_tg',
              'Xmuxunity input writer calb cal 0 vdd gf180_fixed_body_tg',
              'Xpark setpoint readbus park parkb 0 vdd gf180_fixed_body_tg',
              '.model ideal_init SW(Ron=10 Roff=1e30 Vt=1.65 Vh=0.1)',
              'Vinit init 0 PWL(0 3.3 0.99u 3.3 1u 0)']
    if args.combined_writer:
        lines=[line for line in lines if not line.startswith(('Xref ','Xota ','Xcomp ','Xmuxread ','Xmuxunity '))]
        lines += writer.read_text().splitlines()+['Xwriter setpoint readbus writer vdd 0 bias cal calb gf180_sensor_servo_writer']
    if args.sampled_restore:
        lines.remove('Xwriter setpoint readbus writer vdd 0 bias cal calb gf180_sensor_servo_writer')
        lines += ['Xwriter reference readbus writer vdd 0 bias cal calb gf180_sensor_servo_writer',
                  'Xreference_set setpoint reference useheldb useheld 0 vdd gf180_fixed_body_tg',
                  'Xreference_hold heldref reference useheld useheldb 0 vdd gf180_fixed_body_tg',
                  f'Xsample readbus heldref sample sampleb 0 vdd {sample_cell}',
                  'Xholdinit setpoint heldref holdinit holdinitb 0 vdd gf180_fixed_body_tg']
        lines += [f'Xholdcap{i} heldref 0 0 gf180_mim_22x22' for i in range(args.hold_mim_count)]
        if args.physical_offset:
            lines.remove('Xreference_hold heldref reference useheld useheldb 0 vdd gf180_fixed_body_tg')
            lines += ['Xreference_hold calbottom reference usebottom usebottomb 0 vdd gf180_fixed_body_tg',
                      'Xoffset_holdtop heldref caltop useheld useheldb 0 vdd gf180_fixed_body_tg',
                      'Xoffset_sampletop readbus caltop calstore calstoreb 0 vdd gf180_fixed_body_tg',
                      'Xoffset_samplebottom setpoint calbottom calstore calstoreb 0 vdd gf180_fixed_body_tg']
            lines += [f'Xoffsetcap{i} caltop calbottom 0 gf180_mim_22x22' for i in range(args.offset_mim_count)]
            if args.combined_offset_module or args.combined_offset_short_split:
                lines=[line for line in lines if not line.startswith(('Xreference_hold ','Xoffset_holdtop ','Xoffset_sampletop ','Xoffset_samplebottom ','Xoffsetcap'))]
                instance='Xoffsetmodule readbus setpoint heldref reference vdd 0 calstore calstoreb useheld useheldb caltop calbottom '
                instance += 'usebottom usebottomb gf180_offset_subtractor_short_split4' if args.combined_offset_short_split else 'gf180_offset_subtractor'
                if args.offset_isolated_routes:
                    instance += '_isolated'
                if args.offset_reversed_plates:
                    instance += '_reversed'
                if args.offset_dummy_bottom:
                    instance += '_dummybottom'
                if args.offset_sample_dummy_bottom:
                    instance += '_sampledummybottom'
                    if args.offset_sample_dummy_nwidth_um!=.5:
                        instance+='_nf'+f'{args.offset_sample_dummy_nwidth_um:g}'.replace('.','p')
                if args.offset_sample_clock_trim_um:
                    instance+=f'_clocktrim{args.offset_sample_clock_trim_um:g}'+('_sample' if args.offset_sample_clock_trim_net=='SAMPLE' else '')
                if args.offset_switch_width_scale!=1:
                    instance+='_halfswitch'
                if args.offset_split_sample:
                    ports,cell=instance.rsplit(' ',1)
                    instance=ports+' calstorebottom calstorebottomb '+cell+'_splitsample'
                lines += offset_module.read_text().splitlines()+[instance]
                if args.bottom_plate_stagger_ns and args.combined_offset_module:
                    raise ValueError('combined macro shares plate controls; stagger screen uses separate extracted switches')
    if args.writer_input_width_um!=10:
        lines=[line.replace('gf180_sensor_servo_writer',writer_cell) if line.startswith('Xwriter ') else line for line in lines]
    cals=[];parks=[];read_current=[];times=[];samples=[];useheld=[];holdinit=[];followtimes=[]
    # Match reversed macro plates: native low-ground-capacitance TOP floats at calbottom.
    # Each added primitive keeps its own extracted parasitics and grounded substrate.
    lines += [f'Xextraoffsetcap{i} calbottom caltop 0 gf180_mim_22x22'
              for i in range(args.offset_extra_mim_count)]
    if args.physical_sample_buffer:
        # Use the same routed writer as a unity follower; its own reference diode and MIM included.
        # Calibrate through this same buffer, physically absorbing its additive offset.
        lines=[line.replace('Xoffsetmodule readbus setpoint heldref reference ',
                            'Xoffsetmodule bufferedref setpoint bufferedref reference ') for line in lines]
        lines += ['Vbufferidle bufferidle 0 0','Vbufferidleb bufferidleb 0 3.3',
                  f'Ibufferref vdd bufferbias {args.reference_ua:g}u',
                  'Xbuffer bufferinput readbus bufferedref vdd 0 bufferbias bufferidle bufferidleb gf180_sensor_servo_writer',
                  'Xbuffer_input_cal readbus bufferinput calstore calstoreb 0 vdd gf180_fixed_body_tg',
                  'Xbuffer_input_hold heldref bufferinput calstoreb calstore 0 vdd gf180_fixed_body_tg']
    if args.physical_acquisition_buffer:
        # Calibrate through the same two physical buffer stages used by sampled signal.
        lines=[line.replace(f'Xsample readbus heldref sample sampleb 0 vdd {sample_cell}',
                            f'Xsample acquisitionout heldref sample sampleb 0 vdd {sample_cell}')
                   .replace('Xbuffer_input_cal readbus bufferinput ',
                            'Xbuffer_input_cal acquisitionout bufferinput ') for line in lines]
        lines += [f'Iacquisitionref vdd acquisitionbias {args.reference_ua:g}u',
                  'Xacquisitionbuffer readbus readbus acquisitionout vdd 0 acquisitionbias 0 vdd gf180_sensor_servo_writer']
    if args.offset_continuous_use:
        lines=[line.replace('Xreference_set setpoint reference useheldb useheld ',
                            'Xreference_set setpoint reference refclamp refclampb ') for line in lines]
    for i in range(args.slots):
        t=10e-6+i*5e-6;r=0.0051+i*(slot_us*1e-6 if args.sampled_restore else 5e-6);times.append((t,r))
        initial_read=max(3e-6,(2.5+args.offset_acquire_us)*1e-6) if args.physical_offset and i==0 else 3e-6
        writes=[(t-1e-8,0),(t,3.3),(t+1.99e-6,3.3),(t+2e-6,0)]
        reads=[(t-1e-8,0),(t,3.3),(t+initial_read-1e-8,3.3),(t+initial_read,0),
               (r-1e-8,0),(r,3.3),(r+1.99e-6,3.3),(r+2e-6,0)]
        cals += [(t-1e-8,0),(t,3.3),(t+2.01e-6,3.3),(t+2.02e-6,0)]
        calibration=[]
        if args.offset_dedicated_read and i==0 and not args.offset_refresh_each_slot:
            calibration=[(r-6e-6,3e-6)]
            reads += [(r-6.01e-6,0),(r-6e-6,3.3),(r-3.01e-6,3.3),(r-3e-6,0)]
        if args.sampled_restore:
            writes += [(r+2.99e-6,0),(r+3e-6,3.3),(r+4.99e-6,3.3),(r+5e-6,0)]
            reads += [(r+2.99e-6,0),(r+3e-6,3.3),(r+5.99e-6,3.3),(r+6e-6,0)]
            cals += [(r+2.99e-6,0),(r+3e-6,3.3),(r+5.01e-6,3.3),(r+5.02e-6,0)]
            samples += [(r+.49e-6,0),(r+.5e-6,3.3),(r+1.69e-6,3.3),(r+1.7e-6,0)]
            useheld += [(r+2.39e-6,0),(r+2.4e-6,3.3),(r+6.09e-6,3.3),(r+6.1e-6,0)]
            holdinit += [(r-.51e-6,3.3),(r-.5e-6,0),(r+6.99e-6,0),(r+7e-6,3.3)]
        for start,duration in [(t,initial_read),(r,6e-6 if args.sampled_restore else 2e-6)]+calibration:
            parks += [(start-.51e-6,3.3),(start-.5e-6,0),(start+duration+.49e-6,0),(start+duration+.5e-6,3.3)]
        for start,duration in [(t,initial_read),(r,2e-6)]+calibration+([(r+3e-6,3e-6)] if args.sampled_restore else []):
            read_current += [(start-1e-8,0),(start,1e-6),(start+duration-1e-8,1e-6),(start+duration,0)]
        if args.verify_next_read:
            follow=.0051+(args.slots-1)*slot_us*1e-6+args.follow_delay_us*1e-6+i*5e-6
            followtimes.append(follow)
            reads += [(follow-1e-8,0),(follow,3.3),(follow+1.99e-6,3.3),(follow+2e-6,0)]
            parks += [(follow-.51e-6,3.3),(follow-.5e-6,0),(follow+2.49e-6,0),(follow+2.5e-6,3.3)]
            read_current += [(follow-1e-8,0),(follow,1e-6),(follow+1.99e-6,1e-6),(follow+2e-6,0)]
        reads.sort()
        lines += [wave(f'Vwrite{i}',f'write{i}',0,writes),wave(f'Vwriteb{i}',f'writeb{i}',3.3,inverse(writes)),
                  wave(f'Vread{i}',f'read{i}',0,reads),wave(f'Vreadb{i}',f'readb{i}',3.3,inverse(reads)),
                  f'Xcell{i} writer state{i} write{i} writeb{i} 0 vdd gf180_gate_state_cell',
                  f'Xsensor{i} state{i} readbus read{i} readb{i} vdd 0 source{i} gf180_gate_sensor_shielded',
                  f'Sinit{i} initref state{i} init 0 ideal_init']
        if args.probe_charge_fc and i:
            # Two10ns edges plus990ns plateau integrate to1us-equivalent charge.
            current=args.probe_charge_fc*1e-9
            lines.append(wave(f'Iprobe{i}',f'state{i}',0,[(.001,0),(.00100001,-current),(.001001,-current),(.00100101,0)]))
    if args.offset_refresh_each_slot:
        # A separate physical zero-reference state/sensor is initialized once, then read per slot.
        t=5e-6
        refwrites=[(t-1e-8,0),(t,3.3),(t+1.99e-6,3.3),(t+2e-6,0)]
        refreads=[(t-1e-8,0),(t,3.3),(t+2.99e-6,3.3),(t+3e-6,0)]
        cals += [(t-1e-8,0),(t,3.3),(t+2.01e-6,3.3),(t+2.02e-6,0)]
        reference_windows=[(t,3e-6)]
        for _,r in times:
            start=r-(4.8+args.reference_extra_us)*1e-6
            duration=(3+args.reference_extra_us)*1e-6
            refreads += [(start-1e-8,0),(start,3.3),(start+duration-1e-8,3.3),(start+duration,0)]
            reference_windows.append((start,duration))
        for start,duration in reference_windows:
            parks += [(start-.51e-6,3.3),(start-.5e-6,0),(start+duration+.49e-6,0),(start+duration+.5e-6,3.3)]
            read_current += [(start-1e-8,0),(start,1e-6),(start+duration-1e-8,1e-6),(start+duration,0)]
        lines += [wave('Vwriteref','writeref',0,refwrites),wave('Vwriterefb','writerefb',3.3,inverse(refwrites)),
                  wave('Vreadref','readref',0,refreads),wave('Vreadrefb','readrefb',3.3,inverse(refreads)),
                  'Xcellref writer stateref writeref writerefb 0 vdd gf180_gate_state_cell',
                  'Xsensorref stateref readbus readref readrefb vdd 0 sourceref gf180_gate_sensor_shielded',
                  'Sinitref initref stateref init 0 ideal_init']
    parks.sort();read_current.sort();cals.sort()
    if args.offset_continuous_use:
        # Keep both physical use TGs closed; calibration/startup clamps the writer reference.
        useheld=[]
        lines += ['Vuseheld useheld 0 3.3','Vuseheldb useheldb 0 0']
    if args.sampled_restore:
        lines += [wave('Vsample','sample',0,samples),wave('Vsampleb','sampleb',3.3,inverse(samples)),
                  *([wave('Vuseheld','useheld',0,useheld),wave('Vuseheldb','useheldb',3.3,inverse(useheld))] if not args.offset_continuous_use else []),
                  wave('Vholdinit','holdinit',3.3,holdinit),wave('Vholdinitb','holdinitb',0,inverse(holdinit))]
    if args.physical_offset:
        stagger=args.bottom_plate_stagger_ns*1e-9
        # Keep each finite edge10ns; delay bottom closure and open bottom before top.
        bottom=[]
        for _,r in times:
            bottom += [(r+2.39e-6+stagger,0),(r+2.4e-6+stagger,3.3),
                       (r+6.09e-6-stagger,3.3),(r+6.1e-6-stagger,0)]
        if args.offset_continuous_use:
            lines += ['Vusebottom usebottom 0 3.3','Vusebottomb usebottomb 0 0']
        else:
            lines += [wave('Vusebottom','usebottom',0,bottom),wave('Vusebottomb','usebottomb',3.3,inverse(bottom))]
        t=times[0][0]
        end=t+(2.3+args.offset_acquire_us)*1e-6
        points=[(t+2.29e-6,0),(t+2.3e-6,3.3),(end-1e-8,3.3),(end,0)]
        if args.offset_refresh_on_read:
            r=times[0][1]
            points=[(r+.59e-6,0),(r+.6e-6,3.3),(r+1.59e-6,3.3),(r+1.6e-6,0)]
        if args.offset_dedicated_read:
            r=times[0][1]
            points=[(r-5.41e-6,0),(r-5.4e-6,3.3),(r-3.41e-6,3.3),(r-3.4e-6,0)]
        if args.offset_refresh_each_slot:
            points=[]
            for _,r in times:
                points += [(r-(4.21+args.reference_extra_us)*1e-6,0),(r-(4.2+args.reference_extra_us)*1e-6,3.3),(r-2.21e-6,3.3),(r-2.2e-6,0)]
        lines += [wave('Vcalstore','calstore',0,points),wave('Vcalstoreb','calstoreb',3.3,inverse(points))]
        if args.offset_continuous_use:
            first_r=times[0][1]
            clamp=[(first_r-2.21e-6,3.3),(first_r-2.2e-6,0)]+points[4:]
            if args.offset_continuous_clamp_startup_only:
                # Open100ns after first physical sample-bottom closes, leaving1.9us settling.
                end=first_r-(4.1+args.reference_extra_us)*1e-6
                clamp=[(end-1e-8,3.3),(end,0)]
            lines += [wave('Vrefclamp','refclamp',3.3,clamp),wave('Vrefclampb','refclampb',0,inverse(clamp))]
        if args.offset_split_sample:
            advance=args.offset_sample_bottom_advance_ns*1e-9
            bottom_points=[(at-advance if i%4 in [2,3] else at,value)
                           for i,(at,value) in enumerate(points)]
            lines += [wave('Vcalstorebottom','calstorebottom',0,bottom_points),
                      wave('Vcalstorebottomb','calstorebottomb',3.3,inverse(bottom_points))]
    stop=followtimes[-1]+5e-6 if followtimes else times[-1][1]+((9+args.sample_extra_us+args.restore_extra_us)*1e-6 if args.sampled_restore else 5e-6)
    lines += [wave('Vcal','cal',0,cals),wave('Vcalb','calb',3.3,inverse(cals)),
              wave('Vpark','park',3.3,parks),wave('Vparkb','parkb',0,inverse(parks)),
              wave('Iread','readbus',0,read_current),'.control','set numdgt=15',f'setseed {args.seed}','reset',
              f'tran {args.max_step_ns:g}n {stop:.12g}']
    if args.measure_energy:
        lines.append('let supply_power = -3.3*i(vdd)')
    if args.physical_offset:
        lines.append('let offset_delta = v(caltop)-v(calbottom)')
    names=[]
    for i,(t,r) in enumerate(times):
        for name,node,at in [('program','readbus',t+1.9e-6),('gateprogram',f'state{i}',t+1.9e-6),
                             ('released','readbus',t+2.9e-6),('held',f'state{i}',r-1e-6),
                             ('read','readbus',r+1.9e-6),('gateread',f'state{i}',r+1.9e-6)]:
            key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find v({node}) at={phase_time(at):.12g}')
        if args.sampled_restore:
            for name,node,at in [('beforecapture','readbus',r+.4e-6),('captured','heldref',r+1.9e-6),
                                 ('restoreprogram','readbus',r+4.9e-6),('restorereleased','readbus',r+5.9e-6),
                                 ('restoregate',f'state{i}',r+5.9e-6)]:
                key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find v({node}) at={phase_time(at):.12g}')
            for name,node,at in [('buspresample','readbus',r+.48e-6),('gatepresample',f'state{i}',r+.48e-6),
                                 ('bustrackend','readbus',r+1.65e-6),('gatetrackend',f'state{i}',r+1.65e-6),
                                 ('sampletrackend','heldref',r+1.65e-6)]:
                key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find v({node}) at={phase_time(at):.12g}')
            if args.physical_acquisition_buffer:
                for name,at in [('acquisitionpresample',r+.48e-6),('acquisitiontrackend',r+1.65e-6)]:
                    key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find v(acquisitionout) at={phase_time(at):.12g}')
            key=f'restoreref_{i}';names.append(key);lines.append(f'meas tran {key} find v(reference) at={phase_time(r+4.9e-6):.12g}')
            for name,node,at in [('heldafteruse','heldref',r+4.9e-6),('topduringuse','caltop',r+4.9e-6),('bottomduringuse','calbottom',r+4.9e-6)] if args.physical_offset else []:
                key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find v({node}) at={phase_time(at):.12g}')
        if args.physical_offset:
            for name,at in [('offsetpreuse',r+2.38e-6),('offsettopon',r+2.44e-6),
                            ('offsetbottomon',r+2.45e-6+args.bottom_plate_stagger_ns*1e-9),('offsetwriteend',r+4.9e-6)]:
                key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find offset_delta at={phase_time(at):.12g}')
            for name,at in [('offsetbefore',r+2.3e-6),('offsetafter',r+6.2e-6)]:
                key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find offset_delta at={phase_time(at):.12g}')
        if args.offset_refresh_each_slot:
            for name,node,at in [('referencebus','readbus',r-1.9e-6),('referencegate','stateref',r-.9e-6)]:
                key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find v({node}) at={at:.12g}')
            for name,at in [('caldeltabefore',r-2.22e-6),('caldeltaafter',r-2.18e-6),('caldeltasettled',r-.9e-6)]:
                key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find offset_delta at={at:.12g}')
            if args.physical_sample_buffer:
                for name,at in [('bufferbeforecap',r-2.22e-6),('bufferaftercap',r-2.18e-6)]:
                    key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find v(bufferedref) at={at:.12g}')
        if args.verify_next_read:
            for name,node in [('followread','readbus'),('followgate',f'state{i}')]:
                key=f'{name}_{i}';names.append(key);lines.append(f'meas tran {key} find v({node}) at={followtimes[i]+1.9e-6:.12g}')
        if args.measure_energy:
            for name,start in [('energyprogram',t),('energyread',r)]:
                key=f'{name}_{i}';names.append(key)
                lines.append(f'meas tran {key} integ supply_power from={start:.12g} to={start+2e-6:.12g}')
            if args.offset_refresh_each_slot:
                key=f'energyserviceperiod_{i}';names.append(key)
                start=r-(5.3+args.reference_extra_us)*1e-6;end=start+slot_us*1e-6
                lines.append(f'meas tran {key} integ supply_power from={start:.12g} to={end:.12g}')
    lines += ['quit','.endc','.end'];deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
                         '--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir',prefix,
                         '--entrypoint','timeout','eventspikeseg:analog-ngspice47',str(args.simulation_timeout_s),'ngspice','-b',
                         '/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=args.simulation_timeout_s+15)
    log=proc.stdout+proc.stderr;logpath=BASE/f'results/{stem}.log';logpath.write_text(log)
    values={k:float(v) for k,v in re.findall(r'(?m)^\s*((?:program|gateprogram|released|held|read|gateread|energyprogram|energyread|energyserviceperiod|beforecapture|captured|buspresample|gatepresample|bustrackend|gatetrackend|sampletrackend|acquisitionpresample|acquisitiontrackend|restoreprogram|restorereleased|restoregate|restoreref|offsetbefore|offsetafter|heldafteruse|topduringuse|bottomduringuse|referencebus|referencegate|caldeltabefore|caldeltaafter|caldeltasettled|offsetpreuse|offsettopon|offsetbottomon|offsetwriteend|bufferbeforecap|bufferaftercap|followread|followgate)_\d+)\s*=\s*([-+0-9.eE]+)',log)}
    complete=proc.returncode==0 and 'ngspice-47 done' in log and len(values)==len(names)
    rows=[{name:values[f'{name}_{i}'] for name in ['program','gateprogram','released','held','read','gateread']} for i in range(args.slots)] if complete else []
    stats={}
    if complete:
        if args.sampled_restore:
            for i,row in enumerate(rows):
                row.update({name:values[f'{name}_{i}'] for name in ['beforecapture','captured','restoreprogram','restorereleased','restoregate','restoreref']})
                row.update({name:values[f'{name}_{i}'] for name in ['buspresample','gatepresample','bustrackend','gatetrackend','sampletrackend']})
                row['sampling_phase_diagnostics_uv']={
                    'bus_during_track_change':(row['bustrackend']-row['buspresample'])*1e6,
                    'state_during_track_change':(row['gatetrackend']-row['gatepresample'])*1e6,
                    'sample_track_end_minus_bus':(row['sampletrackend']-row['bustrackend'])*1e6,
                    'sample_after_release_minus_track_end':(row['captured']-row['sampletrackend'])*1e6,
                    'state_after_sample_minus_track_end':(row['gateread']-row['gatetrackend'])*1e6}
                if args.physical_acquisition_buffer:
                    row.update({name:values[f'{name}_{i}'] for name in ['acquisitionpresample','acquisitiontrackend']})
                    row['sample_track_end_minus_acquisition_buffer_uv']=(row['sampletrackend']-row['acquisitiontrackend'])*1e6
                row['sample_error_mv']=(row['captured']-row['beforecapture'])*1000
                row['roundtrip_bus_error_mv']=(row['restorereleased']-row['beforecapture'])*1000
                if args.physical_offset:
                    row.update({name:values[f'{name}_{i}'] for name in ['offsetbefore','offsetafter','offsetpreuse','offsettopon','offsetbottomon','offsetwriteend']})
                    row['offset_use_phase_steps_uv']={b+'_minus_'+a:(row[b]-row[a])*1e6 for a,b in zip(['offsetpreuse','offsettopon','offsetbottomon'],['offsettopon','offsetbottomon','offsetwriteend'])}
                    row.update({name:values[f'{name}_{i}'] for name in ['heldafteruse','topduringuse','bottomduringuse']})
                if args.offset_refresh_each_slot:
                    row.update({name:values[f'{name}_{i}'] for name in ['referencebus','referencegate','caldeltabefore','caldeltaafter','caldeltasettled']})
                    row['calibration_release_delta_uv']=(row['caldeltaafter']-row['caldeltabefore'])*1e6
                    row['calibration_settled_delta_uv']=(row['caldeltasettled']-row['caldeltabefore'])*1e6
                    row['offset_calibration_to_preuse_delta_uv']=(row['offsetpreuse']-row['caldeltasettled'])*1e6
                    if args.physical_sample_buffer:
                        row.update({name:values[f'{name}_{i}'] for name in ['bufferbeforecap','bufferaftercap']})
                        row['buffer_calibration_release_step_uv']=(row['bufferaftercap']-row['bufferbeforecap'])*1e6
                if args.verify_next_read:
                    row.update({name:values[f'{name}_{i}'] for name in ['followread','followgate']})
                    row['next_read_error_mv']=(row['followread']-row['beforecapture'])*1000
        stats={f'{name}_mean_v':statistics.mean(row[name] for row in rows) for name in ['program','released','read']}
        stats.update({f'{name}_std_mv':statistics.stdev(row[name] for row in rows)*1000 for name in ['program','released','read']})
        if args.measure_energy:
            for i,row in enumerate(rows):
                for name in ['energyprogram','energyread']:
                    row[name+'_j']=values[f'{name}_{i}']
            for name in ['energyprogram','energyread']:
                stats[name+'_mean_pj']=statistics.mean(row[name+'_j'] for row in rows)*1e12
            if args.offset_refresh_each_slot:
                for i,row in enumerate(rows):
                    row['energyserviceperiod_j']=values[f'energyserviceperiod_{i}']
                stats['energyserviceperiod_mean_pj']=statistics.mean(row['energyserviceperiod_j'] for row in rows)*1e12
                stats['serviceperiod_vdd_mean_power_mw']=stats['energyserviceperiod_mean_pj']/(slot_us*1e3)
    report={'simulation_completed':complete,'simulator_returncode':proc.returncode,
            'simulation_timeout_s':args.simulation_timeout_s,'measured_values_count':len(values),'expected_measured_values_count':len(names),'seed':args.seed,'local_mismatch_enabled':bool(args.mismatch),
            'descriptive_run_name':descriptive_run_name,'command_arguments':vars(args),
            'source_snapshot':source_snapshot.relative_to(ROOT).as_posix(),
            'slots':args.slots,'rows':rows,'statistics':stats,'physical_state_accepted':False,
            'combined_routed_writer':args.combined_writer,
            'writer_input_pair_width_um':args.writer_input_width_um,
            'corner':args.corner,'temperature_c':args.temp_c,'setpoint_v':args.setpoint_v,'mim_corner':'typical',
            'energy_measured':args.measure_energy,
            'sampled_restore':args.sampled_restore,'sample_switch_nf_width_um':args.sample_switch_nwidth_um,'hold_mim_count':args.hold_mim_count if args.sampled_restore else None,
            'offset_extra_mim_count':args.offset_extra_mim_count,
            'total_offset_mim_count':args.offset_mim_count+args.offset_extra_mim_count if args.physical_offset else 0,
            'physical_offset_storage_subtraction':args.physical_offset,'offset_mim_count':args.offset_mim_count if args.physical_offset else None,
            'combined_routed_offset_module':args.combined_offset_module,
            'combined_routed_offset_short_split':args.combined_offset_short_split,
            'offset_isolated_routes':args.offset_isolated_routes,
            'integration_method':args.integration_method,
            'diagnostic_ideal_charge_fc':args.probe_charge_fc,
            'max_step_ns':args.max_step_ns,
            'sample_acquisition_us':1.2+args.sample_extra_us,
            'scheduled_slot_us':slot_us if args.sampled_restore else 5,
            'reference_extra_us':args.reference_extra_us,
            'reference_read_duration_us':3+args.reference_extra_us if args.offset_refresh_each_slot else None,
            'reference_calibration_acquisition_us':2+args.reference_extra_us if args.offset_refresh_each_slot else None,
            'restore_extra_us':args.restore_extra_us,
            'write_feedback_duration_us':2+args.restore_extra_us if args.sampled_restore else 2,
            'physical_sample_buffer':args.physical_sample_buffer,
            'physical_acquisition_buffer':args.physical_acquisition_buffer,
            'offset_reversed_plates':args.offset_reversed_plates,
            'offset_dummy_bottom':args.offset_dummy_bottom,
            'offset_sample_dummy_bottom':args.offset_sample_dummy_bottom,
            'offset_switch_width_scale':args.offset_switch_width_scale,
            'offset_sample_clock_trim_um':args.offset_sample_clock_trim_um,
            'offset_sample_clock_trim_net':args.offset_sample_clock_trim_net,
            'calibration_dummy_nf_width_um':args.offset_sample_dummy_nwidth_um if args.offset_sample_dummy_bottom else None,
            'offset_split_sample':args.offset_split_sample,
            'offset_sample_bottom_advance_ns':args.offset_sample_bottom_advance_ns,
            'offset_refresh_each_slot':args.offset_refresh_each_slot,
            'offset_continuous_use':args.offset_continuous_use,
            'offset_continuous_clamp_startup_only':args.offset_continuous_clamp_startup_only,
            'physical_zero_reference_cells':1 if args.offset_refresh_each_slot else 0,
            'writer_reference_current_ua':args.reference_ua,
            'verify_next_read':args.verify_next_read,
            'follow_delay_from_last_slot_start_us':args.follow_delay_us if args.verify_next_read else None,
            'minimum_idle_hold_after_hold_reset_us':args.follow_delay_us-(7+args.sample_extra_us+args.restore_extra_us) if args.verify_next_read else None,
            'bottom_plate_stagger_ns':args.bottom_plate_stagger_ns,
            'offset_acquire_us':args.offset_acquire_us,
            'offset_refresh_on_read':args.offset_refresh_on_read,
            'offset_dedicated_read':args.offset_dedicated_read,
            'scope':'One shared extracted OTA sequentially programs separate extracted state/sensor slots against their own source-follower read bus; physical read/write/input-mux/park switches and MIM loads. Reference setpoint1.2V defines encoded model zero, not absolute1.65V gate zero. Ideal read/reference current, supplies/control and initial clamp; reference diode schematic. No combined routing/RPEX, sampled noise, accuracy, physical nonlinear encoder or complete PLIF/service acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),source_snapshot,*cells,deck,logpath,modeldir/'design.spice',modeldir/'sm141064.spice',modeldir/'sm141064_mim.spice']}}
    if args.combined_writer:
        report['sha256'][writer.relative_to(ROOT).as_posix()]=hashlib.sha256(writer.read_bytes()).hexdigest()
        report['scope']=report['scope'].replace('Reference diode schematic.','OTA/input mux/reference diode/compensation are one routed12MOS/1MIM writer; state/sensor/readbus load/park are separate extracted pieces.')
        if args.writer_input_width_um!=10:
            report['scope']+=f' Writer uses independently routed/extracted{args.writer_input_width_um:g}um differential-input NFET pair; buffer remains original10um-input writer. Gain/settling/noise/mismatch/input range require requalification; no acceptance from smaller input load.'
    report['scope']=report['scope'].replace('setpoint1.2V',f'setpoint{args.setpoint_v:g}V')
    if args.measure_energy:
        report['scope'] += ' Energy integrates VDD supply over2us program/read windows and includes writer quiescent/reference current; excludes initial-clamp/setpoint/phase-driver supplies, complete channel service, array leakage and full-chip power.'
    if args.sampled_restore:
        report['scope'] += ' Restore reference is physically sampled through extracted TG onto grounded22um MIM caps, then selected through physical reference muxes into the writer. No software oracle for capture/restore; shared-offset subtraction still absent. Deterministic round trip only, not sampled noise or a complete SNN update.'
    if args.physical_offset:
        report['scope']=report['scope'].replace('shared-offset subtraction still absent','shared offset physically captured from first slot released zero versus setpoint onto floating22um MIM, then bottom plate drives restore reference while top plate connects held sample. No software offset oracle; capacitor reuse disturbance measured')
    if args.combined_offset_module or args.combined_offset_short_split:
        report['sha256'][offset_module.relative_to(ROOT).as_posix()]=hashlib.sha256(offset_module.read_bytes()).hexdigest()
        report['scope'] += ' Offset storage and four plate/reference-selection TGs are one routed8MOS/1MIM macro with capacitance extraction; complete sampler/writer/state assembly routing and resistance extraction remain absent.'
        if args.combined_offset_short_split:
            report['scope']=report['scope'].replace('routed8MOS/1MIM','routed8MOS/4MIM with separate bottom-plate controls')
    if args.offset_dedicated_read:
        report['scope'] += ' Shared offset captured during a dedicated3us first-slot zero-reference read6us before signal acquisition. Extra resident-state read disturbance and calibration overhead are included in this transient, not qualified for full service.'
    if args.probe_charge_fc:
        report['scope'] += ' Nonreference slots receive one ideal diagnostic charge pulse at1ms to screen nonzero restore; slot0 remains zero calibration. This does not qualify a synaptic injector, learned weights, nonlinear encoder or PLIF update.'
    if args.sample_extra_us:
        report['scope'] += f' Signal acquisition extended to{1.2+args.sample_extra_us:g}us; subsequent restore/control/measurements shifted equally. Total scheduled slot{slot_us:g}us includes any restore extension. No population service acceptance.'
    if args.restore_extra_us:
        report['scope']+=f' Write/feedback/plate-use end phases and end-of-write measurements extended together by{args.restore_extra_us:g}us; sampled acquisition unchanged. Total slot{slot_us:g}us. Extra service/energy cost included, not qualified population throughput.'
    if args.reference_extra_us:
        report['scope']+=f' Per-slot reference read/capture start{args.reference_extra_us:g}us earlier with ends unchanged: read{3+args.reference_extra_us:g}us/capture{2+args.reference_extra_us:g}us. Slot{slot_us:g}us and extended reference-window VDD energy included; initialization read unchanged. No population throughput or accuracy acceptance.'
    if args.physical_sample_buffer:
        report['scope'] += ' A second routed12MOS/1MIM writer runs as unity buffer, supplied by separate ideal20uA reference. Physical input TGs select calibration readbus or held sample; offset capture and restore plate drive both pass through this same buffer. Extra area/power/noise/settling and calibration reuse remain unqualified; no ideal buffer or software offset correction.'
    if args.offset_reversed_plates:
        report['scope'] += ' Reversed routed offset MIM plates: logical driven TOP connects native bottom plate and logical floating BOTTOM connects native top plate. Uses extracted parasitics, not deleted substrate capacitance.'
    if args.offset_extra_mim_count:
        report['scope'] += f' Adds{args.offset_extra_mim_count} separately extracted22um MIM capacitors in parallel with reversed physical plates and grounded substrates. Added shared-channel capacitor area/acquisition cost is provisional; no combined extension routing/RPEX or noise/model acceptance.'
    if args.offset_dummy_bottom:
        report['scope'] += ' Routed complementary half-width NF/PF bottom dummy devices, with D/S intentionally shorted to BOTTOM. Exact merged-terminal extraction warnings reviewed and retained in layout qualification; no numerical charge correction.'
    if args.physical_acquisition_buffer:
        report['scope']+=f' Additional routed12MOS/1MIM unity buffer before acquisition TG; same physical two-buffer path drives calibration. Extra ideal{args.reference_ua:g}uA reference included in VDD energy when selected. Read bus directly loads buffer input, not hold-bank capacitance. Noise, settling, full assembly and accuracy unqualified.'
    if args.sample_switch_nwidth_um!=1:
        report['scope']+=f' Only acquisition TG is replaced by physically routed{args.sample_switch_nwidth_um:g}um NF/{2*args.sample_switch_nwidth_um:g}um PF,L0.28um. All other switches unchanged; settling/noise/accuracy require qualification.'
    if args.sampled_restore:
        report['scope']+=' Sampling diagnostics compare20ns before track starts (0.48us after read starts) with40ns before track ends and200ns after release, including normal read settling and state/bus interaction; measurements do not uniquely attribute changes to switch injection.'
    if args.offset_continuous_use:
        report['scope']+=' Physical offset top/bottom use TGs remain on; no ideal correction. Phase diagnostic times labelled top/bottom-on are comparison timestamps, not use-clock transitions in this mode. Switched noise, reference lifetime and full PLIF unqualified.'
        if args.offset_continuous_clamp_startup_only:
            report['scope']+=' Separate reference clamp opens100ns after first calibration starts and remains off; thereafter physical sample-bottom TG clamps reference during calibration.'
        else:
            report['scope']+=' Separate reference clamp stays on through startup/first calibration and closes again during later calibration windows.'
    if args.offset_switch_width_scale!=1:
        report['scope']+=' Offset-bank plate switches physically resized to0.5um NF/1um PF, L0.28um; no ideal gain or offset correction.'
    if args.offset_sample_dummy_bottom:
        report['scope']=report['scope'].replace('routed8MOS/4MIM','routed10MOS/4MIM')
        report['scope']+=f' Routed complementary{args.offset_sample_dummy_nwidth_um:g}um NF/{2*args.offset_sample_dummy_nwidth_um:g}um PF dummy devices have D/S intentionally shorted to BOTTOM and gates opposite the calibration-sample pair. Exact extraction warnings/connectivity/dimensions retained and checked in unique LVS qualification; physical charge-compensation candidate, no numerical correction or noise/accuracy acceptance.'
    if args.offset_split_sample:
        order='before' if args.offset_sample_bottom_advance_ns>=0 else 'after'
        report['scope']+=f' Uses independently routed split calibration-bottom SAMPLEBOTTOM controls. Bottom calibration switch opens{abs(args.offset_sample_bottom_advance_ns):g}ns {order} top/input-calibration switches with finite10ns edges. Routing parasitics included; no software offset correction, noise/model/service acceptance.'
    if args.offset_refresh_each_slot:
        report['scope'] += ' Adds one separately extracted physical zero-reference state/sensor, initialized once at5us and read3us before each signal slot; physical offset capacitor recaptured for2us during each reference read. Reference cell read disturbance and all timings included. Extra calibration rail is not one of the model logical states; final population/service/area acceptance remains absent.'
        report['scope']=report['scope'].replace('slot0 remains zero calibration','slot0 is a zero-state control; separate physical reference cell supplies calibration')
        if args.measure_energy:
            report['scope'] += f' VDD energy additionally integrated over each{slot_us:g}us scheduled service period, including reference read/capture, signal acquire/restore and two continuously biased routed writers; excludes external supply/control/current-reference generation, events/PLIF dynamics and accepted population power.'
    if args.physical_acquisition_buffer:
        report['scope']=report['scope'].replace('two continuously biased routed writers','three continuously biased routed writers')
    report['scope']=report['scope'].replace('ideal20uA reference',f'ideal{args.reference_ua:g}uA reference')
    if args.verify_next_read:
        report['scope'] += f' All slots read again{args.follow_delay_us:g}us after last signal-slot start, at least{args.follow_delay_us-(7+args.sample_extra_us+args.restore_extra_us):g}us after final hold-reset phase, through actual sensor/park/read-current phases. Next-read error includes writer idle relaxation and read disturbance. One follow read only; no full multi-bin PLIF/state lifetime or sampled-noise acceptance.'
    report['sha256'][Path(__file__).relative_to(ROOT).as_posix()]=source_sha_at_start
    (BASE/f'results/{stem}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'simulation_completed':complete,'statistics':stats,'rows':rows},indent=2))
    if not complete:
        raise RuntimeError(log[-2500:])


if __name__=='__main__':
    main()
