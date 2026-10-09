"""Audit native writeback metrology and physical re-encoding diagnostics."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 sources={Path(__file__)};cases=[];recoveries=[];restore_groups={}
 for pattern,kind in [('gf180_writeback_resistor_*.json','native_resistor_metrology'),('gf180_encoder_writeback_*.json','physical_writeback_loop')]:
  for path in sorted((BASE/'results').glob(pattern)):
   if path.name=='gf180_encoder_writeback_boundary.json':continue
   r=json.loads(path.read_text());sources.add(path)
   for name,expected in r['sha256'].items():
    f=ROOT/name
    if digest(f)!=expected:raise ValueError('Input provenance mismatch: '+name)
    sources.add(f)
   if r.get('host_reporting_failed'):
    recoveries.append({'evidence':path.relative_to(ROOT).as_posix(),'simulator_returncode_unrecorded':True,'accepted':False,'scope':r['scope']});continue
   snapshot=ROOT/r['source_snapshot'];expected=snapshot.stem.rsplit('_',1)[-1]
   if not re.fullmatch('[a-f0-9]{64}',expected) or digest(snapshot)!=expected:raise ValueError('Executable snapshot mismatch')
   for q in r['qualified_layout_components']:
    if q['magic_drc_count'] or not q['lvs_unique'] or q.get('extraction_feedback',''):raise ValueError('Native qualification differs')
    for name,expected in q['sha256'].items():
     f=BASE/'layout'/q['cell']/name
     if digest(f)!=expected:raise ValueError('Native view mismatch')
     sources.add(f)
   case={'kind':kind,'evidence':path.relative_to(ROOT).as_posix(),'simulation_completed':r['simulation_completed'],'simulator_returncode':r['simulator_returncode'],'settings':r['settings'],'measurements':r['measurements'],'analysis':r.get('analysis',{}),'scope':r['scope']}
   if kind=='physical_writeback_loop':
    if r['learned_beta_metadata']['checkpoint_sha256']!=EXPECTED:raise ValueError('Float checkpoint differs')
    checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
    if digest(checkpoint)!=EXPECTED:raise ValueError('Actual checkpoint differs')
    sources.add(checkpoint)
    deck=next(ROOT/name for name in r['sha256'] if '/benches/' in name and 'encoder_writeback' in name and name.endswith('.spice'));text=deck.read_text()
    required=['Xwriteroute linear '+('writeresfeed' if r['settings'].get('omit_current_probe') else 'writefeed')+' restore restoreb 0 vdd gf180_fixed_body_tg',('Xbase writeresfeed p1 0 gf180_writeback_resistor_60x1' if r.get('trim_bank_metadata') else 'XwritebackR writeresfeed sum 0 gf180_writeback_resistor_123x1'),'Xintegratorreset '+('resetfeed' if r['settings'].get('reset_series_resistor_um',0) else 'linear')+' integratesum resetphase resetphaseb']
    if not all(x in text for x in required):raise ValueError('Physical writeback wiring differs')
    reset_length=r['settings'].get('reset_series_resistor_um',0)
    if reset_length:
     expected_reset=f'Xresetseries linear resetfeed 0 gf180_writeback_resistor_{reset_length}x1'
     if expected_reset not in text or [q['cell'] for q in r['reset_series_resistor_components']]!=[f'gf180_writeback_resistor_{reset_length}x1']:raise ValueError('Native reset resistor topology differs')
    elif re.search(r'(?m)^Xresetseries ',text):raise ValueError('Undeclared reset series device')
    match=re.search(r'(?m)^Iinput sum 0 PWL\(([^\n]+)\)',text)
    tokens=match.group(1).split() if match else [];pairs=list(zip(tokens[::2],tokens[1::2]))
    method=r['settings'].get('integration_method','inherited')
    order=r['settings'].get('integration_order',2)
    if method=='gear' and f'.options method=gear maxord={order}' not in text:raise ValueError('Numerical integration declaration differs')
    if 'integration_order' in r['settings'] and method!='inherited' and f'.options method={method} maxord={order}' not in text:raise ValueError('Explicit numerical method/order declaration differs')
    case['integration_order']=order
    deck_methods=re.findall(r'(?mi)^\.options[^\n]*\bmethod=(trap|gear)\b',text)
    case['requested_integration_method']=method
    case['numerical_integration_method']=deck_methods[-1] if deck_methods else 'trap'
    case['integration_method_label_matches_deck']=method==case['numerical_integration_method']
    enc=r['settings'].get('encode_us',50);expected_end=130-2*(50-enc)
    if pairs[-2:]!=[(f'{10+enc+.02:g}u','0'),(f'{expected_end:g}u','0')]:raise ValueError('Input current must be zero throughout physical restore')
    actual_cf=[x for x in text.splitlines() if re.match(r'Xintegratorfeedback\d+ ',x)];cf_count=r['settings'].get('feedback_mim_count',32)
    routed=r['settings'].get('routed_mim_banks',False)
    if routed:
     if cf_count!=8 or actual_cf or 'Xfeedbackbank caplinear integratesum 0 gf180_mim_bank_22x22_n8' not in text:raise ValueError('Routed feedback bank differs')
     if sorted((q['cell'],q['native_capacitor_instance_count']) for q in r['routed_mim_banks'])!=[('gf180_mim_bank_22x22_n8',8),('gf180_mim_bank_7x7_n9',9)]:raise ValueError('Routed bank native inventory differs')
     for term in [f'@c.xfeedbackbank.x{i}.c_cap[capacitance]' for i in range(8)]+['@c.xfeedbackbank.c0[capacitance]']:
      if term not in text:raise ValueError('Routed native feedback charge metrology differs')
    elif actual_cf!=[f'Xintegratorfeedback{i} caplinear integratesum 0 gf180_mim_22x22' for i in range(cf_count)]:raise ValueError('Actual feedback-bank instance count differs')
    if r['learned_beta_metadata']['reference_window_us']!=4*cf_count/32:raise ValueError('Physical unit window/capacitance scale differs')
    bias=r['settings'].get('active_bias_ua',5)
    if f'Iintegratorbias integratorbias 0 {bias}u' not in text:raise ValueError('Actual shared bias-root current differs')
    held=r['settings'].get('encoder_hold_mim_count',16);actual_hold=[x for x in text.splitlines() if re.match(r'Xcaptureextra\d+ ',x)]
    if routed:
     if held!=8 or actual_hold or 'Xload enc 0 0 gf180_mim_7x7' in text or 'Xencoderholdbank enc 0 0 gf180_mim_bank_7x7_n9' not in text:raise ValueError('Routed encoder hold bank differs')
    elif actual_hold!=[f'Xcaptureextra{i} enc 0 0 gf180_mim_7x7' for i in range(held)]:raise ValueError('Actual encoder hold instances differ')
    case['feedback_bank_count_and_unit_window_audited']=True
    if any(x.startswith(('Vlinear ','Vcaplinear ','Irestore ','Iwriteback ')) for x in text.splitlines()):raise ValueError('Ideal result substitute found')
    if r['settings'].get('reset_dummy') and ('Xresetdummy '+r['settings'].get('reset_dummy_node','linear')+' '+r['settings'].get('reset_dummy_node','linear')+' resetphaseb resetphase 0 vdd gf180_fixed_body_tg_nf0p5') not in text:raise ValueError('Reset dummy wiring differs')
    expected_routes=['Xwriteroute'+(str(i) if i else '')+' linear '+('writeresfeed' if r['settings'].get('omit_current_probe') else 'writefeed')+' restore restoreb 0 vdd gf180_fixed_body_tg' for i in range(r['settings'].get('restore_switch_count',1))]
    actual_routes=[x for x in text.splitlines() if x.startswith('Xwriteroute')]
    if actual_routes!=expected_routes:raise ValueError('Parallel restore switch count/wiring differs')
    case['restore_switch_physical_instance_count']=len(actual_routes)
    circuit_without_routes='\n'.join(x for x in text.splitlines() if not x.startswith('Xwriteroute'))
    signature=hashlib.sha256(circuit_without_routes.encode()).hexdigest()
    case['bench_without_restore_switch_instances_sha256']=signature
    if r['simulation_completed']:restore_groups.setdefault(signature,[]).append(case)
    top=text.rsplit('.ends',1)[-1].split('.control')[0];instance_names=[x.split()[0].lower() for x in top.splitlines() if x.startswith('X')];duplicates=sorted({n for n in instance_names if instance_names.count(n)>1})
    case['duplicate_top_level_instance_names']=duplicates
    if r['simulation_completed'] and duplicates:raise ValueError('Completed bench has duplicate instances')
    case['physical_result_path_and_zero_external_restore_input_audited']=not duplicates;case['beta_applied_once_then_unity_readback_diagnostic']=True
    if r.get('trim_bank_metadata'):
     t=r['trim_bank_metadata'];profile=json.loads((ROOT/t['profile']).read_text());code=t['externally_selected_code']
     if code!=profile['analysis']['best_external_dc_code']['externally_selected_code'] or r['settings']['resistor_corner']!=profile['settings']['resistor_corner']:raise ValueError('External trim selection differs')
     for i,length in enumerate([2,4,8,16,32,64,128]):
      start=f'p{i+1}';end=('bankout' if t.get('two_ended_isolation') else 'sum') if i==6 else f'p{i+2}'
      if f'Xsegment{i} {start} {end} 0 gf180_writeback_resistor_{length}x1' not in text:raise ValueError('Native trim segment differs')
      for j in range(4):
       if f'Xbypass{i}_{j} {start} {end} bit{i} bit{i}b 0 vdd gf180_fixed_body_tg' not in text:raise ValueError('Native bypass differs')
      value='0' if code&(1<<i) else '3.3'
      if f'Vbit{i}command bit{i}command 0 {value}' not in text:raise ValueError('External trim command differs')
      for line in [f'Xbit{i}preA bit{i}command bit{i}preb vdd 0 gf180_phase_inverter',f'Xbit{i}preB bit{i}preb bit{i}pre vdd 0 gf180_phase_inverter',f'Xbit{i}outP bit{i}preb bit{i} vdd 0 gf180_phase_inverter',f'Xbit{i}outN bit{i}pre bit{i}b vdd 0 gf180_phase_inverter']:
       if line not in text:raise ValueError('Native trim driver differs')
     if t.get('two_ended_isolation'):
      for j in range(4):
       if f'Xrestoreout{j} bankout sum restore restoreb 0 vdd gf180_fixed_body_tg' not in text:raise ValueError('Output isolation differs')
     if t.get('park_bank'):
      for j in range(4):
       if ('Xbankpark'+str(j)+' bankout '+('bankparkref' if t.get('park_reference_buffered') else 'common')+' restoreb restore 0 vdd gf180_fixed_body_tg') not in text:raise ValueError('Physical reference parking differs')
     if t.get('park_reference_buffered'):
      for line in ['Xbankparkrefbuffer common bankparkref bankparkref vdd 0 integratorbias bankparkrefcmp gf180_shared_ota_core_pmos_input','Xbankparkrefcomp bankparkrefcmp bankparkref 0 gf180_mim_22x22','Xbankparkrefload bankparkref 0 0 gf180_mim_7x7']:
       if line not in text:raise ValueError('Physical park reference buffer differs')
     case['trim_bank_native_topology_and_external_code_audited']=not duplicates;case['autonomous_calibration_controller_implemented']=False
    if r['simulation_completed']:
     m=r['measurements'];case['absolute_cf_initial_fc']=m['q_initial']*1e15;case['absolute_cf_after_beta_fc']=m['q_after_beta']*1e15;case['absolute_cf_before_unity_fc']=m['q_before_unity']*1e15
     a=r['analysis'];case['first_beta_charge_error_fc']=a['first_beta_charge_fc']-a['first_beta_target_fc'];case['readback_relative_to_first_charge_error_percent']=100*a['writeback_preservation_charge_error_fc']/a['first_beta_charge_fc'] if abs(a['first_beta_charge_fc'])>1 else None
   cases.append(case)
 ip=BASE/'results/gf180_component_lef_import.json';imp=json.loads(ip.read_text())
 for name,expected in imp['sha256'].items():
  f=ROOT/name
  if digest(f)!=expected:raise ValueError('Router input mismatch')
  sources.add(f)
 sources.add(ip)
 comparisons=[]
 for signature,group in restore_groups.items():
  baseline=[x for x in group if x['restore_switch_physical_instance_count']==1]
  if len(baseline)!=1:continue
  b=baseline[0]
  for c in group:
   if c['restore_switch_physical_instance_count']==1:continue
   comparisons.append({'baseline_evidence':b['evidence'],'candidate_evidence':c['evidence'],'identical_bench_except_restore_switch_instances':True,'bench_without_restore_switch_instances_sha256':signature,'baseline_switch_count':1,'candidate_switch_count':c['restore_switch_physical_instance_count'],'input_na':c['settings']['input_na'],'baseline_preservation_error_fc':b['analysis']['writeback_preservation_charge_error_fc'],'candidate_preservation_error_fc':c['analysis']['writeback_preservation_charge_error_fc'],'baseline_preservation_error_percent':b['readback_relative_to_first_charge_error_percent'],'candidate_preservation_error_percent':c['readback_relative_to_first_charge_error_percent'],'combined_layout_or_precision_accepted':False})
 result={'restore_parallel_matched_comparisons':comparisons,'cases':cases,'case_count':len(cases),'simulations_completed':sum(x['simulation_completed'] for x in cases),'reporting_failure_recoveries':recoveries,'physical_and_source_provenance_verified':True,'router_import_verified':imp['router_import_verified'],'physical_writeback_accepted':False,'original_float_accuracy_accepted':False,'full_chip_accepted':False,'scope':'Native resistor metrology and actual CF-result-to-encoder-to-unity-readback diagnostic. Narrow completion/provenance does not qualify RC calibration, noise/mismatch/retention, exact PLIF/weight events or original-float accuracy/5ms population service/combined full-chip layout. Reporting recovery with unrecorded process status is retained separately.','sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
 target=BASE/'results/gf180_encoder_writeback_boundary.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'report':str(target),'case_count':len(cases),'simulations_completed':result['simulations_completed'],'reporting_recoveries':len(recoveries)}))
if __name__=='__main__':main()
