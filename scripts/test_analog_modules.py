"""Run bounded ngspice module checks; does not start digital ASIC jobs.

Usage: python scripts/test_analog_modules.py [--only comparator]
"""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/analog_asic'
NAMES = ['membrane_hold', 'comparator', 'mechanisms', 'synapse_readout', 'sampled_plif']


def nearest(rows, t):
    return min(rows, key=lambda r: abs(r[0]-t))


def audit(name, rows):
    checks = {}
    if name == 'membrane_hold':
        checks['sample_tracks'] = abs(nearest(rows, 1.8e-6)[2]-1.1) < .005
        checks['hold_isolates_input'] = abs(nearest(rows, 4.5e-6)[2]-1.1) < .005
    elif name == 'comparator':
        checks['low_high_low'] = (nearest(rows,.8e-6)[2]<.1 and nearest(rows,2e-6)[2]>1.7 and nearest(rows,4e-6)[2]<.1)
    elif name == 'mechanisms':
        errors=[]; spikes=[]
        for r in rows:
            _, age, penalty, square, rms, spike, residual, inhibited, winner = r
            p=.2*max(0,min(age/5,2-age/5)) if age>=0 else 0
            energy=math.sqrt((.6-p)**2+1e-8)
            errors += [abs(penalty-p),abs(square-(.6-p)**2),abs(rms-energy),abs(inhibited-(.3-.2*energy)),abs(winner-1)]
            # Exclude discontinuity interpolation only, not an entire region.
            if abs(.6-(.45+p)) > 1e-5:
                expected=int(.6>=.45+p)
                spikes.append(abs(spike-expected)<1e-4 and abs(residual-(.6-expected*(.45+p)))<1e-4)
        checks['triangle_rms_inhibition_argmax'] = max(errors)<1e-5
        checks['threshold_subtractive_reset'] = all(spikes)
    elif name == 'synapse_readout':
        checks['signed_charge'] = abs(nearest(rows,2.5e-6)[1]-1.0)<.001 and abs(nearest(rows,4.2e-6)[1]-.95)<.001
        checks['readout_accumulate_reset'] = abs(nearest(rows,2.5e-6)[2]-1.0)<.001 and abs(nearest(rows,5.5e-6)[2]-.9)<.001
        checks['beta_target'] = all(abs(r[3]-.98)<1e-6 for r in rows)
    elif name == 'sampled_plif':
        reference=json.loads((OUT/'sampled_plif_reference.json').read_text())
        errors=[]; spikes=[]
        for expected in reference:
            i=expected['bin']; sampled=nearest(rows,(i*10+8.8)*1e-6); committed=nearest(rows,(i*10+9.8)*1e-6)
            errors.append(abs((committed[1]-.9)/.2-expected['preleaked']))
            spikes.append(int(sampled[3]>.9)==expected['spike'])
        checks['spike_sequence'] = all(spikes)
        checks['state_error_below_0_02_model_units'] = max(errors)<.02
        return checks, dict(max_state_error=max(errors), tolerance_model_units=.02,
                            note='Engineering smoke tolerance only; not a trained-model accuracy target')
    return checks, {}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',choices=NAMES)
    args=parser.parse_args()
    (OUT/'results').mkdir(exist_ok=True)
    results=[]
    for name in ([args.only] if args.only else NAMES):
        data=OUT/'results'/f'{name}.dat'
        if data.exists(): data.unlink()  # discard this bench's stale generated trace
        command=['docker','run','--rm','--memory','2g','--cpus','2',
                 '--volume',f'{ROOT}:/workspace:ro',
                 '--volume',f'{OUT}:/workspace/artifacts/analog_asic',
                 '--workdir','/workspace/artifacts/analog_asic/benches',
                 '--entrypoint','timeout','eventspikeseg:analog-ngspice36','60','ngspice','-b',f'{name}.cir']
        run=subprocess.run(command,capture_output=True,text=True,timeout=90)
        log=run.stdout+run.stderr
        (OUT/'results'/f'{name}.log').write_text(log)
        row=dict(module=name,exit_code=run.returncode,passed=False,
                 bench_sha256=hashlib.sha256((OUT/'benches'/f'{name}.cir').read_bytes()).hexdigest())
        if run.returncode==0 and data.exists() and 'fatal error' not in log.lower():
            rows=[[float(x) for x in line.split()] for line in data.read_text().splitlines()[1:]]
            assert rows and all(math.isfinite(x) for r in rows for x in r)
            checks, metrics=audit(name,rows)
            row.update(checks=checks,metrics=metrics,passed=all(checks.values()),samples=len(rows))
            if name=='comparator':
                energy=sum(-1.8*.5*(a[3]+b[3])*(b[0]-a[0]) for a,b in zip(rows,rows[1:]))
                row['metrics'].update(vdd_energy_j=energy,mean_vdd_power_w=energy/(rows[-1][0]-rows[0][0]),
                                      excluded='external bias/reference generation and all layout parasitics; TT schematic stimulus only')
        results.append(row); print(name, 'PASS' if row['passed'] else 'FAIL', row.get('metrics',{}))
    filename='test_results.json' if not args.only else f'{args.only}_test_results.json'
    (OUT/'results'/filename).write_text(json.dumps(dict(results=results,physical_layout_complete=False),indent=2)+'\n')
    return 0 if all(r['passed'] for r in results) else 1


if __name__=='__main__':
    raise SystemExit(main())
