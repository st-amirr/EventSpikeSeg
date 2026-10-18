"""One bounded native higherpage command/readout sequence, three address epochs."""
from pathlib import Path
import hashlib,json,re,subprocess,time,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic';C='gf180_shared_page_tree_selector8_v2';D=B/'layout'/C
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    qp=D/'qualification.json';fp=D/'flat_cap_full_qualification.json';q=json.loads(qp.read_text());fq=json.loads(fp.read_text());assert q['lvs_unique'] and fq['all_flat_extraction_node_ground_caps_verified'];src=D/(C+'_fullcap.spice');assert sha(src)==fq['sha256'][src.relative_to(R).as_posix()];text=src.read_text();ports=re.search(r'(?m)^\.subckt\s+'+C+r'\s+([^\n]+)',text.replace('\n+',' '))[1].split();assert ports==q['ports']
    frozen=B/'results/gf180_page1024_read_frontend_partition_v1_native_A_B_A.json';f=json.loads(frozen.read_text());assert f['module_simulation_completed'];va=f['cases'][0]['recovered_v'];vb=f['cases'][1]['recovered_v'];stem='gf180_shared_page_tree_selector8_v2_native_A_B_A';rp=B/'results'/(stem+'.json');assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(stem+'.spice');inv=B/'layout/gf180_dense_inverter_v1/gf180_dense_inverter_v1_cap.spice';pre='/workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice'
    lines=['Native hierarchical page selector A-B-A',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options klu method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18',text,inv.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0']
    def ctrl(n,pts):
        wave='PWL('+' '.join(f'{t}u {v}' for t,v in pts)+')';lines.extend([f'V{n} {n}_drv 0 {wave}',f'Xb{n} {n}_drv {n}_b VDD VSS gf180_dense_inverter_v1',f'Xd{n} {n}_b {n} VDD VSS gf180_dense_inverter_v1'])
    def windows(ww):
        pts=[(0,0)]
        for a,b in ww:pts.extend([(a-.01,0),(a,3.3),(b-.01,3.3),(b,0)])
        return pts+[(40,0)]
    addr=[(0,0),(11.99,0),(12,3.3),(24.99,3.3),(25,0),(40,0)]
    for k in range(3):ctrl(f'A{k}',addr)
    ctrl('WRITE_CMD',windows([(.5,1),(13,13.5),(26,26.5)]));ctrl('READ_CMD',windows([(2,11),(14,24),(27,37)]));ctrl('READ_ENABLE',windows([(2.1,10.9),(14.1,23.9),(27.1,36.9)]))
    for j in range(8):
        lines.extend([f'Vr{j} RECOV{j}_src 0 {vb if j==7 else va:.16g}',f'Rr{j} RECOV{j}_src RECOV{j} 100'])
        for mode in ['WRITE','READ','ENABLE']:lines.append(f'Cload{mode}{j} {mode}{j} VSS 100f')
    lines+=['Cout RECOV VSS 100f','Xtree '+' '.join(ports)+' '+C,'.save v(RECOV) '+' '.join(f'v({mode}{j})' for j in range(8) for mode in ['WRITE','READ','ENABLE'])+' i(Vdd)','.tran .02u 40u 0 .2u','.end'];deck.write_text('\n'.join(lines)+'\n');started=time.monotonic()
    run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);lp=rp.with_suffix('.log');log=run.stdout+run.stderr;lp.write_text(log)
    o={'module_simulation_completed':False,'native_primitives':230,'complete_native_C_branches':fq['linear_branch_count'],'returncode':run.returncode,'wall_s':time.monotonic()-started,'full_population_5ms_accepted':False,'full_chip_complete':False,'scope':'Actualnative230MOS higherpage selector withcomplete2332routingC. Threeaddress epochs0→7→0,separateWRITE/READ/ENABLE. Static100ohm childRECOVfixtures frozenfromcompletednative1024frontend recovery;100fFchildcommand/output fixtures areprovisionalloading. No coupledpage storage/longtree/fanout/scheduler/5ms ororiginalfloatprecision claim.'}
    if raw.exists() and b'Binary:\n' in raw.read_bytes():
        header,data=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',header)[1]);names=[l.split()[1] for l in header.decode().split('Variables:\n')[1].splitlines() if l.strip()];a=np.frombuffer(data[:len(data)//(nv*8)*(nv*8)],dtype='<f8').reshape(-1,nv);t=a[:,0];np.savez_compressed(rp.with_suffix('.npz'),waveforms=a,variables=np.array(names));o['last_time_s']=float(t[-1]);o['module_simulation_completed']=bool(run.returncode==0 and abs(t[-1]-40e-6)<1e-12 and np.isfinite(a).all() and 'aborted' not in log.lower())
        if o['module_simulation_completed']:
            at=lambda n,u:float(np.interp(u*1e-6,t,a[:,names.index('v('+n.lower()+')')]));rows=[];logic=[]
            for tag,j,wu,ru,target in [('A_first',0,.75,10.5,va),('B',7,13.25,23.5,vb),('A_return',0,26.25,36.5,va)]:
                val=at('RECOV',ru);rows.append({'case':tag,'page':j,'at_us':ru,'measured_child_source_v':target,'recovered_v':val,'selector_error_v':val-target})
                for mode,u in [('WRITE',wu),('READ',ru),('ENABLE',ru)]:
                    vals=[at(f'{mode}{k}',u) for k in range(8)];logic.append({'case':tag,'mode':mode,'selected_page':j,'outputs_v':vals,'onehot_correct':vals[j]>3.0 and max(v for k,v in enumerate(vals) if k!=j)<.1})
            o.update(cases=rows,command_checks=logic,max_selector_error_v=max(abs(r['selector_error_v']) for r in rows),all_commands_correct=all(r['onehot_correct'] for r in logic));o['hierarchical_page_selection_observed']=o['all_commands_correct'] and o['max_selector_error_v']<.005
    o['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),qp,fp,src,frozen,inv,deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k not in ['sha256','command_checks']},indent=2))
if __name__=='__main__':main()
