"""Physical CF-result resistor-to-encoder writeback and unity readback diagnostic."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
ROOT=flow.ROOT;BASE=flow.BASE;RCELL='gf180_writeback_resistor_123x1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--transient',type=Path,required=True);p.add_argument('--input-na',type=float,choices=[-200,0,200],default=200);p.add_argument('--max-step-ns',type=int,choices=[5,20],default=5);p.add_argument('--omit-current-probe',action='store_true');p.add_argument('--reset-dummy',action='store_true');p.add_argument('--reset-dummy-node',choices=['linear','integratesum'],default='linear');p.add_argument('--restore-switch-count',type=int,choices=[1,2,4,8],default=1);p.add_argument('--trim-bank-profile',type=Path);p.add_argument('--buffer-bank-park-reference',action='store_true');p.add_argument('--encode-us',type=int,choices=[1,5,10,20,25,30,50],default=50);p.add_argument('--feedback-mim-count',type=int,choices=[4,8,16,32],default=32);p.add_argument('--active-bias-ua',type=int,choices=[5,20,50],default=5);p.add_argument('--encoder-hold-mim-count',type=int,choices=[4,8,16],default=16);p.add_argument('--dump-waveforms',action='store_true');p.add_argument('--routed-mim-banks',action='store_true');p.add_argument('--reset-series-resistor-um',type=int,choices=[0,2,8],default=0);p.add_argument('--integration-order',type=int,choices=[1,2],default=2);p.add_argument('--integration-method',choices=['inherited','trap','gear'],default='inherited');a=p.parse_args();a.transient=a.transient.resolve();source=Path(__file__);sha=digest(source)
 delta=50-a.encode_us;unit_us=4*a.feedback_mim_count/32
 def shift(t):return t-2*delta if t>=117 else t-delta if t>=59 else t
 final_us=shift(130)
 donor=json.loads(a.transient.read_text());args=donor['command_arguments']
 if not donor['simulation_completed'] or not all(args.get(k) for k in ['physical_current_reference','physical_beta_driver','physical_park_driver','physical_mode_drivers','mode_driver_output_buffers','integrate_charge']):raise ValueError('Completed physically driven donor required')
 if args['capture_dummy_nf_width_um']!=.75 or args['capture_dummy_pf_width_um']!=1.22 or args['integration_mim_count']!=32 or args['cold_start_prelude_us'] or args['mismatch_seed'] is not None:raise ValueError('Bounded native donor contract differs')
 sources=[a.transient];snap=ROOT/donor['source_snapshot']
 for name,expected in donor['sha256'].items():
  f=snap if name=='scripts/screen_gf180_shared_encoder_inverse.py' else ROOT/name
  if digest(f)!=expected:raise ValueError('Donor provenance differs: '+name)
  sources.append(f)
 deck0=next(ROOT/name for name in donor['sha256'] if '/benches/' in name and 'shared_encoder_inverse' in name and name.endswith('.spice'))
 lines=deck0.read_text().split('.control')[0].splitlines();remove=['Iinput ','Vencodecommand ','Vdecodecommand ','Vbetacommand ','Vparkcommand '];lines=[x for x in lines if not x.startswith(tuple(remove))]
 lines=[x.replace('Xintegratorreset linear integratesum encode encodeb ','Xintegratorreset linear integratesum resetphase resetphaseb ') for x in lines]
 if a.active_bias_ua!=5:
  bias_lines=[i for i,x in enumerate(lines) if x.startswith('Iintegratorbias ')]
  if len(bias_lines)!=1:raise ValueError('Expected native shared bias-root current')
  lines[bias_lines[0]]=f'Iintegratorbias integratorbias 0 {a.active_bias_ua}u'
 lines=[x for x in lines if not (re.match(r'Xintegratorfeedback(\d+) ',x) and int(re.match(r'Xintegratorfeedback(\d+) ',x)[1])>=a.feedback_mim_count)]
 lines=[x for x in lines if not (re.match(r'Xcaptureextra(\d+) ',x) and int(re.match(r'Xcaptureextra(\d+) ',x)[1])>=a.encoder_hold_mim_count)]
 bank_qualified=[]
 if a.routed_mim_banks:
  if a.feedback_mim_count!=8 or a.encoder_hold_mim_count!=8:raise ValueError('Routed banks require eight feedback and eight extra ENC capacitors plus base load')
  for cell,native,count in [('gf180_mim_bank_7x7_n9','gf180_mim_7x7',9),('gf180_mim_bank_22x22_n8','gf180_mim_22x22',8)]:
   folder_bank=BASE/'layout'/cell;bank_qp=folder_bank/'qualification.json';bq=json.loads(bank_qp.read_text())
   if bq['magic_drc_count'] or not bq['lvs_unique'] or bq['extraction_feedback'] or bq['native_capacitor_instance_count']!=count or bq['native_cell']!=native:raise ValueError('Routed MIM bank qualification differs')
   for name,expected in bq['sha256'].items():
    f=folder_bank/name
    if digest(f)!=expected:raise ValueError('Routed bank provenance differs')
    sources.append(f)
   for name,expected in bq['input_sha256'].items():
    f=ROOT/name
    if digest(f)!=expected:raise ValueError('Routed bank native input differs')
    sources.append(f)
   sources.append(bank_qp);bank_qualified.append(bq);lines[1:1]=(folder_bank/(cell+'_cap.spice')).read_text().splitlines()
  lines=[x for x in lines if not x.startswith('Xload ') and not re.match(r'^X(?:captureextra|integratorfeedback)\d+ ',x)]
  lines+=['Xencoderholdbank enc 0 0 gf180_mim_bank_7x7_n9','Xfeedbackbank caplinear integratesum 0 gf180_mim_bank_22x22_n8']
 folder=BASE/'layout'/RCELL;qp=folder/'qualification.json';q=json.loads(qp.read_text())
 if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Native resistor unqualified')
 for name,expected in q['sha256'].items():
  f=folder/name
  if digest(f)!=expected:raise ValueError('Resistor source mismatch')
  sources.append(f)
 trim_metadata=None;trim_qualified=[];resistor_corner='res_typical'
 if a.trim_bank_profile:
  a.trim_bank_profile=a.trim_bank_profile.resolve();tr=json.loads(a.trim_bank_profile.read_text());ts=tr['settings']
  if not tr['simulation_completed'] or a.restore_switch_count!=4 or ts['mos_corner']!=donor['encoder_settings']['corner'] or float(ts['temp_c'])!=float(donor['encoder_settings']['temp_c']):raise ValueError('Trim profile corner/restore count mismatch')
  for name,expected in tr['sha256'].items():
   f=ROOT/name
   if digest(f)!=expected:raise ValueError('Trim provenance differs')
   sources.append(f)
  code=tr['analysis']['best_external_dc_code']['externally_selected_code'];resistor_corner=ts['resistor_corner'];sources.append(a.trim_bank_profile)
  trim_deck=next(ROOT/n for n in tr['sha256'] if '/benches/' in n and n.endswith('.spice'))
  trim_lines=[x for x in trim_deck.read_text().split('.control')[0].splitlines() if re.match(r'^(Xbase |Xsegment\d+ |Xbypass\d+_\d+ |Vbit\d+command |Xbit\d+(?:preA|preB|outP|outN) |Xrestoreout\d+ |Xbankpark\d+ )',x)]
  for i,x in enumerate(trim_lines):
   x=re.sub(r'\bp0\b','writeresfeed',x);x=re.sub(r'\bb\b','common' if x.startswith('Xbankpark') else 'sum',x)
   m=re.match(r'Vbit(\d+)command ',x)
   if m:x=x.rsplit(' ',1)[0]+(' 0' if code&(1<<int(m[1])) else ' 3.3')
   trim_lines[i]=x
  lines+=trim_lines
  for tq in tr['qualified_layout_components']:
   if tq['cell'].startswith('gf180_writeback_resistor_'):
    trim_qualified.append(tq);lines[1:1]=(BASE/'layout'/tq['cell']/(tq['cell']+'_cap.spice')).read_text().splitlines()
  trim_metadata={'profile':a.trim_bank_profile.relative_to(ROOT).as_posix(),'externally_selected_code':code,'autonomous_calibration_controller_implemented':False,'dc_numerical_precision_qualified':False,'two_ended_isolation':ts.get('two_ended_isolation',False),'park_bank':ts.get('park_bank',False)}
 if a.buffer_bank_park_reference:
  if not trim_metadata or not trim_metadata['park_bank']:raise ValueError('Physical park reference buffer requires parked trim bank')
  lines=[x.replace(' bankout common ',' bankout bankparkref ') if x.startswith('Xbankpark') else x for x in lines]
  lines+=['Xbankparkrefbuffer common bankparkref bankparkref vdd 0 integratorbias bankparkrefcmp gf180_shared_ota_core_pmos_input','Xbankparkrefcomp bankparkrefcmp bankparkref 0 gf180_mim_22x22','Xbankparkrefload bankparkref 0 0 gf180_mim_7x7']
  trim_metadata['park_reference_buffered']=True
 reset_qualified=[]
 if a.reset_series_resistor_um:
  cell=f'gf180_writeback_resistor_{a.reset_series_resistor_um}x1';rd=BASE/'layout'/cell;rqpath=rd/'qualification.json';rq=json.loads(rqpath.read_text())
  if rq['magic_drc_count'] or not rq['lvs_unique'] or rq['extraction_feedback']:raise ValueError('Native reset series resistor qualification required')
  for name,expected in rq['sha256'].items():
   f=rd/name
   if digest(f)!=expected:raise ValueError('Native reset resistor provenance differs')
   sources.append(f)
  sources.append(rqpath);reset_qualified.append(rq)
  if not any(x.startswith('.subckt '+cell+' ') for x in lines):lines[1:1]=(rd/(cell+'_cap.spice')).read_text().splitlines()
  lines=[x.replace('Xintegratorreset linear integratesum ', 'Xintegratorreset resetfeed integratesum ') for x in lines]
  lines.append('Xresetseries linear resetfeed 0 '+cell)
 sources.append(qp);lines[1:1]=(folder/(RCELL+'_cap.spice')).read_text().splitlines();md=BASE/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+md.relative_to(ROOT).as_posix();lines.append(f'.lib {prefix}/sm141064.spice {resistor_corner}')
 beta=donor['learned_beta_metadata']['beta_float32'];stop=61.5+unit_us*beta;unity_stop=121.5+unit_us
 def voltage(name,node,points):lines.append(name+' '+node+' 0 PWL('+' '.join(f'{shift(t)*1e-6:.12g} {v:.12g}' for t,v in points)+')')
 voltage('Vencodecommand','encodecommand',[(0,3.3),(59.9,3.3),(60,0),(68,0),(68.1,3.3),(118,3.3),(118.1,0),(130,0)])
 voltage('Vdecodecommand','decodecommand',[(0,0),(60,0),(60.1,3.3),(67.9,3.3),(68,0),(118.1,0),(118.2,3.3),(130,3.3)])
 voltage('Vbetacommand','betacommand',[(0,0),(61.5,0),(61.6,3.3),(stop-.1,3.3),(stop,0),(121.5,0),(121.6,3.3),(unity_stop-.1,3.3),(unity_stop,0),(130,0)])
 voltage('Vparkcommand','parkcommand',[(0,3.3),(61.4,3.3),(61.5,0),(stop,0),(stop+.1,3.3),(121.4,3.3),(121.5,0),(unity_stop,0),(unity_stop+.1,3.3),(130,3.3)])
 voltage('Vresetphasecommand','resetphasecommand',[(0,3.3),(59.9,3.3),(60,0),(119,0),(119.1,3.3),(120,3.3),(120.1,0),(130,0)])
 voltage('Vrestorecommand','restorecommand',[(0,0),(68.2,0),(68.3,3.3),(118.3,3.3),(118.4,0),(130,0)])
 lines.append(f'Iinput sum 0 PWL(0 0 9.9u 0 10u {a.input_na*1e-9:g} {shift(60.01):g}u {a.input_na*1e-9:g} {shift(60.02):g}u 0 {final_us:g}u 0)')
 for phase in ['resetphase','restore']:
  lines+=['X'+phase+'preA '+phase+'command '+phase+'preb vdd 0 gf180_phase_inverter','X'+phase+'preB '+phase+'preb '+phase+'pre vdd 0 gf180_phase_inverter','X'+phase+'outP '+phase+'preb '+phase+' vdd 0 gf180_phase_inverter','X'+phase+'outN '+phase+'pre '+phase+'b vdd 0 gf180_phase_inverter']
 lines+=['Xwriteroute linear '+('writeresfeed' if a.omit_current_probe else 'writefeed')+' restore restoreb 0 vdd gf180_fixed_body_tg',f'XwritebackR writeresfeed sum 0 {RCELL}']
 for i in range(1,a.restore_switch_count):lines.append('Xwriteroute'+str(i)+' linear '+('writeresfeed' if a.omit_current_probe else 'writefeed')+' restore restoreb 0 vdd gf180_fixed_body_tg')
 if a.trim_bank_profile:lines=[x for x in lines if not x.startswith('XwritebackR ')]
 if not a.omit_current_probe:lines+=['Vwriteprobe writefeed writeresfeed 0']
 if a.reset_dummy:
  cell='gf180_fixed_body_tg_nf0p5';dq=next((x for x in donor['qualified_layout_components'] if x['cell']==cell),None)
  if dq is None:raise ValueError('Qualified half-size reset dummy missing from donor')
  lines.append('Xresetdummy '+a.reset_dummy_node+' '+a.reset_dummy_node+' resetphaseb resetphase 0 vdd '+cell)
 terms=[f'@c.xintegratorfeedback{i}.x0.c_cap[capacitance]+@c.xintegratorfeedback{i}.c0[capacitance]' for i in range(a.feedback_mim_count)]
 if a.integration_method!='inherited':lines.append(f'.options method={a.integration_method} maxord={a.integration_order}')
 effective_method=re.findall(r'(?mi)^\.options[^\n]*\bmethod=(trap|gear)\b','\n'.join(lines))[-1]
 if a.routed_mim_banks:terms=[f'@c.xfeedbackbank.x{i}.c_cap[capacitance]' for i in range(8)]+['@c.xfeedbackbank.c0[capacitance]']
 lines+=['.control','set numdgt=15','reset',f'tran {a.max_step_ns}n {final_us:g}u','let cf_total=0*v(caplinear)+('+ '+'.join(terms)+')','let stored_charge=(v(caplinear)-v(integratesum))*cf_total','let signed_current=-i(vprobe)','let power_vdd=-v(vdd)*i(vdd)']
 if not a.omit_current_probe:lines+=['let write_current=-i(vwriteprobe)']
 measures={
 'q_initial':('stored_charge',61.2),'q_after_beta':('stored_charge',67.5),'q_after_restore':('stored_charge',118.8),'q_before_unity':('stored_charge',121.2),'q_after_unity':('stored_charge',129.5),'enc_initial':('v(enc)',59.7),'enc_restored':('v(enc)',117.9),'enc_recaptured':('v(enc)',118.8),'write_current_late':('write_current',117.9),'cf_actual':('cf_total',67.5),'supply_voltage':('v(vdd)',117.9)}
 measures.update({'mirror_pre_capture':('signed_current',59.7),'mirror_post_capture':('signed_current',61.2),'mirror_pre_recapture':('signed_current',117.9),'mirror_post_recapture':('signed_current',118.8)})
 if a.omit_current_probe:measures.pop('write_current_late')
 if trim_metadata and trim_metadata['two_ended_isolation']:
  for tag,t in [('initial',59.7),('pre_restore',67.5),('late',117.9),('released',118.8),('final',129.5)]:
   measures['bankout_'+tag]=('v(bankout)',t);measures['common_'+tag]=('v(common)',t)
   if a.buffer_bank_park_reference:measures['bankparkref_'+tag]=('v(bankparkref)',t)
 for tag,t in [('reset_closed',59.7),('reset_released',60.3),('pre_beta',61.2),('second_reset_closed',119.8),('second_reset_released',120.4)]:
  measures['q_'+tag]=('stored_charge',t)
  for node in ['linear','integratesum','common'] :measures[node+'_'+tag]=('v('+node+')',t)
 measures.update({'linear_late':('v(linear)',117.9),'writefeed_late':('v(writeresfeed)',117.9),'sum_late':('v(sum)',117.9),'integratesum_late':('v(integratesum)',117.9)})
 for name,(vector,t) in measures.items():lines.append(f'meas tran {name} find {vector} at={shift(t):g}u')
 if not a.omit_current_probe:lines+=[f'meas tran write_current_mean avg write_current from={shift(100) if a.encode_us==50 else shift(117.7):g}u to={shift(117.9):g}u']
 lines+=[f'meas tran supply_energy integ power_vdd from=0 to={final_us:g}u','quit','.endc','.end']
 trim_tag=('_trim'+str(trim_metadata['externally_selected_code'])+'_'+digest(a.trim_bank_profile)[:10]) if trim_metadata else ''
 probe_tag=('none' if a.omit_current_probe else 'zeroV')+('_resetDummy_'+a.reset_dummy_node if a.reset_dummy else '')
 stem=f'gf180_encoder_writeback_{donor["encoder_settings"]["corner"]}{donor["encoder_settings"]["temp_c"]}_input{a.input_na:g}_step{a.max_step_ns}_probe{probe_tag}_restore{a.restore_switch_count}{trim_tag}_parkBuf{int(a.buffer_bank_park_reference)}_enc{a.encode_us}_cf{a.feedback_mim_count}_bias{a.active_bias_ua}_hold{a.encoder_hold_mim_count}_wave{int(a.dump_waveforms)}_method{a.integration_method}_banks{int(a.routed_mim_banks)}_ord{a.integration_order}_rstR{a.reset_series_resistor_um}_src{sha[:12]}';deck=BASE/'benches'/(stem+'.spice');wavepath=BASE/'results'/(stem+'_wave.dat')
 if a.dump_waveforms:lines[-3:-3]=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+wavepath.relative_to(ROOT).as_posix()+' v(enc) v(sum) v(common) v(drive) signed_current v(linear) v(integratesum) v(encode) v(decode) v(betaroute)']
 deck.write_text('\n'.join(lines)+'\n');snapshot=BASE/'tools/source_snapshots'/f'encoder_writeback_{sha}.py'
 if not snapshot.exists():snapshot.write_bytes(source.read_bytes())
 sources+=[snapshot,deck,md/'design.spice',md/'sm141064.spice',md/'sm141064_mim.spice']
 proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2','--env','NGSPICE_MEAS_PRECISION=15','--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=proc.stdout+proc.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);sources.append(lp);names=list(measures)+(['write_current_mean'] if not a.omit_current_probe else [])+['supply_energy'];v={k:float(x) for k,x in re.findall(r'(?m)^\s*('+'|'.join(names)+r')\s*=\s*([-+0-9.eE]+)',log)}
 if wavepath.exists():sources.append(wavepath)
 complete=proc.returncode==0 and 'ngspice-47 done' in log and len(v)==len(names) and 'tran simulation(s) aborted' not in log
 analysis={}
 if complete:
  q1=-(v['q_after_beta']-v['q_initial'])*1e15;q2=-(v['q_after_unity']-v['q_before_unity'])*1e15
  analysis={'absolute_cf_initial_fc':v['q_initial']*1e15,'absolute_cf_after_beta_fc':v['q_after_beta']*1e15,'absolute_cf_before_unity_fc':v['q_before_unity']*1e15,'physical_writeback_uses_absolute_cf_voltage':True,'first_beta_charge_fc':q1,'first_beta_target_fc':a.input_na*unit_us*beta,'unity_readback_charge_fc':q2,'writeback_preservation_charge_error_fc':q2-q1,'restore_feedback_charge_disturbance_fc':(v['q_after_restore']-v['q_after_beta'])*1e15,'writeback_current_mean_na':v['write_current_mean']*1e9 if 'write_current_mean' in v else None,'ideal_once_beta_current_na':a.input_na*beta,'vdd_energy_nj':v['supply_energy']*1e9}
 report={'simulation_completed':complete,'simulator_returncode':proc.returncode,'settings':vars(a)|{'transient':a.transient.relative_to(ROOT).as_posix(),'resistor_corner':resistor_corner,'trim_bank_profile':a.trim_bank_profile.relative_to(ROOT).as_posix() if a.trim_bank_profile else None},'donor_evidence':a.transient.relative_to(ROOT).as_posix(),'learned_beta_metadata':dict(donor['learned_beta_metadata'],donor_reference_window_us=donor['learned_beta_metadata']['reference_window_us'],reference_window_us=unit_us),'source_snapshot':snapshot.relative_to(ROOT).as_posix(),'measurements':v,'analysis':analysis,'waveform_path':wavepath.relative_to(ROOT).as_posix() if wavepath.exists() else None,'timing_and_capacitance':{'encode_us':a.encode_us,'feedback_mim_count':a.feedback_mim_count,'encoder_extra_hold_mim_count':a.encoder_hold_mim_count,'active_bias_root_ua':a.active_bias_ua,'unit_window_us':unit_us,'diagnostic_duration_us':final_us,'native_rc_scale_relative_to_32_cap_profile':None if a.routed_mim_banks else a.feedback_mim_count/32,'nominal_native_instance_count_ratio':a.feedback_mim_count/32,'ideal_result_rescaling_used':False},'trim_bank_metadata':trim_metadata,'routed_mim_banks':bank_qualified,'reset_series_resistor_components':reset_qualified,'qualified_layout_components':donor['qualified_layout_components']+[q]+trim_qualified+bank_qualified+reset_qualified,'restore_switch_physical_instance_count':a.restore_switch_count,'combined_restore_layout_qualified':False,'writeback_current_probe_scope':'Direct wire; current observation omitted, actual endpoint charge retained' if a.omit_current_probe else 'Zero-volt series current observation', 'numerical_integration_method':effective_method,'numerical_method_agreement_qualified':False,'physical_writeback_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'scope':'Computed CF voltage physically drives encoder SUM through native poly resistor and TG, with original ideal input current zero during restore. Separate physical reset/restore drivers; first pulse applies checkpoint beta once, second unity diagnostic using the same declared unit window reads recaptured state after CF reset. No mathematical inverse, ideal buffered result, fitted current source or gain/offset correction in writeback circuit. Upstream phase commands/root sources still ideal; untrimmed native RC variation, load disturbance, noise/mismatch/retention, weighted events, threshold/subtractive reset/adaptation,5ms service and combined route/chip acceptance remain open. Native model capacitance endpoint measures both CF terminals. Smaller feedback banks remove actual native MIM instances and shorten the beta/unity unit window by the identical count ratio, retaining native resistance and nominal voltage mapping; edge error/noise/dynamic precision must be measured. Optional smaller encoder hold load removes actual7um native MIM instances, not an ideal capacitance reduction; capture/noise/retention/PVT precision remains unqualified. Shorter encode intervals compress only encoding periods, preserving100ns clock ramps and fixed diagnostic read/reset guards, and do not qualify complete PLIF service. Optional trim bank replaces single resistor with qualified native60um base and seven native resistor/TG bypass segments; fixed external code commands drive actual native inverter trees, not an autonomous calibration controller. Optional opposite-phase trim parking connects bankout to existing common reference through four actual TGs while restore is off; it is not an ideal state/current substitute. With buffered parking, a native seven-MOS OTA follower with actual22um Miller and7um load MIM isolates parking current from the original weak common calibration node using existing physical bias mirror with declared root current; this follower topology is not combined-layout/noise/mismatch qualified. Optional restore switch count instantiates parallel copies of the qualified TG with real shared driver loading; combined placement/routing is not qualified.','sha256':{f.relative_to(ROOT).as_posix():digest(f) for f in set(sources)}}
 target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(target),'simulation_completed':complete,'analysis':analysis},indent=2))
 if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
