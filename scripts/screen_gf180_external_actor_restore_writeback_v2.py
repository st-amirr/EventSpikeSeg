"""One native parent storage/reader/compute restore/writeback case; no ideal DATA source."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';D=B/'assembly/full25_external_bank_service_v4/verification/actor_00_external_service_fullcap_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 fq=D/'qualification.json';q=json.loads(fq.read_text());assert q['full_cap_extraction_completed'] and q['all_native_devices_and_ports_unchanged'] and q['all_native_substrate_caps_verified'];src=D/'parent_fullcap.spice';assert sha(src)==q['sha256'][src.relative_to(R).as_posix()]
 s=src.read_text();tokens=s.replace('\n+',' ');ports=re.search(r'(?m)^\.subckt ESS_ACTOR_00_flat (.+)$',tokens)[1].split();devices=[l.split() for l in tokens.splitlines() if l.startswith('X')]
 initdev=next(t for t in devices if t[2]=='compute__INIT' and 'EXTERNAL_COMPUTE_DATA' in t[1:4]);buffer=next(n for n in [initdev[1],initdev[3]] if n!='EXTERNAL_COMPUTE_DATA');write=next(t for t in devices if t[2]=='compute__C_WRITE' and buffer in t[1:4]);state=next(n for n in [write[1],write[3]] if n!=buffer)
 stem='gf180_external_actor_restore_writeback_v2';rp=B/'results'/(stem+'.json');assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(stem+'.spice');models=B/'pdk/gf180_primitive_source/models/ngspice';pre='/workspace/'+models.relative_to(R).as_posix()
 inv=B/'layout/gf180_dense_inverter_v1/gf180_dense_inverter_v1_cap.spice';assert inv.exists()
 lines=['Native external resident bank actor restore/writeback',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18',s,inv.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vsref STORAGE_REFERENCE 0 1.2','Vcref COMPUTE_REFERENCE 0 1.65','Vinit EXTERNAL_INIT_DATA 0 1.8']
 driven=set()
 def ctrl(n,points):
  assert n in ports and n not in driven,n;driven.add(n);wave=str(points) if isinstance(points,(int,float)) else 'PWL('+' '.join(f'{t}u {v}' for t,v in points)+')';lines.extend([f'Vctrl{len(driven)} {n}_drv 0 {wave}',f'Xdb{len(driven)} {n}_drv {n}_drvb VDD VSS gf180_dense_inverter_v1',f'Xd{len(driven)} {n}_drvb {n} VDD VSS gf180_dense_inverter_v1'])
 def pw(a,b):return [(0,0),(a-.1,0),(a,3.3),(b-.1,3.3),(b,0),(120,0)]
 def pair(a,b,points):ctrl(a,points);ctrl(b,[(t,3.3-v) for t,v in points])
 start=[(0,3.3),(29.9,3.3),(30,0),(71.9,0),(72,3.3),(77.9,3.3),(78,0),(120,0)]
 pair('compute__C_WRITE','compute__C_WRITEB',start)
 ini=[(0,3.3),(49.9,3.3),(50,0),(69.9,0),(70,3.3),(79.9,3.3),(80,0),(120,0)]
 pair('compute__INIT','compute__INITB',ini);pair('compute__RESTORE','compute__RESTOREB',[(0,0),(120,0)])
 pair('EXTERNAL_INITIALIZE','EXTERNAL_INITIALIZEB',[(0,3.3),(49.9,3.3),(50,0),(120,0)]);pair('EXTERNAL_RESTORE','EXTERNAL_RESTOREB',pw(70,80))
 pair('compute__C_PARK_AZ','compute__C_PARK_AZB',[(0,3.3),(24.9,3.3),(25,0),(120,0)]);pair('compute__C_OUTPUT_HOLD','compute__C_OUTPUT_HOLDB',[(0,0),(120,0)])
 ctrl('compute__C_AUXRESET',3.3)
 for c in range(8):
  points=[(0,3.3),(39.9,3.3),(40,0)]
  if c==0:points +=[(89.9,0),(90,3.3),(97.9,3.3),(98,0)]
  points +=[(120,0)];pair(f'compute__CAP{c}',f'compute__CAPB{c}',points);ctrl(f'compute__SEL{c}',0);ctrl(f'bank_service__SEL{c}',3.3 if c==0 else 0)
 for n in ['compute__A0','compute__A1','compute__A2','compute__WRITE_CMD','compute__READ_CMD','compute__READ_ENABLE','bank_service__BANK_SELECT','commit__BIN_START','commit__COMPLETE','event__REQUEST','WEIGHT_SIGN']:ctrl(n,0)
 for n in ['bank_service__A0','bank_service__A1','bank_service__A2','commit__RESET','event__RESET']:ctrl(n,3.3)
 for n in ['commit__CLK','event__CLK']:ctrl(n,[(0,0),(1.9,0),(2,3.3),(2.9,3.3),(3,0),(120,0)])
 ctrl('bank_service__WRITE_CMD',[(0,3.3),(30.9,3.3),(31,0),(99.9,0),(100,3.3),(107.9,3.3),(108,0),(120,0)])
 for n in ['bank_service__READ_CMD','bank_service__READ_ENABLE']:ctrl(n,pw(60,110))
 for n,v in [('compute__C_AUXREF',1.5682088493242619),('compute__C_SENSE_BIAS',.75),('compute__C_RESET_PROGRAM',.45),('compute__C_NCAS',1.1),('compute__C_INJ_PPROGRAM',2.5),('compute__C_INJ_NPROGRAM',.45),('compute__C_PCAS',2.2),('duration__MAG_DATA',.2),('duration__VRESET',.1),('duration__RAMP_CAS',2.2),('duration__RAMP_BIAS',2.6),('duration__BIAS',.75)]:lines.append(f'Vref{len(lines)} {n} 0 {v}')
 for n in ['compute__BIAS','bank_service__B0_BIAS','bank_service__B1_BIAS']:lines.append(f'Iref{len(lines)} 0 {n} 1u')
 for n,v in [('compute__IO_BIAS',9),('compute__PARK_BIAS',1),('bank_service__PBIAS',1),('compute__READER_BIAS',1),('compute__UP_BIAS',1),('compute__DOWN_BIAS',1),('external_up__BIAS',1)]:lines.append(f'Iref{len(lines)} {n} 0 {v}u')
 save=['bank_service__B0_STATE70','bank_service__B0_STATE71','bank_service__B1_STATE70','EXTERNAL_RECOVERED','EXTERNAL_SHIFTED','EXTERNAL_COMPUTE_DATA','SHARED_WRITE_DATA0','BETA_PHASE','SUBTRACTIVE_RESET_PHASE','POSITIVE_INJECTION','NEGATIVE_INJECTION','DETECT_PHASE','xactor.'+state]
 lines+=['Xactor '+' '.join(ports)+' ESS_ACTOR_00_flat','.save '+' '.join('v('+n+')' for n in save)+' i(Vdd)','.tran .02u 120u 0 1u','.end'];deck.write_text('\n'.join(lines)+'\n')
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);log=p.stdout+p.stderr;lp=rp.with_suffix('.log');lp.write_text(log)
 o=dict(completed=False,returncode=p.returncode,storage_restore_writeback_observed=False,native_parent_devices=2362,native_C_branches=q['linear_branch_count'],compute_native_state_node=state,full_chip_complete=False,scope='Actual firstactor v4 native2362MOS/MIM/R primitives and17392verified routingC; externalbank selectedrow7 receives actual physical compute/downshift/capture DATA,not ideal DATA or state source. Physical sharedreader/upshift/restore feeds compute C_STATE,then cap0 and sharedwrite return it. Existing native commit/event controllers heldreset,one resetclock,no requested beta/event/threshold/reset operation;this is an integration roundtrip,not complete neuron update. Native inverter categorical fixtures,external idealreference/programming currents;no IC/UIC,unselectedstatesunforced DC. Active numericalbudget1e-4 notaccuracyproof;typical/noiseoff,no PVT/mismatch/5ms ortrainedaccuracy acceptance.')
 if raw.exists() and b'Binary:\n' in raw.read_bytes():
  h,b=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',h)[1]);names=[l.split()[1] for l in h.decode().split('Variables:\n')[1].splitlines() if l.strip()];w=np.frombuffer(b[:len(b)//(nv*8)*(nv*8)],dtype='<f8').reshape(-1,nv);t=w[:,0];np.savez_compressed(rp.with_suffix('.npz'),waveforms=w,variables=np.array(names));o['last_time_s']=float(t[-1]);o['completed']=bool(p.returncode==0 and abs(t[-1]-120e-6)<1e-12 and 'aborted' not in log.lower() and np.isfinite(w).all())
  if o['completed']:
   at=lambda n,us:float(np.interp(us*1e-6,t,w[:,names.index('v('+n.lower()+')')]));resident=at(save[0],69);recovered=at('EXTERNAL_RECOVERED',69);shift=at('EXTERNAL_SHIFTED',77);comp=at('xactor.'+state,77);held=at('SHARED_WRITE_DATA0',99);final=at(save[0],119);o.update(resident_before_restore_v=resident,reader_error_v=recovered-resident,upshift_error_v=shift-(resident+.45),compute_restore_error_v=comp-shift,held_write_column_v=held,final_resident_v=final,writeback_error_v=final-held,roundtrip_state_change_v=final-resident,opposite_bank_change_v=at(save[2],119)-at(save[2],55));o['storage_restore_writeback_observed']=bool(abs(o['reader_error_v'])<.02 and abs(o['compute_restore_error_v'])<.02 and abs(o['writeback_error_v'])<.06)
 o['sha256']={x.relative_to(R).as_posix():sha(x) for x in [Path(__file__),fq,src,inv,deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
