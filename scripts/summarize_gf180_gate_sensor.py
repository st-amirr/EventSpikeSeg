"""Summarize gate-sensor layout, read disturbance and stationary phase noise."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'artifacts/analog_asic'


def main():
    sources=[Path(__file__)];geometry={}
    for name in ['gf180_gate_sensor','gf180_gate_sensor_shielded']:
        p=BASE/f'layout/{name}/qualification.json';geometry[name]=json.loads(p.read_text());sources.append(p)
    records=[]
    for p in sorted((BASE/'results').glob('gf180_gate_sensor_*.json')):
        if p.name.startswith(('gf180_gate_sensor_noise_','gf180_gate_sensor_boundary')):
            continue
        r=json.loads(p.read_text());sources.append(p)
        row={k:r.get(k) for k in ['simulation_completed','corner','temperature_c','offset_mv','physical_sensor','sensor_cell','physical_park_switch','read_cycles','cycle_gap_us','load_mim_cell','read_disabled_control']}
        row['source']=p.relative_to(ROOT).as_posix()
        if r['simulation_completed']:
            v=r['rows'];low,high=v['low'],v['high']
            heldspan=high['held']-low['held']
            row.update(post_read_span_ratio=(high['after']-low['after'])/heldspan,
                       during_read_span_ratio=(high['during']-low['during'])/heldspan,
                       max_post_read_disturbance_mv=max(abs(x['post_read_disturbance_mv']) for x in v.values()),
                       max_500ns_vs1900ns_bus_difference_uv=max(abs(x['bus_500ns_vs1900ns_uv']) for x in v.values()))
            if 'final' in low:
                row['after_three_reads_span_ratio']=(high['final']-low['final'])/heldspan
                row['max_extra_second_third_read_movement_uv']=max(abs(x['final']-x['after'])*1e6 for x in v.values())
        records.append(row)
    noises=[]
    for p in sorted((BASE/'results').glob('gf180_gate_sensor_noise_*.json')):
        r=json.loads(p.read_text());sources.append(p)
        if not r['simulation_completed']:
            raise ValueError(f'incomplete noise {p}')
        noises.append({'corner':r['corner'],'temperature_c':r['temperature_c'],
                       'bus_noise_uv_rms':r['values']['bus_rms']*1e6,
                       'held_state_noise_uv_rms':r['values']['state_rms']*1e6,
                       'scope':r['scope']})
    x0,y0,x1,y1=geometry['gf180_gate_sensor_shielded']['bbox_um'];area=(x1-x0)*(y1-y0)
    report={'physical_state_accepted':False,'geometry':geometry,'records':records,'stationary_phase_noise':noises,
            'sensor_footprint_um2':area,'sensor_only_unshared_single_rail_inventory_repetition_mm2':area*30976000/1e6,
            'inventory_scaling_scope':'Standalone guard/routing repetition, not optimized array, lower bound or full-chip area. Permanent gate attachment makes one sensor per stored rail; it cannot be counted as one shared reader per actor channel.',
            'conclusion':'Permanent gate sensor avoids complete erasure, but read causes large common shift plus state-dependent gain; local sensor mismatch and resident area remain unresolved. Shortening state rail reduces extracted coupling, not proof of negligible disturbance. Three5ms-spaced read screens contain no weighted events or complete PLIF updates and do not qualify long stream behavior.',
            'next_step':'Measure local mismatch/physical self-reference and full-bin read cycles, compare an array-packed resident sensor with shared-reader sensing/restoration. Require actual analog encode/decode/restore, sampled noise, leakage, original-float replay and service/density before architecture acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (BASE/'results/gf180_gate_sensor_boundary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'area_um2':area,'unshared_single_rail_sensor_mm2':report['sensor_only_unshared_single_rail_inventory_repetition_mm2'],
                      'physical_records':[r for r in records if r.get('physical_sensor')], 'stationary_noise':noises},indent=2))


if __name__=='__main__':
    main()
