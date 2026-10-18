"""Observe internal nodes of the frozen v6 reset circuit without changing its devices."""
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    donor = BASE / 'results/gf180_combined_v6_fresh_transfer_6d6be4fb07_src645ec5d896cd.json'
    original = json.loads(donor.read_text())
    assert original['simulation_completed']
    for n, h in original['sha256'].items():
        assert sha(ROOT / n) == h, n
    source = next(ROOT / n for n in original['sha256'] if n.endswith('.spice') and '/benches/' in n)
    stem = 'gf180_combined_reset_settling_src' + sha(Path(__file__))[:12]
    rp = BASE / 'results' / (stem + '.json')
    assert not rp.exists()
    data = BASE / 'results' / (stem + '.dat')
    deck = BASE / 'benches' / (stem + '.spice')
    lines = source.read_text().splitlines()
    extra = [f'v({node}_{arm}_{tag})' for tag in ['near','high']
             for arm in ['idle','neutral','active']
             for node in ['out','cmp','azin','parkdrive','parkazin','ni']]
    for i, line in enumerate(lines):
        if line.startswith('wrdata '):
            parts = line.split()
            lines[i] = ' '.join(['wrdata','/workspace/'+data.relative_to(ROOT).as_posix(),*parts[2:],*extra])
    # Device definitions, initialization, phases and analysis are byte-identical lines.
    assert [x for x in lines if not x.startswith('wrdata ')] == [x for x in source.read_text().splitlines() if not x.startswith('wrdata ')]
    deck.write_text('\n'.join(lines)+'\n')
    snap = BASE / 'tools/source_snapshots' / (stem+'.py')
    snap.write_bytes(Path(__file__).read_bytes())
    run = subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2',
        '--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout',
        'eventspikeseg:analog-ngspice47','180','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],
        capture_output=True,text=True,timeout=195)
    log = BASE/'results'/(stem+'.log'); log.write_text(run.stdout+run.stderr)
    report = {'donor':donor.relative_to(ROOT).as_posix(),'simulator_returncode':run.returncode,
              'simulation_completed':False,'circuit_unchanged':True,'scope':'Nominal internal-node diagnosis, no hardware or calibration change; no acceptance.'}
    try:
        columns = data.open().readline().split()
        w = np.loadtxt(data,skiprows=1)
        report['simulation_completed'] = bool(run.returncode==0 and w.shape[1]==len(columns) and np.isfinite(w).all() and abs(w[-1,0]-.00605)<1e-12)
        if report['simulation_completed']:
            sample=lambda name,t:float(np.interp(t*1e-6,w[:,0],w[:,columns.index(name)]))
            times=[1043.5,1044.1,1044.8,1045.5,1046,1049.5,1055,1100,6049.5]
            report['samples']=[{'time_us':t,'nodes':{name:sample(name,t) for name in extra}} for t in times]
            # Require all previously saved voltages/currents to reproduce the donor.
            olddata=next(ROOT/n for n in original['sha256'] if n.endswith('.dat'))
            old=np.loadtxt(olddata,skiprows=1)
            report['donor_saved_columns_bit_identical']=bool(np.array_equal(old,w[:,:old.shape[1]]))
    except Exception as e:
        report['postprocess_error']=str(e)
    paths=[Path(__file__),donor,source,deck,snap,log]
    if data.exists(): paths.append(data)
    report['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    rp.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(rp),**{k:v for k,v in report.items() if k not in ['sha256','samples']}},indent=2))
    assert report['simulation_completed']

if __name__=='__main__': main()
