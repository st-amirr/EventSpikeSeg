"""Join official sensor mismatch and physically implemented zero-servo evidence."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    sources=[Path(__file__)]
    layout=BASE/'layout/gf180_sensor_servo_writer/qualification.json'
    geometry=json.loads(layout.read_text());sources.append(layout)
    reproducibility=BASE/'results/gf180_sensor_mismatch_seed17_reproducibility.json'
    check=json.loads(reproducibility.read_text());sources.append(reproducibility)
    if not check['same_seed_exact_rows']:
        raise ValueError('seed reproducibility failed')
    mismatch=[];servo=[]
    for p in sorted((BASE/'results').glob('gf180_gate_sensor_mismatch_*.json')):
        r=json.loads(p.read_text());sources.append(p)
        if not r['simulation_completed']:
            raise ValueError(f'incomplete mismatch {p}')
        mismatch.append({'source':p.relative_to(ROOT).as_posix(),'seed':r['seed'],
                         'local_mismatch_enabled':r['local_mismatch_enabled'],'samples':r['samples'],
                         'statistics':r['statistics']})
    for p in sorted((BASE/'results').glob('gf180_sensor_zero_servo_*.json')):
        r=json.loads(p.read_text());sources.append(p)
        if r.get('sampled_restore'):
            sources.pop()
            continue
        row={'source':p.relative_to(ROOT).as_posix(),'simulation_completed':r['simulation_completed'],
             'seed':r['seed'],'local_mismatch_enabled':r['local_mismatch_enabled'],'slots':r['slots'],
             'combined_routed_writer':r.get('combined_routed_writer',False),'corner':r.get('corner','typical'),
             'temperature_c':r.get('temperature_c',27),'setpoint_v':r.get('setpoint_v',1.2),
             'statistics':r['statistics']}
        if r['simulation_completed']:
            row['read_minus_setpoint_mv']=(r['statistics']['read_mean_v']-row['setpoint_v'])*1000
            row['mean_release_injection_mv']=(r['statistics']['released_mean_v']-r['statistics']['program_mean_v'])*1000
        servo.append(row)
    x0,y0,x1,y1=geometry['bbox_um']
    result={'physical_state_accepted':False,'writer_layout':geometry,'writer_footprint_um2':(x1-x0)*(y1-y0),
            'seed_reproducibility':check,'mismatch':mismatch,'zero_servo':servo,
            'conclusion':'Sensor-referenced initialization physically absorbs local source-follower threshold offset into stored zero. Shared OTA/input switches/reference diode/compensation now one routed macro. Post-release5ms read retains48..67uV sample scatter in three separate-piece8slot mismatch cases; combined routed8slot seed17 about50uV. Shared common offset7..11mV remains uncorrected. No physical sampled restore or nonlinear encoder is implemented.',
            'next_step':'Build physical offset storage/subtraction and sampled analog restore; qualify noise/reference/PVT/range and local mismatch, then compare packed resident sensor area against shared sensing. Preserve exact original-float PLIF semantics; initialize only at model reset boundary, do not replace subtractive spike reset with zero servo.',
            'scope':'Small per-module benches with ideal reference/read currents and supplies/controls/initial clamp. Local mismatch screening is not a manufacturing-yield estimate; DC32sensor and transient8slot populations differ. Schematic reference diode in older separate-piece runs, physical diode in combined writer. MIM typical only. No complete channel service, resistance extraction, gate leakage, full model accuracy, array or full-chip qualification.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    p=BASE/'results/gf180_sensor_self_reference_boundary.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(p),'writer_area_um2':result['writer_footprint_um2'],
                      'servo_cases':len(servo),'all_servo_runs_complete':all(r['simulation_completed'] for r in servo)},indent=2))


if __name__=='__main__':
    main()
