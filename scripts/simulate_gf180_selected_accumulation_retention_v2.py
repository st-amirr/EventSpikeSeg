"""One bounded connected native signed-update/commit/5ms-hold characterization."""
from pathlib import Path
import json,re,hashlib,subprocess,time,array,sys,bisect,math
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';OUT=BASE/'results/selected_accumulation_retention_v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir(parents=True)
    prior=BASE/'results/gf180_decoded_shared_compute_tile_v2_native_selected_row_cycle_v1.json';pm=json.loads(prior.read_text());assert pm['module_simulation_completed']
    source=BASE/'benches/gf180_decoded_shared_compute_tile_v2_native_selected_row_cycle_v1.spice';assert sha(source)==pm['sha256'][source.relative_to(ROOT).as_posix()]
    qdir=BASE/'layout/gf180_decoded_shared_compute_tile_v2';qpath=qdir/'flat_cap_full_qualification.json';q=json.loads(qpath.read_text());native=qdir/(q['flat_subcircuit']+'_fullcap.spice');assert sha(native)==q['sha256'][native.relative_to(ROOT).as_posix()]
    text=source.read_text();assert native.read_text() in text
    def ctrl(name,value):
        nonlocal text
        text,n=re.subn(r'(?m)^Vctrl_'+name+r' .*$',f'Vctrl_{name} {name}_CMD_DRIVER 0 {value}',text);assert n==1,name
    # Keep native read/restore/beta/injection/capture/commit and remove optional
    # decision/reset stimuli from this accumulation-only characterization.
    for n,v in [('C_SAMPLE','0'),('C_SAMPLEB','3.3'),('C_OUTPUT_HOLD','0'),('C_OUTPUT_HOLDB','3.3'),('C_RESET','0')]:ctrl(n,v)
    ctrl('C_NEG','PWL(0 0 109.9u 0 110u 3.3 112.9u 3.3 113u 0 5.23m 0)')
    ctrl('C_NEGB','PWL(0 3.3 109.9u 3.3 110u 0 112.9u 0 113u 3.3 5.23m 3.3)')
    text,n=re.subn(r'(?m)^Vin C_INJ_NPROGRAM 0 .*$', 'Vin C_INJ_NPROGRAM 0 .7',text);assert n==1
    text=text.replace('.options method=gear','.options klu method=gear')
    text,n=re.subn(r'(?m)^\.tran .*$', '.tran .02u 5.23m 0 50u',text);assert n==1
    deck=OUT/'bench.spice';deck.write_text(text);raw=OUT/'waveforms.raw'
    run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',str(ROOT)+':/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','180','ngspice','-b','-r','/workspace/'+raw.relative_to(ROOT).as_posix(),'/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=195)
    log=OUT/'ngspice.log';log.write_text(run.stdout+run.stderr)
    report=dict(module_simulation_completed=False,simulator_returncode=run.returncode,native_module='gf180_decoded_shared_compute_tile_v2',negative_current_program_V=0.7,previous_negative_current_program_V=0.45,native_mos_resistor_mim_counts=[579,8,172],native_capacitance_branches=q['linear_branch_count'],selected_membrane='STATE70',event_workload=[dict(sign='positive',pulse_us=5,start_us=97),dict(sign='negative',pulse_us=3,start_us=110)],retention_window_ms=5,external_native_driver_fixture=True,output_decision_and_reset_stimuli_disabled=True,global_parent_RC_included=False,full_5ms_population_service_accepted=False,scope='Actual native decoded64state tile with complete verified routingC. One selected-row startup, beta step, positive5us and negative3us direct control pulses, analog capture/row commit, then5ms hold in the same connected circuit. Negative-current programming is0.7V instead of prior0.45V; all other analog program/cascode/reference biases retain prior values. One explicit operating-point diagnostic, no trained weight fit. Pulse controls are external qualified driver fixtures, not the routed native duration/event-controller chain. Other56cells use DC startup; no all-state startup, full injector-weight mapping, atlas loading, model accuracy or full-population deadline claim.')
    files={Path(__file__),prior,source,qpath,native,deck,log}
    if raw.exists():
        blob=raw.read_bytes();head,payload=blob.split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',head)[1]);variables=[l.split()[1] for l in head.decode().split('Variables:\n')[1].splitlines() if l.strip()];assert len(variables)==nv
        n=len(payload)//(nv*8);vals=array.array('d');vals.frombytes(payload[:n*nv*8]);
        if sys.byteorder!='little':vals.byteswap()
        times=[vals[i*nv] for i in range(n)];assert n and all(math.isfinite(t) for t in times) and all(a<=b for a,b in zip(times,times[1:]))
        def at(name,us):
            c=variables.index('v('+name.lower()+')');t=us*1e-6;j=bisect.bisect_left(times,t)
            if j==0:return vals[c]
            if j==n:return vals[(n-1)*nv+c]
            a,b=times[j-1:j+1];va,vb=vals[(j-1)*nv+c],vals[j*nv+c];return va+(vb-va)*(t-a)/(b-a)
        report.update(data_points=n,last_time_s=times[-1],module_simulation_completed=bool(run.returncode==0 and abs(times[-1]-5.23e-3)<1e-12 and 'aborted' not in (run.stdout+run.stderr).lower()))
        if report['module_simulation_completed']:
            positive=at('C_STATE',106)-at('C_STATE',96);negative=at('C_STATE',118)-at('C_STATE',109.5);before=at('STATE70',59.5);committed=at('STATE70',230);final=at('STATE70',5230);c=variables.index('v(state70)');after=[vals[i*nv+c] for i,t in enumerate(times) if t>=230e-6]
            report.update(compute_positive_step_mV=positive*1000,compute_negative_step_mV=negative*1000,signed_polarity_observed=positive>0 and negative<0,selected_bank_before_V=before,selected_bank_committed_V=committed,selected_bank_final_V=final,selected_bank_update_mV=(committed-before)*1000,selected_bank_5ms_drift_mV=(final-committed)*1000,selected_bank_5ms_max_excursion_mV=max(abs(x-committed) for x in after)*1000,held_write_column0_V=at('DATA0',139),row_commit_error_mV=(committed-at('DATA0',139))*1000,unselected_rows_max_update_change_mV=1000*max(abs(at(f'STATE{r}{c}',230)-at(f'STATE{r}{c}',59.5)) for r in range(7) for c in range(8)),other_selected_row_columns_max_update_change_mV=1000*max(abs(at(f'STATE7{c}',230)-at(f'STATE7{c}',59.5)) for c in range(1,8)),selected_case_commit_time_upper_bound_us=230)
        files.add(raw)
    report.update(elapsed_seconds=time.monotonic()-started,sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)});(OUT/'simulation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='sha256'}),flush=True)
    assert report['module_simulation_completed']
if __name__=='__main__':main()
