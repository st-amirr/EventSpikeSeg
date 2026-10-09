from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/test_sky130_geometry_weighted_sequence.py'
RES=ROOT/'artifacts/analog_asic/results'
rows=[]
for h in (0.2,0.3,0.4,0.5,0.7,0.9):
    cmd=[sys.executable,str(SCRIPT), '--order=shuffle','--event-offset=0','--event-count=1',
         '--state-cap-um=100','--gate-fraction=0.8',f'--headroom-v={h:g}',
         '--event-spacing-us=0.06','--stop-us=0.3','--series-isolation=true',
         '--reverse-polarity=true','--device-scale=1']
    run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=60)
    if run.returncode:
        raise RuntimeError(f'h={h}: {run.stdout}\n{run.stderr}')
    report=json.loads(run.stdout)
    if not report['simulation_completed']:
        raise RuntimeError(f'h={h}: ngspice transient did not complete')
    row={'headroom_v':h,'target_event_v':report['segment_float_target_v'],
         'measured_event_v':report['measured_event_sum_v'],
         'event_error_pct':100*report['forward_or_order_relative_error'],
         'pre_event_differential_v':report['raw_measurements_v']['pre_diff'],
         'geometry_minmax':report['minimum_and_maximum_device_geometry_scale'],
         'source_report':next(RES.glob(f"sky130_geometry_weighted_sequence_n370_*_ordshuffle_*_H{h:g}_*iso1_rp1_ds1*seg0-1.json")).name}
    rows.append(row); print(json.dumps(row),flush=True)
out={'simulation_completed':True,'corner':'SS','temperature_c':0,'checkpoint_sha256':report['checkpoint_sha256'],
     'sweeps':rows,'scope':'One float event at one high-fanin site, isolated series NMOS devices, fixed gate level, geometry mapped from direct MOS transfer then polarity reversed. Schematic only; no other event devices, extracted routing, mismatch/noise, hold beyond 210.5ns, or layout.'}
(RES/'sky130_series_isolation_geometry_transfer_sweep.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
