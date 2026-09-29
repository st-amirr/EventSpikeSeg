"""Bounded ASAP7 device, storage and integrated-PLIF checks. Never runs ORFS."""
import json
import math
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic/asap7'


def run(name, end_time, dc=False):
    file=OUT/'results'/f'{name}.dat'
    if file.exists(): file.unlink()
    command=['docker','run','--rm','--memory','2g','--cpus','2',
             '--volume',f'{ROOT}:/workspace:ro',
             '--volume',f'{OUT}:/workspace/artifacts/analog_asic/asap7',
             '--workdir','/workspace/artifacts/analog_asic/asap7/benches',
             '--entrypoint','timeout','eventspikeseg:analog-ngspice36',
             '60','../tools/ngspice45/bin/ngspice','-b',f'{name}.cir']
    result=subprocess.run(command,capture_output=True,text=True,timeout=90)
    log=result.stdout+result.stderr
    (OUT/'results'/f'{name}.log').write_text(log)
    rows=[]
    if file.exists(): rows=[[float(x) for x in l.split()] for l in file.read_text().splitlines()[1:]]
    complete=(result.returncode==0 and bool(rows) and rows[-1][0]>=end_time*.999
              and all(math.isfinite(x) for r in rows for x in r)
              and 'aborted' not in log.lower() and 'timestep too small' not in log.lower())
    report=dict(bench=name,simulation_completed=complete,exit_code=result.returncode,
                final_independent_value=rows[-1][0] if rows else None)
    if complete and name.startswith('inverter'):
        report['rail_check_passed']=abs(rows[0][2]-.7)<.01 and (abs(rows[-1][2])<.01 if dc else abs(rows[-1][2]-.7)<.01)
        if not dc: report['switched_low']=min(r[2] for r in rows)<.01
    if complete and name.startswith('retention'):
        # Compare after opening the sampling switch; excludes initial injection.
        initial=min(rows,key=lambda r:abs(r[0]-1.1e-6))[1]
        drift=rows[-1][1]-initial
        report.update(hold_drift_v=drift,normalized_model_drift=drift/.07,
                      provisional_0_02_unit_retention_pass=abs(drift/.07)<.02,
                      caveat='Ideal capacitor and ideal external clocks; no dielectric leakage or layout parasitics')
    if complete and name.startswith('sampled_plif'):
        reference=json.loads((ROOT/'artifacts/analog_asic/sampled_plif_reference.json').read_text())
        errors=[]; spikes=[]
        for e in reference:
            i=e['bin']; capture=min(rows,key=lambda r:abs(r[0]-(i*10+8.8)*1e-6)); commit=min(rows,key=lambda r:abs(r[0]-(i*10+9.8)*1e-6))
            errors.append(abs((commit[1]-.35)/.07-e['preleaked']))
            spikes.append(int(capture[3]>.35)==e['spike'])
        report.update(max_state_error=max(errors),spike_sequence_pass=all(spikes),
                      provisional_state_error_pass=max(errors)<.02)
    print(json.dumps(report))
    return report


def main():
    # Match output file name to bench so stale data cannot masquerade as success.
    inverter=(OUT/'benches/inverter.cir').read_text().replace('inverter_dc.dat','inverter_dc_check.dat')
    (OUT/'benches/inverter_dc_check.cir').write_text(inverter)
    results=[run('inverter_dc_check',.7,dc=True),run('inverter_transient',7e-9)]
    base=(OUT/'benches/retention_external_clock.cir').read_text()
    for cap in [1,10,20]:
        name=f'retention_{cap}pf'
        (OUT/'benches'/f'{name}.cir').write_text(base.replace('cmem=1p',f'cmem={cap}p').replace('retention_external_clock.dat',f'{name}.dat'))
        row=run(name,.005002); row['ideal_capacitance_f']=cap*1e-12; results.append(row)
    results.append(run('sampled_plif_external',80e-6))
    ready=all(x['simulation_completed'] for x in results)
    (OUT/'results/compatibility_checks.json').write_text(json.dumps(dict(
        results=results,all_simulations_completed=ready,full_orfs_ready=False,
        warning='Basic device compatibility does not establish analog macro qualification; retention tolerances are provisional.'),indent=2)+'\n')
    return 0 if ready else 2


if __name__=='__main__': raise SystemExit(main())
