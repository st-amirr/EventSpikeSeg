"""One bounded bidirectional native transfer-gate module simulation."""
from pathlib import Path
import json,hashlib,subprocess,time
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'results/native_transfer_gate_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True);cell='gf180_fixed_body_tg_quarter_shorttracks';folder=BASE/'layout'/cell;qp=folder/'qualification.json';q=json.loads(qp.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'];gp=folder/(cell+'.gds');assert sha(gp)==q['sha256'][gp.name];sp=folder/(cell+'_cap.spice');models=BASE/'pdk/gf180_primitive_source/models/ngspice';pre='/workspace/'+models.relative_to(ROOT).as_posix();data=OUT/'waveforms.dat';deck=OUT/'bench.spice'
    lines=['Native GF180 bidirectional transfer gate',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-9',sp.read_text(),'Vdd vdd 0 3.3','Vsrc src 0 PWL(0 1.0 19.9n 1.0 20n 1.6 39.9n 1.6 40n 2.2 89.9n 2.2 90n 0 5.001m 0)','Ven en 0 PWL(0 3.3 79.9n 3.3 80n 0 5.001m 0)','Venb enb 0 PWL(0 0 79.9n 0 80n 3.3 5.001m 3.3)',f'Xfwd src fwd en enb 0 vdd {cell}',f'Xrev rev src en enb 0 vdd {cell}','Cfwd fwd 0 100f','Crev rev 0 100f','.control','set numdgt=15','tran .02n 5.001m 0 50u','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' v(src) v(fwd) v(rev) v(en) v(enb)','quit','.endc','.end'];deck.write_text('\n'.join(lines)+'\n')
    r=subprocess.run(['docker','run','--rm','--network','none','--memory','1g','--cpus','1','--volume',str(ROOT)+':/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','60','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=75);log=OUT/'ngspice.log';log.write_text(r.stdout+r.stderr)
    report=dict(module_simulation_completed=False,simulator_returncode=r.returncode,fixture_load_fF=100,scope='Actual native2MOS transfer gate with extracted local routingC, both directions, three input voltages and5ms disabled stress.100fF capacitors are external load fixtures; this is not the array membrane-retention or full-system5ms test.')
    files={Path(__file__),qp,gp,sp,deck,log}|set(models.rglob('*.spice'))
    if r.returncode==0 and data.exists():
        rows=[[float(v) for v in s.split()] for s in data.read_text().splitlines()[1:] if s.strip()];assert rows and all(len(r)==6 for r in rows)
        def at(t):return min(rows,key=lambda r:abs(r[0]-t))
        errors=[];obs=[]
        for t,target in [(10e-9,1.0),(30e-9,1.6),(60e-9,2.2)]:
            row=at(t);errors += [abs(row[2]-target),abs(row[3]-target)];obs.append(dict(time_s=row[0],target_V=target,forward_V=row[2],reverse_V=row[3]))
        hold_start=at(1e-6);hold_end=rows[-1]
        report.update(module_simulation_completed=abs(hold_end[0]-5.001e-3)<1e-12,bidirectional_transfer_pass=max(errors)<0.05,max_on_state_error_V=max(errors),disabled_5ms_change_V=dict(forward=hold_end[2]-hold_start[2],reverse=hold_end[3]-hold_start[3]),observations=obs,data_rows=len(rows));files.add(data)
    report.update(elapsed_seconds=time.monotonic()-started,sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)});(OUT/'simulation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='sha256'}),flush=True);assert report['module_simulation_completed'] and report['bidirectional_transfer_pass']
if __name__=='__main__':main()
