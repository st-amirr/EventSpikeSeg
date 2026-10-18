"""Bounded per-physical-instance terminal power characterization; no layout edits."""
from pathlib import Path
import re,json,hashlib,array,sys,bisect,subprocess,time,argparse,concurrent.futures
R=Path(__file__).resolve().parents[1]; B=R/'artifacts/analog_asic'; O=B/'results/module_consumption_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(R).as_posix()
def unfold(s):return re.sub(r'\n\+\s*',' ',s)
def scalar(s):
 m=re.fullmatch(r'([\d.eE+-]+)([a-z]*)',s.lower());return float(m[1])*{'':1,'s':1,'u':1e-6,'n':1e-9,'m':1e-3,'p':1e-12}.get(m[2],1)
def spec(tag,deck,targets,windows,source_report=None):return dict(tag=tag,deck=deck,targets=targets,windows=windows,source_report=source_report)
def jobs():
 b='artifacts/analog_asic/benches/';r='artifacts/analog_asic/results/'
 return [
 spec('page_frontend','artifacts/analog_asic/benches/gf180_page1024_read_frontend_partition_v1_native_A_B_A.spice',['Xpage'],[['three_page_column_accesses',0,40e-6],['idle_after_access',38e-6,40e-6]],'artifacts/analog_asic/results/gf180_page1024_read_frontend_partition_v1_native_A_B_A.json'),
 spec('bias_reference','artifacts/analog_asic/results/module_consumption_v1/bias_reference_source.spice',['Xreference'],[['settled_bias',1e-6,5e-6]],None),
 spec('square_kernel','artifacts/analog_asic/benches/gf180_energy_square_kernel_v1_nominal_src32ecefba0069.spice',['Xkernel'],[['three_input_levels',0,20e-6],['positive_plateau',11e-6,14e-6]],'artifacts/analog_asic/results/gf180_energy_square_kernel_v1_nominal_src32ecefba0069.json'),
 spec('membrane_cell','artifacts/analog_asic/results/module_consumption_v1/membrane_source.spice',['Xcell','Xbare'],[['write',.9e-6,2.1e-6],['read',2.8e-6,4.2e-6],['five_ms_hold',5e-6,5.005e-3]],None),
 spec('plif_core',b+'gf180_five_module_parent_nominal_srcf6f1e759f510.spice',['Xparent_high'],[['beta',1019e-6,1022e-6],['decision_and_reset',1041.5e-6,1049.5e-6],['one_initialized_update',1005e-6,1050e-6],['five_ms_hold',1050e-6,6050e-6]],r+'gf180_five_module_parent_nominal_srcf6f1e759f510.json'),
 spec('signed_injector',b+'gf180_signed_injection_module_standalone_srce24e654834c4.spice',['Xinject_positive','Xinject_negative','Xinject_idle'],[['pulse_and_recovery',1043.5e-6,1049.5e-6],['five_ms_hold',1049.5e-6,6049.5e-6]],r+'gf180_signed_injection_module_standalone_srce24e654834c4.json'),
 spec('sampled_decision',b+'gf180_sampled_decision_module_standalone_src85a19781eca9.spice',['Xdecision_high','Xdecision_low'],[['complete_trace',None,None]],r+'gf180_sampled_decision_module_standalone_src85a19781eca9.json'),
 spec('control_gates',r+'native_control_gates_v1/bench.spice',['Xinv_10fF','Xand_10fF','Xinv_100fF','Xand_100fF'],[['four_truth_states',0,80e-9],['settled_last_state',70e-9,79e-9]],r+'native_control_gates_v1/simulation.json'),
 spec('transfer_gate',r+'native_transfer_gate_v1/bench.spice',['Xfwd','Xrev'],[['two_level_transfers_and_release',0,100e-9],['off_hold',1e-6,5.001e-3]],r+'native_transfer_gate_v1/simulation.json'),
 spec('weight_duration',b+'gf180_guarded_weight_duration_parent_v2_nominal_srcd7548dd3da7a.spice',['Xduration_small','Xduration_middle','Xduration_large'],[['armed_pulse_cycle',1039e-6,1241e-6],['parked',1250e-6,1280e-6]],r+'gf180_guarded_weight_duration_parent_v2_nominal_srcd7548dd3da7a.json'),
 spec('inhibition',b+'gf180_peer_inhibition_nominal_src2426fa2c47a3.spice',['Xinhibit_peer','Xinhibit_no_trigger','Xinhibit_own_spiker'],[['complete_trace',None,None],['five_ms_hold',1050e-6,6050e-6]],r+'gf180_peer_inhibition_nominal_src2426fa2c47a3.json'),
 spec('affine_subtractor',b+'gf180_candidate_penalty_subtractor_v2_nominal_src7374290a03d3.spice',['Xsubtract'],[['input_sequence',0,30e-6],['late_settled',28e-6,30e-6]],r+'gf180_candidate_penalty_subtractor_v2_nominal_src7374290a03d3.json'),
 spec('resident_adaptation',b+'gf180_resident_adaptation_expiry_v3_fullcap_nominal_src98bffbb7a8dd.spice',['Xresident'],[['five_age_advances_two_spikes',0,200e-6],['late_settled',190e-6,200e-6]],r+'gf180_resident_adaptation_expiry_v3_fullcap_nominal_src98bffbb7a8dd.json'),
 spec('adaptation_io',b+'gf180_adaptation_shared_state_io_v6_native_restore_capture.spice',['Xio'],[['restore_capture_sequence',0,110e-6],['late_settled',100e-6,110e-6]],r+'gf180_adaptation_shared_state_io_v6_native_restore_capture.json'),
 spec('class_current_io',b+'gf180_class_current_shared_io_v1_native_readout_restore_capture_v2.spice',['Xio'],[['restore_capture_sequence',0,180e-6],['late_settled',170e-6,180e-6]],r+'gf180_class_current_shared_io_v1_native_readout_restore_capture_v2.json'),
 spec('six_class_readout',b+'gf180_six_class_readout_v3_all_negative_srcc4946d39869d.spice',['Xbank_all_negative'],[['ten_accumulations_and_readout',0,51200e-6],['readout_evaluation',51000e-6,51100e-6],['parked_after_readout',51120e-6,51200e-6]],r+'gf180_six_class_readout_v3_all_negative_srcc4946d39869d.json'),
 spec('event_sequencer',b+'gf180_event_phase_sequencer_native_drivers_src8bbb745a6c8c.spice',['Xseq_one_event_busy_request','Xseq_idle'],[['one_request_cycle',0,8e-6]],r+'gf180_event_phase_sequencer_native_drivers_src8bbb745a6c8c.json'),
 spec('bin_sequencer',b+'gf180_bin_commit_controller_v2_case1_src02cbd1a6b373.spice',['Xseq_wait_then_complete'],[['one_bin_phase_sequence',0,14e-6]],r+'gf180_bin_commit_controller_v2_case1_src02cbd1a6b373.json'),
 ]
def prepare(job):
 src=R/job['deck'];s=src.read_text();jpath=R/job['source_report'] if job.get('source_report') else None
 if jpath:
  j=json.loads(jpath.read_text());recorded=j.get('sha256',{}).get(rel(src));assert recorded and recorded==sha(src),str(src)
 # Keep every native device, parasitic and input fixture. Only add zero-V meters,
 # enable KLU, and replace output-writing commands with a dedicated raw trace.
 s=unfold(s); definitions={}
 for m in re.finditer(r'(?mi)^\.subckt\s+(\S+)\s+(.+)$',s):definitions[m[1].lower()]=m[2].split()
 analysis=re.search(r'(?mi)^\.?tran\s+(.+)$',s);assert analysis,job['tag'];tran=analysis[1];horizon=scalar(tran.split()[1]);job['expected_horizon_s']=horizon
 s=re.sub(r'(?mis)^\.control\s*\n.*?^\.endc\s*\n','',s);s=re.sub(r'(?mi)^\.(save|tran|end)\b.*\n?','',s)
 s=re.sub(r'(?mi)^(\.options)(?![^\n]*\bklu\b)',r'\1 klu',s)
 level=0; metas=[]; found=set(); lines=[]
 for l in s.splitlines():
  if l.lower().startswith('.subckt'):level+=1
  if l.lower().startswith('.ends'):level-=1
  a=l.split()
  if level==0 and a and a[0].lower() in {x.lower() for x in job['targets']}:
   inst=a[0];cell=a[-1];ports=definitions[cell.lower()];nodes=a[1:-1];assert len(ports)==len(nodes),(inst,len(ports),len(nodes));mi=len(metas);new=[];meters=[]
   for pi,(port,node) in enumerate(zip(ports,nodes)):
    inner=f'pm_{mi}_{pi}';meter=f'Vpm_{mi}_{pi}'
    if node.lower() in ['0','gnd','vss']:new.append(node);meters.append({'port':port,'external_node':node,'meter':None});continue
    new.append(inner);lines.extend([f'{meter} {node} {inner}_meter 0',f'Rpm_{mi}_{pi} {inner}_meter {inner} .1']);meters.append({'port':port,'external_node':node,'meter':meter,'internal_node':inner})
   lines.append(' '.join([inst,*new,cell]));metas.append({'instance':inst,'cell':cell,'ports':meters});found.add(inst.lower())
  else:lines.append(l)
 assert found=={x.lower() for x in job['targets']},(job['tag'],found,job['targets'])
 saves=[]
 for m in metas:
  for p in m['ports']:
   if p['external_node'].lower() not in ['0','gnd']:saves.append('v('+p['external_node']+')')
   if p['meter']:saves.extend(['i('+p['meter']+')','v('+p['internal_node']+')'])
 icmap={p['external_node'].lower():p['internal_node'] for m in metas for p in m['ports'] if p.get('internal_node')}
 lines=[re.sub(r'v\(([^)]+)\)',lambda mm:'v('+icmap.get(mm[1].lower(),mm[1])+')',line,flags=re.I) if line.lower().startswith('.ic') else line for line in lines]
 saves=list(dict.fromkeys(saves));lines+=['.save '+' '.join(saves),'.tran '+tran,'.end']
 d=O/job['tag'];d.mkdir(exist_ok=False);deck=d/'bench.spice';deck.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n');job.update(instances=metas,source_deck_sha256=sha(src),source_report_sha256=sha(jpath) if jpath else None,measurement_deck=rel(deck));return job
class Trace:
 def __init__(self,path):
  h,b=path.read_bytes().split(b'Binary:\n',1);self.nv=int(re.search(rb'No. Variables:\s*(\d+)',h)[1]);self.names=[l.split()[1].lower() for l in h.decode().split('Variables:\n')[1].splitlines() if l.strip()];self.v=array.array('d');self.v.frombytes(b[:len(b)//(self.nv*8)*(self.nv*8)])
  if sys.byteorder!='little':self.v.byteswap()
  self.t=list(self.v[0::self.nv]);assert self.t and all(math_isfinite(x) for x in self.v)
 def col(self,n):return list(self.v[self.names.index(n.lower())::self.nv])
def math_isfinite(x):return x==x and abs(x)!=float('inf')
def integral(t,y,a,b,positive=False):
 assert t[0]-1e-12<=a<b<=t[-1]+1e-12,(a,b,t[-1])
 def at(x):
  k=bisect.bisect_left(t,x)
  if k==0:return y[0]
  if k==len(t):return y[-1]
  return y[k-1]+(y[k]-y[k-1])*(x-t[k-1])/(t[k]-t[k-1])
 ids=range(bisect.bisect_right(t,a),bisect.bisect_left(t,b));xs=[a]+[t[k] for k in ids]+[b];ys=[at(a)]+[y[k] for k in ids]+[at(b)];s=0
 for u,v,p,q in zip(xs,xs[1:],ys,ys[1:]):
  if not positive:s+=(v-u)*(p+q)/2
  elif p>=0 and q>=0:s+=(v-u)*(p+q)/2
  elif p>0:s+=(v-u)*p*p/(2*(p-q))
  elif q>0:s+=(v-u)*q*q/(2*(q-p))
 return s

def summarize(job,run,elapsed):
 d=O/job['tag'];raw=d/'waveforms.raw';report={'completed':False,'returncode':run.returncode,'elapsed_wall_s':elapsed,'supply_V':3.3,'temperature_C':27,'corner':'typical','job':job,'scope':'Per-instance terminal-port native SPICE measurement. Native circuit/input fixtures unchanged; zero-V boundary current meters with0.1ohm series stabilization added, KLU enabled. Power is measured at the circuit side, excluding meter resistance losses; max observed inserted voltage drop is recorded per port. Drivers and shared references remain outside the measured module. VDD energy is reported separately from signed net terminal energy and positive energy imports. Net terminal energy includes change in stored energy and is not always dissipation. No full-chip power or calibrated functional precision claim.','instances':[]}
 if raw.exists() and b'Binary:\n' in raw.read_bytes():
  w=Trace(raw);report['last_time_s']=w.t[-1];report['points']=len(w.t);report['completed']=run.returncode==0 and abs(w.t[-1]-job['expected_horizon_s'])<1e-12 and 'aborted' not in (run.stdout+run.stderr).lower()
  if report['completed']:
   for m in job['instances']:
    ports=[];supply=[0.0]*len(w.t);total=[0.0]*len(w.t)
    for p in m['ports']:
     volt=[0.0]*len(w.t) if not p['meter'] else w.col('v('+p['internal_node']+')');current=w.col('i('+p['meter']+')') if p['meter'] else [0.0]*len(w.t);power=[v*i for v,i in zip(volt,current)];p['max_meter_series_drop_V']=.1*max(abs(i) for i in current);ports.append((p,power));total=[a+b for a,b in zip(total,power)]
     if p['port'].lower() in ['vdd','vcc']:supply=[a+b for a,b in zip(supply,power)]
    entry={'instance':m['instance'],'cell':m['cell'],'windows':[]}
    for name,a,b in job['windows']:
     if a is None:a=w.t[0]
     if b is None:b=w.t[-1]
     if a<w.t[0]:a=w.t[0]
     duration=b-a;pe=[dict(port=p['port'],external_node=p['external_node'],max_meter_series_drop_V=p.get('max_meter_series_drop_V',0),signed_net_energy_J=integral(w.t,power,a,b),positive_import_energy_J=integral(w.t,power,a,b,True)) for p,power in ports]
     entry['windows'].append({'name':name,'start_s':a,'end_s':b,'duration_s':duration,'VDD_energy_J':integral(w.t,supply,a,b),'VDD_mean_power_W':integral(w.t,supply,a,b)/duration,'net_terminal_energy_J':integral(w.t,total,a,b),'net_terminal_mean_power_W':integral(w.t,total,a,b)/duration,'positive_terminal_import_energy_J':sum(p['positive_import_energy_J'] for p in pe),'ports':pe})
    report['instances'].append(entry)
 report['sha256']={rel(p):sha(p) for p in [R/job['measurement_deck'],d/'ngspice.log',raw] if p.exists()};(d/'consumption.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return {'tag':job['tag'],'completed':report['completed'],'seconds':round(elapsed,2),'returncode':run.returncode,'last_time_s':report.get('last_time_s'),'rows':len(report['instances'])}
def run_job(job):
 job=prepare(job);d=O/job['tag'];started=time.monotonic()
 try:run=subprocess.run(['docker','run','--rm','--network','none','--memory','1g','--cpus','1','--volume',str(R)+':/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','180','ngspice','-b','-r','/workspace/'+rel(d/'waveforms.raw'),'/workspace/'+job['measurement_deck']],capture_output=True,text=True,timeout=195)
 except subprocess.TimeoutExpired as e:run=subprocess.CompletedProcess([],124,(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else e.stdout or '',(e.stderr or b'').decode() if isinstance(e.stderr,bytes) else e.stderr or '')
 (d/'ngspice.log').write_text(run.stdout+run.stderr,encoding='utf-8');return summarize(job,run,time.monotonic()-started)
def main():
 p=argparse.ArgumentParser();p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=1);p.add_argument('--suffix',default='');args=p.parse_args();selected=[j for j in jobs() if args.only is None or j['tag'] in args.only]
 for j in selected:j['tag']+=args.suffix
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
  futures={ex.submit(run_job,j):j for j in selected}
  for f in concurrent.futures.as_completed(futures):
   try:print(json.dumps(f.result()),flush=True)
   except Exception as e:print(json.dumps({'tag':futures[f]['tag'],'error':str(e)}),flush=True)
if __name__=='__main__':main()
