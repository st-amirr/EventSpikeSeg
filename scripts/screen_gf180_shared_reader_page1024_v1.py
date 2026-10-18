"""Two selected logical rows share one actual feedback reader; all1024 states native."""
from pathlib import Path
import hashlib,json,re,subprocess,time,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
D=B/'assembly/shared_reader_page1024_v1/verification/native_fullcap_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    qp=D/'qualification.json';q=json.loads(qp.read_text())
    assert q['full_cap_extraction_completed'] and q['all_native_devices_and_ports_unchanged'] and q['all_native_substrate_caps_verified']
    src=D/'parent_fullcap.spice';assert sha(src)==q['sha256'][src.relative_to(R).as_posix()]
    text=src.read_text();top=re.search(r'(?m)^\.subckt (\S+)',text)[1];ports=re.search(r'(?m)^\.subckt \S+ (.+)$',text.replace('\n+',' '))[1].split()
    stem='gf180_shared_reader_page1024_v1_native_two_row_A_B_A';rp=B/'results'/(stem+'.json');assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(stem+'.spice')
    models=B/'pdk/gf180_primitive_source/models/ngspice';pre='/workspace/'+models.relative_to(R).as_posix();inv=B/'layout/gf180_dense_inverter_v1/gf180_dense_inverter_v1_cap.spice'
    lines=['Native shared1024state reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options klu method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18',text,inv.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','Inbias 0 MASTER_NBIAS 16u','Ipbias PBIAS 0 1u']
    driven=set()
    def ctrl(n,pts):
        assert n in ports and n not in driven;driven.add(n);wave=str(pts) if isinstance(pts,(int,float)) else 'PWL('+' '.join(f'{t}u {v}' for t,v in pts)+')'
        lines.extend([f'Vc{len(driven)} {n}_drv 0 {wave}',f'Xb{len(driven)} {n}_drv {n}_b VDD VSS gf180_dense_inverter_v1',f'Xd{len(driven)} {n}_b {n} VDD VSS gf180_dense_inverter_v1'])
    def intervals(windows):
        pts=[(0,0)]
        for a,b in windows:pts.extend([(a-.01,0),(a,3.3),(b-.01,3.3),(b,0)])
        return pts+[(34,0)]
    address=[(0,0),(3.99,0),(4,3.3),(9.99,3.3),(10,0),(17.99,0),(18,3.3),(25.99,3.3),(26,0),(34,0)]
    for k in range(3):ctrl(f'LOW{k}',3.3);ctrl(f'HIGH{k}',address)
    ctrl('LOW3',address);ctrl('WRITE_CMD',intervals([(1,3),(5,7)]));ctrl('READ_CMD',intervals([(11,16),(19,24),(27,32)]));ctrl('READ_ENABLE',intervals([(11.2,15.8),(19.2,23.8),(27.2,31.8)]))
    for k in range(8):
        ctrl(f'SEL{k}',3.3 if k==0 else 0)
        lines.extend([f'Vdata{k} DATA_SRC{k} 0 PWL(0 1.2 3.5u 1.2 3.6u 1.35 34u 1.35)',f'Rdata{k} DATA_SRC{k} DATA{k} 100'])
    save=['P0__B0_STATE70','P7__B1_STATE70','P3__B0_STATE70','RECOV','MASTER_NBIAS','PBIAS']
    lines+=['Xpage '+' '.join(ports)+' '+top,'.save '+' '.join('v('+n+')' for n in save)+' i(Vdd)','.tran .02u 34u 0 .2u','.end'];deck.write_text('\n'.join(lines)+'\n')
    started=time.monotonic();p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135)
    lp=rp.with_suffix('.log');log=p.stdout+p.stderr;lp.write_text(log)
    o={'module_simulation_completed':False,'returncode':p.returncode,'elapsed_wall_s':time.monotonic()-started,'solver_KLU_confirmed':'Using KLU' in log,'native_primitives':7847,'native_C_branches':q['linear_branch_count'],'native_state_count':1024,'feedback_reader_count':1,'all1024_states_natively_initialized':False,'full_chip_complete':False,'scope':'Actual full1024state page6818MOS1029MIM andfresh verifiedflatnativeC. One feedbackreader;page-selected shared8read columns plusone columnmux. Two selected8state rows natively written through100ohm analogDATA programming fixtures;otherstates unforcedDC,noIC/UIC. A=P0bank0row7,B=P7bank1row7;readA,B,A withcommands off duringaddress changes andnative categoricalinverter drivers. Sixteen bankreference diodes share16uA master;readerPBIAS1uA. Typical27C/noiseoff. Recovery errors measured againstactualstoredstates,notprogrammedideal; no modelprecision,allrowstartup,retention,throughput orfullASIC acceptance.'}
    if raw.exists() and b'Binary:\n' in raw.read_bytes():
        h,b=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',h)[1]);names=[l.split()[1] for l in h.decode().split('Variables:\n')[1].splitlines() if l.strip()];w=np.frombuffer(b[:len(b)//(nv*8)*(nv*8)],dtype='<f8').reshape(-1,nv);t=w[:,0];o['last_time_s']=float(t[-1]);np.savez_compressed(rp.with_suffix('.npz'),waveforms=w,variables=np.array(names));o['module_simulation_completed']=bool(p.returncode==0 and abs(t[-1]-34e-6)<1e-12 and np.isfinite(w).all() and 'aborted' not in log.lower())
        if o['module_simulation_completed']:
            at=lambda n,u:float(np.interp(u*1e-6,t,w[:,names.index('v('+n.lower()+')')]));rows=[]
            for tag,n,u,target in [('A_first',save[0],15.5,1.2),('B',save[1],23.5,1.35),('A_return',save[0],31.5,1.2)]:
                state=at(n,u);rec=at('RECOV',u);rows.append({'case':tag,'sample_time_us':u,'stored_v':state,'recovered_v':rec,'recovery_error_v':rec-state,'programming_target_v':target,'write_error_v':state-target})
            o.update(cases=rows,max_recovery_error_v=max(abs(x['recovery_error_v']) for x in rows),max_write_error_v=max(abs(x['write_error_v']) for x in rows),A_roundtrip_stored_change_v=rows[2]['stored_v']-rows[0]['stored_v'],unselected_P3_state_change_v=at(save[2],33.5)-at(save[2],.5))
            o['shared_reader_A_B_A_observed']=bool(o['max_recovery_error_v']<.03 and o['max_write_error_v']<.06 and rows[1]['recovered_v']>rows[0]['recovered_v'])
    o['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),qp,src,inv,deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))

if __name__=='__main__':main()
