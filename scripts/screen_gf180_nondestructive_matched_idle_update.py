"""Native current-sense alternative: read membrane without charge-transfer restore."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--park-v',type=float,choices=[0,1.65],default=0)
    parser.add_argument('--max-step-ns',type=int,choices=[10,20],default=20)
    parser.add_argument('--polarity',choices=['p','n','control'],default='control')
    parser.add_argument('--width-us',type=float,choices=[.1,1,4],default=1)
    parser.add_argument('--n-gate-v',type=float,choices=[.4,.42,.45,.55],default=.42)
    parser.add_argument('--neutral',action='store_true')
    parser.add_argument('--idle-reference',choices=['vcm','target'],default='vcm')
    a=parser.parse_args();sources=set();texts=[]
    for cell in ['gf180_nondestructive_storage_read_assembly_guarded_flat','gf180_phase_inverter_fullroute','gf180_fixed_body_tg_fullroute_half']:
        d=BASE/'layout'/cell;p=d/'qualification.json';q=json.loads(p.read_text());sources.add(p)
        assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
        for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
            for n,h in q.get(key,{}).items():
                f=d/n if key=='sha256' else ROOT/n;assert digest(f)==h,str(f);sources.add(f)
        texts.extend((d/(cell+'_cap.spice')).read_text().splitlines())
    models=BASE/'pdk/gf180_primitive_source/models/ngspice';sources.update(models.rglob('*.spice'))
    prefix='/workspace/'+models.relative_to(ROOT).as_posix()
    stem='gf180_nondestructive_matched_idle_update_'+hashlib.sha256(json.dumps(vars(a),sort_keys=True).encode()).hexdigest()[:10]+'_src'+digest(Path(__file__))[:12]
    snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());sources.add(snap)
    lines=['Native non-destructive current read diagnostic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical',
        '.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,
        'Vdd vdd 0 3.3','Vncas ncas 0 1.1','Vpcas pcas 0 2.2','Ireference bias 0 40u','Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u','Vcm vcm 0 1.65',f'Vpark park_voltage 0 {a.park_v}',
        'Vwrite write_command 0 PWL(0 3.3 19.99u 3.3 20u 0 80u 0)',
        'Vread read_command 0 0',
        'Vparking park_command 0 3.3']
    end=22+a.width_us
    lines.extend([f'Vinject_p inject_p 0 {3.3 if a.neutral else 2.75}',f'Vinject_n inject_n 0 {0 if a.neutral else a.n_gate_v}'])
    for kind in ['p','n']:
        active=3.3 if a.polarity==kind else 0
        lines.append(f'Vevent_{kind} event_{kind}_command 0 PWL(0 0 21.99u 0 22u {active} {end-.01}u {active} {end}u 0 80u 0)')
        lines.append(f'Vidle_{kind} event_{kind}_idle_command 0 PWL(0 3.3 21.97u 3.3 21.98u {0 if a.polarity==kind else 3.3} {end+.01}u {0 if a.polarity==kind else 3.3} {end+.02}u 3.3 80u 3.3)')
        lines.extend([f'Xidle_b_{kind} event_{kind}_idle_command event_{kind}_idleb vdd 0 gf180_phase_inverter_fullroute',f'Xidle_{kind} event_{kind}_idleb event_{kind}_idle vdd 0 gf180_phase_inverter_fullroute'])
        lines.extend([f'Xevent_b_{kind} event_{kind}_command event_{kind}b vdd 0 gf180_phase_inverter_fullroute',f'Xevent_{kind} event_{kind}b event_{kind} vdd 0 gf180_phase_inverter_fullroute'])
    for phase in ['write','read','park']:
        lines.extend([f'Xclock_b_{phase} {phase}_command {phase}b vdd 0 gf180_phase_inverter_fullroute',f'Xclock_{phase} {phase}b {phase} vdd 0 gf180_phase_inverter_fullroute'])
    targets={'low':.75,'mid':1.65,'high':2.55}
    for n,v in targets.items():
        idle=f'input_{n}' if a.idle_reference=='target' else 'vcm'
        lines.extend([f'Vin_{n} input_{n} 0 {v}',f'Cbitline_{n} column_{n} 0 200f',
            f'Xcell_{n} state_{n} vcm input_{n} column_{n} drain_{n} write writeb read readb park parkb 0 vdd vcm tiaout_{n} bias tiacmp_{n} gf180_nondestructive_storage_read_assembly_guarded_flat',
            f'Xinjectp_{n} pinternal_{n} inject_p vdd vdd pfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u',f'Xinjectn_{n} ninternal_{n} inject_n 0 0 nfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u',f'Xpcas_{n} pout_{n} pcas pinternal_{n} vdd pfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u',f'Xncas_{n} nout_{n} ncas ninternal_{n} 0 nfet_03v3 w=.5u l=1u ad=.22p as=.22p pd=1.88u ps=1.88u',f'Xpsel_{n} pout_{n} state_{n} event_p event_pb 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xpidle_{n} pout_{n} {idle} event_p_idle event_p_idleb 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xnsel_{n} nout_{n} state_{n} event_n event_nb 0 vdd gf180_fixed_body_tg_fullroute_half',f'Xnidle_{n} nout_{n} {idle} event_n_idle event_n_idleb 0 vdd gf180_fixed_body_tg_fullroute_half',f'.ic v(state_{n})={v} v(drain_{n})={a.park_v}'])
    lines.extend(['.control','set numdgt=15',f'tran {a.max_step_ns}n 51u 0 {a.max_step_ns}n uic'])
    for n in targets:
        lines.extend([f'let state_{n}=v(state_{n})',f'let drain_{n}=v(drain_{n})'])
        for phase,t in [('acquired','19.9u'),('before','20.5u'),('read1','40u'),('after1','50u')]:
            for signal in ['state','drain']:lines.append(f'meas tran {n}_{signal}_{phase} find {signal}_{n} at={t}')
        lines.extend([f'meas tran {n}_tia_output find v(tiaout_{n}) at=40u',f'meas tran {n}_tia_clamp find v(column_{n}) at=40u'])
        lines.extend([f'meas tran {n}_output_min min v(tiaout_{n}) from=35u to=44u',f'meas tran {n}_output_max max v(tiaout_{n}) from=35u to=44u',f'meas tran {n}_output_average avg v(tiaout_{n}) from=35u to=44u'])
        # Compute differences inside SPICE, avoiding subtraction of rounded logs.
        lines.extend([f'meas tran {n}_state_event find state_{n} at=28u',f'let eventdelta_{n}=state_{n}-{n}_state_before',f'meas tran {n}_event_delta find eventdelta_{n} at=28u'])
        lines.append(f'let delta_{n}=state_{n}-{n}_state_event')
        for phase,t in [('after1','50u'),('read1','40u')]:
            lines.append(f'meas tran {n}_delta_{phase} find delta_{n} at={t}')
        lines.extend([f'let write_delta_{n}=state_{n}-{n}_state_acquired',f'meas tran {n}_delta_write find write_delta_{n} at=20.5u'])
    lines.extend(['quit','.endc','.end']);deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');sources.add(deck)
    r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
    log=r.stdout+r.stderr;p=BASE/'results'/(stem+'.log');p.write_text(log);sources.add(p)
    values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_(?:state|current|drain|delta)_(?:acquired|before|read1|after1|read2|after2|write))\s*=\s*([-+0-9.eE]+)',log)}
    complete=r.returncode==0 and len(values)==33 and 'timestep too small' not in log.lower();cases=[]
    if complete:
        for n,target in targets.items():
            v={k.removeprefix(n+'_'):x for k,x in values.items() if k.startswith(n+'_')}
            cases.append({'target_v':target,'measurements':v,'event_delta_mv':1000*float(re.search(r'(?m)^'+n+r'_event_delta\s*=\s*([-+0-9.eE]+)',log)[1]),'initial_write_release_mv':1000*v['delta_write'],
                'post_event_late_drift_uv':1e6*v['delta_after1'],
                'temporary_read_disturbance_mv':1000*v['delta_read1'],'tia_output_v':float(re.search(r'(?m)^'+n+r'_tia_output\s*=\s*([-+0-9.eE]+)',log)[1]),'tia_clamp_v':float(re.search(r'(?m)^'+n+r'_tia_clamp\s*=\s*([-+0-9.eE]+)',log)[1])})
    q={'simulation_completed':complete,'settings':vars(a),'cases':cases,'settling_window':{n:{k:float(re.search(r'(?m)^'+n+'_'+k+r'\s*=\s*([-+0-9.eE]+)',log)[1]) for k in ['output_min','output_max','output_average']} for n in targets} if complete else {},'native_injector_physically_qualified':False,'signed_event_accuracy_accepted':False,'read_disabled':True,'scope':'Idle-reference diagnostic: target mode uses the ideal fixed initialization input as output parking reference, NOT an implemented state follower or a forced membrane waveform. Actual post-write membrane differs from that reference; no mathematical state correction. Independent actual inverter paths for select/idle with20ns commanded break before make on each transition. Continuously biased native schematic cascode branches, extracted qualified half-size select/idle TGs and actual complementary clock inverters, idle diverted to idealVCM. Neutral mode turns off current gates but keeps identical event clocks and switch loads; it is a circuit diagnostic, not an applied numerical correction. Injector routing and bias references unimplemented; no charge accuracy/weight binding acceptance. Read-disabled causal control: select never opens, drain stays zero-parked, late drift50us relative28us post-event state is not read disturbance. Native schematic four-MOS cascode gate-pulse update diagnostic: physical storage/read assembly plus NF/PF0.5um/L1um injection/cascode devices with ideal1.1V NF/2.2V PF cascode references, ideal selected NF0.4/0.42/0.45/0.55V and2.75V PF on-gate references, 10ns ideal gate edges, signed0.1/1/4us pulses. No original float weight binding or calibrated charge model. Injection device load present in control too; state_before20.5us, event measured28us, read-return referenced to actual post-event state28us. No numeric state correction, beta/threshold/reset/adaptation implementation or precision acceptance. Routed assembly voltage diagnostic; no inserted internal ideal current meter or estimated current decoding. Method-change screening only: Physically qualified seven-MOS/7um MIM storage cell with extracted internal routing and qualified clock inverters; Storage-to-frontend COL and supplies/control interfaces are now physically routed in one qualified assembly; external clock drivers and PF reference remain schematic. NF gate stays attached to state from initialization; fixed source/body0. Shared column candidate uses a qualified cap-extracted seven-MOS OTA/8um feedback poly/22um compensation MIM macro, schematic shared PF diode bias with ideal40uA reference, 200fF bitline bench load. Column clamp is now generated by transistor feedback, not an ideal column voltage source; No zero-volt column source is inserted in the physical internal connection. Frontend internal routing/native resistor/cap geometry and storage/frontend interconnect are qualified, but shared PF reference remains schematic; parking/reference supplies remain bench assumptions. One read with parking return, no destructive charge transfer, inverse or restoration of state. Gate leakage disabled/unqualified in native model; no noise/mismatch/PVT/RPEX/5ms retention/read-current decode/full-float/PLIF/service/area acceptance. Constant1.65V parking consumes continuous sense current;0V parking avoids that ideal DC path but incurs reversible drain/gate coupling. Initial write-release error remains.',
        'storage_frontend_assembly_qualified':True,'column_frontend_macro_qualified':True,'sense_primitive_qualified':True,'physical_cell_qualified':True,'physical_storage_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
    p=BASE/'results'/(stem+'.json');p.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'report':str(p),'simulation_completed':complete,'cases':cases},indent=2))
    if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
