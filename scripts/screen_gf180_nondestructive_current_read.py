"""Native current-sense alternative: read membrane without charge-transfer restore."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--park-v',type=float,choices=[0,1.65],default=0)
    parser.add_argument('--max-step-ns',type=int,choices=[10,20],default=20)
    a=parser.parse_args();sources=set();texts=[]
    for cell in ['gf180_fixed_body_tg_fullroute','gf180_phase_inverter_fullroute']:
        d=BASE/'layout'/cell;p=d/'qualification.json';q=json.loads(p.read_text());sources.add(p)
        assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
        for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
            for n,h in q.get(key,{}).items():
                f=d/n if key=='sha256' else ROOT/n;assert digest(f)==h,str(f);sources.add(f)
        texts.extend((d/(cell+'_cap.spice')).read_text().splitlines())
    models=BASE/'pdk/gf180_primitive_source/models/ngspice';sources.update(models.rglob('*.spice'))
    prefix='/workspace/'+models.relative_to(ROOT).as_posix()
    stem='gf180_nondestructive_current_read_'+hashlib.sha256(json.dumps(vars(a),sort_keys=True).encode()).hexdigest()[:10]+'_src'+digest(Path(__file__))[:12]
    snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());sources.add(snap)
    lines=['Native non-destructive current read diagnostic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',
        '.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,
        'Vdd vdd 0 3.3','Vcm vcm 0 1.65',f'Vpark park_voltage 0 {a.park_v}',
        'Vwrite write_command 0 PWL(0 3.3 19.99u 3.3 20u 0 80u 0)',
        'Vread read_command 0 PWL(0 0 29.99u 0 30u 3.3 44.99u 3.3 45u 0 59.99u 0 60u 3.3 74.99u 3.3 75u 0 80u 0)',
        'Vparking park_command 0 PWL(0 3.3 29.97u 3.3 29.98u 0 45.01u 0 45.02u 3.3 59.97u 3.3 59.98u 0 75.01u 0 75.02u 3.3 80u 3.3)']
    for phase in ['write','read','park']:
        lines.extend([f'Xclock_b_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xclock_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
    targets={'low':.75,'mid':1.65,'high':2.55}
    for n,v in targets.items():
        lines.extend([f'Vin_{n} input_{n} 0 {v}',f'Vcolumn_{n} column_{n} 0 1.65',
            f'Xwrite_{n} input_{n} state_{n} write writeb 0 vdd gf180_fixed_body_tg_fullroute',
            f'Xhold_{n} state_{n} vcm cap_mim_2f0_m4m5_noshield c_length=7u c_width=7u',
            f'Xsense_{n} drain_{n} state_{n} 0 0 nfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u',
            f'Xselect_{n} column_{n} drain_{n} read readb 0 vdd gf180_fixed_body_tg_fullroute',
            f'Xpark_{n} park_voltage drain_{n} park parkb 0 vdd gf180_fixed_body_tg_fullroute',
            f'.ic v(state_{n})={v} v(drain_{n})={a.park_v}'])
    lines.extend(['.control','set numdgt=15',f'tran {a.max_step_ns}n 80u 0 {a.max_step_ns}n uic'])
    for n in targets:
        lines.extend([f'let state_{n}=v(state_{n})',f'let current_{n}=-i(Vcolumn_{n})',f'let drain_{n}=v(drain_{n})'])
        for phase,t in [('acquired','19.9u'),('before','25u'),('read1','40u'),('after1','50u'),('read2','70u'),('after2','79u')]:
            for signal in ['state','current','drain']:lines.append(f'meas tran {n}_{signal}_{phase} find {signal}_{n} at={t}')
        # Compute differences inside SPICE, avoiding subtraction of rounded logs.
        lines.append(f'let delta_{n}=state_{n}-{n}_state_before')
        for phase,t in [('after1','50u'),('after2','79u'),('read1','40u')]:
            lines.append(f'meas tran {n}_delta_{phase} find delta_{n} at={t}')
        lines.extend([f'let write_delta_{n}=state_{n}-{n}_state_acquired',f'meas tran {n}_delta_write find write_delta_{n} at=25u'])
    lines.extend(['quit','.endc','.end']);deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');sources.add(deck)
    r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=r.stdout+r.stderr;p=BASE/'results'/(stem+'.log');p.write_text(log);sources.add(p)
    values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_(?:state|current|drain|delta)_(?:acquired|before|read1|after1|read2|after2|write))\s*=\s*([-+0-9.eE]+)',log)}
    complete=r.returncode==0 and len(values)==66 and 'timestep too small' not in log.lower();cases=[]
    if complete:
        for n,target in targets.items():
            v={k.removeprefix(n+'_'):x for k,x in values.items() if k.startswith(n+'_')}
            cases.append({'target_v':target,'measurements':v,'initial_write_release_mv':1000*v['delta_write'],
                'after_first_read_disturbance_uv':1e6*v['delta_after1'],'after_second_read_disturbance_uv':1e6*v['delta_after2'],
                'temporary_read_disturbance_mv':1000*v['delta_read1'],'read_current_a':v['current_read1']})
    q={'simulation_completed':complete,'settings':vars(a),'cases':cases,'scope':'Method-change screening only: official native schematic NF0.5/L1 sense transistor and7um MIM, cap-extracted qualified write/select/park TGs and clock inverters connected schematically. NF gate stays attached to state from initialization; fixed source/body0. Shared ideal column clamp1.65V and ideal parking supply are bench assumptions, not implemented readout/bias. Two reads with parking return, no destructive charge transfer, inverse or restoration of state. Gate leakage disabled/unqualified in native model; no noise/mismatch/PVT/RPEX/5ms retention/read-current decode/full-float/PLIF/service/area acceptance. Constant1.65V parking consumes continuous sense current;0V parking avoids that ideal DC path but incurs reversible drain/gate coupling. Initial write-release error remains.',
        'physical_cell_qualified':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    p=BASE/'results'/(stem+'.json');p.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(p),'simulation_completed':complete,'cases':cases},indent=2))
    if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
