"""One bounded native extracted gate simulation at two stated output loads."""
from pathlib import Path
import json,re,subprocess,time,hashlib,math
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'results/native_control_gates_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True);files={Path(__file__)};texts=[]
    cells=['gf180_phase_inverter_fullroute','gf180_reset_select_and_fullroute']
    for cell in cells:
        folder=BASE/'layout'/cell;qp=folder/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
        gp=folder/(cell+'.gds');assert sha(gp)==q['sha256'][gp.name]
        sp=folder/(cell+'_cap.spice');texts.append(sp.read_text());files.update([qp,gp,sp])
    models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
    lines=['Native GF180 routed inverter and AND truth/delay test',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-9','\n'.join(texts),'Vdd vdd 0 3.3','Va a 0 PWL(0 0 19.9n 0 20n 3.3 39.9n 3.3 40n 0 59.9n 0 60n 3.3 80n 3.3)','Vb b 0 PWL(0 0 39.9n 0 40n 3.3 80n 3.3)']
    nodes=['v(a)','v(b)']
    for tag,load in [('10fF','10f'),('100fF','100f')]:
        lines += [f'Xinv_{tag} a inv_{tag} vdd 0 {cells[0]}',f'Xand_{tag} a b y_{tag} yb_{tag} vdd 0 {cells[1]}',f'Cinv_{tag} inv_{tag} 0 {load}',f'Cy_{tag} y_{tag} 0 {load}',f'Cyb_{tag} yb_{tag} 0 {load}']
        nodes += [f'v(inv_{tag})',f'v(y_{tag})',f'v(yb_{tag})']
    data=OUT/'waveforms.dat';deck=OUT/'bench.spice';lines+=['.control','set numdgt=15','tran 0.02n 80n 0 0.05n','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end'];deck.write_text('\n'.join(lines)+'\n');files.add(deck)
    result=subprocess.run(['docker','run','--rm','--network','none','--memory','1g','--cpus','1','--volume',str(ROOT)+':/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','60','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=75)
    log=OUT/'ngspice.log';log.write_text(result.stdout+result.stderr);files.add(log)
    report=dict(module_simulation_completed=False,simulator_returncode=result.returncode,process_corner='GF180 typical 3.3V 27C',output_loads_fF=[10,100],scope='Actual qualified native extracted MOS plus routing-C inverter/AND cells. Four truth states and stated capacitive loads; nominal local module evidence only, no global wire or SNN5ms claim.')
    if result.returncode==0 and data.exists():
        rows=[]
        for line in data.read_text().splitlines()[1:]:
            if line.strip():rows.append([float(v) for v in line.split()])
        assert rows and all(len(r)==9 for r in rows)
        observations=[];errors=[]
        for t,a,b in [(10e-9,0,0),(30e-9,1,0),(50e-9,0,1),(70e-9,1,1)]:
            row=min(rows,key=lambda r:abs(r[0]-t));expected=[3.3*(1-a),3.3*(a*b),3.3*(1-a*b)]
            for li,tag in enumerate(['10fF','100fF']):
                measured=row[3+li*3:6+li*3];delta=[abs(x-y) for x,y in zip(measured,expected)];errors.extend(delta)
                observations.append(dict(load=tag,time_s=row[0],a=a,b=b,inv_y_yb_V=measured,expected_V=expected,max_error_V=max(delta)))
        def crossing(column,edge,direction):
            for a,b in zip(rows,rows[1:]):
                if b[0]<edge:continue
                if (a[column]-1.65)*direction<=0 and (b[column]-1.65)*direction>=0:
                    return (a[0]+(1.65-a[column])*(b[0]-a[0])/(b[column]-a[column])-edge)*1e9
            return None
        delays=[]
        for li,tag in enumerate(['10fF','100fF']):
            delays.append(dict(load=tag,inverter_fall_ns=crossing(3+li*3,19.95e-9,-1),and_rise_ns=crossing(4+li*3,59.95e-9,1)))
        report.update(module_simulation_completed=True,truth_table_pass=max(errors)<0.33,max_settled_error_V=max(errors),observations=observations,delays=delays,data_rows=len(rows));files.add(data)
    report.update(elapsed_seconds=time.monotonic()-started,sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)})
    (OUT/'simulation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['observations','sha256']}),flush=True)
    assert report['module_simulation_completed'] and report['truth_table_pass']
if __name__=='__main__':main()
