"""Bounded native restore/capture A-B-A with existing resident adaptation.

No IC/UIC. Recovery boundary voltages frozen from the prior completed resident run.
The forest itself and long atlas wires are outside this module case.
"""
from pathlib import Path
import hashlib,json,re,subprocess,time,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 io='gf180_adaptation_shared_state_io_v1';resident='gf180_resident_adaptation_expiry_v3';inv='gf180_dense_inverter_v1';stem='gf180_adaptation_shared_state_io_v1_native_restore_capture';rp=B/'results'/(stem+'.json');assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(stem+'.spice');texts=[];ports={};inputs=[Path(__file__)]
 for c in (io,resident,inv):
  d=B/'layout'/c;qf=d/'qualification.json';q=json.loads(qf.read_text());assert q['magic_drc_count']==0 and (q['lvs_unique'] or q.get('independent_connectivity_accepted'));inputs.append(qf)
  if c!=inv:
   fqf=d/'flat_cap_full_qualification.json';fq=json.loads(fqf.read_text());assert fq['all_flat_extraction_node_ground_caps_verified'];p=d/(fq['flat_subcircuit']+'_fullcap.spice');assert sha(p)==fq['sha256'][p.relative_to(R).as_posix()];txt=p.read_text().replace(fq['flat_subcircuit'],c);inputs.append(fqf)
  else:p=d/(c+'_cap.spice');txt=p.read_text()
  ports[c]=re.search(r'(?m)^\.subckt\s+'+c+r'\s+([^\n]+)',txt.replace('\n+',' '))[1].split();assert set(ports[c])==set(q['ports']);texts.append(txt);inputs.append(p)
 donor=B/'results/gf180_resident_adaptation_expiry_v3_fullcap_nominal_src98bffbb7a8dd.json';d=json.loads(donor.read_text());assert d['module_simulation_completed'];samples=d['cases'][0]['samples_v'];aa=samples['55.0'];bb=samples['9.0'];inputs.append(donor);pre='/workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice';lines=['Nativeadaptation sharedstate restore/capture',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options klu method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18']+texts+['.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vreset VRESET 0 1.2','Vpark PARK 0 1.2','Vprogram PPROGRAM 0 2.6','Vcas PCAS 0 2.2','Vpeak VPEAK 0 1.21','Vinactive VINACTIVE 0 1.35','Vexpire VEXPIRE 0 1.22','Vbase VBASE 0 .9','Vcom VCOM 0 1.65','Vampdata AMP_DATA 0 1.5','Iresident BIAS 0 5u','Iio IO_BIAS 0 34u']
 def inst(tag,c,mapping):lines.append('X'+tag+' '+' '.join(mapping.get(p,p) for p in ports[c])+' '+c)
 def ctrl(n,windows,initial=False):
  pts=[(0,3.3 if initial else 0)]
  for a,b in windows:
   if a>0:pts.extend([(a-.01,0),(a,3.3)])
   pts.extend([(b-.01,3.3),(b,0)])
  pts.append((110,0));lines.append(f'V{n} {n}_drv 0 PWL('+' '.join(f'{t}u {v}' for t,v in pts)+')');inst('b'+n,inv,{'IN':n+'_drv','OUT':n+'B'});inst('d'+n,inv,{'IN':n+'B','OUT':n})
 ctrl('INIT',[(0,5)],True);ctrl('SPIKE',[]);ctrl('ADVANCE',[]);ctrl('RESTORE',[(15,25),(50,60),(85,95)]);ctrl('CAP0',[(35,40)]);ctrl('CAP1',[(70,75)])
 for kind,key in [('AGE','age_v'),('AMP','amplitude_v')]:
  av=aa[key];bv=bb[key];lines.extend([f'V{kind}rec {kind}_RECOV_src 0 PWL(0 {av:.16g} 45u {av:.16g} 45.01u {bv:.16g} 80u {bv:.16g} 80.01u {av:.16g} 110u {av:.16g})',f'R{kind}rec {kind}_RECOV_src {kind}_RECOV 100'])
 mapping={'AMP_BUFFERED':'AMP_BUF','AGE_RESTORE':'RESTORE','AMP_RESTORE':'RESTORE','AGE_RESTOREB':'RESTOREB','AMP_RESTOREB':'RESTOREB'}
 for kind in ('AGE','AMP'):
  for k in range(8):
   mapping[f'{kind}_CAP{k}']=f'CAP{k}' if k<2 else 'VSS';mapping[f'{kind}_CAP{k}B']=f'CAP{k}B' if k<2 else 'VDD'
   lines.append(f'Cload_{kind}{k} {kind}_DATA{k} VSS 100f')
 inst('resident',resident,{});inst('io',io,mapping);names=['AGE','AMPLITUDE','AMP_BUF','ACTIVE','EXPIRED','RESTORE','INIT','AGE_RECOV','AMP_RECOV']+[f'{kind}_DATA{k}' for kind in ('AGE','AMP') for k in range(2)];lines+=['.save '+' '.join('v('+n+')' for n in names)+' i(Vdd)','.tran .02u 110u 0 .2u','.end'];deck.write_text('\n'.join(lines)+'\n');started=time.monotonic();run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);lp=rp.with_suffix('.log');log=run.stdout+run.stderr;lp.write_text(log);o={'module_simulation_completed':False,'native_IO_MOS':172,'native_IO_MIM':84,'native_resident_MOS':131,'native_resident_R':48,'native_resident_MIM':34,'returncode':run.returncode,'wall_s':time.monotonic()-started,'physical_initialization_without_IC_UIC':True,'full_chip_complete':False,'full_population_5ms_accepted':False,'scope':'ActualnativeIO+residentcompleteflatC. INITphysicalTG initialization,threeA-B-Arestorewindows,twoindependentrowcapture slots. Frozenpriorresidentvoltages through100ohmRECOVboundaryfixtures;100fFDATAloads. All16holdbuffers physicallypresent,first2slotscaptured. NoidealAGE/AMPLITUDE/state drive,IC/UIC,digitalnumericalstate or fittedcalibration. Noactualforest/readers/longatlasRC,trainedscales,fullrow8slotservice oraccuracy/5ms acceptance. Existingexpirydeficiency unchanged.'}
 if raw.exists() and b'Binary:\n' in raw.read_bytes():
  header,data=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',header)[1]);vv=[l.split()[1] for l in header.decode().split('Variables:\n')[1].splitlines() if l.strip()];arr=np.frombuffer(data[:len(data)//(nv*8)*(nv*8)],dtype='<f8').reshape(-1,nv);t=arr[:,0];np.savez_compressed(rp.with_suffix('.npz'),waveforms=arr,variables=np.array(vv));o['last_time_s']=float(t[-1]);o['module_simulation_completed']=bool(run.returncode==0 and abs(t[-1]-110e-6)<1e-12 and np.isfinite(arr).all() and 'aborted' not in log.lower())
  if o['module_simulation_completed']:
   at=lambda n,u:float(np.interp(u*1e-6,t,arr[:,vv.index('v('+n.lower()+')')]));rows=[]
   for tag,us,reference in [('A_first',24.5,aa),('B',59.5,bb),('A_return',94.5,aa)]:rows.append({'case':tag,'AGE_v':at('AGE',us),'AMP_v':at('AMPLITUDE',us),'AGE_restore_error_v':at('AGE',us)-reference['age_v'],'AMP_restore_error_v':at('AMPLITUDE',us)-reference['amplitude_v']})
   caps=[]
   for slot,us in [(0,39),(1,74)]:caps.append({'slot':slot,'sample_us':us,'AGE_state_v':at('AGE',us),'AMP_state_v':at('AMPLITUDE',us),'AGE_DATA_v':at(f'AGE_DATA{slot}',us),'AMP_DATA_v':at(f'AMP_DATA{slot}',us),'AGE_capture_error_v':at(f'AGE_DATA{slot}',us)-at('AGE',us),'AMP_capture_error_v':at(f'AMP_DATA{slot}',us)-at('AMPLITUDE',us)})
   o.update(restore_cases=rows,capture_cases=caps,slot0_hold_change_after_B_and_A_return_v={kind:at(kind+'_DATA0',109)-at(kind+'_DATA0',44) for kind in ('AGE','AMP')},slot0_slot1_separation_at_end_v={kind:at(kind+'_DATA0',109)-at(kind+'_DATA1',109) for kind in ('AGE','AMP')},max_restore_error_v=max(abs(r[k]) for r in rows for k in ('AGE_restore_error_v','AMP_restore_error_v')),max_capture_error_v=max(abs(r[k]) for r in caps for k in ('AGE_capture_error_v','AMP_capture_error_v')))
 o['sha256']={p.relative_to(R).as_posix():sha(p) for p in inputs+[deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
