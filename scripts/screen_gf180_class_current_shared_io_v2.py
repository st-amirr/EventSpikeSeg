"""Native class-score restore, output multiplexing and analog row capture.

One bounded A-B-A interface case. Forest RECOV boundary fixture is explicit;
this does not qualify whole-frame throughput or the trained final synapses.
"""
from pathlib import Path
import hashlib,json,re,subprocess,time,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 io='gf180_class_current_shared_io_v1';resident='gf180_six_class_readout_v3';inv='gf180_dense_inverter_v1';rp=B/'results'/f'{io}_native_readout_restore_capture_v2.json';assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(rp.stem+'.spice');texts=[];ports={};inputs=[Path(__file__)]
 for c in (io,resident,inv):
  d=B/'layout'/c;qf=d/'qualification.json';q=json.loads(qf.read_text());assert q['magic_drc_count']==0 and (q['lvs_unique'] or q.get('independent_connectivity_accepted'));inputs.append(qf)
  if c!=inv:
   fqf=d/'flat_cap_full_qualification.json';fq=json.loads(fqf.read_text());assert fq['all_flat_extraction_node_ground_caps_verified'];p=d/(fq['flat_subcircuit']+'_fullcap.spice');assert sha(p)==fq['sha256'][p.relative_to(R).as_posix()];txt=p.read_text().replace(fq['flat_subcircuit'],c);inputs.append(fqf)
  else:p=d/(c+'_cap.spice');txt=p.read_text()
  ports[c]=re.search(r'(?m)^\.subckt\s+'+c+r'\s+([^\n]+)',txt.replace('\n+',' '))[1].split();assert set(ports[c])==set(q['ports']);texts.append(txt);inputs.append(p)
 pre='/workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice';lines=['Native class current shared restore/capture',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options klu method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18']+texts+['.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vresetref VRESET 0 1.65','Vstore STORAGE_REFERENCE 0 1.2','Vcomp COMPUTE_REFERENCE 0 1.65','Istate STATE_BIAS 0 6u','Iselect SELECT_BIAS 0 1u','Iup UP_BIAS 0 2u','Idown DOWN_BIAS 0 2u','Iio IO_BIAS 0 16u','Vrec RECOV_SRC 0 PWL(0 1.18 65u 1.18 65.01u 1.23 115u 1.23 115.01u 1.18 180u 1.18)','Rrec RECOV_SRC RECOV 100']
 def inst(tag,c,mapping):lines.append('X'+tag+' '+' '.join(mapping.get(p,p) for p in ports[c])+' '+c)
 def ctrl(n,windows,initial=False):
  pts=[(0,3.3 if initial else 0)]
  for a,b in windows:
   if a>0:pts.extend([(a-.01,0),(a,3.3)])
   pts.extend([(b-.01,3.3),(b,0)])
  pts.append((180,0));lines.append(f'V{n} {n}_drv 0 PWL('+' '.join(f'{t}u {v}' for t,v in pts)+')');inst('b'+n,inv,{'IN':n+'_drv','OUT':n+'B'});inst('d'+n,inv,{'IN':n+'B','OUT':n})
 ctrl('RESET',[(0,10)],True);ctrl('RESTORE0',[(20,40),(120,140)]);ctrl('RESTORE1',[(70,90)]);ctrl('SELECT0',[(0,65),(110.01,179.99)],True);ctrl('SELECT1',[(65.01,110)]);ctrl('CAP0',[(55,60)]);ctrl('CAP1',[(105,110)]);ctrl('CAP2',[(155,160)])
 mapping={}
 for kind in ('RESTORE','SELECT'):
  for k in range(2,6):mapping[f'{kind}{k}']='VSS';mapping[f'{kind}{k}B']='VDD'
 for k in range(3,8):mapping[f'CAP{k}']='VSS';mapping[f'CAP{k}B']='VDD'
 for k in range(8):lines.append(f'Cload{k} DATA{k} VSS 100f')
 inst('readout',resident,{'EVAL':'VSS','SAMPLE':'VSS'});inst('io',io,mapping)
 names=['RECOV','RESET']+[f'STATE{k}' for k in range(6)]+[f'OUTPUT{k}' for k in range(6)]+[f'DATA{k}' for k in range(3)];lines+=['.save '+' '.join('v('+n+')' for n in names)+' i(Vdd)','.tran .05u 180u 0 .5u','.end'];deck.write_text('\n'.join(lines)+'\n');started=time.monotonic();run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);lp=rp.with_suffix('.log');log=run.stdout+run.stderr;lp.write_text(log);o={'module_simulation_completed':False,'native_IO_MOS':120,'native_IO_MIM':48,'native_IO_R':8,'native_readout_MOS':458,'native_readout_MIM':30,'returncode':run.returncode,'wall_s':time.monotonic()-started,'physical_initialization_without_IC_UIC':True,'full_chip_complete':False,'full_population_5ms_accepted':False,'scope':'Complete native flat C IO plus existing six-class readout. Physical RESET and three A-B-A restore windows onto two distinct class working caps; native OUTPUT onehot TG mux, shared physical downshift and three analog row hold slots. Other four classes/other five holds remain present. Frozen RECOV 1.18/1.23V through100ohm,100fF DATA fixtures. No state IC/UIC,ideal numeric internal drive or trained final synapses. EVAL/SAMPLE inactive; existing independent50ms winner cases retained. Forest loading, full eight-slot row, full-frame sequencing and accuracy/5ms unqualified.'}
 if raw.exists() and b'Binary:\n' in raw.read_bytes():
  header,data=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',header)[1]);vv=[l.split()[1] for l in header.decode().split('Variables:\n')[1].splitlines() if l.strip()];arr=np.frombuffer(data[:len(data)//(nv*8)*(nv*8)],dtype='<f8').reshape(-1,nv);t=arr[:,0];np.savez_compressed(rp.with_suffix('.npz'),waveforms=arr,variables=np.array(vv));o['last_time_s']=float(t[-1]);o['module_simulation_completed']=bool(run.returncode==0 and abs(t[-1]-180e-6)<1e-12 and np.isfinite(arr).all() and 'aborted' not in log.lower())
  if o['module_simulation_completed']:
   at=lambda n,u:float(np.interp(u*1e-6,t,arr[:,vv.index('v('+n.lower()+')')]));cases=[]
   for tag,ch,us,slot,target in [('A_first',0,59,0,1.18),('B',1,109,1,1.23),('A_return',0,159,2,1.18)]:
    state=at(f'STATE{ch}',us);out=at(f'OUTPUT{ch}',us);held=at(f'DATA{slot}',us);cases.append({'case':tag,'channel':ch,'sample_us':us,'storage_target_v':target,'state_v':state,'output_v':out,'held_storage_v':held,'post_release_restore_error_v':state-(target+.45),'buffer_error_v':out-state,'downshift_and_capture_error_v':held-(out-.45),'total_roundtrip_error_v':held-target})
   o.update(cases=cases,max_post_release_restore_error_v=max(abs(c['post_release_restore_error_v']) for c in cases),max_total_roundtrip_error_v=max(abs(c['total_roundtrip_error_v']) for c in cases),slot0_hold_change_v=at('DATA0',179)-at('DATA0',64),unselected_class_final_change_v={str(k):at(f'STATE{k}',179)-at(f'STATE{k}',19) for k in range(2,6)})
 o['sha256']={p.relative_to(R).as_posix():sha(p) for p in inputs+[deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
