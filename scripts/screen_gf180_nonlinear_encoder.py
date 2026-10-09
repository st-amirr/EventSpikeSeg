"""Measure a physical complementary-feedback encoder; no ideal inverse or SNN claim."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def physical_settings_match(settings,args):
    defaults={'compensation_bank_clamp':False,'physical_controller_hysteresis':False,'physical_controller_threshold_scale':1,'physical_compensation_controller':False,'buffer_reference_ua':None,'feedback_scale':1,'minimum_feedback_size_um':7,'switched_compensation':False,'lift_reference_na':2,'lift_reference_node':'span','source_lifted':False,'self_biased_span':False,'calibration_na':1,'input_feedback_mim_count':0,'mirrored_feedback':False,'corner':None,'temp_c':None,'span_v':None,'reference_ua':None}
    return all(settings.get(key,default)==getattr(args,key) for key,default in defaults.items())


def main():
    source_bytes=Path(__file__).read_bytes()
    sha=hashlib.sha256(source_bytes).hexdigest()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corner',choices=['typical','ff','ss'],default='typical')
    parser.add_argument('--temp-c',type=float,default=27)
    parser.add_argument('--span-v',type=float,default=1.0)
    parser.add_argument('--reference-ua',type=float,default=1)
    parser.add_argument('--buffer-reference-ua',type=float,default=None)
    parser.add_argument('--physical-compensation-controller',action='store_true')
    parser.add_argument('--physical-controller-threshold-scale',type=float,choices=[.25,.5,1],default=1)
    parser.add_argument('--physical-controller-hysteresis',action='store_true')
    parser.add_argument('--reuse-zero-noise-op',action='store_true')
    parser.add_argument('--compensation-bank-clamp',action='store_true')
    parser.add_argument('--dc-reset-points',action='store_true')
    parser.add_argument('--op-iterations',type=int,choices=[100,1000],default=100)
    parser.add_argument('--transient',action='store_true')
    parser.add_argument('--transient-without-dc',action='store_true',help='Measure dynamic stability only; no DC error or settling acceptance')
    parser.add_argument('--noise',action='store_true')
    parser.add_argument('--noise-input-na',type=float,choices=[-200,-20,-1,0,1,20,200],default=0)
    parser.add_argument('--transient-max-step-ns',type=int,choices=[25,50,500],default=50)
    parser.add_argument('--phase-us',type=int,choices=[20,50,100,200,1000],default=20)
    parser.add_argument('--input-feedback-mim-count',type=int,choices=[0,1,4,40,200],default=0)
    parser.add_argument('--integration-method',choices=['trap','gear'],default='trap')
    parser.add_argument('--mirrored-feedback',action='store_true')
    parser.add_argument('--self-biased-span',action='store_true')
    parser.add_argument('--calibration-na',type=float,choices=[.001,.01,.1,.5,1,2,5,10],default=1)
    parser.add_argument('--source-lifted',action='store_true')
    parser.add_argument('--lift-reference-na',type=float,choices=[2,20],default=2)
    parser.add_argument('--lift-reference-node',choices=['span','nf-diode'],default='span')
    parser.add_argument('--switched-compensation',action='store_true')
    parser.add_argument('--minimum-feedback-size-um',type=int,choices=[5,7],default=7)
    parser.add_argument('--feedback-scale',type=int,choices=[1,10,50],default=1)
    args=parser.parse_args()
    if args.transient_without_dc and not args.transient:
        raise ValueError('Dynamic-only mode requires transient')
    if args.noise and args.transient:
        raise ValueError('Noise and transient are distinct diagnostic runs')
    if args.self_biased_span and not args.mirrored_feedback:
        raise ValueError('Self-biased reference requires mirrored feedback')
    if args.source_lifted and not args.self_biased_span:
        raise ValueError('Source lift requires physical self-biased span')
    if args.switched_compensation and not (args.source_lifted and args.input_feedback_mim_count>=4):
        raise ValueError('Switched compensation requires lifted encoder and at least four feedback MIMs')
    if args.minimum_feedback_size_um!=7 and not args.switched_compensation:
        raise ValueError('Resized minimum feedback requires switched compensation')
    if args.feedback_scale!=1 and not args.source_lifted:
        raise ValueError('Proportional geometry/current scaling requires lifted source')
    if args.buffer_reference_ua is not None and not (args.self_biased_span and .5<=args.buffer_reference_ua<=20):
        raise ValueError('Separate buffer bias requires self-biased reference and0.5..20uA')
    if args.physical_compensation_controller and not (args.switched_compensation and args.feedback_scale==10):
        raise ValueError('Physical controller currently requires switched compensation and scale10')
    if args.physical_controller_threshold_scale!=1 and not args.physical_compensation_controller:
        raise ValueError('Physical threshold scale requires controller')
    if args.physical_controller_hysteresis and not args.physical_compensation_controller:
        raise ValueError('Hysteresis requires physical controller')
    if args.reuse_zero_noise_op and (args.noise or args.transient):
        raise ValueError('Zero-noise operating-point initialization is a DC solver diagnostic only')
    if args.compensation_bank_clamp and not args.physical_compensation_controller:
        raise ValueError('Physical bank clamp requires physical compensation controller')
    if args.dc_reset_points and (args.noise or args.transient):
        raise ValueError('Per-point solver reset is a DC-only diagnostic')
    if not .6<=args.span_v<=1.4 or not .5<=args.reference_ua<=20:
        raise ValueError('Diagnostic reference range exceeded')
    names=['gf180_shared_ota_core_pmos_input','gf180_complementary_encoder_feedback_grounded',
           'gf180_pmos_bias_reference_grounded','gf180_mim_7x7','gf180_mim_22x22']
    if args.mirrored_feedback:names[1]='gf180_mirrored_encoder_feedback_grounded'
    if args.self_biased_span:names.append('gf180_complementary_encoder_feedback_grounded')
    if args.source_lifted:
        names[1]+='_source_lifted'
        names.append('gf180_complementary_encoder_feedback_grounded_source_lifted')
        if args.feedback_scale!=1:
            names[1]+=f'_w{args.feedback_scale}';names[-1]+=f'_w{args.feedback_scale}'
    if args.switched_compensation:names.append('gf180_fixed_body_tg')
    if args.minimum_feedback_size_um!=7:names.append('gf180_mim_5x5')
    if args.physical_compensation_controller:
        names[1]+='_observer_ports'
        names.append('gf180_encoder_peak_detector_scale10')
        if args.physical_controller_threshold_scale!=1:
            names[-1]+='_threshold'+f'{args.physical_controller_threshold_scale:g}'.replace('.','p')
        if args.physical_controller_hysteresis:names[-1]+='_hysteresis'
    controller_cell=names[-1] if args.physical_compensation_controller else None
    cells=[BASE/'layout'/name/(name+'_cap.spice') for name in names]
    qualifications=[]
    sources=[Path(__file__)]
    for name,cell in zip(names,cells):
        qpath=cell.parent/'qualification.json';q=json.loads(qpath.read_text())
        if q.get('magic_drc_count')!=0 or not q.get('lvs_unique',q.get('netgen_lvs_unique',False)):
            raise ValueError(f'Unqualified layout: {name}')
        if q['sha256'][cell.name]!=hashlib.sha256(cell.read_bytes()).hexdigest():
            raise ValueError(f'Layout capacitance provenance mismatch: {name}')
        qualifications.append(q);sources.extend([qpath,cell])
    stem=f'gf180_nonlinear_encoder_{args.corner}{args.temp_c:g}_span{args.span_v:g}_ref{args.reference_ua:g}_src{sha[:12]}'
    if args.mirrored_feedback:stem+='_mirrored'
    if args.self_biased_span:stem+=f'_selfbias{args.calibration_na:g}na'
    if args.source_lifted:stem+='_sourcelifted'
    if args.source_lifted and (args.lift_reference_na!=2 or args.lift_reference_node!='span'):
        stem+=f'_lift{args.lift_reference_na:g}na_{args.lift_reference_node}'
    if args.switched_compensation:stem+='_switchedcomp'
    if args.minimum_feedback_size_um!=7:stem+=f'_minfeedback{args.minimum_feedback_size_um}um'
    if args.feedback_scale!=1:stem+=f'_feedbackscale{args.feedback_scale}'
    if args.buffer_reference_ua is not None:stem+=f'_bufferref{args.buffer_reference_ua:g}ua'
    if args.physical_compensation_controller:stem+='_physicalcontrol'
    if args.physical_controller_threshold_scale!=1:stem+=f'_threshold{args.physical_controller_threshold_scale:g}'
    if args.physical_controller_hysteresis:stem+='_hysteresis'
    if args.reuse_zero_noise_op:stem+='_zeronodeset'
    if args.compensation_bank_clamp:stem+='_bankclamp'
    if args.dc_reset_points:stem+='_dcreset'
    if args.op_iterations!=100:stem+=f'_opiterations{args.op_iterations}'
    if args.input_feedback_mim_count:stem+=f'_inputfeedback{args.input_feedback_mim_count}mim'
    if args.transient and args.integration_method!='trap':stem+='_'+args.integration_method
    if args.transient:stem+=f'_transient{args.phase_us}us'
    if args.transient_without_dc:stem+='_noreference'
    if args.transient and args.transient_max_step_ns!=50:stem+=f'_maxstep{args.transient_max_step_ns}ns'
    if args.noise:stem+=f'_noise{args.noise_input_na:g}na'
    descriptive_stem=stem
    if len(stem)>210:
        stem=stem[:110]+'_run'+hashlib.sha256(stem.encode()).hexdigest()[:24]
    spectrum_path=BASE/'results'/(stem+'_spectrum.dat')
    modeldir=BASE/'pdk/gf180_primitive_source/models/ngspice'
    prefix='/workspace/'+modeldir.relative_to(ROOT).as_posix()
    snapshot=BASE/'tools/source_snapshots'/f'nonlinear_encoder_{sha}.py'
    snapshot.parent.mkdir(parents=True,exist_ok=True)
    if not snapshot.exists():snapshot.write_bytes(source_bytes)
    sources.append(snapshot)
    lines=['GF180 physical complementary nonlinear feedback encoder',
           f'.include {prefix}/design.spice','.param sw_stat_global=0 sw_stat_mismatch=0',
           f'.lib {prefix}/sm141064.spice {args.corner}',f'.lib {prefix}/sm141064.spice mimcap_typical',
           f'.temp {args.temp_c:g}', f'.options method={args.integration_method} itl1={args.op_iterations} gmin=1e-18 reltol=1e-7 abstol=1e-17 vntol=1e-11']
    for cell in cells:lines.extend(cell.read_text().splitlines())
    lines.extend(['Vdd vdd 0 3.3',f'Vspan span 0 {args.span_v:g}',f'Vcommon common 0 {args.span_v/2:g}',
                  f'Ireference bias 0 {args.reference_ua:g}u','Xbias bias vdd 0 gf180_pmos_bias_reference_grounded',
                  'Xota sum common enc vdd 0 bias cmp gf180_shared_ota_core_pmos_input',
                  'Xfeedback sum enc span 0 gf180_complementary_encoder_feedback_grounded',
                  'Xcomp cmp enc 0 gf180_mim_22x22','Xload enc 0 0 gf180_mim_7x7',
                  'Iinput 0 sum 0','.control','set numdgt=15'])
    input_terminals='sum 0' if args.mirrored_feedback else '0 sum'
    if args.mirrored_feedback:
        lines=[line.replace('Xota sum common enc ', 'Xota common sum enc ')
                   .replace('Xfeedback sum enc span 0 gf180_complementary_encoder_feedback_grounded',
                            'Xfeedback sum enc span 0 vdd gf180_mirrored_encoder_feedback_grounded')
                   .replace('Iinput 0 sum 0','Iinput sum 0 0') for line in lines]
    if args.input_feedback_mim_count:
        insertion=lines.index('.control')
        lines[insertion:insertion]=[f'Xinputfeedback{i} '+('enc' if args.mirrored_feedback else 'cmp')+' sum 0 gf180_mim_7x7' for i in range(args.input_feedback_mim_count)]
    if args.self_biased_span:
        lines=[line for line in lines if not line.startswith(('Vspan ', 'Vcommon '))]
        insertion=lines.index('.control')
        lines[insertion:insertion]=[
            f'Icalibration vdd calspan {args.calibration_na*args.feedback_scale:g}n',
            'Xcalibration common common calspan 0 gf180_complementary_encoder_feedback_grounded',
            'Xspanbuffer calspan span_pre span_pre vdd 0 bias spancmp gf180_shared_ota_core_pmos_input',
            'Xspancomp spancmp span_pre 0 gf180_mim_22x22',
            'Xspanload span_pre 0 0 gf180_mim_7x7',
            'Vspan span_pre span 0']
    if args.source_lifted:
        lines=[line.replace('Xfeedback sum enc span 0 vdd gf180_mirrored_encoder_feedback_grounded',
                            'Xfeedback sum enc span 0 vdd low gf180_mirrored_encoder_feedback_grounded_source_lifted')
                   .replace('Xcalibration common common calspan 0 gf180_complementary_encoder_feedback_grounded',
                            'Xcalibration common common calspan 0 low gf180_complementary_encoder_feedback_grounded_source_lifted') for line in lines]
        insertion=lines.index('.control')
        lines[insertion:insertion]=[
            f'Ilowreference vdd lowcalspan {args.lift_reference_na:g}n',
            'Xlowreference lowcommon lowcommon lowcalspan 0 gf180_complementary_encoder_feedback_grounded',
            'Xlowbuffer '+('lowcommon' if args.lift_reference_node=='nf-diode' else 'lowcalspan')+' low low vdd 0 bias lowcmp gf180_shared_ota_core_pmos_input',
            'Xlowcomp lowcmp low 0 gf180_mim_22x22',
            'Xlowload low 0 0 gf180_mim_7x7']
    if args.feedback_scale!=1:
        lines=[line+f'_w{args.feedback_scale}' if line.startswith(('Xfeedback ','Xcalibration ')) else line for line in lines]
    if args.buffer_reference_ua is not None:
        lines=[line.replace(' 0 bias ', ' 0 bufferbias ') if line.startswith(('Xspanbuffer ','Xlowbuffer ')) else line for line in lines]
        insertion=lines.index('.control')
        lines[insertion:insertion]=[f'Ibufferreference bufferbias 0 {args.buffer_reference_ua:g}u',
                                   'Xbufferbias bufferbias vdd 0 gf180_pmos_bias_reference_grounded']
    if args.switched_compensation:
        if args.minimum_feedback_size_um!=7:
            lines=[line.replace('Xinputfeedback0 enc sum 0 gf180_mim_7x7','Xinputfeedback0 enc sum 0 gf180_mim_5x5') for line in lines]
        for i in range(1,args.input_feedback_mim_count):
            lines=[line.replace(f'Xinputfeedback{i} enc sum 0 ',f'Xinputfeedback{i} enc compbank 0 ') for line in lines]
        insertion=lines.index('.control')
        initial=3.3 if args.noise and abs(args.noise_input_na)>=20 else 0
        lines[insertion:insertion]=['Xcompswitch compbank sum compen compenb 0 vdd gf180_fixed_body_tg',
                                  f'Vcompen compen 0 {initial:g}',f'Vcompenb compenb 0 {3.3-initial:g}']
    if args.physical_compensation_controller:
        lines=[line.rsplit(' ',1)[0]+' pmir nmir '+line.rsplit(' ',1)[1]+'_observer_ports' if line.startswith('Xfeedback ') else line for line in lines]
        lines=[line for line in lines if not line.startswith(('Vcompen ','Vcompenb '))]
        insertion=lines.index('.control')
        lines[insertion:insertion]=[f'Xpeakcontrol pmir nmir bias compen compenb vdd 0 {controller_cell}']
    if args.compensation_bank_clamp:
        insertion=lines.index('.control')
        lines[insertion:insertion]=[
            'Xclampbuffer common clampcommon clampcommon vdd 0 bias clampcmp gf180_shared_ota_core_pmos_input',
            'Xclampcomp clampcmp clampcommon 0 gf180_mim_22x22',
            'Xclampload clampcommon 0 0 gf180_mim_7x7',
            'Xbankclamp compbank clampcommon compenb compen 0 vdd gf180_fixed_body_tg']
    initialization_source=None
    if args.reuse_zero_noise_op:
        matches=[]
        for path in (BASE/'results').glob('gf180_nonlinear_encoder_*.json'):
            prior=json.loads(path.read_text());settings=prior.get('command_arguments',{})
            if prior.get('simulation_completed') and not prior.get('operating_point_solver_warning') and settings.get('noise') and settings.get('noise_input_na')==0 and physical_settings_match(settings,args) and all(prior.get('sha256',{}).get(cell.relative_to(ROOT).as_posix())==hashlib.sha256(cell.read_bytes()).hexdigest() for cell in cells):
                matches.append(path)
        if not matches:raise ValueError('Matching completed zero-bias noise OP required for nodeset')
        initialization_source=max(matches,key=lambda path:path.stat().st_mtime);sources.append(initialization_source)
        operating=json.loads(initialization_source.read_text())['analysis']['operating_point']
        nodeset='.nodeset '+' '.join(f'{key}={value:.15g}' for key,value in operating.items() if key.startswith('v('))
        lines.insert(lines.index('.control'),nodeset)
    positive=sorted(set([value*args.feedback_scale for value in [.0001,.0002,.0005,.001,.002,.005,.01,.02,.05,.1,.2,.5,1,2,5,10,20,50,100,200]]+[.0001,.0002,.0005]))
    currents=[-value for value in reversed(positive)]+[0]+positive
    for index,current in enumerate(currents if not (args.transient or args.noise) else []):
        if args.dc_reset_points:lines.append('reset')
        if args.switched_compensation and not args.physical_compensation_controller:
            level=3.3 if abs(current)>=20*args.feedback_scale else 0
            lines.extend([f'alter Vcompen {level:g}',f'alter Vcompenb {3.3-level:g}'])
        lines.extend([f'echo POINT_{index}',f'alter Iinput {current*1e-9:.15g}',
                      'op','print v(enc) v(sum) i(vdd) i(vspan) v(span) v(common)'+(' v(compen) v(compenb)' if args.switched_compensation else '')])
    dc_source=None
    dc_rows={}
    phase_currents=[value*args.feedback_scale for value in [0,1,20,200,-200,-20,-1,0]]
    if args.transient:
        matches=[]
        for path in (BASE/'results').glob('gf180_nonlinear_encoder_*.json'):
            prior=json.loads(path.read_text());settings=prior.get('command_arguments',{})
            if prior.get('simulation_completed') and not prior.get('operating_point_solver_warning') and not settings.get('transient') and not settings.get('noise') and physical_settings_match(settings,args):
                if all(prior.get('sha256',{}).get(cell.relative_to(ROOT).as_posix())==hashlib.sha256(cell.read_bytes()).hexdigest() for cell in cells):
                    matches.append(path)
        if not args.transient_without_dc:
            if not matches:raise ValueError('Matching extracted DC transfer without solver fallback required')
            dc_source=max(matches,key=lambda path:path.stat().st_mtime);sources.append(dc_source)
            prior=json.loads(dc_source.read_text());dc_rows={row['input_current_na']:row['v(enc)'] for row in prior['rows']}
        step=args.phase_us*1e-6
        points=[(0,0)]
        for i,current in enumerate(phase_currents):
            start=10e-6+i*step
            points.extend([(start-10e-9,(phase_currents[i-1] if i else 0)*1e-9),(start,current*1e-9)])
        source_line=f'Iinput {input_terminals} PWL('+' '.join(f'{at:.12g} {value:.12g}' for at,value in points)+')'
        lines=[source_line if line==f'Iinput {input_terminals} 0' else line for line in lines]
        if args.switched_compensation and not args.physical_compensation_controller:
            control_points=[(0,0)]
            for i,current in enumerate(phase_currents):
                start=10e-6+i*step
                previous=3.3 if i and abs(phase_currents[i-1])>=20*args.feedback_scale else 0
                level=3.3 if abs(current)>=20*args.feedback_scale else 0
                control_points.extend([(start-10e-9,previous),(start,level)])
            for name,invert in [('Vcompen',False),('Vcompenb',True)]:
                source=name+' '+('compenb' if invert else 'compen')+' 0 PWL('+' '.join(f'{at:.12g} {(3.3-value if invert else value):.12g}' for at,value in control_points)+')'
                lines=[source if line.startswith(name+' ') else line for line in lines]
        lines.extend(['setseed 17','reset',f'tran {args.transient_max_step_ns}n {10e-6+len(phase_currents)*step+1e-6:.12g}','let power_vdd=-3.3*i(vdd)'])
        for i,current in enumerate(phase_currents):
            start=10e-6+i*step
            for name,at in [('early',start+.5e-6),('mid',start+2e-6),('late',start+step-.1e-6)]:
                lines.append(f'meas tran {name}_{i} find v(enc) at={at:.12g}')
            lines.append(f'meas tran sumlate_{i} find v(sum) at={start+step-.1e-6:.12g}')
            lines.append(f'meas tran commonlate_{i} find v(common) at={start+step-.1e-6:.12g}')
            lines.append(f'meas tran energy_{i} integ power_vdd from={start:.12g} to={start+step:.12g}')
            window=min(5e-6,step*.1)
            for name,operator in [('late_min','min'),('late_max','max')]:
                lines.append(f'meas tran {name}_{i} {operator} v(enc) from={start+step-window:.12g} to={start+step-.1e-6:.12g}')
            if args.switched_compensation:
                lines.append(f'meas tran controllate_{i} find v(compen) at={start+step-.1e-6:.12g}')
                for name,operator in [('controlmin','min'),('controlmax','max')]:
                    lines.append(f'meas tran {name}_{i} {operator} v(compen) from={start+step-window:.12g} to={start+step-.1e-6:.12g}')
    if args.noise:
        lines=[f'Iinput {input_terminals} DC {args.noise_input_na*args.feedback_scale*1e-9:.15g} AC 1' if line==f'Iinput {input_terminals} 0' else line for line in lines]
        lines.extend(['op','print v(enc) v(sum) i(vdd) v(span) v(common)'+(' v(compen) v(compenb)' if args.switched_compensation else ''),
                      'noise v(enc) Iinput dec 40 10 100Meg',
                      'setplot noise1',
                      'wrdata /workspace/'+spectrum_path.relative_to(ROOT).as_posix()+' onoise_spectrum',
                      'setplot noise2',
                      'print onoise_total inoise_total'])
    lines.extend(['quit','.endc','.end'])
    deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='ascii')
    proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2',
        '--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout',
        'eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],
        capture_output=True,text=True,timeout=135)
    log=proc.stdout+proc.stderr;logpath=BASE/'results'/(stem+'.log');logpath.write_text(log)
    rows=[]
    for index,block in re.findall(r'POINT_(\d+)\s*\n(.*?)(?=POINT_\d+\s*\n|\Z)',log,re.S):
        values={key.lower():float(value) for key,value in re.findall(
            r'(?mi)^\s*(v\(enc\)|v\(sum\)|i\(vdd\)|i\(vspan\)|v\(span\)|v\(common\)|v\(compen\)|v\(compenb\))\s*=\s*([-+0-9.eE]+)',block)}
        if len(values)==(8 if args.switched_compensation else 6):
            rows.append({'input_current_na':currents[int(index)],**values})
    if args.transient:
        values={key:float(value) for key,value in re.findall(r'(?m)^\s*((?:early|mid|late|sumlate|commonlate|energy|late_min|late_max|controllate|controlmin|controlmax)_\d+)\s*=\s*([-+0-9.eE]+)',log)}
        rows=[]
        fields=['early','mid','late','sumlate','commonlate','energy','late_min','late_max']+(['controllate','controlmin','controlmax'] if args.switched_compensation else [])
        if len(values)==len(fields)*len(phase_currents):
            rows=[{'input_current_na':current,**{name:values[f'{name}_{i}'] for name in fields}} for i,current in enumerate(phase_currents)]
            for row in rows:
                row['late_window_peak_to_peak_uv']=(max(row['late_max'],row['late'])-min(row['late_min'],row['late']))*1e6
                if dc_rows:
                    row['late_window_maximum_dc_error_uv']=max(abs(row[name]-dc_rows[row['input_current_na']])*1e6 for name in ['late_min','late_max','late'])
                    row['late_minus_dc_uv']=(row['late']-dc_rows[row['input_current_na']])*1e6
                    row['early_minus_dc_uv']=(row['early']-dc_rows[row['input_current_na']])*1e6
                row['late_sum_minus_reference_uv']=(row['sumlate']-row['commonlate'])*1e6
                row['energy_vdd_pj']=row['energy']*1e12
    noise_values={}
    if args.noise:
        noise_values={key.lower():float(value) for key,value in re.findall(r'(?mi)^\s*(onoise_total|inoise_total|v\(enc\)|v\(sum\)|i\(vdd\)|v\(span\)|v\(common\)|v\(compen\)|v\(compenb\))\s*=\s*([-+0-9.eE]+)',log)}
        rows=[]
    complete=proc.returncode==0 and 'ngspice-47 done' in log and (len(noise_values)==(9 if args.switched_compensation else 7) if args.noise else len(rows)==(len(phase_currents) if args.transient else len(currents)))
    analysis={}
    if complete and not (args.transient or args.noise):
        by_current={row['input_current_na']:row for row in rows}
        zero=by_current[0]['v(enc)']
        analysis={'zero_output_v':zero,
                  'maximum_sum_minus_reference_uv':max(abs(row['v(sum)']-row['v(common)'])*1e6 for row in rows),
                  'span_v_range':[min(row['v(span)'] for row in rows),max(row['v(span)'] for row in rows)],
                  'common_v_range':[min(row['v(common)'] for row in rows),max(row['v(common)'] for row in rows)],
                  'strictly_monotonic':all(b['v(enc)']>a['v(enc)'] for a,b in zip(rows,rows[1:])),
                  'central_gain_mv_per_na':(by_current[.1]['v(enc)']-by_current[-.1]['v(enc)'])*1000/.2,
                  'near_zero_0p1pa_gain_mv_per_na':(by_current[.0001]['v(enc)']-by_current[-.0001]['v(enc)'])*1000/.0002,
                  'positive_outer_gain_mv_per_na':(by_current[200*args.feedback_scale]['v(enc)']-by_current[100*args.feedback_scale]['v(enc)'])*1000/(100*args.feedback_scale),
                  'negative_outer_gain_mv_per_na':(by_current[-100*args.feedback_scale]['v(enc)']-by_current[-200*args.feedback_scale]['v(enc)'])*1000/(100*args.feedback_scale),
                  'encoded_span_v':[rows[0]['v(enc)'],rows[-1]['v(enc)']],
                  'zero_vdd_power_uw':-3.3*by_current[0]['i(vdd)']*1e6,
                  'supply_scope':('VDD includes the physical reference diode stacks and OTA buffers when self-biased/source-lifted. Ideal current-source generation, controls and state access excluded.' if args.self_biased_span else 'VDD only; regulated span/reference/control generation and state access excluded.')}
        for row in rows:row['output_relative_zero_v']=row['v(enc)']-zero
    if complete and args.transient:
        analysis={'maximum_absolute_late_minus_dc_uv':max(abs(row['late_minus_dc_uv']) for row in rows) if dc_rows else None,
                  'maximum_late_window_dc_error_uv':max(row['late_window_maximum_dc_error_uv'] for row in rows) if dc_rows else None,
                  'maximum_late_window_peak_to_peak_uv':max(row['late_window_peak_to_peak_uv'] for row in rows),
                  'maximum_absolute_late_sum_minus_reference_uv':max(abs(row['late_sum_minus_reference_uv']) for row in rows),
                  'service_phase_us':args.phase_us,
                  'mean_vdd_energy_per_phase_pj':sum(row['energy_vdd_pj'] for row in rows)/len(rows),
                  'scope':'Deterministic commanded-current steps, no synaptic accumulator, inverse, stored membrane or sampled-noise acceptance.'}
    if complete and args.noise:
        spectrum=[tuple(float(value) for value in line.split()) for line in spectrum_path.read_text().splitlines() if line.strip()]
        if not spectrum or any(len(row)!=2 for row in spectrum) or not all(b[0]>a[0] for a,b in zip(spectrum,spectrum[1:])):
            raise ValueError('Noise output spectrum must have strictly increasing frequency and one amplitude column')
        averages=[]
        for aperture_us in [0,1,20,100,1000]:
            powers=[]
            for frequency,amplitude in spectrum:
                argument=math.pi*frequency*aperture_us*1e-6
                weight=math.sin(argument)/argument if argument else 1
                powers.append(amplitude**2*weight**2)
            variance=sum((b[0]-a[0])*(pa+pb)/2 for a,b,pa,pb in zip(spectrum,spectrum[1:],powers,powers[1:]))
            averages.append({'ideal_boxcar_aperture_us':aperture_us,'stationary_average_output_rms_uv':math.sqrt(variance)*1e6})
        analysis={'encoded_output_rms_uv':noise_values['onoise_total']*1e6,
                  'ideal_stationary_boxcar_averages':averages,
                  'averaging_scope':'Analytic stationary PSD filtering only, no physical sampler/integrator, phase covariance or settled aperture qualification. Lower cutoff10Hz excludes slower reference noise/drift.',
                  'ngspice_integrated_input_referred_rms_na':noise_values['inoise_total']*1e9,
                  'noise_band_hz':[10,100e6], 'operating_point':noise_values,
                  'scope':'Stationary official-model noise at constant ideal input current with actual extracted encoder feedback. Not sampled noise, SNN state precision or noise of ideal reference supplies/current source.'}
        sources.append(spectrum_path)
    sources.extend([deck,logpath,*[modeldir/name for name in ['design.spice','sm141064.spice','sm141064_mim.spice']]])
    report={'simulation_completed':complete,'simulator_returncode':proc.returncode,
            'op_initialization_source':initialization_source.relative_to(ROOT).as_posix() if initialization_source else None,
            'descriptive_run_name':descriptive_stem,
            'command_arguments':vars(args),'source_snapshot':snapshot.relative_to(ROOT).as_posix(),
            'operating_point_solver_warning':bool(re.search(r'singular matrix|stepping failed|Transient op started',log,re.I)),
            'dc_source':dc_source.relative_to(ROOT).as_posix() if dc_source else None,
            'rows':rows,'analysis':analysis,'qualified_layout_components':qualifications,
            'physical_state_accepted':False,'encoder_accepted':False,'full_chip_accepted':False,
            'scope':'Signed-current compression/command settling using extracted seven-MOS PMOS-input OTA, '
                    +('six-MOS mirrored feedback' if args.mirrored_feedback else 'two-MOS complementary feedback pair')+
                    ', one-MOS PF bias reference and grounded-substrate MIM compensation/load. '
                    'Ideal diagnostic input/reference currents and VDD supply; span/common generation is specified by command arguments and following scope. Actual MOS feedback '
                    'measured, not prescribed asinh transfer. No inverse, state encoding/update, sampled noise, mismatch, '
                    'RPEX, combined encoder layout, float accuracy or population service acceptance.',
            'sha256':{path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}}
    report['sha256'][Path(__file__).relative_to(ROOT).as_posix()]=sha
    if args.transient_without_dc:
        report['scope']+=' Dynamic-only diagnostic: no trusted DC reference, no settling error computed and no accuracy acceptance. Final-window ripple, control swing and virtual-sum deviation are measured directly.'
    if args.mirrored_feedback:
        report['scope']+=' Six-MOS mirrored current feedback replaces direct drain feedback. SUM drives amplifier IN; positive diagnostic current sinks SUM. Optional physical fast-feedback MIM connects ENC to SUM, bypassing mirror response at high frequency. No ideal current mirror.'
    if args.self_biased_span:
        report['scope']+=' Self-biased span removes ideal span/common voltage sources: extracted NF/PF feedback pair is diode-connected in series with ideal diagnostic nA calibration current, its NF diode node defines common, and a second extracted seven-MOS OTA buffers the series voltage into span with physical MIM compensation/load. Noise of these reference transistors/buffer is included; calibration current source remains ideal. No physical nA generator or calibration servo, sampled-state or combined-layout acceptance.'
    if args.source_lifted:
        report['scope']+=f' New separately routed source-lifted six-/two-MOS cells retain NF body at VSS but elevate encoded NF source with a third physical OTA buffering the {args.lift_reference_node} node of a separate extracted{args.lift_reference_na:g}nA NF/PF diode stack. This provides headroom for smaller ideal calibration current; generator/silicon gate leakage/precision/combined layout remain unqualified. Low-reference current remains ideal.'
    if args.switched_compensation:
        report['scope']+=f' One extracted physical TG connects{args.input_feedback_mim_count-1} extra feedback MIMs under '+('a physical nine-MOS current-replica detector using encoder mirror gates and physical PF bias threshold' if args.physical_compensation_controller else f'ideal command-derived controls when absolute input current is at least{20*args.feedback_scale:g}nA')+'. One feedback MIM remains connected. Actual switch charge/capacitance/leakage included; detector threshold/chatter/noise/PVT/control-driver/assembled qualification requires measurement.'
        report['scope']+=f' Always-connected feedback MIM side{args.minimum_feedback_size_um}um; switched extra MIM sides7um unchanged.'
    if args.feedback_scale!=1:
        report['scope']+=f' Encoded NF/PF and matching calibration diode widths/current scaled{args.feedback_scale}x, input-current domain scaled{args.feedback_scale}x to preserve an intended current ratio, not an assumed identical transfer. Four mirror devices and low-reference stack/current unchanged. All row input currents are actual nA; noise_input_na argument is unscaled and actual noise input is argument times feedback_scale. Stability/noise/transfer/power and model-bin effects require measurement.'
    if args.buffer_reference_ua is not None:
        report['scope']+=f' Reference buffers receive a separate physical PF diode bias instance driven by an ideal{args.buffer_reference_ua:g}uA current source; encoder OTA remains at reference_ua. Physical buffer/bias device noise and VDD costs are included. Bias-current generation is still ideal.'
    if args.physical_controller_hysteresis:
        report['scope']+=' Physical controller has11MOS: two added PF devices make threshold current larger while disabled and smaller while enabled. No ideal hysteresis function; loop chatter, actual switching levels and stability require measurement.'
    if args.compensation_bank_clamp:
        report['scope']+=' Disabled extra-cap bank is clamped by a second physical TG to a physical unity OTA buffering common. The opposite control pair selects feedback or clamp, with actual MOS timing/capacitance/charge included; no ideal off-node voltage constraint. Additional OTA/MIM/bias energy and noise included; overlap and reference movement require measurement.'
    if args.reuse_zero_noise_op:
        report['scope']+=' DC nodeset reuses measured voltages from a matching zero-input noise operating point only as Newton initial guesses. No added voltage/current source or physical startup mechanism; final OP still must converge without fallback warnings. A solver guess is not an initialization circuit.'
    if args.dc_reset_points:
        report['scope']+=' Each DC point resets ngspice before altering diagnostic input current. This isolates numerical initial guesses from previous DC points; it is not physical reset/startup or hysteresis trajectory qualification.'
    if args.input_feedback_mim_count:
        report['scope']+=f' Adds{args.input_feedback_mim_count} extracted7um MIM from '+('ENC' if args.mirrored_feedback else 'inverting internal CMP')+' to SUM as physical input feedback. Full modeled capacitance/leakage retained; stability/transfer require measurement.'
    target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(target),'simulation_completed':complete,'analysis':analysis},indent=2))
    if not complete:raise RuntimeError(log[-2000:])


if __name__=='__main__':main()
