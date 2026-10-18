"""New page read-selection circuit with frozen measured native bank RAW boundary fixtures."""
from pathlib import Path
import hashlib,json,re,subprocess,time,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';A=B/'assembly/page1024_read_frontend_partition_v1';D=A/'verification/native_fullcap_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    qp=D/'qualification.json';q=json.loads(qp.read_text());assert q['full_cap_extraction_completed'] and q['all_native_devices_and_ports_unchanged'] and q['all_native_substrate_caps_verified']
    src=D/'parent_fullcap.spice';assert sha(src)==q['sha256'][src.relative_to(R).as_posix()];fixture=A/'frozen_native_RAW_fixture_v1.json';f=json.loads(fixture.read_text())
    text=src.read_text();top=re.search(r'(?m)^\.subckt (\S+)',text)[1];ports=re.search(r'(?m)^\.subckt \S+ (.+)$',text.replace('\n+',' '))[1].split()
    stem='gf180_page1024_read_frontend_partition_v1_native_A_B_A';rp=B/'results'/(stem+'.json');assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(stem+'.spice')
    inv=B/'layout/gf180_dense_inverter_v1/gf180_dense_inverter_v1_cap.spice';pre='/workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice'
    lines=['Native page-selected shared reader boundary simulation',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options klu method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18',text,inv.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2',f'Vbias MASTER_NBIAS 0 {f["shared16diode_master_bias_v"]:.16g}','Ip PBIAS 0 1u']
    driven=set()
    def ctrl(n,pts):
        assert n in ports and n not in driven,n;driven.add(n);wave=str(pts) if isinstance(pts,(int,float)) else 'PWL('+' '.join(f'{t}u {v}' for t,v in pts)+')'
        lines.extend([f'Vc{len(driven)} {n}_drv 0 {wave}',f'Xb{len(driven)} {n}_drv {n}_b VDD VSS gf180_dense_inverter_v1',f'Xd{len(driven)} {n}_b {n} VDD VSS gf180_dense_inverter_v1'])
    def windows(ww):
        pts=[(0,0)]
        for a,b in ww:pts.extend([(a-.01,0),(a,3.3),(b-.01,3.3),(b,0)])
        return pts+[(40,0)]
    addr=[(0,0),(11.99,0),(12,3.3),(24.99,3.3),(25,0),(40,0)]
    for k in range(3):ctrl(f'HIGH{k}',addr)
    for k in range(4):ctrl(f'LOW{k}',0)
    ctrl('WRITE_CMD',0);ctrl('READ_CMD',windows([(1,11),(14,24),(27,37)]));ctrl('READ_ENABLE',windows([(1.1,10.9),(14.1,23.9),(27.1,36.9)]))
    for k in range(8):
        points=[(t,3.3-v) for t,v in addr] if k==0 else addr if k==7 else 0;ctrl(f'SEL{k}',points)
        lines.append(f'Vdata{k} DATA{k} 0 1.2')
    for j in range(8):
        case=f['cases'][1 if j==7 else 0]
        for k,v in enumerate(case['RAW_columns_v']):
            n=f'RAW{j}_{k}';assert n in ports;lines.extend([f'Vraw{j}_{k} {n}_src 0 {v:.16g}',f'Rraw{j}_{k} {n}_src {n} 100'])
    save=['RECOV','RAW0_0','RAW7_7','MASTER_NBIAS','PBIAS','HIGH0','READ_CMD','READ_ENABLE','SEL0','SEL7']
    lines+=['Xpage '+' '.join(ports)+' '+top,'.save '+' '.join('v('+n+')' for n in save)+' i(Vdd)','.tran .02u 40u 0 .2u','.end'];deck.write_text('\n'.join(lines)+'\n');started=time.monotonic()
    run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135)
    lp=rp.with_suffix('.log');log=run.stdout+run.stderr;lp.write_text(log)
    o={'module_simulation_completed':False,'returncode':run.returncode,'elapsed_wall_s':time.monotonic()-started,'solver_KLU_confirmed':'Using KLU' in log,'native_primitives':359,'native_C_branches':q['linear_branch_count'],'feedback_reader_count':1,'full1024_connected_transient_completed':False,'full_chip_complete':False,'scope':'Actual page decoder/readTG/enableinverse/columnmux/feedbackreader physical partition354MOS5MIM,freshfullroutingC. Eight storage/readout children excluded only fromcharacterization;whole1024 layout7847primitives/71802C remainsverified/preserved. Frozen RAWcolumns fromcompletednative128bank39/59us trace,100ohm stiffboundaryfixtures;MASTERbias fromfullpage16diode16uAtrace3.5us. This tests new sharedpage frontend A=page0col0,B=page7col7,A,withactual categoricaldriver chain/decoder,not full1024storage behavior. No fitting,ideal numericalstate,IC/UIC. Does notqualify banksourceimpedance,allstates startup,retention,trainedprecision,5ms orfullASIC.'}
    if raw.exists() and b'Binary:\n' in raw.read_bytes():
        h,b=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',h)[1]);names=[l.split()[1] for l in h.decode().split('Variables:\n')[1].splitlines() if l.strip()];w=np.frombuffer(b[:len(b)//(nv*8)*(nv*8)],dtype='<f8').reshape(-1,nv);t=w[:,0];o['last_time_s']=float(t[-1]);np.savez_compressed(rp.with_suffix('.npz'),waveforms=w,variables=np.array(names));o['module_simulation_completed']=bool(run.returncode==0 and abs(t[-1]-40e-6)<1e-12 and np.isfinite(w).all() and 'aborted' not in log.lower())
        if o['module_simulation_completed']:
            at=lambda n,u:float(np.interp(u*1e-6,t,w[:,names.index('v('+n.lower()+')')]));rows=[]
            for tag,ix,u in [('A_first',0,10.5),('B',1,23.5),('A_return',0,36.5)]:
                target=f['cases'][ix]['actual_stored_reference_v'];rec=at('RECOV',u);rows.append({'case':tag,'at_us':u,'frozen_native_stored_reference_v':target,'recovered_v':rec,'recovery_error_v':rec-target})
            o.update(cases=rows,max_recovery_error_v=max(abs(x['recovery_error_v']) for x in rows),A_return_recovered_change_v=rows[2]['recovered_v']-rows[0]['recovered_v']);o['page_selected_reader_A_B_A_observed']=bool(o['max_recovery_error_v']<.03 and rows[0]['recovered_v']>rows[1]['recovered_v'])
    o['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),qp,src,fixture,inv,deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))

if __name__=='__main__':main()
